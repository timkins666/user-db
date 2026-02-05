"""Handy response classes"""

from typing import Any, Generic, Optional, TypeVar

from fastapi.responses import JSONResponse
from humps import camel
from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class SuccessResult(BaseModel, Generic[T]):
    """Standardised response indicating success with optional typed payload."""

    model_config = ConfigDict(
        json_encoders={object: str},
        ser_json_timedelta="float",
        ser_json_bytes="base64",
        alias_generator=camel.case,
        populate_by_name=True,
        str_strip_whitespace=True,
    )

    success: bool
    payload: Optional[T] = None

    def response(self, status_code=200):
        """Return a JSONResponse with the payload dumped to JSON."""
        return JSONResponse(self.model_dump(mode="json"), status_code=status_code)

    def model_dump(self, **kwargs: Any) -> dict[str, Any]:
        """Dump model to dict, using aliases by default and recursing through nested models."""
        kwargs.setdefault("by_alias", True)
        kwargs.setdefault("mode", "json")
        return super().model_dump(**kwargs)
