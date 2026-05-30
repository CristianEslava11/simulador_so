"""
Algoritmo de reemplazo FIFO (First In, First Out).

Reemplaza la página que fue cargada primero en memoria.
Utiliza el campo loaded_at_time de Page para determinar el orden.
"""

from __future__ import annotations

from core.models.frame import Frame
from core.memory.replacement_algorithm import ReplacementAlgorithm


class FIFOReplacement(ReplacementAlgorithm):
    """Implementación del algoritmo de reemplazo FIFO."""

    def select_victim(self, frames: list[Frame]) -> Frame:
        # Seleccionar el marco cuya página fue cargada primero
        occupied = [f for f in frames if not f.is_free and f.page is not None]
        return min(occupied, key=lambda f: f.page.loaded_at_time)

    def on_page_access(self, frame: Frame) -> None:
        # FIFO no necesita rastrear accesos, solo orden de carga
        pass

    def on_page_load(self, frame: Frame) -> None:
        # El loaded_at_time ya se establece en el MemoryManager al cargar
        pass

    @property
    def name(self) -> str:
        return "FIFO"
