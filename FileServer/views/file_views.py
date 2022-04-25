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


@bp.route("/delete/<int:file_id>/")
@login_required
@admin_permission_required
def delete(file_id):
    file = File.query.get(file_id)
    if not file:
        flash("잘못된 파일 아이디")
        return redirect(url_for(".manage"))

    file_dir = current_app.config["SHARE_FILE_DIR"]
    file_path = os.path.join(file_dir, file.filename)
    file_path = os.path.abspath(file_path)
    
    try:
        if not os.path.isfile(file_path):
            flash("존재하지 않는 파일입니다")
        else:
            os.remove(file_path)

        db.session.delete(file)
        db.session.commit()
    except Exception as e:
        flash("파일 삭제에 실패했습니다")
        db.session.rollback()

    return redirect(url_for(".manage"))


@bp.route("/upload/", methods = ["GET", "POST"])
@login_required
@admin_permission_required
def upload():
    if request.method == "POST":
        if "form-file" not in  request.files:
            flash("잘못된 파일입니다")
            return redirect(url_for(".manage"))

        file = request.files["form-file"]
        if file.filename == "":
            flash("파일이 선택되지 않았습니다")
            return redirect(url_for(".manage"))

        if file:
            filename = secure_filename(file.filename)

            file_dir = current_app.config["SHARE_FILE_DIR"]
            file_path = os.path.join(file_dir, filename)
            file_path = os.path.abspath(file_path)

            file.save(file_path)

            file_hash = md5_file_hash(file_path)
            file = File(filename = file.filename
                        , hash = file_hash
                        , size = os.path.getsize(file_path)
                        , permission = 999)

            db.session.add(file)
            db.session.commit()
            return redirect(url_for(".manage"))

    flash("잘못된 요청")
    return redirect(url_for(".manage"))
