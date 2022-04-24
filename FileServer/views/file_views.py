import os
from glob import glob


from flask import Blueprint, flash, redirect, render_template, send_file, g, current_app
from .auth_views import login_required
from ..models import File

bp = Blueprint("file", __name__, url_prefix = "/file")


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
    file = File.query.get(file_id)
    file_dir = current_app.config["SHARE_FILE_DIR"]
    file_path = os.path.join(file_dir, file.filename)
    
    if not os.path.isfile(file_path):
        return render_template("404.html")

    return send_file(file_path)