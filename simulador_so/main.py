"""
Punto de entrada del Simulador de Sistema Operativo.

Lanza la interfaz grÃ¡fica.  El core se ensambla dentro de la UI sin mover
lÃ³gica de simulaciÃ³n a la capa de presentaciÃ³n.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.main_window import MainWindow


def main() -> None:
    """Lanza el dashboard del simulador."""
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
