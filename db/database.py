"""
Модуль работы с базой данных SQLite для университетов.

Зависимости:
    стандартная библиотека (sqlite3, json, os)

Файл БД:
    db/universities.db  (расположен рядом с этим модулем)
"""

import json
import os
import sqlite3
from contextlib import contextmanager
from typing import Any, Dict, Iterable, List, Optional

# Путь до файла БД относительно текущего файла
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "universities.db")

# Поля, в которых мы ожидаем JSON-строки
JSON_FIELDS = ("programs", "reviews", "languages")


@contextmanager
def get_connection():
    """
    Контекстный менеджер для подключения к БД.
    Всегда использует row_factory=sqlite3.Row, чтобы удобно работать со словарями.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    """
    Создаёт таблицу universities, если её ещё нет.
    Вставку данных ты делаешь сам отдельно.
    """
    ddl = """
    CREATE TABLE IF NOT EXISTS universities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        city TEXT,
        type TEXT,                  -- 'public', 'private' и т.п., можно не заполнять
        rating REAL,
        tuition_fee INTEGER,        -- в тенге за год (примерная стоимость)
        programs TEXT,              -- JSON-массив строк
        languages TEXT,             -- JSON-массив языков обучения, например ["ru","kz","en"]
        international_score REAL,   -- 0–10
        employment_rate REAL,       -- 0–1 или 0–100
        reviews TEXT,               -- JSON-массив строк
        image_url TEXT              -- ссылка на фотографию университета
    );
    """
    with get_connection() as conn:
        conn.execute(ddl)


def _parse_json_field(value: Optional[str]) -> List[Any]:
    if not value:
        return []
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return []


def _row_to_university(row: sqlite3.Row) -> Dict[str, Any]:
    """
    Преобразует sqlite3.Row в удобный словарь для приложения и ИИ.
    """
    if row is None:
        return {}

    uni = dict(row)

    # Распарсим JSON-поля
    for field in JSON_FIELDS:
        if field in uni:
            uni[field] = _parse_json_field(uni.get(field))

    return uni


def get_university_by_id(uid: int) -> Optional[Dict[str, Any]]:
    """
    Возвращает один университет по id или None.
    """
    with get_connection() as conn:
        cur = conn.execute("SELECT * FROM universities WHERE id = ?", (uid,))
        row = cur.fetchone()

    if not row:
        return None

    return _row_to_university(row)


def get_all_universities(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Лёгкий список для UI: только то, что нужно для карточек.
    """
    sql = """
        SELECT id, name, city, rating, image_url
        FROM universities
        ORDER BY rating DESC NULLS LAST, name ASC
    """
    if limit is not None:
        sql += f" LIMIT {int(limit)}"

    with get_connection() as conn:
        cur = conn.execute(sql)
        rows = cur.fetchall()

    result = []
    for r in rows:
        item = dict(r)
        # для совместимости с фронтом можно дублировать image_url в img
        item["img"] = item.get("image_url")
        result.append(item)

    return result


def search_universities(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Поиск по названию (LIKE %query%).
    """
    q = f"%{query.strip()}%"
    with get_connection() as conn:
        cur = conn.execute(
            """
            SELECT id, name, city, rating, image_url
            FROM universities
            WHERE name LIKE ?
            ORDER BY rating DESC NULLS LAST, name ASC
            LIMIT ?
            """,
            (q, limit),
        )
        rows = cur.fetchall()

    result = []
    for r in rows:
        item = dict(r)
        item["img"] = item.get("image_url")
        result.append(item)

    return result


def get_universities_by_ids(ids: Iterable[int]) -> List[Dict[str, Any]]:
    """
    Утилита на будущее: получить несколько университетов по списку id.
    Сейчас в основном используется get_university_by_id, но это пригодится.
    """
    ids = [int(i) for i in ids]
    if not ids:
        return []

    placeholders = ",".join("?" for _ in ids)
    sql = f"SELECT * FROM universities WHERE id IN ({placeholders})"

    with get_connection() as conn:
        cur = conn.execute(sql, ids)
        rows = cur.fetchall()

    return [_row_to_university(r) for r in rows]