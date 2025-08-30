# BlueWave API — Full Build & Run Guide (Windows)

End-to-end notes for setting up, developing, testing, and running the **BlueWave** telemetry API with **Flask**, **MySQL**, **Docker Compose**, and **Swagger docs**.

- API base: `http://127.0.0.1:8000`
- Swagger / OpenAPI docs: `http://127.0.0.1:8000/docs`

---

## Table of Contents

1. **Prerequisites**  
2. **Project Structure**  
3. **Python Dev (Git Bash) — Local SQLite**  
4. **Fixes Applied During Development**  
5. **Run Tests**  
6. **Docker Compose (MySQL + API)**  
7. **Smoke Tests (curl / PowerShell)**  
8. **Configuration**  
9. **File Index & Source Code**  
10. **Screenshots**  
11. **Common Troubleshooting**  
12. **License**  

---

## 1) Prerequisites

- **Windows 10/11**
- **Git Bash** (bundled with Git for Windows)
- **Python 3.11+** (3.13 used in this guide)
- **Docker Desktop** (WSL2 backend enabled)
- **PowerShell** (for some commands)
- (Optional) **jq** for JSON formatting in Git Bash:
  ```bash
  winget install jqlang.jq
  jq --version
  ```

---

## 2) Project Structure

```
bluewave-api/
├─ app/
│  ├─ __init__.py
│  ├─ config.py
│  ├─ extensions.py
│  ├─ models/
│  │  ├─ __init__.py
│  │  ├─ buoy.py
│  │  ├─ observation.py
│  │  ├─ subscription.py   # (present but not required)
│  │  └─ user.py           # (present but not required)
│  ├─ resources/
│  │  ├─ __init__.py
│  │  ├─ auth.py
│  │  ├─ health.py
│  │  ├─ buoys.py
│  │  └─ observations.py
│  ├─ schemas/
│  │  ├─ __init__.py
│  │  └─ observation.py
│  └─ services/
│     ├─ __init__.py
│     ├─ filters.py
│     ├─ timeutils.py
│     └─ rbac.py
├─ tests/
│  ├─ conftest.py
│  ├─ test_buoys.py
│  └─ test_observations.py
├─ Dockerfile
├─ docker-compose.yml
├─ requirements.txt
├─ .gitattributes
├─ .gitignore
└─ README.md
```

---

## 3) Python Dev (Git Bash) — Local SQLite

```bash
# Create venv + activate
python -m venv .venv
source .venv/Scripts/activate

# Install deps
pip install -r requirements.txt

# Dev env vars
export FLASK_APP=app
export FLASK_ENV=development
export DATABASE_URL='sqlite:///bluewave.db'
export JWT_SECRET_KEY='change-me'

# Migrate SQLite
python -m flask db init
python -m flask db migrate -m "initial schema"
python -m flask db upgrade

# Run server
python -m flask run --host=0.0.0.0 --port=8000
```

Check health:
```bash
curl http://127.0.0.1:8000/health
# {"status":"ok"}
```

---

## 4) Fixes Applied During Development

- **Datetime shadowing**: renamed `timezone` import to `dt_timezone` in models (avoid collision with column named `timezone`).  
- **Added missing resources/services**: `buoys.py`, `observations.py`, `filters.py`, `rbac.py`, `timeutils.py`, plus empty `services/__init__.py`.  
- **Removed flask_marshmallow** in favor of plain Marshmallow schemas.  
- **Patched pytest sys.path** in `tests/conftest.py`.  
- **Docker Desktop 500 errors**: fixed by restarting Docker, resetting WSL2, and using `docker context use desktop-linux`.  
- **MySQL 8.4 issue**: `--default-authentication-plugin` not accepted → pinned DB image to **mysql:8.0**.  

---

## 5) Run Tests

```bash
pytest -q
coverage run -m pytest
coverage report -m
```

Example output:

```
.....                                                                    [100%]
5 passed, 11 warnings in 0.14s
```

---

## 6) Docker Compose (MySQL + API)

**docker-compose.yml:**

```yaml
services:
  db:
    image: mysql:8.0
    environment:
      MYSQL_DATABASE: bluewave
      MYSQL_USER: bluewave
      MYSQL_PASSWORD: bluewave
      MYSQL_ROOT_PASSWORD: root
      TZ: UTC
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-uroot", "-proot"]
      interval: 5s
      timeout: 3s
      retries: 30

  api:
    build: .
    environment:
      DATABASE_URL: mysql+pymysql://bluewave:bluewave@db:3306/bluewave
      JWT_SECRET_KEY: change-me
      FLASK_ENV: development
      RATELIMIT_ENABLED: "false"
    depends_on:
      db:
        condition: service_healthy
    ports:
      - "8000:8000"
```

