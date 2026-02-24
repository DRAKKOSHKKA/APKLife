import traceback

from flask import Flask, render_template
from werkzeug.exceptions import HTTPException

from routes.group import bp_group
from routes.main import bp_main
from services.version import get_version_status


def create_app():
    app = Flask(__name__)

    app.register_blueprint(bp_main)
    app.register_blueprint(bp_group, url_prefix="/group")

    @app.context_processor
    def inject_version_status():
        return {"version_status": get_version_status()}

    @app.errorhandler(Exception)
    def handle_exception(error):
        traceback.print_exc()
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
    app.run(host="0.0.0.0", debug=True)
