"""Serializers for authenticate module"""
import re
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from django.contrib.auth.hashers import make_password
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import serializers
from apps.authenticate.models import User
from utils.base.serializers import DynamicFieldsModelSerializer


class UserSerializer(DynamicFieldsModelSerializer):
    """
    Serializer for create and update User
    """

    clinics = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()

    class Meta:
        """
        Class Meta
        """

        model = User
        extra_kwargs = {"password": {"write_only": True}}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.min_length = (
            8
            if (settings.MIN_LENGTH_PASSWORD is None)
            else settings.MIN_LENGTH_PASSWORD
        )
        self.special_chars = (
            ["!", "@", "#", "_", ".", "+", "-", "*"]
            if (isinstance(settings.SPECIAL_CHAR, list))
            or (settings.SPECIAL_CHAR is None)
            else settings.SPECIAL_CHAR
        )

    def validate_password(self, new_pass):
        """
        Validate password field before save
        """
        if new_pass.isdigit():
            raise ValidationError(
                _("This password is entirely numeric."),
                code="password_entirely_numeric",
            )
        if len(new_pass) < self.min_length:
            raise ValidationError(
                _(
                    f"This password is too short. It must contain at least \
                    {self.min_length} character."
                ),
                code="password_too_short",
            )
        valid = False
        for special_char in self.special_chars:
            if special_char in new_pass:
                valid = True
                break
        if not valid:
            raise ValidationError(
                _(
                    "This password has no special characters. It must contain at least \
                    special character. "
                    + ",".join(self.special_chars)
                ),
                code="password_without_special_char",
            )

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        if password and instance.check_password(password):
            instance.set_password(validated_data["password"])
        instance = super().update(instance, validated_data)
        return instance

    def get_permissions(self, obj: User):
        """List of user permissions serialized"""
        return obj.get_user_permissions()


class LoginSerializer(serializers.Serializer):
    """
    Login serializer

    Validate email and password
    """

    email = serializers.EmailField(required=True, allow_blank=False)
    password = serializers.CharField(
        required=True, style={"input_type": "password"}, allow_blank=False
    )

    def validate(self, attrs):
        email = attrs.pop("email", "")
        password = attrs.pop("password", "")
        if email == "" or password == "":
            msg = _("No credentials provided.")
            raise ValidationError(msg)
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist as user_does_not_exist:
            msg = _("Unable to log in with provided credentials.")
            raise ValidationError(msg) from user_does_not_exist

        if not user:
            msg = _("Unable to log in with provided credentials.")
            raise ValidationError(msg)
        return {"user": user}

    def create(self, validated_data):
        """Not implmented"""
        return None

    def update(self, instance, validated_data):
        """Not implmented"""
        return None


class RegisterUserSerializer(serializers.ModelSerializer):
    """
    Register serializer

    Register new user
    """

    password = serializers.CharField(write_only=True, min_length=8)
    password_confirmation = serializers.CharField(write_only=True, min_length=8)

    regex_for_user = re.compile("[=@_!#$%^&*()<>?/\|}{~:]")
    regex_for_email = re.compile("[=!#$%^&*()<>?/\|}{~:]")

    class Meta:
        """
        Class Meta
        """

        model = User

    def validate(self, attrs: dict) -> dict:
        if attrs["username"] and self.regex_for_user.search(attrs["username"]) != None:
            raise serializers.ValidationError(
                "Invalid username.",
            )

        if (
            attrs["email"]
            and self.regex_for_email.search(attrs["email"]) != None
            and "@" not in attrs["email"]
        ):
            raise serializers.ValidationError(
                "Invalid email.",
            )

        if User.objects.filter(email=attrs["email"]).exists():
            raise serializers.ValidationError(
                _("A user is already registered with this e-mail address."),
            )

        if attrs["password"] != attrs["password_confirmation"]:
            raise serializers.ValidationError(
                _("The two password fields didn't match.")
            )
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    """Change password Serializer"""

    user_id = serializers.CharField(required=True)
    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    class Meta:
        """Meta Class"""

        fields = ["current_password", "new_password", "user_id"]

    def validate(self, attrs: dict) -> dict:
        user = User.objects.get(id=attrs["user_id"])
        if (
            user.check_password(attrs["current_password"])
            and attrs["current_password"] != attrs["new_password"]
        ):
            return attrs

        msg = _("Unable to change password.")
        raise ValidationError(msg)

    def create(self, validated_data: dict):
        """Applies new password"""
        user = User.objects.get(id=validated_data["user_id"])
        user.password = make_password(validated_data["new_password"])
        user.save()
        return {}

    def update(self, instance, validated_data):
        """Not implmented"""
        return {}


# class EmailVerificationSerializer(serializers.Serializer):
#     token = serializers.CharField(max_length=555)

#     class Meta:
#         fields = ["token"]


class ForgotPasswordSerializer(serializers.Serializer):
    """Forgot password Serializer"""

    email = serializers.EmailField(min_length=2, required=True)

    class Meta:
        """Meta Class"""

        fields = ["email", "clinic_code"]

    def validate(self, attrs):
        if User.objects.filter(
            email=attrs["email"],
        ).exists():
            return super().validate(attrs)

        raise ValidationError("User not found")

    def create(self, validated_data):
        """
        Send email to change password
        Not implmented
        """
        return {}

    def update(self, instance, validated_data):
        """Not implmented"""
        return {}


class NewPasswordSerializer(serializers.Serializer):
    """Set new password Serializer"""

    password = serializers.CharField(min_length=6, max_length=68, write_only=True)
    token = serializers.CharField(min_length=1, write_only=True)
    uid = serializers.CharField(min_length=1, write_only=True)

    class Meta:
        """Meta Class"""

        fields = ["password", "token", "id"]

    def validate(self, attrs):
        try:
            uid = force_str(urlsafe_base64_decode(attrs["uid"]))
            user = User.objects.get(id=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist) as exc:
            raise ValidationError("Invalid") from exc

        if not default_token_generator.check_token(user, attrs["token"]):
            raise ValidationError("Invalid")

        return attrs

    def create(self, validated_data):
        """Set new password"""
        password = validated_data["password"]
        uid = force_str(urlsafe_base64_decode(validated_data["uid"]))
        user = User.objects.get(id=uid)
        user.set_password(password)
        user.save()

        return {"message": "Password changed successfully"}

    def update(self, instance, validated_data):
        """Not implmented"""
        return {}
