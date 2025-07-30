from typing import List, Dict, Optional, Any, Union

from enum import Enum

from utility.utils import current_utc_time
from pydantic import BaseModel, Field, field_validator, ConfigDict, EmailStr
import datetime
from commons.models.common_models import LeadStage, RoomType, LevelOfStudy, Currency
from constants.constants import Channel
from constants.constants import BillingType


class BudgetFlow(str, Enum):
    upselling = "upselling"
    downselling = "downselling"
    any = "any"


class FilterOperator(str, Enum):
    less_than_or_equal = "less_than_or_equal"
    greater_than_or_equal = "greater_than_or_equal"
    less_than = "less_than"
    greater_than = "greater_than"
    range = "range"
    equals = "equals"
    in_ = "in"
    not_in = "not_in"


class Contact(BaseModel):
    name: str
    profile_picture: Optional[str] = None
    email: str
    phone: str
    position: str
    department: str
    meeting_link: Optional[str] = None


class KAMConfig(BaseModel):
    primary_contact: Contact
    escalation_matrix: List[Contact]


class StagePattern(BaseModel):
    whatsapp: List[int]
    email: List[int]
    call: List[int]

    def __getitem__(self, key: str) -> List[int]:
        return getattr(self, key)


class CommunicationLock(BaseModel):
    chat_locked: bool = True
    call_locked: bool = False
    mail_locked: bool = False
    whatsapp_locked: bool = False


class FeatureLock(BaseModel):
    billing_locked: bool = Field(default=True)


class MultiFAQConfig(BaseModel):
    enabled: bool = Field(default=False)


class PlaygroundConfig(BaseModel):
    enabled: bool = Field(default=False)
    allowed_roles: List[str] = Field(default=[])


class DashboardConfig(BaseModel):
    communication_lock: CommunicationLock = Field(default_factory=CommunicationLock)
    feature_lock: FeatureLock = Field(default_factory=FeatureLock)
    multi_faq_config: MultiFAQConfig = Field(default_factory=MultiFAQConfig)
    playground_config: Optional[PlaygroundConfig] = Field(default_factory=PlaygroundConfig)


# use this to make a field translatable
def TranslatableField(default: Any = None, **kwargs):
    return Field(default=default, json_schema_extra={"should_translate": True}, **kwargs)


class ChannelModalityConfig(BaseModel):
    enabled: bool = Field(default=False)
    cta: str = TranslatableField()
    message: str = TranslatableField()


class CallModalityConfig(ChannelModalityConfig):
    cta: str = TranslatableField(default="Call Us")
    message: str = TranslatableField(default="Prefer to speak over the phone? Tap below to call us.")


class MailModalityConfig(ChannelModalityConfig):
    cta: str = TranslatableField(default="Send Email")
    message: str = TranslatableField(default="Got questions? Send us an email and we'll reply soon!")


class WhatsappModalityConfig(ChannelModalityConfig):
    cta: str = TranslatableField(default="Open Whatsapp")
    message: str = TranslatableField(default="Want to chat on WhatsApp? Tap below to start the conversation.")


class ModalityConfig(BaseModel):
    chat_enabled: bool = Field(default=True)
    call: CallModalityConfig = Field(default_factory=CallModalityConfig)
    mail: MailModalityConfig = Field(default_factory=MailModalityConfig)
    whatsapp: WhatsappModalityConfig = Field(default_factory=WhatsappModalityConfig)


class LanguageDropdownTexts(BaseModel):
    placeholder: str = TranslatableField(default="Search Language")
    popular_label: str = TranslatableField(default="Popular languages")
    all_label: str = TranslatableField(default="All languages")
    results_label: str = TranslatableField(default="Search results")


class AttemptPattern(BaseModel):
    created: StagePattern
    contacted: StagePattern
    processing: StagePattern
    lost: StagePattern

    def __getitem__(self, key: str) -> StagePattern:
        if isinstance(key, LeadStage):
            key = key.value
        return getattr(self, key)


class BudgetConfig(BaseModel):
    delta: float = Field(default=0.1)
    category: BudgetFlow = Field(default=BudgetFlow.any)


class SortingConfig(BaseModel):
    field: str = Field(default="price")
    order: str = Field(default="asc")


class PropertyDataConfig(BaseModel):
    cards: List[str] = Field(
        default=[
            "property_id",
            "configuration_id",
            "property_name",
            "room_name",
            "kind",
            "apartment",
            "available_from",
            "lease",
            "price",
            "image",
            "source_link",
        ]
    )
    llm: List[str] = Field(
        default=[
            "property_name",
            "room_name",
            "kind",
            "apartment",
            "available_from",
            "lease",
            "price",
            "occupants",
            "deposit",
            "installments",
            "utility_fee",
            "apartment",
            "dual_occupancy",
            "bed_type",
            "area",
        ]
    )


