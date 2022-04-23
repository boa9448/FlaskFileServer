from flask import Blueprint

bp = Blueprint("admin", __name__, url_prefix = "/admin")


@bp.route("/member")
def member():
    return "회원 관리 페이지"