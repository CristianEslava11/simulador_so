"""
Modelo de marco de memoria física (frame).

Representa una unidad de memoria física donde se puede cargar una página.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from core.models.page import Page


@dataclass
class Frame:
    """Marco de memoria física.

    Attributes:
        frame_id: Identificador único del marco.
        is_free: Indica si el marco está disponible.
        page: Página actualmente cargada en este marco (None si libre).
    """

    frame_id: int
    is_free: bool = True
    page: Optional[Page] = None
