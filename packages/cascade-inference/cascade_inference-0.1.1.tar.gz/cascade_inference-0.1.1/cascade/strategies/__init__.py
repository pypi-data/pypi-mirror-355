"""
The strategies module provides different methods for checking agreement
between multiple LLM responses.
"""

from .base import AgreementStrategy
from .strict import StrictAgreement
from .remote_semantic import RemoteSemanticAgreement

__all__ = [
    "AgreementStrategy",
    "StrictAgreement",
    "RemoteSemanticAgreement",
]

try:
    from .semantic import SemanticAgreement
    __all__.append("SemanticAgreement")
except ImportError:
    pass 