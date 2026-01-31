"""tests for routers/users.py module"""

from datetime import date, timedelta
import json
import uuid
from fastapi.testclient import TestClient
from fastapi import status
import pytest
from sqlmodel import Session, select

from test.conftest import create_user
from userdb.models.user import User

public_user_keys = {
    "id",
    "firstname",
    "lastname",
    "dateOfBirth",
}


class TestUsersRouter:
    """test user handlers"""

    @pytest.fixture(autouse=True)
    def _set_auth_header(self, app: TestClient, access_token):
        """sets the auth header on the app for all tests in this class"""
        app.headers["Authorization"] = f"Bearer {access_token}"

    def new_user_data(self, **kwargs):
        """valid new user request data"""
        return {
            "firstname": "Test",
            "lastname": "uSEr",
            "dateOfBirth": "2001-02-03",
        } | kwargs

    def test_get_all_users_none_created(self, app: TestClient):
        """test get all users when none exist"""
        response = app.get("/users")
        assert response.text == "[]"

    def test_get_all_users(self, app: TestClient, session: Session):
        """test get all users"""

        num_users = 3

        for i in range(num_users):
            create_user(
                User(
                    firstname=f"user{i}",
                    lastname="ln",
                    date_of_birth=date(2000 + i, 2, 3),
                    deleted=i == 1,
                ),
                session,
            )

        response = app.get("/users")

        assert response.status_code == 200

        users = json.loads(response.text)
        assert [u["firstname"] for u in users] == ["user0", "user2"]
        assert [u["dateOfBirth"][0:4] for u in users] == ["2000", "2002"]

        for user in users:
            # check only contains above expected keys
            assert set(user) == public_user_keys

    def test_create_user_success(self, app: TestClient):
        """test create a user"""

        response = app.post("/users/create", json={"user": self.new_user_data()})

        assert response.status_code == 200

        new_user = json.loads(response.text)
        assert new_user["firstname"] == "Test"
        assert new_user["lastname"] == "uSEr"
        assert new_user["dateOfBirth"] == "2001-02-03"
        assert uuid.UUID(new_user["id"]).version == 4

        assert set(new_user) == public_user_keys

    @pytest.mark.parametrize(
        "dob",
        [
            pytest.param("1850-02-03", id="too old"),
            pytest.param(
                (date.today() - timedelta(weeks=520)).isoformat(), id="too young"
            ),
        ],
    )
    def test_create_user_bad_dob(self, app: TestClient, dob: str):
        """test creating a user with invalid date of birth"""

        response = app.post(
            "/users/create", json={"user": self.new_user_data(dateOfBirth=dob)}
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_create_user_fail_if_id_in_request(self, app: TestClient):
        """test create a user"""

        user_data = {
            **self.new_user_data(),
            "id": str(uuid.uuid4()),
        }

        response = app.post("/users/create", json={"user": user_data})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

        assert "extra_forbidden" in response.text
        assert user_data["id"] in response.text

    def test_delete_user(self, app: TestClient, session: Session):
        """test delete a user"""

        # sqlite needs python date object
        user = create_user(
            User(**self.new_user_data(dateOfBirth=date(2000, 2, 3))), session
        )

        assert len(session.exec(select(User)).all()) == 1
        assert session.exec(select(User)).one().deleted is False

        delete_response = app.delete(f"/user/{user.id}")

        assert delete_response.status_code == status.HTTP_204_NO_CONTENT

        assert len(session.exec(select(User)).all()) == 1
        assert session.exec(select(User)).one().deleted is True

    def test_delete_user_invalid_id_format(self, app: TestClient):
        """test deleting a user with invaild id format"""

        response = app.delete("/user/123")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_delete_user_unknown_id(self, app: TestClient):
        """test delete a non-existent user"""

        response = app.delete(f"/user/{uuid.uuid4()}")

        assert response.status_code == status.HTTP_204_NO_CONTENT
