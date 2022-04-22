from flask import Blueprint, render_template, request, url_for, session, g, flash
from werkzeug.utils import redirect
from werkzeug.security import generate_password_hash, check_password_hash


from .. import db
from FileServer.models import User
from FileServer.forms import LoginForm


bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.route("/")
def index():
    return redirect("login")


@bp.route("/login/", methods = ("GET", "POST"))
def login():
    form = LoginForm()
    if request.method == "POST" and form.validate_on_submit():
        error = None
        user = User().query.filter_by(username = form.username.data).first()
        if not user:
            error = "유저가 없음"
        elif not check_password_hash(user.password, form.password.data):
            error = "비밀번호가 틀림"
        
        if error is None:
            session.clear()
            session["user_id"] = user.id
            return redirect(url_for("main.index"))

        flash(error)
    return render_template("auth/login.html", form = form)


@bp.route("/logout/")
def logout():
    session.clear()
    return redirect("login")


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get("user_id")
    if user_id is None:
        g.user = None
    else:
        g.user = User.query.get(user_id)