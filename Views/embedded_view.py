import tkinter as tk
from tkinter import ttk


def crear_panel_embebido(container, on_back):
    """Crea una barra de navegación y un área para mostrar una vista dentro del panel."""
    container.columnconfigure(0, weight=1)
    container.rowconfigure(1, weight=1)
    barra = ttk.Frame(container)
    barra.grid(row=0, column=0, sticky="ew", pady=(0, 6))
    ttk.Button(barra, text="← Volver a opciones", command=on_back).pack(side="left")
    area = ttk.Frame(container)
    area.grid(row=1, column=0, sticky="nsew")
    area.columnconfigure(0, weight=1)
    area.rowconfigure(0, weight=1)
    return area
