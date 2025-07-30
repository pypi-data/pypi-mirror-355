"""
FletX - Core Page module.
Advanced page with integrated controller, effects, and reactivity management
A page that incorporates advanced features such as controller, effects, and reactivity management, enabling the creation of interactive and dynamic user experiences.
"""

import flet as ft
from typing import (
    Union, List, Optional, Any, Dict, Type, TypeVar, Callable
)
from abc import ABC, abstractmethod
from fletx.core.controller import FletXController
from fletx.core.routing.models import RouteInfo
from fletx.core.di import DI
from fletx.core.effects import EffectManager
# from fletx.decorators import use_effect as useEffect
from fletx.utils import get_logger

T = TypeVar('T', bound=FletXController)


####
##      FLETX PAGE CLASS
#####
class FletXPage(ABC):
    """
    Extended base class for FletX pages.
    A base class that provides basic functionality and methods 
    for FletX pages, allowing to create custom pages and extend 
    them to meet the specific needs of the application.
    """
    
    def __init__(self):
        self.route_info: Optional[RouteInfo] = None
        self._controllers: Dict[Type[FletXController], FletXController] = {}
        self._effects = EffectManager()
        self._logger = get_logger("FletX.Page")
        self._is_mounted = False
        
        # Register FletX Page instance Effect Manager
        DI.put(self._effects, f"page_effects_{id(self)}")

    @classmethod
    @property
    def logger(cls):
        if not cls._logger:
            cls._logger = get_logger('FletX.Page')
        return cls._logger
    
    @abstractmethod
    def build(self) -> Union[ft.Control, List[ft.Control]]:
        """
        Abstract method to implement for building the page.
        An abstract method that must be implemented by derived 
        classes to define the structure and content of the page, 
        allowing to create custom and flexible pages.
        """

        pass
    
    def did_mount(self):
        """Called when the page is mounted"""

        self._is_mounted = True
        self._effects.runEffects()
    
    def will_unmount(self):
        """Called when the page is about to be unmounted."""

        self._is_mounted = False
        self._effects.dispose()
        self._dispose_controllers()
    
    def get_controller(
        self, 
        controller_class: Type[T], 
        tag: str = None
    ) -> T:
        """Gets or creates a controller with automatic lifecycle management."""
        
        controller_key = f"{controller_class.__name__}_{tag}" if tag else controller_class.__name__
        
        if controller_key in self._controllers:
            return self._controllers[controller_key]
            
        # First Check for the controller in global DI
        controller = DI.find(controller_class, tag)
        
        if not controller:
            controller = controller_class()
            DI.put(controller, tag)
        
        self._controllers[controller_key] = controller
        return controller
    
    def add_effect(
        self, 
        effect_fn: Callable, 
        dependencies: List[Any] = None
    ):
        """Adds an effect to the page"""

        self._effects.useEffect(effect_fn, dependencies)
    
    def watch(
        self, 
        reactive_obj, 
        callback: Callable
    ):
        """Observes a reactive object with automatic cleanup"""

        if hasattr(reactive_obj, 'listen'):
            observer = reactive_obj.listen(lambda: self._safe_callback(callback))
            self.add_effect(lambda: lambda: observer.dispose())
            return observer
        else:
            self.logger.warning(f"{reactive_obj} is not a reactive object.")
    
    def _safe_callback(self, callback: Callable):
        """Runs a callback only if the page is mounted."""

        if self._is_mounted:
            try:
                callback()
            except Exception as e:
                self.logger.error(f"Callback error: {e}", exc_info=True)
    
    def _dispose_controllers(self):
        """Cleans up the page's controllers"""
        
        for controller in self._controllers.values():
            controller.dispose()
        self._controllers.clear()
    
    def dispose(self):
        """Cleans up all page resources"""

        self.will_unmount()
        DI.delete(EffectManager, f"page_effects_{id(self)}")

    def on_resize(self, callback: Callable[[ft.ControlEvent], None]):
        """Listens to page size changes"""

        def handler(e):
            if self._is_mounted:
                callback(e)
        
        self.add_effect(
            lambda: self._connect_event_handler("resize", handler),
            []
        )
    
    def on_keyboard(self, callback: Callable[[ft.KeyboardEvent], None]):
        """Listens to keyboard events"""

        def handler(e):
            if self._is_mounted:
                callback(e)
        
        self.add_effect(
            lambda: self._connect_event_handler("keyboard", handler),
            []
        )
    
    def _connect_event_handler(self, event_name: str, handler: Callable):
        """Attaches an event handler with automatic cleanup"""
        
        page = DI.find(ft.Page)
        if page:
            page.on_event(event_name, handler)
            return lambda: page.remove_event_handler(event_name, handler)
        return None