"""
Métricas por proceso.

Almacena los indicadores de rendimiento de un proceso individual
para generar reportes y gráficas.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class ProcessMetrics:
    """Métricas de rendimiento de un proceso.

    Attributes:
        pid: Identificador del proceso.
        arrival_time: Tick en que el proceso llegó al sistema.
        start_time: Tick en que comenzó a ejecutarse por primera vez.
        finish_time: Tick en que finalizó.
        waiting_time: Ticks acumulados en estado READY.
        turnaround_time: Ticks totales desde llegada hasta terminación.
        cpu_time: Ticks acumulados en ejecución.
    """

    pid: int
    arrival_time: int = 0
    start_time: Optional[int] = None
    finish_time: Optional[int] = None
    waiting_time: int = 0
    turnaround_time: int = 0
    cpu_time: int = 0
