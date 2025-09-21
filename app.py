from flask import Flask, render_template, request, redirect, make_response, jsonify
import os
import json
import datetime

from utils_schedule import get_group_info, get_schedule
from routes_group import bp_group

app = Flask(__name__)
app.register_blueprint(bp_group)


import datetime
from flask import Flask, request, render_template

app = Flask(__name__)

def strip_trailing_commas(obj):
    """Рекурсивно убирает запятые в конце всех строк в объекте."""
    if isinstance(obj, str):
        return obj.rstrip(',')
    elif isinstance(obj, list):
        return [strip_trailing_commas(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: strip_trailing_commas(value) for key, value in obj.items()}
    else:
        return obj

@app.route("/")
def index():
    search_string = request.args.get('group_name', type=str)
    week_id = request.args.get('week_id', type=int)
    day_param = request.args.get('day', type=str)

    context = {
        "group_info": None,
        "schedule": {},
        "days_list": [],
        "prev_week_id": None,
        "next_week_id": None,
        "active_day": None,
        "week_id": week_id,
        "error": None,
        "corrected_name": None,
        "no_lessons_week": True
    }

    if search_string:
        entity_info, corrected_name = get_group_info(search_string)

        # Очистка запятых в названии группы и исправленном имени
        entity_info = strip_trailing_commas(entity_info)
        corrected_name = strip_trailing_commas(corrected_name)

        if not entity_info:
            context["error"] = f"'{search_string}' не найдено. Проверьте название."
            return render_template("index.html", **context)

        schedule, days_list, prev_week_id, next_week_id = get_schedule(week_id or 14436, entity_info)

        # Рекурсивная очистка всех строк в расписании и днях
        schedule = strip_trailing_commas(schedule)
        days_list = strip_trailing_commas(days_list)

        # Определяем активный день
        active_day = None
        if day_param:
            for full_day_string in schedule.keys():
                if full_day_string.startswith(day_param) or day_param in full_day_string:
                    active_day = full_day_string
                    break
        elif schedule:
            weekday = datetime.datetime.now().weekday()
            ru_days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
            today_short = ru_days[weekday]
            for full_day_string in schedule.keys():
                if full_day_string.startswith(today_short):
                    active_day = full_day_string
                    break
            if not active_day:
                active_day = list(schedule.keys())[0]

        # Если выбран день → оставляем только его
        filtered_schedule = schedule
        if active_day:
            filtered_schedule = {active_day: schedule[active_day]}

        context.update({
            "group_info": entity_info,
            "schedule": filtered_schedule,
            "days_list": days_list,
            "prev_week_id": prev_week_id,
            "next_week_id": next_week_id,
            "week_id": week_id,
            "corrected_name": corrected_name,
            "no_lessons_week": not bool(schedule),
            "active_day": active_day
        })

    return render_template("index.html", **context)



@app.route("/suggestions.json")
def get_suggestions():
    suggestions_path = os.path.join(app.root_path, 'suggestions.json')
    try:
        with open(suggestions_path, 'r', encoding='utf-8') as f:
            return jsonify(json.load(f))
    except FileNotFoundError:
        return jsonify({"error": "Suggestions file not found"}), 404
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON in suggestions file"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
