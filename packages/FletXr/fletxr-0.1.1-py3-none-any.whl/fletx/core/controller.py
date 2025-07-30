"""
Base Controller for FletX.
fletx.core.controller module that provides a basic implementation for 
controllers in FletX, allowing to manage interactions between views and data models, 
and to facilitate the creation of robust and maintainable applications.
"""

from typing import List, Callable, Any
from fletx.core.effects import EffectManager
from fletx.core.di import DI


####
##      FLETX BASE CONTROLLER CLASS
#####
class FletXController:
    """
    Advanced Controller with Reactivity.
    A controller that incorporates reactivity features, 
    allowing to manage data changes and events in an efficient and automatic way, 
    to create interactive and dynamic applications.
    """
    
    _effects_manager: EffectManager = None

    def __init__(self):
        self._effects = EffectManager()
        self._disposed = False
        
        # Register effets Manager
        DI.put(self._effects, f"effects_{id(self)}")

    @property
    def effects(self) -> EffectManager:
        """Gets the effect manager"""

        if self._disposed:
            raise RuntimeError("Controller is disposed")
            
        return DI.find(EffectManager, f"effects_{id(self)}")
    
    def on_ready(self):
        """Lifecycle point when the controller is ready"""

        self._effects.runEffects()
    
    def dispose(self):
        """Cleans up all resources"""

        if not self._disposed:
            self._effects.dispose()
            self._disposed = True
    
    def add_effect(
        self, 
        effect_fn: Callable, 
        deps: List[Any] = None
    ):
        """Ajoute un effet au contrôleur"""

        self._effects.useEffect(effect_fn, deps)