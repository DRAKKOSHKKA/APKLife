"""Routes for schedule page and background refresh endpoints."""

from pathlib import Path

from flask import Blueprint, jsonify, render_template, request

from services.metrics import snapshot
from services.schedule import force_refresh_context, load_schedule_context

bp_group = Blueprint("group", __name__)
LOG_PATH = Path("logs/app.log")


@bp_group.route("/")
def group_page():
    """Render group schedule page."""
    context = load_schedule_context(request.args)
    return render_template("group.html", **context)


@bp_group.route("/refresh", methods=["GET"])
def refresh_page():
    """Force refresh schedule from network and return rendered fragment for UI update."""
    context = force_refresh_context(request.args)
    html = render_template("partials/schedule_content.html", **context)
    return jsonify(
        {
            "ok": bool(context.get("schedule")),
            "html": html,
            "message": context.get("schedule_message"),
            "source": context.get("schedule_source"),
            "cache_updated_at": context.get("cache_updated_at"),
            "error": context.get("error"),
            "offline": context.get("offline"),
            "cache_state": context.get("cache_state"),
            "metrics": context.get("metrics"),
        }
    )


@bp_group.route("/metrics", methods=["GET"])
def metrics_page():
    """Return current in-memory metrics for DEV mode."""
    return jsonify(snapshot())


@bp_group.route("/logs", methods=["GET"])
def logs_page():
    """Return tail of application logs for DEV mode."""
    if not LOG_PATH.exists():
        return jsonify({"lines": []})

    lines = LOG_PATH.read_text(encoding="utf-8", errors="ignore").splitlines()[-200:]
    return jsonify({"lines": lines})
