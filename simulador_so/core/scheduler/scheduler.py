"""
Interfaz abstracta para algoritmos de planificación de procesos.

Define el contrato que deben cumplir todas las implementaciones
(Round Robin, SJF, Priority) para poder ser intercambiadas
en el Kernel sin modificar su código.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from core.models.process import Process


class Scheduler(ABC):
    """Clase base abstracta para planificadores de procesos.

    Toda implementación concreta debe definir cómo se agregan procesos
    a la cola, cómo se selecciona el siguiente, y cómo se remueven.
    """

    @abstractmethod
    def add_process(self, process: Process) -> None:
        """Agrega un proceso a la cola de listos.

        Args:
            process: Proceso a agregar.
        """

    @abstractmethod
    def get_next_process(self) -> Optional[Process]:
        """Selecciona y retorna el siguiente proceso a ejecutar.

        Returns:
            El proceso seleccionado, o None si la cola está vacía.
        """

    @abstractmethod
    def remove_process(self, pid: int) -> None:
        """Elimina un proceso de la cola de listos.

        Args:
            pid: Identificador del proceso a eliminar.
        """

    @property
    @abstractmethod
    def name(self) -> str:
        """Nombre del algoritmo de planificación."""