class BaseFilter(BaseModel):
    use: bool = Field(default=False)
    minor_filter: bool = Field(default=False)
    operator: FilterOperator = Field(default=FilterOperator.equals)


class PropertyFilterConfig(BaseModel):
    geo_filter: BaseFilter = Field(default_factory=BaseFilter)
    manager_name: BaseFilter = Field(default_factory=BaseFilter)
    city: BaseFilter = Field(default_factory=BaseFilter)
    country: BaseFilter = Field(default_factory=BaseFilter)
    property_names: BaseFilter = Field(default_factory=BaseFilter)
    nearby_places: BaseFilter = Field(default_factory=BaseFilter)
    nearby_universities: BaseFilter = Field(default_factory=BaseFilter)
    room_types: BaseFilter = Field(default_factory=BaseFilter)
    budget: BaseFilter = Field(default_factory=BaseFilter)
    duration: BaseFilter = Field(default_factory=BaseFilter)
    move_in_date: BaseFilter = Field(default_factory=BaseFilter)
    lease: BaseFilter = Field(default_factory=BaseFilter)
    tenant_type: BaseFilter = Field(default_factory=BaseFilter)
    academic_year: BaseFilter = Field(default_factory=BaseFilter)
    room_names: BaseFilter = Field(default_factory=BaseFilter)
    occupants: BaseFilter = Field(default_factory=BaseFilter)
    installments: BaseFilter = Field(default_factory=BaseFilter)
    sold_out: BaseFilter = Field(default_factory=BaseFilter)


class ScoringWeights(BaseModel):
    field: str
    weight: float


class FilterFields(BaseModel):
    field: str
    operator: List[FilterOperator] = Field(default_factory=list)


class PropertyRecommendationConfig(BaseModel):
    scoring_weights: List[ScoringWeights] = Field(default_factory=list)
    must_filters: List[FilterFields] = Field(default_factory=list)
    should_filters: List[FilterFields] = Field(default_factory=list)
    minimum_should_match: int = Field(default=1)
    group_by_property_name: bool = Field(default=True)


class RecommendationConfig(BaseModel):
    radius_filtering: int = Field(default=1000)
    page_size: int = Field(default=3)
    sorting: List[SortingConfig] = Field(default=[])
    budget: BudgetConfig = Field(default_factory=BudgetConfig)
    show_in_cards: bool = Field(default=False)
    academic_year_split: bool = Field(default=False)
    property_filter_config: Dict[str, BaseFilter] = Field(default_factory=dict)
    property_data_config: PropertyDataConfig = Field(default_factory=PropertyDataConfig)
    property_recommendation_config: PropertyRecommendationConfig = Field(default_factory=PropertyRecommendationConfig)


class FlagConfig(BaseModel):
    tag: bool = Field(default=True)
    conversation: bool = Field(default=True)
    summary: bool = Field(default=True)
    lead_data: bool = Field(default=True)


class LLMConfig(BaseModel):
    country_name: str
    assistant_name: str
    service_down_message: Optional[str] = None
    retry_limit: int = 5
    recommendation_config: RecommendationConfig = Field(default_factory=RecommendationConfig)
    flag_config: FlagConfig = Field(default_factory=FlagConfig)


class TicketConfig(BaseModel):
    ticket_list_url: str
    ticket_post_url: str


class FormFieldType(str, Enum):
    email = "email"
    phone = "phone"
    text = "text"
    dropdown = "dropdown"


class FormField(BaseModel):
    code: str = TranslatableField()
    name: str = TranslatableField()
    mandatory: bool
    type: FormFieldType
    values: Optional[List[str]] = None


class FormFields(BaseModel):
    enabled: bool
    title: str = TranslatableField(default="Please fill in the form below before starting the chat")
    fields: List[FormField]
    start_chatting_text: str = TranslatableField(default="Start Chatting")


class QuestionnaireType(str, Enum):
    rating = "rating"
    input = "input"


class QuestionnaireHeader(BaseModel):
    header: str = TranslatableField(default="Hey! How did we do?")
    sub_header: str = TranslatableField(default="Help us improve our service by rating your experience")
    feedback_submit_button: str = TranslatableField(default="Submit Feedback")
    feedback_skip_button: str = TranslatableField(default="Skip")
    submission_header: str = TranslatableField(default="Thank you for your feedback")
    submission_sub_header: str = TranslatableField(default="This will help us improve")
    submit_button: str = TranslatableField(default="Start New Chat")
    skip_button: str = TranslatableField(default="Close")


