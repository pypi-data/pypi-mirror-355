from uuid import UUID

from ed_domain.core.aggregate_roots.order import Order
from ed_domain.persistence.async_repositories.abc_async_order_repository import \
    ABCAsyncOrderRepository

from ed_infrastructure.persistence.sqlalchemy.models import OrderModel
from ed_infrastructure.persistence.sqlalchemy.repositories.bill_repository import \
    BillRepository
from ed_infrastructure.persistence.sqlalchemy.repositories.generic_repository import \
    AsyncGenericRepository
from ed_infrastructure.persistence.sqlalchemy.repositories.parcel_repository import \
    ParcelRepository


class OrderRepository(
    ABCAsyncOrderRepository,
    AsyncGenericRepository[Order, OrderModel],
):
    def __init__(self) -> None:
        super().__init__(OrderModel)
        self._bill_repository = BillRepository()
        self._parcel_repository = ParcelRepository()

    async def update(self, id: UUID, entity: Order) -> bool:
        bill_updated = await self._bill_repository.update(entity.bill.id, entity.bill)
        parcel_updated = await self._parcel_repository.update(
            entity.parcel.id, entity.parcel
        )

        order_updated = await self.update(id, entity)

        return bill_updated or parcel_updated or order_updated

    @classmethod
    def _to_entity(cls, model: OrderModel) -> Order:
        return Order(
            id=model.id,
            order_number=model.order_number,
            business_id=model.business_id,
            consumer_id=model.consumer_id,
            driver_id=model.driver_id if model.driver_id else None,
            bill=BillRepository._to_entity(model.bill),
            parcel=ParcelRepository._to_entity(model.parcel),
            latest_time_of_delivery=model.latest_time_of_delivery,
            distance_in_km=model.distance_in_km,
            order_status=model.order_status,
            create_datetime=model.create_datetime,
            update_datetime=model.update_datetime,
            deleted=model.deleted,
            deleted_datetime=model.deleted_datetime,
        )

    @classmethod
    def _to_model(cls, entity: Order) -> OrderModel:
        return OrderModel(
            id=entity.id,
            order_number=entity.order_number,
            business_id=entity.business_id,
            consumer_id=entity.consumer_id,
            driver_id=entity.driver_id if entity.driver_id else None,
            bill_id=entity.bill.id,
            parcel_id=entity.parcel.id,
            latest_time_of_delivery=entity.latest_time_of_delivery,
            distance_in_km=entity.distance_in_km,
            order_status=entity.order_status,
            create_datetime=entity.create_datetime,
            update_datetime=entity.update_datetime,
            deleted=entity.deleted,
            deleted_datetime=entity.deleted_datetime,
        )
