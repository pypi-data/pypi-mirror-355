from azure.identity import (
    ChainedTokenCredential,
    ManagedIdentityCredential,
    EnvironmentCredential,
    TokenCachePersistenceOptions,
    get_bearer_token_provider
)

from logging import getLogger
from opentelemetry import trace, baggage
from opentelemetry.propagate import extract

logger = getLogger("__main__")
tracer = trace.get_tracer("__main__")
class AzureIdentityHelper:
    """
    A helper class to provide a chained Azure token credential.
    It prioritizes Managed Identity, then Environment variables.
    Token caching is configured for in-memory persistence.
    """
    def __init__(self):
        # Configure in-memory token cache persistence
        # For in-memory, unencrypted storage is typically allowed for simplicity during development.
        # In production, especially with shared environments, consider the security implications.
        token_cache_options = TokenCachePersistenceOptions(allow_unencrypted_storage=True)

        # Create individual credential instances
        managed_identity_credential = ManagedIdentityCredential(
            token_cache_persistence_options=token_cache_options
        )
        environment_credential = EnvironmentCredential(
            token_cache_persistence_options=token_cache_options
        )

        # Create a chain of credentials
        # The chain will try credentials in the order they are provided.
        self._credential = ChainedTokenCredential(
            managed_identity_credential,
            environment_credential
        )

    def get_credential(self) -> ChainedTokenCredential:
        """
        Returns the configured ChainedTokenCredential.
        """
        with tracer.start_as_current_span("AzureIdentityHelper.get_credential"):
            logger.info("Retrieving ChainedTokenCredential.")
        return self._credential
    
    def get_token(self, scopes):
        """
        Returns the configured ChainedTokenCredential.
        """
        with tracer.start_as_current_span("AzureIdentityHelper.get_token_provider"):
            logger.info("Retrieving ChainedTokenCredential provider.")
        return self._credential.get_token(scopes=scopes)
    
    def get_token_provider(self, scopes):
        """
        Returns the configured ChainedTokenCredential.
        """
        with tracer.start_as_current_span("AzureIdentityHelper.get_token_provider"):
            logger.info("Retrieving ChainedTokenCredential provider.")
        return get_bearer_token_provider(self._credential, scopes=scopes)
    

# Example usage (optional, for testing or demonstration):
if __name__ == "__main__":
    helper = AzureIdentityHelper()
    credential = helper.get_credential()
    print("Successfully created ChainedTokenCredential.")
