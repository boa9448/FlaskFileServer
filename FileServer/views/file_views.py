import os
import hashlib
import functools
from glob import glob
from datetime import datetime


from flask import Blueprint, flash, redirect, render_template, request, send_file, g, current_app, url_for
from werkzeug.utils import secure_filename
from sqlalchemy import or_, and_


from .auth_views import login_required, admin_permission_required
from ..models import File, FileAccessLog, FileAccessPermission
from .. import db


bp = Blueprint("file", __name__, url_prefix = "/file")


def log(file):
    try:
        user = g.user
        file_log = FileAccessLog(user_id = user.id
                        , file_id = file.id
                        , file_name = file.filename
                        , create_date = datetime.now())

        db.session.add(file_log)
        db.session.commit()
    except:
        db.rollback()

def file_log(message, file):
    def Inner(view):
        @functools.wraps(view)
        def wrapper(*args, **kwargs):
            log(message, file)
            return view(*args, **kwargs)
        return wrapper
    return Inner


@bp.route("/list/")
@login_required
def _list():
    if g.user.admin_permission:
        file_list = File.query.all()
    else:
        file_list = File.query.join(FileAccessPermission)\
                        .filter(and_(FileAccessPermission.user_id == g.user.id, File.permission < g.user.permission)).all()

    return render_template("file/file_list.html", file_list = file_list)


@bp.route("/down/<int:file_id>/")
@login_required
def down(file_id):
    user = g.user
    user_access_filter = and_(FileAccessPermission.user_id == user.id
                        , FileAccessPermission.id == file_id)
    access_filter = and_(user_access_filter , user.permission > File.permission)
    
    file = File.query.join(FileAccessPermission)\
                .filter(access_filter).first()

    if not file:
        return render_template("404.html")
    
    log(file)
    if user.permission <= file.permission and not user.admin_permission:
        return render_template("404.html")

    file_dir = current_app.config["SHARE_FILE_DIR"]
    file_path = os.path.join(file_dir, file.filename)
    
    if not os.path.isfile(file_path):
        return render_template("404.html")

    return send_file(file_path)