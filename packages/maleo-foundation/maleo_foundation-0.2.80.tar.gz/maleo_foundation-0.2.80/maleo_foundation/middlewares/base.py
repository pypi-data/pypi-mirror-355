import json
import threading
import time
import traceback
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Awaitable, Callable, Optional, Sequence, Dict, List
from uuid import UUID, uuid4

from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from maleo_foundation.authentication import Authentication
from maleo_foundation.enums import BaseEnums
from maleo_foundation.client.manager import MaleoFoundationClientManager
from maleo_foundation.models.schemas import BaseGeneralSchemas
from maleo_foundation.models.responses import BaseResponses
from maleo_foundation.models.transfers.general.token import MaleoFoundationTokenGeneralTransfers
from maleo_foundation.models.transfers.parameters.token import MaleoFoundationTokenParametersTransfers
from maleo_foundation.models.transfers.parameters.signature import MaleoFoundationSignatureParametersTransfers
from maleo_foundation.utils.extractor import BaseExtractors
from maleo_foundation.utils.logging import MiddlewareLogger

RequestProcessor = Callable[[Request], Awaitable[Optional[Response]]]
ResponseProcessor = Callable[[Response], Awaitable[Response]]

class RateLimiter:
    """Thread-safe rate limiter with automatic cleanup."""

    def __init__(
        self,
        limit:int,
        window:timedelta,
        ip_timeout:timedelta,
        cleanup_interval:timedelta
    ):
        self.limit = limit
        self.window = window
        self.ip_timeout = ip_timeout
        self.cleanup_interval = cleanup_interval
        self._requests:Dict[str, List[datetime]] = defaultdict(list)
        self._last_seen:Dict[str, datetime] = {}
        self._last_cleanup = datetime.now()
        self._lock = threading.RLock()

    def is_rate_limited(
        self,
        client_ip:str
    ) -> bool:
        """Check if client IP is rate limited and record the request."""
        with self._lock:
            now = datetime.now()
            self._last_seen[client_ip] = now

            # Remove old requests outside the window
            self._requests[client_ip] = [
                timestamp for timestamp in self._requests[client_ip]
                if now - timestamp <= self.window
            ]

            # Check rate limit
            if len(self._requests[client_ip]) >= self.limit:
                return True

            # Record this request
            self._requests[client_ip].append(now)
            return False

    def cleanup_old_data(
        self,
        logger:MiddlewareLogger
    ) -> None:
        """Clean up old request data to prevent memory growth."""
        now = datetime.now()
        if now - self._last_cleanup <= self.cleanup_interval:
            return

        with self._lock:
            inactive_ips = []

            for ip in list(self._requests.keys()):
                # Remove IPs with empty request lists
                if not self._requests[ip]:
                    inactive_ips.append(ip)
                    continue

                # Remove IPs that haven't been active recently
                last_active = self._last_seen.get(ip, datetime.min)
                if now - last_active > self.ip_timeout:
                    inactive_ips.append(ip)

            # Clean up inactive IPs
            for ip in inactive_ips:
                self._requests.pop(ip, None)
                self._last_seen.pop(ip, None)

            self._last_cleanup = now
            logger.debug(
                f"Cleaned up request cache. Removed {len(inactive_ips)} inactive IPs. "
                f"Current tracked IPs: {len(self._requests)}"
            )


class ResponseBuilder:
    """Handles response building and header management."""

    def __init__(
        self,
        keys:BaseGeneralSchemas.RSAKeys,
        maleo_foundation:MaleoFoundationClientManager
    ):
        self.keys = keys
        self.maleo_foundation = maleo_foundation

    def add_response_headers(
        self,
        request:Request,
        authentication:Authentication,
        response:Response,
        request_timestamp:datetime,
        response_timestamp:datetime,
        process_time:float,
        request_id:UUID
    ) -> Response:
        """Add custom headers to response."""
        # Basic headers
        response.headers["X-Request-ID"] = str(request_id)
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Request-Timestamp"] = request_timestamp.isoformat()
        response.headers["X-Response-Timestamp"] = response_timestamp.isoformat()

        # Add signature header
        self._add_signature_header(request, response, request_timestamp, response_timestamp, process_time, request_id)

        # Add new authorization header if needed
        self._add_new_authorization_header(request, authentication, response)

        return response

    def _add_signature_header(
        self,
        request:Request,
        response:Response,
        request_timestamp:datetime,
        response_timestamp:datetime,
        process_time:float,
        request_id:UUID
    ) -> None:
        """Generate and add signature header."""
        message = (
            f"{request.method}|{request.url.path}|{request_timestamp.isoformat()}|"
            f"{response_timestamp.isoformat()}|{str(process_time)}|{str(request_id)}"
        )

        sign_parameters = MaleoFoundationSignatureParametersTransfers.Sign(
            key=self.keys.private,
            password=self.keys.password,
            message=message
        )

        sign_result = self.maleo_foundation.services.signature.sign(parameters=sign_parameters)
        if sign_result.success:
            response.headers["X-Signature"] = sign_result.data.signature

    def _add_new_authorization_header(
        self,
        request:Request,
        authentication:Authentication,
        response:Response
    ) -> None:
        """Add new authorization header for refresh tokens."""
        if not self._should_regenerate_auth(request, authentication, response):
            return

        payload = MaleoFoundationTokenGeneralTransfers.BaseEncodePayload.model_validate(
            authentication.credentials.token.payload.model_dump()
        )

        parameters = MaleoFoundationTokenParametersTransfers.Encode(
            key=self.keys.private,
            password=self.keys.password,
            payload=payload
        )

        result = self.maleo_foundation.services.token.encode(parameters=parameters)
        if result.success:
            response.headers["X-New-Authorization"] = result.data.token

    def _should_regenerate_auth(
        self,
        request:Request,
        authentication:Authentication,
        response:Response
    ) -> bool:
        """Check if authorization should be regenerated."""
        return (
            authentication.user.is_authenticated
            and authentication.credentials.token.type == BaseEnums.TokenType.REFRESH
            and 200 <= response.status_code < 300
            and "logout" not in request.url.path
        )


