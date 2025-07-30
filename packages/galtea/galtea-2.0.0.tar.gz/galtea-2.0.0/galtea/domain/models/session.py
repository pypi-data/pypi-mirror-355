from typing import Optional

from ...utils.from_camel_case_base_model import FromCamelCaseBaseModel


class SessionBase(FromCamelCaseBaseModel):
    """Base model for creating a new session."""

    id: Optional[str] = None  # client-provided or auto-generated
    version_id: Optional[str] = None
    test_case_id: Optional[str] = None  # implies a test_id
    context: Optional[str] = None  # flexible string context for user-defined information


class Session(SessionBase):
    """Complete session model returned from the API."""

    id: str
    created_at: str
    deleted_at: Optional[str] = None
