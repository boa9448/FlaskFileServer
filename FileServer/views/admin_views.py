import os
import hashlib
from glob import glob


from flask import Blueprint, redirect, render_template, flash, url_for, current_app


from .. import db
from ..models import User, File
from .auth_views import login_required, admin_permission_required

bp = Blueprint("admin", __name__, url_prefix = "/admin")


@bp.route("/member/")
@login_required
@admin_permission_required
def user_manage():
    user_list = User.query.all()
    user_permission_list = ["권한 없음", "관리자", "허가된 사용자"]
    return render_template("admin/user_manage.html", user_list = user_list, permission = user_permission_list)


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

    return redirect(url_for(".user_manage"))


@bp.route("enable/<int:user_id>/")
@login_required
@admin_permission_required
def enable(user_id):
    user = User.query.get(user_id)
    if not user:
        flash("잘못된 유저 아이디입니다")
    else:
        user.permission = 1
        db.session.add(user)
        db.session.commit()

    return redirect(url_for(".user_manage"))


@bp.route("disable/<int:user_id>/")
@login_required
@admin_permission_required
def disable(user_id):
    user = User.query.get(user_id)
    if not user:
        flash("잘못된 유저 아이디입니다")
    else:
        user.permission = 0
        db.session.add(user)
        db.session.commit()

    return redirect(url_for(".user_manage"))



@bp.route("/file/")
@login_required
@admin_permission_required
def file_manage():
    file_list = File.query.all()

    return render_template("admin/file_manage.html", file_list = file_list)


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
def file_refresh():
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

    return redirect(url_for(".file_manage"))


@bp.route("/fileenable/<int:file_id>")
@login_required
@admin_permission_required
def file_enable(file_id):
    file = File.query.get(file_id)
    file.permission = 0
    db.session.add(file)
    db.session.commit()

    return redirect(url_for(".file_manage"))


@bp.route("/filedisable/<int:file_id>")
@login_required
@admin_permission_required
def file_disable(file_id):
    file = File.query.get(file_id)
    file.permission = 999
    db.session.add(file)
    db.session.commit()

    return redirect(url_for(".file_manage"))