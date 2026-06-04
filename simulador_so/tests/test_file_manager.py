import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.config.simulation_config import SimulationConfig
from core.cpu.cpu import CPU
from core.events.event import FILE_CONFLICT, FILE_LOCKED, FILE_UNLOCKED
from core.events.event_bus import EventBus
from core.filesystem.file_manager import FileManager
from core.kernel.kernel import Kernel
from core.memory.fifo import FIFOReplacement
from core.memory.memory_manager import MemoryManager
from core.metrics.metrics_logger import MetricsLogger
from core.models.process_state import ProcessState
from core.scheduler.round_robin import RoundRobinScheduler


def build_file_manager():
    config = SimulationConfig(num_files=1)
    event_bus = EventBus()
    file_manager = FileManager(config, event_bus)
    return file_manager, event_bus


def test_successful_lock_emits_file_locked_event():
    file_manager, event_bus = build_file_manager()
    events = []
    event_bus.subscribe(FILE_LOCKED, events.append)

    result = file_manager.request_access(pid=1, file_name="archivo_0")

    assert result is True
    assert file_manager.files["archivo_0"].locked_by == 1
    assert events[0].data == {"pid": 1, "file": "archivo_0"}


def test_conflict_emits_file_conflict_event():
    file_manager, event_bus = build_file_manager()
    events = []
    event_bus.subscribe(FILE_CONFLICT, events.append)

    assert file_manager.request_access(pid=1, file_name="archivo_0") is True
    result = file_manager.request_access(pid=2, file_name="archivo_0")

    assert result is False
    assert file_manager.files["archivo_0"].locked_by == 1
    assert events[0].data == {
        "pid": 2,
        "file": "archivo_0",
        "locked_by": 1,
    }


def test_release_unlocks_file_and_allows_next_process():
    file_manager, event_bus = build_file_manager()
    events = []
    event_bus.subscribe(FILE_UNLOCKED, events.append)

    assert file_manager.request_access(pid=1, file_name="archivo_0") is True
    file_manager.release_access(pid=1, file_name="archivo_0")
    result = file_manager.request_access(pid=2, file_name="archivo_0")

    assert file_manager.files["archivo_0"].locked_by == 2
    assert result is True
    assert events[0].data == {"pid": 1, "file": "archivo_0"}


def test_metrics_logger_counts_file_conflicts():
    file_manager, event_bus = build_file_manager()
    metrics = MetricsLogger(event_bus)

    file_manager.request_access(pid=1, file_name="archivo_0")
    file_manager.request_access(pid=2, file_name="archivo_0")
    file_manager.request_access(pid=3, file_name="archivo_0")

    assert metrics.get_summary()["file_conflicts"] == 2


def test_kernel_generates_file_lock_conflict_and_unlock_events():
    config = SimulationConfig(
        num_frames=3,
        pages_per_process=2,
        quantum=2,
        num_files=2,
    )
    event_bus = EventBus()
    scheduler = RoundRobinScheduler(quantum=config.quantum)
    cpu = CPU(event_bus)
    memory = MemoryManager(config, FIFOReplacement(), event_bus)
    file_manager = FileManager(config, event_bus)
    metrics = MetricsLogger(event_bus)
    kernel = Kernel(
        config=config,
        scheduler=scheduler,
        cpu=cpu,
        memory_manager=memory,
        file_manager=file_manager,
        event_bus=event_bus,
        metrics_logger=metrics,
    )
    events = []
    for event_type in (FILE_LOCKED, FILE_CONFLICT, FILE_UNLOCKED):
        event_bus.subscribe(event_type, events.append)

    processes = [
        kernel.create_process("P1", burst_time=6),
        kernel.create_process("P2", burst_time=3),
        kernel.create_process("P3", burst_time=4),
    ]

    while any(p.state != ProcessState.TERMINATED for p in processes):
        kernel.tick()

    event_types = [event.event_type for event in events]
    assert FILE_LOCKED in event_types
    assert FILE_CONFLICT in event_types
    assert FILE_UNLOCKED in event_types
    locked_files = {
        event.data["file"]
        for event in events
        if event.event_type == FILE_LOCKED
    }
    assert locked_files == {"archivo_0", "archivo_1"}
    assert any(
        event.event_type == FILE_CONFLICT
        and event.data["file"] == "archivo_0"
        and event.data["locked_by"] == 1
        for event in events
    )
    assert metrics.get_summary()["file_conflicts"] >= 1
    assert file_manager.files["archivo_0"].locked_by is None
    assert file_manager.files["archivo_1"].locked_by is None