**Commands:**

```bash
docker compose down -v
docker compose up -d --build
docker compose logs -f db   # watch until healthy
docker compose exec api python -m flask db upgrade
```

---

## 7) Smoke Tests (curl / PowerShell)

**Git Bash:**
```bash
# Health
curl -s http://127.0.0.1:8000/health

# Token
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/auth/token | jq -r .access_token)

# Create a buoy
curl -s -X POST http://127.0.0.1:8000/buoys   -H "Authorization: Bearer $TOKEN"   -H "Content-Type: application/json"   -d '{"name":"BW-DOCKER","lat":6.40,"lon":3.40,"status":"active"}' | jq
```

**PowerShell:**
```powershell
Invoke-RestMethod http://127.0.0.1:8000/health

$TOKEN = (Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/auth/token).access_token

Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/buoys `
  -Headers @{Authorization="Bearer $TOKEN"} `
  -ContentType "application/json" `
  -Body '{"name":"BW-DOCKER","lat":6.40,"lon":3.40,"status":"active"}'
```

---

## 8) Configuration

- **Environment variables**
  - `DATABASE_URL` — SQLAlchemy DSN (`sqlite:///bluewave.db` or `mysql+pymysql://...`)
  - `JWT_SECRET_KEY` — change for production
  - `FLASK_ENV` — `development` in dev
  - `RATELIMIT_ENABLED` — `false` to silence dev warning

- **OpenAPI/Swagger**: `/docs`

---

## 9) File Index & Source Code

### `requirements.txt`
```txt
Flask
Flask-SQLAlchemy
Flask-Migrate
Flask-JWT-Extended
flask-smorest
Flask-Limiter
PyMySQL
marshmallow
apispec
cryptography
pytest
coverage
```

### `Dockerfile`
```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV FLASK_APP=app
ENV PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["python","-m","flask","run","--host=0.0.0.0","--port=8000"]
```

### `docker-compose.yml`
```yaml
services:
  db:
    image: mysql:8.0
    environment:
      MYSQL_DATABASE: bluewave
      MYSQL_USER: bluewave
      MYSQL_PASSWORD: bluewave
      MYSQL_ROOT_PASSWORD: root
      TZ: UTC
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-uroot", "-proot"]
      interval: 5s
      timeout: 3s
      retries: 30

  api:
    build: .
    environment:
      DATABASE_URL: mysql+pymysql://bluewave:bluewave@db:3306/bluewave
      JWT_SECRET_KEY: change-me
      FLASK_ENV: development
      RATELIMIT_ENABLED: "false"
    depends_on:
      db:
        condition: service_healthy
    ports:
      - "8000:8000"
```

### `app/__init__.py`
```python
from flask import Flask
from .extensions import db, migrate, jwt, api, limiter
from .config import Config
from .resources.auth import blp as AuthBlp
from .resources.observations import blp as ObsBlp
from .resources.buoys import blp as BuoysBlp
from .resources.health import blp as HealthBlp

def create_app(config_object=Config):
    app = Flask(__name__)
    app.config.from_object(config_object)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    limiter.init_app(app)
    api.init_app(app)  # OpenAPI + Swagger UI at /docs

    api.register_blueprint(HealthBlp)
    api.register_blueprint(AuthBlp)
    api.register_blueprint(BuoysBlp)
    api.register_blueprint(ObsBlp)

    return app
```

### `app/config.py`
```python
import os

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///bluewave.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me")

    API_TITLE = "BlueWave API"
    API_VERSION = "v1"
    OPENAPI_VERSION = "3.0.3"
    OPENAPI_URL_PREFIX = "/"
    OPENAPI_SWAGGER_UI_PATH = "/docs"
    OPENAPI_SWAGGER_UI_URL = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"

    PROPAGATE_EXCEPTIONS = True

    # Rate limiting
    RATELIMIT_ENABLED = os.getenv("RATELIMIT_ENABLED", "true").lower() == "true"
```

### `app/extensions.py`
```python
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_smorest import Api
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
api = Api()
limiter = Limiter(key_func=get_remote_address, enabled=True)
```

### `app/resources/health.py`
```python
from flask_smorest import Blueprint

blp = Blueprint("Health", "health", url_prefix="/health", description="Health check")

@blp.route("")
def health():
    return {"status": "ok"}
```

