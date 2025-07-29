from abc import ABC, abstractmethod
from typing import Tuple

import numpy as np

from viztools.coordinate_system import CoordinateSystem
from viztools.render_backend.base_render_backend import Surface, RenderBackend

Color = np.ndarray | Tuple[int, int, int, int] | Tuple[int, int, int]


class Drawable(ABC):
    @abstractmethod
    def draw(
            self, screen: Surface, coordinate_system: CoordinateSystem, screen_size: np.ndarray,
            render_backend: RenderBackend
    ):
        pass


def _normalize_color(color: Color) -> np.ndarray:
    if len(color) == 3:
        return np.array([*color, 255], dtype=np.float32)
    if len(color) != 4:
        raise ValueError(f'color must be of length 3 or 4, not {len(color)}.')
    return np.array(color, dtype=np.float32)


