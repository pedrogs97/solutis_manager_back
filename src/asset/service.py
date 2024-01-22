"""Asset service"""
import logging
from typing import List

from fastapi import status
from fastapi.exceptions import HTTPException
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.orm import Session

from src.asset.filters import (
    AssetClothingSizeFilter,
    AssetFilter,
    AssetStatusFilter,
    AssetTypeFilter,
)
from src.asset.models import (
    AssetClothingSizeModel,
    AssetModel,
    AssetStatusModel,
    AssetTypeModel,
)
from src.asset.schemas import (
    AssetClothingSizeSerializer,
    AssetSerializerSchema,
    AssetStatusSerializerSchema,
    AssetTypeSerializerSchema,
    InactivateAssetSchema,
    NewAssetSchema,
    UpdateAssetSchema,
)
from src.auth.models import UserModel
from src.log.services import LogService

logger = logging.getLogger(__name__)
service_log = LogService()


class AssetService:
    """Asset services"""

    def __get_asset_or_404(self, asset_id: int, db_session: Session) -> AssetModel:
        """Get asset or 404"""
        asset = db_session.query(AssetModel).filter(AssetModel.id == asset_id).first()
        if not asset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"field": "assetId", "error": "Ativo não encontrado"},
            )

        return asset

    def __validate_nested(self, data: NewAssetSchema, db_session: Session) -> tuple:
        """Validates clothing size, type and status values"""
        errors = []
        asset_type = None
        clothing_size = None
        asset_status = None
        if data.type_id:
            asset_type = (
                db_session.query(AssetTypeModel)
                .filter(AssetTypeModel.id == data.type_id)
                .first()
            )
            if not asset_type:
                errors.append(
                    {
                        "field": "assetType",
                        "error": f"Tipo de Ativo não existe. {asset_type}",
                    }
                )

        if data.clothing_size_id:
            clothing_size = (
                db_session.query(AssetClothingSizeModel)
                .filter(AssetClothingSizeModel.id == data.clothing_size_id)
                .first()
            )
            if not clothing_size:
                errors.append(
                    {
                        "field": "clothingSize",
                        "error": f"Tamanho de roupa não existe. {clothing_size}",
                    }
                )

        if data.status_id:
            asset_status = (
                db_session.query(AssetStatusModel)
                .filter(AssetStatusModel.id == data.status_id)
                .first()
            )
            if not asset_status:
                errors.append(
                    {
                        "field": "assetStatus",
                        "error": f"Situação de Ativo não existe. {asset_status}",
                    }
                )

        if len(errors) > 0:
            raise HTTPException(
                detail=errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        return (
            asset_type,
            clothing_size,
            asset_status,
        )

    def serialize_asset(self, asset: AssetModel) -> AssetSerializerSchema:
        """Serialize asset"""
        return AssetSerializerSchema(
            id=asset.id,
            type=AssetTypeSerializerSchema(**asset.type.__dict__)
            if asset.type
            else None,
            clothing_size=AssetClothingSizeSerializer(**asset.clothing_size.__dict__)
            if asset.clothing_size
            else None,
            status=AssetStatusSerializerSchema(**asset.status.__dict__)
            if asset.status
            else None,
            register_number=asset.register_number,
            description=asset.description,
            supplier=asset.supplier,
            assurance_date=asset.assurance_date,
            observations=asset.observations,
            discard_reason=asset.discard_reason,
            pattern=asset.pattern,
            operational_system=asset.operational_system,
            serial_number=asset.serial_number,
            imei=asset.imei,
            acquisition_date=asset.acquisition_date.isoformat(),
            value=asset.value,
            ms_office=asset.ms_office,
            line_number=asset.line_number,
            operator=asset.operator,
            model=asset.model,
            accessories=asset.accessories,
            configuration=asset.configuration,
            quantity=asset.quantity,
            unit=asset.unit,
            by_agile=asset.by_agile,
            invoice_asset_id=asset.invoice.asset_id if asset.invoice else None,
        )

    def serialize_asset_type(
        self, asset_type: AssetTypeModel
    ) -> AssetTypeSerializerSchema:
        """Serialize asset type"""

        return AssetTypeSerializerSchema(**asset_type.__dict__)

    def serialize_asset_status(
        self, asset_status: AssetStatusModel
    ) -> AssetStatusSerializerSchema:
        """Serialize asset status"""

        return AssetStatusSerializerSchema(**asset_status.__dict__)

    def serialize_asset_clothing_size(
        self, asset_clothing_size: AssetClothingSizeModel
    ) -> AssetClothingSizeSerializer:
        """Serialize asset clothing size"""

        return AssetClothingSizeSerializer(**asset_clothing_size.__dict__)

    def create_asset(
        self, data: NewAssetSchema, db_session: Session, authenticated_user: UserModel
    ) -> AssetSerializerSchema:
        """Creates new asset"""
        errors = []
        if (
            data.code
            and db_session.query(AssetModel)
            .filter(AssetModel.code == data.code)
            .first()
        ):
            errors.append({"field": "code", "error": "Este Código já existe."})
        if (
            db_session.query(AssetModel)
            .filter(AssetModel.register_number == data.register_number)
            .first()
        ):
            errors.append(
                {
                    "field": "registerNumber",
                    "error": "Este N° de Patrimônio já existe",
                }
            )

        if len(errors) > 0:
            raise HTTPException(
                detail=errors,
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        (
            asset_type,
            clothing_size,
            asset_status,
        ) = self.__validate_nested(data, db_session)

        new_asset = AssetModel(
            code=data.code,
            register_number=data.register_number,
            description=data.description,
            supplier=data.supplier,
            assurance_date=data.assurance_date,
            observations=data.observations,
            discard_reason=data.discard_reason,
            pattern=data.pattern,
            operational_system=data.operational_system,
            serial_number=data.serial_number,
            imei=data.imei,
            acquisition_date=data.acquisition_date,
            value=data.value,
            ms_office=data.ms_office,
            line_number=data.line_number,
            operator=data.operator,
            model=data.model,
            accessories=data.accessories,
            configuration=data.configuration,
            quantity=data.quantity,
            unit=data.unit,
            active=True,
            by_agile=True,
        )

        new_asset.type = asset_type
        new_asset.clothing_size = clothing_size
        new_asset.status = asset_status

        db_session.add(new_asset)
        db_session.commit()
        db_session.flush()

        service_log.set_log(
            "lending",
            "asset",
            "Criação de Ativo",
            new_asset.id,
            authenticated_user,
            db_session,
        )
        logger.info("New Asset. %s", str(new_asset))

        return self.serialize_asset(new_asset)

    def update_asset(
        self,
        asset_id: int,
        data: UpdateAssetSchema,
        db_session: Session,
        authenticated_user: UserModel,
    ) -> AssetSerializerSchema:
        """Uptades an asset"""
        asset = self.__get_asset_or_404(asset_id, db_session)

        if data.observations:
            asset.observations = data.observations

        db_session.add(asset)
        db_session.commit()
        db_session.flush()

        service_log.set_log(
            "lending",
            "asset",
            "Edição de Ativo",
            asset.id,
            authenticated_user,
            db_session,
        )
        logger.info("Updated Asset. %s", str(asset))
        return self.serialize_asset(asset)

    def inactivate_asset(
        self,
        asset_id: int,
        data: InactivateAssetSchema,
        db_session: Session,
        authenticated_user: UserModel,
    ) -> AssetSerializerSchema:
        """Uptades an asset"""
        asset = self.__get_asset_or_404(asset_id, db_session)

        asset.active = data.active

        db_session.add(asset)
        db_session.commit()
        db_session.flush()

        service_log.set_log(
            "lending",
            "asset",
            "Inativação de Ativo",
            asset.id,
            authenticated_user,
            db_session,
        )
        logger.info("Inactivate Asset. %s", str(asset))
        return self.serialize_asset(asset)

    def get_asset(self, asset_id: int, db_session: Session) -> AssetSerializerSchema:
        """Get an asset"""
        asset = self.__get_asset_or_404(asset_id, db_session)
        return self.serialize_asset(asset)

    def get_assets(
        self,
        db_session: Session,
        asset_filters: AssetFilter,
        fields: str = "",
        page: int = 1,
        size: int = 50,
    ) -> Page[AssetSerializerSchema]:
        """Get assets list"""

        asset_list = asset_filters.filter(db_session.query(AssetModel))

        params = Params(page=page, size=size)
        if fields == "":
            paginated = paginate(
                asset_list,
                params=params,
                transformer=lambda asset_list: [
                    self.serialize_asset(asset).model_dump(by_alias=True)
                    for asset in asset_list
                ],
            )
            return paginated

        list_fields = fields.split(",")
        paginated = paginate(
            asset_list,
            params=params,
            transformer=lambda asset_list: [
                self.serialize_asset(asset).model_dump(
                    include={*list_fields}, by_alias=True
                )
                for asset in asset_list
            ],
        )
        return paginated

    def get_asset_types(
        self,
        db_session: Session,
        filter_asset_type: AssetTypeFilter,
        fields: str = "",
    ) -> List[AssetTypeSerializerSchema]:
        """Get asset types list"""

        asset_type_list = filter_asset_type.filter(db_session.query(AssetTypeModel))

        if fields == "":
            return [
                self.serialize_asset_type(asset_type).model_dump(by_alias=True)
                for asset_type in asset_type_list
            ]

        list_fields = fields.split(",")
        return [
            self.serialize_asset_type(asset_type).model_dump(
                include={*list_fields}, by_alias=True
            )
            for asset_type in asset_type_list
        ]

    def get_asset_status(
        self,
        db_session: Session,
        filter_asset_status: AssetStatusFilter,
        fields: str = "",
    ) -> List[AssetTypeSerializerSchema]:
        """Get asset status list"""

        asset_status = filter_asset_status.filter(db_session.query(AssetStatusModel))

        if fields == "":
            return [
                self.serialize_asset_status(asset_status).model_dump(by_alias=True)
                for asset_status in asset_status
            ]

        list_fields = fields.split(",")
        return [
            self.serialize_asset_status(asset_status).model_dump(
                include={*list_fields}, by_alias=True
            )
            for asset_status in asset_status
        ]

    def get_asset_clothing_size(
        self,
        db_session: Session,
        filter_asset_clothing_size: AssetClothingSizeFilter,
        fields: str = "",
    ) -> List[AssetTypeSerializerSchema]:
        """Get asset status list"""

        asset_clothing_size = filter_asset_clothing_size.filter(
            db_session.query(AssetClothingSizeModel)
        )

        if fields == "":
            return [
                self.serialize_asset_clothing_size(asset_clothing_size).model_dump(
                    by_alias=True
                )
                for asset_clothing_size in asset_clothing_size
            ]

        list_fields = fields.split(",")
        return [
            self.serialize_asset_clothing_size(asset_status).model_dump(
                include={*list_fields}, by_alias=True
            )
            for asset_status in asset_clothing_size
        ]
