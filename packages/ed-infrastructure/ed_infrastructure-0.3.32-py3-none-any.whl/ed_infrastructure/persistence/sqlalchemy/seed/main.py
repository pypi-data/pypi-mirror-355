from ed_domain.core.aggregate_roots import Order
from ed_domain.core.entities.waypoint import WaypointType

from ed_infrastructure.persistence.sqlalchemy.seed.admin import get_admin
from ed_infrastructure.persistence.sqlalchemy.seed.api_key import get_api_key
from ed_infrastructure.persistence.sqlalchemy.seed.auth_users import (
    get_admin_auth_user, get_business_auth_user, get_consumer_auth_user,
    get_driver_auth_user)
from ed_infrastructure.persistence.sqlalchemy.seed.bill import get_bill
from ed_infrastructure.persistence.sqlalchemy.seed.business import get_business
from ed_infrastructure.persistence.sqlalchemy.seed.car import get_car
from ed_infrastructure.persistence.sqlalchemy.seed.consumer import get_consumer
from ed_infrastructure.persistence.sqlalchemy.seed.delivery_job import \
    get_delivery_job
from ed_infrastructure.persistence.sqlalchemy.seed.driver import get_driver
from ed_infrastructure.persistence.sqlalchemy.seed.location import get_location
from ed_infrastructure.persistence.sqlalchemy.seed.order import get_order
from ed_infrastructure.persistence.sqlalchemy.seed.parcel import get_parcel
from ed_infrastructure.persistence.sqlalchemy.seed.waypoint import get_waypoint
from ed_infrastructure.persistence.sqlalchemy.unit_of_work import UnitOfWork


async def async_seed(uow: UnitOfWork) -> None:
    await uow.create_tables()
    async with uow.transaction():
        print("Creating driver_auth_users...")
        driver_auth_user = await uow.auth_user_repository.create(get_driver_auth_user())

        print("Creating business_auth_users...")
        business_auth_user = await uow.auth_user_repository.create(
            get_business_auth_user()
        )

        print("Creating consumer_auth_users...")
        consumer_auth_user = await uow.auth_user_repository.create(
            get_consumer_auth_user()
        )

        print("Creating admin_auth_users...")
        admin_auth_user = await uow.auth_user_repository.create(get_admin_auth_user())

        print("Creating admin...")
        admin = await uow.admin_repository.create(get_admin(admin_auth_user.id))

        print("Creating locations...")
        location = await uow.location_repository.create(get_location())

        print("Creating consumers...")
        consumer = await uow.consumer_repository.create(
            get_consumer(consumer_auth_user.id, location.id)
        )

        print("Creating businesss...")
        business = await uow.business_repository.create(
            get_business(business_auth_user.id, location.id, [])
        )

        print("Creating api_key...")
        api_key = await uow.api_key_repository.create(get_api_key(business.id))

        print("Creating cars...")
        car = await uow.car_repository.create(get_car())

        print("Creating drivers...")
        driver = await uow.driver_repository.create(
            get_driver(driver_auth_user.id, car, location.id)
        )

        print("Creating parcels...")
        parcel = await uow.parcel_repository.create(get_parcel())

        print("Creating bills...")
        bill = await uow.bill_repository.create(get_bill())

        print("Creating orders...")
        order = await uow.order_repository.create(
            get_order(business.id, consumer.id, driver.id, bill, parcel)
        )

        print("Creating delivery_jobs...")
        delivery_job = await uow.delivery_job_repository.create(
            get_delivery_job(driver.id, [])
        )

        print("Creating waypoints...")
        waypoint = await uow.waypoint_repository.create(
            get_waypoint(delivery_job.id, 1, order.id)
        )

        print(delivery_job.__dict__)


async def async_get(uow: UnitOfWork) -> None:
    async with uow.transaction():
        print("\n\nGetting auth_users...")
        driver_auth_user = await uow.auth_user_repository.get_all()
        print(driver_auth_user)

        print("\n\nGetting locations...")
        location = await uow.location_repository.get_all()
        print(location)

        print("\n\nGetting consumers...")
        consumer = await uow.consumer_repository.get_all()
        print(consumer)

        print("\n\nGetting businesss...")
        business = await uow.business_repository.get_all()
        print(business)

        print("\n\nGetting cars...")
        car = await uow.car_repository.get_all()
        print(car)

        print("\n\nGetting drivers...")
        driver = await uow.driver_repository.get_all()
        print(driver)

        print("\n\nGetting parcels...")
        parcel = await uow.parcel_repository.get_all()
        print(parcel)

        print("\n\nGetting bills...")
        bill = await uow.bill_repository.get_all()
        print(bill)

        print("\n\nGetting orders...")
        order = await uow.order_repository.get_all()
        print(order)

        print("\n\nGetting waypoints...")
        waypoint = await uow.waypoint_repository.get_all()
        print(waypoint)

        print("\n\nGetting delivery_jobs...")
        delivery_job = await uow.delivery_job_repository.get_all()
        print(delivery_job)


async def seed_delivery_job(uow: UnitOfWork) -> list[Order]:
    orders: list[Order] = []

    async with uow.transaction():
        print("Getting business, consumer, and delivery_job...")
        business = (await uow.business_repository.get_all())[0]
        consumer = (await uow.consumer_repository.get_all())[0]
        delivery_job = (await uow.delivery_job_repository.get_all())[0]

        sequence = 1
        for _ in range(10):
            print(f"Creating parcel {sequence}...")
            parcel = await uow.parcel_repository.create(get_parcel())

            print(f"Creating bill {sequence}...")
            bill = await uow.bill_repository.create(get_bill())

            print(f"Creating order {sequence}...")
            order = await uow.order_repository.create(
                get_order(business.id, consumer.id, None, bill, parcel)
            )
            waypoint_1 = await uow.waypoint_repository.create(
                get_waypoint(
                    delivery_job.id, sequence + 1, order.id, WaypointType.PICK_UP
                )
            )
            waypoint_2 = await uow.waypoint_repository.create(
                get_waypoint(
                    delivery_job.id, sequence + 2, order.id, WaypointType.DROP_OFF
                )
            )

            delivery_job.add_waypoint(waypoint_1)
            delivery_job.add_waypoint(waypoint_2)
            sequence += 2

        print(delivery_job)

    return orders
