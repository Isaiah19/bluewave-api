from flask_smorest import Blueprint, abort
from flask.views import MethodView
from flask import request
from flask_jwt_extended import jwt_required, get_jwt
from ..extensions import db
from ..models.observation import Observation
from ..schemas.observation import ObservationCreate, ObservationUpdate, ObservationOut
from ..services.filters import apply_observation_filters
from ..services.timeutils import is_current_quarter
from ..services.rbac import dataset_projection

blp = Blueprint("Observations", "observations", url_prefix="/observations", description="Telemetry")

# Swagger/OpenAPI examples
EXAMPLES_CREATE = {
    "single": {
        "summary": "Single observation",
        "value": {
            "buoy_id": 1,
            "observed_at": "2025-08-30T12:00:00Z",
            "timezone": "UTC",
            "lat": 6.43,
            "lon": 3.41,
            "temp_c": 24.5,
            "humidity": 55,
            "wind_m_s": 3.2,
            "precipitation_mm": 0.0,
            "haze": False,
            "notes": "ok"
        },
    },
    "bulk": {
        "summary": "Bulk observations",
        "value": [
            {
                "buoy_id": 1,
                "observed_at": "2025-08-30T12:00:00Z",
                "timezone": "UTC",
                "lat": 6.43,
                "lon": 3.41,
                "temp_c": 24.5,
                "humidity": 55,
                "wind_m_s": 3.2,
                "precipitation_mm": 0.0,
                "haze": False,
                "notes": "ok"
            },
            {
                "buoy_id": 1,
                "observed_at": "2025-08-30T13:00:00Z",
                "timezone": "UTC",
                "lat": 6.44,
                "lon": 3.42,
                "temp_c": 24.7,
                "humidity": 54,
                "wind_m_s": 3.0,
                "precipitation_mm": 0.0,
                "haze": False,
                "notes": "ok2"
            }
        ],
    },
}

EXAMPLE_UPDATE_FULL = {
    "summary": "Full replace (PUT)",
    "value": {
        "buoy_id": 1,
        "observed_at": "2025-08-30T12:30:00Z",
        "timezone": "UTC",
        "lat": 6.50,
        "lon": 3.50,
        "temp_c": 26.0,
        "humidity": 58,
        "wind_m_s": 2.8,
        "precipitation_mm": 0.0,
        "haze": False,
        "notes": "replaced"
    },
}

EXAMPLE_UPDATE_PATCH = {
    "summary": "Partial update (PATCH)",
    "value": {"notes": "patched"},
}

@blp.route("")
class ObservationsList(MethodView):
    @jwt_required()
    @blp.arguments(ObservationCreate(many=True), required=False)
    @blp.response(201, description="Created. Returns created ids and items (projected by tier).")
    @blp.doc(
        summary="Create observations (single or bulk)",
        description="Accepts a single object or an array of objects. All values are JSON.",
        requestBody={"required": True, "content": {"application/json": {"examples": EXAMPLES_CREATE}}},
        responses={400: {"description": "Invalid payload"}},
    )
    def post(self, payload=None):
        data = payload if isinstance(payload, list) else [payload]
        if not data or data == [None]:
            abort(400, message="Request body must be a JSON object or array of objects.")

        objs = [Observation(**item) for item in data]
        db.session.add_all(objs)
        db.session.commit()

        tier = get_jwt().get("tier", "processed")
        created_ids = [o.id for o in objs]
        created_items = [dataset_projection(o, tier) for o in objs]
        return {"created": created_ids, "items": created_items}

    @jwt_required()
    @blp.response(200, description="Filtered & paginated observations")
    @blp.doc(
        summary="List observations with filters",
        description=(
            "Query params:\n"
            "- `from`, `to` (ISO-8601)\n"
            "- `buoy_id`\n"
            "- `lat_min`, `lat_max`, `lon_min`, `lon_max`\n"
            "- `page` (default 1), `per_page` (default 100, max 1000)"
        ),
        parameters=[
            {"in": "query", "name": "from", "schema": {"type": "string", "example": "2025-08-30T00:00:00Z"}},
            {"in": "query", "name": "to", "schema": {"type": "string", "example": "2025-08-31T00:00:00Z"}},
            {"in": "query", "name": "buoy_id", "schema": {"type": "integer", "example": 1}},
            {"in": "query", "name": "lat_min", "schema": {"type": "number", "example": 6.40}},
            {"in": "query", "name": "lat_max", "schema": {"type": "number", "example": 6.50}},
            {"in": "query", "name": "lon_min", "schema": {"type": "number", "example": 3.40}},
            {"in": "query", "name": "lon_max", "schema": {"type": "number", "example": 3.50}},
            {"in": "query", "name": "page", "schema": {"type": "integer", "example": 1}},
            {"in": "query", "name": "per_page", "schema": {"type": "integer", "example": 100}},
        ],
    )
    def get(self):
        args = request.args.to_dict()
        q = apply_observation_filters(db.session.query(Observation), Observation, args)

        # paging (defensive bounds)
        try:
            page = int(args.get("page", 1))
        except ValueError:
            page = 1
        page = max(page, 1)

        try:
            per = int(args.get("per_page", 100))
        except ValueError:
            per = 100
        per = min(max(per, 1), 1000)

        tier = get_jwt().get("tier", "processed")
        items = q.order_by(Observation.observed_at.desc()).paginate(page=page, per_page=per, error_out=False).items

        return {
            "items": [dataset_projection(i, tier) for i in items],
            "count": len(items),
            "page": page,
            "per_page": per
        }

