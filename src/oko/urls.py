from django.urls import path

from oko.views import page

urlpatterns = [
    path("", page, {"template": "oko/home.html"}, name="home"),
    path("dashboard/", page, {"template": "oko/dashboard.html"}, name="dashboard"),
]
