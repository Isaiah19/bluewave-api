# app/services/rbac.py
from flask_jwt_extended import get_jwt

def require_role(*roles):
    claims = get_jwt()
    return claims.get("role") in roles

def dataset_projection(record, tier):
    # 'raw' sees everything; 'processed' might hide exact coordinates or notes
    data = record.to_dict()
    if tier == "processed":
        data.pop("notes", None)
        # example: round coordinates
        data["lat"] = round(data["lat"], 3)
        data["lon"] = round(data["lon"], 3)
    return data

