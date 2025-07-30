"""
FletX main entry point
"""

import flet as ft
from typing import Dict, Type, Optional
from fletx.core.routing.router import FletXRouter
from fletx.core.page import FletXPage
# from fletx.core.factory import FletXWidgetRegistry
from fletx.utils.logger import SharedLogger
from fletx.utils.context import AppContext


####
##      FLETX APPLICATION
#####
class FletXApp:
    """Main application class"""
    
    def __init__(
        self, 
        initial_route: str = "/",
        theme_mode: ft.ThemeMode = ft.ThemeMode.SYSTEM,
        debug: bool = False
    ):
        """
        Initializes the FletX application
        
        Args:
            routes: Dictionary of routes {path: PageClass}
            initial_route: Initial route
            theme_mode: Theme mode
            debug: Debug mode
        """

        self.initial_route = initial_route
        self.theme_mode = theme_mode
        self.debug = debug

        # Initialization of the shared logger
        SharedLogger._initialize_logger(
            name = 'FletX',
            debug = debug
        )
        self.logger = SharedLogger.get_logger(__name__)
        
        
    def run(self, **kwargs):
        """Deprecated method – use only in controlled environments"""

        import warnings
        warnings.warn(
            "Prefer using ft.app(target=main) with _main()", 
            DeprecationWarning
        )
        ft.app(target=self._main, **self.kwargs)
    
    def _main(self, page: ft.Page):
        """Main entry point for Flet"""

        try:
            # Configure page
            page.theme_mode = self.theme_mode

            # Register all widgets
            # FletXWidgetRegistry.register_all(page)
            
            # FletX App Context Initialization
            AppContext.initialize(page, self.debug)

            AppContext.set_data("logger", self.logger)
            
            # FletX Router Initialization
            FletXRouter.initialize(page, initial_route = self.initial_route)
            
            self.logger.info("FletX Application initialized with success")
            
        except Exception as e:
            self.logger.error(f"Error when initializing FletX App: {e}")
            page.add(ft.Text(f"Error: {e}", color=ft.Colors.RED))