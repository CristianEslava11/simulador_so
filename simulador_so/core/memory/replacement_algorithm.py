"""
Interfaz abstracta para algoritmos de reemplazo de páginas.

Define el contrato que deben cumplir FIFO y LRU para que el
MemoryManager pueda intercambiarlos sin modificar su código.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from core.models.frame import Frame


class ReplacementAlgorithm(ABC):
    """Clase base abstracta para algoritmos de reemplazo de páginas."""

    @abstractmethod
    def select_victim(self, frames: list[Frame]) -> Frame:
        """Selecciona el marco que será reemplazado.

        Args:
            frames: Lista de marcos ocupados en memoria.

        Returns:
            El marco seleccionado como víctima.
        """

    @abstractmethod
    def on_page_access(self, frame: Frame) -> None:
        """Notifica que se accedió a una página ya cargada.

        Usado por LRU para actualizar el orden de acceso.

        Args:
            frame: Marco cuya página fue accedida.
        """

    @abstractmethod
    def on_page_load(self, frame: Frame) -> None:
        """Notifica que se cargó una página nueva en un marco.

        Usado por FIFO para registrar el orden de carga.

        Args:
            frame: Marco donde se cargó la página.
        """

    @property
    @abstractmethod
    def name(self) -> str:
        """Nombre del algoritmo de reemplazo."""
