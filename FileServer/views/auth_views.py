import functools
from datetime import datetime
from operator import or_, and_


from flask import Blueprint, render_template, request, url_for, session, g, flash
from werkzeug.utils import redirect
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import or_

from FileServer import db
from FileServer.models import FileAccessPermission, User, UserLog, File
from FileServer.forms import LoginForm, SignupForm


bp = Blueprint("auth", __name__, url_prefix="/auth")


def log(message, user):
    try:
        user_log = UserLog(user_id = user.id, level = 20, type = 0
                , message = f"user id : {user.id}, username : {user.username} {message}"
                , create_date = datetime.now())
        db.session.add(user_log)
        db.session.commit()
    except:
        db.rollback()

def auth_log(message, user = None):
    def Inner(view):
        @functools.wraps(view)
        def wrapper(*args, **kwargs):
            user_ = user if user else g.user
            log(message, user_)
            return view(*args, **kwargs)
        return wrapper
    return Inner


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
            log("로그인 성공", user)
            if _next:
                return redirect(_next)

            return redirect(url_for("main.index"))

        flash(error)
    return render_template("auth/login.html", form = form)


@bp.route("/logout/")
@auth_log("로그아웃 성공")
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

            log("회원 가입", user)
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
            user = g.user
            log("잘못된 접근(관리자 페이지 접근 시도)", user)
            return redirect(url_for("main.index"))

        return view(*args, **kwargs)

    return wrapped_view