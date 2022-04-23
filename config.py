import os 


BASE_DIR = os.path.dirname(__file__)

SQLALCHEMY_DATABASE_URI = "sqlite:///{}".format(os.path.join(BASE_DIR, "FileServer.db"))
SQLALCHEMY_TRACK_MODIFICATIONS = False
SECRET_KEY = "dev"

APP_DIR = "FileServer"
SHARE_FILE_DIR = os.path.join(BASE_DIR, APP_DIR, "files")