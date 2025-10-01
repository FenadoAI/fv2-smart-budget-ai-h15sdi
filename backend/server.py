"""FastAPI server exposing AI agent endpoints."""

import csv
import io
import logging
import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional

import bcrypt
import jwt
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request, UploadFile, File
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, EmailStr, Field
from starlette.middleware.cors import CORSMiddleware

from ai_agents.agents import AgentConfig, ChatAgent, SearchAgent
from subscription_models import (
    Subscription, SubscriptionResponse, CheckoutRequest, CheckoutResponse,
    CancelRequest, UpgradeRequest, UpgradeResponse, EntitlementsResponse,
    LinkTokenResponse, ExchangePublicTokenRequest, ExchangePublicTokenResponse,
    BankConnectionResponse, SyncResponse, BankConnection,
    SimulateRequest, SimulateResponse, CreateRuleRequest, CreateRuleResponse,
    ApproveRuleRequest, RollbackRequest, RollbackResponse, AuditLogEntry,
    AutopilotRule, EnhancedReportRequest, EnhancedReportResponse
)
from entitlements import get_entitlements, require_tier, require_feature
from autopilot_engine import AutopilotEngine


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).parent

JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
security = HTTPBearer()

# Stripe Configuration
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY", "")

# Plaid Configuration
PLAID_CLIENT_ID = os.getenv("PLAID_CLIENT_ID", "")
PLAID_SECRET = os.getenv("PLAID_SECRET_SANDBOX", "")
PLAID_ENV = os.getenv("PLAID_ENV", "sandbox")

# Initialize Autopilot engine
autopilot_engine = AutopilotEngine()


