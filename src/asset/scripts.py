""" Asset scripts """

import logging

from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import and_, or_

from src.asset.models import AssetModel, AssetStatusHistoricModel
from src.lending.models import LendingModel

logger = logging.getLogger(__name__)


def fix_asset_status(db_session: Session):
    """Fix asset status that are not updated when a lending is created"""
    all_assets_to_update = (
        db_session.query(
            AssetModel,
            LendingModel.status_id,
            LendingModel.created_at,
        )
        .outerjoin(LendingModel, AssetModel.id == LendingModel.asset_id)
        .filter(
            and_(
                or_(LendingModel.status_id == 1, LendingModel.status_id == 2),
                AssetModel.status_id == 1,
                LendingModel.asset_id.isnot(None),
            )
        )
    )
    logger.info("Updating %s assets status...", all_assets_to_update.count())
    print(f"Updating {all_assets_to_update.count()} assets status...")
    assets_to_update = []
    history_to_create = []
    for asset, _, created_at in all_assets_to_update.all():
        asset.status_id = 2
        assets_to_update.append(asset)
        history_to_create.append(
            AssetStatusHistoricModel(
                asset_id=asset.id, status_id=2, created_at=created_at
            )
        )
    db_session.bulk_save_objects(assets_to_update)
    db_session.bulk_save_objects(history_to_create)
    db_session.commit()
    print("All assets status fixed!")
    logger.info("All assets status fixed!")
    db_session.close_all()


def fix_asset_historic(db_session: Session):
    """Fix asset historic that are not updated when a lending is created"""
    all_assets_to_update = (
        db_session.query(
            AssetModel,
            LendingModel.status_id,
            LendingModel.created_at,
            LendingModel.updated_at,
        )
        .outerjoin(LendingModel, AssetModel.id == LendingModel.asset_id)
        .outerjoin(AssetStatusHistoricModel)
        .filter(
            LendingModel.deleted == 0,
            AssetStatusHistoricModel.id.is_(None),
        )
    )
    print(f"Updating {all_assets_to_update.count()} assets historic...")
    logger.info("Updating %s assets historic...", all_assets_to_update.count())
    history_to_create = []
    for asset, lending_status_id, created_at, updated_at in all_assets_to_update.all():
        print(asset.id)
        if lending_status_id in [1, 2, 3]:
            history_to_create.append(
                AssetStatusHistoricModel(
                    asset_id=asset.id, status_id=2, created_at=created_at
                )
            )
        elif lending_status_id == 4:
            history_to_create.append(
                AssetStatusHistoricModel(
                    asset_id=asset.id, status_id=1, created_at=updated_at
                )
            )
    db_session.bulk_save_objects(history_to_create)
    db_session.commit()
    print("All assets historic fixed!")
    logger.info("All assets historic fixed!")
    db_session.close_all()


def fix_asset_pattern_ios(db_session: Session):
    """Fix asset pattern for iOS"""
    all_assets_to_update = db_session.query(AssetModel).filter(
        AssetModel.description.startswith("MACBOOK")
    )

    print(f"Updating {all_assets_to_update.count()} assets pattern ios...")
    logger.info("Updating %s assets pattern ios...", all_assets_to_update.count())
    assets_to_update = []
    for asset in all_assets_to_update.all():
        asset.pattern = "MACBOOK"
        assets_to_update.append(asset)
    db_session.bulk_save_objects(assets_to_update)
    db_session.commit()
    print("All assets pattern fixed!")
    logger.info("All assets pattern fixed!")
    db_session.close_all()
