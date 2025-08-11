"""Universal Information Retrieval Framework"""

from ._version import __version__, __version_info__
from .client import UIR
from .models import (
    SearchRequest,
    SearchResponse,
    SearchResult,
    VectorSearchRequest,
    HybridSearchRequest,
    SearchOptions,
    Provider,
    ProviderType
)

__all__ = [
    "__version__",
    "__version_info__",
    "UIR",
    "SearchRequest",
    "SearchResponse",
    "SearchResult", 
    "VectorSearchRequest",
    "HybridSearchRequest",
    "SearchOptions",
    "Provider",
    "ProviderType"
]