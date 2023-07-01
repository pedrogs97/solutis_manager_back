"""Views for lending module"""
from rest_framework.viewsets import ModelViewSet
from knox.auth import TokenAuthentication
from apps.lending.models import (
    Material,
    Tag,
    Document,
    MaterialVerification,
    MaterialVerificationAnswer,
    MaterialHistorical,
)
from apps.lending.serializers import (
    MaterialSerializer,
    TagSerializer,
    DocumentSerializer,
    MaterialVerificationSerializer,
    MaterialVerificationAnswerSerializer,
    MaterialHistoricalSerializer,
)
from utils.base.permissions import (
    CustomDjangoModelPermissions,
)


class MaterialVerificationViewset(ModelViewSet):
    """Question views."""

    authentication_classes = (TokenAuthentication,)
    permission_classes = (CustomDjangoModelPermissions,)
    serializer_class = MaterialVerificationSerializer
    queryset = MaterialVerification.objects.all()


class MaterialVerificationAnswerViewset(ModelViewSet):
    """Answer views."""

    authentication_classes = (TokenAuthentication,)
    permission_classes = (CustomDjangoModelPermissions,)
    serializer_class = MaterialVerificationAnswerSerializer
    queryset = MaterialVerificationAnswer.objects.all()


class MaterialHistoricViewset(ModelViewSet):
    """Material historic views."""

    authentication_classes = (TokenAuthentication,)
    permission_classes = (CustomDjangoModelPermissions,)
    serializer_class = MaterialHistoricalSerializer
    queryset = MaterialHistorical.objects.all()


class MaterialViewset(ModelViewSet):
    """Materials views."""

    authentication_classes = (TokenAuthentication,)
    permission_classes = (CustomDjangoModelPermissions,)
    serializer_class = MaterialSerializer
    queryset = Material.objects.all()


class TagViewset(ModelViewSet):
    """Tags views."""

    authentication_classes = (TokenAuthentication,)
    permission_classes = (CustomDjangoModelPermissions,)
    serializer_class = TagSerializer
    queryset = Tag.objects.all()


class DocumentViewset(ModelViewSet):
    """Documents views."""

    authentication_classes = (TokenAuthentication,)
    permission_classes = (CustomDjangoModelPermissions,)
    serializer_class = DocumentSerializer
    queryset = Document.objects.all()
