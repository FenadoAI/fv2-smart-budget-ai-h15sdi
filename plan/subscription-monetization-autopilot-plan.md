# Subscription, Monetization & Autopilot Implementation Plan

## Requirement ID: fv2-smart-budget-ai-h15sdi (Subscription Enhancement)

## Executive Summary
Transform the AI personal finance assistant into a premium SaaS product with:
1. **3-tier subscription model** (Free, Pro ₹399/mo, Premium ₹999/mo)
2. **Stripe billing integration** with trial handling and proration
3. **Bank API integrations** (Plaid/SaltEdge) for real-time data sync
4. **"Autopilot: Your Financial Twin"** - AI-powered autonomous financial assistant with Monte Carlo simulations and auto-execution rules

## 1. Subscription Tiers & Entitlements

### Free Tier
- Manual transaction entry
- Limited AI insights (basic budget generation)
- CSV upload (max 1/week)
- Access to community tips
- Basic dashboard

### Pro Tier (₹399/mo or ₹3,999/year - save 17%)
- **30-day free trial**
- Automated CSV imports (unlimited)
- Deeper AI insights (contextual explanations, multi-month trends)
- **Full Goal Tracking** (unlimited goals, progress bars, auto-contributions)
- Weekly health reports
- Smart Alerts (custom threshold rules)
- Basic Export & Reports (PDF monthly summary)
- Priority email support

### Premium Tier (₹999/mo or ₹9,999/year - save 17%)
- **Everything in Pro, plus:**
- **Direct Bank API integrations** (Plaid/SaltEdge real-time sync)
- **Investment portfolio tracking** (link brokerage accounts)
- **Tax planning summaries** (AI-generated tax optimization)
- **Advanced reporting** (custom date ranges, CSV/PDF/Excel exports)
- **Autopilot: Your Financial Twin** (AI simulations + auto-execution)
- Automated bill negotiation concierge
- Priority chat support (24/7)

## 2. Entitlements Schema

```json
{
  "user_id": "uuid",
  "subscription_tier": "free|pro|premium",
  "subscription_status": "active|trial|cancelled|expired",
  "trial_ends_at": "ISO8601",
  "subscription_period_start": "ISO8601",
  "subscription_period_end": "ISO8601",
  "stripe_customer_id": "cus_xxx",
  "stripe_subscription_id": "sub_xxx",
  "features": {
    "csv_upload_limit_per_week": 1|999,
    "goal_limit": 1|999,
    "ai_insights_depth": "basic|advanced|premium",
    "bank_sync_enabled": false|true,
    "autopilot_enabled": false|true,
    "export_formats": ["pdf"]|["pdf","csv","excel"],
    "support_tier": "email|priority_email|24x7_chat"
  },
  "usage": {
    "csv_uploads_this_week": 0,
    "goals_count": 0,
    "bank_accounts_linked": 0
  }
}
```

## 3. Backend Implementation

### 3.1 Database Collections

**subscriptions** collection:
```python
{
  "_id": ObjectId,
  "user_id": str,
  "tier": "free|pro|premium",
  "status": "active|trial|cancelled|expired|past_due",
  "stripe_customer_id": str,
  "stripe_subscription_id": str,
  "trial_ends_at": datetime,
  "current_period_start": datetime,
  "current_period_end": datetime,
  "cancel_at_period_end": bool,
  "created_at": datetime,
  "updated_at": datetime
}
```

**bank_connections** collection:
```python
{
  "_id": ObjectId,
  "user_id": str,
  "institution_name": str,
  "institution_id": str,
  "access_token_encrypted": str,  # AES-256 encrypted
  "item_id": str,  # Plaid item_id
  "status": "active|reconnect_required|error",
  "accounts": [{
    "account_id": str,
    "name": str,
    "type": "checking|savings|investment",
    "subtype": str,
    "current_balance": float,
    "available_balance": float,
    "last_synced_at": datetime
  }],
  "last_sync_at": datetime,
  "created_at": datetime
}
```

**autopilot_rules** collection:
```python
{
  "_id": ObjectId,
  "user_id": str,
  "rule_name": str,
  "mode": "conservative|balanced|experimental",
  "enabled": bool,
  "condition": {
    "type": "paycheck_surplus|spending_spike|goal_underfunded",
    "threshold": float,
    "parameters": {}
  },
  "action": {
    "type": "sweep_to_goal|round_up_invest|freeze_subscription|alert",
    "target_account": str,
    "parameters": {}
  },
  "simulation_results": {
    "success_probability": float,
    "estimated_impact": float,
    "risk_level": "low|medium|high"
  },
  "execution_log": [{
    "executed_at": datetime,
    "amount": float,
    "result": "success|failed",
    "rollback_available_until": datetime
  }],
  "created_at": datetime,
  "approved_by_user": bool
}
```

