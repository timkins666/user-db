"""user model classes"""

from datetime import datetime, date
import re
import uuid
from fastapi import HTTPException, status
from humps import camel
from sqlmodel import Field, SQLModel
from pydantic import field_validator


NAME_ALLOWED_CHARS = re.compile(r"^[A-Za-zÀ-ÖØ-öø-ÿ- ]+$")


class UserBase(SQLModel):
    """common properties"""

    model_config = {
        "alias_generator": camel.case,
        "validate_by_name": True,
        "str_strip_whitespace": True,
        "extra": "forbid",
    }

    firstname: str = Field(
        min_length=1,
        max_length=100,
    )
    lastname: str = Field(
        min_length=1,
        max_length=100,
    )
    date_of_birth: date = Field(alias="dateOfBirth")


class UserCreate(
    UserBase,
):
    """fields required to create a new user"""

    @field_validator("date_of_birth")
    @classmethod
    def _validate_dob(cls, v) -> bool:
        """
        validate the date of birth.
        - must be at least 16 to use the system, just because.
        - must be after 1900.
        """
        min_age = 16  # handily means we can be lazy and not consider leap years
        today = date.today()
        max_date = today.replace(year=today.year - min_age)

        if v > max_date:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"User must be at least {min_age} years old",
            )
        if v < date(1900, 1, 1):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="User must be born on or after 01/01/1900",
            )
        return v

    @field_validator("firstname", "lastname")
    @classmethod
    def _validate_name(cls, v) -> bool:
        """
        Ensure name fields only contain valid characters.
        """
        if not NAME_ALLOWED_CHARS.match(v):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Name must only contain letters, spaces and hyphens",
            )
        return v


class UserPublic(UserBase):
    """user data returned to client"""

    id: uuid.UUID


class User(UserBase, table=True):
    """full User entity"""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now, primary_key=True)
    deleted: bool = Field(default=False)
