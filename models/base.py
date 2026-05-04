from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Single declarative base shared by every SQLAlchemy model.
    Import from here — never create a second Base elsewhere.
    """
    pass