class RequestLogger:
    """Handles request/response logging."""

    def __init__(
        self,
        logger:MiddlewareLogger
    ):
        self.logger = logger

    def log_request_response(
        self,
        request:Request,
        authentication:Authentication,
        response:Response,
        client_ip:str,
        request_id:UUID,
        log_level:str = "info"
    ) -> None:
        """Log request and response details."""
        authentication_info = self._get_authentication_info(authentication)

        log_func = getattr(self.logger, log_level)
        log_func(
            f"Request | ID: {request_id} {authentication_info} | IP: {client_ip} | "
            f"Host: {request.client.host} | Port: {request.client.port} | "
            f"Method: {request.method} | URL: {request.url.path} | "
            f"Headers: {dict(request.headers)} - Response | Status: {response.status_code}"
        )
    
    def log_exception(
        self,
        request:Request,
        authentication:Authentication,
        error:Exception,
        client_ip:str,
        request_id:UUID
    ) -> None:
        """Log exception details."""
        authentication_info = self._get_authentication_info(authentication)

        error_details = {
            "request_id": str(request_id),
            "error": str(error),
            "traceback": traceback.format_exc().split("\n"),
            "client_ip": client_ip,
            "method": request.method,
            "url": request.url.path,
            "headers": dict(request.headers),
        }

        self.logger.error(
            f"Request | ID: {request_id} {authentication_info} | IP: {client_ip} | "
            f"Host: {request.client.host} | Port: {request.client.port} | "
            f"Method: {request.method} | URL: {request.url.path} | "
            f"Headers: {dict(request.headers)} - Response | Status: 500 | "
            f"Exception:\n{json.dumps(error_details, indent=4)}"
        )

    def _get_authentication_info(self, authentication:Authentication) -> str:
        """Get authentication info string."""
        if not authentication.user.is_authenticated:
            return "| Unauthenticated"

        return (
            f"| Token type: {authentication.credentials.token.type} | "
            f"Username: {authentication.user.display_name} | "
            f"Email: {authentication.user.identity}"
        )