class Questionnaire(BaseModel):
    question: str = TranslatableField()
    placeholder: str = TranslatableField(default="Please type your feedback")
    type: QuestionnaireType = Field(default=QuestionnaireType.rating)


class QuestionnaireConfig(BaseModel):
    enabled: bool = Field(default=False)
    questions: List[Questionnaire] = Field(default=[])
    headers: QuestionnaireHeader = Field(default_factory=QuestionnaireHeader)

class AgentConfig(BaseModel):
    default_agent_id: str

class ChatBoxInput(BaseModel):
    is_enabled: bool = Field(default=True)
    placeholder_text: str = TranslatableField(default="Type your message here")
    error_message: str = TranslatableField(default="Message cannot exceed 1000 characters")


class WelcomeMessage(BaseModel):
    original_message: str = TranslatableField(default="Hi there!")
    translated_message: str = Field(default="Hi there!")


class CommunicationRedirects(BaseModel):
    phone: str = TranslatableField(default="Call Us")
    chat: str = TranslatableField(default="Let's chat")


class PopupMessagePosition(str, Enum):
    left = "left"
    right = "right"
    top = "top"
    bottom = "bottom"


class WidgetConfig(BaseModel):
    model_config = ConfigDict(json_encoders={datetime.datetime: lambda v: v.isoformat()}, validate_assignment=True)

    bot_name: str
    client_name: str
    header_name: str
    expires_at: datetime.datetime
    client_logo_url: str
    user_profile_icon: str
    client_profile_icon: str
    accent_color: str
    client_widget_icon: str
    welcome_messages: WelcomeMessage = Field(default_factory=WelcomeMessage)
    suggested_questions: List[str] = TranslatableField()
    online_text: str = TranslatableField(default="Online")
    new_chat_text: str = TranslatableField(default="New Chat")
    alert_sound: List[str]
    open_delay: int
    selected_alert_sound: str
    terms_and_conditions: str
    quick_replies_enabled: bool = False
    modality_config: Optional[ModalityConfig] = Field(default_factory=ModalityConfig)
    typing_delay: Optional[int] = 0
    nudge_delay: int = 0
    form_fields: FormFields = Field(default_factory=lambda: FormFields(enabled=False, fields=[]))
    initial_chat_box_input: bool = True
    chat_box_input: ChatBoxInput = Field(default_factory=ChatBoxInput)
    phone_delay: Optional[int] = -1
    popup_message: Optional[str] = TranslatableField(default="Hi there!")
    popup_message_position: Optional[PopupMessagePosition] = Field(default=PopupMessagePosition.left)
    communication_redirects_enabled: bool = Field(default=False)
    communication_redirects_background_colour: str = Field(default="#F67E35")
    communication_redirects: CommunicationRedirects = Field(default_factory=CommunicationRedirects)
    questionnaire_config: QuestionnaireConfig = Field(default_factory=QuestionnaireConfig)
    language_dropdown_texts: LanguageDropdownTexts = Field(default_factory=LanguageDropdownTexts)
    joined_chat_label: str = TranslatableField(default="joined the chat")
    reconnecting_label: str = TranslatableField(default="Reconnecting, please wait...")
    welcome_message: str = TranslatableField(default="Hi there!")
    

    @field_validator("expires_at", mode="before")
    def ensure_timezone_aware(cls, v: datetime.datetime | str) -> datetime.datetime:
        if isinstance(v, str):
            v = datetime.datetime.fromisoformat(v)
        if v.tzinfo is None:
            return v.replace(tzinfo=current_utc_time().tzinfo)
        return v

    @field_validator("accent_color", mode="before")
    def validate_accent_color(cls, v):
        if not v.startswith("#") or len(v) != 7 or not all(c in "0123456789ABCDEFabcdef" for c in v[1:]):
            raise ValueError("Accent color must be a valid hex color (e.g., #FF0000)")
        return v

    @field_validator("bot_name", "client_name", "header_name", "suggested_questions", mode="before")
    def validate_required_strings(cls, v: Union[str, List[str]]) -> Any:
        if isinstance(v, list):
            if not all(item and item.strip() != "" for item in v):
                raise ValueError("This field cannot be empty")
            return v
        if not v or v.strip() == "":
            raise ValueError("This field cannot be empty")
        return v.strip()

    @classmethod
    def get_field_types(cls) -> dict:
        """Get field types categorized by their Python types."""
        return {
            "string_fields": [field_name for field_name, field in cls.model_fields.items() if field.annotation == str],
            "list_fields": [field_name for field_name, field in cls.model_fields.items() if getattr(field.annotation, "__origin__", None) == list],
        }


