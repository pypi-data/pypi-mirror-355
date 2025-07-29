import os
from azure.identity import (
    ChainedTokenCredential,
    ManagedIdentityCredential,
    EnvironmentCredential,
    TokenCachePersistenceOptions,
    get_bearer_token_provider,
    DefaultAzureCredential
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
        client_secret_available =  os.getenv("AZURE_CLIENT_SECRET") is not None
        
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
        if client_secret_available:
            logger.info("Using Environment Credential first with token cache persistence.")
            self._credential = ChainedTokenCredential(
                environment_credential,
                managed_identity_credential
            )
        else:
            logger.info("Using Managed Identity Credential first with token cache persistence.")
            # self._credential = ChainedTokenCredential(

            #     managed_identity_credential,
            #     environment_credential
            # )
            self._credential = DefaultAzureCredential(
                token_cache_persistence_options=token_cache_options
            )

    def get_credential(self):
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
        return self._credential.get_token(scopes)
    
    def get_token_provider(self, scopes):
        """
        Returns the configured ChainedTokenCredential.
        """
        with tracer.start_as_current_span("AzureIdentityHelper.get_token_provider"):
            logger.info("Retrieving ChainedTokenCredential provider.")
        return get_bearer_token_provider(self._credential, scopes)
