from flask import Blueprint, redirect, render_template, flash, url_for

from .. import db
from ..models import User
from .auth_views import login_required, admin_permission_required

bp = Blueprint("admin", __name__, url_prefix = "/admin")


@bp.route("/member/")
@login_required
@admin_permission_required
def member():
    user_list = User.query.all()
    user_permission_list = ["권한 없음", "관리자", "허가된 사용자"]
    return render_template("admin/member.html", user_list = user_list, permission = user_permission_list)


@bp.route("/delete/<int:user_id>/")
@login_required
@admin_permission_required
def delete(user_id):
    user = User.query.filter_by(id=user_id).first()
    if not user:
        flash("잘못된 유저 아이디 입니다")
    else:
        if user.permission == 1:
            flash("관리자 계정은 삭제할 수 없습니다")
        else:
            username = user.username
            db.session.delete(user)
            db.session.commit()
            flash(f"{username} 삭제 성공!")

    return redirect(url_for(".member"))


@bp.route("enable/<int:user_id>/")
@login_required
@admin_permission_required
def enable(user_id):
    user = User.query.filter_by(id = user_id).first()
    if not user:
        flash("잘못된 유저 아이디입니다")
    else:
        user.permission = 2
        db.session.add(user)
        db.session.commit()

    return redirect(url_for(".member"))


@bp.route("disable/<int:user_id>/")
@login_required
@admin_permission_required
def disable(user_id):
    user = User.query.filter_by(id = user_id).first()
    if not user:
        flash("잘못된 유저 아이디입니다")
    else:
        user.permission = 0
        db.session.add(user)
        db.session.commit()

    return redirect(url_for(".member"))