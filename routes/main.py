from flask import Blueprint, render_template
from services.utils_schedule import get_current_week, get_current_day_name
from services.versioning import get_version_status

bp_main = Blueprint("main", __name__)

@bp_main.route("/")
def index():
    return render_template(
        "index.html",
        current_week=get_current_week(),
        current_day_name=get_current_day_name(),
        version_status=get_version_status(),
    )
