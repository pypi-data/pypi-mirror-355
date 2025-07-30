import logging
from pathlib import Path
from types import ModuleType
import flet
from typing import Optional, Union
from importlib import import_module

from fletx.utils.context import AppContext

# FletX Logger Utility
def get_logger(name: str) -> logging.Logger:
    """Gets a logger from the global context"""

    base_logger = AppContext.get_data("logger")
    if base_logger is None:

        # Fallback if the context is not initialized
        logger = logging.getLogger(name)
        logger.addHandler(logging.NullHandler())
        return logger
    return base_logger.getChild(name)


# FletXApp Context Page Getter
def get_page() -> flet.Page: 
    """Gets the current FletX page from the global context"""
    
    page = AppContext.get_page()
    if page is None:
        raise RuntimeError(
            "FletX application context is not initialized."
            " Ensure AppContext.initialize() is called before accessing the page."
        )
    return page

# IMPORT MODULE
def import_module_from(path: Union[str,Path]) ->'ModuleType':
    """Import module using importlib"""
    
    return import_module(path)