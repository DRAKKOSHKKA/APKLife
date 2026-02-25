"""Main landing page and diagnostics routes."""

from __future__ import annotations

from flask import Blueprint, jsonify, render_template

from services.cache_store import cache_size
from services.config import settings
from services.runtime_state import snapshot_state
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


@bp_main.route("/health")
def health():
    """Return health diagnostic payload."""
    state = snapshot_state()
    return jsonify(
        {
            "application_version": settings.app_version,
            "last_successful_update": state.get("last_successful_update"),
            "last_error_message": state.get("last_error"),
            "cache_size": cache_size(),
            "uptime_started_at": state.get("started_at"),
        }
    )
