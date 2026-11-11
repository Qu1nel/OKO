from django.urls import path

from oko.views import card_create, card_detail, card_list, page

urlpatterns = [
    path("", page, {"template": "oko/home.html"}, name="home"),
    path("dashboard/", page, {"template": "oko/dashboard.html"}, name="dashboard"),
    path("cards/", card_list, name="cards"),
    path("cards/new/", card_create, name="card_create"),
    path("cards/<int:pk>/", card_detail, name="card_detail"),
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
