import flet as ft
from fletx.core import (
    FletXPage
)

from ..controllers.counter import CounterController
from ..components import MyReactiveText


class CounterPage(FletXPage):
    ctrl = CounterController()
    
    def build(self):
        return ft.Column(
            spacing = 20,
            expand = True,
            alignment = ft.MainAxisAlignment.CENTER,
            horizontal_alignment = ft.CrossAxisAlignment.CENTER,
            controls = [
                ft.Text(
                    "{{ project_name | pascal_case }} Counter",
                    size = 20,
                    weight = ft.FontWeight.BOLD
                ),
                MyReactiveText(
                    value = '0',
                    rx_text = self.ctrl.count, # Auto update when count changes
                    size = 100, 
                    weight = ft.FontWeight.BOLD
                ),
                ft.ElevatedButton(
                    "Increment",
                    on_click=lambda e: self.ctrl.count.increment()  # Auto UI update
                )
            ]
        )