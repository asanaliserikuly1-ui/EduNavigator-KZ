# app.py
from flask import Flask, render_template, request, jsonify
from database import init_db, get_db

app = Flask(__name__)

# --- Инициализация базы при старте приложения ---
# Без seed, чтобы не дублировать данные каждый запуск
init_db(seed=False)


# --- Основные страницы ---
@app.route("/")
def index():
    return render_template("index.html", active_page="home")


@app.route("/universities")
def universities_page():
    return render_template("universities.html", active_page="universities")


@app.route("/compare")
def compare():
    return render_template("compare.html", active_page="compare")


@app.route("/3d")
def tours_3d():
    return render_template("tours_3d.html", active_page="tours_3d")


@app.route("/international")
def intl_programs():
    return render_template("intlprograms.html", active_page="intl")


@app.route("/about")
def about():
    return render_template("about.html", active_page="about")


# --- API: Поиск университетов ---
@app.route("/api/search")
def api_search():
    query = (request.args.get("q") or "").strip().lower()
    city = (request.args.get("city") or "").strip().lower()

    conn = get_db()
    cur = conn.cursor()

    sql = "SELECT * FROM universities WHERE 1=1"
    params = []

    if query:
        # Ищем и по имени, и по описанию
        sql += " AND (LOWER(name) LIKE ? OR LOWER(description) LIKE ?)"
        like = f"%{query}%"
        params.extend([like, like])

    if city:
        # точное совпадение города (но без учёта регистра)
        sql += " AND LOWER(city) = ?"
        params.append(city)

    cur.execute(sql, params)
    rows = cur.fetchall()
    conn.close()

    results = [dict(row) for row in rows]

    return jsonify(results)


if __name__ == "__main__":
    # Локальный запуск
    app.run(debug=True)