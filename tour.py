import os, json, requests, re
from flask import Flask, render_template, jsonify, request

app = Flask(__name__, template_folder="templates", static_folder="static")
TOURS_DIR = os.path.join("data", "tours")

# --------------------------
#  OLLAMA CONFIG
# --------------------------
OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "qwen2.5:7b"



def ask_ollama(messages):
    """Отправляет чат-запрос локальной модели Ollama."""
    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": False
    }
    try:
        r = requests.post(OLLAMA_URL, json=payload, timeout=60)
        r.raise_for_status()
        data = r.json()

        # Если Ollama выдала ошибку внутри JSON
        if "message" not in data or not data["message"].get("content"):
            return "Извините, я временно недоступен. Попробуйте ещё раз."

        return data["message"]["content"]

    except Exception as e:
        print("OLLAMA ERROR:", e)
        return "Ассистент временно недоступен."



# --------------------------
#  LOAD TOUR JSON
# --------------------------
def load_tour(tour_id):
    path = os.path.join(TOURS_DIR, f"{tour_id}.json")
    if not os.path.exists(path):
        return None
    return json.load(open(path, "r", encoding="utf-8"))


# --------------------------
#  SMART SCENE DESCRIPTION
# --------------------------
def describe_scene(scene):
    desc = scene.get("description", "").strip()
    if desc:
        return desc

    title = scene.get("title", "")

    prompt = [
        {"role": "system", "content": "Ты создаёшь короткие описания локаций для 3D-туров."},
        {"role": "user", "content": f"Опиши сцену '{title}' в 1–2 предложениях."}
    ]

    return ask_ollama(prompt)


# --------------------------
#  SYSTEM PROMPT
# --------------------------
def build_system_prompt(tour, current_scene):
    scenes = tour["scenes"]

    scene_list = "\n".join(
        f"- id: {sid}\n  title: {s.get('title')}\n  description: {s.get('description','')}"
        for sid, s in scenes.items()
    )

    return f"""
Ты — продвинутый ИИ-гид DataHub в 3D-туре '{tour.get("title")}'.

ТВОИ ВОЗМОЖНОСТИ:
• Кратко объяснять, где находится пользователь.
• Давать справочную информацию по локациям.
• Отвечать на вопросы в чате.
• Совершать переходы между сценами по запросу пользователя.
• Если сцена изменена — создавать краткое описание.

=== ЛОКАЦИИ ===
{scene_list}

=== ПРАВИЛА ===
1. Всегда отвечай по-русски.
2. Кратко, дружелюбно, без воды.
3. Не придумывай сцен, которых нет.
4. Для перехода всегда возвращай JSON:
   {{"action":"goto","scene":"id"}}
5. На команду "_mini_info_" — просто верни краткое описание сцены.
6. На команду "Опиши эту локацию." — опиши текущую сцену.
7. Если description пустое — придумай описание сам.

Текущая сцена: {current_scene}
"""


# --------------------------
#  ROUTES
# --------------------------
@app.route("/")
def index():
    tours = [t.replace(".json", "") for t in os.listdir(TOURS_DIR) if t.endswith(".json")]
    return render_template("tours_3d.html", tours=tours)


@app.route("/tour/<tour_id>")
def tour_page(tour_id):
    tour = load_tour(tour_id)
    if not tour:
        return "NOT FOUND", 404
    return render_template("tour/viewer.html",
                           tour_id=tour_id,
                           tour_title=tour.get("title", ""))


@app.route("/api/tour/<tour_id>")
def api_tour(tour_id):
    tour = load_tour(tour_id)
    if not tour:
        return jsonify({"error": "not found"}), 404
    return jsonify(tour)


# --------------------------
#   AI ENDPOINT
# --------------------------
@app.route("/api/assistant", methods=["POST"])
def api_assistant():
    data = request.json or {}

    tour_id = data.get("tour_id")
    current_scene = data.get("current_scene")
    user_message = data.get("message", "").strip()

    tour = load_tour(tour_id)
    scenes = tour["scenes"]

    # ====== АВТО-ОПИСАНИЕ СЦЕНЫ (мини-инфо) ======
    if user_message == "_mini_info_":
        scene = scenes[current_scene]
        title = scene.get("title", "Локация")

        description = scene.get("description")
        if not description:
            # fallback если нет описания — в стиле экскурсовода
            description = (
                f"Вы находитесь в локации «{title}». "
                f"Это место является важной частью кампуса. "
                f"Здесь обычно проходят различные мероприятия или активность, "
                f"связанная с этой зоной."
            )

        return jsonify({"text": description})

    # ====== SYSTEM PROMPT СТИЛЬ ЭКСКУРСОВОДА ======
    system_prompt = (
        "Ты — профессиональный экскурсовод в 3D-туре по университету. "
        "Всегда отвечай ТОЛЬКО на чистом русском языке. "
        "Запрещено использовать китайские, английские или другие языки. "
        "Стиль ответа: дружелюбный, спокойный, как экскурсовод, "
        "который объясняет пользователю, что он видит вокруг. "
        "Отвечай кратко (1–3 предложения), без воды. "
        "Если пользователь спрашивает о локации, опиши её так, "
        "как будто стоишь рядом и рассказываешь. "
        "Если спрашивает что-то другое — дай понятный, вежливый ответ."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]

    # ====== Запрос к Ollama ======
    answer = ask_ollama(messages)

    # Fallback если Ollama вернул ошибку
    if not answer or "Ошибка" in str(answer):
        answer = (
            "Прошу прощения, у меня возникла небольшая пауза. "
            "Попробуйте повторить вопрос, и я с радостью продолжу экскурсию!"
        )

    return jsonify({"text": answer})



if __name__ == "__main__":
    app.run(debug=True)