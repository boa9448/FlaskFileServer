import os
from glob import glob


from flask import Blueprint, render_template, send_file
from .auth_views import login_required


from .. import config

bp = Blueprint("file", __name__, url_prefix = "/file")


@bp.route("/list/")
@login_required
def list():
    file_dir = config.SHARE_FILE_DIR
    print(file_dir)

    glob_pattern = os.path.join(file_dir, "*.*")
    file_list = glob(glob_pattern)
    file_list = [os.path.split(file)[1] for file in file_list]

    return render_template("file/file_list.html", file_list = file_list)


@bp.route("/down/<path:filename>")
@login_required
def down(filename):
    file_dir = config.SHARE_FILE_DIR

    print(filename)
    file_path = os.path.join(file_dir, filename)

    return send_file(file_path)