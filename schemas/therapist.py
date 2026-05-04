import uuid

from pydantic import BaseModel


class TherapistOut(BaseModel):
    id: uuid.UUID
    name: str
    specialization: str
    contact_number: str
    location: str
    is_emergency_contact: bool

    model_config = {"from_attributes": True}
    

class TherapistListOut(BaseModel):
    """
    Response for GET /therapists.
    Emergency contacts are always first in the list (sorted by service layer).
    """
    therapists: list[TherapistOut]
    total:      int