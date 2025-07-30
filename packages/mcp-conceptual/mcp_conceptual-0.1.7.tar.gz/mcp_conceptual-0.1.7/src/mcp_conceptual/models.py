"""Pydantic models for Conceptual API responses."""

from datetime import date, datetime
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field


class MoneyMetric(BaseModel):
    amount: float
    formatted: str


class PercentageMetric(BaseModel):
    value: float
    formatted: str


class ConversionData(BaseModel):
    type: str
    count: int
    value: float
    is_primary: bool


class CacAnalysis(BaseModel):
    primary_cac: Optional[MoneyMetric] = None
    confidence_status: Literal["high_confidence", "medium_confidence", "low_confidence"]
    performance_indicator: Literal[
        "exceeding_target", "meeting_target", "below_target", "poor_performance", "no_conversions"
    ]


class KeywordMetaData(BaseModel):
    keyword_type: Literal["keyword", "search_term", "unknown"]
    match_type: Optional[str] = None
    quality_score: Optional[int] = Field(None, ge=1, le=10)
    keyword_id: Optional[str] = None


class KeywordPerformanceMetrics(BaseModel):
    cost: MoneyMetric
    clicks: int
    impressions: int
    ctr: PercentageMetric
    cpc: MoneyMetric


class KeywordPerformance(BaseModel):
    keyword: str
    campaign_name: Optional[str] = None
    ad_group_name: Optional[str] = None
    performance: KeywordPerformanceMetrics
    conversions: List[ConversionData]
    cac_analysis: CacAnalysis
    meta: KeywordMetaData


class CreativeStatusInfo(BaseModel):
    value: str
    display: str
    is_active: bool
    is_paused: bool
    color: Literal["green", "yellow", "red", "gray"]


class CampaignInfo(BaseModel):
    id: str
    name: str


class AdSetInfo(BaseModel):
    id: str
    name: str


class CreativeAssets(BaseModel):
    primary_text: Optional[str] = None
    headline: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    call_to_action: Optional[str] = None
    creative_type: Literal["image", "video", "carousel", "text"]


class CreativeConversions(BaseModel):
    total: int
    breakdown: List[Dict[str, Union[str, int]]]


class CreativeMetricsDetailed(BaseModel):
    cpm: MoneyMetric
    cpc: MoneyMetric
    ctr: PercentageMetric
    conversion_rate: PercentageMetric
    cost_per_conversion: MoneyMetric


class CreativePerformanceMetrics(BaseModel):
    spend: MoneyMetric
    impressions: int
    clicks: int
    conversions: CreativeConversions
    reach: int
    frequency: float
    metrics: CreativeMetricsDetailed


class CreativeDates(BaseModel):
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    start_time: Optional[datetime] = None
    stop_time: Optional[datetime] = None


class CreativeActions(BaseModel):
    can_pause: bool
    can_activate: bool
    can_edit: bool


class TargetingInfo(BaseModel):
    age_min: Optional[int] = None
    age_max: Optional[int] = None
    genders: Optional[str] = None
    locations: Optional[List[str]] = None
    interests: Optional[List[str]] = None
    behaviors: Optional[List[str]] = None
    placements: Optional[List[str]] = None


class OptimizationInfo(BaseModel):
    optimization_goal: Optional[str] = None
    bid_strategy: Optional[str] = None
    budget_type: Optional[str] = None
    learning_stage: Optional[str] = None
    delivery_status: Optional[str] = None


class CreativePerformance(BaseModel):
    id: str
    name: str
    status: CreativeStatusInfo
    campaign: CampaignInfo
    ad_set: AdSetInfo
    creative_assets: CreativeAssets
    performance: CreativePerformanceMetrics
    dates: CreativeDates
    platform: str
    actions: CreativeActions
    targeting: TargetingInfo
    optimization: OptimizationInfo


class CustomerInfo(BaseModel):
    id: int
    name: str
    meta_id: Optional[int] = None


class DatePeriod(BaseModel):
    start_date: date
    end_date: date


class PaginationInfo(BaseModel):
    total_records: int
    returned_records: int
    offset: int
    limit: int


class KeywordMeta(BaseModel):
    customer: CustomerInfo
    period: DatePeriod
    view_type: str
    advanced_mode: bool
    pagination: PaginationInfo
    cache_expires_at: datetime


class CreativeMeta(BaseModel):
    customer: CustomerInfo
    platform: str
    attribution_window: str
    period: DatePeriod
    filters: Dict[str, Any]
    pagination: PaginationInfo


class ApiResponse(BaseModel):
    code: int
    message: str


class KeywordResponse(ApiResponse):
    data: List[KeywordPerformance]
    meta: KeywordMeta


class CreativeResponse(ApiResponse):
    data: List[CreativePerformance]
    meta: CreativeMeta


class ManualKeywordsInfo(BaseModel):
    info: str
    usage: str
    example: Dict[str, Any]


class CampaignContentInfo(BaseModel):
    info: str
    usage: str
    available_actions: Dict[str, str]


class InfoMeta(BaseModel):
    customer: CustomerInfo
    view_type: str
    note: str


class ManualKeywordsResponse(ApiResponse):
    data: ManualKeywordsInfo
    meta: InfoMeta


class CampaignContentResponse(ApiResponse):
    data: CampaignContentInfo
    meta: InfoMeta


class CreativeStatus(BaseModel):
    creative_id: str
    status: str
    last_updated: Optional[datetime] = None


class CreativeStatusResponse(ApiResponse):
    data: CreativeStatus


class CreativeStatusUpdate(BaseModel):
    creative_id: str
    previous_status: Optional[str] = None
    new_status: str
    updated_at: datetime


class CreativeStatusUpdateResponse(ApiResponse):
    data: CreativeStatusUpdate


class ErrorResponse(ApiResponse):
    error: str
    errors: Optional[Dict[str, List[str]]] = None