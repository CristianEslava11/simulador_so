"""
Archivo simulado.

Representa un archivo virtual con control de acceso concurrente
mediante un threading.Lock integrado directamente (sin wrapper).
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SimulatedFile:
    """Archivo simulado con mutex integrado.

    Attributes:
        name: Nombre del archivo.
        size: Tamaño simulado del archivo.
        locked_by: PID del proceso que tiene el lock (None si libre).
    """

    name: str
    size: int = 0
    locked_by: Optional[int] = None
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def acquire(self, pid: int) -> bool:
        """Intenta adquirir el lock del archivo.

        Args:
            pid: PID del proceso que solicita acceso.

        Returns:
            True si se adquirió el lock, False si ya estaba bloqueado.
        """
        acquired = self._lock.acquire(blocking=False)
        if acquired:
            self.locked_by = pid
        return acquired

    def release(self, pid: int) -> None:
        """Libera el lock del archivo.

        Args:
            pid: PID del proceso que libera el acceso.
        """
        if self.locked_by == pid:
            self.locked_by = None
            self._lock.release()
