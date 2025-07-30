"""
{{ description }}

A FletX application.
Author: {{ author }}
Version: {{ version }}
"""

import flet as ft
from fletx.app import FletXApp
from app.routes import {{ project_name | pascal_case }}Router

def main(page: ft.Page):
    """Main entry point for the Flet application."""

    # Configure Page
    page.title = "{{ project_name }}"

    # Setting up theme
    page.theme = ft.Theme(
        color_scheme_seed = ft.Colors.GREEN
    )
    page.dark_theme = ft.Theme(
        color_scheme_seed = ft.Colors.BLUE_800,
        scaffold_bgcolor = ft.Colors.BLACK,
    )
    page.theme_mode = ft.ThemeMode.DARK

    # Setting up window size
    page.window.height = 810
    page.window.width = 400
    
    # FletX Application Initialization
    app = FletXApp(
        initial_route = "/",
        debug = True
    )
    
    # 
    app._main(page) 

if __name__ == "__main__":
    ft.app(target=main)