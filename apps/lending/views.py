"""Views for lending module"""
from rest_framework.viewsets import ModelViewSet
from knox.auth import TokenAuthentication
from apps.lending.models import (
    Asset,
    Tag,
    Document,
    AssetVerification,
    AssetVerificationAnswer,
    AssetHistorical,
)
from apps.lending.serializers import (
    AssetSerializer,
    TagSerializer,
    DocumentSerializer,
    AssetVerificationSerializer,
    AssetVerificationAnswerSerializer,
    AssetHistoricalSerializer,
)
from utils.base.permissions import (
    CustomDjangoModelPermissions,
)


class AssetVerificationViewset(ModelViewSet):
    """Question views."""

    authentication_classes = (TokenAuthentication,)
    permission_classes = (CustomDjangoModelPermissions,)
    serializer_class = AssetVerificationSerializer
    queryset = AssetVerification.objects.all()


class AssetVerificationAnswerViewset(ModelViewSet):
    """Answer views."""

    authentication_classes = (TokenAuthentication,)
    permission_classes = (CustomDjangoModelPermissions,)
    serializer_class = AssetVerificationAnswerSerializer
    queryset = AssetVerificationAnswer.objects.all()


class AssetHistoricViewset(ModelViewSet):
    """Asset historic views."""

    authentication_classes = (TokenAuthentication,)
    permission_classes = (CustomDjangoModelPermissions,)
    serializer_class = AssetHistoricalSerializer
    queryset = AssetHistorical.objects.all()


class AssetViewset(ModelViewSet):
    """Assets views."""

    authentication_classes = (TokenAuthentication,)
    permission_classes = (CustomDjangoModelPermissions,)
    serializer_class = AssetSerializer
    queryset = Asset.objects.all()


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
