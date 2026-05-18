import sqlite3
import os
from datetime import date

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "keenpie.db")


def _ensure_dir():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


def get_conn():
    _ensure_dir()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS task_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            sort_order INTEGER NOT NULL DEFAULT 0,
            content TEXT NOT NULL DEFAULT '',
            time_label TEXT,
            time_value TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            note TEXT DEFAULT '',
            metadata TEXT DEFAULT '{}'
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_date_order ON task_items(date, sort_order)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_date_status ON task_items(date, status)")
    conn.commit()
    conn.close()


def get_tasks_by_date(target_date: str) -> list[dict]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM task_items WHERE date=? ORDER BY sort_order",
        (target_date,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_pending_tasks(target_date: str, limit: int = 4) -> list[dict]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM task_items WHERE date=? AND status='pending' ORDER BY sort_order LIMIT ?",
        (target_date, limit)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def upsert_task(task: dict) -> int:
    conn = get_conn()
    if task.get("id"):
        conn.execute("""
            UPDATE task_items
            SET date=?, sort_order=?, content=?, time_label=?, time_value=?, status=?, note=?, metadata=?
            WHERE id=?
        """, (
            task["date"], task["sort_order"], task["content"],
            task.get("time_label"), task.get("time_value"),
            task.get("status", "pending"), task.get("note", ""),
            task.get("metadata", "{}"), task["id"]
        ))
        conn.commit()
        conn.close()
        return task["id"]
    else:
        cur = conn.execute("""
            INSERT INTO task_items (date, sort_order, content, time_label, time_value, status, note, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            task["date"], task["sort_order"], task["content"],
            task.get("time_label"), task.get("time_value"),
            task.get("status", "pending"), task.get("note", ""),
            task.get("metadata", "{}")
        ))
        conn.commit()
        new_id = cur.lastrowid
        conn.close()
        return new_id


def update_task_status(task_id: int, status: str):
    conn = get_conn()
    conn.execute("UPDATE task_items SET status=? WHERE id=?", (status, task_id))
    conn.commit()
    conn.close()


def update_task_note(task_id: int, note: str):
    conn = get_conn()
    conn.execute("UPDATE task_items SET note=? WHERE id=?", (note, task_id))
    conn.commit()
    conn.close()


def delete_task(task_id: int):
    conn = get_conn()
    conn.execute("DELETE FROM task_items WHERE id=?", (task_id,))
    conn.commit()
    conn.close()


def reorder_tasks(target_date: str, task_ids: list[int]):
    conn = get_conn()
    for i, tid in enumerate(task_ids):
        conn.execute("UPDATE task_items SET sort_order=? WHERE id=?", (i, tid))
    conn.commit()
    conn.close()


def get_distinct_dates(limit: int = 7, before_date: str | None = None) -> list[str]:
    conn = get_conn()
    if before_date:
        rows = conn.execute(
            "SELECT DISTINCT date FROM task_items WHERE date < ? ORDER BY date DESC LIMIT ?",
            (before_date, limit)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT DISTINCT date FROM task_items WHERE date <= ? ORDER BY date DESC LIMIT ?",
            (str(date.today()), limit)
        ).fetchall()
    conn.close()
    return [r["date"] for r in rows]


def export_all_data() -> list[dict]:
    conn = get_conn()
    rows = conn.execute("SELECT * FROM task_items ORDER BY date DESC, sort_order").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def clear_all_data():
    conn = get_conn()
    conn.execute("DELETE FROM task_items")
    conn.commit()
    conn.close()
