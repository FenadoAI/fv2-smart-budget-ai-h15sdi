"""Subscription, entitlements, bank integration, and Autopilot models."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import uuid


# ============= Subscription Models =============
class Subscription(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    tier: str = "free"  # free, pro, premium
    status: str = "active"  # active, trial, cancelled, expired, past_due
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    trial_ends_at: Optional[datetime] = None
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    cancel_at_period_end: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SubscriptionResponse(BaseModel):
    tier: str
    status: str
    current_period_end: Optional[datetime] = None
    cancel_at_period_end: bool
    trial_ends_at: Optional[datetime] = None


class CheckoutRequest(BaseModel):
    tier: str  # pro, premium
    billing_period: str = "monthly"  # monthly, annual


class CheckoutResponse(BaseModel):
    checkout_url: str
    session_id: str


class CancelRequest(BaseModel):
    cancel_at_period_end: bool = True


class UpgradeRequest(BaseModel):
    new_tier: str  # pro, premium


class UpgradeResponse(BaseModel):
    proration_amount: float
    effective_immediately: bool
    new_tier: str


class EntitlementsResponse(BaseModel):
    tier: str
    status: str
    features: Dict[str, Any]
    usage: Dict[str, Any]
    limits: Dict[str, Any]


# ============= Bank Integration Models =============
class BankConnection(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    institution_name: str
    institution_id: str
    access_token_encrypted: str  # AES-256 encrypted Plaid access token
    item_id: str  # Plaid item_id
    status: str = "active"  # active, reconnect_required, error
    accounts: List[Dict] = Field(default_factory=list)
    last_sync_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class LinkTokenRequest(BaseModel):
    pass  # No body needed


class LinkTokenResponse(BaseModel):
    link_token: str
    expiration: datetime


class ExchangePublicTokenRequest(BaseModel):
    public_token: str


class ExchangePublicTokenResponse(BaseModel):
    connection_id: str
    accounts: List[Dict]


class BankConnectionResponse(BaseModel):
    connection_id: str
    institution_name: str
    accounts: List[Dict]
    last_sync: Optional[datetime]
    status: str


class SyncResponse(BaseModel):
    transactions_added: int
    balances_updated: int
    last_sync: datetime


# ============= Autopilot Models =============
class AutopilotRule(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    rule_name: str
    mode: str  # conservative, balanced, experimental
    enabled: bool = False
    condition: Dict
    action: Dict
    simulation_results: Optional[Dict] = None
    execution_log: List[Dict] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    approved_by_user: bool = False


class SimulateRequest(BaseModel):
    scenario: str  # job_loss, market_dip, big_purchase, windfall
    mode: str = "balanced"  # conservative, balanced, experimental


class SimulationScenario(BaseModel):
    outcome: str
    probability: float
    recommended_actions: List[str]
    final_balance: float
    goal_completion_rate: float


class SimulateResponse(BaseModel):
    scenarios: List[SimulationScenario]
    median_final_balance: float
    worst_case_balance: float
    best_case_balance: float


class CreateRuleRequest(BaseModel):
    rule_name: str
    condition: Dict
    action: Dict
    mode: str = "balanced"


class CreateRuleResponse(BaseModel):
    rule_id: str
    simulation_results: Dict


class ApproveRuleRequest(BaseModel):
    approved: bool


class RollbackRequest(BaseModel):
    reason: str


class RollbackResponse(BaseModel):
    rolled_back: bool
    refunded_amount: float


class AuditLogEntry(BaseModel):
    execution_id: str
    rule_name: str
    executed_at: datetime
    amount: float
    result: str
    rollback_available: bool
    rollback_until: Optional[datetime]


# ============= Enhanced Report Models =============
class EnhancedReportRequest(BaseModel):
    report_type: str = "monthly_summary"  # monthly_summary, tax_summary, investment_performance
    format: str = "pdf"  # pdf, csv, excel
    start_date: str
    end_date: str
    include_sections: List[str] = Field(default_factory=lambda: ["transactions", "budget", "goals"])


class EnhancedReportResponse(BaseModel):
    report_url: str
    expires_at: datetime
    report_type: str
    format: str
