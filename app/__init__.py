from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from config import config

db = SQLAlchemy()
migrate = Migrate()

db = SQLAlchemy()
migrate = Migrate()
from flask_jwt_extended import JWTManager
from app.routes.routes import auth_blueprint
from app.routes.account_routes import account_blueprint

jwt = JWTManager()
def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # Register the blueprints
    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    app.register_blueprint(account_blueprint, url_prefix='/account')

    return app
