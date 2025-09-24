"""user http handlers"""

from typing import Annotated
import uuid
from fastapi import APIRouter, Body, Path, status
from sqlmodel import select

from userdb.db import SessionDep
from userdb.models.user import User, UserCreate, UserPublic

router = APIRouter()


@router.get(
    "/users",
    response_model=list[UserPublic],
    summary="Return all users from the database",
)
async def get_all_users(session: SessionDep):
    """get all non-deleted users"""
    # pylint: disable=singleton-comparison
    return session.exec(select(User).where(User.deleted == False)).all()


@router.post(
    "/users/create",
    response_model=UserPublic,
    summary="Create a new user",
)
async def create_user(
    user: Annotated[UserCreate, Body(embed=True)],
    session: SessionDep,
):
    """
    Create a user
    """
    db_user = User.model_validate(user)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


@router.delete(
    "/user/{user_id}",
    summary="Delete the specified user id",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_user(
    user_id: Annotated[uuid.UUID, Path(title="The ID of the user to delete")],
    session: SessionDep,
):
    """soft deletes a user"""
    statement = select(User).where(User.id == user_id)
    results = session.exec(statement)
    user = results.first()

    if not user:
        # probably deleted by someone else but would add logging
        return

    user.deleted = True
    session.commit()
