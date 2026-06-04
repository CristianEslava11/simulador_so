"""
Ventana principal del simulador.

La UI consume el core existente: crea procesos, avanza ticks y muestra el
estado actual de Kernel, memoria, archivos, eventos y métricas.
"""

from __future__ import annotations

import importlib
import queue
import random
import tkinter as tk
from tkinter import filedialog, ttk

try:
    ctk = importlib.import_module("customtkinter")
except ModuleNotFoundError:
    class _MissingCustomTkinter:
        CTk = object

    ctk = _MissingCustomTkinter()
    CUSTOMTKINTER_AVAILABLE = False
else:
    CUSTOMTKINTER_AVAILABLE = True

from core.config.simulation_config import SimulationConfig
from core.cpu.cpu import CPU
from core.events.event import (
    CONTEXT_SWITCH,
    FILE_CONFLICT,
    FILE_LOCKED,
    FILE_UNLOCKED,
    PAGE_FAULT,
    PAGE_HIT,
    PAGE_REPLACED,
    PROCESS_CREATED,
    PROCESS_FINISHED,
    PROCESS_STARTED,
)
from core.events.event_bus import EventBus
from core.filesystem.file_manager import FileManager
from core.kernel.kernel import Kernel
from core.memory.fifo import FIFOReplacement
from core.memory.lru import LRUReplacement
from core.memory.memory_manager import MemoryManager
from core.metrics.metrics_logger import MetricsLogger
from core.models.process_state import ProcessState
from core.scheduler.priority import PriorityScheduler
from core.scheduler.round_robin import RoundRobinScheduler
from core.scheduler.sjf import SJFScheduler


EVENT_TYPES = (
    PROCESS_CREATED,
    PROCESS_STARTED,
    PROCESS_FINISHED,
    CONTEXT_SWITCH,
    PAGE_HIT,
    PAGE_FAULT,
    PAGE_REPLACED,
    FILE_LOCKED,
    FILE_CONFLICT,
    FILE_UNLOCKED,
)

STATE_COLORS = {
    ProcessState.NEW.value: "#9ca3af",
    ProcessState.READY.value: "#3b82f6",
    ProcessState.RUNNING.value: "#22c55e",
    ProcessState.WAITING.value: "#eab308",
    ProcessState.TERMINATED.value: "#6b7280",
}


