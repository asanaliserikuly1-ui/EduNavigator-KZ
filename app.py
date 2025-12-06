import os
import json
import requests
import re
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

# ---- DB IMPORTS ----
from db.database import (
    init_db,
    get_all_universities,
    get_university_by_id,
    search_universities,
)
from ai.compare_ai import compare_universities


# ---- SYSTEM CONFIG ----
load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TOURS_DIR = os.path.join(BASE_DIR, "data", "tours")

# ---- OLLAMA CONFIG ----
OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "qwen2.5:7b"


# ---- ASK AI ----
def ask_ollama(messages):
    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": False
    }
    try:
        r = requests.post(OLLAMA_URL, json=payload, timeout=60)
        r.raise_for_status()
        data = r.json()

        return data.get("message", {}).get("content", "")
    except Exception as e:
        print("OLLAMA ERROR:", e)
        return ""


# ---- LOAD TOUR ----
def load_tour(tour_id):
    path = os.path.join(TOURS_DIR, f"{tour_id}.json")
    if not os.path.exists(path):
        return None
    return json.load(open(path, "r", encoding="utf-8"))


# ---- SCENE DESCRIPTION GENERATOR ----
def describe_scene(scene):
    desc = (scene.get("description") or "").strip()
    if desc:
        return desc

    title = scene.get("title", "")
    if not title:
        return ""

    prompt = [
        {"role": "system",
         "content": "Ты создаёшь короткие описания локаций для 3D-туров. Пиши только на русском языке."},
        {"role": "user", "content": f"Опиши локацию '{title}' в 1–2 предложениях."}
    ]

    return ask_ollama(prompt)


# ---- SYSTEM PROMPT BUILDER ----
def build_system_prompt(tour, current_scene):
    scenes = tour.get("scenes", {})
    scene_list = "\n".join(
        f"- id: {sid}\n  title: {s.get('title')}\n  description: {s.get('description', '')}"
        for sid, s in scenes.items()
    )

    return f"""
Ты — профессиональный ИИ-гид кампуса.

Цель: помогать человеку ориентироваться на территории университета, как экскурсовод.

=== ЛОКАЦИИ ===
{scene_list}

=== ПРАВИЛА ===
1. Отвечай ТОЛЬКО на чистом русском языке.
2. Говори кратко — 1–3 предложения.
3. Если пользователь спрашивает о локации — объясни простыми словами.
4. Если description пустое — придумай короткое описание.
5. Не отправляй JSON, просто отвечай словами.
6. Будь дружелюбным экскурсоводом.

Текущая сцена: {current_scene}
"""


# ========================================================
#   MAIN APP
# ========================================================
def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")

    init_db()

    # ==== MAIN WEBSITE ====

    @app.route("/")
    def index():
        return render_template("index.html", active_page="home")

    @app.route("/universities")
    def universities_page():
        universities = get_all_universities()
        return render_template(
            "universities.html",
            active_page="universities",
            universities=universities,
        )

    @app.route("/compare")
    def compare_page():
        return render_template("compare.html", active_page="compare")

    @app.route("/international")
    def intl_programs():
        return render_template("intlprograms.html", active_page="intl")

    @app.route("/about")
    def about():
        return render_template("about.html", active_page="about")

    # ==== 3D TOUR ROUTES ====

    @app.route("/3d")
    def tours_3d():
        try:
            tours = [
                f.replace(".json", "")
                for f in os.listdir(TOURS_DIR)
                if f.lower().endswith(".json")
            ]
        except:
            tours = []

        return render_template("tours_3d.html", tours=tours, active_page="3d")

    @app.route("/tour/<tour_id>")
    def tour_page(tour_id):
        tour = load_tour(tour_id)
        if not tour:
            return "NOT FOUND", 404

        return render_template(
            "tour/viewer.html",
            tour_id=tour_id,
            tour_title=tour.get("title", "")
        )

    @app.route("/api/tour/<tour_id>")
    def api_tour(tour_id):
        tour = load_tour(tour_id)
        if not tour:
            return jsonify({"error": "not found"}), 404
        return jsonify(tour)

    # ==== AI ASSISTANT ====

    @app.route("/api/assistant", methods=["POST"])
    def api_assistant():
        data = request.json or {}

        tour_id = data.get("tour_id")
        current_scene = data.get("current_scene")
        user_message = data.get("message", "").strip()

        tour = load_tour(tour_id)
        if not tour:
            return jsonify({"text": "Тур не найден, попробуй перезагрузить страницу."}), 404

        scenes = tour.get("scenes", {})

        # === MINI INFO handler ===
        if user_message in ("_mini_info_", "__mini_info__", "mini_info"):
            scene = scenes.get(current_scene)
            if not scene:
                return jsonify({"text": "Описание этой локации пока недоступно."})

            title = scene.get("title", "Локация")
            description = (scene.get("description") or "").strip()

            if not description:
                description = describe_scene(scene)

            return jsonify({"text": description})

        # === BUILD SYSTEM PROMPT ===
        system_prompt = build_system_prompt(tour, current_scene)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]

        # === ASK AI ===
        answer = ask_ollama(messages)

        # === Anti-Chinese/English Filter ===
        if not answer or len(re.findall(r"[А-Яа-яЁё]", answer)) < 3:
            retry = [
                {"role": "system", "content": "Отвечай ТОЛЬКО на чистом русском языке, как экскурсовод."},
                {"role": "user", "content": user_message}
            ]
            answer = ask_ollama(retry)

        if not answer or len(re.findall(r"[А-Яа-яЁё]", answer)) < 3:
            answer = "Немного запутался — повтори вопрос, я отвечу на чистом русском 😊"

        return jsonify({"text": answer})

    # ==== API FOR UNIVERSITY COMPARISON ====

    @app.get("/api/universities")
    def api_universities():
        return jsonify(get_all_universities())

    @app.get("/api/search")
    def api_search():
        query = request.args.get("q", "").strip()
        if not query:
            return jsonify([])
        return jsonify(search_universities(query, limit=10))

    @app.post("/api/compare_ai")
    def api_compare_ai():
        data = request.get_json(silent=True) or {}
        id1 = data.get("id1")
        id2 = data.get("id2")
        goal = data.get("goal")

        if not id1 or not id2:
            return jsonify({"error": "Нужно передать id1 и id2"}), 400

        if id1 == id2:
            return jsonify({"error": "Выберите два разных университета"}), 400

        uni1 = get_university_by_id(int(id1))
        uni2 = get_university_by_id(int(id2))

        if not uni1 or not uni2:
            return jsonify({"error": "Университет не найден"}), 404

        try:
            text = compare_universities(uni1, uni2, goal=goal)
        except Exception as exc:
            print("AI error:", exc)
            return jsonify({"error": "Ошибка при обращении к ИИ"}), 500

        return jsonify({"result": text})

    @app.route("/favicon.ico")
    def favicon():
        return "", 204

    return app


# ==== RUN APP ====
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
