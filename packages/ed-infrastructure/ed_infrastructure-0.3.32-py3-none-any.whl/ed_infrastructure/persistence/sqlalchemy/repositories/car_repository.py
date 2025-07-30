from ed_domain.core.entities.car import Car
from ed_domain.persistence.async_repositories.abc_async_car_repository import \
    ABCAsyncCarRepository

from ed_infrastructure.persistence.sqlalchemy.models import CarModel
from ed_infrastructure.persistence.sqlalchemy.repositories.generic_repository import \
    AsyncGenericRepository


class CarRepository(ABCAsyncCarRepository, AsyncGenericRepository[Car, CarModel]):
    def __init__(self) -> None:
        super().__init__(CarModel)

    @classmethod
    def _to_entity(cls, model: CarModel) -> Car:
        return Car(
            id=model.id,
            make=model.make,
            model=model.model,
            year=model.year,
            registration_number=model.registration_number,
            license_plate_number=model.license_plate_number,
            color=model.color,
            seats=model.seats,
            create_datetime=model.create_datetime,
            update_datetime=model.update_datetime,
            deleted_datetime=model.update_datetime,
            deleted=model.deleted,
        )

    @classmethod
    def _to_model(cls, entity: Car) -> CarModel:
        return CarModel(
            id=entity.id,
            make=entity.make,
            model=entity.model,
            year=entity.year,
            registration_number=entity.registration_number,
            license_plate_number=entity.license_plate_number,
            color=entity.color,
            seats=entity.seats,
            create_datetime=entity.create_datetime,
            update_datetime=entity.update_datetime,
            deleted=entity.deleted,
            deleted_datetime=entity.deleted_datetime,
        )
