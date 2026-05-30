"""
Modelo de página virtual.

Representa una página en el espacio de direcciones virtuales de un proceso.
Contiene la información necesaria para los algoritmos de reemplazo:
    - loaded_at_time: para FIFO (primera en entrar, primera en salir).
    - last_access_time: para LRU (menos recientemente usada).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Page:
    """Página virtual de un proceso.

    Attributes:
        page_id: Número de página dentro del proceso.
        pid: Identificador del proceso propietario.
        loaded: Indica si la página está cargada en un marco de memoria.
        frame_id: Marco de memoria asignado (None si no está cargada).
        loaded_at_time: Tick en que fue cargada en memoria (para FIFO).
        last_access_time: Tick del último acceso (para LRU).
    """

    page_id: int
    pid: int
    loaded: bool = False
    frame_id: Optional[int] = None
    loaded_at_time: int = 0
    last_access_time: int = 0
