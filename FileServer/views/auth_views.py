import functools
from datetime import datetime
from operator import or_


from flask import Blueprint, render_template, request, url_for, session, g, flash
from werkzeug.utils import redirect
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import or_

from FileServer import db
from FileServer.models import User
from FileServer.forms import LoginForm, SignupForm


bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.route("/")
def index():
    return redirect(url_for('.login'))


@bp.route("/login/", methods = ("GET", "POST"))
def login():
    form = LoginForm()
    if request.method == "POST" and form.validate_on_submit():
        error = None
        user = User().query.filter_by(username = form.username.data).first()
        if not user:
            error = "등록된 유저가 없습니다"
        elif not check_password_hash(user.password, form.password.data):
            error = "비밀번호가 일치하지 않습니다"
        
        if error is None:
            session.clear()
            session["user_id"] = user.id
            _next = request.args.get("next", "")
            if _next:
                return redirect(_next)

            return redirect(url_for("main.index"))

        flash(error)
    return render_template("auth/login.html", form = form)


@bp.route("/logout/")
def logout():
    session.clear()
    return redirect(url_for("main.index"))


@bp.route("/signup/", methods = ("GET", "POST"))
def signup():
    form = SignupForm()
    if request.method == "POST" and form.validate_on_submit():
        user = User().query.filter(or_(User.username == form.username.data, User.email == form.email.data)).first()
        if not user:
            user = User(username = form.username.data
                        , password = generate_password_hash(form.password1.data)
                        , email = form.email.data
                        , admin_permission = 0
                        , permission = 0
                        , create_date = datetime.now())
            db.session.add(user)
            db.session.commit()
            return redirect(url_for('.login'))
        
        flash("이미 존재하는 유저입니다")
    return render_template("auth/signup.html", form = form)


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get("user_id")
    if user_id is None:
        g.user = None
    else:
        g.user = User.query.get(user_id)


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(*args, **kwargs):
        if g.user is None:
            _next = request.url if request.method == "GET" else ""
            return redirect(url_for("auth.login", next = _next))

        return view(*args, **kwargs)

    return wrapped_view


def admin_permission_required(view):
    @functools.wraps(view)
    def wrapped_view(*args, **kwargs):
        if not g.user.admin_permission:
            flash("권한이 부족합니다")
            return redirect(url_for("main.index"))

        return view(*args, **kwargs)

    return wrapped_view


@bp.route("/manage/")
@login_required
@admin_permission_required
def manage():
    user_list = User.query.all()
    user_permission_list = ["권한 없음", "관리자", "허가된 사용자"]
    return render_template("auth/user_manage.html", user_list = user_list, permission = user_permission_list)


@bp.route("/delete/<int:user_id>/")
@login_required
@admin_permission_required
def delete(user_id):
    user = User.query.get(user_id)
    if not user:
        flash("잘못된 유저 아이디 입니다")
    else:
        if user.admin_permission:
            flash("관리자 계정은 삭제할 수 없습니다")
        else:
            username = user.username
            db.session.delete(user)
            db.session.commit()
            flash(f"{username} 삭제 성공!")

    return redirect(url_for(".manage"))


@bp.route("permission/<int:user_id>/<int:permission>/")
@login_required
@admin_permission_required
def _permission(user_id, permission):
    user = User.query.get(user_id)
    if not user:
        flash("잘못된 유저 아이디입니다")
    else:
        user.permission = permission
        db.session.add(user)
        db.session.commit()

    return redirect(url_for(".manage"))