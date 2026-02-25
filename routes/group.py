from flask import Blueprint, render_template, request
from services.schedule import load_schedule_context
from services.versioning import get_version_status

bp_group = Blueprint("group", __name__)

@bp_group.route("/")
def group_page():
    context = load_schedule_context(request.args)
    context["version_status"] = get_version_status()
    return render_template("group.html", **context)
