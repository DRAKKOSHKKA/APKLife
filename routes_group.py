from flask import Blueprint, render_template, request
from utils_schedule import get_group_info, get_schedule

bp_group = Blueprint('group', __name__)

@bp_group.route('/group', methods=['GET'])
def group_schedule():
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
        "first_lesson_indices": {},
        "no_lessons_week": True,
        "week_id": week_id,
        "error": None,
        "corrected_name": None
    }
    if not search_string:
        context["error"] = "Не указано название группы"
        return render_template('index.html', **context)
    entity_info, corrected_name = get_group_info(search_string)
    if not entity_info:
        context["error"] = f"'{search_string}' не найдено. Проверьте название."
        return render_template('index.html', **context)
    schedule, days_list, prev_week_id, next_week_id = get_schedule(week_id, entity_info)
    context.update({
        "group_info": entity_info,
        "schedule": schedule or {},
        "days_list": days_list or [],
        "prev_week_id": prev_week_id,
        "next_week_id": next_week_id,
        "week_id": week_id,
        "no_lessons_week": not bool(schedule),
        "corrected_name": corrected_name
    })
    # Определяем активный день
    active_day = None
    if day_param:
        for full_day_string in context["schedule"].keys():
            if full_day_string.startswith(day_param):
                active_day = full_day_string
                break
    elif context["days_list"]:
        import datetime
        weekday = datetime.datetime.now().weekday()
        ru_days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
        today_short = ru_days[weekday]
        for full_day_string in context["schedule"].keys():
            if full_day_string.startswith(today_short):
                active_day = full_day_string
                break
        if not active_day:
            active_day = list(context["schedule"].keys())[0]
    context["active_day"] = active_day
    return render_template('index.html', **context)