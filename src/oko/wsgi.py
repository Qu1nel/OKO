"""Expose the application used by Django's development server."""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "oko.settings")
application = get_wsgi_application()
