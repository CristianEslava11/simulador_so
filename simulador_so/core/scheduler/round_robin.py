"""
Planificador Round Robin.

Asigna un quantum de tiempo fijo a cada proceso.  Cuando el quantum
se agota, el proceso vuelve al final de la cola circular.
"""

from __future__ import annotations

from collections import deque
from typing import Optional

from core.models.process import Process
from core.scheduler.scheduler import Scheduler


class RoundRobinScheduler(Scheduler):
    """Implementación del algoritmo Round Robin.

    Attributes:
        quantum: Número de ticks que cada proceso puede ejecutar
            antes de ser interrumpido.
    """

    def __init__(self, quantum: int = 4) -> None:
        self.quantum = quantum
        self._ready_queue: deque[Process] = deque()

    def add_process(self, process: Process) -> None:
        self._ready_queue.append(process)

    def get_next_process(self) -> Optional[Process]:
        if not self._ready_queue:
            return None
        return self._ready_queue.popleft()

    def remove_process(self, pid: int) -> None:
        self._ready_queue = deque(
            p for p in self._ready_queue if p.pid != pid
        )

    @property
    def name(self) -> str:
        return "Round Robin"