class WidgetConfigResponse(WidgetConfig):
    whatsapp_link: Optional[str] = None
    call_link: Optional[str] = None
    email_link: Optional[str] = None


class VoiceAgentCost(BaseModel):
    value: float
    unit: str
    currency: str


class VoiceAgent(BaseModel):
    voice_id: str
    name: str
    accent: str
    age: str
    gender: str
    language: str
    voice_url: str
    cost: VoiceAgentCost
    voice_provider: Optional[str] = None

    class Config:
        example = {
            "voice_id": "123",
            "name": "John Doe",
            "accent": "American",
            "age": "middle-aged",
            "gender": "Male",
            "language": "English",
            "voice_url": "https://example.com/voice.mp3",
            "voice_provider": "aws",
        }


class EmailConfig(BaseModel):
    signature: str = Field(default="powered by verbaflo")
    blocked_emails: List[EmailStr] = Field(default_factory=list)
    blocked_domains: List[str] = Field(default_factory=list)


class CallConfig(BaseModel):
    assistant_name: str
    selected_voice_id: str
    selected_voice_provider: str


class CallConfigInput(BaseModel):
    assistant_name: Optional[str] = None
    selected_voice_id: Optional[str] = None
    selected_voice_provider: Optional[str] = None


class TemplateConfig(BaseModel):
    broadcast_name: Optional[str] = None
    template_name: Optional[str] = None
    student_template_name: Optional[str] = None
    professional_template_name: Optional[str] = None


class TemplateType(str, Enum):
    call = "call"


class WhatsappRateLimit(BaseModel):
    send_template_message_per_10_seconds: int = Field(default=30)
    send_template_message_per_day: int = Field(default=250)


class WhatsappConfig(BaseModel):
    assistant_name: str
    nudge_delay: int = 0
    quick_replies_enabled: bool = False
    suggested_questions: Optional[List[str]] = None
    whatsapp_initial_message: str = Field(default="Hi there! I'm interested in learning more about the accommodation options you offer.")
    whatsapp_rate_limit: WhatsappRateLimit = Field(default_factory=WhatsappRateLimit)
    template_config: List[Dict[TemplateType, TemplateConfig]] = Field(default_factory=list)


class WhatsappConfigInput(BaseModel):
    assistant_name: Optional[str] = None


class MFAType(Enum):
    EMAIL = "email"
    SMS = "sms"


class MFAConfig(BaseModel):
    mfa_enabled: bool
    mfa_type: MFAType


class CustomerFlow(BaseModel):
    enabled: bool = Field(default=False)


class InboundSales(BaseModel):
    enabled: bool = Field(default=True)
    subscribed_channels: Dict[Channel, bool] = Field(default_factory=dict)
    property_flow_version: int = Field(default=0)


class Verticals(BaseModel):
    customer: CustomerFlow = Field(default_factory=CustomerFlow)
    inbound_sales: InboundSales = Field(default_factory=InboundSales)


class ChannelMultiplier(BaseModel):
    per_session_cost: float


class PPUBasedOnSessions(BaseModel):
    chatbot: ChannelMultiplier
    email: ChannelMultiplier
    call: ChannelMultiplier
    wa: ChannelMultiplier


class PPUBasedOnConsumption(BaseModel):
    chatbot: ChannelMultiplier
    email: ChannelMultiplier
    call: ChannelMultiplier
    wa: ChannelMultiplier


class Billing(BaseModel):
    billing_model: BillingType
    ppu_based_on_sessions: Optional[PPUBasedOnSessions]
    ppu_based_on_consumption: Optional[PPUBasedOnConsumption]


class LeadDelete(BaseModel):
    enabled: bool = Field(default=False)
    allowed_roles: List[str] = Field(default=[])


class FeatureConfig(BaseModel):
    crm_update_enabled: bool = Field(default=False)
    auto_ai_enabled: bool = Field(default=False)


class Industry(str, Enum):
    PBSA = "pbsa"
    GUARANTOR = "guarantor"


class CampaignConfig(BaseModel):
    campaign_locked: bool = Field(default=True)
    allowed_roles: List[str] = Field(default=["vf-admin"])
    subscribed_channels: Dict[Channel, bool] = Field(default_factory=lambda: {Channel.WHATSAPP: False, Channel.EMAIL: False, Channel.CALL: False})


