# app/resources/auth.py
from flask_smorest import Blueprint, abort
from flask.views import MethodView
from flask_jwt_extended import create_access_token
from datetime import timedelta

blp = Blueprint("Auth", "auth", url_prefix="/auth", description="JWT auth")

@blp.route("/token")
class TokenResource(MethodView):
    @blp.doc(description="Exchange username/password for a JWT")
    def post(self):
        # In production: verify password, fetch role/tier from DB
        # For demo, issue a token with claims:
        claims = {"role":"researcher", "tier":"raw"}
        token = create_access_token(identity="user1", additional_claims=claims, expires_delta=timedelta(hours=8))
        return {"access_token": token}, 200

