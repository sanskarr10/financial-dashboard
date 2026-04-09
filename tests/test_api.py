"""
Integration tests for the Finance Dashboard API
Run with: pytest tests/ -v
"""
import pytest
import os
import sys
from pathlib import Path

# Use isolated test database
TEST_DB = str(Path(__file__).parent / "test_finance.db")
os.environ["DB_PATH"] = TEST_DB

from fastapi.testclient import TestClient
from app.main import app
from app.models.database import init_db
from app.models.user_model import UserModel

client = TestClient(app)

@pytest.fixture(scope="session", autouse=True)
def setup_db():
    init_db()
    UserModel.create("Admin",   "admin@test.com",   "Password123!", "admin")
    UserModel.create("Analyst", "analyst@test.com", "Password123!", "analyst")
    UserModel.create("Viewer",  "viewer@test.com",  "Password123!", "viewer")
    yield
    for f in [TEST_DB, TEST_DB + "-wal", TEST_DB + "-shm"]:
        try: os.unlink(f)
        except: pass

@pytest.fixture(scope="session")
def admin_token(setup_db):
    res = client.post("/api/auth/login", json={"email": "admin@test.com", "password": "Password123!"})
    return res.json()["token"]

@pytest.fixture(scope="session")
def analyst_token(setup_db):
    res = client.post("/api/auth/login", json={"email": "analyst@test.com", "password": "Password123!"})
    return res.json()["token"]

@pytest.fixture(scope="session")
def viewer_token(setup_db):
    res = client.post("/api/auth/login", json={"email": "viewer@test.com", "password": "Password123!"})
    return res.json()["token"]

# ── Auth ───────────────────────────────────────────────────────────────────────
class TestAuth:
    def test_login_admin(self, admin_token):
        assert admin_token is not None

    def test_login_wrong_password(self):
        res = client.post("/api/auth/login", json={"email": "admin@test.com", "password": "wrong"})
        assert res.status_code == 401

    def test_me(self, admin_token):
        res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        assert res.json()["user"]["role"] == "admin"

    def test_me_no_token(self):
        res = client.get("/api/auth/me")
        assert res.status_code == 403

# ── Records ────────────────────────────────────────────────────────────────────
class TestRecords:
    created_id = None

    def test_viewer_can_list(self, viewer_token):
        res = client.get("/api/records", headers={"Authorization": f"Bearer {viewer_token}"})
        assert res.status_code == 200
        assert "records" in res.json()

    def test_analyst_can_create(self, analyst_token):
        res = client.post("/api/records",
            headers={"Authorization": f"Bearer {analyst_token}"},
            json={"amount": 1500, "type": "income", "category": "Salary", "date": "2024-06-01"}
        )
        assert res.status_code == 201
        assert res.json()["record"]["amount"] == 1500
        TestRecords.created_id = res.json()["record"]["id"]

    def test_viewer_cannot_create(self, viewer_token):
        res = client.post("/api/records",
            headers={"Authorization": f"Bearer {viewer_token}"},
            json={"amount": 100, "type": "expense", "category": "Groceries", "date": "2024-06-01"}
        )
        assert res.status_code == 403

    def test_analyst_can_update(self, analyst_token):
        res = client.patch(f"/api/records/{TestRecords.created_id}",
            headers={"Authorization": f"Bearer {analyst_token}"},
            json={"amount": 2000}
        )
        assert res.status_code == 200
        assert res.json()["record"]["amount"] == 2000

    def test_viewer_cannot_delete(self, viewer_token):
        res = client.delete(f"/api/records/{TestRecords.created_id}",
            headers={"Authorization": f"Bearer {viewer_token}"}
        )
        assert res.status_code == 403

    def test_admin_can_delete(self, admin_token):
        res = client.delete(f"/api/records/{TestRecords.created_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert res.status_code == 200

    def test_validation_missing_fields(self, analyst_token):
        res = client.post("/api/records",
            headers={"Authorization": f"Bearer {analyst_token}"},
            json={"type": "income"}
        )
        assert res.status_code == 422

    def test_filter_by_type(self, analyst_token, viewer_token):
        client.post("/api/records",
            headers={"Authorization": f"Bearer {analyst_token}"},
            json={"amount": 500, "type": "expense", "category": "Rent", "date": "2024-06-01"}
        )
        res = client.get("/api/records?type=expense",
            headers={"Authorization": f"Bearer {viewer_token}"}
        )
        assert res.status_code == 200
        for r in res.json()["records"]:
            assert r["type"] == "expense"

# ── Dashboard ──────────────────────────────────────────────────────────────────
class TestDashboard:
    def test_overview_all_roles(self, viewer_token):
        res = client.get("/api/dashboard/overview",
            headers={"Authorization": f"Bearer {viewer_token}"}
        )
        assert res.status_code == 200
        s = res.json()["summary"]
        assert "total_income" in s
        assert "total_expenses" in s
        assert "net_balance" in s

    def test_categories_analyst(self, analyst_token):
        res = client.get("/api/dashboard/categories",
            headers={"Authorization": f"Bearer {analyst_token}"}
        )
        assert res.status_code == 200

    def test_categories_viewer_forbidden(self, viewer_token):
        res = client.get("/api/dashboard/categories",
            headers={"Authorization": f"Bearer {viewer_token}"}
        )
        assert res.status_code == 403

    def test_monthly_trends(self, analyst_token):
        res = client.get("/api/dashboard/trends/monthly",
            headers={"Authorization": f"Bearer {analyst_token}"}
        )
        assert res.status_code == 200
        assert "trends" in res.json()

# ── Users ──────────────────────────────────────────────────────────────────────
class TestUsers:
    def test_admin_can_list(self, admin_token):
        res = client.get("/api/users", headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        assert "users" in res.json()

    def test_viewer_cannot_list(self, viewer_token):
        res = client.get("/api/users", headers={"Authorization": f"Bearer {viewer_token}"})
        assert res.status_code == 403

    def test_admin_can_create(self, admin_token):
        res = client.post("/api/users",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"name": "New User", "email": "new@test.com", "password": "Password123!", "role": "viewer"}
        )
        assert res.status_code == 201
        assert res.json()["user"]["role"] == "viewer"

    def test_duplicate_email(self, admin_token):
        res = client.post("/api/users",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"name": "Dupe", "email": "new@test.com", "password": "Password123!"}
        )
        assert res.status_code == 409
