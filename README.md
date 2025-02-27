# Receipt Management API: A FastAPI Service for Digital Receipt Generation and Storage

The Receipt Management API is a modern FastAPI application that enables businesses to create, store, and manage digital receipts. It provides secure user authentication and comprehensive receipt management capabilities with formatted output generation.

This service helps businesses transition from paper receipts to digital formats while maintaining familiar receipt layouts and calculations. The API supports multiple payment types, product tracking, and user-specific receipt management with features like filtering by date ranges and total amounts. Built with FastAPI and SQLModel, it offers high performance, automatic API documentation, and type safety throughout the application.

## Repository Structure
```
app/
├── core/                     # Core functionality and configuration
│   ├── config.py            # Application configuration settings
│   └── security.py          # Authentication and authorization logic
├── db/
│   └── database.py          # Database connection and initialization
├── routes/                  # API endpoint definitions
│   ├── receipt.py           # Receipt management endpoints
│   └── user.py             # User authentication endpoints
├── tests/                   # Test suite
│   └── routes/             # API endpoint tests
├── main.py                 # Application entry point and FastAPI setup
├── models.py               # Data models and schemas
└── pyproject.toml         # Project dependencies and configuration
```

## Usage Instructions
### Prerequisites
- Python 3.12 or higher
- PostgreSQL database
- Environment variables configured for database connection and JWT secret key

### Installation
```bash
# Clone the repository
git clone git@github.com:AHTOXA86/receipts_archive.git
cd receipts_archive/app

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Quick Start
1. Set up environment variables:
```bash
export DATABASE_URL="postgresql://user:password@localhost/db_name"
export SECRET_KEY='{"k":"AwTQXpUwWOK6x_zIVr3am1f8i0Fpz1rmT01SpHEVbG4","kty":"oct"}'
export ACCESS_TOKEN_EXPIRE_MINUTES=30
```

2. Start the application:
```bash
cd ../
uvicorn app.main:app --reload
```

3. Create a new user:
```python
import requests

response = requests.post(
    "http://localhost:8000/users/",
    json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "secretpassword",
        "full_name": "Test User"
    }
)
```
### Documentation
http://localhost:8000/docs


### More Detailed Examples
1. Authenticate and get access token:
```python
response = requests.post(
    "http://localhost:8000/token",
    data={
        "username": "testuser",
        "password": "secretpassword"
    }
)
token = response.json()["access_token"]
```

2. Create a new receipt:
```python
headers = {"Authorization": f"Bearer {token}"}
receipt_data = {
    "shop_name": "My Shop",
    "payment_type": "CASH",
    "amount": 100.00,
    "products": [
        {
            "name": "Product 1",
            "price": 50.00,
            "quantity": 2,
            "quantity_type": "PCS"
        }
    ]
}

response = requests.post(
    "http://localhost:8000/receipts/",
    json=receipt_data,
    headers=headers
)
```

### Troubleshooting
1. Authentication Issues
- Error: "Could not validate credentials"
  - Verify token expiration
  - Check if token is included in Authorization header
  - Ensure token format is "Bearer <token>"

2. Database Connection Issues
- Error: "Could not connect to database"
  - Verify DATABASE_URL environment variable
  - Check database server status
  - Ensure database user has proper permissions

3. Receipt Creation Failures
- Enable debug logging:
```bash
uvicorn app.main:app --log-level debug
```
- Check request payload matches schema
- Verify all required fields are provided

## Data Flow
The application processes receipts through a structured flow from user input to storage and formatted output.

```ascii
User Request → Authentication → Input Validation → Database Storage
     ↓                                                  ↓
Formatted Output ←---- Receipt Generation ←---- Data Retrieval
```

Key component interactions:
1. User authentication via JWT tokens
2. Input validation using Pydantic models
3. Database operations through SQLModel
4. Receipt formatting with configurable templates
5. Product calculations and totals computation
6. Payment type validation and change calculation
7. Secure user-specific receipt access control