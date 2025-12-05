# database.py
import sqlite3
import os
from pathlib import Path

# Абсолютный путь к базе, чтобы не было сюрпризов при запуске из разных мест
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "universities.db"


def get_db():
    """
    Возвращает подключение к базе данных.
    ВНИМАНИЕ: вызывающий код обязан сам закрывать conn.close().
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(seed: bool = False):
    """
    Создаёт базу и таблицу universities, если их нет.
    Если seed=True — заполняет тестовыми данными.
    """
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS universities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            city TEXT NOT NULL,
            image TEXT,
            description TEXT
        )
        """
    )

    conn.commit()

    if seed:
        seed_sample_data(conn)

    conn.close()
    print("✔ База создана / проверена.")


def add_university(name: str, city: str, image: str, description: str, conn=None):
    """
    Добавление одного университета.
    Можно передавать существующее conn (для массовой загрузки).
    """
    close_after = False
    if conn is None:
        conn = get_db()
        close_after = True

    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO universities (name, city, image, description)
        VALUES (?, ?, ?, ?)
        """,
        (name, city, image, description),
    )

    conn.commit()
    if close_after:
        conn.close()

    print(f"✔ Добавлен университет: {name}")


def seed_sample_data(conn=None):
    """
    Добавление примерных университетов для теста.
    Здесь можно потом заменить на 77 универов.
    """
    close_after = False
    if conn is None:
        conn = get_db()
        close_after = True

    sample = [
        ("SDU University", "Kaskelen", "/static/universities/sdu.jpg",
         "Современный кампус, сильные IT и бизнес программы."),
        ("IITU", "Almaty", "/static/universities/iitu.jpg",
         "IT университет, готовящий программистов и инженеров."),
        ("AITU", "Astana", "/static/universities/aitu.jpg",
         "Международный IT университет в столице."),
        ("KBTU", "Almaty", "/static/universities/kbtu.jpg",
         "Технологический университет с инженерными направлениями."),
        ("KazNU", "Almaty", "/static/universities/kaznu.jpg",
         "Крупнейший национальный университет Казахстана."),
    ]

    cur = conn.cursor()

    # Проверим, пустая ли таблица — чтобы не дублировать при каждом запуске
    cur.execute("SELECT COUNT(*) AS cnt FROM universities")
    count = cur.fetchone()["cnt"]
    if count == 0:
        for uni in sample:
            add_university(*uni, conn=conn)
        print("✔ Загружены примерные данные (5 университетов).")
    else:
        print("ℹ Данные уже есть, seed пропущен.")

    if close_after:
        conn.close()


if __name__ == "__main__":
    # Если запустить python database.py — создаст БД и зальёт sample
    init_db(seed=True)