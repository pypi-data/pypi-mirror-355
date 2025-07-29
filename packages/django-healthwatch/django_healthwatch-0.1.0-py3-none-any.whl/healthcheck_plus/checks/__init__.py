from ..registry import registry
from .db_check import DatabaseCheck
from .cache_check import CacheCheck
from .storage_check import StorageCheck

registry.register(DatabaseCheck)
registry.register(CacheCheck)
registry.register(StorageCheck)
