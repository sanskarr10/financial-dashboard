import uuid
import math
from .database import get_connection

class RecordModel:

    @staticmethod
    def create(amount: float, type_: str, category: str, date: str,
               created_by: str, notes: str = None) -> dict:
        uid = str(uuid.uuid4())
        conn = get_connection()
        conn.execute(
            "INSERT INTO financial_records (id, amount, type, category, date, notes, created_by) "
            "VALUES (?,?,?,?,?,?,?)",
            (uid, amount, type_, category, date, notes, created_by)
        )
        conn.commit()
        conn.close()
        return RecordModel.find_by_id(uid)

    @staticmethod
    def find_by_id(uid: str) -> dict | None:
        conn = get_connection()
        row = conn.execute(
            "SELECT r.*, u.name as created_by_name FROM financial_records r "
            "JOIN users u ON r.created_by = u.id "
            "WHERE r.id = ? AND r.deleted_at IS NULL", (uid,)
        ).fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def find_all(type_: str = None, category: str = None,
                 start_date: str = None, end_date: str = None,
                 page: int = 1, limit: int = 20) -> dict:
        conn = get_connection()
        where = "WHERE r.deleted_at IS NULL"
        params = []
        if type_:       where += " AND r.type = ?";       params.append(type_)
        if category:    where += " AND r.category = ?";   params.append(category)
        if start_date:  where += " AND r.date >= ?";      params.append(start_date)
        if end_date:    where += " AND r.date <= ?";      params.append(end_date)

        total = conn.execute(
            f"SELECT COUNT(*) as count FROM financial_records r {where}", params
        ).fetchone()["count"]

        rows = conn.execute(
            f"SELECT r.*, u.name as created_by_name FROM financial_records r "
            f"JOIN users u ON r.created_by = u.id {where} "
            f"ORDER BY r.date DESC, r.created_at DESC LIMIT ? OFFSET ?",
            params + [limit, (page - 1) * limit]
        ).fetchall()
        conn.close()

        return {
            "records": [dict(r) for r in rows],
            "total": total,
            "page": page,
            "limit": limit,
            "pages": math.ceil(total / limit) if total else 0
        }

    @staticmethod
    def update(uid: str, data: dict) -> dict | None:
        allowed = {k: v for k, v in data.items()
                   if k in ("amount", "type", "category", "date", "notes") and v is not None}
        if not allowed:
            return RecordModel.find_by_id(uid)
        fields = ", ".join(f"{k} = ?" for k in allowed)
        fields += ", updated_at = datetime('now')"
        conn = get_connection()
        conn.execute(
            f"UPDATE financial_records SET {fields} WHERE id = ? AND deleted_at IS NULL",
            list(allowed.values()) + [uid]
        )
        conn.commit()
        conn.close()
        return RecordModel.find_by_id(uid)

    @staticmethod
    def soft_delete(uid: str):
        conn = get_connection()
        conn.execute(
            "UPDATE financial_records SET deleted_at = datetime('now') WHERE id = ? AND deleted_at IS NULL",
            (uid,)
        )
        conn.commit()
        conn.close()

    # ── Analytics ──────────────────────────────────────────────────────────────

    @staticmethod
    def get_totals(start_date: str = None, end_date: str = None) -> dict:
        conn = get_connection()
        where = "WHERE deleted_at IS NULL"
        params = []
        if start_date: where += " AND date >= ?"; params.append(start_date)
        if end_date:   where += " AND date <= ?"; params.append(end_date)
        row = conn.execute(f"""
            SELECT
                COALESCE(SUM(CASE WHEN type='income'  THEN amount ELSE 0   END), 0) as total_income,
                COALESCE(SUM(CASE WHEN type='expense' THEN amount ELSE 0   END), 0) as total_expenses,
                COALESCE(SUM(CASE WHEN type='income'  THEN amount ELSE -amount END), 0) as net_balance,
                COUNT(*) as total_records
            FROM financial_records {where}
        """, params).fetchone()
        conn.close()
        return dict(row)

    @staticmethod
    def get_category_totals(type_: str = None, start_date: str = None, end_date: str = None) -> list:
        conn = get_connection()
        where = "WHERE deleted_at IS NULL"
        params = []
        if type_:      where += " AND type = ?";    params.append(type_)
        if start_date: where += " AND date >= ?";   params.append(start_date)
        if end_date:   where += " AND date <= ?";   params.append(end_date)
        rows = conn.execute(f"""
            SELECT category, type, SUM(amount) as total, COUNT(*) as count
            FROM financial_records {where}
            GROUP BY category, type ORDER BY total DESC
        """, params).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def get_monthly_trends(year: int = None) -> list:
        from datetime import datetime
        target_year = str(year or datetime.now().year)
        conn = get_connection()
        rows = conn.execute("""
            SELECT
                strftime('%Y-%m', date) as month,
                SUM(CASE WHEN type='income'  THEN amount ELSE 0      END) as income,
                SUM(CASE WHEN type='expense' THEN amount ELSE 0      END) as expenses,
                SUM(CASE WHEN type='income'  THEN amount ELSE -amount END) as net
            FROM financial_records
            WHERE deleted_at IS NULL AND strftime('%Y', date) = ?
            GROUP BY month ORDER BY month ASC
        """, (target_year,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def get_weekly_trends() -> list:
        conn = get_connection()
        rows = conn.execute("""
            SELECT
                strftime('%Y-W%W', date) as week,
                SUM(CASE WHEN type='income'  THEN amount ELSE 0      END) as income,
                SUM(CASE WHEN type='expense' THEN amount ELSE 0      END) as expenses,
                SUM(CASE WHEN type='income'  THEN amount ELSE -amount END) as net
            FROM financial_records
            WHERE deleted_at IS NULL AND date >= date('now', '-12 weeks')
            GROUP BY week ORDER BY week ASC
        """).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def get_recent_activity(limit: int = 10) -> list:
        conn = get_connection()
        rows = conn.execute(
            "SELECT r.*, u.name as created_by_name FROM financial_records r "
            "JOIN users u ON r.created_by = u.id "
            "WHERE r.deleted_at IS NULL ORDER BY r.created_at DESC LIMIT ?",
            (limit,)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]
