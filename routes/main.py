"""Main landing page routes."""

from flask import Blueprint, render_template

from services.utils_schedule import get_current_day_name, get_current_week

bp_main = Blueprint("main", __name__)


@bp_main.route("/")
def index():
    """Render search page with default week/day values."""
    return render_template(
        "index.html",
        current_week=get_current_week(),
        current_day_name=get_current_day_name(),
    )
