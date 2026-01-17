# Personal Finance Manager API

## Project Overview

Personal Finance Manager API is a Flask-based web application designed to help users manage their personal finances. It offers features such as user registration and login, account management, tracking of income and expenses, budgeting, and financial goal setting.

## Features

- **User Registration and Login**: Securely register and log in users with JWT authentication.
- **Account Management**: Create and manage multiple accounts (checking, savings, credit, etc.).
- **Income and Expense Tracking**: Add, update, delete, and categorize income and expense transactions with automatic balance updates.
- **Transaction Filtering**: Filter transactions by date range, category, type, and account.
- **Financial Reports**: Get summaries of income, expenses, and category breakdowns.
- **Budgeting**: (Coming soon) Set budgets for different categories and track adherence.
- **Financial Goals**: (Coming soon) Set and monitor progress towards financial goals.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

- Python 3.8 or newer
- pip (Python package installer)

### Setting Up a Development Environment

1. **Clone the Repository**

```bash
git clone https://github.com/darwin757/personal_finance_manager.git
cd personal_finance_manager
```

2. **Create and Activate a Virtual Environment**

On Windows:
```bash
python -m venv venv
.\venv\Scripts\activate
```

On macOS and Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

3. **Install Required Packages**

```bash
pip install -r requirements.txt
```

### Initializing the Database

Before running the application for the first time, you need to create the database and apply migrations:

```bash
flask db upgrade
```

### Running the Application

Run the Flask application using:

```bash
flask run
```

The API will be available at `http://127.0.0.1:5000/`.

## API Endpoints

### Authentication
- **User Registration**: `POST /auth/register`
  - Registers a new user.
  - Body: `{"username": "string", "password": "string"}`
- **User Login**: `POST /auth/login`
  - Authenticates a user and returns a JWT token.
  - Body: `{"username": "string", "password": "string"}`

### Account Management
- **Create Account**: `POST /accounts`
  - Creates a new account for the authenticated user.
  - Body: `{"name": "string", "account_type": "string", "balance": number}`
- **List Accounts**: `GET /accounts`
  - Lists all accounts for the authenticated user.
- **Get Account**: `GET /accounts/<account_id>`
  - Retrieves a specific account by ID.
- **Update Account**: `PUT /accounts/<account_id>`
  - Updates an existing account.
  - Body: `{"name": "string", "account_type": "string", "balance": number}`
- **Delete Account**: `DELETE /accounts/<account_id>`
  - Deletes an account.

### Transaction Management (Income & Expense Tracking)
- **Create Transaction**: `POST /transactions`
  - Creates a new transaction (income or expense).
  - Body: `{"account_id": number, "amount": number, "transaction_type": "income|expense", "category": "string", "description": "string", "date": "ISO date string (optional)"}`
- **List Transactions**: `GET /transactions`
  - Lists all transactions for the authenticated user with optional filters.
  - Query params: `account_id`, `transaction_type`, `category`, `start_date`, `end_date`, `page`, `per_page`
- **Get Transaction**: `GET /transactions/<transaction_id>`
  - Retrieves a specific transaction by ID.
- **Update Transaction**: `PUT /transactions/<transaction_id>`
  - Updates an existing transaction.
  - Body: Same as create transaction (all fields optional)
- **Delete Transaction**: `DELETE /transactions/<transaction_id>`
  - Deletes a transaction and updates account balance.
- **Transaction Summary**: `GET /transactions/summary`
  - Gets a summary of transactions (total income, expenses, net, category breakdown).
  - Query params: `account_id`, `start_date`, `end_date`

*Note: All endpoints except `/auth/register` and `/auth/login` require JWT authentication via `Authorization: Bearer <token>` header.*

## Running Tests

To run the test suite:

```bash
python -m pytest tests/
```

Or run specific test files:

```bash
python -m pytest tests/test_account_management.py
python -m pytest tests/test_transaction_management.py
```

## Contributing

Please read [CONTRIBUTING.md](https://github.com/darwin757/personal_finance_manager/blob/main/CONTRIBUTING.md) for details on our code of conduct, and the process for submitting pull requests to us.

## License

This project is licensed under the MIT License - see the [LICENSE.md](https://github.com/darwin757/personal_finance_manager/blob/main/LICENSE.md) file for details.
