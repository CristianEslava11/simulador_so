"""
Bus de eventos mínimo (patrón Publish/Subscribe).

Permite desacoplar módulos del simulador: cada módulo publica eventos
sin conocer quién los consume, y los consumidores se suscriben sin
conocer quién los produce.

Thread-safe mediante threading.Lock porque el Kernel y la UI
operan en hilos distintos.
"""

from __future__ import annotations

import threading
from collections import defaultdict
from typing import Callable

from core.events.event import Event


class EventBus:
    """Bus de eventos con patrón Publish/Subscribe.

    Uso:
        bus = EventBus()
        bus.subscribe("PAGE_FAULT", mi_callback)
        bus.publish(Event(timestamp=1, event_type="PAGE_FAULT", source="MemoryManager"))
    """

    def __init__(self) -> None:
        self._subscribers: dict[str, list[Callable[[Event], None]]] = defaultdict(list)
        self._lock = threading.Lock()

    def subscribe(self, event_type: str, callback: Callable[[Event], None]) -> None:
        """Registra un callback que será invocado cada vez que se
        publique un evento del tipo indicado.

        Args:
            event_type: Tipo de evento al que suscribirse.
            callback: Función que recibe un Event como argumento.
        """
        with self._lock:
            self._subscribers[event_type].append(callback)

    def publish(self, event: Event) -> None:
        """Publica un evento y notifica a todos los suscriptores registrados
        para ese tipo de evento.

        Args:
            event: Evento a publicar.
        """
        with self._lock:
            subscribers = list(self._subscribers.get(event.event_type, []))

        for callback in subscribers:
            callback(event)
