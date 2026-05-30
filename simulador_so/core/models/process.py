"""
Modelo del Process Control Block (PCB).

Representa toda la información que el sistema operativo mantiene
sobre un proceso: identificación, estado, planificación, paginación y métricas.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from core.models.process_state import ProcessState


@dataclass
class Process:
    """Bloque de control de un proceso simulado (PCB).

    Attributes:
        pid: Identificador único del proceso.
        name: Nombre descriptivo.
        state: Estado actual del proceso.
        priority: Prioridad de planificación (menor valor = mayor prioridad).
        burst_time: Total de ráfagas de CPU requeridas.
        remaining_time: Ráfagas de CPU pendientes.
        arrival_time: Tick del sistema en el que el proceso fue creado.
        page_table: Mapeo página -> marco.  -1 indica que la página no
            está cargada en memoria física.
        num_pages: Cantidad total de páginas del proceso.
        waiting_time: Ticks acumulados en estado READY.
        turnaround_time: Ticks totales desde creación hasta terminación.
        cpu_time: Ticks acumulados en ejecución.
        start_time: Tick en que el proceso comenzó a ejecutarse por primera vez.
        finish_time: Tick en que el proceso terminó.
    """

    # --- Identificación ---
    pid: int
    name: str

    # --- Planificación ---
    state: ProcessState = ProcessState.NEW
    priority: int = 0
    burst_time: int = 0
    remaining_time: int = 0
    arrival_time: int = 0

    # --- Paginación ---
    page_table: list[int] = field(default_factory=list)
    num_pages: int = 0

    # --- Métricas ---
    waiting_time: int = 0
    turnaround_time: int = 0
    cpu_time: int = 0
    start_time: Optional[int] = None
    finish_time: Optional[int] = None
