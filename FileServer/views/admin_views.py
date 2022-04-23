from flask import Blueprint, render_template

from ..models import User
from .auth_views import login_required, admin_permission_required

bp = Blueprint("admin", __name__, url_prefix = "/admin")


@bp.route("/member")
@login_required
@admin_permission_required
def member():
    user_list = User.query.all()
    user_permission_list = ["권한 없음", "관리자", "허가된 사용자"]
    return render_template("admin/member.html", user_list = user_list, permission = user_permission_list)