class BaseMiddleware(BaseHTTPMiddleware):
    """Base middleware with rate limiting, logging, and response enhancement."""

    def __init__(
        self,
        app:FastAPI,
        keys:BaseGeneralSchemas.RSAKeys,
        logger:MiddlewareLogger,
        maleo_foundation:MaleoFoundationClientManager,
        allow_origins:Sequence[str] = (),
        allow_methods:Sequence[str] = ("GET",),
        allow_headers:Sequence[str] = (),
        allow_credentials:bool = False,
        limit:int = 10,
        window:int = 1,
        cleanup_interval:int = 60,
        ip_timeout:int = 300
    ):
        super().__init__(app)

        # Core components
        self.rate_limiter = RateLimiter(
            limit=limit,
            window=timedelta(seconds=window),
            ip_timeout=timedelta(seconds=ip_timeout),
            cleanup_interval=timedelta(seconds=cleanup_interval)
        )
        self.response_builder = ResponseBuilder(keys, maleo_foundation)
        self.request_logger = RequestLogger(logger)

        # CORS settings (if needed)
        self.cors_config = {
            'allow_origins': allow_origins,
            'allow_methods': allow_methods,
            'allow_headers': allow_headers,
            'allow_credentials': allow_credentials,
        }

    async def dispatch(self, request:Request, call_next:RequestResponseEndpoint) -> Response:
        """Main middleware dispatch method."""
        # Generate unique request ID
        request_id = uuid4()
        request.state.request_id = request_id

        # Setup
        self.rate_limiter.cleanup_old_data(self.request_logger.logger)
        request_timestamp = datetime.now(tz=timezone.utc)
        request.state.request_timestamp = request_timestamp
        start_time = time.perf_counter()
        client_ip = BaseExtractors.extract_client_ip(request)
        authentication = Authentication(credentials=request.auth, user=request.user)

        try:
            # Rate limiting check
            if self.rate_limiter.is_rate_limited(client_ip):
                return self._create_rate_limit_response(
                    request, authentication, client_ip, request_timestamp, start_time, request_id
                )

            # Optional preprocessing
            pre_response = await self._request_processor(request)
            if pre_response is not None:
                return self._build_final_response(
                    request, authentication, pre_response, client_ip,
                    request_timestamp, start_time, request_id
                )

            # Main request processing
            response = await call_next(request)
            return self._build_final_response(
                request, authentication, response, client_ip,
                request_timestamp, start_time, request_id
            )

        except Exception as e:
            return self._handle_exception(
                request, authentication, e, client_ip, request_timestamp, start_time, request_id
            )

    async def _request_processor(self, request:Request) -> Optional[Response]:
        """Override this method for custom request preprocessing."""
        return None

    def _create_rate_limit_response(
        self,
        request:Request,
        authentication:Authentication,
        client_ip:str,
        request_timestamp:datetime,
        start_time:float,
        request_id:UUID
    ) -> Response:
        """Create rate limit exceeded response."""
        response = JSONResponse(
            content=BaseResponses.RateLimitExceeded().model_dump(),
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )
        
        return self._build_final_response(
            request, authentication, response, client_ip,
            request_timestamp, start_time, request_id, log_level="warning"
        )

    def _build_final_response(
        self,
        request:Request,
        authentication:Authentication,
        response:Response,
        client_ip:str,
        request_timestamp:datetime,
        start_time:float,
        request_id:UUID,
        log_level:str = "info"
    ) -> Response:
        """Build final response with headers and logging."""
        response_timestamp = datetime.now(tz=timezone.utc)
        process_time = time.perf_counter() - start_time
        
        # Add headers
        response = self.response_builder.add_response_headers(
            request, authentication, response, request_timestamp, response_timestamp, process_time, request_id
        )

        # Log request/response
        self.request_logger.log_request_response(
            request, authentication, response, client_ip, request_id, log_level
        )

        return response

    def _handle_exception(
        self,
        request:Request,
        authentication:Authentication,
        error:Exception,
        client_ip:str,
        request_timestamp:datetime,
        start_time:float,
        request_id:UUID
    ) -> Response:
        """Handle exceptions and create error response."""
        response_timestamp = datetime.now(tz=timezone.utc)
        process_time = time.perf_counter() - start_time
        
        response = JSONResponse(
            content=BaseResponses.ServerError().model_dump(),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

        # Log exception
        self.request_logger.log_exception(request, authentication, error, client_ip, request_id)
        
        # Add headers
        return self.response_builder.add_response_headers(
            request, authentication, response, request_timestamp, response_timestamp, process_time, request_id
        )


def add_base_middleware(
    app:FastAPI,
    keys:BaseGeneralSchemas.RSAKeys,
    logger:MiddlewareLogger,
    maleo_foundation:MaleoFoundationClientManager,
    allow_origins:Sequence[str] = (),
    allow_methods:Sequence[str] = ("GET",),
    allow_headers:Sequence[str] = (),
    allow_credentials:bool = False,
    limit:int = 10,
    window:int = 1,
    cleanup_interval:int = 60,
    ip_timeout:int = 300
) -> None:
    """
    Add Base middleware to the FastAPI application.

    Args:
        app:FastAPI application instance
        keys:RSA keys for signing and token generation
        logger:Middleware logger instance
        maleo_foundation:Client manager for foundation services
        allow_origins:CORS allowed origins
        allow_methods:CORS allowed methods
        allow_headers:CORS allowed headers
        allow_credentials:CORS allow credentials flag
        limit:Request count limit per window
        window:Time window for rate limiting (seconds)
        cleanup_interval:Cleanup interval for old IP data (seconds)
        ip_timeout:IP timeout after last activity (seconds)

    Example:
        ```python
        add_base_middleware(
            app=app,
            keys=rsa_keys,
            logger=middleware_logger,
            maleo_foundation=client_manager,
            limit=10,
            window=1,
            cleanup_interval=60,
            ip_timeout=300
        )
        ```
    """
    app.add_middleware(
        BaseMiddleware,
        keys=keys,
        logger=logger,
        maleo_foundation=maleo_foundation,
        allow_origins=allow_origins,
        allow_methods=allow_methods,
        allow_headers=allow_headers,
        allow_credentials=allow_credentials,
        limit=limit,
        window=window,
        cleanup_interval=cleanup_interval,
        ip_timeout=ip_timeout
    )