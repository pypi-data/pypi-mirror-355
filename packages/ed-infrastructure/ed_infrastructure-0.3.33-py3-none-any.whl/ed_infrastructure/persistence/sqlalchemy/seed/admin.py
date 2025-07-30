from datetime import UTC
from uuid import UUID

from ed_domain.core.aggregate_roots import Admin
from ed_domain.core.aggregate_roots.admin import AdminRole
from jsons import datetime

from ed_infrastructure.common.generic import get_new_id


def get_admin(admin_user_id: UUID) -> Admin:
    return Admin(
        user_id=admin_user_id,
        id=get_new_id(),
        first_name="Fikernew",
        last_name="Birhanu",
        phone_number="251977346620",
        email="phikernew0808@gmail.com",
        role=AdminRole.SUPER_ADMIN,
        create_datetime=datetime.now(UTC),
        update_datetime=datetime.now(UTC),
        deleted_datetime=datetime.now(UTC),
        deleted=False,
    )
