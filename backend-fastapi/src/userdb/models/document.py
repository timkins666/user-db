"""document model classes"""

import re
from humps import camel
from pydantic import BaseModel, Field


NAME_ALLOWED_CHARS = re.compile(r"^[A-Za-zÀ-ÖØ-öø-ÿ- ]+$")


class DocumentBase(BaseModel):
    """common properties"""

    model_config = {
        "alias_generator": camel.case,
        "validate_by_name": True,
        "str_strip_whitespace": True,
        "extra": "forbid",
    }

    filename: str = Field(min_length=1)
    content_type: str = Field(
        min_length=1,
        max_length=30,
    )


class DocumentPresignRequest(
    DocumentBase,
):
    """fields required to create a presign request"""


class DocumentPresignResponse(BaseModel):
    """presign url data returned to client"""

    model_config = {
        "alias_generator": camel.case,
        "validate_by_name": True,
    }

    upload_url: str
    upload_id: str
