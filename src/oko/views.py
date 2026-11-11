from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_safe

from oko.assets import frontend_assets


@require_safe
def page(request: HttpRequest, template: str) -> HttpResponse:
    script, styles = frontend_assets()
    theme = "dark" if request.COOKIES.get("oko_theme") == "dark" else "light"
    return render(request, template, {"script": script, "styles": styles, "theme": theme})