@blp.route("/<int:obs_id>")
class ObservationItem(MethodView):
    @jwt_required()
    @blp.response(200, ObservationOut, description="Observation (projected by tier)")
    @blp.doc(summary="Get observation by id")
    def get(self, obs_id):
        o = Observation.query.get_or_404(obs_id)
        tier = get_jwt().get("tier", "processed")
        return dataset_projection(o, tier)

    @jwt_required()
    @blp.arguments(ObservationCreate)
    @blp.response(200, ObservationOut, description="Updated observation (projected by tier)")
    @blp.doc(
        summary="Replace observation (PUT)",
        description="Full replace. Fails with 409 if record is not in the current quarter.",
        requestBody={"required": True, "content": {"application/json": {"examples": {"put": EXAMPLE_UPDATE_FULL}}}},
        responses={409: {"description": "Quarter lock: cannot modify historical data"}},
    )
    def put(self, payload, obs_id):
        o = Observation.query.get_or_404(obs_id)
        if not is_current_quarter(o.observed_at):
            abort(409, message="Historical records are locked; cannot modify prior to current quarter.")
        for field, value in payload.items():
            setattr(o, field, value)
        db.session.commit()
        tier = get_jwt().get("tier", "processed")
        return dataset_projection(o, tier)

    @jwt_required()
    @blp.arguments(ObservationUpdate, as_kwargs=True)
    @blp.response(200, ObservationOut, description="Updated observation (projected by tier)")
    @blp.doc(
        summary="Partially update observation (PATCH)",
        description="Partial update. Fails with 409 if record is not in the current quarter.",
        requestBody={"required": True, "content": {"application/json": {"examples": {"patch": EXAMPLE_UPDATE_PATCH}}}},
        responses={409: {"description": "Quarter lock: cannot modify historical data"}},
    )
    def patch(self, obs_id, **update):
        o = Observation.query.get_or_404(obs_id)
        if not is_current_quarter(o.observed_at):
            abort(409, message="Historical records are locked; cannot modify prior to current quarter.")
        for k, v in update.items():
            setattr(o, k, v)
        db.session.commit()
        tier = get_jwt().get("tier", "processed")
        return dataset_projection(o, tier)

    @jwt_required()
    @blp.response(204, description="Deleted")
    @blp.doc(
        summary="Delete observation",
        description="Delete. Fails with 409 if record is not in the current quarter.",
        responses={409: {"description": "Quarter lock: cannot delete historical data"}},
    )
    def delete(self, obs_id):
        o = Observation.query.get_or_404(obs_id)
        if not is_current_quarter(o.observed_at):
            abort(409, message="Historical records are locked; cannot delete prior to current quarter.")
        db.session.delete(o)
        db.session.commit()
        return ""