### 3.2 API Endpoints

#### Billing & Subscriptions
```python
POST /api/billing/checkout
  Body: {tier: "pro|premium", billing_period: "monthly|annual"}
  Returns: {checkout_url: str, session_id: str}

GET /api/billing/subscription
  Returns: {tier, status, current_period_end, cancel_at_period_end, ...}

POST /api/billing/cancel
  Body: {cancel_at_period_end: bool}
  Returns: {status: "cancelled", effective_date: datetime}

POST /api/billing/upgrade
  Body: {new_tier: "pro|premium"}
  Returns: {proration_amount: float, effective_immediately: bool}

POST /api/billing/webhook
  Body: Stripe webhook payload
  Handles: subscription.created, subscription.updated, subscription.deleted,
           invoice.paid, invoice.payment_failed, customer.subscription.trial_will_end

GET /api/user/entitlements
  Returns: {tier, features, usage, limits}
```

#### Bank Integration
```python
POST /api/bank/create-link-token
  Returns: {link_token: str, expiration: datetime}

POST /api/bank/exchange-public-token
  Body: {public_token: str}
  Returns: {connection_id: str, accounts: [...]}

GET /api/bank/connections
  Returns: [{connection_id, institution_name, accounts, last_sync, status}]

POST /api/bank/sync/{connection_id}
  Returns: {transactions_added: int, balances_updated: int}

DELETE /api/bank/connection/{connection_id}
  Returns: {status: "deleted"}

GET /api/bank/transactions
  Query: ?start_date=...&end_date=...&connection_id=...
  Returns: [{transaction_id, date, description, amount, category, ...}]
```

#### Autopilot
```python
POST /api/autopilot/simulate
  Body: {scenario: "job_loss|market_dip|big_purchase", mode: "conservative|balanced|experimental"}
  Returns: {scenarios: [{outcome, probability, recommended_actions}]}

POST /api/autopilot/create-rule
  Body: {rule_name, condition, action, mode}
  Returns: {rule_id, simulation_results}

GET /api/autopilot/rules
  Returns: [{rule_id, rule_name, enabled, mode, simulation_results, execution_log}]

PUT /api/autopilot/rule/{rule_id}
  Body: {enabled: bool, ...}
  Returns: {rule_id, updated_fields}

POST /api/autopilot/approve/{rule_id}
  Body: {approved: bool}
  Returns: {rule_id, approved_by_user, status}

DELETE /api/autopilot/rule/{rule_id}
  Returns: {status: "deleted"}

POST /api/autopilot/rollback/{execution_id}
  Body: {reason: str}
  Returns: {rolled_back: bool, refunded_amount: float}

GET /api/autopilot/audit-log
  Returns: [{execution_id, rule_name, executed_at, amount, result, rollback_available}]
```

#### Enhanced Reports
```python
POST /api/reports/generate
  Body: {
    report_type: "monthly_summary|tax_summary|investment_performance",
    format: "pdf|csv|excel",
    start_date: "YYYY-MM-DD",
    end_date: "YYYY-MM-DD",
    include_sections: ["transactions", "budget", "goals", "autopilot_actions"]
  }
  Returns: {report_url: str, expires_at: datetime}
  Gated: Pro (PDF only), Premium (all formats + custom dates)
```

### 3.3 Entitlement Middleware

```python
from functools import wraps
from fastapi import HTTPException, Depends

async def get_user_entitlements(user_id: str, db):
    subscription = await db.subscriptions.find_one({"user_id": user_id})
    if not subscription:
        return {"tier": "free", "status": "active"}
    return subscription

def require_tier(minimum_tier: str):
    """Decorator to gate endpoints by subscription tier"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user_id = kwargs.get('user_id') or kwargs.get('current_user').id
            entitlements = await get_user_entitlements(user_id, kwargs.get('db'))

            tier_hierarchy = {"free": 0, "pro": 1, "premium": 2}
            user_tier = tier_hierarchy.get(entitlements.get("tier", "free"), 0)
            required_tier = tier_hierarchy.get(minimum_tier, 0)

            if user_tier < required_tier:
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "feature_gated",
                        "message": f"This feature requires {minimum_tier.title()} subscription",
                        "current_tier": entitlements.get("tier"),
                        "required_tier": minimum_tier,
                        "upgrade_url": "/pricing"
                    }
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator

# Usage:
@app.post("/api/bank/create-link-token")
@require_tier("premium")
async def create_plaid_link_token(user_id: str, db: AsyncIOMotorClient):
    ...
```

