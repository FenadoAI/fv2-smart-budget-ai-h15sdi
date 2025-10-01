# AI-Powered Personal Finance Assistant - Implementation Plan

## Requirement ID: e1780344-49ca-4a5f-872a-464de02ffda1

## Overview
Build a modern website for an AI-powered personal finance assistant targeting young professionals. Users can manually enter transactions or upload CSV files, and receive AI-generated monthly budgets with actionable savings insights.

## Backend Implementation

### 1. Database Models
- **User**: username, email, hashed_password, created_at
- **Transaction**: user_id, date, description, amount, category, type (income/expense)
- **Budget**: user_id, month, year, analysis, savings_opportunities, total_income, total_expenses, created_at

### 2. API Endpoints

#### Authentication
- POST /api/auth/signup - Create new user account
- POST /api/auth/login - Login and get JWT token
- GET /api/auth/me - Get current user info

#### Transactions
- POST /api/transactions - Add single transaction
- GET /api/transactions - List user's transactions
- DELETE /api/transactions/{id} - Delete transaction
- POST /api/transactions/upload - Upload CSV file

#### Budget Analysis
- POST /api/budget/generate - Generate AI budget analysis
- GET /api/budget/latest - Get latest budget report
- GET /api/budget/history - Get all budget reports

### 3. AI Integration
- Use LiteLLM with gemini-2.5-flash for budget analysis
- Analyze transaction data to:
  - Categorize spending
  - Identify savings opportunities
  - Suggest budget allocations
  - Highlight overspending categories

## Frontend Implementation

### 1. Marketing Pages
- **Homepage** (`/`)
  - Hero section with value proposition
  - Features section (3-4 key features)
  - Benefits section (how it helps young professionals)
  - How it works (3-step process)
  - CTA buttons to sign up
  - Modern design with engaging visuals

### 2. Authentication Pages
- **Sign Up** (`/signup`)
  - Email, username, password fields
  - Validation and error handling
  - Redirect to dashboard on success

- **Login** (`/login`)
  - Email/username and password
  - Redirect to dashboard on success

### 3. Dashboard (`/dashboard`)
- **Transaction Management**
  - Form to add manual transactions
  - CSV upload button
  - Transaction list (filterable by date, category)
  - Delete transaction capability

- **Budget Analysis**
  - Generate Budget button
  - Display latest budget report
  - Show spending by category
  - Highlight savings opportunities
  - Visual charts/graphs

### 4. Design System
- Tailwind CSS with custom color scheme
- shadcn/ui components
- Lucide React icons
- Unsplash images for marketing pages
- Responsive design (mobile-first)

## CSV Upload Format
Expected CSV columns:
- Date (YYYY-MM-DD or MM/DD/YYYY)
- Description
- Amount (positive for income, negative for expenses)
- Category (optional, AI can categorize)

## AI Prompt Strategy
Send transaction data to AI with:
- All transactions for the current month
- Request for:
  - Monthly budget recommendations
  - Top 3-5 savings opportunities
  - Spending category breakdown
  - Actionable advice for young professionals

## Success Metrics
- User sign-ups
- Budget reports generated
- Transactions entered
- User engagement (return visits)

## Implementation Order
1. Backend: Auth system
2. Backend: Transaction APIs
3. Backend: AI budget analysis
4. Frontend: Marketing homepage
5. Frontend: Auth pages
6. Frontend: Dashboard with transactions
7. Frontend: Budget display
8. Testing and refinement
