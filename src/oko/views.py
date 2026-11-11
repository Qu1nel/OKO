from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_safe

from oko.assets import frontend_assets


@require_safe
def home(request: HttpRequest) -> HttpResponse:
    script, styles = frontend_assets()
    return render(request, "oko/home.html", {"script": script, "styles": styles})
