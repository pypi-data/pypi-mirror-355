from datetime import UTC

from ed_domain.core.aggregate_roots import AuthUser
from jsons import datetime

from ed_infrastructure.common.generic import get_new_id


def get_business_auth_user() -> AuthUser:
    return AuthUser(
        id=get_new_id(),
        first_name="Shamil",
        last_name="Bedru",
        phone_number="251948671563",
        email="shamilbedru47@gmail.com",
        password_hash="$2b$12$mlewRx4nfy7FKCB.RJrVs.N.CD95q3DBBDr6zqxtOzQoBvQjnzFK6",
        verified=True,
        logged_in=False,
        create_datetime=datetime.now(UTC),
        update_datetime=datetime.now(UTC),
        deleted_datetime=datetime.now(UTC),
        deleted=False,
    )


def get_admin_auth_user() -> AuthUser:
    return AuthUser(
        id=get_new_id(),
        first_name="Fikernew",
        last_name="Birhanu",
        phone_number="251930316621",
        email="ffekirnew0808@gmail.com",
        password_hash="$2b$12$mlewRx4nfy7FKCB.RJrVs.N.CD95q3DBBDr6zqxtOzQoBvQjnzFK6",
        verified=True,
        logged_in=False,
        create_datetime=datetime.now(UTC),
        update_datetime=datetime.now(UTC),
        deleted_datetime=datetime.now(UTC),
        deleted=False,
    )


def get_consumer_auth_user() -> AuthUser:
    return AuthUser(
        id=get_new_id(),
        first_name="Fikernew",
        last_name="Birhanu",
        phone_number="251930316620",
        email="phikernew0808@gmail.com",
        password_hash="$2b$12$mlewRx4nfy7FKCB.RJrVs.N.CD95q3DBBDr6zqxtOzQoBvQjnzFK6",
        verified=True,
        logged_in=False,
        create_datetime=datetime.now(UTC),
        update_datetime=datetime.now(UTC),
        deleted_datetime=datetime.now(UTC),
        deleted=False,
    )


def get_driver_auth_user() -> AuthUser:
    return AuthUser(
        id=get_new_id(),
        first_name="Firaol",
        last_name="Ibrahim",
        phone_number="251977346620",
        email="firaolibrahim28@gmail.com",
        password_hash="$2b$12$mlewRx4nfy7FKCB.RJrVs.N.CD95q3DBBDr6zqxtOzQoBvQjnzFK6",
        verified=True,
        logged_in=False,
        create_datetime=datetime.now(UTC),
        update_datetime=datetime.now(UTC),
        deleted_datetime=datetime.now(UTC),
        deleted=False,
    )


def get_random_auth_user(
    first_name: str,
    last_name: str,
    index: int,
) -> AuthUser:
    phone_number = "2519000000"
    phone_number += str(index) if len(str(index)) == 2 else "0" + str(index)

    return AuthUser(
        id=get_new_id(),
        first_name=first_name,
        last_name=last_name,
        phone_number=phone_number,
        email="default@ed.com",
        password_hash="",
        verified=True,
        logged_in=False,
        create_datetime=datetime.now(UTC),
        update_datetime=datetime.now(UTC),
        deleted_datetime=datetime.now(UTC),
        deleted=False,
    )
