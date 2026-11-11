import json
import os
import re
import tempfile
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urljoin, urlsplit
from urllib.request import urlopen

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "oko.settings")
django.setup()

from django.conf import settings  # noqa: E402
from django.contrib.staticfiles.testing import StaticLiveServerTestCase  # noqa: E402
from django.core.exceptions import ImproperlyConfigured  # noqa: E402
from django.test import SimpleTestCase, override_settings  # noqa: E402

from oko.assets import frontend_assets  # noqa: E402


class AssetLinks(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.urls: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "script" and attributes.get("type") == "module":
            self.urls.append(attributes["src"] or "")
        if tag == "link" and attributes.get("rel") == "stylesheet":
            self.urls.append(attributes["href"] or "")


@override_settings(ALLOWED_HOSTS=["testserver"])
class PageTests(SimpleTestCase):
    def test_home_uses_real_manifest_and_allows_only_safe_methods(self) -> None:
        response = self.client.get("/")
        self.assertContains(response, "Открыть дашборд")
        self.assertContains(response, 'href="/dashboard/"')
        parser = AssetLinks()
        parser.feed(response.content.decode())
        script, styles = frontend_assets()
        self.assertCountEqual(parser.urls, [f"/static/{path}" for path in [script, *styles]])
        self.assertEqual(self.client.head("/").status_code, 200)
        self.assertEqual(self.client.post("/").status_code, 405)
        self.assertEqual(self.client.get("/missing/").status_code, 404)

    def test_dashboard_renders_the_empty_state_and_reads_the_theme_cookie(self) -> None:
        for value, theme in (("dark", "dark"), ("light", "light"), ("unexpected", "light")):
            self.client.cookies["oko_theme"] = value
            for path in ("/", "/dashboard/"):
                with self.subTest(cookie=value, path=path):
                    response = self.client.get(path)
                    self.assertContains(response, f'data-theme="{theme}"')
                    self.assertIn("Cookie", response.headers["Vary"])

        self.client.cookies.clear()
        response = self.client.get("/dashboard/")
        self.assertContains(response, 'data-theme="light"')
        self.assertContains(response, "Здесь появится график")
        self.assertContains(response, "Пока нечего повторять")
        self.assertEqual(self.client.head("/dashboard/").status_code, 200)
        self.assertEqual(self.client.post("/dashboard/").status_code, 405)

    def test_invalid_build_fails_with_rebuild_instruction_without_touching_real_dist(self) -> None:
        self.enterContext(self.assertLogs("django.request", level="ERROR"))
        work = settings.BASE_DIR / ".work"
        work.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=work) as temporary:
            dist = Path(temporary)
            with self.settings(VITE_DIST=dist):
                with self.assertRaisesRegex(ImproperlyConfigured, "npm run build"):
                    self.client.get("/")
                (dist / ".vite").mkdir()
                manifest = dist / ".vite" / "manifest.json"
                manifest.write_text("{broken", encoding="utf-8")
                with self.assertRaisesRegex(ImproperlyConfigured, "npm run build"):
                    self.client.get("/")
                manifest.write_text("{}", encoding="utf-8")
                with self.assertRaisesRegex(ImproperlyConfigured, "npm run build"):
                    self.client.get("/")

                (dist / "assets").mkdir()
                (dist / "assets" / "main.js").write_text("export {};", encoding="utf-8")
                css = dist / "assets" / "main.css"
                css.write_text("body {}", encoding="utf-8")
                entry = {"isEntry": True, "file": "assets/main.js", "css": ["assets/main.css"]}
                for changes in [
                    {"file": "assets/missing.js"},
                    {"css": ["assets/missing.css"]},
                    {"css": []},
                    {"file": "../outside.js"},
                    {"file": "https://example.invalid/main.js"},
                    {"imports": ["shared.js"]},
                    {"dynamicImports": ["lazy.js"]},
                ]:
                    with self.subTest(changes=changes):
                        manifest.write_text(json.dumps({"frontend/main.ts": {**entry, **changes}}), encoding="utf-8")
                        with self.assertRaisesRegex(ImproperlyConfigured, "npm run build"):
                            self.client.get("/")
                manifest.write_text(json.dumps({"frontend/main.ts": entry}), encoding="utf-8")
                self.assertEqual(self.client.get("/").status_code, 200)
                css.unlink()
                with self.assertRaisesRegex(ImproperlyConfigured, "npm run build"):
                    self.client.get("/")


class BuiltPageHTTPTests(StaticLiveServerTestCase):
    databases = set()

    def test_built_css_resources_load_from_the_served_stylesheet_url(self) -> None:
        with urlopen(self.live_server_url + "/", timeout=10) as response:
            parser = AssetLinks()
            parser.feed(response.read().decode())
        resources = []
        for path in parser.urls:
            if not path.endswith(".css"):
                continue
            stylesheet_url = self.live_server_url + path
            with urlopen(stylesheet_url, timeout=10) as response:
                css = response.read().decode()
            for reference in re.findall(r"url\(([^)]+)\)", css):
                asset_url = urljoin(stylesheet_url, reference.strip("\"' "))
                self.assertEqual(urlsplit(asset_url).netloc, urlsplit(self.live_server_url).netloc)
                try:
                    response = urlopen(asset_url, timeout=10)
                except HTTPError as error:
                    error.close()
                    raise
                with response:
                    self.assertEqual(response.status, 200)
                    self.assertGreater(len(response.read()), 0)
                resources.append(asset_url)
        self.assertTrue(resources, "Expected the local font referenced by the built CSS")

    def test_live_html_and_local_assets_are_served_by_django_staticfiles(self) -> None:
        page_assets = []
        for route in ("/", "/dashboard/"):
            with self.subTest(route=route), urlopen(self.live_server_url + route, timeout=10) as response:
                self.assertEqual(response.status, 200)
                self.assertEqual(response.headers.get_content_type(), "text/html")
                parser = AssetLinks()
                parser.feed(response.read().decode())
                self.assertGreaterEqual(len(parser.urls), 2)
                page_assets.append(parser.urls)
        self.assertEqual(page_assets[0], page_assets[1])
        for path in page_assets[0]:
            self.assertTrue(path.startswith("/static/assets/"))
            with urlopen(self.live_server_url + path, timeout=10) as response:
                self.assertEqual(response.status, 200)
                expected = "text/css" if path.endswith(".css") else "javascript"
                self.assertIn(expected, response.headers.get_content_type())
                self.assertGreater(len(response.read()), 0)
        for path in ["/static/.vite/manifest.json", "/static/assets/missing.js"]:
            with self.subTest(path=path), self.assertRaises(HTTPError) as error:
                urlopen(self.live_server_url + path, timeout=10)
            self.assertEqual(error.exception.code, 404)
            error.exception.close()
