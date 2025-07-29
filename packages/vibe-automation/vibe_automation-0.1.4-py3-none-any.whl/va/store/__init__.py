from .store import Store, ExecutionStore, ReviewStore
from .in_memory import InMemoryStore


def get_store() -> Store:
    return InMemoryStore()


__all__ = [get_store, Store, ExecutionStore, ReviewStore, InMemoryStore]
