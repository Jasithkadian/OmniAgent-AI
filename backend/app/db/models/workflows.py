import enum
from uuid import UUID
from typing import Optional

from sqlalchemy import Enum, Text, JSON, UUID as SQL_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class WorkflowStatusEnum(str, enum.Enum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"


class Workflow(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "workflows"

    user_id: Mapped[UUID] = mapped_column(SQL_UUID, nullable=False, index=True)
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[WorkflowStatusEnum] = mapped_column(
        Enum(WorkflowStatusEnum, name="workflow_status"),
        default=WorkflowStatusEnum.queued,
        nullable=False,
        index=True,
    )
    state_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
