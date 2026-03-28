from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)

    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "kallisto-dev-secret")
    
    # MySQL connection via environment variable or default
    db_uri = os.environ.get(
        "DATABASE_URL",
        "mysql+pymysql://root:1234@localhost:3306/project"
    )
    app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    from .api import api
    from .views import views

    app.register_blueprint(api)
    app.register_blueprint(views)

    with app.app_context():
        db.create_all()

    return app