# Makes 'services_external' a Python package.
from .redis_client import RedisClient, get_redis_client_dependency

__all__ = ["RedisClient", "get_redis_client_dependency"]
