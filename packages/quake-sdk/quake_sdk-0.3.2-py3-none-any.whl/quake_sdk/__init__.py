"""
Quake SDK for Python

提供对 Quake 网络空间测绘系统的 API 访问
"""

from typing import Union, List, Dict, Any

# 直接从 client 导入 QuakeClient，方便用户使用
from .client import QuakeClient
from .exceptions import (
    QuakeAPIException,
    QuakeAuthException,
    QuakeRateLimitException,
    QuakeInvalidRequestException,
    QuakeServerException
)
from .models import (
    # Request Models
    RealtimeSearchQuery,
    ScrollSearchQuery,
    AggregationQuery,
    FaviconSimilarityQuery,
    # User Info Models
    User,
    UserRole,
    UserInfoData,
    EnterpriseInformation,
    PrivacyLog,
    DisableInfo,
    InvitationCodeInfo,
    RoleValidityPeriod,
    # Response Data Models (core data part of responses)
    QuakeService,
    QuakeHost,
    AggregationBucket,
    SimilarIconData,
    Location,
    Component,
    ServiceData,
    # Specific Service Info Models (examples)
    HttpServiceInfo,
    FtpServiceInfo,
    SshServiceInfo,
    # Full Response Wrappers
    UserInfoResponse,
    FilterableFieldsResponse,
    ServiceSearchResponse,
    ServiceScrollResponse,
    ServiceAggregationResponse,
    HostSearchResponse,
    HostScrollResponse,
    HostAggregationResponse,
    SimilarIconResponse
)
from .utils import validate_quake_data

__version__ = "0.3.1"  # Added pyrate_limiter dependency for rate limiting

__all__ = [
    "QuakeClient",
    # Exceptions
    "QuakeAPIException",
    "QuakeAuthException",
    "QuakeRateLimitException",
    "QuakeInvalidRequestException",
    "QuakeServerException",
    # Request Models
    "RealtimeSearchQuery",
    "ScrollSearchQuery",
    "AggregationQuery",
    "FaviconSimilarityQuery",
    # User Info Models
    "User",
    "UserRole",
    "UserInfoData",
    "EnterpriseInformation",
    "PrivacyLog",
    "DisableInfo",
    "InvitationCodeInfo",
    "RoleValidityPeriod",
    # Response Data Models
    "QuakeService",
    "QuakeHost",
    "AggregationBucket",
    "SimilarIconData",
    "Location",
    "Component",
    "ServiceData",
    "HttpServiceInfo",
    "FtpServiceInfo",
    "SshServiceInfo",
    # Full Response Wrappers
    "UserInfoResponse",
    "FilterableFieldsResponse",
    "ServiceSearchResponse",
    "ServiceScrollResponse",
    "ServiceAggregationResponse",
    "HostSearchResponse",
    "HostScrollResponse",
    "HostAggregationResponse",
    "SimilarIconResponse",
    "validate_quake_data"
]
