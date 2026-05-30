"""
Modelo de evento del sistema y constantes de tipos de evento.

Cada acción relevante del simulador genera un Event que es publicado
en el EventBus para que los módulos interesados reaccionen.
"""

from __future__ import annotations

from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Constantes de tipos de evento
# ---------------------------------------------------------------------------

PROCESS_CREATED = "PROCESS_CREATED"
PROCESS_STARTED = "PROCESS_STARTED"
PROCESS_FINISHED = "PROCESS_FINISHED"
CONTEXT_SWITCH = "CONTEXT_SWITCH"

PAGE_FAULT = "PAGE_FAULT"
PAGE_HIT = "PAGE_HIT"
PAGE_REPLACED = "PAGE_REPLACED"

FILE_LOCKED = "FILE_LOCKED"
FILE_UNLOCKED = "FILE_UNLOCKED"
FILE_CONFLICT = "FILE_CONFLICT"


# ---------------------------------------------------------------------------
# Clase Event
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Event:
    """Evento inmutable del sistema.

    Attributes:
        timestamp: Tick del sistema en el que ocurrió el evento.
        event_type: Tipo del evento (usar las constantes definidas arriba).
        source: Nombre del módulo que generó el evento.
        data: Datos adicionales asociados al evento.
    """

    timestamp: int
    event_type: str
    source: str
    data: dict = field(default_factory=dict)

    def __str__(self) -> str:
        return f"[{self.timestamp:>4}] {self.event_type:<20} | {self.source} | {self.data}"
