import uuid

from sqlalchemy import Boolean, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Therapist(Base):
    """
    Static directory of mental health professionals.
    is_emergency_contact=True entries float to the top
    of the Severe Risk screen.
    """
    __tablename__ = "therapists"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    specialization: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # e.g. "Clinical Psychologist" | "CBT Specialist"
    contact_number: Mapped[str] = mapped_column(String(20), nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    is_emergency_contact: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, index=True
    )

    def __repr__(self) -> str:
        return (
            f"<Therapist id={self.id} name={self.name!r} "
            f"emergency={self.is_emergency_contact}>"
        )