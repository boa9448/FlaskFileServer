from flask import Flask, render_template
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()
migrate = Migrate()


def page_not_found(e):
    return render_template('404.html'), 404


def create_app():
    app = Flask(__name__)
    app.config.from_envvar("APP_CONFIG_FILE")

    db.init_app(app)
    migrate.init_app(app, db)
    from . import models

    from .views import main_views, auth_views, file_views
    app.register_error_handler(404, page_not_found)
    app.register_blueprint(main_views.bp)
    app.register_blueprint(auth_views.bp)
    app.register_blueprint(file_views.bp)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)