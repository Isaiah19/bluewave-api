# app/extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_smorest import Api
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from marshmallow import ValidationError

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
api = Api()  # serves /swagger-ui and /openapi.json
limiter = Limiter(key_func=get_remote_address)
