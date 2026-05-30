"""
Planificador Shortest Job First (SJF).

Selecciona el proceso con menor tiempo restante de ejecución.
No preemptivo: una vez que un proceso comienza, ejecuta hasta
completar su ráfaga o bloquearse.
"""

from __future__ import annotations

from typing import Optional

from core.models.process import Process
from core.scheduler.scheduler import Scheduler


class SJFScheduler(Scheduler):
    """Implementación del algoritmo Shortest Job First."""

    def __init__(self) -> None:
        self._ready_queue: list[Process] = []

    def add_process(self, process: Process) -> None:
        self._ready_queue.append(process)

    def get_next_process(self) -> Optional[Process]:
        if not self._ready_queue:
            return None
        # Seleccionar el proceso con menor remaining_time
        self._ready_queue.sort(key=lambda p: p.remaining_time)
        return self._ready_queue.pop(0)

    def remove_process(self, pid: int) -> None:
        self._ready_queue = [
            p for p in self._ready_queue if p.pid != pid
        ]

    @property
    def name(self) -> str:
        return "Shortest Job First"
