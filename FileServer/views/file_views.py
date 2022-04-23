import os
from glob import glob


from flask import Blueprint, flash, redirect, render_template, send_file, g 
from .auth_views import login_required


from .. import config

bp = Blueprint("file", __name__, url_prefix = "/file")


@bp.route("/list/")
@login_required
def _list():
    if g.user.permission == 0:
        flash("권한이 부족합니다")
        return render_template("file/file_list.html", file_info_list = list())

    file_dir = config.SHARE_FILE_DIR

    glob_pattern = os.path.join(file_dir, "*.*")
    file_list = glob(glob_pattern)

    file_info_list = list()
    for file in file_list:
        name = os.path.split(file)[1]
        file_size = os.path.getsize(file) / 1024
        file_info_list.append((name, file_size))

    return render_template("file/file_list.html", file_info_list = file_info_list)


@bp.route("/down/<path:filename>")
@login_required
def down(filename):
    file_dir = config.SHARE_FILE_DIR
    file_path = os.path.join(file_dir, filename)

    return send_file(file_path)