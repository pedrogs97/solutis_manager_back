"""Lenging service"""
from typing import List
import logging
from fastapi import status
from fastapi.exceptions import HTTPException
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.lending.models import (
    AssetModel,
    AssetClothingSizeModel,
    AssetStatusModel,
    AssetTypeModel,
)
from app.lending.schemas import (
    AssetTotvsSchema,
    NewAssetSchema,
    AssetSerializer,
    AssetTypeSerializer,
    AssetClothingSizeSerializer,
    AssetStatusSerializer,
    AssetTypeTotvsSchema,
    UpdateAssetSchema,
)

logger = logging.getLogger(__name__)


class AssetService:
    """Asset services"""

    def __get_asset_or_404(self, asset_id: int, db_session: Session) -> AssetModel:
        """Get asset or 404"""
        asset = db_session.query(AssetModel).filter(AssetModel.id == asset_id).first()
        if not asset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Ativo não encontrado"
            )

        return asset

    def __validate_nested(self, data: NewAssetSchema, db_session: Session) -> tuple:
        """Validates clothing size, type and status values"""
        if data.type:
            asset_type = (
                db_session.query(AssetTypeModel)
                .filter(AssetTypeModel.name == data.type)
                .first()
            )
            if not asset_type:
                raise HTTPException(
                    detail=f"Tipo de Ativo não existe. {asset_type}",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

        if data.clothing_size:
            clothing_size = (
                db_session.query(AssetClothingSizeModel)
                .filter(AssetClothingSizeModel.name == data.clothing_size)
                .first()
            )
            if not clothing_size:
                raise HTTPException(
                    detail=f"Tamanho de roupa não existe. {clothing_size}",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

        if data.status:
            asset_status = (
                db_session.query(AssetStatusModel)
                .filter(AssetStatusModel.name == data.status)
                .first()
            )
            if not asset_status:
                raise HTTPException(
                    detail=f"Situação de Ativo não existe. {asset_status}",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )

        return (
            asset_type,
            clothing_size,
            asset_status,
        )

    def serialize_asset(self, asset: AssetModel) -> AssetSerializer:
        """Serialize asset"""
        return AssetSerializer(
            id=asset.id,
            type=AssetTypeSerializer(**asset.type.__dict__),
            clothing_size=AssetClothingSizeSerializer(**asset.clothing_size.__dict__),
            status=AssetStatusSerializer(**asset.status),
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
            acquisition_date=asset.acquisition_date,
            value=asset.value,
            ms_office=asset.ms_office,
            line_number=asset.line_number,
            operator=asset.operator,
            model=asset.model,
            accessories=asset.accessories,
            configuration=asset.configuration,
            quantity=asset.quantity,
            unit=asset.unit,
        )

    def create_asset(
        self, data: NewAssetSchema, db_session: Session
    ) -> AssetSerializer:
        """Creates new asset"""
        if (
            data.code
            and db_session.query(AssetModel)
            .filter(AssetModel.code == data.code)
            .first()
        ):
            raise HTTPException(
                detail="Este Código já existe.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        if (
            db_session.query(AssetModel)
            .filter(AssetModel.register_number == data.register_number)
            .first()
        ):
            raise HTTPException(
                detail="Este N° de Patrimônio já existe",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        (
            asset_type,
            clothing_size,
            asset_status,
        ) = self.__validate_nested(data, db_session)

        new_emplyoee = AssetModel(
            type=asset_type,
            clothing_size=clothing_size,
            status=asset_status,
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
        )
        db_session.add(new_emplyoee)
        db_session.commit()
        return self.serialize_asset(new_emplyoee)

    def update_asset(
        self, asset_id: int, data: UpdateAssetSchema, db_session: Session
    ) -> AssetSerializer:
        """Uptades an asset"""
        asset = self.__get_asset_or_404(asset_id, db_session)

        (
            asset_type,
            clothing_size,
            asset_status,
        ) = self.__validate_nested(data, db_session)
        if data.type:
            asset.type = asset_type
        if data.clothing_size:
            asset.clothing_size = clothing_size
        if data.status:
            asset.status = asset_status
        if data.code:
            asset.code = data.code
        if data.register_number:
            asset.register_number = data.register_number
        if data.description:
            asset.description = data.description
        if data.supplier:
            asset.supplier = data.supplier
        if data.assurance_date:
            asset.assurance_date = data.assurance_date
        if data.observations:
            asset.observations = data.observations
        if data.discard_reason:
            asset.discard_reason = data.discard_reason
        if data.pattern:
            asset.pattern = data.pattern
        if data.operational_system:
            asset.operational_system = data.operational_system
        if data.serial_number:
            asset.serial_number = data.serial_number
        if data.imei:
            asset.imei = data.imei
        if data.value:
            asset.value = data.value
        if data.ms_office:
            asset.ms_office = data.ms_office
        if data.line_number:
            asset.line_number = data.line_number
        if data.operator:
            asset.operator = data.operator
        if data.model:
            asset.model = data.model
        if data.accessories:
            asset.accessories = data.accessories
        if data.configuration:
            asset.configuration = data.configuration
        if data.quantity:
            asset.quantity = data.quantity
        if data.unit:
            asset.unit = data.unit
        if data.active:
            asset.active = data.active

        db_session.add(asset)
        db_session.commit()
        return self.serialize_asset(asset)

    def get_asset(self, asset_id: int, db_session: Session) -> AssetSerializer:
        """Get an asset"""
        asset = self.__get_asset_or_404(asset_id, db_session)
        return self.serialize_asset(asset)

    def get_assets(
        self,
        db_session: Session,
        search: str = "",
        filter_asset: str = None,
        active: bool = True,
        page: int = 1,
        size: int = 50,
    ) -> Page[AssetSerializer]:
        """Get assets list"""

        asset_list = db_session.query(AssetModel).filter(
            or_(
                AssetModel.code.ilike(f"%{search}"),
                AssetModel.register_number.ilike(f"%{search}%"),
                AssetModel.description.ilike(f"%{search}"),
                AssetModel.supplier.ilike(f"%{search}"),
                AssetModel.pattern.ilike(f"%{search}"),
                AssetModel.operational_system.ilike(f"%{search}"),
                AssetModel.serial_number.ilike(f"%{search}"),
                AssetModel.imei.ilike(f"%{search}"),
                AssetModel.line_number.ilike(f"%{search}"),
                AssetModel.operator.ilike(f"%{search}"),
                AssetModel.model.ilike(f"%{search}"),
            )
        )

        if filter_asset:
            asset_list = asset_list.join(
                AssetModel.type,
            ).filter(
                or_(
                    AssetTypeModel.name == filter_asset,
                )
            )

            asset_list = asset_list.join(
                AssetModel.status,
            ).filter(
                or_(
                    AssetStatusModel.name == filter_asset,
                )
            )

            asset_list = asset_list.join(
                AssetModel.clothing_size,
            ).filter(
                or_(
                    AssetClothingSizeModel.name == filter_asset,
                )
            )

        asset_list = asset_list.filter(AssetModel.active == active)

        params = Params(page=page, size=size)
        paginated = paginate(
            asset_list,
            params=params,
            transformer=lambda asset_list: [
                self.serialize_asset(asset) for asset in asset_list
            ],
        )
        return paginated

    def update_asset_totvs(
        self, totvs_assets: List[AssetTotvsSchema], db_session: Session
    ):
        """Updates assets from totvs"""
        try:
            updates: List[AssetModel] = []
            for totvs_asset in totvs_assets:
                if (
                    db_session.query(AssetModel)
                    .filter(AssetModel.code == totvs_asset.code)
                    .first()
                ):
                    continue

                asset_type = (
                    db_session.query(AssetTypeModel)
                    .filter(AssetTypeModel.name == totvs_asset.type)
                    .first()
                )

                dict_asset = {
                    **totvs_asset.model_dump(exclude={"asset_type"}),
                    "type": asset_type,
                }

                updates.append(AssetModel(**dict_asset))

            db_session.add_all(updates)
            db_session.commit()
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE) from exc

    def update_asset_type_totvs(
        self,
        totvs_asset_type: List[AssetTypeTotvsSchema],
        db_session: Session,
    ):
        """Updates asset type from totvs"""
        try:
            updates: List[AssetTypeModel] = []
            for totvs_asset_type_item in totvs_asset_type:
                db_asset_type = (
                    db_session.query(AssetTypeModel)
                    .filter(AssetTypeModel.code == totvs_asset_type_item.code)
                    .first()
                )
                if db_asset_type:
                    db_asset_type.group_code = totvs_asset_type_item.group_code
                    db_asset_type.name = totvs_asset_type_item.name
                    updates.append(db_asset_type)
                    continue

                updates.append(AssetTypeModel(**totvs_asset_type_item.model_dump()))

            db_session.add_all(updates)
            db_session.commit()
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE) from exc
