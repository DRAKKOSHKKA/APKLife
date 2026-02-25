"""Flask application entrypoint with global context and error handlers."""

from __future__ import annotations

from flask import Flask, render_template
from werkzeug.exceptions import HTTPException

from routes.group import bp_group
from routes.main import bp_main
from services.config import settings
from services.logger import setup_logger
from services.metrics import snapshot
from services.version import get_version_status

logger = setup_logger(__name__)


def create_app() -> Flask:
    """Build Flask app instance and register routes/middleware."""
    app = Flask(__name__)

    app.register_blueprint(bp_main)
    app.register_blueprint(bp_group, url_prefix="/group")

    @app.context_processor
    def inject_version_status():
        """Inject global status into all templates."""
        return {
            "version_status": get_version_status(),
            "offline": False,
            "cache_state": "unknown",
            "metrics": snapshot(),
        }

    @app.errorhandler(Exception)
    def handle_exception(error):
        """Render user-friendly error pages for both HTTP and unexpected errors."""
        logger.exception("Unhandled exception: %s", error)

        if isinstance(error, HTTPException):
            return (
                render_template(
                    "errors/error.html",
                    code=error.code,
                    name=error.name,
                    description=error.description,
                ),
                error.code,
            )

        return (
            render_template(
                "errors/error.html",
                code=500,
                name="Internal Server Error",
                description="Произошла непредвиденная ошибка.",
            ),
            500,
        )

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host=settings.host, port=settings.port, debug=settings.debug)
