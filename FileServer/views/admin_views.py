import os
import hashlib
from glob import glob
from datetime import datetime


from flask import url_for, redirect, flash, g, render_template, Blueprint, current_app, request
from sqlalchemy import and_


from .. import db
from ..models import User, File, FileAccessPermission
from .auth_views import login_required, admin_permission_required, log


bp = Blueprint("admin", __name__, url_prefix = "/admin")


@bp.route("/user/list/")
@login_required
@admin_permission_required
def user_list():
    user_list = User.query.all()
    return render_template("admin/admin_user_manage.html", user_list = user_list)


@bp.route("/user/delete/<int:user_id>/")
@login_required
@admin_permission_required
def user_delete(user_id):
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

    return redirect(url_for(".user_list"))


@bp.route("/user/permission/<int:user_id>/<int:permission>/")
@login_required
@admin_permission_required
def user_permission(user_id, permission):
    user = User.query.get_or_404(user_id)
    if not user:
        flash("잘못된 유저 아이디입니다")
    else:
        log("권한 변경", user)
        user.permission = permission
        db.session.add(user)
        db.session.commit()

    return redirect(url_for(".user_list"))


@bp.route("/user/permission/close")
@login_required
@admin_permission_required
def user_permission_close():
    try:
        User.query.update({User.permission : 0})
        db.session.commit()
    except RuntimeError:
        flash("모든 권한 변경 실패")
        db.session.rollback()

    return redirect(url_for(".user_list"))

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


@bp.route("/user/file/permission/<int:user_id>/")
@login_required
@admin_permission_required
def user_file_permission(user_id):
    file_id = request.args.get("file_id", None)
    
    if file_id:
        toggle_file_access_permission(user_id, file_id)
        return redirect(url_for(".user_file_permission", user_id = user_id))

    q = File.query.outerjoin(FileAccessPermission, and_(File.id == FileAccessPermission.file_id
                            , FileAccessPermission.user_id == user_id))\
                .add_columns(File.id, File.filename, File.size, FileAccessPermission.user_id)
    
    file_info_list = q.all()

    return render_template("admin/admin_user_file_permission.html", user_id = user_id, file_list = file_info_list)


@bp.route("/file/list/")
@login_required
@admin_permission_required
def file_list():
    file_list = File.query.all()
    return render_template("admin/admin_file_manage.html", file_list = file_list)


#https://stackoverflow.com/questions/16874598/how-do-i-calculate-the-md5-checksum-of-a-file-in-python
def md5_file_hash(file_name):
    with open(file_name, "rb") as f:
        file_hash = hashlib.md5()
        while chunk := f.read(8192):
            file_hash.update(chunk)

    return file_hash.hexdigest()


@bp.route("/file/refresh/")
@login_required
@admin_permission_required
def list_refresh():
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

    return redirect(url_for(".file_list"))


@bp.route("/permission/<int:file_id>/<int:permission>/")
def file_permission(file_id, permission):
    file = File.query.get(file_id)
    if not file:
        flash("잘못된 파일 아이디")
    else:
        file.permission = permission
        db.session.add(file)
        db.session.commit()

    return redirect(url_for(".file_list"))


@bp.route("/file/delete/<int:file_id>/")
@login_required
@admin_permission_required
def file_delete(file_id):
    file = File.query.get(file_id)
    if not file:
        flash("잘못된 파일 아이디")
        return redirect(url_for(".file_list"))

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

    return redirect(url_for(".file_list"))


@bp.route("/file/upload/", methods = ["GET", "POST"])
@login_required
@admin_permission_required
def file_upload():
    if request.method == "POST":
        if "form-file" not in  request.files:
            flash("잘못된 파일입니다")
            return redirect(url_for(".file_list"))

        file = request.files["form-file"]
        if file.filename == "":
            flash("파일이 선택되지 않았습니다")
            return redirect(url_for(".file_list"))

        if file:
            file_dir = current_app.config["SHARE_FILE_DIR"]
            filename = os.path.split(file.filename)[-1]

            file_path = os.path.join(file_dir, filename)
            file_path = os.path.abspath(file_path)

            file.save(file_path)

            file_hash = md5_file_hash(file_path)
            file = File(filename = filename
                        , hash = file_hash
                        , size = os.path.getsize(file_path)
                        , permission = 999)

            db.session.add(file)
            db.session.commit()
            return redirect(url_for(".file_list"))

    flash("잘못된 요청")
    return redirect(url_for(".file_list"))
