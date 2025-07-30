from ed_domain.core.aggregate_roots.auth_user import AuthUser
from ed_domain.persistence.async_repositories.abc_async_auth_user_repository import \
    ABCAsyncAuthUserRepository

from ed_infrastructure.persistence.sqlalchemy.models import AuthUserModel
from ed_infrastructure.persistence.sqlalchemy.repositories.generic_repository import \
    AsyncGenericRepository


class AuthUserRepository(
    ABCAsyncAuthUserRepository, AsyncGenericRepository[AuthUser, AuthUserModel]
):
    def __init__(self) -> None:
        super().__init__(AuthUserModel)

    @classmethod
    def _to_entity(cls, model: AuthUserModel) -> AuthUser:
        return AuthUser(
            id=model.id,
            first_name=model.first_name,
            last_name=model.last_name,
            password_hash=model.password_hash,
            verified=model.verified,
            logged_in=model.logged_in,
            email=model.email,
            phone_number=model.phone_number,
            create_datetime=model.create_datetime,
            update_datetime=model.update_datetime,
            deleted=model.deleted,
            deleted_datetime=model.deleted_datetime,
        )

    @classmethod
    def _to_model(cls, entity: AuthUser) -> AuthUserModel:
        return AuthUserModel(
            id=entity.id,
            first_name=entity.first_name,
            last_name=entity.last_name,
            password_hash=entity.password_hash,
            verified=entity.verified,
            logged_in=entity.logged_in,
            email=entity.email,
            phone_number=entity.phone_number,
            create_datetime=entity.create_datetime,
            update_datetime=entity.update_datetime,
            deleted=entity.deleted,
            deleted_datetime=entity.deleted_datetime,
        )
