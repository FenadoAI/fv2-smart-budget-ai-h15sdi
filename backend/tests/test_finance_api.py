"""Test finance API endpoints - requires running server on port 8001."""

import os
import requests
from datetime import datetime

# Load environment
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / ".env")

BASE_URL = "http://localhost:8001/api"


def test_auth_flow():
    """Test signup and login flow."""
    username = f"testuser_{datetime.now().timestamp()}"
    email = f"{username}@example.com"
    password = "testpass123"

    # Test signup
    signup_response = requests.post(
        f"{BASE_URL}/auth/signup",
        json={"username": username, "email": email, "password": password}
    )
    assert signup_response.status_code == 200, f"Signup failed: {signup_response.text}"

    signup_data = signup_response.json()
    assert signup_data["success"] is True, f"Signup not successful: {signup_data}"
    assert "token" in signup_data, "Token not in signup response"
    assert signup_data["user"]["username"] == username

    token = signup_data["token"]

    # Test login
    login_response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"username": username, "password": password}
    )
    assert login_response.status_code == 200, f"Login failed: {login_response.text}"

    login_data = login_response.json()
    assert login_data["success"] is True, f"Login not successful: {login_data}"
    assert "token" in login_data

    # Test get current user
    me_response = requests.get(
        f"{BASE_URL}/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert me_response.status_code == 200, f"Get me failed: {me_response.text}"
    me_data = me_response.json()
    assert me_data["username"] == username

    return token


def test_transaction_flow():
    """Test transaction CRUD operations."""
    # First, create a user and get token
    token = test_auth_flow()

    # Create transaction
    transaction_data = {
        "date": "2025-10-01",
        "description": "Salary",
        "amount": 5000.0,
        "category": "Income",
        "type": "income"
    }

    create_response = requests.post(
        f"{BASE_URL}/transactions",
        json=transaction_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert create_response.status_code == 200, f"Create transaction failed: {create_response.text}"
    transaction = create_response.json()
    assert transaction["description"] == "Salary"
    transaction_id = transaction["id"]

    # Get transactions
    get_response = requests.get(
        f"{BASE_URL}/transactions",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert get_response.status_code == 200, f"Get transactions failed: {get_response.text}"
    transactions = get_response.json()
    assert len(transactions) > 0, "No transactions returned"
    assert any(t["id"] == transaction_id for t in transactions), "Created transaction not found"

    # Delete transaction
    delete_response = requests.delete(
        f"{BASE_URL}/transactions/{transaction_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert delete_response.status_code == 200, f"Delete transaction failed: {delete_response.text}"
    delete_data = delete_response.json()
    assert delete_data["success"] is True

    print("✅ Transaction flow test passed")


def test_budget_generation():
    """Test budget generation with AI."""
    # First, create a user and get token
    token = test_auth_flow()

    # Add some transactions
    transactions = [
        {"date": "2025-10-01", "description": "Salary", "amount": 5000.0, "category": "Income", "type": "income"},
        {"date": "2025-10-05", "description": "Rent", "amount": 1500.0, "category": "Housing", "type": "expense"},
        {"date": "2025-10-10", "description": "Groceries", "amount": 300.0, "category": "Food", "type": "expense"},
        {"date": "2025-10-15", "description": "Netflix", "amount": 15.0, "category": "Entertainment", "type": "expense"},
        {"date": "2025-10-20", "description": "Uber", "amount": 50.0, "category": "Transportation", "type": "expense"},
    ]

    for trans in transactions:
        requests.post(
            f"{BASE_URL}/transactions",
            json=trans,
            headers={"Authorization": f"Bearer {token}"}
        )

    # Generate budget
    budget_response = requests.post(
        f"{BASE_URL}/budget/generate",
        json={"month": 10, "year": 2025},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert budget_response.status_code == 200, f"Budget generation failed: {budget_response.text}"

    budget = budget_response.json()
    assert budget["total_income"] == 5000.0, f"Incorrect total income: {budget['total_income']}"
    assert budget["total_expenses"] == 1865.0, f"Incorrect total expenses: {budget['total_expenses']}"
    assert "analysis" in budget, "No analysis in budget"
    assert len(budget["savings_opportunities"]) > 0, "No savings opportunities"
    assert "spending_by_category" in budget, "No spending by category"

    # Get latest budget
    latest_response = requests.get(
        f"{BASE_URL}/budget/latest",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert latest_response.status_code == 200, f"Get latest budget failed: {latest_response.text}"
    latest_budget = latest_response.json()
    assert latest_budget["month"] == 10

    print("✅ Budget generation test passed")


if __name__ == "__main__":
    print("Testing Finance API endpoints...")
    print("\n1. Testing auth flow...")
    test_auth_flow()
    print("✅ Auth flow test passed")

    print("\n2. Testing transaction flow...")
    test_transaction_flow()

    print("\n3. Testing budget generation...")
    test_budget_generation()

    print("\n✅ All tests passed!")
