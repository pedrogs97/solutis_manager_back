"""URLs for authenticate module"""
from django.urls import include, path

from knox import views as knox_views
from rest_framework import routers
from apps.authenticate.views import (
    LoginView,
    UsersAdminViewset,
    UserViewset,
)

app_name = "authenticate"

router = routers.DefaultRouter()
router.register(r"users-admin", UsersAdminViewset)
router.register(r"users", UserViewset)


urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", knox_views.LogoutView.as_view(), name="knox_logout"),
    path("logoutall/", knox_views.LogoutAllView.as_view(), name="knox_logoutall"),
    path("", include(router.urls)),
]


urlpatterns = [path("authenticate/", include(urlpatterns))]
