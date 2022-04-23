from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_envvar("APP_CONFIG_FILE")

    db.init_app(app)
    migrate.init_app(app, db)
    from . import models

    from .views import main_views, auth_views, file_views, admin_views
    app.register_blueprint(main_views.bp)
    app.register_blueprint(auth_views.bp)
    app.register_blueprint(file_views.bp)
    app.register_blueprint(admin_views.bp)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)