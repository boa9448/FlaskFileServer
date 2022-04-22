from flask import Blueprint, url_for, g, session
from werkzeug.utils import redirect

bp = Blueprint("main", __name__, url_prefix = "/")

@bp.route("/")
def index():
    if not g.user:
        return redirect(url_for("auth.login"))

    return "파일 리스트"