### `app/resources/auth.py`
```python
from flask_smorest import Blueprint
from flask_jwt_extended import create_access_token
from datetime import timedelta

blp = Blueprint("Auth", "auth", url_prefix="/auth", description="Auth & tokens")

@blp.route("/token", methods=["POST"])
def token():
    # Demo token (no login form): role & tier claims embedded for RBAC/data projection
    claims = {"role": "researcher", "tier": "raw"}  # adjust as needed
    tok = create_access_token(identity="user1", additional_claims=claims, expires_delta=timedelta(hours=8))
    return {"access_token": tok}
```

### `app/models/__init__.py`
```python
from .buoy import Buoy
from .observation import Observation
```

### `app/models/buoy.py`
```python
from ..extensions import db

class Buoy(db.Model):
    __tablename__ = "buoys"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    lat = db.Column(db.Float, nullable=False)
    lon = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(32), default="active", nullable=False)

    def to_dict(self):
        return {"id": self.id, "name": self.name, "lat": self.lat, "lon": self.lon, "status": self.status}
```

### `app/models/observation.py`
```python
from datetime import datetime, timezone as dt_timezone
from ..extensions import db

class Observation(db.Model):
    __tablename__ = "observations"

    id = db.Column(db.Integer, primary_key=True)
    buoy_id = db.Column(db.Integer, db.ForeignKey("buoys.id"), nullable=False)
    observed_at = db.Column(db.DateTime(timezone=True), nullable=False)
    timezone = db.Column(db.String(64), nullable=False)

    lat = db.Column(db.Float, nullable=False)
    lon = db.Column(db.Float, nullable=False)
    temp_c = db.Column(db.Float, nullable=False)
    humidity = db.Column(db.Float, nullable=False)
    wind_m_s = db.Column(db.Float, nullable=False)
    precipitation_mm = db.Column(db.Float, nullable=False)
    haze = db.Column(db.Boolean, nullable=False, default=False)
    notes = db.Column(db.Text, default="", nullable=False)

    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(dt_timezone.utc))
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(dt_timezone.utc),
        onupdate=lambda: datetime.now(dt_timezone.utc),
    )

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
```

### `app/schemas/__init__.py`
```python
# empty is fine
```

### `app/schemas/observation.py`
```python
from marshmallow import Schema, fields, validate

class ObservationCreate(Schema):
    """Schema for creating observations (single or bulk)."""
    buoy_id = fields.Int(required=True)
    observed_at = fields.DateTime(required=True)  # ISO-8601
    timezone = fields.String(required=True)
    lat = fields.Float(required=True)
    lon = fields.Float(required=True)
    temp_c = fields.Float(required=True)
    humidity = fields.Float(required=True, validate=validate.Range(min=0, max=100))
    wind_m_s = fields.Float(required=True)
    precipitation_mm = fields.Float(required=True)
    haze = fields.Boolean(required=True)
    notes = fields.String(load_default="")

class ObservationUpdate(Schema):
    """Schema for updates. All fields optional; handler enforces PUT/PATCH semantics."""
    buoy_id = fields.Int()
    observed_at = fields.DateTime()
    timezone = fields.String()
    lat = fields.Float()
    lon = fields.Float()
    temp_c = fields.Float()
    humidity = fields.Float(validate=validate.Range(min=0, max=100))
    wind_m_s = fields.Float()
    precipitation_mm = fields.Float()
    haze = fields.Boolean()
    notes = fields.String()

class ObservationOut(ObservationCreate):
    id = fields.Int()
    created_at = fields.DateTime()
    updated_at = fields.DateTime()
```

### `app/resources/buoys.py`
```python
from flask_smorest import Blueprint, abort
from flask.views import MethodView
from flask_jwt_extended import jwt_required
from ..extensions import db
from ..models.buoy import Buoy

blp = Blueprint("Buoys", "buoys", url_prefix="/buoys", description="Manage buoys")

@blp.route("")
class BuoyList(MethodView):
    @jwt_required()
    @blp.response(200)
    def get(self):
        return {"items": [b.to_dict() for b in Buoy.query.order_by(Buoy.id).all()]}

    @jwt_required()
    @blp.response(201)
    def post(self):
        data = blp.arguments(dict, location="json")(lambda x: x)()  # quick accept any json
        name = data.get("name")
        lat = data.get("lat")
        lon = data.get("lon")
        status = data.get("status", "active")
        if not all(v is not None for v in (name, lat, lon)):
            abort(400, message="name, lat, lon are required")
        b = Buoy(name=name, lat=lat, lon=lon, status=status)
        db.session.add(b)
        db.session.commit()
        return b.to_dict()

@blp.route("/<int:buoy_id>")
class BuoyItem(MethodView):
    @jwt_required()
    @blp.response(200)
    def get(self, buoy_id):
        return Buoy.query.get_or_404(buoy_id).to_dict()

    @jwt_required()
    @blp.response(200)
    def put(self, buoy_id):
        b = Buoy.query.get_or_404(buoy_id)
        data = blp.arguments(dict, location="json")(lambda x: x)()
        for k in ("name", "lat", "lon", "status"):
            if k in data:
                setattr(b, k, data[k])
        db.session.commit()
        return b.to_dict()

    @jwt_required()
    @blp.response(204)
    def delete(self, buoy_id):
        b = Buoy.query.get_or_404(buoy_id)
        db.session.delete(b)
        db.session.commit()
        return ""
```

