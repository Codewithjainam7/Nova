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
    # Import here to avoid circular dependencies
    from backend.planner.core import PlannerCore
    from backend.planner.engines import (
        MockLLMProvider, IntentDetector, GoalExtractor,
        RiskDetector, TaskDecomposer, DependencyResolver,
        ClarificationEngine
    )
    from backend.memory.core import MemoryEngine
    from backend.providers.core import AIProviderManager
    from backend.browser.core import BrowserEngine
    from backend.desktop.core import DesktopEngine
    from backend.vision.core import VisionEngine
    from backend.voice.core import VoiceEngine
    from backend.chat.core import ChatSystem
    from backend.context.core import ContextEngine
    from backend.verification.core import VerificationManager
    from backend.verification.registry import VerificationRegistry

    # Initialize Provider Manager early
    provider_manager = AIProviderManager()
    di_container.register_singleton(AIProviderManager, provider_manager)

    # Initialize Verification dependencies
    registry = VerificationRegistry()
    verification_manager = VerificationManager(registry)

    # Initialize Planner dependencies
    planner_core = PlannerCore(provider_manager=provider_manager)

    di_container.register_singleton(PlannerCore, planner_core)
    di_container.register_singleton(MemoryEngine, MemoryEngine())
    di_container.register_singleton(BrowserEngine, BrowserEngine())
    di_container.register_singleton(DesktopEngine, DesktopEngine())
    di_container.register_singleton(VisionEngine, VisionEngine())
    di_container.register_singleton(VoiceEngine, VoiceEngine())
    di_container.register_singleton(ChatSystem, ChatSystem())
    di_container.register_singleton(ContextEngine, ContextEngine())
    di_container.register_singleton(VerificationManager, verification_manager)
    
    app_logger.info("DI Container bootstrapped with all Subsystems.")
