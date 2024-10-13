from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import and_, or_

from src.asset.models import AssetModel, AssetStatusHistoricModel
from src.lending.models import LendingModel


def fix_asset_status(db_session: Session):
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
    db_session.close_all()
