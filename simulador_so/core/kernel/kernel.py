"""
Kernel del sistema operativo simulado.

Orquestador principal que coordina todos los módulos del core.
Recibe todas sus dependencias mediante inyección en el constructor,
lo que permite intercambiar implementaciones sin modificar este código.
"""

from __future__ import annotations

from core.config.simulation_config import SimulationConfig
from core.cpu.cpu import CPU
from core.events.event import Event, CONTEXT_SWITCH, PROCESS_CREATED
from core.events.event_bus import EventBus
from core.filesystem.file_manager import FileManager
from core.memory.memory_manager import MemoryManager
from core.metrics.metrics_logger import MetricsLogger
from core.models.process import Process
from core.models.process_state import ProcessState
from core.scheduler.scheduler import Scheduler


class Kernel:
    """Orquestador principal del simulador de sistema operativo.

    Coordina la ejecución de la simulación tick a tick, delegando
    en los módulos especializados.

    Attributes:
        config: Configuración de la simulación.
        scheduler: Planificador de procesos inyectado.
        cpu: CPU simulada.
        memory_manager: Gestor de memoria.
        file_manager: Gestor de archivos.
        event_bus: Bus de eventos.
        metrics_logger: Logger de métricas.
        current_tick: Tick actual del sistema.
        running: Indica si la simulación está activa.
        processes: Todos los procesos creados, indexados por PID.
    """

    def __init__(
        self,
        config: SimulationConfig,
        scheduler: Scheduler,
        cpu: CPU,
        memory_manager: MemoryManager,
        file_manager: FileManager,
        event_bus: EventBus,
        metrics_logger: MetricsLogger,
    ) -> None:
        self.config = config
        self.scheduler = scheduler
        self.cpu = cpu
        self.memory_manager = memory_manager
        self.file_manager = file_manager
        self.event_bus = event_bus
        self.metrics_logger = metrics_logger
        self.current_tick: int = 0
        self.running: bool = False
        self.processes: dict[int, Process] = {}
        self._next_pid: int = 1
        self._quantum_used: int = 0
        self._last_running_pid: int | None = None
        self._file_holds: dict[int, tuple[str, int]] = {}

    def start(self) -> None:
        """Inicia la simulación."""
        self.running = True
        # TODO: Implementar bucle de simulación

    def stop(self) -> None:
        """Detiene la simulación."""
        self.running = False

    def tick(self) -> None:
        """Ejecuta un paso de la simulación.

        Este es el método central que coordina todos los módulos
        en cada tick del sistema.
        """
        # TODO: Implementar lógica del tick
        self._release_expired_file_locks()

        process = self.cpu.current_process

        if process is None:
            process = self.scheduler.get_next_process()
            self._quantum_used = 0

        if process is None:
            self.cpu.ticks_idle += 1
            self._last_running_pid = None
            self.current_tick += 1
            return

        if (
            self._last_running_pid is not None
            and self._last_running_pid != process.pid
        ):
            self.cpu.context_switches += 1
            self.event_bus.publish(Event(
                timestamp=self.current_tick,
                event_type=CONTEXT_SWITCH,
                source="Kernel",
                data={
                    "from_pid": self._last_running_pid,
                    "to_pid": process.pid,
                },
            ))

        process.state = ProcessState.RUNNING

        for other in self.processes.values():
            if other.state == ProcessState.READY:
                other.waiting_time += 1

        if process.num_pages > 0:
            page_number = process.cpu_time % process.num_pages
            self.memory_manager.current_tick = self.current_tick
            self.memory_manager.access_page(process.pid, page_number)

        self._simulate_file_access(process)
        self.cpu.execute_tick(process, self.current_tick)
        self._last_running_pid = process.pid

        if process.state == ProcessState.TERMINATED:
            self.memory_manager.deallocate_pages(process)
            self._release_process_file_lock(process.pid)
            self.metrics_logger.record_process(process)
            self.cpu.current_process = None
            self._quantum_used = 0
        else:
            self._quantum_used += 1
            if hasattr(self.scheduler, "quantum") and self._quantum_used >= self.config.quantum:
                process.state = ProcessState.READY
                self.scheduler.add_process(process)
                self.cpu.current_process = None

        for process in self.processes.values():
            if process.state != ProcessState.TERMINATED:
                process.turnaround_time = self.current_tick + 1 - process.arrival_time

        self.current_tick += 1

    def _simulate_file_access(self, process: Process) -> None:
        """Simula una solicitud simple de archivo para evidenciar mutex."""
        if process.cpu_time != 0 or process.pid in self._file_holds:
            return
        if not self.file_manager.files:
            return

        file_name = self._select_file_for_process(process)
        self.file_manager.current_tick = self.current_tick
        if self.file_manager.request_access(process.pid, file_name):
            hold_until = self.current_tick + self.config.quantum + 3
            self._file_holds[process.pid] = (file_name, hold_until)

    def _select_file_for_process(self, process: Process) -> str:
        """Selecciona un archivo objetivo para mostrar concurrencia visible."""
        usable_files = min(2, max(1, self.config.num_files))
        file_index = (process.pid - 1) % usable_files
        return f"archivo_{file_index}"

    def _release_expired_file_locks(self) -> None:
        """Libera archivos cuyo tiempo simulado de uso ya terminÃ³."""
        for pid, (file_name, release_tick) in list(self._file_holds.items()):
            if self.current_tick >= release_tick:
                self.file_manager.current_tick = self.current_tick
                self.file_manager.release_access(pid, file_name)
                del self._file_holds[pid]

    def _release_process_file_lock(self, pid: int) -> None:
        """Libera el archivo retenido por un proceso que termina."""
        hold = self._file_holds.pop(pid, None)
        if hold is None:
            return

        file_name, _ = hold
        self.file_manager.current_tick = self.current_tick + 1
        self.file_manager.release_access(pid, file_name)

    def create_process(
        self,
        name: str,
        burst_time: int,
        priority: int = 0,
    ) -> Process:
        """Crea un nuevo proceso y lo registra en el sistema.

        Args:
            name: Nombre del proceso.
            burst_time: Ráfagas de CPU requeridas.
            priority: Prioridad del proceso (menor = más prioritario).

        Returns:
            El proceso creado.
        """
        process = Process(
            pid=self._next_pid,
            name=name,
            state=ProcessState.READY,
            burst_time=burst_time,
            remaining_time=burst_time,
            priority=priority,
            arrival_time=self.current_tick,
            num_pages=self.config.pages_per_process,
            page_table=[-1] * self.config.pages_per_process,
        )
        self._next_pid += 1
        self.processes[process.pid] = process
        self.memory_manager.allocate_pages(process)
        self.scheduler.add_process(process)

        self.event_bus.publish(Event(
            timestamp=self.current_tick,
            event_type=PROCESS_CREATED,
            source="Kernel",
            data={"pid": process.pid, "name": name},
        ))

        return process
