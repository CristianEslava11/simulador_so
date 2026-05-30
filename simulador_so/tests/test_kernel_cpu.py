import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.config.simulation_config import SimulationConfig
from core.cpu.cpu import CPU
from core.events.event import CONTEXT_SWITCH, PROCESS_FINISHED, PROCESS_STARTED
from core.events.event_bus import EventBus
from core.filesystem.file_manager import FileManager
from core.kernel.kernel import Kernel
from core.memory.fifo import FIFOReplacement
from core.memory.memory_manager import MemoryManager
from core.metrics.metrics_logger import MetricsLogger
from core.models.process_state import ProcessState
from core.scheduler.priority import PriorityScheduler
from core.scheduler.round_robin import RoundRobinScheduler
from core.scheduler.scheduler import Scheduler
from core.scheduler.sjf import SJFScheduler


def build_kernel(scheduler: Scheduler, quantum: int = 2):
    config = SimulationConfig(quantum=quantum)
    event_bus = EventBus()
    cpu = CPU(event_bus)
    memory_manager = MemoryManager(config, FIFOReplacement(), event_bus)
    file_manager = FileManager(config, event_bus)
    metrics_logger = MetricsLogger(event_bus)

    kernel = Kernel(
        config=config,
        scheduler=scheduler,
        cpu=cpu,
        memory_manager=memory_manager,
        file_manager=file_manager,
        event_bus=event_bus,
        metrics_logger=metrics_logger,
    )
    return kernel, event_bus


def run_until_finished(kernel: Kernel) -> None:
    while any(p.state != ProcessState.TERMINATED for p in kernel.processes.values()):
        kernel.tick()


def run_until_finished_with_trace(kernel: Kernel) -> list[int]:
    execution_order = []

    while any(p.state != ProcessState.TERMINATED for p in kernel.processes.values()):
        previous_cpu_time = {
            pid: process.cpu_time
            for pid, process in kernel.processes.items()
        }
        kernel.tick()

        executed = [
            pid
            for pid, process in kernel.processes.items()
            if process.cpu_time > previous_cpu_time[pid]
        ]
        assert len(executed) <= 1
        execution_order.extend(executed)

    return execution_order


def assert_metrics(process, waiting_time: int, turnaround_time: int, cpu_time: int) -> None:
    assert process.waiting_time == waiting_time
    assert process.turnaround_time == turnaround_time
    assert process.cpu_time == cpu_time
    assert process.remaining_time == 0
    assert process.state == ProcessState.TERMINATED


def test_process_runs_until_terminated_and_publishes_start_and_finish_events():
    kernel, event_bus = build_kernel(RoundRobinScheduler(quantum=4), quantum=4)
    events = []
    event_bus.subscribe(PROCESS_STARTED, events.append)
    event_bus.subscribe(PROCESS_FINISHED, events.append)

    process = kernel.create_process("P1", burst_time=3)

    assert process.state == ProcessState.READY

    run_until_finished(kernel)

    assert_metrics(process, waiting_time=0, turnaround_time=3, cpu_time=3)
    assert [event.event_type for event in events] == [
        PROCESS_STARTED,
        PROCESS_FINISHED,
    ]


def test_round_robin_controlled_scenario_metrics_and_context_switches():
    kernel, event_bus = build_kernel(RoundRobinScheduler(quantum=2), quantum=2)
    context_switches = []
    event_bus.subscribe(CONTEXT_SWITCH, context_switches.append)

    p1 = kernel.create_process("P1", burst_time=5)
    p2 = kernel.create_process("P2", burst_time=3)
    p3 = kernel.create_process("P3", burst_time=1)

    execution_order = run_until_finished_with_trace(kernel)

    # Gantt esperado con quantum=2:
    # P1 P1 | P2 P2 | P3 | P1 P1 | P2 | P1
    assert execution_order == [p1.pid, p1.pid, p2.pid, p2.pid, p3.pid, p1.pid, p1.pid, p2.pid, p1.pid]
    assert_metrics(p1, waiting_time=4, turnaround_time=9, cpu_time=5)
    assert_metrics(p2, waiting_time=5, turnaround_time=8, cpu_time=3)
    assert_metrics(p3, waiting_time=4, turnaround_time=5, cpu_time=1)
    assert kernel.current_tick == 9
    assert kernel.cpu.context_switches == 5
    assert len(context_switches) == 5
    assert [event.data for event in context_switches] == [
        {"from_pid": p1.pid, "to_pid": p2.pid},
        {"from_pid": p2.pid, "to_pid": p3.pid},
        {"from_pid": p3.pid, "to_pid": p1.pid},
        {"from_pid": p1.pid, "to_pid": p2.pid},
        {"from_pid": p2.pid, "to_pid": p1.pid},
    ]


