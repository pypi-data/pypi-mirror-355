"""Session management for the MontyCloud DAY2 SDK."""

import logging
from typing import TYPE_CHECKING, Any, Dict, Optional, TypeVar, cast

from day2.auth.credentials import Credentials
from day2.client.config import Config

if TYPE_CHECKING:
    from day2.resources.assessment import AssessmentClient
    from day2.resources.cost import CostClient
    from day2.resources.tenant import TenantClient

T = TypeVar("T")

logger = logging.getLogger(__name__)


class Session:
    """Session for interacting with the MontyCloud API.

    The Session manages authentication credentials, tenant context, and client creation.
    It provides access to all DAY2 API resources through dedicated client properties.

    Attributes:
        credentials: Authentication credentials for API access.
        tenant_id: Current tenant ID context for API operations.

    Examples:
        Create a session with API credentials:

        >>> session = Session(api_key="your-api-key", api_secret_key="your-secret-key")
        >>> tenants = session.tenant.list_tenants()

        Create a session with custom configuration:

        >>> config = Config(timeout=60, max_retries=5)
        >>> session = Session(api_key="key", api_secret_key="secret", config=config)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret_key: Optional[str] = None,
        credentials: Optional[Credentials] = None,
        tenant_id: Optional[str] = None,
        config: Optional[Config] = None,
    ) -> None:
        """Initialize a new session.

        Args:
            api_key: API key for authentication. If not provided, will attempt to load
                from environment variables or configuration file.
            api_secret_key: API secret key for authentication. Required if api_key is provided.
            credentials: Pre-configured Credentials object. Takes precedence over api_key/api_secret_key.
            tenant_id: Default tenant ID for API operations. Can be changed later with set_tenant().
            config: Configuration object with API settings. If not provided, loads from file or uses defaults.

        Raises:
            ValueError: If api_key is provided without api_secret_key.
            AuthenticationError: If no valid credentials are found.
        """
        # Initialize credentials
        if credentials:
            self.credentials = credentials
        else:
            self.credentials = Credentials(
                api_key=api_key, api_secret_key=api_secret_key
            )

        # Initialize configuration
        self._config = config or Config.from_file()

        # Use tenant_id from parameters, or from config file
        self.tenant_id: Optional[str] = tenant_id or self._config.tenant_id
        self._clients: Dict[str, Any] = {}

        logger.debug("Initialized session with tenant_id=%s", self.tenant_id)

    def _save_tenant_to_config(self) -> None:
        """Save tenant ID to configuration file."""
        if not self.tenant_id:
            return

        # Create a Config object with the current tenant_id
        config = Config(tenant_id=self.tenant_id)

        # Save to the config file
        config.save_to_file()

    def client(self, service_name: str) -> Any:
        """Get a service client for the specified service.

        Args:
            service_name: Name of the service to get a client for.

        Returns:
            Client for the specified service.

        Raises:
            ValueError: If the specified service is not supported.
        """
        if service_name not in self._clients:
            self._clients[service_name] = self._create_client(service_name)

        return self._clients[service_name]

    @property
    def tenant(self) -> "TenantClient":
        """Get the tenant client.

        Returns:
            TenantClient: The tenant client.
        """
        return cast("TenantClient", self.client("tenant"))

    @property
    def assessment(self) -> "AssessmentClient":
        """Get the assessment client.

        Returns:
            AssessmentClient: The assessment client.
        """
        return cast("AssessmentClient", self.client("assessment"))

    @property
    def cost(self) -> "CostClient":
        """Get the cost client.

        Returns:
            CostClient: The cost client.
        """
        return cast("CostClient", self.client("cost"))

    def _create_client(self, service_name: str) -> Any:
        """Create a client for the specified service.

        Args:
            service_name: Name of the service to create a client for.

        Returns:
            Client for the specified service.

        Raises:
            ValueError: If the specified service is not supported.
        """
        # Import the actual classes at runtime to avoid circular imports
        from day2.resources.assessment import AssessmentClient
        from day2.resources.cost import CostClient
        from day2.resources.tenant import TenantClient

        service_map = {
            "tenant": TenantClient,
            "assessment": AssessmentClient,
            "cost": CostClient,
        }

        if service_name not in service_map:
            raise ValueError(f"Unsupported service: {service_name}")

        return service_map[service_name](self)

    def set_tenant(self, tenant_id: str) -> None:
        """Set the current tenant context.

        Args:
            tenant_id: Tenant ID to set as the current context.
        """
        logger.debug("Setting tenant context to %s", tenant_id)
        self.tenant_id = tenant_id

        # Save tenant ID to config
        self._save_tenant_to_config()

        # Invalidate existing clients to ensure they use the new tenant
        self._clients = {}

    def clear_tenant(self) -> None:
        """Clear the current tenant context."""
        logger.debug("Clearing tenant context")
        self.tenant_id = None

        # Save tenant ID to config (will remove it)
        self._save_tenant_to_config()

        # Invalidate existing clients to ensure they use the new tenant
        self._clients = {}
