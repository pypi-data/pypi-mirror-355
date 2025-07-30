from ed_domain.core.entities.otp import Otp
from ed_domain.persistence.async_repositories.abc_async_otp_repository import \
    ABCAsyncOtpRepository

from ed_infrastructure.persistence.sqlalchemy.models import OtpModel
from ed_infrastructure.persistence.sqlalchemy.repositories.generic_repository import \
    AsyncGenericRepository


class OtpRepository(
    ABCAsyncOtpRepository,
    AsyncGenericRepository[Otp, OtpModel],
):
    def __init__(self) -> None:
        super().__init__(OtpModel)

    @classmethod
    def _to_entity(cls, model: OtpModel) -> Otp:
        return Otp(
            id=model.id,
            user_id=model.user_id,
            otp_type=model.otp_type,
            value=model.value,
            expiry_datetime=model.expiry_datetime,
            create_datetime=model.create_datetime,
            update_datetime=model.update_datetime,
            deleted=model.deleted,
            deleted_datetime=model.deleted_datetime,
        )

    @classmethod
    def _to_model(cls, entity: Otp) -> OtpModel:
        return OtpModel(
            id=entity.id,
            user_id=entity.user_id,
            otp_type=entity.otp_type,
            value=entity.value,
            expiry_datetime=entity.expiry_datetime,
            create_datetime=entity.create_datetime,
            update_datetime=entity.update_datetime,
            deleted=entity.deleted,
            deleted_datetime=entity.deleted_datetime,
        )
