"""
Gestor de memoria con paginación por demanda.

Administra marcos de memoria física, atiende solicitudes de páginas
y utiliza un ReplacementAlgorithm inyectado para manejar page faults
cuando no hay marcos libres.
"""

from __future__ import annotations

from core.config.simulation_config import SimulationConfig
from core.events.event import Event, PAGE_FAULT, PAGE_HIT, PAGE_REPLACED
from core.events.event_bus import EventBus
from core.memory.replacement_algorithm import ReplacementAlgorithm
from core.models.frame import Frame
from core.models.page import Page
from core.models.process import Process


class MemoryManager:
    """Gestor de memoria física simulada.

    Attributes:
        config: Configuración de la simulación.
        replacement: Algoritmo de reemplazo de páginas inyectado.
        event_bus: Bus de eventos.
        frames: Lista de marcos de memoria física.
        pages: Diccionario de páginas, indexado por (pid, page_id).
        current_tick: Tick actual del sistema.
    """

    def __init__(
        self,
        config: SimulationConfig,
        replacement: ReplacementAlgorithm,
        event_bus: EventBus,
    ) -> None:
        self.config = config
        self.replacement = replacement
        self.event_bus = event_bus
        self.frames: list[Frame] = [
            Frame(frame_id=i) for i in range(config.num_frames)
        ]
        self.pages: dict[tuple[int, int], Page] = {}
        self.processes: dict[int, Process] = {}
        self.current_tick: int = 0

    def access_page(self, pid: int, page_number: int) -> bool:
        """Accede a una página de un proceso.

        Args:
            pid: Identificador del proceso.
            page_number: Número de página a acceder.

        Returns:
            True si fue page hit, False si fue page fault.
        """
        # TODO: Implementar lógica de acceso a página
        key = (pid, page_number)
        if key not in self.pages:
            raise ValueError(f"Pagina no asignada: pid={pid}, page={page_number}")

        page = self.pages[key]

        if page.loaded:
            page.last_access_time = self.current_tick
            frame = self.frames[page.frame_id]
            self.replacement.on_page_access(frame)
            self.event_bus.publish(Event(
                timestamp=self.current_tick,
                event_type=PAGE_HIT,
                source="MemoryManager",
                data={
                    "pid": pid,
                    "page": page_number,
                    "frame": frame.frame_id,
                },
            ))
            return True

        self.event_bus.publish(Event(
            timestamp=self.current_tick,
            event_type=PAGE_FAULT,
            source="MemoryManager",
            data={"pid": pid, "page": page_number},
        ))

        frame = next((f for f in self.frames if f.is_free), None)
        if frame is None:
            frame = self.replacement.select_victim(self.frames)
            old_page = frame.page
            if old_page is not None:
                old_process = self.processes.get(old_page.pid)
                if old_process is not None:
                    old_process.page_table[old_page.page_id] = -1
                old_page.loaded = False
                old_page.frame_id = None

                self.event_bus.publish(Event(
                    timestamp=self.current_tick,
                    event_type=PAGE_REPLACED,
                    source="MemoryManager",
                    data={
                        "old_pid": old_page.pid,
                        "old_page": old_page.page_id,
                        "new_pid": pid,
                        "new_page": page_number,
                        "frame": frame.frame_id,
                    },
                ))

        page.loaded = True
        page.frame_id = frame.frame_id
        page.loaded_at_time = self.current_tick
        page.last_access_time = self.current_tick
        frame.page = page
        frame.is_free = False

        process = self.processes[pid]
        process.page_table[page_number] = frame.frame_id
        self.replacement.on_page_load(frame)
        return False

    def allocate_pages(self, process: Process) -> None:
        """Crea las entradas de página para un proceso nuevo.

        Args:
            process: Proceso al que asignar páginas.
        """
        # TODO: Implementar asignación inicial
        self.processes[process.pid] = process
        process.page_table = [-1] * process.num_pages

        for page_number in range(process.num_pages):
            self.pages[(process.pid, page_number)] = Page(
                page_id=page_number,
                pid=process.pid,
            )

    def deallocate_pages(self, process: Process) -> None:
        """Libera todas las páginas y marcos de un proceso terminado.

        Args:
            process: Proceso cuyas páginas se liberarán.
        """
        # TODO: Implementar liberación
        for page_number in range(process.num_pages):
            page = self.pages.get((process.pid, page_number))
            if page is None:
                continue

            if page.loaded and page.frame_id is not None:
                frame = self.frames[page.frame_id]
                frame.page = None
                frame.is_free = True

            page.loaded = False
            page.frame_id = None
            process.page_table[page_number] = -1
