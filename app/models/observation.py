# app/models/observation.py
from ..extensions import db
import datetime as dt  # use module alias to avoid name shadowing


def utcnow() -> dt.datetime:
    """Return current UTC datetime (timezone-aware)."""
    return dt.datetime.now(dt.timezone.utc)


class Observation(db.Model):
    __tablename__ = "observation"

    id = db.Column(db.Integer, primary_key=True)

    # Foreign Keys / relationships
    buoy_id = db.Column(db.Integer, db.ForeignKey("buoy.id"), nullable=False)

    # Core telemetry (ensure observed_at is timezone-aware)
    observed_at = db.Column(db.DateTime(timezone=True), index=True, nullable=False)

    # Note: this column is named 'timezone' by requirement; keep it.
    # We avoid shadowing by importing datetime as `dt` above.
    timezone = db.Column(db.String(64), nullable=False)

    lat = db.Column(db.Float, index=True, nullable=False)
    lon = db.Column(db.Float, index=True, nullable=False)
    temp_c = db.Column(db.Float, nullable=False)
    humidity = db.Column(db.Float, nullable=False)
    wind_m_s = db.Column(db.Float, nullable=False)
    precipitation_mm = db.Column(db.Float, nullable=False)
    haze = db.Column(db.Boolean, nullable=False, default=False)
    notes = db.Column(db.Text, default="")

    # Audit timestamps (UTC)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    # Relationship backref (defined here so Observation.buoy works even if Buoy is in another file)
    buoy = db.relationship("Buoy", backref="observations")

    def to_dict(self) -> dict:
        # Simple serializer for API responses
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def __repr__(self) -> str:
        return f"<Observation id={self.id} buoy_id={self.buoy_id} at={self.observed_at.isoformat() if self.observed_at else None}>"