# ============= Auth Models =============
class UserSignup(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    email: str
    hashed_password: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    created_at: datetime


class AuthResponse(BaseModel):
    success: bool
    token: Optional[str] = None
    user: Optional[UserResponse] = None
    error: Optional[str] = None


# ============= Transaction Models =============
class TransactionCreate(BaseModel):
    date: str
    description: str
    amount: float
    category: Optional[str] = None
    type: str  # "income" or "expense"


class Transaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    date: str
    description: str
    amount: float
    category: Optional[str] = None
    type: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ============= Budget Models =============
class BudgetAnalysis(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    month: int
    year: int
    analysis: str
    savings_opportunities: List[str]
    total_income: float
    total_expenses: float
    spending_by_category: dict
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BudgetRequest(BaseModel):
    month: Optional[int] = None
    year: Optional[int] = None


class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class StatusCheckCreate(BaseModel):
    client_name: str


class ChatRequest(BaseModel):
    message: str
    agent_type: str = "chat"
    context: Optional[dict] = None


class ChatResponse(BaseModel):
    success: bool
    response: str
    agent_type: str
    capabilities: List[str]
    metadata: dict = Field(default_factory=dict)
    error: Optional[str] = None


class SearchRequest(BaseModel):
    query: str
    max_results: int = 5


class SearchResponse(BaseModel):
    success: bool
    query: str
    summary: str
    search_results: Optional[dict] = None
    sources_count: int
    error: Optional[str] = None


# ============= Financial Chat Models =============
class FinancialChatRequest(BaseModel):
    message: str
    context_type: Optional[str] = "auto"  # auto, transactions, budget, goals


class FinancialChatResponse(BaseModel):
    success: bool
    response: str
    suggestions: List[str] = Field(default_factory=list)
    context_used: List[str] = Field(default_factory=list)
    error: Optional[str] = None


# ============= Goal Models =============
class GoalCreate(BaseModel):
    title: str
    target_amount: float
    current_amount: float = 0
    deadline: Optional[str] = None
    category: Optional[str] = None


class Goal(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    title: str
    target_amount: float
    current_amount: float
    deadline: Optional[str] = None
    category: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class GoalProgress(BaseModel):
    goal_id: str
    percentage: float
    remaining_amount: float
    days_left: Optional[int] = None
    on_track: bool


# ============= Insight Models =============
class InsightRequest(BaseModel):
    period_type: str = "monthly"  # weekly, monthly


class InsightReport(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    period_type: str
    start_date: str
    end_date: str
    summary: str
    trends: dict
    recommendations: List[str]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ============= Alert Models =============
class AlertRuleCreate(BaseModel):
    rule_type: str  # threshold, subscription, pattern
    threshold_amount: Optional[float] = None
    category: Optional[str] = None
    enabled: bool = True


class AlertRule(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    rule_type: str
    threshold_amount: Optional[float] = None
    category: Optional[str] = None
    enabled: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TriggeredAlert(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    rule_id: str
    user_id: str
    message: str
    triggered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    acknowledged: bool = False


# ============= Gamification Models =============
class UserStats(BaseModel):
    user_id: str
    current_streak: int = 0
    longest_streak: int = 0
    total_transactions: int = 0
    badges_earned: List[str] = Field(default_factory=list)
    last_activity_date: Optional[str] = None


class Badge(BaseModel):
    id: str
    name: str
    description: str
    icon: str
    criteria: str
    rarity: str  # common, rare, epic, legendary


class Achievement(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    badge_id: str
    unlocked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ============= Report Models =============
class ReportRequest(BaseModel):
    format: str  # pdf, excel
    period_start: str
    period_end: str
    include_sections: List[str] = Field(default_factory=lambda: ["transactions", "budget", "insights"])


def _ensure_db(request: Request):
    try:
        return request.app.state.db
    except AttributeError as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=503, detail="Database not ready") from exc


def _get_agent_cache(request: Request) -> Dict[str, object]:
    if not hasattr(request.app.state, "agent_cache"):
        request.app.state.agent_cache = {}
    return request.app.state.agent_cache


async def _get_or_create_agent(request: Request, agent_type: str):
    cache = _get_agent_cache(request)
    if agent_type in cache:
        return cache[agent_type]

    config: AgentConfig = request.app.state.agent_config

    if agent_type == "search":
        cache[agent_type] = SearchAgent(config)
    elif agent_type == "chat":
        cache[agent_type] = ChatAgent(config)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown agent type '{agent_type}'")

    return cache[agent_type]


# ============= Auth Helpers =============
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def create_token(user_id: str, username: str) -> str:
    payload = {
        "user_id": user_id,
        "username": username,
        "exp": datetime.now(timezone.utc) + timedelta(days=7)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), request: Request = None):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id")

        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        db = _ensure_db(request)
        user_data = await db.users.find_one({"id": user_id})

        if not user_data:
            raise HTTPException(status_code=401, detail="User not found")

        return User(**user_data)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_dotenv(ROOT_DIR / ".env")

    mongo_url = os.getenv("MONGO_URL")
    db_name = os.getenv("DB_NAME")

    if not mongo_url or not db_name:
        missing = [name for name, value in {"MONGO_URL": mongo_url, "DB_NAME": db_name}.items() if not value]
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")

    client = AsyncIOMotorClient(mongo_url)

    try:
        app.state.mongo_client = client
        app.state.db = client[db_name]
        app.state.agent_config = AgentConfig()
        app.state.agent_cache = {}
        logger.info("AI Agents API starting up")
        yield
    finally:
        client.close()
        logger.info("AI Agents API shutdown complete")


app = FastAPI(
    title="AI Agents API",
    description="Minimal AI Agents API with LangGraph and MCP support",
    lifespan=lifespan,
)

api_router = APIRouter(prefix="/api")


@api_router.get("/")
async def root():
    return {"message": "AI Finance Assistant API"}


# ============= Auth Endpoints =============
@api_router.post("/auth/signup", response_model=AuthResponse)
async def signup(user_data: UserSignup, request: Request):
    try:
        db = _ensure_db(request)

        # Validate input
        if not user_data.username or not user_data.username.strip():
            return AuthResponse(success=False, error="Username is required")

        if not user_data.email or not user_data.email.strip():
            return AuthResponse(success=False, error="Email is required")

        if not user_data.password:
            return AuthResponse(success=False, error="Password is required")

        if len(user_data.password) < 6:
            return AuthResponse(success=False, error="Password must be at least 6 characters")

        if len(user_data.username.strip()) < 3:
            return AuthResponse(success=False, error="Username must be at least 3 characters")

        # Check if username exists
        existing_username = await db.users.find_one({"username": user_data.username})
        if existing_username:
            return AuthResponse(success=False, error="Username already exists")

        # Check if email exists
        existing_email = await db.users.find_one({"email": user_data.email})
        if existing_email:
            return AuthResponse(success=False, error="Email already exists")

        # Create user
        user = User(
            username=user_data.username.strip(),
            email=user_data.email.strip().lower(),
            hashed_password=hash_password(user_data.password)
        )

        await db.users.insert_one(user.model_dump())

        # Generate token
        token = create_token(user.id, user.username)

        return AuthResponse(
            success=True,
            token=token,
            user=UserResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                created_at=user.created_at
            )
        )
    except Exception as exc:
        logger.exception("Error in signup")
        return AuthResponse(success=False, error="An error occurred during signup. Please try again.")


@api_router.post("/auth/login", response_model=AuthResponse)
async def login(login_data: UserLogin, request: Request):
    try:
        db = _ensure_db(request)

        # Validate input
        if not login_data.username or not login_data.username.strip():
            return AuthResponse(success=False, error="Username is required")

        if not login_data.password:
            return AuthResponse(success=False, error="Password is required")

        # Find user
        user_data = await db.users.find_one({"username": login_data.username.strip()})
        if not user_data:
            return AuthResponse(success=False, error="Invalid username or password")

        user = User(**user_data)

        # Verify password
        if not verify_password(login_data.password, user.hashed_password):
            return AuthResponse(success=False, error="Invalid username or password")

        # Generate token
        token = create_token(user.id, user.username)

        return AuthResponse(
            success=True,
            token=token,
            user=UserResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                created_at=user.created_at
            )
        )
    except Exception as exc:
        logger.exception("Error in login")
        return AuthResponse(success=False, error="An error occurred during login. Please try again.")


@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        created_at=current_user.created_at
    )


# ============= Transaction Endpoints =============
@api_router.post("/transactions", response_model=Transaction)
async def create_transaction(
    transaction_data: TransactionCreate,
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    try:
        db = _ensure_db(request)

        transaction = Transaction(
            user_id=current_user.id,
            **transaction_data.model_dump()
        )

        await db.transactions.insert_one(transaction.model_dump())
        return transaction
    except Exception as exc:
        logger.exception("Error creating transaction")
        raise HTTPException(status_code=500, detail=str(exc))


@api_router.get("/transactions", response_model=List[Transaction])
async def get_transactions(
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    try:
        db = _ensure_db(request)
        transactions = await db.transactions.find({"user_id": current_user.id}).sort("date", -1).to_list(1000)
        return [Transaction(**t) for t in transactions]
    except Exception as exc:
        logger.exception("Error getting transactions")
        raise HTTPException(status_code=500, detail=str(exc))


@api_router.delete("/transactions/{transaction_id}")
async def delete_transaction(
    transaction_id: str,
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    try:
        db = _ensure_db(request)
        result = await db.transactions.delete_one({"id": transaction_id, "user_id": current_user.id})

        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Transaction not found")

        return {"success": True, "message": "Transaction deleted"}
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error deleting transaction")
        raise HTTPException(status_code=500, detail=str(exc))


@api_router.post("/transactions/upload")
async def upload_transactions(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    try:
        db = _ensure_db(request)

        # Read CSV file
        content = await file.read()
        csv_data = io.StringIO(content.decode())
        reader = csv.DictReader(csv_data)

        transactions = []
        for row in reader:
            # Parse CSV row - flexible format
            date = row.get("Date") or row.get("date") or row.get("DATE")
            description = row.get("Description") or row.get("description") or row.get("DESCRIPTION")
            amount_str = row.get("Amount") or row.get("amount") or row.get("AMOUNT")
            category = row.get("Category") or row.get("category") or row.get("CATEGORY") or None

            if not date or not description or not amount_str:
                continue

            try:
                amount = float(amount_str.replace("$", "").replace(",", ""))
            except ValueError:
                continue

            transaction_type = "income" if amount > 0 else "expense"

            transaction = Transaction(
                user_id=current_user.id,
                date=date,
                description=description,
                amount=abs(amount),
                category=category,
                type=transaction_type
            )
            transactions.append(transaction.model_dump())

        if transactions:
            await db.transactions.insert_many(transactions)

        return {"success": True, "count": len(transactions), "message": f"Uploaded {len(transactions)} transactions"}
    except Exception as exc:
        logger.exception("Error uploading transactions")
        raise HTTPException(status_code=500, detail=str(exc))


@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate, request: Request):
    db = _ensure_db(request)
    status_obj = StatusCheck(**input.model_dump())
    await db.status_checks.insert_one(status_obj.model_dump())
    return status_obj


@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks(request: Request):
    db = _ensure_db(request)
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]


@api_router.post("/chat", response_model=ChatResponse)
async def chat_with_agent(chat_request: ChatRequest, request: Request):
    try:
        agent = await _get_or_create_agent(request, chat_request.agent_type)
        response = await agent.execute(chat_request.message)

        return ChatResponse(
            success=response.success,
            response=response.content,
            agent_type=chat_request.agent_type,
            capabilities=agent.get_capabilities(),
            metadata=response.metadata,
            error=response.error,
        )
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Error in chat endpoint")
        return ChatResponse(
            success=False,
            response="",
            agent_type=chat_request.agent_type,
            capabilities=[],
            error=str(exc),
        )


@api_router.post("/search", response_model=SearchResponse)
async def search_and_summarize(search_request: SearchRequest, request: Request):
    try:
        search_agent = await _get_or_create_agent(request, "search")
        search_prompt = (
            f"Search for information about: {search_request.query}. "
            "Provide a comprehensive summary with key findings."
        )
        result = await search_agent.execute(search_prompt, use_tools=True)

        if result.success:
            metadata = result.metadata or {}
            return SearchResponse(
                success=True,
                query=search_request.query,
                summary=result.content,
                search_results=metadata,
                sources_count=int(metadata.get("tool_run_count", metadata.get("tools_used", 0)) or 0),
            )

        return SearchResponse(
            success=False,
            query=search_request.query,
            summary="",
            sources_count=0,
            error=result.error,
        )
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Error in search endpoint")
        return SearchResponse(
            success=False,
            query=search_request.query,
            summary="",
            sources_count=0,
            error=str(exc),
        )


@api_router.get("/agents/capabilities")
async def get_agent_capabilities(request: Request):
    try:
        search_agent = await _get_or_create_agent(request, "search")
        chat_agent = await _get_or_create_agent(request, "chat")

        return {
            "success": True,
            "capabilities": {
                "search_agent": search_agent.get_capabilities(),
                "chat_agent": chat_agent.get_capabilities(),
            },
        }
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Error getting capabilities")
        return {"success": False, "error": str(exc)}


# ============= Budget Analysis Endpoints =============
@api_router.post("/budget/generate", response_model=BudgetAnalysis)
async def generate_budget(
    budget_request: BudgetRequest,
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    try:
        db = _ensure_db(request)

        # Get current month/year if not specified
        now = datetime.now(timezone.utc)
        month = budget_request.month or now.month
        year = budget_request.year or now.year

        # Get transactions for the specified month
        transactions = await db.transactions.find({"user_id": current_user.id}).to_list(1000)

        # Filter transactions by month/year
        month_transactions = []
        for t in transactions:
            try:
                # Parse date (support multiple formats)
                date_str = t.get("date", "")
                if "-" in date_str:
                    parts = date_str.split("-")
                    t_year = int(parts[0])
                    t_month = int(parts[1])
                elif "/" in date_str:
                    parts = date_str.split("/")
                    t_month = int(parts[0])
                    t_year = int(parts[2])
                else:
                    continue

                if t_year == year and t_month == month:
                    month_transactions.append(t)
            except (ValueError, IndexError):
                continue

        if not month_transactions:
            raise HTTPException(status_code=400, detail="No transactions found for the specified month")

        # Calculate totals
        total_income = sum(t["amount"] for t in month_transactions if t["type"] == "income")
        total_expenses = sum(t["amount"] for t in month_transactions if t["type"] == "expense")

        # Group by category
        spending_by_category = {}
        for t in month_transactions:
            category = t.get("category") or "Uncategorized"
            if t["type"] == "expense":
                spending_by_category[category] = spending_by_category.get(category, 0) + t["amount"]

        # Prepare AI prompt
        transactions_text = "\n".join([
            f"- {t['date']}: {t['description']} - ${t['amount']:.2f} ({t['type']}) [{t.get('category', 'Uncategorized')}]"
            for t in month_transactions
        ])

        prompt = f"""You are a personal finance advisor for young professionals. Analyze the following transactions for {month}/{year}:

{transactions_text}

Summary:
- Total Income: ${total_income:.2f}
- Total Expenses: ${total_expenses:.2f}
- Net: ${total_income - total_expenses:.2f}

Spending by Category:
{chr(10).join([f'- {cat}: ${amt:.2f}' for cat, amt in spending_by_category.items()])}

Please provide:
1. A personalized monthly budget analysis (2-3 paragraphs)
2. Top 3-5 actionable savings opportunities (be specific based on the data)
3. Practical advice for this young professional

Focus on identifying recurring subscriptions, overspending categories, and realistic ways to improve their financial habits."""

        # Get AI analysis
        chat_agent = await _get_or_create_agent(request, "chat")
        result = await chat_agent.execute(prompt)

        if not result.success:
            raise HTTPException(status_code=500, detail="Failed to generate budget analysis")

        # Parse savings opportunities from AI response
        savings_opportunities = []
        lines = result.content.split("\n")
        in_savings_section = False
        for line in lines:
            if "savings" in line.lower() or "opportunities" in line.lower():
                in_savings_section = True
                continue
            if in_savings_section and line.strip().startswith(("-", "•", "1.", "2.", "3.", "4.", "5.")):
                savings_opportunities.append(line.strip().lstrip("-•123456789. "))

        if not savings_opportunities:
            # Fallback savings opportunities
            if spending_by_category:
                top_category = max(spending_by_category.items(), key=lambda x: x[1])
                savings_opportunities.append(f"Review spending in {top_category[0]} (${top_category[1]:.2f})")
            savings_opportunities.append("Track daily expenses to identify small unnecessary purchases")
            savings_opportunities.append("Set up automatic savings transfers")

        # Create budget analysis
        budget = BudgetAnalysis(
            user_id=current_user.id,
            month=month,
            year=year,
            analysis=result.content,
            savings_opportunities=savings_opportunities[:5],
            total_income=total_income,
            total_expenses=total_expenses,
            spending_by_category=spending_by_category
        )

        await db.budgets.insert_one(budget.model_dump())
        return budget

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error generating budget")
        raise HTTPException(status_code=500, detail=str(exc))


@api_router.get("/budget/latest", response_model=BudgetAnalysis)
async def get_latest_budget(
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    try:
        db = _ensure_db(request)
        budget_data = await db.budgets.find_one(
            {"user_id": current_user.id},
            sort=[("created_at", -1)]
        )

        if not budget_data:
            raise HTTPException(status_code=404, detail="No budget found")

        return BudgetAnalysis(**budget_data)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error getting latest budget")
        raise HTTPException(status_code=500, detail=str(exc))


@api_router.get("/budget/history", response_model=List[BudgetAnalysis])
async def get_budget_history(
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    try:
        db = _ensure_db(request)
        budgets = await db.budgets.find({"user_id": current_user.id}).sort("created_at", -1).to_list(100)
        return [BudgetAnalysis(**b) for b in budgets]
    except Exception as exc:
        logger.exception("Error getting budget history")
        raise HTTPException(status_code=500, detail=str(exc))


# ============= Financial Chat Endpoints =============
@api_router.post("/chat/financial", response_model=FinancialChatResponse)
async def financial_chat(
    chat_request: FinancialChatRequest,
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    try:
        db = _ensure_db(request)
        context_used = []
        context_text = ""

        # Gather user context
        transactions = await db.transactions.find({"user_id": current_user.id}).sort("date", -1).limit(50).to_list(50)
        if transactions:
            context_used.append("recent_transactions")
            total_income = sum(t["amount"] for t in transactions if t["type"] == "income")
            total_expenses = sum(t["amount"] for t in transactions if t["type"] == "expense")
            context_text += f"\nUser's Recent Financial Data:\n"
            context_text += f"- Total Income: ${total_income:.2f}\n"
            context_text += f"- Total Expenses: ${total_expenses:.2f}\n"
            context_text += f"- Net: ${total_income - total_expenses:.2f}\n"

        budget = await db.budgets.find_one({"user_id": current_user.id}, sort=[("created_at", -1)])
        if budget:
            context_used.append("budget_analysis")
            context_text += f"\nLatest Budget Analysis ({budget['month']}/{budget['year']}):\n"
            context_text += f"- Top spending categories: {', '.join(list(budget['spending_by_category'].keys())[:3])}\n"

        goals = await db.goals.find({"user_id": current_user.id}).to_list(10)
        if goals:
            context_used.append("goals")
            context_text += f"\nActive Goals: {len(goals)}\n"

        # Create financial advisor prompt
        system_prompt = f"""You are a friendly personal finance assistant for {current_user.username}.
Provide helpful, actionable financial advice based on their data. Be conversational, encouraging, and specific.
{context_text}

User's question: {chat_request.message}

Provide a clear, helpful response and suggest 2-3 actionable next steps."""

        chat_agent = await _get_or_create_agent(request, "chat")
        result = await chat_agent.execute(system_prompt)

        if not result.success:
            return FinancialChatResponse(
                success=False,
                response="I'm having trouble processing your request. Please try again.",
                error=result.error
            )

        # Extract suggestions (simple heuristic)
        suggestions = [
            "View your budget analysis",
            "Set a savings goal",
            "Review spending by category"
        ]

        return FinancialChatResponse(
            success=True,
            response=result.content,
            suggestions=suggestions,
            context_used=context_used
        )

    except Exception as exc:
        logger.exception("Error in financial chat")
        return FinancialChatResponse(
            success=False,
            response="An error occurred. Please try again.",
            error=str(exc)
        )


# ============= Goal Tracking Endpoints =============
@api_router.post("/goals", response_model=Goal)
async def create_goal(
    goal_data: GoalCreate,
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    try:
        db = _ensure_db(request)
        goal = Goal(user_id=current_user.id, **goal_data.model_dump())
        await db.goals.insert_one(goal.model_dump())
        return goal
    except Exception as exc:
        logger.exception("Error creating goal")
        raise HTTPException(status_code=500, detail=str(exc))


@api_router.get("/goals", response_model=List[Goal])
async def get_goals(
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    try:
        db = _ensure_db(request)
        goals = await db.goals.find({"user_id": current_user.id}).sort("created_at", -1).to_list(100)
        return [Goal(**g) for g in goals]
    except Exception as exc:
        logger.exception("Error getting goals")
        raise HTTPException(status_code=500, detail=str(exc))


@api_router.put("/goals/{goal_id}", response_model=Goal)
async def update_goal(
    goal_id: str,
    goal_data: GoalCreate,
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    try:
        db = _ensure_db(request)
        result = await db.goals.update_one(
            {"id": goal_id, "user_id": current_user.id},
            {"$set": goal_data.model_dump()}
        )
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Goal not found")

        updated_goal = await db.goals.find_one({"id": goal_id})
        return Goal(**updated_goal)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error updating goal")
        raise HTTPException(status_code=500, detail=str(exc))


@api_router.delete("/goals/{goal_id}")
async def delete_goal(
    goal_id: str,
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    try:
        db = _ensure_db(request)
        result = await db.goals.delete_one({"id": goal_id, "user_id": current_user.id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Goal not found")
        return {"success": True, "message": "Goal deleted"}
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error deleting goal")
        raise HTTPException(status_code=500, detail=str(exc))


@api_router.get("/goals/{goal_id}/progress", response_model=GoalProgress)
async def get_goal_progress(
    goal_id: str,
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    try:
        db = _ensure_db(request)
        goal_data = await db.goals.find_one({"id": goal_id, "user_id": current_user.id})
        if not goal_data:
            raise HTTPException(status_code=404, detail="Goal not found")

        goal = Goal(**goal_data)
        percentage = (goal.current_amount / goal.target_amount * 100) if goal.target_amount > 0 else 0
        remaining = goal.target_amount - goal.current_amount

        days_left = None
        on_track = True
        if goal.deadline:
            try:
                deadline_date = datetime.strptime(goal.deadline, "%Y-%m-%d")
                days_left = (deadline_date - datetime.now(timezone.utc)).days
                if days_left > 0:
                    required_daily = remaining / days_left if days_left > 0 else remaining
                    on_track = required_daily < (goal.target_amount / 30)  # Simple heuristic
            except ValueError:
                pass

        return GoalProgress(
            goal_id=goal_id,
            percentage=min(percentage, 100),
            remaining_amount=max(remaining, 0),
            days_left=days_left,
            on_track=on_track
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error calculating goal progress")
        raise HTTPException(status_code=500, detail=str(exc))


# ============= Insights Endpoints =============
@api_router.post("/insights/generate", response_model=InsightReport)
async def generate_insight(
    insight_request: InsightRequest,
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    try:
        db = _ensure_db(request)
        now = datetime.now(timezone.utc)

        # Calculate date range
        if insight_request.period_type == "weekly":
            start_date = (now - timedelta(days=7)).strftime("%Y-%m-%d")
            end_date = now.strftime("%Y-%m-%d")
        else:  # monthly
            start_date = now.replace(day=1).strftime("%Y-%m-%d")
            end_date = now.strftime("%Y-%m-%d")

        # Get transactions in period
        transactions = await db.transactions.find({"user_id": current_user.id}).to_list(1000)

        # Filter by date range (simple filter)
        period_transactions = [t for t in transactions if start_date <= t.get("date", "") <= end_date]

        if not period_transactions:
            raise HTTPException(status_code=400, detail="No transactions found for this period")

        # Calculate trends
        total_income = sum(t["amount"] for t in period_transactions if t["type"] == "income")
        total_expenses = sum(t["amount"] for t in period_transactions if t["type"] == "expense")

        category_spending = {}
        for t in period_transactions:
            if t["type"] == "expense":
                cat = t.get("category") or "Uncategorized"
                category_spending[cat] = category_spending.get(cat, 0) + t["amount"]

        trends = {
            "total_income": total_income,
            "total_expenses": total_expenses,
            "net": total_income - total_expenses,
            "top_categories": dict(sorted(category_spending.items(), key=lambda x: x[1], reverse=True)[:5])
        }

        # Generate AI summary
        prompt = f"""Analyze this {insight_request.period_type} financial data for {current_user.username}:

Period: {start_date} to {end_date}
- Income: ${total_income:.2f}
- Expenses: ${total_expenses:.2f}
- Net: ${total_income - total_expenses:.2f}
- Top spending categories: {', '.join([f'{k}: ${v:.2f}' for k, v in list(category_spending.items())[:3]])}

Provide a brief summary (2-3 sentences) and 3 specific recommendations."""

        chat_agent = await _get_or_create_agent(request, "chat")
        result = await chat_agent.execute(prompt)

        if not result.success:
            raise HTTPException(status_code=500, detail="Failed to generate insights")

        # Extract recommendations
        recommendations = [
            "Review your highest spending category",
            "Set up automatic savings transfers",
            "Track subscription renewals"
        ]

        insight = InsightReport(
            user_id=current_user.id,
            period_type=insight_request.period_type,
            start_date=start_date,
            end_date=end_date,
            summary=result.content,
            trends=trends,
            recommendations=recommendations
        )

        await db.insights.insert_one(insight.model_dump())
        return insight

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error generating insight")
        raise HTTPException(status_code=500, detail=str(exc))


@api_router.get("/insights/latest", response_model=InsightReport)
async def get_latest_insight(
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    try:
        db = _ensure_db(request)
        insight = await db.insights.find_one({"user_id": current_user.id}, sort=[("created_at", -1)])
        if not insight:
            raise HTTPException(status_code=404, detail="No insights found")
        return InsightReport(**insight)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error getting latest insight")
        raise HTTPException(status_code=500, detail=str(exc))


@api_router.get("/insights/history", response_model=List[InsightReport])
async def get_insight_history(
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    try:
        db = _ensure_db(request)
        insights = await db.insights.find({"user_id": current_user.id}).sort("created_at", -1).to_list(50)
        return [InsightReport(**i) for i in insights]
    except Exception as exc:
        logger.exception("Error getting insight history")
        raise HTTPException(status_code=500, detail=str(exc))


# ============= Alert Endpoints =============
@api_router.post("/alerts/rules", response_model=AlertRule)
async def create_alert_rule(
    rule_data: AlertRuleCreate,
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    try:
        db = _ensure_db(request)
        rule = AlertRule(user_id=current_user.id, **rule_data.model_dump())
        await db.alert_rules.insert_one(rule.model_dump())
        return rule
    except Exception as exc:
        logger.exception("Error creating alert rule")
        raise HTTPException(status_code=500, detail=str(exc))


@api_router.get("/alerts/rules", response_model=List[AlertRule])
async def get_alert_rules(
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    try:
        db = _ensure_db(request)
        rules = await db.alert_rules.find({"user_id": current_user.id}).to_list(100)
        return [AlertRule(**r) for r in rules]
    except Exception as exc:
        logger.exception("Error getting alert rules")
        raise HTTPException(status_code=500, detail=str(exc))


@api_router.put("/alerts/rules/{rule_id}", response_model=AlertRule)
async def update_alert_rule(
    rule_id: str,
    rule_data: AlertRuleCreate,
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    try:
        db = _ensure_db(request)
        result = await db.alert_rules.update_one(
            {"id": rule_id, "user_id": current_user.id},
            {"$set": rule_data.model_dump()}
        )
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Alert rule not found")

        updated_rule = await db.alert_rules.find_one({"id": rule_id})
        return AlertRule(**updated_rule)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error updating alert rule")
        raise HTTPException(status_code=500, detail=str(exc))


@api_router.delete("/alerts/rules/{rule_id}")
async def delete_alert_rule(
    rule_id: str,
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    try:
        db = _ensure_db(request)
        result = await db.alert_rules.delete_one({"id": rule_id, "user_id": current_user.id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Alert rule not found")
        return {"success": True, "message": "Alert rule deleted"}
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error deleting alert rule")
        raise HTTPException(status_code=500, detail=str(exc))


@api_router.get("/alerts/triggered", response_model=List[TriggeredAlert])
async def get_triggered_alerts(
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    try:
        db = _ensure_db(request)
        alerts = await db.triggered_alerts.find({"user_id": current_user.id, "acknowledged": False}).sort("triggered_at", -1).to_list(50)
        return [TriggeredAlert(**a) for a in alerts]
    except Exception as exc:
        logger.exception("Error getting triggered alerts")
        raise HTTPException(status_code=500, detail=str(exc))


@api_router.post("/alerts/acknowledge/{alert_id}")
async def acknowledge_alert(
    alert_id: str,
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    try:
        db = _ensure_db(request)
        result = await db.triggered_alerts.update_one(
            {"id": alert_id, "user_id": current_user.id},
            {"$set": {"acknowledged": True}}
        )
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Alert not found")
        return {"success": True, "message": "Alert acknowledged"}
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error acknowledging alert")
        raise HTTPException(status_code=500, detail=str(exc))


# ============= Gamification Endpoints =============
@api_router.get("/gamification/stats", response_model=UserStats)
async def get_user_stats(
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    try:
        db = _ensure_db(request)
        stats_data = await db.user_stats.find_one({"user_id": current_user.id})

        if not stats_data:
            # Create initial stats
            stats = UserStats(user_id=current_user.id)
            await db.user_stats.insert_one(stats.model_dump())
            return stats

        return UserStats(**stats_data)
    except Exception as exc:
        logger.exception("Error getting user stats")
        raise HTTPException(status_code=500, detail=str(exc))


@api_router.post("/gamification/check-streak")
async def check_streak(
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    try:
        db = _ensure_db(request)
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        stats_data = await db.user_stats.find_one({"user_id": current_user.id})
        if not stats_data:
            stats = UserStats(user_id=current_user.id, current_streak=1, longest_streak=1, last_activity_date=today)
            await db.user_stats.insert_one(stats.model_dump())
            return {"success": True, "streak": 1, "message": "Streak started!"}

        stats = UserStats(**stats_data)

        # Check if activity is today
        if stats.last_activity_date == today:
            return {"success": True, "streak": stats.current_streak, "message": "Already tracked today"}

        # Check if yesterday
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
        if stats.last_activity_date == yesterday:
            stats.current_streak += 1
            stats.longest_streak = max(stats.longest_streak, stats.current_streak)
        else:
            stats.current_streak = 1

        stats.last_activity_date = today

        await db.user_stats.update_one(
            {"user_id": current_user.id},
            {"$set": stats.model_dump()}
        )

        return {"success": True, "streak": stats.current_streak, "message": f"Streak: {stats.current_streak} days!"}
    except Exception as exc:
        logger.exception("Error checking streak")
        raise HTTPException(status_code=500, detail=str(exc))


@api_router.get("/gamification/badges", response_model=List[Badge])
async def get_badges():
    badges = [
        Badge(id="first_transaction", name="Getting Started", description="Add your first transaction", icon="🌱", criteria="1 transaction", rarity="common"),
        Badge(id="week_streak", name="Week Warrior", description="Track expenses for 7 days straight", icon="🔥", criteria="7 day streak", rarity="common"),
        Badge(id="month_streak", name="Monthly Master", description="Track expenses for 30 days straight", icon="⭐", criteria="30 day streak", rarity="rare"),
        Badge(id="goal_achiever", name="Goal Crusher", description="Complete your first savings goal", icon="🎯", criteria="Complete 1 goal", rarity="rare"),
        Badge(id="budget_pro", name="Budget Pro", description="Generate 5 budget analyses", icon="💰", criteria="5 budgets", rarity="epic"),
        Badge(id="savings_legend", name="Savings Legend", description="Save $1000 or more", icon="💎", criteria="$1000 saved", rarity="legendary"),
    ]
    return badges


@api_router.get("/gamification/achievements", response_model=List[Achievement])
async def get_achievements(
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    try:
        db = _ensure_db(request)
        achievements = await db.achievements.find({"user_id": current_user.id}).to_list(100)
        return [Achievement(**a) for a in achievements]
    except Exception as exc:
        logger.exception("Error getting achievements")
        raise HTTPException(status_code=500, detail=str(exc))


# ============= Export & Reports Endpoints =============
@api_router.post("/reports/generate")
async def generate_report(
    report_request: ReportRequest,
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    try:
        db = _ensure_db(request)

        # Get data for report
        transactions = await db.transactions.find({"user_id": current_user.id}).to_list(1000)
        budget = await db.budgets.find_one({"user_id": current_user.id}, sort=[("created_at", -1)])
        insights = await db.insights.find({"user_id": current_user.id}).sort("created_at", -1).limit(5).to_list(5)

        # Filter transactions by date range
        filtered_transactions = [
            t for t in transactions
            if report_request.period_start <= t.get("date", "") <= report_request.period_end
        ]

        report_data = {
            "user": current_user.username,
            "period": f"{report_request.period_start} to {report_request.period_end}",
            "transactions": filtered_transactions,
            "budget": budget,
            "insights": insights,
            "format": report_request.format
        }

        # For now, return data structure (PDF/Excel generation can be added later)
        return {
            "success": True,
            "message": f"Report data prepared in {report_request.format} format",
            "data": {
                "transaction_count": len(filtered_transactions),
                "total_income": sum(t["amount"] for t in filtered_transactions if t["type"] == "income"),
                "total_expenses": sum(t["amount"] for t in filtered_transactions if t["type"] == "expense"),
            }
        }
    except Exception as exc:
        logger.exception("Error generating report")
        raise HTTPException(status_code=500, detail=str(exc))


# ============= Subscription & Billing Endpoints =============
@api_router.get("/user/entitlements", response_model=EntitlementsResponse)
async def get_user_entitlements(
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    """Get user's subscription tier and entitlements."""
    try:
        db = _ensure_db(request)
        subscription = await db.subscriptions.find_one({"user_id": current_user.id})

        tier = "free"
        status = "active"
        if subscription:
            tier = subscription.get("tier", "free")
            status = subscription.get("status", "active")

        entitlements = get_entitlements(tier, status)

        # Get usage data
        csv_uploads_this_week = 0  # TODO: Implement actual tracking
        goals_count = await db.goals.count_documents({"user_id": current_user.id})
        bank_accounts = await db.bank_connections.count_documents({"user_id": current_user.id})

        return EntitlementsResponse(
            tier=tier,
            status=status,
            features=entitlements["features"],
            usage={
                "csv_uploads_this_week": csv_uploads_this_week,
                "goals_count": goals_count,
                "bank_accounts_linked": bank_accounts,
            },
            limits=entitlements["limits"],
        )
    except Exception as exc:
        logger.exception("Error getting entitlements")
        raise HTTPException(status_code=500, detail=str(exc))


@api_router.post("/billing/checkout", response_model=CheckoutResponse)
async def create_checkout_session(
    checkout_req: CheckoutRequest,
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    """Create Stripe checkout session for subscription."""
    try:
        # Stub implementation - requires actual Stripe integration
        # In production, use stripe.checkout.Session.create()

        session_id = f"cs_test_{uuid.uuid4()}"
        checkout_url = f"https://checkout.stripe.com/pay/{session_id}"

        return CheckoutResponse(checkout_url=checkout_url, session_id=session_id)
    except Exception as exc:
        logger.exception("Error creating checkout session")
        raise HTTPException(status_code=500, detail=str(exc))


@api_router.get("/billing/subscription", response_model=SubscriptionResponse)
async def get_subscription(
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    """Get user's current subscription details."""
    try:
        db = _ensure_db(request)
        subscription = await db.subscriptions.find_one({"user_id": current_user.id})

        if not subscription:
            return SubscriptionResponse(
                tier="free",
                status="active",
                cancel_at_period_end=False
            )

        return SubscriptionResponse(
            tier=subscription.get("tier", "free"),
            status=subscription.get("status", "active"),
            current_period_end=subscription.get("current_period_end"),
            cancel_at_period_end=subscription.get("cancel_at_period_end", False),
            trial_ends_at=subscription.get("trial_ends_at"),
        )
    except Exception as exc:
        logger.exception("Error getting subscription")
        raise HTTPException(status_code=500, detail=str(exc))


@api_router.post("/billing/cancel")
async def cancel_subscription(
    cancel_req: CancelRequest,
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    """Cancel subscription (immediate or at period end)."""
    try:
        db = _ensure_db(request)
        subscription = await db.subscriptions.find_one({"user_id": current_user.id})

        if not subscription:
            raise HTTPException(status_code=404, detail="No active subscription")

        # Update cancellation status
        await db.subscriptions.update_one(
            {"user_id": current_user.id},
            {"$set": {
                "cancel_at_period_end": cancel_req.cancel_at_period_end,
                "status": "cancelled" if not cancel_req.cancel_at_period_end else "active",
                "updated_at": datetime.now(timezone.utc),
            }}
        )

        effective_date = subscription.get("current_period_end") if cancel_req.cancel_at_period_end else datetime.now(timezone.utc)

        return {"status": "cancelled", "effective_date": effective_date}
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error cancelling subscription")
        raise HTTPException(status_code=500, detail=str(exc))


@api_router.post("/billing/upgrade", response_model=UpgradeResponse)
async def upgrade_subscription(
    upgrade_req: UpgradeRequest,
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    """Upgrade subscription to a higher tier."""
    try:
        db = _ensure_db(request)
        subscription = await db.subscriptions.find_one({"user_id": current_user.id})

        current_tier = "free"
        if subscription:
            current_tier = subscription.get("tier", "free")

        # Calculate proration (simplified)
        tier_prices = {"pro": 399, "premium": 999}
        proration = tier_prices.get(upgrade_req.new_tier, 0) - tier_prices.get(current_tier, 0)

        # Update subscription
        if subscription:
            await db.subscriptions.update_one(
                {"user_id": current_user.id},
                {"$set": {
                    "tier": upgrade_req.new_tier,
                    "status": "active",
                    "updated_at": datetime.now(timezone.utc),
                }}
            )
        else:
            # Create new subscription
            new_sub = Subscription(
                user_id=current_user.id,
                tier=upgrade_req.new_tier,
                status="trial",
                trial_ends_at=datetime.now(timezone.utc) + timedelta(days=30),
            )
            await db.subscriptions.insert_one(new_sub.model_dump())

        return UpgradeResponse(
            proration_amount=max(proration, 0),
            effective_immediately=True,
            new_tier=upgrade_req.new_tier,
        )
    except Exception as exc:
        logger.exception("Error upgrading subscription")
        raise HTTPException(status_code=500, detail=str(exc))


@api_router.post("/billing/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks for subscription events."""
    try:
        # Stub implementation - requires actual Stripe webhook verification
        payload = await request.json()
        event_type = payload.get("type", "")

        logger.info(f"Received Stripe webhook: {event_type}")

        # Handle different event types
        # subscription.created, subscription.updated, subscription.deleted,
        # invoice.paid, invoice.payment_failed, customer.subscription.trial_will_end

        return {"received": True}
    except Exception as exc:
        logger.exception("Error handling webhook")
        raise HTTPException(status_code=500, detail=str(exc))


# ============= Bank Integration Endpoints =============
@api_router.post("/bank/create-link-token", response_model=LinkTokenResponse)
@require_tier("premium")
async def create_plaid_link_token(
    current_user: User = Depends(get_current_user),
    request: Request = None,
    db = None
):
    """Create Plaid Link token for bank connection (Premium only)."""
    try:
        # Stub implementation - requires actual Plaid integration
        # In production: plaid_client.link_token_create()

        link_token = f"link-sandbox-{uuid.uuid4()}"
        expiration = datetime.now(timezone.utc) + timedelta(minutes=30)

        return LinkTokenResponse(link_token=link_token, expiration=expiration)
    except Exception as exc:
        logger.exception("Error creating link token")
        raise HTTPException(status_code=500, detail=str(exc))


@api_router.post("/bank/exchange-public-token", response_model=ExchangePublicTokenResponse)
@require_tier("premium")
async def exchange_public_token(
    token_req: ExchangePublicTokenRequest,
    current_user: User = Depends(get_current_user),
    request: Request = None,
    db = None
):
    """Exchange Plaid public token for access token (Premium only)."""
    try:
        if not db:
            db = _ensure_db(request)

        # Stub implementation - requires actual Plaid token exchange
        # In production: plaid_client.item_public_token_exchange()

        connection_id = str(uuid.uuid4())
        item_id = f"item-sandbox-{uuid.uuid4()}"
        access_token_encrypted = "encrypted_access_token_placeholder"

        # Create bank connection
        bank_conn = BankConnection(
            id=connection_id,
            user_id=current_user.id,
            institution_name="Chase Bank",
            institution_id="ins_sandbox",
            access_token_encrypted=access_token_encrypted,
            item_id=item_id,
            status="active",
            accounts=[
                {"account_id": "acc_1", "name": "Checking", "type": "depository", "subtype": "checking", "current_balance": 1500.00, "available_balance": 1500.00},
                {"account_id": "acc_2", "name": "Savings", "type": "depository", "subtype": "savings", "current_balance": 5000.00, "available_balance": 5000.00},
            ],
            last_sync_at=datetime.now(timezone.utc),
        )

        await db.bank_connections.insert_one(bank_conn.model_dump())

        return ExchangePublicTokenResponse(
            connection_id=connection_id,
            accounts=bank_conn.accounts,
        )
    except Exception as exc:
        logger.exception("Error exchanging public token")
        raise HTTPException(status_code=500, detail=str(exc))


@api_router.get("/bank/connections", response_model=List[BankConnectionResponse])
@require_tier("premium")
async def get_bank_connections(
    current_user: User = Depends(get_current_user),
    request: Request = None,
    db = None
):
    """Get all bank connections for user (Premium only)."""
    try:
        if not db:
            db = _ensure_db(request)

        connections = await db.bank_connections.find({"user_id": current_user.id}).to_list(100)

        return [
            BankConnectionResponse(
                connection_id=c["id"],
                institution_name=c["institution_name"],
                accounts=c.get("accounts", []),
                last_sync=c.get("last_sync_at"),
                status=c.get("status", "active"),
            )
            for c in connections
        ]
    except Exception as exc:
        logger.exception("Error getting bank connections")
        raise HTTPException(status_code=500, detail=str(exc))


@api_router.post("/bank/sync/{connection_id}", response_model=SyncResponse)
@require_tier("premium")
async def sync_bank_connection(
    connection_id: str,
    current_user: User = Depends(get_current_user),
    request: Request = None,
    db = None
):
    """Sync transactions and balances from bank (Premium only)."""
    try:
        if not db:
            db = _ensure_db(request)

        connection = await db.bank_connections.find_one({"id": connection_id, "user_id": current_user.id})
        if not connection:
            raise HTTPException(status_code=404, detail="Bank connection not found")

        # Stub implementation - requires actual Plaid sync
        # In production: plaid_client.transactions_sync()

        transactions_added = 5  # Simulated
        balances_updated = len(connection.get("accounts", []))

        # Update last sync time
        await db.bank_connections.update_one(
            {"id": connection_id},
            {"$set": {"last_sync_at": datetime.now(timezone.utc)}}
        )

        return SyncResponse(
            transactions_added=transactions_added,
            balances_updated=balances_updated,
            last_sync=datetime.now(timezone.utc),
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error syncing bank connection")
        raise HTTPException(status_code=500, detail=str(exc))


@api_router.delete("/bank/connection/{connection_id}")
@require_tier("premium")
async def delete_bank_connection(
    connection_id: str,
    current_user: User = Depends(get_current_user),
    request: Request = None,
    db = None
):
    """Delete bank connection (Premium only)."""
    try:
        if not db:
            db = _ensure_db(request)

        result = await db.bank_connections.delete_one({"id": connection_id, "user_id": current_user.id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Bank connection not found")

        return {"status": "deleted"}
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error deleting bank connection")
        raise HTTPException(status_code=500, detail=str(exc))


# ============= Autopilot Endpoints =============
@api_router.post("/autopilot/simulate", response_model=SimulateResponse)
@require_tier("premium")
async def simulate_autopilot(
    sim_req: SimulateRequest,
    current_user: User = Depends(get_current_user),
    request: Request = None,
    db = None
):
    """Run Monte Carlo simulation for Autopilot (Premium only)."""
    try:
        if not db:
            db = _ensure_db(request)

        # Gather user's financial data
        transactions = await db.transactions.find({"user_id": current_user.id}).to_list(1000)
        goals = await db.goals.find({"user_id": current_user.id}).to_list(100)

        # Calculate averages
        income_transactions = [t for t in transactions if t["type"] == "income"]
        expense_transactions = [t for t in transactions if t["type"] == "expense"]

        avg_income = sum(t["amount"] for t in income_transactions) / max(len(income_transactions), 1)
        avg_expenses = sum(t["amount"] for t in expense_transactions) / max(len(expense_transactions), 1)

        user_data = {
            "current_balance": 5000,  # TODO: Get from bank connection or calculate
            "avg_monthly_income": avg_income,
            "avg_monthly_expenses": avg_expenses,
            "goals": [{"id": g["id"], "target_amount": g["target_amount"], "current_amount": g["current_amount"]} for g in goals],
        }

        # Run simulation
        results = autopilot_engine.run_simulation(user_data, sim_req.scenario, sim_req.mode)

        return SimulateResponse(**results)
    except Exception as exc:
        logger.exception("Error running simulation")
        raise HTTPException(status_code=500, detail=str(exc))


@api_router.post("/autopilot/create-rule", response_model=CreateRuleResponse)
@require_tier("premium")
async def create_autopilot_rule(
    rule_req: CreateRuleRequest,
    current_user: User = Depends(get_current_user),
    request: Request = None,
    db = None
):
    """Create Autopilot rule (Premium only)."""
    try:
        if not db:
            db = _ensure_db(request)

        rule = AutopilotRule(
            user_id=current_user.id,
            rule_name=rule_req.rule_name,
            mode=rule_req.mode,
            enabled=False,  # Requires approval
            condition=rule_req.condition,
            action=rule_req.action,
            simulation_results={
                "success_probability": 0.75,
                "estimated_impact": 500.00,
                "risk_level": "low",
            },
        )

        await db.autopilot_rules.insert_one(rule.model_dump())

        return CreateRuleResponse(
            rule_id=rule.id,
            simulation_results=rule.simulation_results,
        )
    except Exception as exc:
        logger.exception("Error creating Autopilot rule")
        raise HTTPException(status_code=500, detail=str(exc))


@api_router.get("/autopilot/rules", response_model=List[AutopilotRule])
@require_tier("premium")
async def get_autopilot_rules(
    current_user: User = Depends(get_current_user),
    request: Request = None,
    db = None
):
    """Get all Autopilot rules (Premium only)."""
    try:
        if not db:
            db = _ensure_db(request)

        rules = await db.autopilot_rules.find({"user_id": current_user.id}).to_list(100)
        return [AutopilotRule(**r) for r in rules]
    except Exception as exc:
        logger.exception("Error getting Autopilot rules")
        raise HTTPException(status_code=500, detail=str(exc))


@api_router.put("/autopilot/rule/{rule_id}", response_model=AutopilotRule)
@require_tier("premium")
async def update_autopilot_rule(
    rule_id: str,
    rule_data: CreateRuleRequest,
    current_user: User = Depends(get_current_user),
    request: Request = None,
    db = None
):
    """Update Autopilot rule (Premium only)."""
    try:
        if not db:
            db = _ensure_db(request)

        result = await db.autopilot_rules.update_one(
            {"id": rule_id, "user_id": current_user.id},
            {"$set": rule_data.model_dump()}
        )

        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Rule not found")

        updated_rule = await db.autopilot_rules.find_one({"id": rule_id})
        return AutopilotRule(**updated_rule)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error updating Autopilot rule")
        raise HTTPException(status_code=500, detail=str(exc))


@api_router.post("/autopilot/approve/{rule_id}")
@require_tier("premium")
async def approve_autopilot_rule(
    rule_id: str,
    approve_req: ApproveRuleRequest,
    current_user: User = Depends(get_current_user),
    request: Request = None,
    db = None
):
    """Approve or reject Autopilot rule for execution (Premium only)."""
    try:
        if not db:
            db = _ensure_db(request)

        result = await db.autopilot_rules.update_one(
            {"id": rule_id, "user_id": current_user.id},
            {"$set": {"approved_by_user": approve_req.approved, "enabled": approve_req.approved}}
        )

        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Rule not found")

        return {"rule_id": rule_id, "approved_by_user": approve_req.approved, "status": "active" if approve_req.approved else "disabled"}
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error approving rule")
        raise HTTPException(status_code=500, detail=str(exc))


@api_router.delete("/autopilot/rule/{rule_id}")
@require_tier("premium")
async def delete_autopilot_rule(
    rule_id: str,
    current_user: User = Depends(get_current_user),
    request: Request = None,
    db = None
):
    """Delete Autopilot rule (Premium only)."""
    try:
        if not db:
            db = _ensure_db(request)

        result = await db.autopilot_rules.delete_one({"id": rule_id, "user_id": current_user.id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Rule not found")

        return {"status": "deleted"}
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error deleting rule")
        raise HTTPException(status_code=500, detail=str(exc))


@api_router.post("/autopilot/rollback/{execution_id}", response_model=RollbackResponse)
@require_tier("premium")
async def rollback_autopilot_execution(
    execution_id: str,
    rollback_req: RollbackRequest,
    current_user: User = Depends(get_current_user),
    request: Request = None,
    db = None
):
    """Rollback an Autopilot execution (Premium only)."""
    try:
        # Stub implementation - would reverse a transaction
        return RollbackResponse(rolled_back=True, refunded_amount=150.00)
    except Exception as exc:
        logger.exception("Error rolling back execution")
        raise HTTPException(status_code=500, detail=str(exc))


@api_router.get("/autopilot/audit-log", response_model=List[AuditLogEntry])
@require_tier("premium")
async def get_autopilot_audit_log(
    current_user: User = Depends(get_current_user),
    request: Request = None,
    db = None
):
    """Get Autopilot execution audit log (Premium only)."""
    try:
        # Stub implementation - would return actual execution history
        return []
    except Exception as exc:
        logger.exception("Error getting audit log")
        raise HTTPException(status_code=500, detail=str(exc))


# ============= Enhanced Reports Endpoints =============
@api_router.post("/reports/generate-enhanced", response_model=EnhancedReportResponse)
async def generate_enhanced_report(
    report_req: EnhancedReportRequest,
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    """Generate enhanced reports (format gated by tier)."""
    try:
        db = _ensure_db(request)

        # Check format entitlement
        subscription = await db.subscriptions.find_one({"user_id": current_user.id})
        tier = subscription.get("tier", "free") if subscription else "free"

        from entitlements import TIER_FEATURES
        allowed_formats = TIER_FEATURES.get(tier, TIER_FEATURES["free"])["export_formats"]

        if report_req.format not in allowed_formats:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "format_gated",
                    "message": f"{report_req.format.upper()} export requires Pro or Premium subscription",
                    "current_tier": tier,
                    "upgrade_url": "/pricing",
                }
            )

        # Stub implementation - would generate actual PDF/Excel file
        report_url = f"https://reports.example.com/{uuid.uuid4()}.{report_req.format}"
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)

        return EnhancedReportResponse(
            report_url=report_url,
            expires_at=expires_at,
            report_type=report_req.report_type,
            format=report_req.format,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error generating enhanced report")
        raise HTTPException(status_code=500, detail=str(exc))


app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
