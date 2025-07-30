"""
Shared client configuration models for Verbaflo.

This package provides Pydantic models for configuring various aspects of the Verbaflo platform,
including client configurations, widget settings, communication channels, and more.
"""

try:
    from importlib.metadata import version
    __version__ = version("vf-config-model")
except ImportError:
    __version__ = "unknown"

# Main configuration models
from .client_config_models import (
    ClientConfig,
    ClientConfigResponse,
    WidgetConfig,
    WidgetConfigResponse,
    WidgetConfigInput,
    TenantChannelClientConfig,
)

# Common models and enums
from .commons.models.common_models import (
    LeadStage,
    RoomType,
    LevelOfStudy,
    Currency,
)

# Constants and enums
from .constants.constants import (
    BillingType,
    Channel,
)

# Feature-specific models
from .client_config_models import (
    KAMConfig,
    Contact,
    LLMConfig,
    CallConfig,
    EmailConfig,
    WhatsappConfig,
    MFAConfig,
    FeatureConfig,
    DashboardConfig,
    QuestionnaireConfig,
    CampaignConfig,
    Billing,
    Verticals,
    Languages,
)

# Utility models
from .client_config_models import (
    BudgetFlow,
    FilterOperator,
    FormFieldType,
    PopupMessagePosition,
    QuestionnaireType,
    Industry,
    MFAType,
)

__all__ = [
    # Version
    "__version__",
    
    # Main configs
    "ClientConfig",
    "ClientConfigResponse",
    "WidgetConfig",
    "WidgetConfigResponse",
    "WidgetConfigInput",
    "TenantChannelClientConfig",
    
    # Common models
    "LeadStage",
    "RoomType",
    "LevelOfStudy",
    "Currency",
    
    # Constants
    "BillingType",
    "Channel",
    
    # Feature configs
    "KAMConfig",
    "Contact",
    "LLMConfig",
    "CallConfig",
    "EmailConfig",
    "WhatsappConfig",
    "MFAConfig",
    "FeatureConfig",
    "DashboardConfig",
    "QuestionnaireConfig",
    "CampaignConfig",
    "Billing",
    "Verticals",
    "Languages",
    
    # Utility models
    "BudgetFlow",
    "FilterOperator",
    "FormFieldType",
    "PopupMessagePosition",
    "QuestionnaireType",
    "Industry",
    "MFAType",
]