### `app/services/__init__.py`
```python
# empty is fine
```

### `app/services/timeutils.py`
```python
from datetime import datetime, timezone as dt_timezone

def is_current_quarter(dt):
    """Return True if dt (aware or naive treated as UTC) is inside the current quarter (UTC)."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=dt_timezone.utc)
    now = datetime.now(dt_timezone.utc)
    q_start_month = ((now.month - 1) // 3) * 3 + 1
    q_start = datetime(now.year, q_start_month, 1, tzinfo=dt_timezone.utc)
    return dt >= q_start
```

### `app/services/rbac.py`
```python
def dataset_projection(obs, tier: str):
    """
    Return a dict projection of observation record based on tier.
    - raw: full detail
    - processed: rounded coords, includes notes
    - researcher: rounded coords, hides notes
    """
    d = obs.to_dict()
    if tier == "raw":
        return d
    if tier == "processed":
        d["lat"] = round(d["lat"], 3)
        d["lon"] = round(d["lon"], 3)
        return d
    # researcher or default
    d["lat"] = round(d["lat"], 2)
    d["lon"] = round(d["lon"], 2)
    d["notes"] = ""
    return d
```

### `app/services/filters.py`
```python
from sqlalchemy import and_
from datetime import datetime

def _parse_dt(val):
    try:
        return datetime.fromisoformat(val.replace("Z", "+00:00"))
    except Exception:
        return None

def apply_observation_filters(query, Observation, args):
    filters = []
    if "from" in args:
        dt = _parse_dt(args.get("from"))
        if dt: filters.append(Observation.observed_at >= dt)
    if "to" in args:
        dt = _parse_dt(args.get("to"))
        if dt: filters.append(Observation.observed_at <= dt)

    if "buoy_id" in args:
        try:
            filters.append(Observation.buoy_id == int(args["buoy_id"]))
        except ValueError:
            pass

    # bounding box
    def ffloat(k): 
        try: return float(args[k])
        except Exception: return None

    lat_min, lat_max = ffloat("lat_min"), ffloat("lat_max")
    lon_min, lon_max = ffloat("lon_min"), ffloat("lon_max")
    if lat_min is not None: filters.append(Observation.lat >= lat_min)
    if lat_max is not None: filters.append(Observation.lat <= lat_max)
    if lon_min is not None: filters.append(Observation.lon >= lon_min)
    if lon_max is not None: filters.append(Observation.lon <= lon_max)

    if filters:
        query = query.filter(and_(*filters))
    return query
```

### `app/resources/observations.py`
```python
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

@blp.route("")
class ObservationsList(MethodView):
    @jwt_required()
    @blp.arguments(ObservationCreate(many=True), required=False)
    @blp.response(201)
    def post(self, payload=None):
        """
        Bulk create observations.
        Send either a single object or an array; both are accepted.
        """
        data = payload if isinstance(payload, list) else [payload]
        if not data or data == [None]:
            abort(400, message="Request body must be a JSON object or array of objects.")
        objs = [Observation(**item) for item in data]
        db.session.add_all(objs)
        db.session.commit()
        return {"created": [o.id for o in objs]}

    @jwt_required()
    @blp.response(200)
    def get(self):
        """
        Filter and page observations.
        Query params: from, to, buoy_id, lat_min, lat_max, lon_min, lon_max, page, per_page
        """
        args = request.args.to_dict()
        q = apply_observation_filters(db.session.query(Observation), Observation, args)
        page = max(int(args.get("page", 1)), 1)
        per = min(max(int(args.get("per_page", 100)), 1), 1000)
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
    @blp.response(200, ObservationOut)
    def get(self, obs_id):
        o = Observation.query.get_or_404(obs_id)
        tier = get_jwt().get("tier", "processed")
        return dataset_projection(o, tier)

    @jwt_required()
    @blp.arguments(ObservationCreate)     # For PUT we expect a full object (create schema)
    @blp.response(200)
    def put(self, payload, obs_id):
        """
        Full update/replace. Enforces quarter-lock for editing historical records.
        """
        o = Observation.query.get_or_404(obs_id)
        if not is_current_quarter(o.observed_at):
            abort(409, message="Historical records are locked; cannot modify prior to current quarter.")
        # Replace fields explicitly (PUT semantics)
        for field, value in payload.items():
            setattr(o, field, value)
        db.session.commit()
        return {"updated": obs_id}

    @jwt_required()
    @blp.arguments(ObservationUpdate, as_kwargs=True)  # Partial set of fields allowed
    @blp.response(200)
    def patch(self, obs_id, **update):
        """
        Partial update. Enforces quarter-lock.
        """
        o = Observation.query.get_or_404(obs_id)
        if not is_current_quarter(o.observed_at):
            abort(409, message="Historical records are locked; cannot modify prior to current quarter.")
        for k, v in update.items():
            setattr(o, k, v)
        db.session.commit()
        return {"updated": obs_id}

    @jwt_required()
    @blp.response(204)
    def delete(self, obs_id):
        """
        Delete observation. Enforces quarter-lock.
        """
        o = Observation.query.get_or_404(obs_id)
        if not is_current_quarter(o.observed_at):
            abort(409, message="Historical records are locked; cannot delete prior to current quarter.")
        db.session.delete(o)
        db.session.commit()
        return ""
```

