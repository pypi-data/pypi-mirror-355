from contextlib import asynccontextmanager
from typing import AsyncGenerator

from ed_domain.persistence.async_repositories import (
    ABCAsyncApiKeyRepository, ABCAsyncAuthUserRepository,
    ABCAsyncBillRepository, ABCAsyncBusinessRepository, ABCAsyncCarRepository,
    ABCAsyncConsumerRepository, ABCAsyncDeliveryJobRepository,
    ABCAsyncDriverRepository, ABCAsyncLocationRepository,
    ABCAsyncNotificationRepository, ABCAsyncOrderRepository,
    ABCAsyncOtpRepository, ABCAsyncParcelRepository, ABCAsyncUnitOfWork)
from ed_domain.persistence.async_repositories.abc_async_unit_of_work import \
    ABCAsyncAdminRepository
from ed_domain.persistence.async_repositories.abc_async_waypoint_repository import \
    ABCAsyncWaypointRepository
from sqlalchemy.ext.asyncio import AsyncSession

from ed_infrastructure.persistence.sqlalchemy.db_engine import (DbConfig,
                                                                DbEngine)
from ed_infrastructure.persistence.sqlalchemy.db_session import DbSession
from ed_infrastructure.persistence.sqlalchemy.models import BaseModel
from ed_infrastructure.persistence.sqlalchemy.repositories import (
    AdminRepository, ApiKeyRepository, AuthUserRepository, BillRepository,
    BusinessRepository, CarRepository, ConsumerRepository,
    DeliveryJobRepository, DriverRepository, LocationRepository,
    NotificationRepository, OrderRepository, OtpRepository, ParcelRepository,
    WaypointRepository)


class UnitOfWork(ABCAsyncUnitOfWork):
    async def create_tables(self) -> None:
        async with self._db_engine.engine.begin() as conn:
            await conn.run_sync(self._base.metadata.drop_all)
            await conn.run_sync(self._base.metadata.create_all)

    async def stop(self) -> None:
        await self._db_engine.dispose()

    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[None, None]:
        try:
            async_session: AsyncSession = self._db_session()

            self._set_repository_sessions(async_session)

            await async_session.begin()
            yield
            await async_session.commit()

        except Exception:
            await async_session.rollback()  # type: ignore
            raise

        finally:
            await async_session.close()  # type: ignore
            self._clear_repository_sessions()

    def __init__(self, db_config: DbConfig) -> None:
        self._base = BaseModel
        self._db_engine = DbEngine(db_config)
        self._db_session = DbSession(self._db_engine)

        self._admin_repository = AdminRepository()
        self._auth_user_repository = AuthUserRepository()
        self._bill_repository = BillRepository()
        self._business_repository = BusinessRepository()
        self._car_repository = CarRepository()
        self._consumer_repository = ConsumerRepository()
        self._driver_repository = DriverRepository()
        self._delivery_job_repository = DeliveryJobRepository()
        self._location_repository = LocationRepository()
        self._notification_repository = NotificationRepository()
        self._otp_repository = OtpRepository()
        self._order_repository = OrderRepository()
        self._parcel_repository = ParcelRepository()
        self._waypoint_repository = WaypointRepository()
        self._api_key_repository = ApiKeyRepository()

        self._repositories = [
            self._admin_repository,
            self._auth_user_repository,
            self._bill_repository,
            self._business_repository,
            self._car_repository,
            self._consumer_repository,
            self._driver_repository,
            self._delivery_job_repository,
            self._location_repository,
            self._notification_repository,
            self._otp_repository,
            self._order_repository,
            self._waypoint_repository,
            self._parcel_repository,
            self._api_key_repository,
        ]

    @property
    def admin_repository(self) -> ABCAsyncAdminRepository:
        return self._admin_repository

    @property
    def bill_repository(self) -> ABCAsyncBillRepository:
        return self._bill_repository

    @property
    def business_repository(self) -> ABCAsyncBusinessRepository:
        return self._business_repository

    @property
    def car_repository(self) -> ABCAsyncCarRepository:
        return self._car_repository

    @property
    def consumer_repository(self) -> ABCAsyncConsumerRepository:
        return self._consumer_repository

    @property
    def delivery_job_repository(self) -> ABCAsyncDeliveryJobRepository:
        return self._delivery_job_repository

    @property
    def driver_repository(self) -> ABCAsyncDriverRepository:
        return self._driver_repository

    @property
    def location_repository(self) -> ABCAsyncLocationRepository:
        return self._location_repository

    @property
    def notification_repository(self) -> ABCAsyncNotificationRepository:
        return self._notification_repository

    @property
    def order_repository(self) -> ABCAsyncOrderRepository:
        return self._order_repository

    @property
    def otp_repository(self) -> ABCAsyncOtpRepository:
        return self._otp_repository

    @property
    def auth_user_repository(self) -> ABCAsyncAuthUserRepository:
        return self._auth_user_repository

    @property
    def waypoint_repository(self) -> ABCAsyncWaypointRepository:
        return self._waypoint_repository

    @property
    def api_key_repository(self) -> ABCAsyncApiKeyRepository:
        return self._api_key_repository

    @property
    def parcel_repository(self) -> ABCAsyncParcelRepository:
        return self._parcel_repository

    def _set_repository_sessions(self, session: AsyncSession):
        for repository in self._repositories:
            repository.session = session

    def _clear_repository_sessions(self):
        for repository in self._repositories:
            repository.session = None
