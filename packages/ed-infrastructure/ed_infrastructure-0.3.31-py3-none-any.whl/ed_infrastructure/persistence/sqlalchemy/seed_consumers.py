from random import choice

from ed_infrastructure.persistence.sqlalchemy.seed.auth_users import \
    get_random_auth_user
from ed_infrastructure.persistence.sqlalchemy.seed.consumer import get_consumer
from ed_infrastructure.persistence.sqlalchemy.seed.location import (
    generate_random_latitude, generate_random_longitude, get_location)
from ed_infrastructure.persistence.sqlalchemy.unit_of_work import UnitOfWork

ethiopian_first_names = [
    "Abel",
    "Bekele",
    "Chaltu",
    "Dagmawi",
    "Eleni",
    "Fikirte",
    "Girma",
    "Hirut",
    "Isayas",
    "Jember",
    "Kalkidan",
    "Lulit",
    "Meles",
    "Nardos",
    "Obse",
    "Pawlos",
    "Rahel",
    "Selam",
    "Tadesse",
    "Yohannes",
]

ethiopian_last_names = [
    "Abebe",
    "Berhanu",
    "Chekole",
    "Desalegn",
    "Endeshaw",
    "Fekadu",
    "Gebremariam",
    "Hailu",
    "Ibrahim",
    "Kebede",
    "Lema",
    "Mekonnen",
    "Negash",
    "Oumer",
    "Petros",
    "Reda",
    "Shiferaw",
    "Teshome",
    "Wondimu",
    "Yilma",
]


async def seed_consumers(uow: UnitOfWork):
    async with uow.transaction():
        print("Creating consumer auth users...")
        auth_users = await uow.auth_user_repository.create_many(
            [
                get_random_auth_user(
                    choice(ethiopian_first_names), choice(
                        ethiopian_last_names), i
                )
                for i in range(10)
            ]
        )

        print("Creating locations...")
        locations = await uow.location_repository.create_many(
            [
                get_location(generate_random_latitude(),
                             generate_random_longitude())
                for _ in range(10)
            ]
        )

        print("Creating consumers...")
        consumers = await uow.consumer_repository.create_many(
            [
                get_consumer(
                    auth_users[i].id,
                    locations[i].id,
                    auth_users[i].first_name,
                    auth_users[i].last_name,
                    auth_users[i].phone_number or "",
                    auth_users[i].email or "",
                )
                for i in range(10)
            ]
        )

        return consumers
