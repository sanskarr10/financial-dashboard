# Finance Dashboard Backend (Python)

A production-ready REST API backend for a finance dashboard system, featuring role-based access control, financial record management, and summary analytics. Built with **Python + FastAPI**.

---

## Tech Stack

| Layer       | Choice                    | Reason                                                    |
|-------------|---------------------------|-----------------------------------------------------------|
| Language    | Python 3.11+              | Clean, readable, excellent for backend APIs               |
| Framework   | FastAPI                   | Modern, fast, auto-generates OpenAPI/Swagger docs         |
| Database    | SQLite (built-in)         | Zero setup, file-based, works everywhere out of the box   |
| Auth        | JWT (python-jose)         | Stateless, standard for REST APIs                         |
| Validation  | Pydantic v2               | Schema-first, automatic request validation                |
| Password    | passlib + bcrypt          | Industry standard hashing                                 |
| Rate Limit  | slowapi                   | Simple rate limiting middleware                           |
| Testing     | pytest + httpx            | Full integration test coverage                            |

---

## Project Structure

```
finance-dashboard-python/
├── app/
│   ├── main.py                  # FastAPI app, middleware, router wiring
│   ├── models/
│   │   ├── database.py          # SQLite connection + schema init
│   │   ├── user_model.py        # User queries
│   │   └── record_model.py      # Record queries + analytics
│   ├── middleware/
│   │   ├── auth.py              # JWT verification + require_role()
│   │   └── schemas.py           # Pydantic validation schemas
│   └── routes/
│       ├── auth.py              # Login, /me
│       ├── users.py             # User CRUD
│       ├── records.py           # Record CRUD
│       └── dashboard.py         # Analytics endpoints
├── tests/
│   └── test_api.py              # Full integration test suite
├── seed.py                      # Database seeder
├── requirements.txt
└── README.md
```

---

## Setup

### Prerequisites
- Python 3.11+
- pip

### 1. Create virtual environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Seed the database
```bash
python seed.py
```

Default users created:

| Email                  | Password      | Role     |
|------------------------|---------------|----------|
| admin@example.com      | Password123!  | admin    |
| analyst@example.com    | Password123!  | analyst  |
| viewer@example.com     | Password123!  | viewer   |

### 4. Start the server
```bash
uvicorn app.main:app --reload
```

Server runs on `http://localhost:8000`

### 5. Run tests
```bash
pytest tests/ -v
```

---

## Interactive API Docs (Free — Built In!)

FastAPI automatically generates live interactive documentation:

| URL | Description |
|-----|-------------|
| `http://localhost:8000/docs` | Swagger UI — try every endpoint in the browser |
| `http://localhost:8000/redoc` | ReDoc — clean reference documentation |

No Postman needed — you can test every endpoint directly from the browser.

---

## Role-Based Access Control

| Action                        | Viewer | Analyst | Admin |
|-------------------------------|--------|---------|-------|
| Login / view own profile      | ✅     | ✅      | ✅    |
| View financial records        | ✅     | ✅      | ✅    |
| View dashboard summary        | ✅     | ✅      | ✅    |
| View recent activity          | ✅     | ✅      | ✅    |
| Create / update records       | ❌     | ✅      | ✅    |
| Delete records (soft)         | ❌     | ❌      | ✅    |
| View category breakdown       | ❌     | ✅      | ✅    |
| View monthly/weekly trends    | ❌     | ✅      | ✅    |
| Manage users (CRUD)           | ❌     | ❌      | ✅    |

---

## API Reference

Base URL: `http://localhost:8000/api`

All endpoints except `/api/auth/login` require:
```
Authorization: Bearer <token>
```

### Auth
| Method | Endpoint       | Access  |
|--------|----------------|---------|
| POST   | /auth/login    | Public  |
| GET    | /auth/me       | All     |

### Records
| Method | Endpoint        | Access          |
|--------|-----------------|-----------------|
| GET    | /records        | All             |
| GET    | /records/:id    | All             |
| POST   | /records        | Analyst, Admin  |
| PATCH  | /records/:id    | Analyst, Admin  |
| DELETE | /records/:id    | Admin only      |

### Dashboard
| Method | Endpoint                   | Access          |
|--------|----------------------------|-----------------|
| GET    | /dashboard/overview        | All             |
| GET    | /dashboard/summary         | All             |
| GET    | /dashboard/recent          | All             |
| GET    | /dashboard/categories      | Analyst, Admin  |
| GET    | /dashboard/trends/monthly  | Analyst, Admin  |
| GET    | /dashboard/trends/weekly   | Analyst, Admin  |

### Users
| Method | Endpoint    | Access     |
|--------|-------------|------------|
| GET    | /users      | Admin only |
| GET    | /users/:id  | Admin only |
| POST   | /users      | Admin only |
| PATCH  | /users/:id  | Admin only |
| DELETE | /users/:id  | Admin only |

---

## Technical Decisions and Trade-offs

This project was built using **Python with FastAPI** because FastAPI is modern, performant, and automatically generates OpenAPI documentation — meaning every endpoint is self-documenting with zero extra effort. For the database, **SQLite via Python's built-in `sqlite3` module** was chosen because it requires zero infrastructure, works on every machine without installation, and is perfectly suited for a locally runnable assessment project — unlike the Node.js version which required a third-party library (sql.js) to avoid native compilation issues, Python's sqlite3 is part of the standard library and works everywhere. Authentication uses **JWT tokens via python-jose** because they are stateless and standard for REST APIs. Access control uses a **three-tier role hierarchy** (viewer < analyst < admin) rather than a permissions table because the requirements map cleanly onto a linear hierarchy and a permissions table would add unnecessary complexity. Financial records use **soft delete** by setting a `deleted_at` timestamp to preserve audit history. Input validation uses **Pydantic v2** which is FastAPI's native validation layer — schemas are defined as Python classes with type annotations, and FastAPI automatically validates requests and returns structured 422 errors on failure. All dashboard analytics are computed in **SQL aggregation queries** rather than Python loops for efficiency. The main trade-offs are that SQLite would be replaced with PostgreSQL in production, JWT tokens cannot be instantly revoked without a blacklist, and page-based pagination can show inconsistent results if records change between requests — all consciously accepted in favour of simplicity appropriate for this scope.

---

## Additional Notes

The database is created automatically on first run — no manual setup needed. The `data/` folder and `finance.db` file are created when you run `python seed.py` or start the server for the first time. The seed script is safe to re-run at any time — it clears existing data before inserting fresh records. The `amount` field is constrained to positive numbers because the direction of money flow is captured by the `type` field (income or expense), making negative amounts unnecessary. FastAPI's built-in Swagger UI at `/docs` means you can test every endpoint directly in your browser without Postman — this is a significant advantage of the Python version over the Node.js version. The `/api/dashboard/overview` endpoint returns all dashboard data in a single request to minimise round trips. All timestamps are stored as ISO strings in SQLite for human readability. If this project were extended toward production, the recommended next steps would be migrating to PostgreSQL with SQLAlchemy ORM, adding refresh tokens, setting up Alembic for database migrations, adding structured logging, and containerising with Docker.
