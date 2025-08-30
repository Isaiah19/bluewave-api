from marshmallow import Schema, fields, validate

class BuoyCreate(Schema):
    name = fields.String(required=True, metadata={"example": "BW-001"})
    lat = fields.Float(required=True, metadata={"example": 6.430})
    lon = fields.Float(required=True, metadata={"example": 3.410})
    status = fields.String(required=True, validate=validate.OneOf(["active", "inactive", "maintenance"]),
                           metadata={"example": "active"})

class BuoyUpdate(Schema):
    name = fields.String(metadata={"example": "BW-001"})
    lat = fields.Float(metadata={"example": 6.431})
    lon = fields.Float(metadata={"example": 3.411})
    status = fields.String(validate=validate.OneOf(["active", "inactive", "maintenance"]),
                           metadata={"example": "maintenance"})

class BuoyOut(BuoyCreate):
    id = fields.Int(metadata={"example": 2})
    created_at = fields.DateTime(metadata={"example": "2025-08-30T10:00:00Z"})
    updated_at = fields.DateTime(metadata={"example": "2025-08-30T12:00:00Z"})