class Language(BaseModel):
    language: str = Field(default="en")
    name: str = Field(default="english")


class Languages(BaseModel):
    popular_languages: List[Language] = Field(default=[])
    other_languages: List[Language] = Field(default=[])


class ClientConfig(BaseModel):
    model_config = ConfigDict(json_encoders={datetime.datetime: lambda v: v.isoformat()})

    client_code: str
    client_name: str
    schedule_length: int = 15
    grace_period: int = 5
    grace_period_start_day: int = 10
    weekend_enabled: bool
    holidays: List[str]
    attempt_pattern: AttemptPattern
    preferred_timing_window: List[Dict[str, str]]
    ticket_config: Optional[TicketConfig] = None
    widget_config: WidgetConfig
    kam_config: Optional[KAMConfig] = None
    llm_config: LLMConfig
    room_types: Optional[List[RoomType]] = None
    level_of_study: Optional[List[LevelOfStudy]] = None
    analytics_dummy_data: Optional[Dict[str, Any]] = None
    valid_email_domains: Optional[List[str]] = Field(default=[])
    prop_configs: Optional[Dict[str, Any]] = None  # for_students: bool, for_non_students: bool
    user_email_notification: Optional[List[str]] = Field(default=[])
    voice_agents: Optional[List[VoiceAgent]] = Field(default=[])
    dashboard_config: DashboardConfig = Field(default_factory=DashboardConfig)
    call_config: CallConfig
    email_config: EmailConfig
    whatsapp_config: WhatsappConfig
    mfa_config: MFAConfig = Field(default_factory=lambda: MFAConfig(mfa_enabled=False, mfa_type=MFAType.EMAIL))
    feature_config: FeatureConfig = Field(default_factory=FeatureConfig)
    industry: List[Industry] = Field(default=[Industry.PBSA])
    verticals: Verticals = Field(default_factory=Verticals)
    lead_delete: Optional[LeadDelete] = Field(default_factory=LeadDelete)
    campaign_config: CampaignConfig = Field(default_factory=CampaignConfig)
    billing: Optional[Billing] = None
    multilingual_support: bool = Field(default=True)
    languages: Optional[Languages] = Field(default=None)
    default_currency: Currency = Field(default=Currency.GBP)
    agent_config: AgentConfig = Field(default_factory=lambda: AgentConfig(default_agent_id=""))


class WidgetConfigInput(BaseModel):
    bot_name: Optional[str] = None
    client_name: Optional[str] = None
    header_name: Optional[str] = None
    accent_color: Optional[str] = None
    welcome_message: Optional[str] = None
    suggested_questions: Optional[List[str]] = None
    selected_alert_sound: Optional[str] = None
    terms_and_conditions: Optional[str] = None


class ClientConfigResponse(BaseModel):
    model_config = ConfigDict(json_encoders={datetime.datetime: lambda v: v.isoformat()})

    client_code: str
    client_name: str
    preferred_timing_window: List[Dict[str, str]]
    ticket_config: Optional[TicketConfig] = None
    widget_config: WidgetConfig
    kam_config: Optional[KAMConfig] = None
    llm_config: LLMConfig
    room_types: Optional[List[RoomType]] = None
    level_of_study: Optional[List[LevelOfStudy]] = None
    analytics_dummy_data: Optional[Dict[str, Any]] = None
    valid_email_domains: Optional[List[str]] = Field(default=[])
    prop_configs: Optional[Dict[str, Any]] = None  # for_students: bool, for_non_students: bool
    user_email_notification: Optional[List[str]] = Field(default=[])
    voice_agents: Optional[List[VoiceAgent]] = Field(default=[])
    dashboard_config: DashboardConfig = Field(default_factory=DashboardConfig)
    call_config: CallConfig
    email_config: EmailConfig
    whatsapp_config: WhatsappConfig
    mfa_config: MFAConfig = Field(default_factory=lambda: MFAConfig(mfa_enabled=False, mfa_type=MFAType.EMAIL))
    lead_delete: Optional[LeadDelete] = Field(default_factory=LeadDelete)
    campaign_config: CampaignConfig = Field(default_factory=CampaignConfig)
    questionnaire_config: QuestionnaireConfig = Field(default_factory=QuestionnaireConfig)


class TenantChannelClientConfig(WidgetConfigResponse):
    languages: Optional[Languages] = Field(default_factory=Languages)
