import asyncio

from fletx.core.routing.router import (
    FletXRouter
)
from fletx.core.routing.config import (
    RoutePattern, RouterConfig, router_config,
    ModuleRouter
)
from fletx.core.routing.guards import RouteGuard
from fletx.core.routing.middleware import RouteMiddleware
from fletx.core.routing.transitions import (
    TransitionType, RouteTransition
)
from fletx.core.routing.models import (
    RouteInfo, RouterState, RouteType,
    NavigationIntent, NavigationMode, 
    NavigationResult, IRouteResolver
)
# from fletx.core.background import run_background


# Convenience functions for global router access

def get_router() -> FletXRouter:
    """Get the global router instance."""
    return FletXRouter.get_instance()

def navigate(route: str, **kwargs) -> NavigationResult:
    """Navigate using the global router."""
    router = get_router()
    return router.navigate(route, **kwargs)

def go_back() -> bool:
    """Go back using the global router."""
    return get_router().go_back()

def go_forward() -> bool:
    """Go forward using the global router."""
    return get_router().go_forward()


__all__ = [
    'RouteGuard',
    'RouteMiddleware',
    'TransitionType',
    'RouteTransition',
    'RoutePattern',
    'RouterConfig',
    'FletXRouter',
    'NavigationResult',
    'RouteInfo',
    'RouterState',
    'RouteType',
    'NavigationIntent',
    'NavigationMode',
    'IRouteResolver',
    'ModuleRouter',
    'router_config',

    # FUNCTIONS
    'get_router',
    'navigate',
    'go_back',
    'go_forward'
]