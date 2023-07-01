"""Lending serializers"""
from rest_framework.serializers import (
    ModelSerializer,
    SlugRelatedField,
    SerializerMethodField,
)
from apps.lending.models import (
    Tag,
    Material,
    Document,
    Witness,
    MaterialVerification,
    MaterialVerificationAnswer,
    MaterialHistorical,
)


class TagSerializer(ModelSerializer):
    """Model serializer for Tags"""

    class Meta:
        """Class Meta"""

        model = Tag
        exclude = ["created_at", "updated_at"]


class MaterialSerializer(ModelSerializer):
    """Model serializer for Materials"""

    tag = SlugRelatedField(queryset=Tag.objects.all(), slug_field="code")

    class Meta:
        """Class Meta"""

        model = Material
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


class MaterialVerificationSerializer(ModelSerializer):
    """Model serializer for Questions asked in the check"""

    class Meta:
        """Class Meta"""

        model = MaterialVerification
        exclude = ["created_at", "updated_at"]


class MaterialVerificationAnswerSerializer(ModelSerializer):
    """Model serializer for Questions asked in the check"""

    question = SlugRelatedField(
        queryset=MaterialVerification.objects.all(), slug_field="field"
    )

    class Meta:
        """Class Meta"""

        model = MaterialVerificationAnswer
        exclude = ["material_verification", "created_at", "updated_at"]


class MaterialHistoricalSerializer(ModelSerializer):
    """Model serializer for History of action performed on the equipment"""

    class Meta:
        """Class Meta"""

        model = MaterialHistorical
        exclude = ["created_at", "updated_at"]
