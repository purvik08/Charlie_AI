import hashlib
import json
import logging
import math
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional


logger = logging.getLogger(__name__)


class RetrievalMemory:
    """SQLite retrieval memory with cached lightweight offline embeddings."""

    def __init__(self, db_path: str, dimensions: int = 128, retention_limit: int = 500) -> None:
        self.db_path = Path(db_path)
        self.dimensions = dimensions
        self.retention_limit = retention_limit
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    user_input TEXT NOT NULL,
                    assistant_response TEXT NOT NULL,
                    summary TEXT,
                    embedding TEXT NOT NULL,
                    metadata TEXT
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_conversation_timestamp ON conversations(timestamp)")

    def add(self, user_input: str, assistant_response: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        embedding = self.embed(f"{user_input}\n{assistant_response}")
        summary = self._summarize(user_input, assistant_response)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO conversations
                (timestamp, user_input, assistant_response, summary, embedding, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    time.time(),
                    user_input,
                    assistant_response,
                    summary,
                    json.dumps(embedding),
                    json.dumps(metadata or {}),
                ),
            )
            self._enforce_retention(conn)

    def retrieve(self, query: str, limit: int = 4) -> List[Dict[str, Any]]:
        start = time.perf_counter()
        query_embedding = self.embed(query)
        rows = []
        with self._connect() as conn:
            for row in conn.execute(
                "SELECT id, timestamp, user_input, assistant_response, summary, embedding, metadata FROM conversations"
            ):
                try:
                    embedding = json.loads(row[5])
                    score = self.cosine_similarity(query_embedding, embedding)
                    rows.append((score, row))
                except Exception:
                    continue
        rows.sort(key=lambda item: item[0], reverse=True)
        logger.info(
            "memory_retrieval_complete",
            extra={"latency_seconds": round(time.perf_counter() - start, 3), "rows": len(rows)},
        )
        return [
            {
                "id": row[0],
                "timestamp": row[1],
                "user": row[2],
                "assistant": row[3],
                "summary": row[4],
                "score": score,
                "metadata": json.loads(row[6] or "{}"),
            }
            for score, row in rows[:limit]
            if score > 0.05
        ]

    def embed(self, text: str) -> List[float]:
        """CPU-cheap hashed embedding fallback, deterministic and fully offline."""
        vector = [0.0] * self.dimensions
        for token in text.lower().split():
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            idx = int.from_bytes(digest[:4], "little") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[idx] += sign
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]

    @staticmethod
    def cosine_similarity(a: List[float], b: List[float]) -> float:
        if not a or not b or len(a) != len(b):
            return 0.0
        return sum(x * y for x, y in zip(a, b))

    @staticmethod
    def _summarize(user_input: str, assistant_response: str) -> str:
        text = f"User: {user_input} Assistant: {assistant_response}"
        return text[:240]

    def _enforce_retention(self, conn: sqlite3.Connection) -> None:
        conn.execute(
            """
            DELETE FROM conversations
            WHERE id NOT IN (
                SELECT id FROM conversations ORDER BY timestamp DESC LIMIT ?
            )
            """,
            (self.retention_limit,),
        )

