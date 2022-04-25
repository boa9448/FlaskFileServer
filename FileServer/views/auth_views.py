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
            log("계정 삭제 성공", user)
            username = user.username
            db.session.delete(user)
            db.session.commit()
            flash(f"{username} 삭제 성공!")

    return redirect(url_for(".manage"))


@bp.route("/permission/<int:user_id>/<int:permission>/")
@login_required
@admin_permission_required
def _permission(user_id, permission):
    user = User.query.get(user_id)
    if not user:
        flash("잘못된 유저 아이디입니다")
    else:
        log("권한 변경", user)
        user.permission = permission
        db.session.add(user)
        db.session.commit()

    return redirect(url_for(".manage"))


def toggle_file_access_permission(user_id, file_id):
    user = User.query.get(user_id)
    if not user:
        flash("잘못된 유저 아이디")
        return

    file_acc_per = FileAccessPermission.query.filter(and_(FileAccessPermission.user_id == user_id
                                                        , FileAccessPermission.file_id == file_id)).first()
    if file_acc_per:
        try:
            db.session.delete(file_acc_per)
            db.session.commit()
        except:
            db.session.rollback()
            flash("권한 설정에 실패했습니다")

        return

    try:
        file_acc_per = FileAccessPermission(user_id = user_id
                                            , file_id = file_id
                                            , create_date = datetime.now())

        db.session.add(file_acc_per)
        db.session.commit()
    except:
        flash("권한 설정에 실패했습니다")
        db.session.rollback()


@bp.route("/file/permission/<int:user_id>/")
@bp.route("/file/permission/<int:user_id>/<int:file_id>/")
@login_required
@admin_permission_required
def file_permission(user_id, file_id = None):
    file_list = File.query.all()
    
    #WDW : 최적화 필요
    file_info_list = list()
    for idx, file in enumerate(file_list, 1):
        result = FileAccessPermission.query.filter_by(user_id = user_id, file_id = idx).first()
        file_info_list.append((file, True if result else False))

    if file_id:
        toggle_file_access_permission(user_id, file_id)
        return redirect(url_for(".file_permission", user_id = user_id))

    return render_template("auth/user_file_manage.html", user_id = user_id, file_list = file_info_list)