import os
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from app.models.user_model import UserModel

JWT_SECRET  = os.getenv("JWT_SECRET", "finance-dashboard-secret-dev-only")
ALGORITHM   = "HS256"
EXPIRE_HOURS = 24

bearer_scheme = HTTPBearer()

ROLE_LEVELS = {"viewer": 1, "analyst": 2, "admin": 3}

def create_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=EXPIRE_HOURS)
    return jwt.encode({"sub": user_id, "exp": expire}, JWT_SECRET, algorithm=ALGORITHM)

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> dict:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = UserModel.find_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    if user["status"] != "active":
        raise HTTPException(status_code=403, detail="Account is inactive")
    return user

def require_role(*roles: str):
    min_level = min(ROLE_LEVELS.get(r, 99) for r in roles)

    def checker(current_user: dict = Depends(get_current_user)) -> dict:
        if ROLE_LEVELS.get(current_user["role"], 0) < min_level:
            raise HTTPException(
                status_code=403,
                detail=f"Access denied. Required role: {' or '.join(roles)}. Your role: {current_user['role']}"
            )
        return current_user
    return checker
