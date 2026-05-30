import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.config.simulation_config import SimulationConfig
from core.cpu.cpu import CPU
from core.events.event import PAGE_FAULT, PAGE_HIT, PAGE_REPLACED
from core.events.event_bus import EventBus
from core.filesystem.file_manager import FileManager
from core.kernel.kernel import Kernel
from core.memory.fifo import FIFOReplacement
from core.memory.lru import LRUReplacement
from core.memory.memory_manager import MemoryManager
from core.metrics.metrics_logger import MetricsLogger
from core.models.process import Process
from core.models.process_state import ProcessState
from core.scheduler.round_robin import RoundRobinScheduler


def build_process(pid: int = 1, pages: int = 4) -> Process:
    return Process(
        pid=pid,
        name=f"P{pid}",
        burst_time=pages,
        remaining_time=pages,
        num_pages=pages,
        page_table=[-1] * pages,
    )


def build_memory(num_frames: int = 2, pages_per_process: int = 4, replacement=None):
    config = SimulationConfig(
        num_frames=num_frames,
        pages_per_process=pages_per_process,
    )
    event_bus = EventBus()
    memory = MemoryManager(config, replacement or FIFOReplacement(), event_bus)
    return memory, event_bus


def test_allocate_pages_creates_virtual_pages_without_loading_frames():
    memory, _ = build_memory(num_frames=2, pages_per_process=4)
    process = build_process(pages=4)

    memory.allocate_pages(process)

    assert process.page_table == [-1, -1, -1, -1]
    assert len(memory.pages) == 4
    assert all(not page.loaded for page in memory.pages.values())
    assert all(frame.is_free and frame.page is None for frame in memory.frames)


def test_page_fault_loads_page_into_free_frame():
    memory, event_bus = build_memory(num_frames=2, pages_per_process=4)
    process = build_process(pages=4)
    page_faults = []
    event_bus.subscribe(PAGE_FAULT, page_faults.append)
    memory.allocate_pages(process)

    result = memory.access_page(process.pid, 0)

    assert result is False
    assert process.page_table[0] == 0
    assert memory.pages[(process.pid, 0)].loaded is True
    assert memory.frames[0].page == memory.pages[(process.pid, 0)]
    assert page_faults[0].data == {"pid": process.pid, "page": 0}


def test_page_hit_updates_last_access_time_and_emits_event():
    memory, event_bus = build_memory(num_frames=2, pages_per_process=4)
    process = build_process(pages=4)
    page_hits = []
    event_bus.subscribe(PAGE_HIT, page_hits.append)
    memory.allocate_pages(process)

    memory.current_tick = 0
    memory.access_page(process.pid, 0)
    memory.current_tick = 5
    result = memory.access_page(process.pid, 0)

    page = memory.pages[(process.pid, 0)]
    assert result is True
    assert page.last_access_time == 5
    assert page_hits[0].data == {
        "pid": process.pid,
        "page": 0,
        "frame": process.page_table[0],
    }


def test_fifo_replaces_oldest_loaded_page():
    memory, event_bus = build_memory(num_frames=2, pages_per_process=3)
    process = build_process(pages=3)
    replacements = []
    event_bus.subscribe(PAGE_REPLACED, replacements.append)
    memory.allocate_pages(process)

    memory.current_tick = 0
    memory.access_page(process.pid, 0)
    memory.current_tick = 1
    memory.access_page(process.pid, 1)
    memory.current_tick = 2
    memory.access_page(process.pid, 2)

    assert process.page_table[0] == -1
    assert memory.pages[(process.pid, 0)].loaded is False
    assert memory.pages[(process.pid, 2)].loaded is True
    assert replacements[0].data == {
        "old_pid": process.pid,
        "old_page": 0,
        "new_pid": process.pid,
        "new_page": 2,
        "frame": 0,
    }


def test_lru_replaces_least_recently_used_page():
    memory, _ = build_memory(
        num_frames=2,
        pages_per_process=3,
        replacement=LRUReplacement(),
    )
    process = build_process(pages=3)
    memory.allocate_pages(process)

    memory.current_tick = 0
    memory.access_page(process.pid, 0)
    memory.current_tick = 1
    memory.access_page(process.pid, 1)
    memory.current_tick = 2
    memory.access_page(process.pid, 0)
    memory.current_tick = 3
    memory.access_page(process.pid, 2)

    assert memory.pages[(process.pid, 0)].loaded is True
    assert memory.pages[(process.pid, 1)].loaded is False
    assert memory.pages[(process.pid, 2)].loaded is True
    assert process.page_table[1] == -1


def test_metrics_logger_counts_memory_events():
    memory, event_bus = build_memory(num_frames=1, pages_per_process=2)
    metrics = MetricsLogger(event_bus)
    process = build_process(pages=2)
    memory.allocate_pages(process)

    memory.current_tick = 0
    memory.access_page(process.pid, 0)
    memory.current_tick = 1
    memory.access_page(process.pid, 0)
    memory.current_tick = 2
    memory.access_page(process.pid, 1)

    summary = metrics.get_summary()
    assert summary["page_faults"] == 2
    assert summary["page_hits"] == 1
    assert summary["page_replacements"] == 1


def test_kernel_accesses_memory_on_each_cpu_tick_and_frees_pages_on_finish():
    config = SimulationConfig(
        num_frames=2,
        pages_per_process=2,
        quantum=10,
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

    process = kernel.create_process("P1", burst_time=3)

    while process.state != ProcessState.TERMINATED:
        kernel.tick()

    summary = metrics.get_summary()
    assert summary["page_faults"] == 2
    assert summary["page_hits"] == 1
    assert summary["page_replacements"] == 0
    assert summary["processes_completed"] == 1
    assert summary["processes"][process.pid] == {
        "waiting_time": 0,
        "turnaround_time": 3,
        "cpu_time": 3,
    }
    assert process.page_table == [-1, -1]
    assert all(frame.is_free and frame.page is None for frame in memory.frames)
