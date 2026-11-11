from django.contrib import messages
from django.core.exceptions import ImproperlyConfigured
from django.db import OperationalError
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_safe
from django.views.decorators.vary import vary_on_cookie
from loguru import logger

from oko.assets import frontend_assets
from oko.forms import CardForm
from oko.models import Card

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


@require_safe
@vary_on_cookie
def card_list(request: HttpRequest) -> HttpResponse:
    return _render_page(request, "oko/cards.html", {"active_section": "cards", "cards": Card.objects.all()})


@require_http_methods(["GET", "HEAD", "POST"])
@vary_on_cookie
def card_create(request: HttpRequest) -> HttpResponse:
    form = CardForm(request.POST if request.method == "POST" else None)
    status = 200
    if request.method == "POST" and form.is_valid():
        try:
            form.save()
        except OperationalError as error:
            logger.error("Could not save card to SQLite: {}", error)
            form.add_error(None, "Не удалось сохранить карточку. Попробуйте ещё раз.")
            status = 503
        else:
            messages.success(request, "Карточка сохранена")
            return redirect("cards")

    return _render_page(request, "oko/card_form.html", {"active_section": "cards", "form": form}, status=status)


@require_safe
@vary_on_cookie
def card_detail(request: HttpRequest, pk: int) -> HttpResponse:
    card = get_object_or_404(Card, pk=pk)
    return _render_page(request, "oko/card_detail.html", {"active_section": "cards", "card": card})


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
