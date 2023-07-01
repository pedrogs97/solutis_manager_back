"""Views for authenticate module"""
from django.contrib.auth.signals import user_logged_in
from django.utils import timezone
from knox.models import AuthToken
from knox.auth import TokenAuthentication
from knox.views import LoginView as KnoxLoginView
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAdminUser
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.generics import RetrieveUpdateAPIView, CreateAPIView
from apps.authenticate.serializers import (
    LoginSerializer,
    UserSerializer,
    ChangePasswordSerializer,
    ForgotPasswordSerializer,
)
from apps.authenticate.models import User
from utils.base.permissions import (
    CustomDjangoModelPermissions,
    IsOwner,
)


class LoginView(KnoxLoginView):
    """Login view"""

    authentication_classes = None
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        """Override login with clinic"""
        serliazer = LoginSerializer(data=request.data)
        if serliazer.is_valid():
            user = serliazer.data["user"]
            token_limit_per_user = self.get_token_limit_per_user()
            if token_limit_per_user is not None:
                now = timezone.now()
                token = user.auth_token_set.filter(expiry__gt=now)
                if token.count() >= token_limit_per_user:
                    return Response(
                        {
                            "error": "Maximum amount of tokens allowed per user exceeded."
                        },
                        status=status.HTTP_403_FORBIDDEN,
                    )
            token_ttl = self.get_token_ttl()
            instance, token = AuthToken.objects.create(user, token_ttl)
            user_logged_in.send(sender=user.__class__, request=request, user=user)
            data = self.get_post_response_data(request, token, instance)
            return Response(data)
        else:
            return Response(serliazer.errors, status=status.HTTP_400_BAD_REQUEST)


class MeView(RetrieveUpdateAPIView):
    """View to get, update yourself."""

    authentication_classes = (TokenAuthentication,)
    permission_classes = (CustomDjangoModelPermissions, IsOwner)
    serializer_class = UserSerializer


class ChangePasswordView(CreateAPIView):
    """View to update password"""

    authentication_classes = (TokenAuthentication,)
    permission_classes = (CustomDjangoModelPermissions, IsOwner)
    serializer_class = ChangePasswordSerializer

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        data["user_id"] = request.user.id
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )


class ForgotPasswordView(CreateAPIView):
    """View forgot password"""

    authentication_classes = (TokenAuthentication,)
    permission_classes = IsOwner
    serializer_class = ForgotPasswordSerializer

    def create(self, request, *args, **kwargs):
        """Method POST to request forgot password"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )


class UsersAdminViewset(ModelViewSet):
    """Users views for admins."""

    authentication_classes = (TokenAuthentication,)
    permission_classes = IsAdminUser
    serializer_class = UserSerializer
    queryset = User.objects.all()


class UserViewset(ModelViewSet):
    """Users views."""

    authentication_classes = (TokenAuthentication,)
    permission_classes = (CustomDjangoModelPermissions,)
    serializer_class = UserSerializer
    queryset = User.objects.all()
