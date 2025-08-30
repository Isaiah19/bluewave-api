from flask_smorest import Blueprint, abort
from flask.views import MethodView
from flask import request
from flask_jwt_extended import jwt_required
from ..extensions import db, limiter
from ..models.buoy import Buoy
from ..schemas.buoy import BuoyCreate, BuoyUpdate, BuoyOut

blp = Blueprint("Buoys", "buoys", url_prefix="/buoys", description="Manage buoy registry")

# Swagger/OpenAPI examples
EXAMPLE_CREATE = {
    "single": {
        "summary": "Create a buoy",
        "value": {"name": "BW-API", "lat": 6.43, "lon": 3.41, "status": "active"},
    }
}
EXAMPLE_PUT = {
    "summary": "Replace buoy (PUT)",
    "value": {"name": "BW-API", "lat": 6.44, "lon": 3.42, "status": "maintenance"},
}
EXAMPLE_PATCH = {"summary": "Partial update (PATCH)", "value": {"status": "inactive"}}

@blp.route("")
class BuoyList(MethodView):
    @jwt_required()
    @limiter.limit("60/minute")  # read-friendly
    @blp.response(200, BuoyOut(many=True), description="List buoys")
    @blp.doc(
        summary="List buoys",
        parameters=[
            {"in": "query", "name": "q", "schema": {"type": "string", "example": "BW-"}}
        ],
        description="Optionally filter by name substring using `?q=`.",
    )
    def get(self):
        q = request.args.get("q", "").strip()
        query = Buoy.query
        if q:
            query = query.filter(Buoy.name.ilike(f"%{q}%"))
        return query.order_by(Buoy.id.asc()).all()

    @jwt_required()
    @limiter.limit("10/minute")  # protect writes
    @blp.arguments(BuoyCreate)
    @blp.response(201, BuoyOut, description="Created buoy")
    @blp.doc(
        summary="Create buoy",
        requestBody={"required": True, "content": {"application/json": {"examples": EXAMPLE_CREATE}}},
        responses={409: {"description": "Buoy with same name exists"}},
    )
    def post(self, payload):
        # Unique by name
        if Buoy.query.filter_by(name=payload["name"]).first():
            abort(409, message="Buoy name already exists.")
        b = Buoy(**payload)
        db.session.add(b)
        db.session.commit()
        return b

@blp.route("/<int:buoy_id>")
class BuoyItem(MethodView):
    @jwt_required()
    @limiter.limit("60/minute")
    @blp.response(200, BuoyOut, description="Buoy")
    @blp.doc(summary="Get buoy by id")
    def get(self, buoy_id):
        return Buoy.query.get_or_404(buoy_id)

    @jwt_required()
    @limiter.limit("10/minute")
    @blp.arguments(BuoyCreate)  # PUT expects full object
    @blp.response(200, BuoyOut, description="Updated buoy (PUT)")
    @blp.doc(
        summary="Replace buoy (PUT)",
        requestBody={"required": True, "content": {"application/json": {"examples": {"put": EXAMPLE_PUT}}}},
    )
    def put(self, payload, buoy_id):
        b = Buoy.query.get_or_404(buoy_id)
        # Enforce unique name if changed
        if payload["name"] != b.name and Buoy.query.filter_by(name=payload["name"]).first():
            abort(409, message="Buoy name already exists.")
        for k, v in payload.items():
            setattr(b, k, v)
        db.session.commit()
        return b

    @jwt_required()
    @limiter.limit("10/minute")
    @blp.arguments(BuoyUpdate, as_kwargs=True)
    @blp.response(200, BuoyOut, description="Updated buoy (PATCH)")
    @blp.doc(
        summary="Partially update buoy (PATCH)",
        requestBody={"required": True, "content": {"application/json": {"examples": {"patch": EXAMPLE_PATCH}}}},
    )
    def patch(self, buoy_id, **updates):
        b = Buoy.query.get_or_404(buoy_id)
        # If name is being changed, check uniqueness
        if "name" in updates and updates["name"] != b.name:
            if Buoy.query.filter_by(name=updates["name"]).first():
                abort(409, message="Buoy name already exists.")
        for k, v in updates.items():
            setattr(b, k, v)
        db.session.commit()
        return b

    @jwt_required()
    @limiter.limit("10/minute")
    @blp.response(204, description="Deleted")
    @blp.doc(summary="Delete buoy")
    def delete(self, buoy_id):
        b = Buoy.query.get_or_404(buoy_id)
        db.session.delete(b)
        db.session.commit()
        return ""
