# tests/conftest.py
import os
import sys
import pytest

# --- Ensure project root (…/bluewave-api) is on sys.path BEFORE importing app ---
HERE = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(HERE, ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app import create_app
from app.extensions import db


class TestConfig:
    TESTING = True
    DEBUG = False

    # Fast, isolated DB for tests
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Security / API meta (match your app’s defaults as needed)
    JWT_SECRET_KEY = "test-secret"
    API_TITLE = "BlueWave API (Test)"
    API_VERSION = "v1"

    # Disable rate limiting in tests
    RATELIMIT_ENABLED = False

    # Smorest/OpenAPI (fine for tests, keeps app happy)
    OPENAPI_VERSION = "3.0.3"
    OPENAPI_URL_PREFIX = "/"
    OPENAPI_SWAGGER_UI_PATH = "/docs"
    OPENAPI_SWAGGER_UI_URL = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
    PROPAGATE_EXCEPTIONS = True


@pytest.fixture(scope="session")
def app():
    """Create an app bound to an in-memory DB, then tear it down after the session."""
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
    """Obtain a JWT from /auth/token for authenticated endpoints."""
    rv = client.post("/auth/token")
    assert rv.status_code == 200, rv.get_json()
    return rv.get_json()["access_token"]


@pytest.fixture()
def authz(token):
    return {"Authorization": f"Bearer {token}"}

