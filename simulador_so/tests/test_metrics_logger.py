import csv
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.events.event import (
    CONTEXT_SWITCH,
    Event,
    FILE_CONFLICT,
    PAGE_FAULT,
    PAGE_HIT,
    PAGE_REPLACED,
)
from core.events.event_bus import EventBus
from core.metrics.metrics_logger import MetricsLogger
from core.models.process import Process


def test_summary_counts_events_and_averages_process_metrics():
    event_bus = EventBus()
    metrics = MetricsLogger(event_bus)
    p1 = Process(
        pid=1,
        name="P1",
        waiting_time=2,
        turnaround_time=7,
        cpu_time=5,
    )
    p2 = Process(
        pid=2,
        name="P2",
        waiting_time=4,
        turnaround_time=9,
        cpu_time=5,
    )

    metrics.record_process(p1)
    metrics.record_process(p2)
    event_bus.publish(Event(0, PAGE_FAULT, "test"))
    event_bus.publish(Event(1, PAGE_FAULT, "test"))
    event_bus.publish(Event(2, PAGE_HIT, "test"))
    event_bus.publish(Event(3, PAGE_REPLACED, "test"))
    event_bus.publish(Event(4, FILE_CONFLICT, "test"))
    event_bus.publish(Event(5, CONTEXT_SWITCH, "test"))

    summary = metrics.get_summary()

    assert summary["processes_completed"] == 2
    assert summary["avg_waiting_time"] == 3.0
    assert summary["avg_turnaround_time"] == 8.0
    assert summary["page_faults"] == 2
    assert summary["page_hits"] == 1
    assert summary["page_replacements"] == 1
    assert summary["file_conflicts"] == 1
    assert summary["context_switches"] == 1
    assert summary["processes"][1] == {
        "waiting_time": 2,
        "turnaround_time": 7,
        "cpu_time": 5,
    }


def test_export_csv_generates_process_metrics_file(tmp_path):
    event_bus = EventBus()
    metrics = MetricsLogger(event_bus)
    metrics.record_process(Process(
        pid=1,
        name="P1",
        waiting_time=2,
        turnaround_time=7,
        cpu_time=5,
    ))
    metrics.record_process(Process(
        pid=2,
        name="P2",
        waiting_time=1,
        turnaround_time=3,
        cpu_time=2,
    ))
    csv_path = tmp_path / "metrics.csv"

    metrics.export_csv(str(csv_path))

    with open(csv_path, newline="", encoding="utf-8") as csv_file:
        rows = list(csv.reader(csv_file))

    assert rows == [
        ["pid", "waiting_time", "turnaround_time", "cpu_time"],
        ["1", "2", "7", "5"],
        ["2", "1", "3", "2"],
    ]


def test_export_txt_generates_summary_report(tmp_path):
    event_bus = EventBus()
    metrics = MetricsLogger(event_bus)
    metrics.record_process(Process(
        pid=1,
        name="P1",
        waiting_time=2,
        turnaround_time=7,
        cpu_time=5,
    ))
    event_bus.publish(Event(0, PAGE_FAULT, "test"))
    event_bus.publish(Event(1, PAGE_HIT, "test"))
    event_bus.publish(Event(2, FILE_CONFLICT, "test"))
    txt_path = tmp_path / "metrics.txt"

    metrics.export_txt(str(txt_path))

    content = txt_path.read_text(encoding="utf-8")
    assert "SIMULADOR DE SISTEMA OPERATIVO" in content
    assert "PROCESOS FINALIZADOS: 1" in content
    assert "Waiting Time Promedio: 2.00" in content
    assert "Turnaround Time Promedio: 7.00" in content
    assert "Page Faults: 1" in content
    assert "Page Hits: 1" in content
    assert "File Conflicts: 1" in content
    assert "1    2   7   5" in content
