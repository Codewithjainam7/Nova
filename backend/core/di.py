from typing import Any, Callable, Dict, Type, TypeVar
from backend.core.logger import app_logger

T = TypeVar("T")

class DependencyInjectionContainer:
    """
    Service Registry and Dependency Resolver for NOVA.
    Supports singletons and transient/scoped services.
    """
    def __init__(self):
        self._singletons: Dict[Type, Any] = {}
        self._factories: Dict[Type, Callable[[], Any]] = {}

    def register_singleton(self, interface: Type[T], implementation: T):
        """Register an existing instance as a singleton."""
        self._singletons[interface] = implementation
        app_logger.debug(f"Registered singleton for {interface.__name__}")

    def register_factory(self, interface: Type[T], factory: Callable[[], T], as_singleton: bool = False):
        """Register a factory method for lazy initialization."""
        if as_singleton:
            # Wrap the factory to cache the result
            def singleton_factory():
                if interface not in self._singletons:
                    self._singletons[interface] = factory()
                return self._singletons[interface]
            self._factories[interface] = singleton_factory
        else:
            self._factories[interface] = factory
        app_logger.debug(f"Registered factory for {interface.__name__} (singleton={as_singleton})")

    def resolve(self, interface: Type[T]) -> T:
        """Resolve a service dependency."""
        if interface in self._singletons:
            return self._singletons[interface]
        
        if interface in self._factories:
            return self._factories[interface]()
            
        raise ValueError(f"Service {interface.__name__} not registered in DI container.")

di_container = DependencyInjectionContainer()
