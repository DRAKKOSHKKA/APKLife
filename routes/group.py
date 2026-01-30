from flask import Blueprint, render_template, request
from services.schedule import load_schedule_context

bp_group = Blueprint("group", __name__)

@bp_group.route("/")
def group_page():
    context = load_schedule_context(request.args)
    return render_template("group.html", **context)
