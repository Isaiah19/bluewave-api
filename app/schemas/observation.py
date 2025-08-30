from marshmallow import Schema, fields, validate

# ── Create (POST, PUT) ─────────────────────────────────────────────────────────

class ObservationCreate(Schema):
    """Schema for creating observations (single or bulk)."""
    buoy_id = fields.Int(required=True, metadata={"description": "Buoy ID", "example": 1})
    observed_at = fields.DateTime(required=True, metadata={"description": "ISO-8601 time (UTC recommended)", "example": "2025-08-30T12:00:00Z"})
    timezone = fields.String(required=True, metadata={"example": "UTC"})
    lat = fields.Float(required=True, metadata={"example": 6.430})
    lon = fields.Float(required=True, metadata={"example": 3.410})
    temp_c = fields.Float(required=True, metadata={"example": 24.5})
    humidity = fields.Float(required=True, validate=validate.Range(min=0, max=100), metadata={"example": 55})
    wind_m_s = fields.Float(required=True, metadata={"example": 3.2})
    precipitation_mm = fields.Float(required=True, metadata={"example": 0.0})
    haze = fields.Boolean(required=True, metadata={"example": False})
    notes = fields.String(load_default="", metadata={"example": "clear sky"})

# ── Update (PATCH) ─────────────────────────────────────────────────────────────

class ObservationUpdate(Schema):
    """Schema for partial updates (PATCH)."""
    buoy_id = fields.Int(metadata={"example": 1})
    observed_at = fields.DateTime(metadata={"example": "2025-08-30T12:30:00Z"})
    timezone = fields.String(metadata={"example": "UTC"})
    lat = fields.Float(metadata={"example": 6.500})
    lon = fields.Float(metadata={"example": 3.500})
    temp_c = fields.Float(metadata={"example": 26.0})
    humidity = fields.Float(validate=validate.Range(min=0, max=100), metadata={"example": 58})
    wind_m_s = fields.Float(metadata={"example": 2.8})
    precipitation_mm = fields.Float(metadata={"example": 0.0})
    haze = fields.Boolean(metadata={"example": False})
    notes = fields.String(metadata={"example": "patched"})

# ── Output ─────────────────────────────────────────────────────────────────────

class ObservationOut(ObservationCreate):
    """Schema for responses."""
    id = fields.Int(metadata={"example": 42})
    created_at = fields.DateTime(metadata={"example": "2025-08-30T12:00:01Z"})
    updated_at = fields.DateTime(metadata={"example": "2025-08-30T12:30:01Z"})

