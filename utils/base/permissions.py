"""Project base permissions"""
from rest_framework import exceptions, permissions


class CustomDjangoModelPermissions(permissions.BasePermission):
    """
    The request is authenticated using `django.contrib.auth` permissions.
    See: https://docs.djangoproject.com/en/dev/topics/auth/#permissions
    It ensures that the user is authenticated, and has the appropriate
    `add`/`change`/`delete` permissions on the model.
    This permission can only be applied against view classes that
    provide a `.queryset` attribute.
    """

    # Map methods into required permission codes.
    perms_map = {
        "GET": ["view_%(model_name)s"],
        "OPTIONS": [],
        "HEAD": [],
        "POST": ["add_%(model_name)s"],
        "PUT": ["change_%(model_name)s"],
        "PATCH": ["change_%(model_name)s"],
        "DELETE": ["delete_%(model_name)s"],
    }

    authenticated_users_only = True

    def get_required_permissions(self, method, model_cls):
        """
        Given a model and an HTTP method, return the list of permission
        codes that the user is required to have.
        """
        kwargs = {
            "model_name": model_cls._meta.model_name,
        }

        if method not in self.perms_map:
            raise exceptions.MethodNotAllowed(method)

        return [perm % kwargs for perm in self.perms_map[method]]

    def _queryset(self, view):
        assert (
            hasattr(view, "get_queryset") or getattr(view, "queryset", None) is not None
        ), (
            f"Cannot apply {self.__class__.__name__} on a view that does not set "
            "`.queryset` or have a `.get_queryset()` method."
        )

        if hasattr(view, "get_queryset"):
            queryset = view.get_queryset()
            assert (
                queryset is not None
            ), f"{view.__class__.__name__}.get_queryset() returned None"
            return queryset
        return view.queryset

    def has_permission(self, request, view):
        # Workaround to ensure DjangoModelPermissions are not applied
        # to the root view when using DefaultRouter.
        if getattr(view, "_ignore_model_permissions", False):
            return True

        if not request.user or (
            not request.user.is_authenticated and self.authenticated_users_only
        ):
            return False

        queryset = self._queryset(view)
        perms = self.get_required_permissions(request.method, queryset.model)
        return request.user.has_perms(perms)


class IsOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Check if is the owner of the snippet.
        return obj == request.user
