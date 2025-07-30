from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class BaseModel(DeclarativeBase):
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, nullable=False)
    create_datetime: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    update_datetime: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    deleted: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False)
    deleted_datetime: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
