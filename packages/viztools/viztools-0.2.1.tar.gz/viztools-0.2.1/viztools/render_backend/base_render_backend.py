from abc import ABC, abstractmethod
from typing import Tuple, List, Self

import numpy as np

from .events import Event


class Surface(ABC):
    @abstractmethod
    def get_size(self) -> Tuple[int, int]:
        pass

    @abstractmethod
    def fill(self, color: np.ndarray):
        pass

    @abstractmethod
    def line(self, color: np.ndarray, start: Tuple[int, int] | np.ndarray, end: Tuple[int, int] | np.ndarray):
        pass

    @abstractmethod
    def circle(self, color: np.ndarray, pos: Tuple[int, int] | np.ndarray, radius: int | float):
        pass

    @abstractmethod
    def blit(self, surface: Self, pos: Tuple[int, int] | np.ndarray):
        pass


class Font(ABC):
    def __init__(self, font_name: str, font_size: int):
        self.font_name = font_name
        self.font_size = font_size

    @abstractmethod
    def render(self, text: str, color: np.ndarray, antialias: bool, background: np.ndarray = None) -> Surface:
        pass


class RenderBackend(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def init(self):
        pass

    @abstractmethod
    def quit(self):
        pass

    @abstractmethod
    def get_font(self, font_size: int, font_name: str) -> Font:
        pass

    @abstractmethod
    def set_key_repeat(self, delay: int, interval: int):
        pass

    @abstractmethod
    def create_window(self, title: str, size: Tuple[int, int] = (0, 0)) -> Surface:
        """
        Create a window with the given title and size. If size is (0, 0), the window will be full screen.
        :param title: The title of the window.
        :param size: The size of the window as (width, height).
        """
        pass

    @abstractmethod
    def create_surface(self, size: Tuple[int, int], enable_alpha: bool = True) -> Surface:
        pass

    @abstractmethod
    def swap_buffers(self):
        pass

    @abstractmethod
    def get_events(self) -> List[Event]:
        pass
