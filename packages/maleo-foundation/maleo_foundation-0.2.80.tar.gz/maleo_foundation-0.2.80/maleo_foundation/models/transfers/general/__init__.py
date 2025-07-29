from __future__ import annotations
from maleo_foundation.models.schemas.general import BaseGeneralSchemas
from .token import MaleoFoundationTokenGeneralTransfers

class BaseGeneralTransfers:
    Token = MaleoFoundationTokenGeneralTransfers

class AccessTransfers(
    BaseGeneralSchemas.AccessedBy,
    BaseGeneralSchemas.AccessedAt
): pass