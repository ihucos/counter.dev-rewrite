from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    LoginSerializer,
    PasswordChangeSerializer,
    RegisterSerializer,
    UpdateSettingsSerializer,
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
        auth_login(request, request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class SettingsView(APIView):
    def post(self, request):
        serializer = UpdateSettingsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        changed = False
        for field in ("timezone", "email", "prefs"):
            if field in serializer.validated_data:
                setattr(user, field, serializer.validated_data[field])
                changed = True
        if changed:
            user.save()
        return Response(UserSerializer(user).data)
