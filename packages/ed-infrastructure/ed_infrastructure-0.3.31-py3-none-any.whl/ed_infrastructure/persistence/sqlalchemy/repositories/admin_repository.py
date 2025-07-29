from ed_domain.core.aggregate_roots.admin import Admin
from ed_domain.persistence.async_repositories.abc_async_admin_repository import \
    ABCAsyncAdminRepository

from ed_infrastructure.persistence.sqlalchemy.models import AdminModel
from ed_infrastructure.persistence.sqlalchemy.repositories.generic_repository import \
    AsyncGenericRepository


class AdminRepository(
    ABCAsyncAdminRepository, AsyncGenericRepository[Admin, AdminModel]
):
    def __init__(self) -> None:
        super().__init__(AdminModel)

    @classmethod
    def _to_entity(cls, model: AdminModel) -> Admin:
        return Admin(
            id=model.id,
            user_id=model.user_id,
            first_name=model.first_name,
            last_name=model.last_name,
            phone_number=model.phone_number,
            email=model.email,
            role=model.role,
            create_datetime=model.create_datetime,
            update_datetime=model.update_datetime,
            deleted=model.deleted,
            deleted_datetime=model.deleted_datetime,
        )

    @classmethod
    def _to_model(cls, entity: Admin) -> AdminModel:
        return AdminModel(
            id=entity.id,
            user_id=entity.user_id,
            first_name=entity.first_name,
            last_name=entity.last_name,
            phone_number=entity.phone_number,
            email=entity.email,
            role=entity.role,
            create_datetime=entity.create_datetime,
            update_datetime=entity.update_datetime,
            deleted=entity.deleted,
            deleted_datetime=entity.deleted_datetime,
        )
