from flask import Blueprint, render_template, url_for, g, session
from werkzeug.utils import redirect

bp = Blueprint("main", __name__, url_prefix = "/")

@bp.route("/")
def index():
    if not g.user:
        return redirect(url_for("auth.login"))

    return redirect(url_for("file.list"))