from flask import Flask, render_template
from routes.group import bp_group
from routes.main import bp_main
from werkzeug.exceptions import HTTPException
import traceback


def create_app():
    app = Flask(__name__)

    # Роуты
    app.register_blueprint(bp_main)
    app.register_blueprint(bp_group, url_prefix="/group")

    # Глобальный перехват ошибок
    @app.errorhandler(Exception)
    def handle_exception(e):

        # HTTP ошибки (404, 403 и т.д.)
        if isinstance(e, HTTPException):
            return render_template(
                "errors/error.html",
                code=e.code,
                name=e.name,
                description=e.description
            ), e.code

        # Python ошибки (TypeError, ValueError, etc)
        traceback.print_exc()

        return render_template(
            "errors/error.html",
            code=500,
            name=type(e).__name__,
            description="Внутренняя ошибка сервера"
        ), 500

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", debug=True)
