from ..extensions import db

class Buoy(db.Model):
    __tablename__ = "buoy"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True, nullable=False)
    lat = db.Column(db.Float)
    lon = db.Column(db.Float)
    status = db.Column(db.String(32), nullable=False, default="active")
