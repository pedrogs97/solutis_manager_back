"""Verification service"""
import logging
from typing import List

from fastapi import status
from fastapi.exceptions import HTTPException
from sqlalchemy.orm import Session

from src.asset.models import AssetTypeModel
from src.auth.models import UserModel
from src.lending.models import LendingModel
from src.log.services import LogService
from src.verification.models import (
    VerificationAnswerModel,
    VerificationAnswerOptionModel,
    VerificationCategoryModel,
    VerificationModel,
    VerificationTypeModel,
)
from src.verification.schemas import (
    NewVerificationAnswerSchema,
    NewVerificationSchema,
    VerificationAnswerSerializerSchema,
    VerificationSerializerSchema,
)

logger = logging.getLogger(__name__)
service_log = LogService()


class VerificationService:
    """Verification service"""

    def __get_verification_or_404(
        self, verification_id: int, db_session: Session
    ) -> VerificationModel:
        """Get verification or 404"""
        verification = (
            db_session.query(VerificationModel)
            .filter(VerificationModel.id == verification_id)
            .first()
        )
        if not verification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "field": "verificationId",
                    "error": "Pergunta de Verificação não encontrada.",
                },
            )

        return verification

    def __get_asset_type_or_404(
        self, asset_type_id: int, db_session: Session
    ) -> AssetTypeModel:
        """Get asset type or 404"""
        asset_type = (
            db_session.query(AssetTypeModel)
            .filter(AssetTypeModel.id == asset_type_id)
            .first()
        )

        if not asset_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "field": "assetTypeId",
                    "error": "Tipo do Ativo não encontrado.",
                },
            )
        return asset_type

    def __get_verification_type_or_404(
        self, verification_type_id: int, db_session: Session
    ) -> VerificationTypeModel:
        """Get verification type or 404"""
        vertification_type = (
            db_session.query(VerificationTypeModel)
            .filter(VerificationTypeModel.id == verification_type_id)
            .first()
        )

        if not vertification_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "field": "verificationTypeId",
                    "error": "Tipo do Verificação não encontrado.",
                },
            )
        return vertification_type

    def __get_verification_category_or_create(
        self, verification_category: str, db_session: Session
    ) -> VerificationCategoryModel:
        """Get verification category or create"""
        vertification_category = (
            db_session.query(VerificationCategoryModel)
            .filter(VerificationCategoryModel.name == verification_category)
            .first()
        )

        if not vertification_category:
            new_category = VerificationCategoryModel(name=verification_category)
            db_session.add(new_category)
            db_session.commit()
            db_session.flush()

        return vertification_category

    def __get_lending_or_404(
        self, lending_id: int, db_session: Session
    ) -> LendingModel:
        """Get lending or 404"""
        lending = (
            db_session.query(LendingModel).filter(LendingModel.id == lending_id).first()
        )
        if not lending:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"field": "lendingId", "error": "Comodato não encontrado"},
            )

        return lending

    def serialize_verification(
        self, verification: VerificationModel
    ) -> VerificationSerializerSchema:
        """Serialize verification"""
        options = [option.name for option in verification.options]
        return VerificationSerializerSchema(
            id=verification.id,
            question=verification.question,
            step=verification.step,
            asset_type=verification.asset_type.name,
            category=verification.category.name,
            options=options,
        )

    def serialize_answer_verification(
        self, answer_verification: VerificationAnswerModel
    ) -> VerificationAnswerSerializerSchema:
        """Serialize answer verification"""
        return VerificationAnswerSerializerSchema(
            id=answer_verification.id,
            type=answer_verification.type.name,
            answer=answer_verification.answer,
            lending_id=answer_verification.lending.id,
            verification=self.serialize_verification(answer_verification.verification),
        )

    def __create_options(
        self, data: NewVerificationSchema, db_session: Session
    ) -> List[VerificationAnswerOptionModel]:
        """Creates new options"""
        new_options = []

        for new_option in data.options:
            new_options.append(VerificationAnswerOptionModel(name=new_option))

        db_session.add_all(new_options)
        db_session.commit()
        db_session.flush()

        return new_options

    def create_verification(
        self,
        data: NewVerificationSchema,
        db_session: Session,
        authenticated_user: UserModel,
    ) -> VerificationSerializerSchema:
        """Creates new asset verification"""

        asset_type = self.__get_asset_type_or_404(data.asset_type_id, db_session)

        category = self.__get_verification_category_or_create(data.category, db_session)

        new_options = self.__create_options(data, db_session)

        new_verification = VerificationModel(
            question=data.question,
            step=data.step,
        )

        new_verification.category = category
        new_verification.options = new_options
        new_verification.asset_type = asset_type

        db_session.add(new_verification)
        db_session.commit()
        db_session.flush()

        service_log.set_log(
            "lending",
            "verification",
            f"Adição de nova pergunta de verificação para {str(asset_type)}",
            new_verification.id,
            authenticated_user,
            db_session,
        )
        logger.info("New verification. %s", str(new_verification))

        return self.serialize_verification(new_verification)

    def get_asset_verifications(
        self, asset_type_id: int, db_session: Session
    ) -> List[VerificationSerializerSchema]:
        """Returns asset type verifications"""
        verifications = (
            db_session.query(VerificationModel)
            .filter(VerificationModel.asset_type_id == asset_type_id)
            .all()
        )

        return [
            VerificationSerializerSchema(
                id=verification.id,
                question=verification.question,
                asset_type=verification.asset_type.name,
                step=verification.step,
                category=verification.category.name,
                options=[option.name for option in verification.options],
            )
            for verification in verifications
        ]

    def create_answer_verification(
        self,
        data: NewVerificationAnswerSchema,
        db_session: Session,
        authenticated_user: UserModel,
    ) -> VerificationAnswerSerializerSchema:
        """Creates new answer verification"""

        verification = self.__get_verification_or_404(data.verification_id, db_session)

        verification_type = self.__get_verification_type_or_404(
            data.type_id, db_session
        )

        lending = self.__get_lending_or_404(data.lending_id, db_session)

        new_answer_verification = VerificationAnswerModel(
            lending=lending,
            answer=data.answer,
            observations=data.observations,
        )

        new_answer_verification.type = (verification_type,)
        new_answer_verification.verification = (verification,)

        db_session.add(new_answer_verification)
        db_session.commit()
        db_session.flush()

        service_log.set_log(
            "lending",
            "verification",
            "Adição de nova resposta verificação",
            new_answer_verification.id,
            authenticated_user,
            db_session,
        )
        logger.info("New answer verification. %s", str(new_answer_verification))

        return self.serialize_answer_verification(new_answer_verification)
