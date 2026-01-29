from flask import Blueprint, render_template

bp_main = Blueprint("main", __name__)

@bp_main.route("/")
def index():
    return render_template("index.html")
