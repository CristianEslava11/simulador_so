"""
Gestor de archivos simulados.

Gestiona el acceso concurrente a archivos simulados y publica
eventos de bloqueo/desbloqueo/conflicto en el EventBus.
"""

from __future__ import annotations

from core.config.simulation_config import SimulationConfig
from core.events.event import Event, FILE_LOCKED, FILE_UNLOCKED, FILE_CONFLICT
from core.events.event_bus import EventBus
from core.filesystem.simulated_file import SimulatedFile


class FileManager:
    """Gestiona archivos simulados y su acceso concurrente.

    Attributes:
        config: Configuración de la simulación.
        event_bus: Bus de eventos.
        files: Diccionario de archivos simulados, indexado por nombre.
        current_tick: Tick actual del sistema.
    """

    def __init__(self, config: SimulationConfig, event_bus: EventBus) -> None:
        self.config = config
        self.event_bus = event_bus
        self.files: dict[str, SimulatedFile] = {
            f"archivo_{i}": SimulatedFile(name=f"archivo_{i}")
            for i in range(config.num_files)
        }
        self.current_tick: int = 0

    def request_access(self, pid: int, file_name: str) -> bool:
        """Solicita acceso exclusivo a un archivo.

        Args:
            pid: PID del proceso solicitante.
            file_name: Nombre del archivo.

        Returns:
            True si se otorgó el acceso, False si hay conflicto.
        """
        # TODO: Implementar lógica de acceso
        if file_name not in self.files:
            raise ValueError(f"Archivo no existe: {file_name}")

        simulated_file = self.files[file_name]
        acquired = simulated_file.acquire(pid)

        if acquired:
            self.event_bus.publish(Event(
                timestamp=self.current_tick,
                event_type=FILE_LOCKED,
                source="FileManager",
                data={"pid": pid, "file": file_name},
            ))
            return True

        self.event_bus.publish(Event(
            timestamp=self.current_tick,
            event_type=FILE_CONFLICT,
            source="FileManager",
            data={
                "pid": pid,
                "file": file_name,
                "locked_by": simulated_file.locked_by,
            },
        ))
        return False

    def release_access(self, pid: int, file_name: str) -> None:
        """Libera el acceso a un archivo.

        Args:
            pid: PID del proceso que libera.
            file_name: Nombre del archivo.
        """
        # TODO: Implementar lógica de liberación
        if file_name not in self.files:
            raise ValueError(f"Archivo no existe: {file_name}")

        simulated_file = self.files[file_name]
        if simulated_file.locked_by != pid:
            return

        simulated_file.release(pid)
        self.event_bus.publish(Event(
            timestamp=self.current_tick,
            event_type=FILE_UNLOCKED,
            source="FileManager",
            data={"pid": pid, "file": file_name},
        ))