## 4. Frontend Implementation

### 4.1 Component Architecture

#### PricingTable.js
- 3-column responsive layout (stacks on mobile)
- Feature comparison grid
- "Most Popular" badge on Pro
- Annual/Monthly toggle with savings indicator
- CTA buttons: "Current Plan" | "Start Free Trial" | "Upgrade Now"
- Tooltips on premium features

#### UpgradeModal.js
- Triggered when user hits gated feature
- Shows "Unlock [Feature Name]" header
- Displays current vs required tier
- Feature benefit list (3-5 bullets)
- CTA: "Start 30-Day Free Trial" or "Upgrade to [Tier]"
- "Learn More" link to pricing page

#### BankConnectFlow.js
- Step 1: Privacy & Security explainer modal
- Step 2: Plaid Link integration (OAuth iframe)
- Step 3: Account selection checkboxes
- Step 4: Sync in progress (loading state)
- Step 5: Success confirmation with account list
- Error state: Reconnection required banner

#### AutopilotSetupWizard.js
- Step 1: Welcome & explainer video/animation
- Step 2: Mode selection (Conservative/Balanced/Experimental)
- Step 3: Rule builder (condition + action selectors)
- Step 4: Simulation preview (Monte Carlo results visualization)
- Step 5: Opt-in confirmation with legal disclaimer
- Step 6: Success & rule monitoring dashboard

#### SubscriptionManagement.js
- Current plan card with benefits
- Billing history table
- Payment method update
- Cancel/Pause subscription (with save offer)
- Upgrade/Downgrade CTAs with proration preview

### 4.2 New Pages

#### Pricing.js (`/pricing`)
- Hero: "Choose Your Financial Freedom Plan"
- 3-tier comparison table (PricingTable component)
- FAQ accordion (10-12 common questions)
- Trust indicators (user count, testimonials, security badges)
- Final CTA: "Start Your Free 30-Day Trial"

#### Subscription.js (`/dashboard/subscription`)
- SubscriptionManagement component
- Usage meters (CSV uploads, goals, bank accounts)
- Feature utilization stats
- Upgrade suggestions based on usage patterns

### 4.3 Dashboard Integration

#### Feature Gates
```jsx
// Example: Goal creation gate
{goals.length >= goalLimit && tier === 'free' && (
  <UpgradeModal
    feature="Unlimited Goals"
    currentTier="free"
    requiredTier="pro"
    benefits={[
      "Create unlimited savings goals",
      "Track progress with visual charts",
      "Auto-contribution recommendations"
    ]}
  />
)}
```

#### Upgrade CTAs
- Header: "Upgrade" button with sparkle icon (always visible for free/pro)
- After goal completion: "Reach your goals 3x faster with Autopilot"
- CSV upload limit: "You've used 1/1 CSV uploads this week. Upgrade for unlimited."
- Insights panel: "Unlock deeper AI analysis with Pro"

## 5. Autopilot: Your Financial Twin

### 5.1 Core Concept
AI-powered simulation engine that:
1. **Analyzes** user's real financial data (transactions, balances, goals, income patterns)
2. **Simulates** 1,000+ scenarios (job loss, market crash, windfall, big expense)
3. **Recommends** protective actions based on probability-weighted outcomes
4. **Executes** approved rules automatically when conditions are met
5. **Monitors** continuously and adjusts rules based on new data

### 5.2 Autopilot Modes

#### Conservative Mode
- Focus: Risk minimization, emergency fund building
- Example rules:
  - "If paycheck > $X, sweep surplus into Emergency Goal until 6-month target"
  - "Alert if discretionary spending > 15% of income"
  - "Auto-pause recurring subscriptions if net worth drops 10%"

#### Balanced Mode
- Focus: Mix of savings + moderate investing
- Example rules:
  - "Round up transactions to nearest $10, invest in index ETF"
  - "If windfall > $500, allocate 50% savings / 50% investment"
  - "Auto-contribute 10% of bonus to retirement goal"

#### Experimental Mode
- Focus: Aggressive optimization, micro-investing, opportunistic actions
- Example rules:
  - "Auto-invest tax refund into thematic ETFs based on AI market analysis"
  - "Dynamic budget reallocation: shift unused dining budget to investments"
  - "Bill negotiation: auto-submit negotiation requests when contract renewals detected"

### 5.3 Simulation Engine

