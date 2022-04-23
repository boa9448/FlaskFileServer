export FLASK_APP=FileServer
export APP_CONFIG_FILE=E:/source/repos/FlaskFileServer/config/production.py

waitress-serve --port=5000 --call "FileServer:create_app"