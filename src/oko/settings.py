"""Development settings for the loopback-only source-checkout scaffold."""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
VITE_DIST = BASE_DIR / "dist"

# No sessions, user data, or database are used by this technical page
SECRET_KEY = "oko-local-development-scaffold-only"
DEBUG = True
ALLOWED_HOSTS = ["127.0.0.1", "localhost", "[::1]"]
INSTALLED_APPS = ["django.contrib.staticfiles", "oko"]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "oko.urls"
WSGI_APPLICATION = "oko.wsgi.application"
TEMPLATES = [{"BACKEND": "django.template.backends.django.DjangoTemplates", "APP_DIRS": True}]
STATIC_URL = "/static/"
STATICFILES_DIRS = [("assets", VITE_DIST / "assets")]
USE_TZ = True
