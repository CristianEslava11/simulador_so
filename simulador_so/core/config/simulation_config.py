"""
Configuración de la simulación.

Centraliza todos los parámetros ajustables del simulador para que se
puedan modificar sin tocar código de los módulos.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SimulationConfig:
    """Parámetros configurables de la simulación.

    Attributes:
        num_frames: Cantidad de marcos en la memoria física.
        pages_per_process: Páginas asignadas a cada proceso.
        quantum: Quantum de tiempo para Round Robin (en ticks).
        scheduler_algorithm: Algoritmo de planificación ("round_robin", "sjf", "priority").
        replacement_algorithm: Algoritmo de reemplazo de páginas ("fifo", "lru").
        tick_duration_ms: Duración de un tick en milisegundos (controla velocidad visual).
        max_processes: Máximo de procesos simultáneos en el sistema.
        num_files: Cantidad de archivos simulados.
    """

    num_frames: int = 16
    pages_per_process: int = 8
    quantum: int = 4
    scheduler_algorithm: str = "round_robin"
    replacement_algorithm: str = "fifo"
    tick_duration_ms: int = 500
    max_processes: int = 10
    num_files: int = 5
