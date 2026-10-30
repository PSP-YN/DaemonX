"""
Thread-Safe SQLite Database Engine with FTS5 Full-Text Search and JSON/CSV/Markdown Exports
"""
import csv
import json
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any

from daemonx.core.config import DATABASE_PATH
from daemonx.core.exceptions import StorageError
from daemonx.storage.schema import SCHEMA_SQL, TAXONOMY_CATEGORIES


class Database:
    def __init__(self, db_path: Path | str = DATABASE_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        """Returns SQLite connection with WAL mode and row factory."""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def init_db(self):
        """Initializes tables and seeds taxonomy categories."""
        with self.get_connection() as conn:
            conn.executescript(SCHEMA_SQL)
            # Seed categories if not already present
            for cat_id, name, desc in TAXONOMY_CATEGORIES:
                conn.execute(
                    "INSERT OR IGNORE INTO categories (id, name, description) VALUES (?, ?, ?)",
                    (cat_id, name, desc)
                )
            conn.commit()

    # --- Media Items ---
    def insert_media_item(
        self,
        source_type: str,
        original_path: str | None = None,
        device_path: str | None = None,
        sha256: str | None = None,
        phash: str | None = None,
        width: int | None = None,
        height: int | None = None,
        file_size: int | None = None,
        media_id: str | None = None
    ) -> str:
        m_id = media_id or f"med_{uuid.uuid4().hex[:12]}"
        now = time.time()
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO media_items 
                (id, source_type, original_path, device_path, sha256, phash, width, height, file_size, created_at, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
                """,
                (m_id, source_type, original_path, device_path, sha256, phash, width, height, file_size, now)
            )
            conn.commit()
        return m_id

    def get_media_item(self, media_id: str) -> dict | None:
        with self.get_connection() as conn:
            row = conn.execute("SELECT * FROM media_items WHERE id = ?", (media_id,)).fetchone()
            return dict(row) if row else None

    def update_media_status(self, media_id: str, status: str, quarantine_path: str | None = None):
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE media_items SET status = ?, processed_at = ?, quarantine_path = coalesce(?, quarantine_path) WHERE id = ?",
                (status, time.time(), quarantine_path, media_id)
            )
            conn.commit()

    def find_duplicate_by_hash(self, sha256: str | None, phash: str | None) -> dict | None:
        if not sha256 and not phash:
            return None
        with self.get_connection() as conn:
            if sha256:
                row = conn.execute("SELECT * FROM media_items WHERE sha256 = ?", (sha256,)).fetchone()
                if row:
                    return dict(row)
            if phash:
                row = conn.execute("SELECT * FROM media_items WHERE phash = ?", (phash,)).fetchone()
                if row:
                    return dict(row)
        return None

    # --- Extracted Content ---
    def insert_extracted_content(
        self,
        media_id: str,
        full_text: str = "",
        ocr_confidence: float = 1.0,
        caption: str = "",
        creator: str = "",
        source_url: str = "",
        summary: str = ""
    ) -> str:
        c_id = f"cnt_{uuid.uuid4().hex[:12]}"
        now = time.time()
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO extracted_content 
                (id, media_id, full_text, ocr_confidence, caption, creator, source_url, summary, extracted_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (c_id, media_id, full_text, ocr_confidence, caption, creator, source_url, summary, now)
            )
            conn.commit()
        return c_id

    # --- Resources ---
    def insert_resource(
        self,
        media_id: str | None,
        resource_type: str,
        title: str,
        url: str | None = None,
        creator_or_author: str | None = None,
        description: str | None = None,
        metadata: dict | None = None
    ) -> str:
        r_id = f"res_{uuid.uuid4().hex[:12]}"
        meta_json = json.dumps(metadata or {})
        now = time.time()
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO resources (id, media_id, resource_type, title, url, creator_or_author, description, metadata_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (r_id, media_id, resource_type, title, url, creator_or_author, description, meta_json, now)
            )
            conn.commit()
        return r_id

    # --- Tags and Categories ---
    def add_tag(self, media_id: str, tag_name: str, category_name: str | None = None):
        with self.get_connection() as conn:
            tag_id = f"tag_{tag_name.lower().replace(' ', '_')}"
            conn.execute("INSERT OR IGNORE INTO tags (id, name) VALUES (?, ?)", (tag_id, tag_name))

            cat_id = None
            if category_name:
                row = conn.execute("SELECT id FROM categories WHERE name = ?", (category_name,)).fetchone()
                if row:
                    cat_id = row["id"]

            conn.execute(
                "INSERT OR IGNORE INTO media_tags (media_id, tag_id, category_id) VALUES (?, ?, ?)",
                (media_id, tag_id, cat_id)
            )
            conn.commit()

    # --- Full-Text Search ---
    def search(self, query: str, limit: int = 50) -> list[dict]:
        """Executes full-text search across FTS5 index and joins metadata."""
        if not query or not query.strip():
            return []

        # Sanitize query for FTS5 (escape quotes, append prefix wildcard)
        safe_q = query.replace('"', '""')
        fts_query = f'"{safe_q}"*'

        with self.get_connection() as conn:
            sql = """
            SELECT m.id as media_id, m.source_type, m.original_path, m.created_at,
                   c.full_text, c.caption, c.creator, c.summary, c.source_url,
                   rank
            FROM knowledge_fts f
            JOIN media_items m ON f.media_id = m.id
            LEFT JOIN extracted_content c ON m.id = c.media_id
            WHERE knowledge_fts MATCH ?
            ORDER BY rank
            LIMIT ?
            """
            try:
                rows = conn.execute(sql, (fts_query, limit)).fetchall()
                return [dict(r) for r in rows]
            except sqlite3.OperationalError:
                # Fallback to simple LIKE search if FTS query syntax error occurs
                fallback_sql = """
                SELECT m.id as media_id, m.source_type, m.original_path, m.created_at,
                       c.full_text, c.caption, c.creator, c.summary, c.source_url
                FROM media_items m
                LEFT JOIN extracted_content c ON m.id = c.media_id
                WHERE c.full_text LIKE ? OR c.caption LIKE ? OR c.creator LIKE ?
                LIMIT ?
                """
                like_pattern = f"%{query}%"
                rows = conn.execute(fallback_sql, (like_pattern, like_pattern, like_pattern, limit)).fetchall()
                return [dict(r) for r in rows]

    # --- Processing Jobs (Task Engine) ---
    def save_job(self, job_id: str, task_name: str, status: str, current_step: int, total_steps: int, state: dict):
        now = time.time()
        state_str = json.dumps(state)
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO processing_jobs 
                (id, task_name, status, current_step, total_steps, state_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, coalesce((SELECT created_at FROM processing_jobs WHERE id = ?), ?), ?)
                """,
                (job_id, task_name, status, current_step, total_steps, state_str, job_id, now, now)
            )
            conn.commit()

    def get_job(self, job_id: str) -> dict | None:
        with self.get_connection() as conn:
            row = conn.execute("SELECT * FROM processing_jobs WHERE id = ?", (job_id,)).fetchone()
            if not row:
                return None
            d = dict(row)
            d["state"] = json.loads(d["state_json"]) if d["state_json"] else {}
            return d

    def list_jobs(self, limit: int = 50) -> list[dict]:
        with self.get_connection() as conn:
            rows = conn.execute("SELECT * FROM processing_jobs ORDER BY updated_at DESC LIMIT ?", (limit,)).fetchall()
            return [dict(r) for r in rows]

    # --- Cleanup and Audit Logging ---
    def log_cleanup(self, media_id: str, action: str, original_path: str, quarantine_path: str | None = None, verified: bool = False, details: str = ""):
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO cleanup_log (id, media_id, action, original_path, quarantine_path, performed_at, verified, details)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (f"cln_{uuid.uuid4().hex[:12]}", media_id, action, original_path, quarantine_path, time.time(), int(verified), details)
            )
            conn.commit()

    def log_audit(self, event_type: str, description: str, actor: str = "daemonx_agent", metadata: dict | None = None):
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO audit_log (id, event_type, description, actor, timestamp, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (f"aud_{uuid.uuid4().hex[:12]}", event_type, description, actor, time.time(), json.dumps(metadata or {}))
            )
            conn.commit()

    # --- Exports (JSON, CSV, Markdown) ---
    def export_knowledge(self, format: str = "json") -> str:
        with self.get_connection() as conn:
            rows = conn.execute(
                """
                SELECT m.id, m.source_type, m.original_path, m.created_at, m.status,
                       c.full_text, c.caption, c.creator, c.summary, c.source_url
                FROM media_items m
                LEFT JOIN extracted_content c ON m.id = c.media_id
                ORDER BY m.created_at DESC
                """
            ).fetchall()
            records = [dict(r) for r in rows]

        if format.lower() == "json":
            return json.dumps(records, indent=2, default=str)
        elif format.lower() == "csv":
            import io
            buf = io.StringIO()
            if records:
                writer = csv.DictWriter(buf, fieldnames=records[0].keys())
                writer.writeheader()
                writer.writerows(records)
            return buf.getvalue()
        elif format.lower() == "markdown":
            lines = ["# DAEMONX Knowledge Export\n"]
            for r in records:
                lines.append(f"## {r['id']} ({r['source_type']})")
                if r.get("creator"):
                    lines.append(f"- **Creator**: @{r['creator']}")
                if r.get("source_url"):
                    lines.append(f"- **URL**: {r['source_url']}")
                if r.get("caption"):
                    lines.append(f"- **Caption**: {r['caption']}")
                if r.get("summary"):
                    lines.append(f"- **Summary**: {r['summary']}")
                if r.get("full_text"):
                    lines.append(f"\n```text\n{r['full_text']}\n```\n")
                lines.append("---\n")
            return "\n".join(lines)
        else:
            raise StorageError(f"Unsupported export format '{format}'")
