from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_safe
from django.views.decorators.vary import vary_on_cookie

from oko.assets import frontend_assets


@require_safe
@vary_on_cookie
def page(request: HttpRequest, template: str) -> HttpResponse:
    script, styles = frontend_assets()
    return render(request, template, {"script": script, "styles": styles})