**Monte Carlo Implementation:**
```python
# Pseudocode
def run_autopilot_simulation(user_data, scenario, mode):
    results = []
    for _ in range(1000):
        simulated_future = simulate_n_months(
            starting_balance=user_data.current_balance,
            income_stream=perturb(user_data.avg_income),  # Add noise
            expense_stream=perturb(user_data.avg_expenses),
            scenario_event=scenario,  # e.g., "job_loss_month_3"
            autopilot_rules=generate_rules_for_mode(mode),
            duration_months=12
        )
        results.append({
            "final_balance": simulated_future.balance,
            "goal_completion": simulated_future.goals_met,
            "risk_events_survived": simulated_future.emergencies_handled
        })

    return {
        "median_final_balance": percentile(results, 50),
        "p10_final_balance": percentile(results, 10),  # Worst-case
        "p90_final_balance": percentile(results, 90),  # Best-case
        "goal_success_rate": mean([r.goal_completion for r in results]),
        "recommended_rules": rank_rules_by_impact(results)
    }
```

### 5.4 Rule Execution & Safety

**Approval Flow:**
1. User enables Autopilot mode
2. AI generates recommended rules based on simulation
3. User reviews each rule (shown with "Why?" explanation)
4. User approves or customizes rule
5. Rule becomes active only after explicit approval

**Execution Safeguards:**
- **Dry run first:** All new rules run in simulation-only mode for 7 days
- **Transaction limits:** Max $500/transaction unless user raises limit
- **24-hour rollback window:** All automated transfers can be reversed
- **Audit log:** Every action logged with timestamp, amount, reason
- **Kill switch:** User can pause all Autopilot actions instantly

**Regulatory Compliance:**
- Terms of Service explicit opt-in for automated transactions
- "Financial advice" disclaimer: "Autopilot is an optimization tool, not fiduciary advice"
- User retains full control and liability
- Data encryption: AES-256 for bank tokens, TLS for all API calls

### 5.5 Monetization Model

**Premium Feature:**
- Base: Included in Premium tier (₹999/mo)
- Add-on: ₹299/mo for Pro users (7-day trial)

**Future Revenue Streams:**
1. **Partner commissions:**
   - Brokerage account referrals (user opens investment account)
   - Bill negotiation service (take 20% of savings)
   - Credit card optimization (referral fees)

2. **Performance tiers:**
   - Premium Plus: ₹1,499/mo + 5% performance fee on investment gains above benchmark
   - Enterprise: Family plans, financial advisor co-pilot

## 6. Marketing Copy & Positioning

### Homepage Hero Update
**Headline:** "Your AI Financial Twin That Actually Takes Action"

**Subheadline:** "Not just insights—Autopilot runs 1,000+ simulations on your real finances and executes protective actions automatically. Save more, stress less."

**3 Key Benefits:**
1. 🤖 **Your Financial Twin** - AI that simulates job loss, market dips, and windfalls to protect your future
2. 🚀 **Auto-Execution** - Approved rules run automatically: sweep to savings, round-up investments, pause overspending
3. 🛡️ **Risk-Free** - 24-hour rollback on all actions, full audit logs, you're always in control

### Pricing Page Copy

**Free Tier:**
"Get Started with Smart Finance"
- Perfect for tracking basics and learning AI budgeting

**Pro Tier (Most Popular):**
"Unlock AI-Powered Insights & Goals"
- For serious savers who want automation and intelligence
- 30-day free trial, cancel anytime

**Premium Tier:**
"The Full Financial Command Center"
- Real-time bank sync + Autopilot = Hands-off wealth building
- Everything automated, nothing left to chance

### Autopilot Explainer (3 paragraphs)

**What is Autopilot?**
Autopilot is your AI-powered Financial Twin. It studies your income, spending, goals, and investments—then runs Monte Carlo simulations to predict how you'd handle job loss, market crashes, or unexpected windfalls. Based on 1,000+ scenarios, it recommends (and can execute) protective actions like sweeping surplus to emergency funds, round-up investing, or pausing subscriptions during spending spikes.

**How does it work?**
Choose your mode: Conservative (protect savings), Balanced (save + invest), or Experimental (aggressive optimization). Autopilot builds custom rules tailored to your finances. You review and approve each rule before it goes live. Once active, Autopilot monitors your accounts 24/7 and executes approved actions automatically—like transferring bonus money to your vacation goal or investing your tax refund. Every action is logged, reversible for 24 hours, and requires your explicit permission.

**Why it stands out:**
Unlike static budgets or passive alerts, Autopilot *acts* on your behalf. It's the difference between a fitness tracker (tells you to exercise) and a personal trainer (makes you do it). With bank integrations, real-time data, and AI decision-making, Autopilot turns your financial plan into a self-driving system. You set the destination; Autopilot handles the wheel.

