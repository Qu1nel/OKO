from django.urls import path

from oko.views import page

urlpatterns = [
    path("", page, {"template": "oko/home.html"}, name="home"),
    path("dashboard/", page, {"template": "oko/dashboard.html"}, name="dashboard"),
    path(
        "cards/",
        page,
        {"template": "oko/empty_section.html", "heading": "Карточки", "message": "Здесь пока нет карточек."},
        name="cards",
    ),
    path(
        "statistics/",
        page,
        {
            "template": "oko/empty_section.html",
            "heading": "Статистика",
            "message": "Здесь появятся результаты занятий.",
        },
        name="statistics",
    ),
    path(
        "settings/",
        page,
        {"template": "oko/empty_section.html", "heading": "Настройки", "message": "Здесь будут настройки приложения."},
        name="settings",
    ),
]

handler404 = "oko.views.page_not_found"
handler500 = "oko.views.server_error"
