# backend/accounts/urls.py

from django.urls import path
from .views import RegisterView, ProfileView, SuperuserAdminLinkView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("superuser-admin-link/", SuperuserAdminLinkView.as_view(), name="superuser_admin_link"),
]

