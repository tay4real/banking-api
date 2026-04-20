# Banking REST API

A production-grade banking API built with Python, FastAPI, and PostgreSQL.
Designed to financial services standards with security-first architecture.

## Tech stack

- **Runtime**: Python 3.13, FastAPI
- **Database**: PostgreSQL 16 with SQLAlchemy ORM and Alembic migrations
- **Cache / blacklist**: Redis 7
- **Auth**: JWT (access + refresh tokens) with Redis blacklisting
- **Security**: bcrypt (SHA-256 pre-hash), rate limiting, security headers, IDOR prevention
- **Deployment**: Docker, Docker Compose

## Features

- User registration and authentication with JWT
- Access token + refresh token rotation
- Token blacklisting on logout via Redis
- Bank account management (savings, current, fixed deposit)
- NUBAN-format account number generation
- Role-based access control (customer, admin, support)
- Rate limiting per IP and per authenticated user
- Structured JSON logging with correlation IDs
- Global error handling — no stack traces exposed to clients
- Full test suite with pytest (SQLite in-memory)

## Getting started

**Prerequisites**: Docker Desktop

```bash
git clone https://github.com/YOUR_USERNAME/banking-api.git
cd banking-api
cp .env.example .env          # add your SECRET_KEY
docker compose up --build -d
```

API available at `http://localhost:8000`
Interactive docs at `http://localhost:8000/docs` (development only)

## Running tests

```bash
python -m pytest tests/ -v --cov=app --cov-report=term-missing
```

## API endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/v1/auth/register` | None | Register new user |
| POST | `/api/v1/auth/login` | None | Login, receive tokens |
| POST | `/api/v1/auth/refresh` | None | Refresh access token |
| POST | `/api/v1/auth/logout` | Bearer | Logout, blacklist token |
| GET | `/api/v1/users/me` | Bearer | Get own profile |
| POST | `/api/v1/accounts` | Bearer | Create bank account |
| GET | `/api/v1/accounts` | Bearer | List own accounts |
| GET | `/api/v1/accounts/{id}` | Bearer | Get account details |
| GET | `/api/v1/accounts/{id}/balance` | Bearer | Get balance |
| PATCH | `/api/v1/accounts/{id}/freeze` | Admin | Freeze account |
| PATCH | `/api/v1/accounts/{id}/unfreeze` | Admin | Unfreeze account |

## Security design decisions

- UUID primary keys prevent sequential ID enumeration
- `Numeric(19,4)` for balances — never `Float`
- Database-level `CHECK` constraint prevents negative balances
- IDOR prevention — ownership verified on every account query
- Timing-safe login — dummy hash evaluated when user not found
- Soft deletes only — financial records are never destroyed
- Non-root Docker user in production