class MainWindow(ctk.CTk):
    """Dashboard principal del simulador."""

    def __init__(self, ui_queue: queue.Queue | None = None) -> None:
        if not CUSTOMTKINTER_AVAILABLE:
            raise RuntimeError(
                "CustomTkinter no esta instalado. Ejecuta: pip install -r requirements.txt"
            )

        super().__init__()
        self.ui_queue = ui_queue or queue.Queue()
        self.running = False
        self.event_log: list[str] = []
        self.process_counter = 0

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("Simulador de Sistema Operativo")
        self.geometry("1280x820")
        self.minsize(1100, 720)

        self.scheduler_var = tk.StringVar(value="Round Robin")
        self.replacement_var = tk.StringVar(value="FIFO")
        self.quantum_var = tk.StringVar(value="4")
        self.process_name_var = tk.StringVar(value="")
        self.burst_var = tk.StringVar(value="6")
        self.priority_var = tk.StringVar(value="1")

        self._configure_styles()
        self._build_kernel()
        self._build_layout()
        self._refresh_all()

    def _configure_styles(self) -> None:
        style = ttk.Style(self)
        style.theme_use("default")
        style.configure(
            "Treeview",
            background="#111827",
            foreground="#e5e7eb",
            fieldbackground="#111827",
            borderwidth=0,
            rowheight=26,
        )
        style.configure(
            "Treeview.Heading",
            background="#1f2937",
            foreground="#f9fafb",
            relief="flat",
        )
        style.map("Treeview", background=[("selected", "#2563eb")])

    def _build_kernel(self) -> None:
        scheduler_algorithm = {
            "Round Robin": "round_robin",
            "SJF": "sjf",
            "Priority": "priority",
        }[self.scheduler_var.get()]
        replacement_algorithm = self.replacement_var.get().lower()

        try:
            quantum = max(1, int(self.quantum_var.get()))
        except ValueError:
            quantum = 4
            self.quantum_var.set("4")

        self.config = SimulationConfig(
            num_frames=3,
            pages_per_process=2,
            quantum=quantum,
            scheduler_algorithm=scheduler_algorithm,
            replacement_algorithm=replacement_algorithm,
        )
        self.event_bus = EventBus()
        self.scheduler = self._make_scheduler()
        self.replacement = self._make_replacement()
        self.cpu = CPU(self.event_bus)
        self.memory_manager = MemoryManager(self.config, self.replacement, self.event_bus)
        self.file_manager = FileManager(self.config, self.event_bus)
        self.metrics_logger = MetricsLogger(self.event_bus)
        self.kernel = Kernel(
            config=self.config,
            scheduler=self.scheduler,
            cpu=self.cpu,
            memory_manager=self.memory_manager,
            file_manager=self.file_manager,
            event_bus=self.event_bus,
            metrics_logger=self.metrics_logger,
        )

        for event_type in EVENT_TYPES:
            self.event_bus.subscribe(event_type, self._handle_event)

    def _make_scheduler(self):
        if self.config.scheduler_algorithm == "round_robin":
            return RoundRobinScheduler(quantum=self.config.quantum)
        if self.config.scheduler_algorithm == "sjf":
            return SJFScheduler()
        return PriorityScheduler()

    def _make_replacement(self):
        if self.config.replacement_algorithm == "lru":
            return LRUReplacement()
        return FIFOReplacement()

    def _build_layout(self) -> None:
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(1, weight=1)

        self._build_top_panel()
        self._build_left_panel()
        self._build_right_panel()

    def _build_top_panel(self) -> None:
        panel = ctk.CTkFrame(self, fg_color="#111827")
        panel.grid(row=0, column=0, columnspan=2, sticky="ew", padx=12, pady=(12, 8))
        panel.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            panel,
            text="Simulador de Sistema Operativo",
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        title.grid(row=0, column=0, sticky="w", padx=14, pady=(12, 4))

        self.status_label = ctk.CTkLabel(panel, text="")
        self.status_label.grid(row=1, column=0, sticky="w", padx=14, pady=(0, 12))

        buttons = ctk.CTkFrame(panel, fg_color="transparent")
        buttons.grid(row=0, column=1, rowspan=2, sticky="e", padx=12)

        for index, (text, command) in enumerate((
            ("Iniciar", self.start_simulation),
            ("Pausar", self.pause_simulation),
            ("Tick Manual", self.manual_tick),
            ("Crear 5 Procesos", self.create_sample_processes),
            ("Reiniciar", self.restart_simulation),
            ("Exportar TXT", self.export_txt),
            ("Exportar CSV", self.export_csv),
        )):
            button = ctk.CTkButton(buttons, text=text, command=command, width=112)
            button.grid(row=index // 4, column=index % 4, padx=4, pady=4)

    def _build_left_panel(self) -> None:
        left = ctk.CTkFrame(self, fg_color="transparent")
        left.grid(row=1, column=0, sticky="nsew", padx=(12, 6), pady=(0, 12))
        left.grid_columnconfigure(0, weight=1)
        left.grid_rowconfigure(0, weight=2)
        left.grid_rowconfigure(1, weight=1)
        left.grid_rowconfigure(2, weight=1)

        self.process_tree = self._panel_tree(
            left,
            "Procesos",
            ("pid", "name", "state", "priority", "remaining", "waiting", "turnaround"),
            ("PID", "Nombre", "Estado", "Prioridad", "CPU restante", "WT", "TT"),
            row=0,
        )
        self.process_tree.tag_configure("RUNNING", foreground=STATE_COLORS["RUNNING"])
        self.process_tree.tag_configure("READY", foreground=STATE_COLORS["READY"])
        self.process_tree.tag_configure("WAITING", foreground=STATE_COLORS["WAITING"])
        self.process_tree.tag_configure("TERMINATED", foreground=STATE_COLORS["TERMINATED"])

        self.memory_tree = self._panel_tree(
            left,
            "Memoria",
            ("frame", "pid", "page"),
            ("Frame", "PID", "Pagina"),
            row=1,
        )

        self.event_text = self._event_panel(left, row=2)

    def _build_right_panel(self) -> None:
        right = ctk.CTkFrame(self, fg_color="transparent")
        right.grid(row=1, column=1, sticky="nsew", padx=(6, 12), pady=(0, 12))
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(2, weight=1)

        self._config_panel(right, row=0)
        self._cpu_metrics_panel(right, row=1)
        self.file_tree = self._panel_tree(
            right,
            "Archivos",
            ("file", "locked_by"),
            ("Archivo", "Bloqueado por PID"),
            row=2,
        )

    def _panel_tree(
        self,
        parent,
        title: str,
        columns: tuple[str, ...],
        headings: tuple[str, ...],
        row: int,
    ) -> ttk.Treeview:
        panel = ctk.CTkFrame(parent, fg_color="#111827")
        panel.grid(row=row, column=0, sticky="nsew", pady=(0, 8))
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(1, weight=1)

        label = ctk.CTkLabel(panel, text=title, font=ctk.CTkFont(size=16, weight="bold"))
        label.grid(row=0, column=0, sticky="w", padx=10, pady=(8, 4))

        tree = ttk.Treeview(panel, columns=columns, show="headings", height=7)
        for column, heading in zip(columns, headings):
            tree.heading(column, text=heading)
            tree.column(column, width=110, anchor="center")
        tree.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        return tree

    def _event_panel(self, parent, row: int) -> ctk.CTkTextbox:
        panel = ctk.CTkFrame(parent, fg_color="#111827")
        panel.grid(row=row, column=0, sticky="nsew", pady=(0, 8))
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(1, weight=1)

        label = ctk.CTkLabel(panel, text="Eventos", font=ctk.CTkFont(size=16, weight="bold"))
        label.grid(row=0, column=0, sticky="w", padx=10, pady=(8, 4))

        textbox = ctk.CTkTextbox(panel, fg_color="#020617", text_color="#e5e7eb")
        textbox.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        textbox.configure(state="disabled")
        return textbox

    def _config_panel(self, parent, row: int) -> None:
        panel = ctk.CTkFrame(parent, fg_color="#111827")
        panel.grid(row=row, column=0, sticky="ew", pady=(0, 8))
        for column in range(4):
            panel.grid_columnconfigure(column, weight=1)

        ctk.CTkLabel(panel, text="Configuracion", font=ctk.CTkFont(size=16, weight="bold")).grid(
            row=0, column=0, columnspan=4, sticky="w", padx=10, pady=(8, 4)
        )

        ctk.CTkLabel(panel, text="Planificador").grid(
            row=1, column=0, padx=8, pady=(4, 0), sticky="w"
        )
        ctk.CTkLabel(panel, text="Reemplazo memoria").grid(
            row=1, column=1, padx=8, pady=(4, 0), sticky="w"
        )
        ctk.CTkLabel(panel, text="Quantum (Round Robin)").grid(
            row=1, column=2, padx=8, pady=(4, 0), sticky="w"
        )
        ctk.CTkOptionMenu(
            panel,
            values=["Round Robin", "SJF", "Priority"],
            variable=self.scheduler_var,
            command=lambda _: self.restart_simulation(),
        ).grid(row=2, column=0, padx=8, pady=(2, 8), sticky="ew")
        ctk.CTkOptionMenu(
            panel,
            values=["FIFO", "LRU"],
            variable=self.replacement_var,
            command=lambda _: self.restart_simulation(),
        ).grid(row=2, column=1, padx=8, pady=(2, 8), sticky="ew")
        ctk.CTkEntry(panel, textvariable=self.quantum_var, placeholder_text="Ej: 2").grid(
            row=2, column=2, padx=8, pady=(2, 8), sticky="ew"
        )
        ctk.CTkButton(panel, text="Aplicar", command=self.restart_simulation).grid(
            row=2, column=3, padx=8, pady=(2, 8), sticky="ew"
        )

        ctk.CTkLabel(panel, text="Nombre proceso").grid(
            row=3, column=0, padx=8, pady=(2, 0), sticky="w"
        )
        ctk.CTkLabel(panel, text="Burst CPU").grid(
            row=3, column=1, padx=8, pady=(2, 0), sticky="w"
        )
        ctk.CTkLabel(panel, text="Prioridad").grid(
            row=3, column=2, padx=8, pady=(2, 0), sticky="w"
        )
        ctk.CTkEntry(panel, textvariable=self.process_name_var, placeholder_text="Ej: P1").grid(
            row=4, column=0, padx=8, pady=(2, 10), sticky="ew"
        )
        ctk.CTkEntry(panel, textvariable=self.burst_var, placeholder_text="Ej: 5").grid(
            row=4, column=1, padx=8, pady=(2, 10), sticky="ew"
        )
        ctk.CTkEntry(panel, textvariable=self.priority_var, placeholder_text="Ej: 1").grid(
            row=4, column=2, padx=8, pady=(2, 10), sticky="ew"
        )
        ctk.CTkButton(panel, text="Crear", command=self.create_process).grid(
            row=4, column=3, padx=8, pady=(2, 10), sticky="ew"
        )

    def _cpu_metrics_panel(self, parent, row: int) -> None:
        panel = ctk.CTkFrame(parent, fg_color="#111827")
        panel.grid(row=row, column=0, sticky="ew", pady=(0, 8))
        panel.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(panel, text="CPU y Métricas", font=ctk.CTkFont(size=16, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=10, pady=(8, 4)
        )
        self.cpu_label = ctk.CTkLabel(panel, text="", justify="left", anchor="w")
        self.cpu_label.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 6))

        self.cpu_progress = ctk.CTkProgressBar(panel)
        self.cpu_progress.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 10))
        self.cpu_progress.set(0)

        self.metrics_label = ctk.CTkLabel(panel, text="", justify="left", anchor="w")
        self.metrics_label.grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 10))

    def start_simulation(self) -> None:
        self.running = True
        self._schedule_tick()

    def pause_simulation(self) -> None:
        self.running = False

    def _schedule_tick(self) -> None:
        if not self.running:
            return
        if self._has_active_processes():
            self.kernel.tick()
            self._refresh_all()
        self.after(self.config.tick_duration_ms, self._schedule_tick)

    def manual_tick(self) -> None:
        if self._has_active_processes():
            self.kernel.tick()
            self._refresh_all()

    def create_process(self) -> None:
        self.process_counter += 1
        name = self.process_name_var.get().strip() or f"P{self.process_counter}"
        try:
            burst_time = max(1, int(self.burst_var.get()))
        except ValueError:
            burst_time = 5
            self.burst_var.set("5")
        try:
            priority = int(self.priority_var.get())
        except ValueError:
            priority = 0
            self.priority_var.set("0")

        self.kernel.create_process(name=name, burst_time=burst_time, priority=priority)
        self.process_name_var.set("")
        self._refresh_all()

    def create_sample_processes(self) -> None:
        """Crea cinco procesos de prueba con datos variados."""
        for _ in range(5):
            self.process_counter += 1
            self.kernel.create_process(
                name=f"P{self.process_counter}",
                burst_time=random.randint(2, 9),
                priority=random.randint(0, 4),
            )
        self._refresh_all()

    def restart_simulation(self) -> None:
        self.running = False
        self.event_log.clear()
        self.process_counter = 0
        self._build_kernel()
        self._refresh_all()

    def export_txt(self) -> None:
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")],
        )
        if path:
            self.metrics_logger.export_txt(path)

    def export_csv(self) -> None:
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
        )
        if path:
            self.metrics_logger.export_csv(path)

    def _has_active_processes(self) -> bool:
        return any(
            process.state != ProcessState.TERMINATED
            for process in self.kernel.processes.values()
        )

    def _handle_event(self, event) -> None:
        self.event_log.append(str(event))
        self.event_log = self.event_log[-250:]

    def _refresh_all(self) -> None:
        self._refresh_status()
        self._refresh_processes()
        self._refresh_cpu_metrics()
        self._refresh_memory()
        self._refresh_files()
        self._refresh_events()

    def _refresh_status(self) -> None:
        self.status_label.configure(
            text=(
                f"Scheduler: {self.scheduler.name}    "
                f"Reemplazo: {self.replacement.name}    "
                f"Tick: {self.kernel.current_tick}"
            )
        )

    def _refresh_processes(self) -> None:
        self.process_tree.delete(*self.process_tree.get_children())
        for process in self.kernel.processes.values():
            state = process.state.value
            self.process_tree.insert(
                "",
                "end",
                values=(
                    process.pid,
                    process.name,
                    state,
                    process.priority,
                    process.remaining_time,
                    process.waiting_time,
                    process.turnaround_time,
                ),
                tags=(state,),
            )

    def _refresh_cpu_metrics(self) -> None:
        current = self.cpu.current_process
        if current is None:
            current_text = "Proceso actual: CPU ociosa"
            progress = 0
        else:
            current_text = (
                f"Proceso actual: PID {current.pid} - {current.name}\n"
                f"Tiempo de CPU acumulado: {current.cpu_time}\n"
                f"CPU restante: {current.remaining_time}"
            )
            progress = current.cpu_time / current.burst_time if current.burst_time else 0

        self.cpu_label.configure(
            text=(
                f"{current_text}\n"
                f"Cambios de contexto: {self.metrics_logger.context_switches}\n"
                f"Utilización de CPU: {self.cpu.utilization:.2f}%"
            )
        )
        self.cpu_progress.set(min(1, progress))

        summary = self.metrics_logger.get_summary()
        self.metrics_label.configure(
            text=(
                "CPU\n"
                f"Tiempo de espera promedio: {summary['avg_waiting_time']:.2f}\n"
                f"Tiempo de retorno promedio: {summary['avg_turnaround_time']:.2f}\n\n"
                "Memoria\n"
                f"Fallos de página: {summary['page_faults']}\n"
                f"Aciertos de página: {summary['page_hits']}\n"
                f"Reemplazos de página: {summary['page_replacements']}\n\n"
                "Archivos\n"
                f"Conflictos de archivo: {summary['file_conflicts']}"
            )
        )

    def _refresh_memory(self) -> None:
        self.memory_tree.delete(*self.memory_tree.get_children())
        for frame in self.memory_manager.frames:
            if frame.page is None:
                values = (frame.frame_id, "Libre", "-")
            else:
                values = (frame.frame_id, frame.page.pid, frame.page.page_id)
            self.memory_tree.insert("", "end", values=values)

    def _refresh_files(self) -> None:
        self.file_tree.delete(*self.file_tree.get_children())
        for file_name, simulated_file in self.file_manager.files.items():
            locked_by = simulated_file.locked_by
            self.file_tree.insert(
                "",
                "end",
                values=(file_name, locked_by if locked_by is not None else "Libre"),
            )

    def _refresh_events(self) -> None:
        self.event_text.configure(state="normal")
        self.event_text.delete("1.0", "end")
        self.event_text.insert("end", "\n".join(self.event_log))
        self.event_text.see("end")
        self.event_text.configure(state="disabled")
