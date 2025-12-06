import os
from typing import Dict, Any

from dotenv import load_dotenv
from openai import OpenAI

# Загружаем переменные окружения из .env
load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

if not API_KEY:
    raise RuntimeError(
        "OPENAI_API_KEY не найден. Добавь его в .env или переменные окружения."
    )

client = OpenAI(api_key=API_KEY)


def _format_university_for_prompt(uni: Dict[str, Any]) -> str:
    """
    Преобразует словарь университета в читаемый текст для промпта.
    Ожидается структура, как возвращает db.database.get_university_by_id.
    """
    if not uni:
        return "неизвестный университет"

    name = uni.get("name", "—")
    city = uni.get("city") or "город не указан"
    utype = uni.get("type") or "тип не указан"
    rating = uni.get("rating")
    tuition = uni.get("tuition_fee")
    programs = uni.get("programs") or []
    languages = uni.get("languages") or []
    intl = uni.get("international_score")
    employ = uni.get("employment_rate")
    reviews = uni.get("reviews") or []

    lines = [
        f"Название: {name}",
        f"Город: {city}",
        f"Тип: {utype}",
    ]

    if rating is not None:
        lines.append(f"Рейтинг (внутри платформы): {rating:.1f} из 10")

    if tuition is not None:
        lines.append(f"Примерная стоимость обучения в год: {tuition} KZT")

    if programs:
        lines.append("Основные программы: " + ", ".join(programs))

    if languages:
        lines.append("Языки обучения: " + ", ".join(languages))

    if intl is not None:
        lines.append(f"Международность (обмены, иностранные студенты): {intl:.1f} из 10")

    if employ is not None:
        # приводим к процентам, если это 0–1
        employ_percent = employ * 100 if 0 < employ <= 1 else employ
        lines.append(f"Трудоустройство выпускников: ~{employ_percent:.0f}%")

    if reviews:
        # ограничим 3 отзывами, чтобы промпт не раздувать
        trimmed = reviews[:3]
        lines.append("Отзывы студентов (выборочно):")
        for r in trimmed:
            lines.append(f"- {r}")

    return "\n".join(lines)


def compare_universities(uni1: Dict[str, Any],
                         uni2: Dict[str, Any],
                         goal: str | None = None) -> str:
    """
    Основная функция: принимает 2 словаря с данными университетов и
    опциональную цель абитуриента (goal), возвращает текстовый вывод ИИ на русском.

    Никакой бизнес-логики Flask здесь нет — только работа с моделью.
    """

    if not uni1 or not uni2:
        raise ValueError("Оба университета должны быть переданы в compare_universities")

    uni1_block = _format_university_for_prompt(uni1)
    uni2_block = _format_university_for_prompt(uni2)

    goal_text = goal.strip() if isinstance(goal, str) and goal.strip() else None

    user_instruction = f"""
Ты — эксперт по высшему образованию в Казахстане.
Тебе даны данные о двух университетах. 
Нужно коротко и понятно для абитуриента сравнить их и дать рекомендацию.

Если указана цель абитуриента — учитывай её в выводе.

Формат ответа:
1) Краткое сравнение по ключевым параметрам (стоимость, качество программ, отзывы, международность, трудоустройство).
2) Плюсы и минусы каждого вуза отдельными списками.
3) Для кого лучше подойдёт Университет A, для кого Университет B.
4) Итоговая рекомендация в 1–2 предложениях.

Пиши по-русски, без воды, понятным языком.
Избегай прямых оценок "плохой/ужасный", используй мягкие формулировки.
"""

    if goal_text:
        user_instruction += f"\nЦель абитуриента: {goal_text}\n"

    user_instruction += "\n\n=== Университет A ===\n"
    user_instruction += uni1_block
    user_instruction += "\n\n=== Университет B ===\n"
    user_instruction += uni2_block

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": (
                    "Ты профессиональный консультант по выбору университета в Казахстане. "
                    "Отвечай структурированно, с заголовками и маркированными списками."
                ),
            },
            {"role": "user", "content": user_instruction},
        ],
        temperature=0.3,
        max_tokens=900,
    )

    content = response.choices[0].message.content.strip()
    return content