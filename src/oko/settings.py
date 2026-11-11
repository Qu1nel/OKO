"""Development settings for the loopback-only application."""

import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured


def _database_path() -> Path:
    if override := os.environ.get("OKO_DB_PATH"):
        path = Path(override).expanduser()
        if not path.is_absolute():
            raise ImproperlyConfigured("OKO_DB_PATH must be an absolute path to a SQLite file.")
        return path

    if os.name == "nt":
        data_dir = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
        return data_dir / "OKO" / "oko.sqlite3"

    data_dir = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share")
    if not data_dir.is_absolute():
        data_dir = Path.home() / ".local" / "share"
    return data_dir / "oko" / "oko.sqlite3"


BASE_DIR = Path(__file__).resolve().parents[2]
VITE_DIST = BASE_DIR / "dist"

SECRET_KEY = "oko-local-development-scaffold-only"
DEBUG = True
ALLOWED_HOSTS = ["127.0.0.1", "localhost", "[::1]"]
INSTALLED_APPS = ["django.contrib.staticfiles", "django.contrib.messages", "oko"]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "oko.urls"
WSGI_APPLICATION = "oko.wsgi.application"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": ["oko.theme.theme_context", "django.contrib.messages.context_processors.messages"]
        },
    }
]
STATIC_URL = "/static/"
STATICFILES_DIRS = [("assets", VITE_DIST / "assets")]
MESSAGE_STORAGE = "django.contrib.messages.storage.cookie.CookieStorage"
DATABASES = {
    "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": _database_path(), "TEST": {"NAME": ":memory:"}}
}
USE_TZ = True
