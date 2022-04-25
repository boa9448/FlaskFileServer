import os
import hashlib
from glob import glob
from datetime import datetime


from flask import url_for, redirect, flash, g, render_template, Blueprint, current_app, request
from werkzeug.utils import secure_filename
from sqlalchemy import and_


from .. import db
from ..models import User, File, FileAccessPermission
from auth_views import login_required, admin_permission_required, log


bp = Blueprint("admin", __name__, url_prefix = "/admin")


@bp.route("/user/list/")
@login_required
@admin_permission_required
def user_list():
    user_list = User.query.all()
    return render_template("auth/user_manage.html", user_list = user_list)


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


@bp.route("/user/permission/<int:user_id>/")
@login_required
@admin_permission_required
def user_permission(user_id):
    permission = request.args.get("permission", None)
    if permission is None:
        flash("잘못된 권한입니다")
        return redirect(url_for(".user_list"))

    user = User.query.get_or_404(user_id)
    if not user:
        flash("잘못된 유저 아이디입니다")
    else:
        log("권한 변경", user)
        user.permission = permission
        db.session.add(user)
        db.session.commit()

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
    file_list = File.query.all()
    
    if file_id:
        toggle_file_access_permission(user_id, file_id)

    #WDW : 최적화 필요
    file_info_list = list()
    for idx, file in enumerate(file_list, 1):
        result = FileAccessPermission.query.filter_by(user_id = user_id, file_id = idx).first()
        file_info_list.append((file, True if result else False))

    return render_template("auth/user_file_manage.html", user_id = user_id, file_list = file_info_list)


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
