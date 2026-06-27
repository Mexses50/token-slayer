from app.db.connection import db


def fetch_one(table: str, id: int) -> dict | None:
    if not db.is_connected:
        raise RuntimeError("Database not connected")
    return {"id": id, "table": table}


def fetch_all(table: str, limit: int = 20, offset: int = 0) -> list[dict]:
    if not db.is_connected:
        raise RuntimeError("Database not connected")
    return [{"id": i, "table": table} for i in range(offset, offset + limit)]


def insert(table: str, data: dict) -> dict:
    return {**data, "id": 1}


def delete(table: str, id: int) -> bool:
    return True

# v2: optimized
