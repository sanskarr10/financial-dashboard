from pydantic import BaseModel, EmailStr, field_validator, model_validator
from typing import Optional
from datetime import date
import re

# ── Auth ──────────────────────────────────────────────────────────────────────
class LoginSchema(BaseModel):
    email: EmailStr
    password: str

# ── Users ─────────────────────────────────────────────────────────────────────
class CreateUserSchema(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str = "viewer"

    @field_validator("name")
    @classmethod
    def name_length(cls, v):
        if len(v.strip()) < 2:
            raise ValueError("Name must be at least 2 characters")
        return v.strip()

    @field_validator("password")
    @classmethod
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v

    @field_validator("role")
    @classmethod
    def valid_role(cls, v):
        if v not in ("viewer", "analyst", "admin"):
            raise ValueError("Role must be viewer, analyst, or admin")
        return v

class UpdateUserSchema(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None

    @field_validator("role")
    @classmethod
    def valid_role(cls, v):
        if v and v not in ("viewer", "analyst", "admin"):
            raise ValueError("Role must be viewer, analyst, or admin")
        return v

    @field_validator("status")
    @classmethod
    def valid_status(cls, v):
        if v and v not in ("active", "inactive"):
            raise ValueError("Status must be active or inactive")
        return v

# ── Records ───────────────────────────────────────────────────────────────────
class CreateRecordSchema(BaseModel):
    amount: float
    type: str
    category: str
    date: str
    notes: Optional[str] = None

    @field_validator("amount")
    @classmethod
    def positive_amount(cls, v):
        if v <= 0:
            raise ValueError("Amount must be positive")
        return v

    @field_validator("type")
    @classmethod
    def valid_type(cls, v):
        if v not in ("income", "expense"):
            raise ValueError("Type must be income or expense")
        return v

    @field_validator("category")
    @classmethod
    def valid_category(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("Category is required")
        if len(v) > 100:
            raise ValueError("Category max 100 characters")
        return v.strip()

    @field_validator("date")
    @classmethod
    def valid_date(cls, v):
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", v):
            raise ValueError("Date must be in YYYY-MM-DD format")
        return v

    @field_validator("notes")
    @classmethod
    def notes_length(cls, v):
        if v and len(v) > 500:
            raise ValueError("Notes max 500 characters")
        return v

class UpdateRecordSchema(BaseModel):
    amount: Optional[float] = None
    type: Optional[str] = None
    category: Optional[str] = None
    date: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("amount")
    @classmethod
    def positive_amount(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Amount must be positive")
        return v

    @field_validator("type")
    @classmethod
    def valid_type(cls, v):
        if v and v not in ("income", "expense"):
            raise ValueError("Type must be income or expense")
        return v

    @field_validator("date")
    @classmethod
    def valid_date(cls, v):
        if v and not re.match(r"^\d{4}-\d{2}-\d{2}$", v):
            raise ValueError("Date must be in YYYY-MM-DD format")
        return v
