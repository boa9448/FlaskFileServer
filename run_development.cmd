@echo off
set FLASK_APP=FileServer
set FLASK_ENV=development
set APP_CONFIG_FILE=..\config\development.py

flask run --port 5001