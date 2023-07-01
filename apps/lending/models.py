"""Lending models"""
from django.db import models
from utils.base.models import BaseModel
from utils.images import OverwriteImage, upload_to

# Pontos para solicitar:
# O modelo da etiqueta do equipamento
# O modelo do contrato - informando os campos que não são fixos
# O modelo de verificação dos equipamentos
# Há um modelo desejado de registro de ações do sistema (ex.: ao incluir um equipamento, deve-se registrar o usuário que realizou a ação, data e hora)


class Tag(BaseModel):
    """Represents the equipment identification code"""

    number = models.CharField(max_length=50)
    code = models.CharField(max_length=255)
    image = models.ImageField(
        blank=True,
        null=True,
        storage=OverwriteImage(),
        upload_to=upload_to,
        max_length=255,
    )


class Material(BaseModel):
    """Represents managed equipment"""

    class MaterialStatus(models.TextChoices):
        """Equipment status"""

        RESERVED = "Reservado", "Reservado"
        AVAILABLE = "Disponível", "Disponível"
        MAINTENANCE = "Em manutenção", "Em manutenção"

    tag = models.OneToOneField(
        Tag, on_delete=models.DO_NOTHING, related_name="material"
    )
    name = models.CharField(max_length=150)
    description = models.CharField(max_length=255, default="")
    status = models.CharField(
        max_length=13, choices=MaterialStatus.choices, default=MaterialStatus.AVAILABLE
    )
    observation = models.CharField(max_length=150, default="")
    assurance = models.DateField(null=True)
    original_value = models.DecimalField(max_digits=12, decimal_places=2)
    depreciation = models.DecimalField(max_digits=5, decimal_places=2)


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


class EmployeeMaterialDoc(BaseModel):
    """Represents relationship between signed document, equipment and employee"""

    # employee = pega da TOTvs
    material = models.ForeignKey(
        Material, on_delete=models.PROTECT, related_name="employee_material_docs"
    )
    doc = models.OneToOneField(
        Document,
        on_delete=models.PROTECT,
        related_name="employee_material_doc",
        unique=True,
    )


class MaterialVerification(BaseModel):
    """Represents the question asked in the check"""

    field = models.CharField(max_length=50)


class MaterialVerificationAnswer(BaseModel):
    """Represents the answer to the question asked in the check"""

    material_verification = models.ForeignKey(
        MaterialVerification,
        on_delete=models.PROTECT,
        related_name="material_verification_answers",
    )
    answer = models.CharField(max_length=150)


class MaterialHistorical(BaseModel):
    """Represents the history of actions performed on the equipment"""

    class MaterialHistoricalAction(models.TextChoices):
        """Equipment status"""

        LOCATION = "Locação", "Locação"
        MAINTENANCE = "Manutenção", "Manutenção"
        DISCARD = "Descarte", "Descarte"
        UPGRADE = "Melhorias", "Melhorias"

    employee_material_doc = models.ForeignKey(
        EmployeeMaterialDoc,
        on_delete=models.PROTECT,
        related_name="material_historicals",
    )
    materail_verification_answer = models.ForeignKey(
        MaterialVerificationAnswer,
        on_delete=models.PROTECT,
        related_name="material_historicals",
    )
    action = models.CharField(max_length=13, choices=MaterialHistoricalAction.choices)
    occurance = models.DateField(auto_now_add=True)
    observations = models.CharField(max_length=150, default="")
