# app/resources/health.py
from flask_smorest import Blueprint
from flask.views import MethodView

blp = Blueprint("Health", "health", url_prefix="/health", description="Liveness")

@blp.route("")
class Health(MethodView):
    def get(self):
        return {"status":"ok"}