### `tests/conftest.py`
```python
import os
import sys
import pytest

# Ensure project root is on sys.path BEFORE importing app
HERE = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(HERE, ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app import create_app
from app.extensions import db

class TestConfig:
    TESTING = True
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = "test-secret"
    API_TITLE = "BlueWave API (Test)"
    API_VERSION = "v1"
    RATELIMIT_ENABLED = False
    OPENAPI_VERSION = "3.0.3"
    OPENAPI_URL_PREFIX = "/"
    OPENAPI_SWAGGER_UI_PATH = "/docs"
    OPENAPI_SWAGGER_UI_URL = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
    PROPAGATE_EXCEPTIONS = True

@pytest.fixture(scope="session")
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture()
def client(app):
    return app.test_client()

@pytest.fixture()
def token(client):
    rv = client.post("/auth/token")
    assert rv.status_code == 200, rv.get_json()
    return rv.get_json()["access_token"]

@pytest.fixture()
def authz(token):
    return {"Authorization": f"Bearer {token}"}
```

### `tests/test_buoys.py`
```python
def test_create_and_get_buoy(client, authz):
    # Create buoy
    rv = client.post("/buoys", json={"name": "B1", "lat": 1.23, "lon": 4.56, "status": "active"}, headers=authz)
    assert rv.status_code == 201
    data = rv.get_json()
    assert data["name"] == "B1"

    # List buoys
    rv = client.get("/buoys", headers=authz)
    assert rv.status_code == 200
    assert "items" in rv.get_json()
```

### `tests/test_observations.py`
```python
from datetime import datetime, timezone

def test_create_and_list_observation(client, authz):
    # First create buoy
    rv = client.post("/buoys", json={"name": "B2", "lat": 2, "lon": 3, "status": "active"}, headers=authz)
    buoy_id = rv.get_json()["id"]

    # Create observation
    obs = {
        "buoy_id": buoy_id,
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "timezone": "UTC",
        "lat": 2.1,
        "lon": 3.1,
        "temp_c": 25.0,
        "humidity": 60,
        "wind_m_s": 3.2,
        "precipitation_mm": 0.0,
        "haze": False,
        "notes": "test obs"
    }
    rv = client.post("/observations", json=[obs], headers=authz)
    assert rv.status_code == 201
    data = rv.get_json()
    assert "created" in data

    # List observations
    rv = client.get("/observations", headers=authz)
    assert rv.status_code == 200
    assert "items" in rv.get_json()
```

---

## 10) Screenshots

> Place PNG files in `screenshots/` and ensure the file names match below.

- **Swagger UI** (`http://127.0.0.1:8000/docs`)  
  `screenshots/swagger.png`

- **Pytest Results** (`pytest -q`)  
  `screenshots/tests.png`

- **Buoy Created via curl**  
  `screenshots/curl_buoy.png`

---

## 11) Common Troubleshooting

- `pytest` fails → ensure `tests/conftest.py` sys.path fix present.  
- Docker API 500 → restart Docker Desktop, run `wsl --shutdown`, check `docker context ls`.  
- MySQL init error → ensure using `mysql:8.0` not `mysql:8.4`.  
- Port 3306 conflict → map `"3307:3306"` in compose or remove host port mapping.  

---

## 12) License

MIT (or as required by your course).

