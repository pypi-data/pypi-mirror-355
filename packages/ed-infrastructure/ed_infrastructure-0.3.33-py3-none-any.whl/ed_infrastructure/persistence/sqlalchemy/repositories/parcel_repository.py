from ed_domain.core.entities.parcel import Parcel
from ed_domain.persistence.async_repositories.abc_async_parcel_repository import \
    ABCAsyncParcelRepository

from ed_infrastructure.persistence.sqlalchemy.models import ParcelModel
from ed_infrastructure.persistence.sqlalchemy.repositories.generic_repository import \
    AsyncGenericRepository


class ParcelRepository(
    ABCAsyncParcelRepository,
    AsyncGenericRepository[Parcel, ParcelModel],
):
    def __init__(self) -> None:
        super().__init__(ParcelModel)

    @classmethod
    def _to_entity(cls, model: ParcelModel) -> Parcel:
        return Parcel(
            id=model.id,
            size=model.size,
            length=model.length,
            width=model.width,
            height=model.height,
            weight=model.weight,
            fragile=model.fragile,
            create_datetime=model.create_datetime,
            update_datetime=model.update_datetime,
            deleted=model.deleted,
            deleted_datetime=model.deleted_datetime,
        )

    @classmethod
    def _to_model(cls, entity: Parcel) -> ParcelModel:
        return ParcelModel(
            id=entity.id,
            size=entity.size,
            length=entity.length,
            width=entity.width,
            height=entity.height,
            weight=entity.weight,
            fragile=entity.fragile,
            create_datetime=entity.create_datetime,
            update_datetime=entity.update_datetime,
            deleted=entity.deleted,
            deleted_datetime=entity.deleted_datetime,
        )
