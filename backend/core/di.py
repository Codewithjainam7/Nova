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
            
        # Return none instead of error for optional dependencies during bootstrap
        return None

di_container = DependencyInjectionContainer()

def bootstrap_di():
    # Import core cloud-safe subsystems first
    from backend.planner.core import PlannerCore
    from backend.memory.core import MemoryEngine
    from backend.providers.core import AIProviderManager
    from backend.chat.core import ChatSystem
    from backend.context.core import ContextEngine
    from backend.verification.core import VerificationManager
    from backend.verification.registry import VerificationRegistry
    from backend.core.environment import load_environment, is_cloud_mode

    load_environment()

    # Initialize Provider Manager early
    provider_manager = AIProviderManager()
    provider_manager.bootstrap()
    di_container.register_singleton(AIProviderManager, provider_manager)

    # Initialize Verification dependencies
    registry = VerificationRegistry()
    verification_manager = VerificationManager(registry)

    # Initialize Planner dependencies
    planner_core = PlannerCore(provider_manager=provider_manager)

    di_container.register_singleton(PlannerCore, planner_core)
    di_container.register_singleton(MemoryEngine, MemoryEngine())
    di_container.register_singleton(ChatSystem, ChatSystem())
    di_container.register_singleton(ContextEngine, ContextEngine())
    di_container.register_singleton(VerificationManager, verification_manager)

    # Local-only hardware/desktop/audio engines (skipped cleanly in cloud mode)
    if not is_cloud_mode():
        for mod_path, cls_name in [
            ("backend.browser.core", "BrowserEngine"),
            ("backend.desktop.core", "DesktopEngine"),
            ("backend.vision.core", "VisionEngine"),
            ("backend.voice.core", "VoiceEngine"),
        ]:
            try:
                mod = __import__(mod_path, fromlist=[cls_name])
                cls = getattr(mod, cls_name)
                di_container.register_singleton(cls, cls())
            except Exception as e:
                app_logger.warning(f"Optional local subsystem {cls_name} skipped: {e}")

    app_logger.info(f"DI Container bootstrapped (cloud_mode={is_cloud_mode()}).")
