from ed_domain.core.entities.bill import Bill
from ed_domain.persistence.async_repositories.abc_async_bill_repository import \
    ABCAsyncBillRepository

from ed_infrastructure.persistence.sqlalchemy.models import BillModel
from ed_infrastructure.persistence.sqlalchemy.repositories.generic_repository import \
    AsyncGenericRepository


class BillRepository(ABCAsyncBillRepository, AsyncGenericRepository[Bill, BillModel]):
    def __init__(self) -> None:
        super().__init__(BillModel)

    @classmethod
    def _to_entity(cls, model: BillModel) -> Bill:
        return Bill(
            id=model.id,
            amount_in_birr=model.amount_in_birr,
            bill_status=model.bill_status,
            due_date=model.due_date,
            create_datetime=model.create_datetime,
            update_datetime=model.update_datetime,
            deleted=model.deleted,
            deleted_datetime=model.deleted_datetime,
        )

    @classmethod
    def _to_model(cls, entity: Bill) -> BillModel:
        return BillModel(
            id=entity.id,
            amount_in_birr=entity.amount_in_birr,
            bill_status=entity.bill_status,
            due_date=entity.due_date,
            create_datetime=entity.create_datetime,
            update_datetime=entity.update_datetime,
            deleted=entity.deleted,
            deleted_datetime=entity.deleted_datetime,
        )
