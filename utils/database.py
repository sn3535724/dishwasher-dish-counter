import json
import sqlite3
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "history.db"


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                original_filename TEXT NOT NULL,
                upload_filename TEXT NOT NULL,
                result_filename TEXT NOT NULL,
                dish_count INTEGER NOT NULL,
                details_json TEXT NOT NULL,
                average_confidence REAL NOT NULL,
                processing_time REAL NOT NULL,
                mode TEXT NOT NULL,
                image_size INTEGER NOT NULL,
                confidence REAL NOT NULL
            )
        """)
        connection.commit()


def add_request(
    original_filename: str,
    upload_filename: str,
    result_filename: str,
    dish_count: int,
    class_counts: dict,
    average_confidence: float,
    processing_time: float,
    mode: str,
    image_size: int,
    confidence: float,
):
    timestamp = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    details_json = json.dumps(class_counts, ensure_ascii=False)

    with get_connection() as connection:
        connection.execute("""
            INSERT INTO requests (
                timestamp, original_filename, upload_filename, result_filename,
                dish_count, details_json, average_confidence, processing_time,
                mode, image_size, confidence
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            timestamp, original_filename, upload_filename, result_filename,
            dish_count, details_json, average_confidence, processing_time,
            mode, image_size, confidence,
        ))
        connection.commit()


def get_history(limit: int = 20):
    with get_connection() as connection:
        rows = connection.execute("""
            SELECT * FROM requests
            ORDER BY id DESC
            LIMIT ?
        """, (limit,)).fetchall()

    records = []
    for row in rows:
        record = dict(row)
        record["class_counts"] = json.loads(record["details_json"])
        records.append(record)
    return records


def clear_history():
    with get_connection() as connection:
        connection.execute("DELETE FROM requests")
        connection.commit()
