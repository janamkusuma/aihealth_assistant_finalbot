from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Dict, Any
import sqlite3
import os
from datetime import datetime

from app.auth import get_current_user

router = APIRouter(prefix="/api/quiz", tags=["Quiz"])

# ✅ DB file (same folder level as backend if you already have health.db)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))  # backend/app
DB_PATH = os.path.join(BASE_DIR, "health.db")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS quiz_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT,
            score INTEGER,
            total INTEGER,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()


class QuizSaveIn(BaseModel):
    score: int
    total: int


@router.post("/save")
def save_quiz_score(body: QuizSaveIn, user=Depends(get_current_user)) -> Dict[str, Any]:
    init_db()

    # user object shape can differ; handle both
    email = None
    if isinstance(user, dict):
        email = user.get("email") or user.get("username")
    else:
        email = getattr(user, "email", None) or getattr(user, "username", None) or "unknown"

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO quiz_scores (user_email, score, total, created_at) VALUES (?,?,?,?)",
        (email, int(body.score), int(body.total), datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

    return {"message": "saved"}


@router.get("/my-scores")
def my_scores(user=Depends(get_current_user)) -> List[Dict[str, Any]]:
    init_db()

    email = None
    if isinstance(user, dict):
        email = user.get("email") or user.get("username")
    else:
        email = getattr(user, "email", None) or getattr(user, "username", None) or "unknown"

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute(
        "SELECT score, total, created_at FROM quiz_scores WHERE user_email=? ORDER BY id DESC",
        (email,)
    )
    rows = cur.fetchall()
    conn.close()

    return [{"score": r["score"], "total": r["total"], "created_at": r["created_at"]} for r in rows]
