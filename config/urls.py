from django.contrib import admin
from django.urls import path
from core import views

urlpatterns = [
    path("admin/", admin.site.urls),

    path("", views.home, name="home"),
    path("login/", views.login_page, name="login"),
    path("set-password/", views.set_password, name="set_password"),
    path("logout/", views.logout_view, name="logout"),

    path("dashboard/", views.dashboard, name="dashboard"),
    path("bitcoin/", views.bitcoin, name="bitcoin"),
    path("insurance/", views.insurance, name="insurance"),
]
