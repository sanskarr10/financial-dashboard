import uuid
from passlib.context import CryptContext
from .database import get_connection

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserModel:

    @staticmethod
    def create(name: str, email: str, password: str, role: str = "viewer") -> dict:
        uid = str(uuid.uuid4())
        password_hash = pwd_context.hash(password)
        conn = get_connection()
        conn.execute(
            "INSERT INTO users (id, name, email, password_hash, role) VALUES (?,?,?,?,?)",
            (uid, name, email, password_hash, role)
        )
        conn.commit()
        conn.close()
        return UserModel.find_by_id(uid)

    @staticmethod
    def find_by_id(uid: str) -> dict | None:
        conn = get_connection()
        row = conn.execute(
            "SELECT id, name, email, role, status, created_at, updated_at FROM users WHERE id = ?",
            (uid,)
        ).fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def find_by_email(email: str) -> dict | None:
        conn = get_connection()
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def find_all(status: str = None, role: str = None, page: int = 1, limit: int = 20) -> dict:
        conn = get_connection()
        where = "WHERE 1=1"
        params = []
        if status:
            where += " AND status = ?"; params.append(status)
        if role:
            where += " AND role = ?"; params.append(role)

        total = conn.execute(
            f"SELECT COUNT(*) as count FROM users {where}", params
        ).fetchone()["count"]

        rows = conn.execute(
            f"SELECT id, name, email, role, status, created_at, updated_at FROM users {where} "
            f"ORDER BY created_at DESC LIMIT ? OFFSET ?",
            params + [limit, (page - 1) * limit]
        ).fetchall()
        conn.close()

        import math
        return {
            "users": [dict(r) for r in rows],
            "total": total,
            "page": page,
            "limit": limit,
            "pages": math.ceil(total / limit) if total else 0
        }

    @staticmethod
    def update(uid: str, data: dict) -> dict | None:
        allowed = {k: v for k, v in data.items() if k in ("name", "role", "status") and v is not None}
        if not allowed:
            return UserModel.find_by_id(uid)
        fields = ", ".join(f"{k} = ?" for k in allowed)
        fields += ", updated_at = datetime('now')"
        conn = get_connection()
        conn.execute(f"UPDATE users SET {fields} WHERE id = ?", list(allowed.values()) + [uid])
        conn.commit()
        conn.close()
        return UserModel.find_by_id(uid)

    @staticmethod
    def delete(uid: str):
        conn = get_connection()
        conn.execute("DELETE FROM users WHERE id = ?", (uid,))
        conn.commit()
        conn.close()

    @staticmethod
    def verify_password(plain: str, hashed: str) -> bool:
        return pwd_context.verify(plain, hashed)
