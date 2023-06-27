"""Lending models"""
from django.db import models
from utils.base.models import BaseModel
from utils.images import OverwriteImage, upload_to

# Pontos para solicitar:
# O modelo da etiqueta do equipamento
# O modelo do contrato - informando os campos que não são fixos
# O modelo de verificação dos equipamentos


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

    tag = models.OneToOneField(Tag, on_delete=models.DO_NOTHING)
    name = models.CharField(max_length=150)
    description = models.CharField(max_length=255, default="")
    status = models.CharField(
        max_length=13, choices=MaterialStatus.choices, default=MaterialStatus.AVAILABLE
    )
    observation = models.CharField(max_length=150, default="")
    assurance = models.DateField(null=True)


class Document(BaseModel):
    """Represents the contract signed by the company and employee"""

    name = models.CharField(max_length=50)
    path = models.FileField()
    signed = models.DateField(null=True)


class Witness(BaseModel):
    """Represents the witness of the contract"""

    doc = models.ForeignKey(Document, on_delete=models.PROTECT)
    full_name = models.CharField(max_length=150)
    signed = models.DateField(null=True)


class EmployeeMaterialDoc(BaseModel):
    """Represents relationship between signed document, equipment and employee"""

    # employee = pega da TOTvs
    material = models.ForeignKey(Material, on_delete=models.PROTECT)
    doc = models.ForeignKey(Document, on_delete=models.PROTECT)


class MaterialVerification(BaseModel):
    """Represents the question asked in the check"""

    field = models.CharField(max_length=50)


class MaterialVerificationAnswer(BaseModel):
    """Represents the answer to the question asked in the check"""

    material_verification = models.ForeignKey(
        MaterialVerification, on_delete=models.PROTECT
    )
    answer = models.CharField(max_length=150)


class MaterialHistory(BaseModel):
    """Represents the history of actions performed on the equipment"""

    class MaterialHistoryAction(models.TextChoices):
        """Equipment status"""

        LOCATION = "Locação", "Locação"
        MAINTENANCE = "Manutenção", "Manutenção"
        DISCARD = "Descarte", "Descarte"
        UPGRADE = "Melhorias", "Melhorias"

    material = models.ForeignKey(Material, on_delete=models.PROTECT)
    employee_material_doc = models.ForeignKey(
        EmployeeMaterialDoc, on_delete=models.PROTECT
    )
    materail_verification_answer = models.ForeignKey(
        MaterialVerificationAnswer, on_delete=models.PROTECT
    )
    action = models.CharField(max_length=13, choices=MaterialHistoryAction.choices)
    occurance = models.DateField(auto_now_add=True)
    observations = models.CharField(max_length=150, default="")
