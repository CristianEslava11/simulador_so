"""
Algoritmo de reemplazo LRU (Least Recently Used).

Reemplaza la página que no ha sido accedida por más tiempo.
Utiliza el campo last_access_time de Page para determinar el orden.
"""

from __future__ import annotations

from core.models.frame import Frame
from core.memory.replacement_algorithm import ReplacementAlgorithm


class LRUReplacement(ReplacementAlgorithm):
    """Implementación del algoritmo de reemplazo LRU."""

    def select_victim(self, frames: list[Frame]) -> Frame:
        # Seleccionar el marco cuya página fue accedida menos recientemente
        occupied = [f for f in frames if not f.is_free and f.page is not None]
        return min(occupied, key=lambda f: f.page.last_access_time)

    def on_page_access(self, frame: Frame) -> None:
        # El last_access_time se actualiza en el MemoryManager al acceder
        pass

    def on_page_load(self, frame: Frame) -> None:
        # Al cargar, el last_access_time también se actualiza en MemoryManager
        pass

    @property
    def name(self) -> str:
        return "LRU"
