from typing import List, Optional

from galtea.utils.string import build_query_params, is_valid_id

from ...domain.models.session import Session, SessionBase
from ...infrastructure.clients.http_client import Client


class SessionService:
    """
    Service for managing Sessions.
    A Session is a group of inference results that make a full conversation between a user and an AI system.
    """

    def __init__(self, client: Client):
        """Initialize the SessionService with the provided HTTP client.

        Args:
            client (Client): The HTTP client for making API requests.
        """
        self._client: Client = client

    def create(
        self,
        version_id: str,
        id: Optional[str] = None,
        test_case_id: Optional[str] = None,
        context: Optional[str] = None,
        is_production: Optional[bool] = None,
    ) -> Session:
        """Create a new session.

        Args:
            version_id (str): The version ID to associate with this session
            id (str, optional): Client-provided session ID (auto-generated if not provided)
            test_case_id (str, optional): The test case ID (implies a test_id)
            context (str, optional): Flexible string context for user-defined information
            is_production (bool, optional): Whether this is a PRODUCTION session or not.
                A PRODUCTION session is the one we create for tracking real-time user interactions.
                Defaults to False.

        Returns:
            Session: The created session object

        Raises:
            ValueError: If is_production is False and test_case_id is None
        """
        if not is_valid_id(version_id):
            raise ValueError("A valid version_id is required to create a session")

        # Construct SessionBase payload
        session_base: SessionBase = SessionBase(
            id=id,
            version_id=version_id,
            test_case_id=test_case_id,
            context=context,
        )

        # Validate the payload

        request_body = session_base.model_dump(by_alias=True, exclude_none=True)
        session_base.model_validate(request_body)

        # Add isProduction to the request body since it's not part of Session entity
        request_body["isProduction"] = is_production

        # Send the request
        response = self._client.post("sessions", json=request_body)

        return Session(**response.json())

    def get(self, session_id: str) -> Session:
        """Get a session by ID.

        Args:
            session_id (str): The session ID to retrieve

        Returns:
            Session: The session object
        """
        response = self._client.get(f"sessions/{session_id}")
        return Session(**response.json())

    def get_or_create(
        self,
        id: str,
        version_id: str,
        test_case_id: Optional[str] = None,
        context: Optional[str] = None,
        is_production: Optional[bool] = False,
    ) -> Session:
        """Get an existing session or create a new one if it doesn't exist.

        Args:
            id (str): The session ID to fetch or create from.
            version_id (str): The version ID to associate with this session
            test_case_id (Optional[str]): The test case ID (implies a test_id)
            context (Optional[str]): Flexible string context for user-defined information
            is_production (bool, optional): Whether this is a production session. Defaults to False.

        Returns:
            Session: The existing or newly created session object
        """
        if not is_valid_id(id):
            raise ValueError("A valid session ID must be provided.")
        if not is_valid_id(version_id):
            raise ValueError("A valid version ID must be provided.")

        try:
            return self.get(id)
        except Exception:
            return self.create(
                id=id,
                version_id=version_id,
                test_case_id=test_case_id,
                context=context,
                is_production=is_production,
            )

    def list(
        self,
        version_id: str,
        test_case_id: Optional[str] = None,
        offset: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[Session]:
        """List sessions with optional filtering.

        Args:
            version_id (str): Filter by version ID
            test_case_id (str, optional): Filter by test case ID
            offset (Optional[int]): Number of results to skip
            limit (Optional[int]): Maximum number of results to return

        Returns:
            List[Session]: List of session objects
        """
        if not is_valid_id(version_id):
            raise ValueError("A valid version ID must be provided.")

        query_params = build_query_params(
            versionIds=[version_id],
            testCaseIds=[test_case_id] if test_case_id else None,
            offset=offset,
            limit=limit,
        )
        response = self._client.get(f"sessions?{query_params}")
        return [Session(**session) for session in response.json()]

    def delete(self, session_id: str) -> None:
        """Delete a session by ID.

        Args:
            session_id (str): The session ID to delete

        Raises:
            ValueError: If the session ID is not valid
        """
        if not is_valid_id(session_id):
            raise ValueError("A valid session ID must be provided.")

        self._client.delete(f"sessions/{session_id}")
