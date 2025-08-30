from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# --- Core config (env-first for safety) ---
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-secret-change-me")
DEBUG = os.getenv("DJANGO_DEBUG", "true").lower() == "true"
ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")

# --- Installed apps ---
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "store",  # our e-commerce app
]

# --- Security / middleware (CSRF + SecurityMiddleware enabled) ---
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",          # (security)
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",             # (CSRF protection)
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "bluewave_site.urls"

# --- Templates (add project-level templates folder for Bootstrap pages) ---
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],  # <-- create this folder
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "bluewave_site.wsgi.application"

# --- Database: SQLite in development (US-19) ---
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# To switch to MySQL later (US-20), set DJANGO_DB=mysql and provide env vars:
if os.getenv("DJANGO_DB", "sqlite").lower() == "mysql":
    DATABASES["default"] = {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.getenv("MYSQL_DB", "bluewave"),
        "USER": os.getenv("MYSQL_USER", "bluewave"),
        "PASSWORD": os.getenv("MYSQL_PASSWORD", "bluewave"),
        "HOST": os.getenv("MYSQL_HOST", "localhost"),
        "PORT": os.getenv("MYSQL_PORT", "3306"),
        # Optional: "OPTIONS": {"charset": "utf8mb4"},
    }

# --- Password validation (defaults fine) ---
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- i18n / tz ---
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# --- Static files ---
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]  # create this folder for CSS/JS if needed

# --- Auth helpers ---
LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/dashboard/"
LOGOUT_REDIRECT_URL = "/"

# --- Integration: Flask API base for JWT requests from the dashboard ---
BLUEWAVE_API_BASE = os.getenv("BLUEWAVE_API_BASE", "http://127.0.0.1:8000")

# --- Default PK type ---
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

