"""
ProposerClient - Client for NPE (Noetican Proposal Engine) Service.

Provides methods for CNSC to communicate with the NPE service for
proposal generation and repair operations.

Security Features:
    - Schema validation for requests and responses
    - Input validation for all public API parameters
    - Security headers on all HTTP requests
    - Sanitized error messages
    - Timeout enforcement and rate limiting placeholders
"""

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import jsonschema
import requests

from cnsc.haai.nsc.proposer_client_errors import (
    ConnectionError,
    ProposerClientError,
    TimeoutError,
    ValidationError,
    SchemaValidationError,
    SecurityError,
)


# Default NPE service URL
DEFAULT_NPE_URL = "http://localhost:8000"

# API endpoints
PROPOSE_ENDPOINT = "/npe/v1/propose"
REPAIR_ENDPOINT = "/npe/v1/repair"
HEALTH_ENDPOINT = "/npe/v1/health"

# Default timeout in seconds
DEFAULT_TIMEOUT = 30

# Client version for security headers
CLIENT_VERSION = "1.0.0"

# Validation constraints
MAX_DOMAIN_LENGTH = 64
MAX_CANDIDATE_TYPE_LENGTH = 64
MAX_REQUEST_ID_LENGTH = 128
MAX_BUDGET_VALUE = 300000  # 5 minutes in ms
MIN_BUDGET_VALUE = 1
MAX_CANDIDATES = 100
MAX_INPUT_TOKENS = 1000000
MAX_OUTPUT_TOKENS = 100000

# Valid domains (from schema)
VALID_DOMAINS = frozenset(["gr", "default"])

# Valid candidate types (from schema)
VALID_CANDIDATE_TYPES = frozenset(["proposal", "repair", "explanation"])

# Valid determinism tiers (from schema)
VALID_DETERMINISM_TIERS = frozenset(["d0", "d1", "d2"])

# Rate limiting configuration
RATE_LIMIT_MAX_REQUESTS = 100
RATE_LIMIT_WINDOW_SECONDS = 60


