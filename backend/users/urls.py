from django.urls import path

from . import views

urlpatterns = [
    path("register/", views.RegisterView.as_view(), name="register"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("me/", views.MeView.as_view(), name="me"),
    path("password/change/", views.PasswordChangeView.as_view(), name="password-change"),
    path("email/change/", views.EmailChangeView.as_view(), name="email-change"),
    path("timezone/", views.TimezoneView.as_view(), name="timezone"),
    path("prefs/", views.PrefsView.as_view(), name="prefs"),
    path("password/reset/", views.password_reset_request, name="password-reset"),
    path(
        "password/reset/confirm/",
        views.password_reset_confirm,
        name="password-reset-confirm",
    ),
]
