import redis.asyncio as aioredis # Use the async version of the redis library
from typing import Optional, Any, AsyncGenerator
import json # For serializing/deserializing complex objects if stored in Redis

from app.core.config import settings


class RedisClient:
    _client: Optional[aioredis.Redis] = None
    _instance: Optional['RedisClient'] = None # For singleton pattern via dependency

    def __init__(self, client: aioredis.Redis):
        # This constructor is primarily for the dependency to pass the initialized client
        if RedisClient._client is None : # Ensure the class client is set if direct instantiation happens
             RedisClient._client = client
        self.client = RedisClient._client # Use the class-level client

    @classmethod
    async def _initialize_client(cls) -> aioredis.Redis:
        """Initializes the Redis client connection if not already done."""
        if cls._client is None or not await cls._is_connected(cls._client):
            print(f"Initializing Redis client for URL: {settings.REDIS_URL}")
            try:
                cls._client = aioredis.from_url(
                    str(settings.REDIS_URL),
                    encoding="utf-8",
                    decode_responses=True
                )
                await cls._client.ping()
                print("Redis client initialized and connected successfully.")
            except Exception as e:
                cls._client = None
                print(f"Failed to initialize or connect to Redis: {e}")
                raise ConnectionError(f"Could not connect to Redis: {e}") from e
        return cls._client

    @classmethod
    async def _is_connected(cls, client: Optional[aioredis.Redis]) -> bool:
        if client is None:
            return False
        try:
            await client.ping()
            return True
        except (aioredis.exceptions.ConnectionError, aioredis.exceptions.TimeoutError, ConnectionRefusedError):
            return False
        except Exception: # Catch any other unexpected exception during ping
            return False

    @classmethod
    async def get_client_instance(cls) -> 'RedisClient':
        """Gets a RedisClient instance, initializing the underlying connection if needed."""
        if cls._instance is None:
            underlying_client = await cls._initialize_client()
            cls._instance = cls(client=underlying_client) # Pass the initialized client
        elif cls._client is None or not await cls._is_connected(cls._client):
            # Re-initialize if client exists but is disconnected
            underlying_client = await cls._initialize_client()
            # cls._instance client will be updated as it refers to cls._client
        return cls._instance

    @classmethod
    async def close_global_client(cls):
        """Closes the global Redis client connection."""
        if cls._client:
            print("Closing global Redis client connection...")
            try:
                await cls._client.close()
                # For newer versions of redis-py, pool disconnect is handled by close()
                # If using an older version or specific setup, you might need:
                # await cls._client.connection_pool.disconnect()
            except Exception as e:
                print(f"Error closing Redis connection: {e}")
            finally:
                cls._client = None
                cls._instance = None # Clear instance as well
                print("Global Redis client connection closed and instance cleared.")

    # --- Instance Methods for Cache Operations ---
    # These methods will now use self.client which points to RedisClient._client
    async def set_cache(self, key: str, value: Any, expire_seconds: Optional[int] = None, is_json: bool = False):
        """Sets a value in the cache."""
        if not self.client or not await self._is_connected(self.client): # Use instance client
            print("Redis client not available for set_cache.")
            # Optionally raise an error or handle gracefully
            return

        try:
            processed_value = json.dumps(value) if is_json else str(value)
            await self.client.set(key, processed_value, ex=expire_seconds)
            if settings.DEBUG: print(f"Cache SET: key='{key}' (expires in {expire_seconds}s)")
        except Exception as e:
            print(f"Error setting cache for key '{key}': {e}")

    async def get_cache(self, key: str, is_json: bool = False) -> Optional[Any]:
        """Gets a value from the cache."""
        if not self.client or not await self._is_connected(self.client):
            if settings.DEBUG: print(f"Redis client not available for get_cache key='{key}'")
            return None

        try:
            value = await self.client.get(key)
            if value is not None:
                if settings.DEBUG: print(f"Cache HIT: key='{key}'")
                return json.loads(value) if is_json else value
            if settings.DEBUG: print(f"Cache MISS: key='{key}'")
        except Exception as e:
            print(f"Error getting cache for key '{key}': {e}")
        return None

    async def delete_cache(self, key: str):
        """Deletes a key from the cache."""
        if not self.client or not await self._is_connected(self.client):
            print("Redis client not available for delete_cache.")
            return
        try:
            await self.client.delete(key)
            if settings.DEBUG: print(f"Cache DELETE: key='{key}'")
        except Exception as e:
            print(f"Error deleting cache for key '{key}': {e}")

    async def clear_cache_by_prefix(self, prefix: str):
        """Deletes all keys matching a given prefix. Use with caution."""
        if not self.client or not await self._is_connected(self.client):
            print("Redis client not available for clear_cache_by_prefix.")
            return
        try:
            # Ensure the client supports async iteration for scan_iter or adapt
            keys_to_delete = []
            async for key_item in self.client.scan_iter(match=f"{prefix}*"):
                keys_to_delete.append(key_item)

            if keys_to_delete:
                await self.client.delete(*keys_to_delete)
                if settings.DEBUG: print(f"Cache CLEAR_BY_PREFIX: deleted {len(keys_to_delete)} keys with prefix '{prefix}'")
            elif settings.DEBUG:
                print(f"Cache CLEAR_BY_PREFIX: no keys found with prefix '{prefix}'")
        except Exception as e:
            print(f"Error clearing cache by prefix '{prefix}': {e}")


# FastAPI Dependency provider for RedisClient instance
async def get_redis_client_dependency() -> AsyncGenerator[RedisClient, None]:
    """
    FastAPI dependency that provides a RedisClient instance.
    Manages the lifecycle of the Redis connection via the class methods.
    """
    # Ensures client is initialized on first request via this dependency
    # The RedisClient.get_client_instance() handles the actual connection pool.
    # The lifespan manager in main.py should handle global close.
    redis_client_instance = None
    try:
        redis_client_instance = await RedisClient.get_client_instance()
        yield redis_client_instance
    except ConnectionError as e:
        # If Redis connection fails during app startup or first use,
        # the app might not be usable if Redis is critical.
        # Log this prominently. For now, allow app to continue if possible.
        print(f"CRITICAL: Redis connection failed in dependency: {e}")
        # Yield None or raise an HTTPException if Redis is absolutely critical for all routes using it
        # For now, if get_client_instance raises, it will propagate. If it doesn't, but client is None:
        if redis_client_instance is None or redis_client_instance.client is None:
             # This case should ideally be handled by get_client_instance raising an error
             print("CRITICAL: Redis client instance or underlying client is None in dependency.")
        yield redis_client_instance # Still yield, service methods will check client availability
    except Exception as e:
        print(f"Unexpected error in get_redis_client_dependency: {e}")
        # Depending on policy, re-raise or yield None
        raise # Re-raise unexpected errors
    # finally:
        # The closing of the global client should be handled by the application's
        # lifespan manager (shutdown event) to ensure it's done once for the app.
        # If not using lifespan for this, you might close here, but it's less ideal.
        # await RedisClient.close_global_client() # Typically NOT closed here per-request


# Update services_external/__init__.py to export the correct dependency name
# from .redis_client import RedisClient, get_redis_client_dependency
# __all__ = ["RedisClient", "get_redis_client_dependency"]
