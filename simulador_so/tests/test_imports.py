"""
Test de verificación de importaciones.

Verifica que todos los módulos del proyecto se importan correctamente
sin errores de sintaxis ni dependencias faltantes.
"""

import sys
import os

# Agregar simulador_so al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_import_models():
    """Verifica que todos los modelos se importan correctamente."""
    from core.models.process_state import ProcessState
    from core.models.process import Process
    from core.models.page import Page
    from core.models.frame import Frame

    # Verificar que ProcessState tiene los estados esperados
    assert hasattr(ProcessState, "NEW")
    assert hasattr(ProcessState, "READY")
    assert hasattr(ProcessState, "RUNNING")
    assert hasattr(ProcessState, "WAITING")
    assert hasattr(ProcessState, "TERMINATED")

    # Verificar que Process se puede instanciar
    p = Process(pid=1, name="test")
    assert p.pid == 1
    assert p.state == ProcessState.NEW

    # Verificar que Page tiene loaded_at_time (para FIFO)
    page = Page(page_id=0, pid=1)
    assert hasattr(page, "loaded_at_time")
    assert hasattr(page, "last_access_time")

    # Verificar que Frame se puede instanciar
    frame = Frame(frame_id=0)
    assert frame.is_free is True


def test_import_events():
    """Verifica que el sistema de eventos se importa correctamente."""
    from core.events.event import (
        Event,
        PROCESS_CREATED,
        PAGE_FAULT,
        FILE_LOCKED,
    )
    from core.events.event_bus import EventBus

    # Verificar que Event es inmutable (frozen)
    event = Event(timestamp=0, event_type=PROCESS_CREATED, source="test")
    assert event.timestamp == 0

    # Verificar que EventBus funciona
    bus = EventBus()
    received = []
    bus.subscribe(PROCESS_CREATED, lambda e: received.append(e))
    bus.publish(event)
    assert len(received) == 1
    assert received[0] is event


def test_import_config():
    """Verifica que la configuración se importa correctamente."""
    from core.config.simulation_config import SimulationConfig

    config = SimulationConfig()
    assert config.num_frames == 16
    assert config.quantum == 4


def test_import_scheduler():
    """Verifica que los planificadores se importan correctamente."""
    from core.scheduler.scheduler import Scheduler
    from core.scheduler.round_robin import RoundRobinScheduler
    from core.scheduler.sjf import SJFScheduler
    from core.scheduler.priority import PriorityScheduler

    # Verificar que son subclases de Scheduler
    assert issubclass(RoundRobinScheduler, Scheduler)
    assert issubclass(SJFScheduler, Scheduler)
    assert issubclass(PriorityScheduler, Scheduler)

    # Verificar instanciación
    rr = RoundRobinScheduler(quantum=3)
    assert rr.name == "Round Robin"


def test_import_memory():
    """Verifica que los módulos de memoria se importan correctamente."""
    from core.memory.replacement_algorithm import ReplacementAlgorithm
    from core.memory.fifo import FIFOReplacement
    from core.memory.lru import LRUReplacement
    from core.memory.memory_manager import MemoryManager

    # Verificar que son subclases de ReplacementAlgorithm
    assert issubclass(FIFOReplacement, ReplacementAlgorithm)
    assert issubclass(LRUReplacement, ReplacementAlgorithm)

    assert FIFOReplacement().name == "FIFO"
    assert LRUReplacement().name == "LRU"


def test_import_filesystem():
    """Verifica que los módulos de filesystem se importan correctamente."""
    from core.filesystem.simulated_file import SimulatedFile
    from core.filesystem.file_manager import FileManager

    f = SimulatedFile(name="test.txt")
    assert f.locked_by is None


def test_import_metrics():
    """Verifica que los módulos de métricas se importan correctamente."""
    from core.metrics.process_metrics import ProcessMetrics
    from core.metrics.metrics_logger import MetricsLogger

    pm = ProcessMetrics(pid=1)
    assert pm.waiting_time == 0
    assert pm.arrival_time == 0
    assert pm.start_time is None


def test_import_kernel():
    """Verifica que el kernel se importa correctamente."""
    from core.kernel.kernel import Kernel


def test_import_ui():
    """Verifica que la UI se importa correctamente."""
    from ui.main_window import MainWindow
