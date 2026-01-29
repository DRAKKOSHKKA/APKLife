from flask import Blueprint, render_template, request
from services.utils_schedule import get_current_week, get_current_day_name

bp_info = Blueprint("info", __name__)

@bp_info.route("/")
def info():
    return render_template("info.html")
