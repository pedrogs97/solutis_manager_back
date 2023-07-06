"""Lending serializers"""
from rest_framework.serializers import (
    ModelSerializer,
    SlugRelatedField,
    SerializerMethodField,
)
from apps.lending.models import (
    Tag,
    Asset,
    Document,
    Witness,
    AssetVerification,
    AssetVerificationAnswer,
    AssetHistorical,
)


class TagSerializer(ModelSerializer):
    """Model serializer for Tags"""

    class Meta:
        """Class Meta"""

        model = Tag
        exclude = ["created_at", "updated_at"]


class AssetSerializer(ModelSerializer):
    """Model serializer for Assets"""

    tag = SlugRelatedField(queryset=Tag.objects.all(), slug_field="code")

    class Meta:
        """Class Meta"""

        model = Asset
        exclude = ["created_at", "updated_at"]


class WitnessSerializer(ModelSerializer):
    """Model serializer for Witnesses"""

    class Meta:
        """Class Meta"""

        model = Witness
        exclude = ["created_at", "updated_at"]


class DocumentSerializer(ModelSerializer):
    """Model serialzier for Documents"""

    witnesses = SerializerMethodField()

    class Meta:
        """Class Meta"""

        model = Document
        exclude = ["created_at", "updated_at"]

    def get_witnesses(self, obj: Document) -> dict:
        """Get all document witnesses"""
        return WitnessSerializer(obj.witnesses.all(), many=True).data


class AssetVerificationSerializer(ModelSerializer):
    """Model serializer for Questions asked in the check"""

    class Meta:
        """Class Meta"""

        model = AssetVerification
        exclude = ["created_at", "updated_at"]


class AssetVerificationAnswerSerializer(ModelSerializer):
    """Model serializer for Questions asked in the check"""

    question = SlugRelatedField(
        queryset=AssetVerification.objects.all(), slug_field="field"
    )

    class Meta:
        """Class Meta"""

        model = AssetVerificationAnswer
        exclude = ["asset_verification", "created_at", "updated_at"]


class AssetHistoricalSerializer(ModelSerializer):
    """Model serializer for History of action performed on the equipment"""

    class Meta:
        """Class Meta"""

        model = AssetHistorical
        exclude = ["created_at", "updated_at"]
