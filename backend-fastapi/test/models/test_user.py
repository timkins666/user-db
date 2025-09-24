"""User class tests"""

from contextlib import nullcontext
from datetime import date
from unittest import mock
from pydantic import ValidationError
import pytest
from fastapi import HTTPException

from userdb.models import user as sut


class TestUserCreate:
    """Tests for UserCreate"""

    def test_validate_success(self):
        """validate with valid data"""
        user = sut.UserCreate(firstname="x", lastname="y", dateOfBirth=date(2000, 1, 1))

        assert user.firstname == user.firstname
        assert user.lastname == user.lastname
        assert user.date_of_birth == user.date_of_birth

    def test_model_strips_name_whitespace(self):
        """model strips whitespace from strings"""
        user = sut.UserCreate(
            firstname=" x ", lastname=" \t y \n", dateOfBirth=date(2000, 1, 1)
        )

        assert user.firstname == "x"
        assert user.lastname == "y"
        assert user.date_of_birth == user.date_of_birth

    @pytest.mark.parametrize(
        "dob, valid", [(date(1899, 12, 31), False), (date(1900, 1, 1), True)]
    )
    def test_validate_too_old(self, dob: date, valid: bool):
        """validate with dob before 1900"""

        with (
            pytest.raises(HTTPException, match=r"01/01/1900")
            if not valid
            else nullcontext()
        ):
            result = sut.UserCreate(firstname="x", lastname="y", dateOfBirth=dob)

        if valid:
            assert result.date_of_birth == dob

    @pytest.mark.parametrize(
        "birth_date, valid",
        [
            (1, True),
            (2, False),
        ],
    )
    @mock.patch.object(sut, "date")
    def test_validate_too_young(self, mock_date, birth_date: int, valid: bool):
        """validate with age < 16"""
        mock_date.today.return_value = date(2016, 1, 1)
        mock_date.side_effect = date

        with (
            pytest.raises(HTTPException, match=r"at least 16")
            if not valid
            else nullcontext()
        ):
            result = sut.UserCreate(
                firstname="x", lastname="y", dateOfBirth=date(2000, 1, birth_date)
            )

        if valid:
            assert result.date_of_birth == date(2000, 1, birth_date)

    @pytest.mark.parametrize(
        "firstname, lastname",
        [
            ("Christopher", "Lee"),
            ("Chris topher", "Lëèéê"),
            ("Öäöü-Öäöü", "Öäöü Öäöü Öäöü"),
        ],
    )
    def test_validate_names_valid(self, firstname: str, lastname: str):
        """validate with valid names"""
        _ = sut.UserCreate(
            firstname=firstname, lastname=lastname, dateOfBirth=date(2000, 1, 1)
        )

    @pytest.mark.parametrize(
        "firstname, lastname",
        [("Chris_topher", "Lee"), ("Christopher", "L3e")],
    )
    def test_validate_names_invalid_chars(self, firstname: str, lastname: str):
        """validate with valid names"""

        with pytest.raises(HTTPException, match="must only contain"):
            _ = sut.UserCreate(
                firstname=firstname, lastname=lastname, dateOfBirth=date(2000, 1, 1)
            )

    @pytest.mark.parametrize(
        "firstname, lastname, error",
        [
            (None, "y", "should be a valid string"),
            ("x", None, "should be a valid string"),
            ("", "y", "string_too_short"),
            ("x", "", "string_too_short"),
            ("x" * 101, "y", "string_too_long"),
            ("x", "y" * 101, "string_too_long"),
        ],
    )
    def test_validate_names_error(self, firstname: str, lastname: str, error: str):
        """validate with valid names"""

        with pytest.raises(ValidationError, match=error):
            _ = sut.UserCreate(
                firstname=firstname, lastname=lastname, dateOfBirth=date(2000, 1, 1)
            )