def test_sjf_controlled_scenario_metrics_and_context_switches():
    kernel, _ = build_kernel(SJFScheduler(), quantum=2)

    p1 = kernel.create_process("P1", burst_time=5)
    p2 = kernel.create_process("P2", burst_time=2)
    p3 = kernel.create_process("P3", burst_time=1)

    execution_order = run_until_finished_with_trace(kernel)

    # Orden esperado SJF no preventivo: P3, P2, P1.
    assert execution_order == [p3.pid, p2.pid, p2.pid, p1.pid, p1.pid, p1.pid, p1.pid, p1.pid]
    assert_metrics(p3, waiting_time=0, turnaround_time=1, cpu_time=1)
    assert_metrics(p2, waiting_time=1, turnaround_time=3, cpu_time=2)
    assert_metrics(p1, waiting_time=3, turnaround_time=8, cpu_time=5)
    assert kernel.current_tick == 8
    assert kernel.cpu.context_switches == 2


def test_priority_controlled_scenario_metrics_and_context_switches():
    kernel, _ = build_kernel(PriorityScheduler(), quantum=2)

    p1 = kernel.create_process("P1", burst_time=3, priority=3)
    p2 = kernel.create_process("P2", burst_time=2, priority=1)
    p3 = kernel.create_process("P3", burst_time=1, priority=2)

    execution_order = run_until_finished_with_trace(kernel)

    # Menor valor numerico = mayor prioridad. Orden esperado: P2, P3, P1.
    assert execution_order == [p2.pid, p2.pid, p3.pid, p1.pid, p1.pid, p1.pid]
    assert_metrics(p2, waiting_time=0, turnaround_time=2, cpu_time=2)
    assert_metrics(p3, waiting_time=2, turnaround_time=3, cpu_time=1)
    assert_metrics(p1, waiting_time=3, turnaround_time=6, cpu_time=3)
    assert kernel.current_tick == 6
    assert kernel.cpu.context_switches == 2


def test_waiting_time_equals_turnaround_time_minus_cpu_time():
    kernel, _ = build_kernel(RoundRobinScheduler(quantum=2), quantum=2)

    processes = [
        kernel.create_process("P1", burst_time=5),
        kernel.create_process("P2", burst_time=3),
        kernel.create_process("P3", burst_time=1),
    ]

    run_until_finished(kernel)

    for process in processes:
        assert process.waiting_time == process.turnaround_time - process.cpu_time


def test_context_switches_ignore_round_robin_quantum_when_same_process_resumes():
    kernel, event_bus = build_kernel(RoundRobinScheduler(quantum=2), quantum=2)
    context_switches = []
    event_bus.subscribe(CONTEXT_SWITCH, context_switches.append)

    process = kernel.create_process("P1", burst_time=5)

    run_until_finished(kernel)

    assert_metrics(process, waiting_time=0, turnaround_time=5, cpu_time=5)
    assert kernel.cpu.context_switches == 0
    assert context_switches == []


def test_context_switches_do_not_count_after_idle_cpu_period():
    kernel, event_bus = build_kernel(RoundRobinScheduler(quantum=2), quantum=2)
    context_switches = []
    event_bus.subscribe(CONTEXT_SWITCH, context_switches.append)

    p1 = kernel.create_process("P1", burst_time=1)
    run_until_finished(kernel)
    kernel.tick()

    p2 = kernel.create_process("P2", burst_time=1)
    run_until_finished(kernel)

    assert_metrics(p1, waiting_time=0, turnaround_time=1, cpu_time=1)
    assert_metrics(p2, waiting_time=0, turnaround_time=1, cpu_time=1)
    assert kernel.cpu.context_switches == 0
    assert context_switches == []
