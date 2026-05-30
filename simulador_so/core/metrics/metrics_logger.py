"""
Logger de métricas del simulador.

Se suscribe a eventos del EventBus para acumular estadísticas
por proceso y globales.  Permite exportar a CSV y TXT.
"""

from __future__ import annotations

import csv
from typing import Optional

from core.events.event import (
    CONTEXT_SWITCH,
    Event,
    FILE_CONFLICT,
    PAGE_FAULT,
    PAGE_HIT,
    PAGE_REPLACED,
)
from core.events.event_bus import EventBus
from core.metrics.process_metrics import ProcessMetrics
from core.models.process import Process


class MetricsLogger:
    """Registra y calcula métricas de la simulación.

    Se suscribe automáticamente a los eventos relevantes del EventBus
    al ser instanciado.

    Attributes:
        event_bus: Bus de eventos.
        process_metrics: Métricas por proceso, indexadas por PID.
        page_faults: Contador global de page faults.
        page_hits: Contador global de page hits.
        page_replacements: Contador global de reemplazos de página.
        file_conflicts: Contador global de conflictos de archivo.
        context_switches: Contador global de cambios de contexto.
        events_log: Lista cronológica de todos los eventos recibidos.
    """

    def __init__(self, event_bus: EventBus) -> None:
        self.event_bus = event_bus
        self.process_metrics: dict[int, ProcessMetrics] = {}
        self.page_faults: int = 0
        self.page_hits: int = 0
        self.page_replacements: int = 0
        self.file_conflicts: int = 0
        self.context_switches: int = 0
        self.events_log: list[Event] = []

        for event_type in (
            PAGE_HIT,
            PAGE_FAULT,
            PAGE_REPLACED,
            FILE_CONFLICT,
            CONTEXT_SWITCH,
        ):
            self.event_bus.subscribe(event_type, self._handle_event)

    def record_process(self, process: Process) -> None:
        """Registra las mÃ©tricas finales de un proceso terminado."""
        self.process_metrics[process.pid] = ProcessMetrics(
            pid=process.pid,
            arrival_time=process.arrival_time,
            start_time=process.start_time,
            finish_time=process.finish_time,
            waiting_time=process.waiting_time,
            turnaround_time=process.turnaround_time,
            cpu_time=process.cpu_time,
        )

    def _handle_event(self, event: Event) -> None:
        """Callback genérico para procesar eventos.

        Args:
            event: Evento recibido del bus.
        """
        self.events_log.append(event)
        if event.event_type == PAGE_HIT:
            self.page_hits += 1
        elif event.event_type == PAGE_FAULT:
            self.page_faults += 1
        elif event.event_type == PAGE_REPLACED:
            self.page_replacements += 1
        elif event.event_type == FILE_CONFLICT:
            self.file_conflicts += 1
        elif event.event_type == CONTEXT_SWITCH:
            self.context_switches += 1
        # TODO: Actualizar contadores según event_type

    def get_summary(self) -> dict:
        """Retorna un resumen de todas las métricas.

        Returns:
            Diccionario con métricas globales y por proceso.
        """
        processes_completed = len(self.process_metrics)
        total_waiting_time = sum(
            metric.waiting_time for metric in self.process_metrics.values()
        )
        total_turnaround_time = sum(
            metric.turnaround_time for metric in self.process_metrics.values()
        )
        avg_waiting_time = (
            total_waiting_time / processes_completed
            if processes_completed
            else 0.0
        )
        avg_turnaround_time = (
            total_turnaround_time / processes_completed
            if processes_completed
            else 0.0
        )

        return {
            "processes_completed": processes_completed,
            "avg_waiting_time": avg_waiting_time,
            "avg_turnaround_time": avg_turnaround_time,
            "page_faults": self.page_faults,
            "page_hits": self.page_hits,
            "page_replacements": self.page_replacements,
            "file_conflicts": self.file_conflicts,
            "context_switches": self.context_switches,
            "processes": {
                pid: {
                    "waiting_time": m.waiting_time,
                    "turnaround_time": m.turnaround_time,
                    "cpu_time": m.cpu_time,
                }
                for pid, m in self.process_metrics.items()
            },
        }

    def export_csv(self, path: str) -> None:
        """Exporta las métricas por proceso a un archivo CSV.

        Args:
            path: Ruta del archivo CSV a generar.
        """
        # TODO: Implementar exportación
        with open(path, mode="w", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(["pid", "waiting_time", "turnaround_time", "cpu_time"])

            for pid in sorted(self.process_metrics):
                metric = self.process_metrics[pid]
                writer.writerow([
                    metric.pid,
                    metric.waiting_time,
                    metric.turnaround_time,
                    metric.cpu_time,
                ])

    def export_txt(self, path: str) -> None:
        """Exporta un resumen de métricas a un archivo de texto.

        Args:
            path: Ruta del archivo TXT a generar.
        """
        # TODO: Implementar exportación
        summary = self.get_summary()

        lines = [
            "=" * 40,
            "SIMULADOR DE SISTEMA OPERATIVO",
            "=" * 40,
            "",
            f"PROCESOS FINALIZADOS: {summary['processes_completed']}",
            "",
            "CPU",
            "-" * 40,
            f"Waiting Time Promedio: {summary['avg_waiting_time']:.2f}",
            f"Turnaround Time Promedio: {summary['avg_turnaround_time']:.2f}",
            f"Context Switches: {summary['context_switches']}",
            "",
            "MEMORIA",
            "-" * 40,
            f"Page Faults: {summary['page_faults']}",
            f"Page Hits: {summary['page_hits']}",
            f"Page Replacements: {summary['page_replacements']}",
            "",
            "ARCHIVOS",
            "-" * 40,
            f"File Conflicts: {summary['file_conflicts']}",
            "",
            "DETALLE POR PROCESO",
            "-" * 40,
            "PID  WT  TT  CPU",
        ]

        for pid in sorted(self.process_metrics):
            metric = self.process_metrics[pid]
            lines.append(
                f"{metric.pid:<4} {metric.waiting_time:<3} "
                f"{metric.turnaround_time:<3} {metric.cpu_time:<3}"
            )

        with open(path, mode="w", encoding="utf-8") as txt_file:
            txt_file.write("\n".join(lines))
            txt_file.write("\n")
