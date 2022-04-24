import os
import hashlib
import functools
from glob import glob
from datetime import datetime


from flask import Blueprint, flash, redirect, render_template, send_file, g, current_app, url_for


from .auth_views import login_required, admin_permission_required
from ..models import File, FileAccessLog
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
        file_list = File.query.filter(File.permission < g.user.permission)

    return render_template("file/file_list.html", file_list = file_list)


@bp.route("/down/<int:file_id>/")
@login_required
def down(file_id):
    user = g.user
    file = File.query.get(file_id)
    log(file)
    if not user.permission <= file.permission:
        return render_template("404.html")

    file_dir = current_app.config["SHARE_FILE_DIR"]
    file_path = os.path.join(file_dir, file.filename)
    
    if not os.path.isfile(file_path):
        return render_template("404.html")

    return send_file(file_path)


@bp.route("/manage/")
@login_required
@admin_permission_required
def manage():
    file_list = File.query.all()

    return render_template("file/file_manage.html", file_list = file_list)


#https://stackoverflow.com/questions/16874598/how-do-i-calculate-the-md5-checksum-of-a-file-in-python
def md5_file_hash(file_name):
    with open(file_name, "rb") as f:
        file_hash = hashlib.md5()
        while chunk := f.read(8192):
            file_hash.update(chunk)

    return file_hash.hexdigest()


@bp.route("/refresh/")
@login_required
@admin_permission_required
def refresh():
    file_dir = current_app.config["SHARE_FILE_DIR"]
    glob_pattern = os.path.join(file_dir, "*.*")
    disk_file_list = glob(glob_pattern)
    disk_file_hash_list = list()

    for disk_file in disk_file_list:
        file_hash = md5_file_hash(disk_file)
        disk_file_hash_list.append(file_hash)

    #모두 삭제 후 
    try:
        File.query.delete()
        db.session.commit()
    except:
        db.session.rollback()

    #새로 등록
    try:
        for disk_file, file_hash in zip(disk_file_list, disk_file_hash_list):
            file = File(filename = os.path.split(disk_file)[-1]
                        , permission = 999
                        , hash = file_hash
                        , size = os.path.getsize(disk_file))
            
            db.session.add(file)

        db.session.commit()
    except:
        db.session.rollback()

    return redirect(url_for(".manage"))


@bp.route("/permission/<int:file_id>/<int:permission>/")
def _permission(file_id, permission):
    file = File.query.get(file_id)
    if not file:
        flash("잘못된 파일 아이디")
    else:
        file.permission = permission
        db.session.add(file)
        db.session.commit()

    return redirect(url_for("file.manage"))