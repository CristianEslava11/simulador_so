"""
Enumeración de estados del ciclo de vida de un proceso.

Un proceso pasa por estos estados durante su ejecución en el simulador:
    NEW -> READY -> RUNNING -> TERMINATED
                 -> WAITING -> READY (ciclo de espera por E/S o recurso)
"""

from enum import Enum


class ProcessState(Enum):
    """Estados posibles de un proceso en el sistema operativo simulado."""

    NEW = "NEW"
    """Proceso recién creado, aún no ingresa a la cola de listos."""

    READY = "READY"
    """Proceso en cola de listos, esperando ser asignado a la CPU."""

    RUNNING = "RUNNING"
    """Proceso actualmente en ejecución en la CPU."""

    WAITING = "WAITING"
    """Proceso bloqueado esperando un recurso (E/S, archivo, etc.)."""

    TERMINATED = "TERMINATED"
    """Proceso finalizado, ya no requiere CPU."""
