"""Resolve the scaffold's single Vite entry from its current build manifest."""

import json
from pathlib import Path, PurePosixPath

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

BUILD_HELP = "Run python scripts/node.py npm run build from the project root."


def frontend_assets() -> tuple[str, list[str]]:
    """Return local JS/CSS paths, rejecting incomplete or unsupported builds."""
    dist = Path(settings.VITE_DIST)
    try:
        manifest = json.loads((dist / ".vite" / "manifest.json").read_text(encoding="utf-8"))
        entry = manifest["frontend/main.ts"]
        if entry.get("isEntry") is not True or entry.get("imports") or entry.get("dynamicImports"):
            raise ValueError("Expected one entry without imported chunks")
        script = entry["file"]
        styles = entry["css"]
        if not isinstance(styles, list) or not styles:
            raise ValueError("Expected entry CSS")
        for filename, suffix in [(script, ".js"), *((style, ".css") for style in styles)]:
            if not isinstance(filename, str) or "\\" in filename:
                raise ValueError("Expected a local asset path")
            path = PurePosixPath(filename)
            resolved = (dist / filename).resolve()
            if (
                path.is_absolute()
                or path.parts[0] != "assets"
                or ".." in path.parts
                or path.suffix != suffix
                or not resolved.is_relative_to((dist / "assets").resolve())
                or not resolved.is_file()
            ):
                raise ValueError(f"Missing or invalid asset: {filename}")
    except (OSError, ValueError, KeyError, TypeError, AttributeError, IndexError) as error:
        raise ImproperlyConfigured(f"Vite build is missing, invalid, or unsupported. {BUILD_HELP}") from error
    return script, styles
