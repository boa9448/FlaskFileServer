import os
import functools
from pathlib import Path
from glob import glob
from datetime import datetime


from flask import Blueprint, flash, redirect, render_template, request, send_file, g, current_app, url_for
from werkzeug.utils import secure_filename
from sqlalchemy import or_, and_


from .auth_views import login_required, admin_permission_required
from ..models import File, FileAccessLog, FileAccessPermission
from .. import db


bp = Blueprint("file", __name__, url_prefix = "/file")


def log(file_id):
    try:
        user = g.user
        file = File.query.get(file_id)
        file_log = FileAccessLog(user_id = user.id
                        , file_id = file.id
                        , file_name = file.filename
                        , create_date = datetime.now())

        db.session.add(file_log)
        db.session.commit()
    except:
        db.session.rollback()


def file_log(view):
    @functools.wraps(view)
    def wrapper(*args, **kwargs):
        log(kwargs["file_id"])
        return view(*args, **kwargs)
    return wrapper


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
@file_log
def down(file_id):
    user = g.user

    if not user.admin_permission:
        user_access_filter = and_(FileAccessPermission.user_id == user.id
                            , FileAccessPermission.file_id == file_id)
        access_filter = and_(user_access_filter , user.permission > File.permission)
        
        file = File.query.join(FileAccessPermission)\
                    .filter(access_filter).first()

        if not file:
            return render_template("404.html")
    else:
        file = File.query.get_or_404(file_id)

    file_dir = current_app.config["SHARE_FILE_DIR"]
    file_path = os.path.join(file_dir, file.filename)
    
    if not os.path.exists(file_path):
        return render_template("404.html")

    print(999)
    return send_file(file_path)