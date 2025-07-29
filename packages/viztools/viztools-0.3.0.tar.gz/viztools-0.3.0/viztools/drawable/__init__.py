from abc import ABC, abstractmethod
from typing import Tuple

import pygame as pg
import numpy as np

from viztools.coordinate_system import CoordinateSystem

Color = np.ndarray | Tuple[int, int, int, int] | Tuple[int, int, int]


class Drawable(ABC):
    @abstractmethod
    def draw(self, screen: pg.Surface, coordinate_system: CoordinateSystem):
        pass


def _normalize_color(color: Color) -> np.ndarray:
    if len(color) == 3:
        return np.array([*color, 255], dtype=np.float32)
    if len(color) != 4:
        raise ValueError(f'color must be of length 3 or 4, not {len(color)}.')
    return np.array(color, dtype=np.float32)
