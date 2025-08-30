from flask import Flask
from .extensions import db, migrate, jwt, api, limiter
from .config import Config
from .resources.auth import blp as AuthBlp
from .resources.observations import blp as ObsBlp
from .resources.buoys import blp as BuoysBlp
from .resources.health import blp as HealthBlp

def create_app(config_object=Config):
    app = Flask(__name__)
    app.config.from_object(config_object)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    limiter.init_app(app)
    api.init_app(app)  # OpenAPI + Swagger UI at /docs

    api.register_blueprint(HealthBlp)
    api.register_blueprint(AuthBlp)
    api.register_blueprint(BuoysBlp)
    api.register_blueprint(ObsBlp)

    return app

