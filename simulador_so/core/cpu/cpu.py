"""
CPU simulada.

Ejecuta ticks de CPU sobre procesos, actualiza sus contadores
y publica eventos relevantes en el EventBus.
"""

from __future__ import annotations

from typing import Optional

from core.events.event import Event, PROCESS_STARTED, PROCESS_FINISHED
from core.events.event_bus import EventBus
from core.models.process import Process
from core.models.process_state import ProcessState


class CPU:
    """Simula la unidad central de procesamiento.

    Attributes:
        event_bus: Bus de eventos para publicar notificaciones.
        current_process: Proceso actualmente en ejecución.
        ticks_busy: Ticks totales en los que la CPU estuvo ocupada.
        ticks_idle: Ticks totales en los que la CPU estuvo ociosa.
        context_switches: Cantidad de cambios de contexto realizados.
    """

    def __init__(self, event_bus: EventBus) -> None:
        self.event_bus = event_bus
        self.current_process: Optional[Process] = None
        self.ticks_busy: int = 0
        self.ticks_idle: int = 0
        self.context_switches: int = 0

    def execute_tick(self, process: Process, current_tick: int) -> None:
        """Ejecuta un tick de CPU sobre el proceso dado.

        Args:
            process: Proceso a ejecutar.
            current_tick: Tick actual del sistema.
        """
        # TODO: Implementar lógica de ejecución
        self.current_process = process

        if process.start_time is None:
            process.start_time = current_tick
            self.event_bus.publish(Event(
                timestamp=current_tick,
                event_type=PROCESS_STARTED,
                source="CPU",
                data={"pid": process.pid, "name": process.name},
            ))

        if process.remaining_time <= 0:
            return

        process.remaining_time -= 1
        process.cpu_time += 1
        self.ticks_busy += 1

        if process.remaining_time == 0:
            process.state = ProcessState.TERMINATED
            process.finish_time = current_tick + 1
            process.turnaround_time = process.finish_time - process.arrival_time
            self.event_bus.publish(Event(
                timestamp=process.finish_time,
                event_type=PROCESS_FINISHED,
                source="CPU",
                data={"pid": process.pid, "name": process.name},
            ))

    def is_idle(self) -> bool:
        """Retorna True si la CPU no tiene un proceso asignado."""
        return self.current_process is None

    @property
    def utilization(self) -> float:
        """Porcentaje de utilización de la CPU."""
        total = self.ticks_busy + self.ticks_idle
        if total == 0:
            return 0.0
        return (self.ticks_busy / total) * 100.0
