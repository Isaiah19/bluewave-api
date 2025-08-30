# app/services/filters.py
from sqlalchemy import and_
from dateutil.parser import isoparse

def apply_observation_filters(q, model, args):
    if "from" in args:
        q = q.filter(model.observed_at >= isoparse(args["from"]))
    if "to" in args:
        q = q.filter(model.observed_at <= isoparse(args["to"]))
    if "buoy_id" in args:
        q = q.filter(model.buoy_id == int(args["buoy_id"]))
    # bounding box? lat_min, lat_max, lon_min, lon_max
    for key in ("lat_min","lat_max","lon_min","lon_max"):
        if key in args: args[key] = float(args[key])
    if all(k in args for k in ("lat_min","lat_max")):
        q = q.filter(model.lat >= args["lat_min"], model.lat <= args["lat_max"])
    if all(k in args for k in ("lon_min","lon_max")):
        q = q.filter(model.lon >= args["lon_min"], model.lon <= args["lon_max"])
    return q