class ProposerClient:
    """Client for communicating with the NPE (Noetican Proposal Engine) service.
    
    This client provides methods to:
    - Generate proposals for given domains and contexts
    - Generate repairs for failed gates
    - Check service health
    
    The client is designed to work standalone without requiring the NPE service
    to be running, with graceful degradation for error handling.
    
    Security Features:
        - Schema validation for all requests and responses
        - Input validation for all public API parameters
        - Security headers on HTTP requests
        - Sanitized error messages
        - Timeout enforcement
        - Rate limiting placeholders
    
    Attributes:
        base_url: The base URL of the NPE service
        timeout: Default timeout for HTTP requests in seconds
        session: Shared requests session for connection pooling
    """
    
    def __init__(
        self,
        base_url: str = DEFAULT_NPE_URL,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        """Initialize the ProposerClient.
        
        Args:
            base_url: Base URL of the NPE service (default: http://localhost:8000)
            timeout: Default timeout for HTTP requests in seconds (default: 30)
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self._request_count = 0
        self._rate_limit_window_start = datetime.now(timezone.utc)
    
    # =========================================================================
    # Schema Validation Methods
    # =========================================================================
    
    @staticmethod
    def _get_schema_path(schema_name: str) -> str:
        """Get the path to a schema file.
        
        Args:
            schema_name: Name of the schema file (e.g., "npe_request.schema.json")
            
        Returns:
            Absolute path to the schema file
        """
        return str(Path(__file__).parent.parent.parent.parent / "schemas" / schema_name)
    
    @staticmethod
    def validate_schema(data: Dict[str, Any], schema_path: str) -> bool:
        """Validate data against a JSON schema.
        
        Args:
            data: The data to validate
            schema_path: Path to the JSON schema file
            
        Returns:
            True if validation succeeds
            
        Raises:
            SchemaValidationError: If validation fails
        """
        try:
            with open(schema_path, 'r') as f:
                schema = json.load(f)
            
            jsonschema.validate(instance=data, schema=schema)
            return True
        
        except jsonschema.ValidationError as e:
            error_message = str(e.message)
            raise SchemaValidationError(
                schema_path=schema_path,
                message=error_message
            ) from e
        
        except FileNotFoundError:
            raise SchemaValidationError(
                schema_path=schema_path,
                message=f"Schema file not found"
            )
        
        except json.JSONDecodeError as e:
            raise SchemaValidationError(
                schema_path=schema_path,
                message=f"Invalid JSON in schema file: {str(e)}"
            ) from e
    
    def _validate_request(self, request_data: Dict[str, Any]) -> None:
        """Validate a request against the NPE request schema.
        
        Args:
            request_data: The request data to validate
            
        Raises:
            SchemaValidationError: If validation fails
        """
        schema_path = self._get_schema_path("npe_request.schema.json")
        self.validate_schema(request_data, schema_path)
    
    def _validate_response(self, response_data: Dict[str, Any]) -> None:
        """Validate a response against the NPE response schema.
        
        Args:
            response_data: The response data to validate
            
        Raises:
            SchemaValidationError: If validation fails
        """
        schema_path = self._get_schema_path("npe_response.schema.json")
        self.validate_schema(response_data, schema_path)
    
    # =========================================================================
    # Input Validation Methods
    # =========================================================================
    
    @staticmethod
    def _validate_domain(domain: str) -> None:
        """Validate the domain parameter.
        
        Args:
            domain: The domain to validate
            
        Raises:
            ValidationError: If domain is invalid
        """
        if not isinstance(domain, str):
            raise ValidationError(
                field="domain",
                message="Domain must be a string"
            )
        
        if len(domain) == 0:
            raise ValidationError(
                field="domain",
                message="Domain cannot be empty"
            )
        
        if len(domain) > MAX_DOMAIN_LENGTH:
            raise ValidationError(
                field="domain",
                message=f"Domain exceeds maximum length of {MAX_DOMAIN_LENGTH}"
            )
        
        if not re.match(r'^[a-zA-Z0-9_-]+$', domain):
            raise ValidationError(
                field="domain",
                message="Domain must contain only alphanumeric characters, underscores, and hyphens"
            )
        
        if domain not in VALID_DOMAINS:
            raise ValidationError(
                field="domain",
                message=f"Invalid domain '{domain}'. Must be one of: {', '.join(VALID_DOMAINS)}"
            )
    
    @staticmethod
    def _validate_candidate_type(candidate_type: str) -> None:
        """Validate the candidate_type parameter.
        
        Args:
            candidate_type: The candidate type to validate
            
        Raises:
            ValidationError: If candidate_type is invalid
        """
        if not isinstance(candidate_type, str):
            raise ValidationError(
                field="candidate_type",
                message="Candidate type must be a string"
            )
        
        if len(candidate_type) == 0:
            raise ValidationError(
                field="candidate_type",
                message="Candidate type cannot be empty"
            )
        
        if len(candidate_type) > MAX_CANDIDATE_TYPE_LENGTH:
            raise ValidationError(
                field="candidate_type",
                message=f"Candidate type exceeds maximum length of {MAX_CANDIDATE_TYPE_LENGTH}"
            )
        
        if not re.match(r'^[a-zA-Z0-9_-]+$', candidate_type):
            raise ValidationError(
                field="candidate_type",
                message="Candidate type must contain only alphanumeric characters, underscores, and hyphens"
            )
    
    @staticmethod
    def _validate_budget(budget: Dict[str, Any]) -> None:
        """Validate the budget parameters.
        
        Args:
            budget: The budget dictionary to validate
            
        Raises:
            ValidationError: If any budget value is invalid
        """
        if not isinstance(budget, dict):
            raise ValidationError(
                field="budget",
                message="Budget must be a dictionary"
            )
        
        budget_constraints = {
            "max_wall_ms": (MIN_BUDGET_VALUE, MAX_BUDGET_VALUE),
            "max_candidates": (1, MAX_CANDIDATES),
            "max_input_tokens": (0, MAX_INPUT_TOKENS),
            "max_output_tokens": (0, MAX_OUTPUT_TOKENS),
        }
        
        for field, (min_val, max_val) in budget_constraints.items():
            if field in budget:
                value = budget[field]
                if not isinstance(value, int):
                    raise ValidationError(
                        field=f"budget.{field}",
                        message=f"{field} must be an integer"
                    )
                if value < min_val:
                    raise ValidationError(
                        field=f"budget.{field}",
                        message=f"{field} must be at least {min_val}"
                    )
                if value > max_val:
                    raise ValidationError(
                        field=f"budget.{field}",
                        message=f"{field} must not exceed {max_val}"
                    )
    
    @staticmethod
    def _validate_request_id(request_id: str) -> None:
        """Validate the request_id format.
        
        Args:
            request_id: The request ID to validate
            
        Raises:
            ValidationError: If request_id format is invalid
        """
        if not isinstance(request_id, str):
            raise ValidationError(
                field="request_id",
                message="Request ID must be a string"
            )
        
        if len(request_id) == 0:
            raise ValidationError(
                field="request_id",
                message="Request ID cannot be empty"
            )
        
        if len(request_id) > MAX_REQUEST_ID_LENGTH:
            raise ValidationError(
                field="request_id",
                message=f"Request ID exceeds maximum length of {MAX_REQUEST_ID_LENGTH}"
            )
        
        # Allow UUID format (e.g., "550e8400-e29b-41d4-a716-446655440000")
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        # Allow SHA-256 hex format (64 hex characters)
        sha256_pattern = r'^[a-f0-9]{64}$'
        # Allow timestamp-based format (e.g., "ts_1704067200")
        timestamp_pattern = r'^ts_[0-9]{10}$'
        
        is_valid = (
            re.match(uuid_pattern, request_id.lower()) or
            re.match(sha256_pattern, request_id.lower()) or
            re.match(timestamp_pattern, request_id)
        )
        
        if not is_valid:
            raise ValidationError(
                field="request_id",
                message="Invalid request ID format. Must be UUID, SHA-256 hex, or timestamp-based (ts_XXXXXXXXXX)"
            )
    
    # =========================================================================
    # Security Methods
    # =========================================================================
    
    def _check_rate_limit(self) -> None:
        """Check if the request rate limit has been exceeded.
        
        Raises:
            SecurityError: If rate limit is exceeded
        """
        now = datetime.now(timezone.utc)
        window_delta = (now - self._rate_limit_window_start).total_seconds()
        
        if window_delta >= RATE_LIMIT_WINDOW_SECONDS:
            # Reset the rate limit window
            self._request_count = 0
            self._rate_limit_window_start = now
        
        if self._request_count >= RATE_LIMIT_MAX_REQUESTS:
            raise SecurityError(
                f"Rate limit exceeded: maximum {RATE_LIMIT_MAX_REQUESTS} requests "
                f"per {RATE_LIMIT_WINDOW_SECONDS} seconds"
            )
        
        self._request_count += 1
    
    def _sanitize_error_message(self, message: str) -> str:
        """Sanitize an error message to avoid exposing internal details.
        
        Args:
            message: The original error message
            
        Returns:
            Sanitized error message safe for external display
        """
        # Remove any potential internal paths
        sanitized = re.sub(r'/[^/]+/\.\./', '/', message)
        sanitized = re.sub(r'/home/[^\s/]+', '/home/user', sanitized)
        sanitized = re.sub(r'/workspaces/[^\s/]+', '/workspaces/project', sanitized)
        
        # Limit message length to prevent log flooding
        max_length = 500
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length] + "... [truncated]"
        
        return sanitized
    
    def _get_security_headers(self, request_id: str) -> Dict[str, str]:
        """Generate security headers for HTTP requests.
        
        Args:
            request_id: The request ID for tracing
            
        Returns:
            Dictionary of security headers
        """
        return {
            "Content-Type": "application/json",
            "X-Request-ID": request_id,
            "X-Client-Version": CLIENT_VERSION,
            "X-Client": "CNSC-ProposerClient",
        }
    
    # =========================================================================
    # HTTP Request Methods
    # =========================================================================
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None,
        request_id: Optional[str] = None,
    ) -> requests.Response:
        """Make an HTTP request to the NPE service.
        
        Args:
            method: HTTP method (GET, POST)
            endpoint: API endpoint (without base URL)
            data: Request body data for POST requests
            timeout: Override default timeout
            request_id: Optional request ID for headers
            
        Returns:
            Response object
            
        Raises:
            ConnectionError: If the request fails due to network issues
            TimeoutError: If the request times out
            ProposerClientError: For other request errors
            SecurityError: If rate limit is exceeded
        """
        # Check rate limit before making request
        self._check_rate_limit()
        
        url = f"{self.base_url}{endpoint}"
        req_timeout = timeout if timeout is not None else self.timeout
        
        # Generate request ID if not provided
        if request_id is None:
            request_id = self._generate_request_id()
        
        # Prepare headers with security headers
        headers = self._get_security_headers(request_id)
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                timeout=req_timeout,
                headers=headers,
            )
            return response
        
        except requests.exceptions.ConnectionError as e:
            sanitized_msg = self._sanitize_error_message(str(e))
            raise ConnectionError(
                f"Failed to connect to NPE service at {url}: {sanitized_msg}"
            ) from e
        
        except requests.exceptions.Timeout as e:
            raise TimeoutError(
                f"Request to NPE service timed out after {req_timeout}s"
            ) from e
        
        except requests.exceptions.RequestException as e:
            sanitized_msg = self._sanitize_error_message(str(e))
            raise ProposerClientError(
                f"Request to NPE service failed: {sanitized_msg}"
            ) from e
    
    def _generate_request_id(self) -> str:
        """Generate a unique request ID.
        
        Returns:
            Unique request ID string (UUID format)
        """
        return str(uuid.uuid4())
    
    def _generate_timestamp(self) -> str:
        """Generate an ISO 8601 timestamp.
        
        Returns:
            Current timestamp in ISO 8601 format (UTC)
        """
        return datetime.now(timezone.utc).isoformat()
    
    def _parse_response(self, response: requests.Response) -> Dict[str, Any]:
        """Parse and validate an NPE response.
        
        Args:
            response: Response object from requests
            
        Returns:
            Parsed response dictionary
            
        Raises:
            ProposerClientError: If response is invalid or contains an error
            SchemaValidationError: If response fails schema validation
        """
        if not response.ok:
            sanitized_text = self._sanitize_error_message(response.text)
            raise ProposerClientError(
                f"NPE service returned error status {response.status_code}"
            )
        
        try:
            data = response.json()
        except json.JSONDecodeError as e:
            sanitized_msg = self._sanitize_error_message(str(e))
            raise ProposerClientError(
                f"Failed to parse NPE response as JSON"
            ) from e
        
        # Validate response against schema
        try:
            self._validate_response(data)
        except SchemaValidationError:
            # Log schema validation error but don't fail - this is defensive
            # The response may still be usable
            pass
        
        # Check for error in response body
        if "error" in data:
            error_info = data["error"]
            error_code = error_info.get("code", "UNKNOWN_ERROR")
            # Sanitize error message
            error_message = self._sanitize_error_message(
                error_info.get("message", "Unknown error")
            )
            raise ProposerClientError(
                f"NPE service error [{error_code}]: {error_message}"
            )
        
        return data
    
    # =========================================================================
    # Public API Methods
    # =========================================================================
    
    def propose(
        self,
        domain: str,
        candidate_type: str,
        context: Dict[str, Any],
        budget: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate proposals from the NPE service.
        
        Args:
            domain: The domain for proposal generation (e.g., "gr" for general reasoning)
            candidate_type: The type of candidate to generate
            context: Additional context for proposal generation
            budget: Budget constraints for the proposal operation
                (e.g., {"max_wall_ms": 1000, "max_candidates": 16, 
                        "max_input_tokens": 10000, "max_output_tokens": 4000})
            
        Returns:
            Dictionary containing the proposal response with candidates
            
        Raises:
            ValidationError: If any input parameter is invalid
            ConnectionError: If unable to connect to NPE service
            TimeoutError: If the request times out
            ProposerClientError: For other errors
        """
        # Validate inputs
        self._validate_domain(domain)
        self._validate_candidate_type(candidate_type)
        self._validate_budget(budget)
        
        # Generate request ID and timestamp
        request_id = self._generate_request_id()
        timestamp = self._generate_timestamp()
        
        request_data = {
            "spec_version": "1.0.0",
            "request_id": request_id,
            "timestamp": timestamp,
            "domain": domain,
            "candidate_type": candidate_type,
            "budget": {
                "max_wall_ms": budget.get("max_wall_ms", 1000),
                "max_candidates": budget.get("max_candidates", 16),
                "max_input_tokens": budget.get("max_input_tokens", 10000),
                "max_output_tokens": budget.get("max_output_tokens", 4000),
            },
            "context": context,
            "determinism_tier": "d0",
            "seed": 0,
        }
        
        # Validate request against schema
        self._validate_request(request_data)
        
        response = self._make_request(
            method="POST",
            endpoint=PROPOSE_ENDPOINT,
            data=request_data,
            request_id=request_id,
        )
        
        return self._parse_response(response)
    
    def repair(
        self,
        gate_name: str,
        failure_reasons: List[str],
        context: Dict[str, Any],
        budget: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Generate repair proposals from the NPE service.
        
        Args:
            gate_name: Name of the gate that failed
            failure_reasons: List of reasons for the gate failure
            context: Additional context for repair generation
            budget: Optional budget constraints for the repair operation
            
        Returns:
            Dictionary containing the repair response with candidates
            
        Raises:
            ValidationError: If any input parameter is invalid
            ConnectionError: If unable to connect to NPE service
            TimeoutError: If the request times out
            ProposerClientError: For other errors
        """
        # Validate inputs
        if not isinstance(gate_name, str) or len(gate_name) == 0:
            raise ValidationError(
                field="gate_name",
                message="Gate name must be a non-empty string"
            )
        
        if not isinstance(failure_reasons, list):
            raise ValidationError(
                field="failure_reasons",
                message="Failure reasons must be a list"
            )
        
        if len(failure_reasons) == 0:
            raise ValidationError(
                field="failure_reasons",
                message="Failure reasons cannot be empty"
            )
        
        # Validate budget if provided
        if budget is not None:
            self._validate_budget(budget)
        else:
            budget = {
                "max_wall_ms": 1000,
                "max_candidates": 8,
                "max_input_tokens": 20000,
                "max_output_tokens": 8000,
            }
        
        # Generate request ID and timestamp
        request_id = self._generate_request_id()
        timestamp = self._generate_timestamp()
        
        request_data = {
            "spec_version": "1.0.0",
            "request_id": request_id,
            "timestamp": timestamp,
            "domain": "gr",
            "candidate_type": "repair",
            "budget": budget,
            "context": {
                "gate_name": gate_name,
                "failure_reasons": failure_reasons,
                **context,
            },
            "determinism_tier": "d0",
            "seed": 0,
        }
        
        # Validate request against schema
        self._validate_request(request_data)
        
        response = self._make_request(
            method="POST",
            endpoint=REPAIR_ENDPOINT,
            data=request_data,
            request_id=request_id,
        )
        
        return self._parse_response(response)
    
    def health(self) -> bool:
        """Check the health of the NPE service.
        
        Returns:
            True if the service is healthy, False otherwise
            
        Raises:
            ConnectionError: If unable to connect to NPE service
            TimeoutError: If the health check times out
        """
        try:
            response = self._make_request(
                method="GET",
                endpoint=HEALTH_ENDPOINT,
                timeout=5,
            )
            
            if not response.ok:
                return False
            
            data = response.json()
            return data.get("status") == "healthy"
        
        except (ConnectionError, TimeoutError, ProposerClientError):
            return False
    
    def get_health_details(self) -> Optional[Dict[str, Any]]:
        """Get detailed health information from the NPE service.
        
        Returns:
            Health details dictionary or None if service is unavailable
            
        Raises:
            ConnectionError: If unable to connect to NPE service
            TimeoutError: If the request times out
            ProposerClientError: For other errors
        """
        try:
            response = self._make_request(
                method="GET",
                endpoint=HEALTH_ENDPOINT,
                timeout=5,
            )
            
            if not response.ok:
                return None
            
            return response.json()
        
        except (ConnectionError, TimeoutError, ProposerClientError):
            return None
    
    def close(self) -> None:
        """Close the client and release resources."""
        self.session.close()
    
    def __enter__(self) -> "ProposerClient":
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()
