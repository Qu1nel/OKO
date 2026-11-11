from django.core.exceptions import ImproperlyConfigured
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_safe
from django.views.decorators.vary import vary_on_cookie

from oko.assets import frontend_assets

SECTIONS = (
    ("dashboard", "Сегодня"),
    ("cards", "Карточки"),
    ("statistics", "Статистика"),
    ("settings", "Настройки"),
)


def _render_page(request: HttpRequest, template: str, context: dict[str, object], *, status: int = 200) -> HttpResponse:
    try:
        script, styles = frontend_assets()
    except ImproperlyConfigured:
        if status < 400:
            raise
        script, styles = None, []

    context.update({"script": script, "styles": styles, "sections": SECTIONS})
    return render(request, template, context, status=status)


@require_safe
@vary_on_cookie
def page(request: HttpRequest, template: str, **content: str) -> HttpResponse:
    active_section = request.resolver_match.url_name if request.resolver_match else None
    return _render_page(request, template, {"active_section": active_section, **content})


@vary_on_cookie
def page_not_found(request: HttpRequest, exception: Exception) -> HttpResponse:
    return _render_page(
        request,
        "oko/error.html",
        {"code": 404, "heading": "Страница не найдена", "message": "Проверьте адрес или вернитесь к обзору."},
        status=404,
    )


@vary_on_cookie
def server_error(request: HttpRequest) -> HttpResponse:
    return _render_page(
        request,
        "oko/error.html",
        {"code": 500, "heading": "Не удалось открыть страницу", "message": "Попробуйте ещё раз позже."},
        status=500,
    )
