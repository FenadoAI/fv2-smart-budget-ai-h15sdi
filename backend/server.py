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


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).parent

JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
security = HTTPBearer()


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

        # Check if user exists
        existing_user = await db.users.find_one({"$or": [{"username": user_data.username}, {"email": user_data.email}]})
        if existing_user:
            return AuthResponse(success=False, error="Username or email already exists")

        # Create user
        user = User(
            username=user_data.username,
            email=user_data.email,
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
        return AuthResponse(success=False, error=str(exc))


@api_router.post("/auth/login", response_model=AuthResponse)
async def login(login_data: UserLogin, request: Request):
    try:
        db = _ensure_db(request)

        # Find user
        user_data = await db.users.find_one({"username": login_data.username})
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
        return AuthResponse(success=False, error=str(exc))


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


app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
