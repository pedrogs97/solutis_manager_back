"""Lending models"""
from django.db import models
from utils.base.models import BaseModel
from utils.images import OverwriteImage, upload_to


class Tag(BaseModel):
    """Represents the asset identification code"""

    number = models.CharField(max_length=50)
    code = models.CharField(max_length=255)
    image = models.ImageField(
        blank=True,
        null=True,
        storage=OverwriteImage(),
        upload_to=upload_to,
        max_length=255,
    )


class Asset(BaseModel):
    """Represents managed asset"""

    class AssetStatus(models.TextChoices):
        """Asset status"""

        RESERVED = "Reservado", "Reservado"
        AVAILABLE = "Disponível", "Disponível"
        MAINTENANCE = "Em manutenção", "Em manutenção"

    tag = models.OneToOneField(Tag, on_delete=models.DO_NOTHING, related_name="asset")
    name = models.CharField(max_length=150)
    description = models.CharField(max_length=255, default="")
    status = models.CharField(
        max_length=13, choices=AssetStatus.choices, default=AssetStatus.AVAILABLE
    )
    observation = models.CharField(max_length=150, default="")
    assurance = models.DateField(null=True)
    original_value = models.DecimalField(max_digits=12, decimal_places=2)
    depreciation = models.DecimalField(max_digits=5, decimal_places=2)
    image = models.ImageField(
        blank=True,
        null=True,
        storage=OverwriteImage(),
        upload_to=upload_to,
        max_length=255,
    )


class Document(BaseModel):
    """Represents the contract signed by the company and employee"""

    name = models.CharField(max_length=50)
    path = models.FileField()
    signed = models.DateField(null=True)


class Witness(BaseModel):
    """Represents the witness of the contract"""

    doc = models.ForeignKey(
        Document, on_delete=models.PROTECT, related_name="witnesses"
    )
    full_name = models.CharField(max_length=150)
    signed = models.DateField(null=True)


class EmployeeAssetDoc(BaseModel):
    """Represents relationship between signed document, asset and employee"""

    # employee = pega da TOTvs
    asset = models.ForeignKey(
        Asset, on_delete=models.PROTECT, related_name="employee_asset_docs"
    )
    doc = models.OneToOneField(
        Document,
        on_delete=models.PROTECT,
        related_name="employee_asset_doc",
        unique=True,
    )


class AssetVerification(BaseModel):
    """Represents the question asked in the check"""

    field = models.CharField(max_length=50)


class AssetVerificationAnswer(BaseModel):
    """Represents the answer to the question asked in the check"""

    asset_verification = models.ForeignKey(
        AssetVerification,
        on_delete=models.PROTECT,
        related_name="asset_verification_answers",
    )
    answer = models.CharField(max_length=150)


class AssetHistorical(BaseModel):
    """Represents the history of actions performed on the asset"""

    class AssetHistoricalAction(models.TextChoices):
        """Asset status"""

        LOCATION = "Locação", "Locação"
        MAINTENANCE = "Manutenção", "Manutenção"
        DISCARD = "Descarte", "Descarte"
        UPGRADE = "Melhorias", "Melhorias"

    employee_asset_doc = models.ForeignKey(
        EmployeeAssetDoc,
        on_delete=models.PROTECT,
        related_name="asset_historicals",
    )
    materail_verification_answer = models.ForeignKey(
        AssetVerificationAnswer,
        on_delete=models.PROTECT,
        related_name="asset_historicals",
    )
    action = models.CharField(max_length=13, choices=AssetHistoricalAction.choices)
    occurance = models.DateField(auto_now_add=True)
    observations = models.CharField(max_length=150, default="")
