from uuid import UUID

from ed_domain.core.aggregate_roots.driver import Driver
from ed_domain.persistence.async_repositories.abc_async_driver_repository import \
    ABCAsyncDriverRepository

from ed_infrastructure.persistence.sqlalchemy.models import DriverModel
from ed_infrastructure.persistence.sqlalchemy.repositories.car_repository import \
    CarRepository
from ed_infrastructure.persistence.sqlalchemy.repositories.generic_repository import \
    AsyncGenericRepository


class DriverRepository(
    ABCAsyncDriverRepository, AsyncGenericRepository[Driver, DriverModel]
):
    def __init__(self) -> None:
        super().__init__(DriverModel)
        self._car_repository = CarRepository()

    async def update(self, id: UUID, entity: Driver) -> bool:
        car_updated = await self._car_repository.update(entity.car.id, entity.car)
        driver_updated = await self.update(id, entity)

        return car_updated or driver_updated

    @classmethod
    def _to_entity(cls, model: DriverModel) -> Driver:
        return Driver(
            id=model.id,
            user_id=model.user_id,
            first_name=model.first_name,
            last_name=model.last_name,
            profile_image=model.profile_image,
            phone_number=model.phone_number,
            email=model.email,
            location_id=model.location_id,
            car=CarRepository._to_entity(model.car),
            create_datetime=model.create_datetime,
            update_datetime=model.update_datetime,
            deleted=model.deleted,
            deleted_datetime=model.deleted_datetime,
        )

    @classmethod
    def _to_model(cls, entity: Driver) -> DriverModel:
        return DriverModel(
            id=entity.id,
            user_id=entity.user_id,
            first_name=entity.first_name,
            last_name=entity.last_name,
            profile_image=entity.profile_image,
            phone_number=entity.phone_number,
            location_id=entity.location_id,
            car_id=entity.car.id,
            available=entity.available,
            email=entity.email,
            create_datetime=entity.create_datetime,
            update_datetime=entity.update_datetime,
            deleted=entity.deleted,
            deleted_datetime=entity.deleted_datetime,
        )
