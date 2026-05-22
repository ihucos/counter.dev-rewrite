from django.conf import settings
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import User
from .serializers import (
    EmailChangeSerializer,
    LoginSerializer,
    PasswordChangeSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    PrefsSerializer,
    RegisterSerializer,
    TimezoneSerializer,
    UserSerializer,
)


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        auth_login(request, user)
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        auth_login(request, user)
        return Response(UserSerializer(user).data)


class LogoutView(APIView):
    def post(self, request):
        auth_logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def delete(self, request):
        user = request.user
        auth_logout(request)
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PasswordChangeView(APIView):
    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save()
        auth_login(request, request.user)  # refresh session
        return Response(status=status.HTTP_204_NO_CONTENT)


class EmailChangeView(APIView):
    def post(self, request):
        serializer = EmailChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request.user.email = serializer.validated_data.get("email") or None
        request.user.save(update_fields=["email"])
        return Response(UserSerializer(request.user).data)


class TimezoneView(APIView):
    def post(self, request):
        serializer = TimezoneSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request.user.timezone = serializer.validated_data["timezone"]
        request.user.save(update_fields=["timezone"])
        return Response(UserSerializer(request.user).data)


class PrefsView(APIView):
    def post(self, request):
        serializer = PrefsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request.user.prefs = serializer.validated_data["prefs"]
        request.user.save(update_fields=["prefs"])
        return Response(UserSerializer(request.user).data)


@api_view(["POST"])
@permission_classes([AllowAny])
def password_reset_request(request):
    serializer = PasswordResetRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    email = serializer.validated_data["email"]
    # Don't leak whether the email exists
    user = User.objects.filter(email__iexact=email).first()
    if user:
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        reset_url = f"{settings.PASSWORD_RESET_URL_BASE}?uid={uid}&token={token}"
        send_mail(
            subject="Reset your counter.dev password",
            message=f"Reset link: {reset_url}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=True,
        )
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["POST"])
@permission_classes([AllowAny])
def password_reset_confirm(request):
    serializer = PasswordResetConfirmSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        uid = force_str(urlsafe_base64_decode(serializer.validated_data["uid"]))
        user = User.objects.get(pk=uid)
    except (User.DoesNotExist, ValueError, TypeError):
        return Response({"detail": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST)
    if not default_token_generator.check_token(user, serializer.validated_data["token"]):
        return Response({"detail": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST)
    user.set_password(serializer.validated_data["new_password"])
    user.save()
    return Response(status=status.HTTP_204_NO_CONTENT)