## 7. Analytics & A/B Testing

### Event Tracking
```javascript
// Frontend analytics wrapper
trackEvent("pricing_page_view", {source: "dashboard_banner"})
trackEvent("upgrade_click", {from_tier: "free", to_tier: "pro", cta_location: "goal_limit_gate"})
trackEvent("trial_start", {tier: "pro", billing_period: "monthly"})
trackEvent("trial_convert", {tier: "pro", days_elapsed: 28})
trackEvent("bank_connect_success", {institution: "Chase", accounts_linked: 2})
trackEvent("autopilot_enable", {mode: "balanced", rules_approved: 3})
trackEvent("autopilot_execution", {rule_id: "xyz", amount: 150, result: "success"})
trackEvent("churn_event", {tier: "pro", reason: "too_expensive", tenure_days: 45})
```

### A/B Test Ideas
1. **Trial length:** 14-day vs 30-day free trial (hypothesis: longer trial = higher conversion)
2. **Pricing anchor:** Show crossed-out "regular price" vs no anchor (test value perception)
3. **CTA copy:** "Start Free Trial" vs "Try Pro Free for 30 Days" (specificity test)
4. **Autopilot positioning:** Lead with Autopilot vs lead with bank sync (feature prioritization)
5. **Annual discount:** 2 months free vs "17% off" (framing test)

## 8. Implementation Checklist

### Backend
- [ ] Stripe integration (checkout, webhooks, subscription management)
- [ ] Subscription & entitlements schema + MongoDB collections
- [ ] Entitlement middleware for all gated endpoints
- [ ] Plaid integration (link token, exchange, sync, webhooks)
- [ ] Bank connection encryption (AES-256 for tokens)
- [ ] Autopilot simulation engine (Monte Carlo)
- [ ] Autopilot rule creation & execution logic
- [ ] Enhanced export/reports with premium formats
- [ ] Analytics event logging

### Frontend
- [ ] PricingTable component (3-tier, responsive)
- [ ] UpgradeModal component (feature gates + CTAs)
- [ ] BankConnectFlow component (Plaid Link integration)
- [ ] AutopilotSetupWizard component (mode selection, rule builder)
- [ ] SubscriptionManagement page (billing, cancel, upgrade)
- [ ] Pricing page (`/pricing`)
- [ ] Upgrade CTAs in dashboard (banners, buttons, modals)
- [ ] Feature gates throughout app (goals, reports, insights)
- [ ] Analytics tracking wrapper

### Testing
- [ ] Stripe sandbox checkout flow (monthly, annual, trial)
- [ ] Subscription webhook handling (trial_end, payment_failed, cancelled)
- [ ] Entitlement gating (free user tries premium feature)
- [ ] Plaid sandbox bank connection (link, sync, error states)
- [ ] Autopilot simulation (run 1000 iterations, verify results)
- [ ] Autopilot rule execution (dry run, live execution, rollback)
- [ ] Proration logic (upgrade mid-cycle)

## 9. Pricing Structure (Editable)

| Tier | Monthly | Annual | Trial | Discount |
|------|---------|--------|-------|----------|
| Free | ₹0 | ₹0 | N/A | N/A |
| Pro | ₹399 | ₹3,999 | 30 days | 17% (2 months free) |
| Premium | ₹999 | ₹9,999 | 7 days | 17% (2 months free) |

**Stripe Product IDs (Sandbox):**
- pro_monthly: `price_xxxxx`
- pro_annual: `price_xxxxx`
- premium_monthly: `price_xxxxx`
- premium_annual: `price_xxxxx`

## 10. Success Metrics

**North Star Metric:** Monthly Recurring Revenue (MRR)

**Key Metrics:**
- Trial-to-paid conversion rate (target: >40%)
- Free-to-Pro upgrade rate (target: >10% within 90 days)
- Pro-to-Premium upgrade rate (target: >20% within 6 months)
- Churn rate (target: <5% monthly)
- Autopilot adoption (target: >60% of Premium users enable within 30 days)
- Bank connection success rate (target: >80% first-attempt)

**Feature Engagement:**
- Autopilot rules created per user (target: 3+ average)
- Autopilot executions per month (target: 5+ average)
- Bank sync frequency (target: 2x/week average)
- Report exports per Premium user (target: 1+ per month)

---

## Timeline: 2-3 Days
- Day 1: Backend (Stripe, entitlements, Plaid stubs, Autopilot simulation)
- Day 2: Frontend (PricingTable, UpgradeModal, BankConnectFlow, AutopilotSetupWizard)
- Day 3: Integration testing, homepage updates, product one-pager
