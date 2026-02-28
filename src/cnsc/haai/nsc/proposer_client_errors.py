"""
Error Classes for ProposerClient.

Defines the exception hierarchy for the NPE client.
"""


class ProposerClientError(Exception):
    """Base exception for ProposerClient errors.

    All exceptions raised by the ProposerClient inherit from this class.
    """

    def __init__(self, message: str) -> None:
        """Initialize the exception.

        Args:
            message: Error message describing the issue
        """
        super().__init__(message)
        self.message = message

    def __str__(self) -> str:
        """Return string representation."""
        return self.message


class ConnectionError(ProposerClientError):
    """Exception raised when network connection fails.

    This is raised when the client cannot establish a connection
    to the NPE service.
    """

    def __init__(self, message: str) -> None:
        """Initialize the connection error.

        Args:
            message: Error message describing the connection failure
        """
        super().__init__(message)
        self.message = message


class TimeoutError(ProposerClientError):
    """Exception raised when a request times out.

    This is raised when the NPE service does not respond within
    the specified timeout period.
    """

    def __init__(self, message: str) -> None:
        """Initialize the timeout error.

        Args:
            message: Error message describing the timeout
        """
        super().__init__(message)
        self.message = message


class ValidationError(ProposerClientError):
    """Exception raised when input validation fails.

    This is raised when parameters fail validation checks,
    such as invalid domain, candidate_type, or budget values.
    """

    def __init__(self, field: str, message: str) -> None:
        """Initialize the validation error.

        Args:
            field: Name of the field that failed validation
            message: Description of the validation failure
        """
        full_message = f"Validation error in field '{field}': {message}"
        super().__init__(full_message)
        self.field = field
        self.message = full_message

    def __str__(self) -> str:
        """Return string representation."""
        return self.message


class SchemaValidationError(ProposerClientError):
    """Exception raised when schema validation fails.

    This is raised when request or response data fails to validate
    against the JSON schema.
    """

    def __init__(self, schema_path: str, message: str) -> None:
        """Initialize the schema validation error.

        Args:
            schema_path: Path to the schema file used for validation
            message: Description of the schema validation failure
        """
        full_message = f"Schema validation failed against '{schema_path}': {message}"
        super().__init__(full_message)
        self.schema_path = schema_path
        self.message = full_message

    def __str__(self) -> str:
        """Return string representation."""
        return self.message


class SecurityError(ProposerClientError):
    """Exception raised when a security check fails.

    This is raised when security-related checks fail, such as
    rate limiting or suspicious activity detection.
    """

    def __init__(self, message: str) -> None:
        """Initialize the security error.

        Args:
            message: Description of the security violation
        """
        super().__init__(message)
        self.message = message
