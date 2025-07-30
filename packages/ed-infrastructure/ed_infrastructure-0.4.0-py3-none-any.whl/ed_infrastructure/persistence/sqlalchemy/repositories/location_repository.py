from ed_domain.core.aggregate_roots import Location
from ed_domain.persistence.async_repositories.abc_async_location_repository import \
    ABCAsyncLocationRepository

from ed_infrastructure.persistence.sqlalchemy.models import LocationModel
from ed_infrastructure.persistence.sqlalchemy.repositories.generic_repository import \
    AsyncGenericRepository


class LocationRepository(
    ABCAsyncLocationRepository, AsyncGenericRepository[Location, LocationModel]
):
    def __init__(self) -> None:
        super().__init__(LocationModel)

    @classmethod
    def _to_entity(cls, model: LocationModel) -> Location:
        return Location(
            id=model.id,
            address=model.address,
            latitude=model.latitude,
            longitude=model.longitude,
            postal_code=model.postal_code,
            city=model.city,
            country=model.country,
            last_used=model.last_used,
            create_datetime=model.create_datetime,
            update_datetime=model.update_datetime,
            deleted=model.deleted,
            deleted_datetime=model.deleted_datetime,
        )

    @classmethod
    def _to_model(cls, entity: Location) -> LocationModel:
        return LocationModel(
            id=entity.id,
            address=entity.address,
            latitude=entity.latitude,
            longitude=entity.longitude,
            postal_code=entity.postal_code,
            city=entity.city,
            country=entity.country,
            last_used=entity.last_used,
            create_datetime=entity.create_datetime,
            update_datetime=entity.update_datetime,
            deleted=entity.deleted,
            deleted_datetime=entity.deleted_datetime,
        )
