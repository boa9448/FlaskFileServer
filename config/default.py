import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

APP_DIR = "FileServer"
SHARE_FILE_DIR = os.path.join(BASE_DIR, APP_DIR, "files")