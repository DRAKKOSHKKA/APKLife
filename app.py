from flask import Flask, render_template, request
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
        # Логирование ошибки в консоль
        traceback.print_exc()

        # Если это HTTP ошибка, используем её код и описание
        if isinstance(e, HTTPException):
            return render_template(
                "errors/error.html",
                code=e.code,
                name=e.name,
                description=e.description
            ), e.code

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", debug=True)
