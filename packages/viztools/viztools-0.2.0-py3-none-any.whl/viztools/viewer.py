from abc import abstractmethod, ABC
from typing import Tuple, Optional, List

import numpy as np
import pygame as pg

from viztools.coordinate_system import DEFAULT_SCREEN_SIZE, CoordinateSystem, draw_coordinate_system
from viztools.drawable import Drawable
from viztools.render_backend import BackendType
from viztools.render_backend.events import Event, EventType
from viztools.render_backend.opengl_backend import OpenglBackend
from viztools.render_backend.pygame_backend import PygameBackend


class Viewer(ABC):
    def __init__(
            self, screen_size: Optional[Tuple[int, int]] = None, framerate: int = 60, font_size: int = 16,
            title: str = "Viewer", backend_type: BackendType = BackendType.PYGAME,
    ):
        if backend_type == BackendType.PYGAME:
            self.render_backend = PygameBackend()
        elif backend_type == BackendType.OPENGL:
            self.render_backend = OpenglBackend()
        else:
            raise ValueError(f'Invalid backend type: {backend_type}')
        self.render_backend.init()
        self.render_backend.set_key_repeat(130, 25)

        self.running = True
        self.render_needed = True
        self.clock = pg.time.Clock()
        self.framerate = framerate

        screen_size = screen_size or DEFAULT_SCREEN_SIZE
        self.screen = self.render_backend.create_window(title)

        self.coordinate_system = CoordinateSystem(screen_size)

        self.render_font = self.render_backend.get_font(font_size)

    def run(self):
        delta_time = 0
        while self.running:
            self._handle_events()
            self.tick(delta_time)
            if self.render_needed:
                self._render()
                self.render_needed = False
            delta_time = self.clock.tick(self.framerate)
        self.render_backend.quit()

    def tick(self, delta_time: float):
        pass

    @abstractmethod
    def render(self):
        pass

    def render_drawables(self, drawables: List[Drawable]):
        for drawable in drawables:
            drawable.draw(self.screen, self.coordinate_system, np.array(self.screen.get_size()), self.render_backend)

    def render_coordinate_system(self):
        draw_coordinate_system(self.screen, self.coordinate_system, self.render_font)

    def _render(self):
        self.render()
        self.render_backend.swap_buffers()

    def _handle_events(self):
        events = self.render_backend.get_events()
        for event in events:
            self.handle_event(event)

    @abstractmethod
    def handle_event(self, event: Event):
        if self.coordinate_system.handle_event(event):
            self.render_needed = True
        if event.type == EventType.QUIT:
            self.running = False
        if event.type in (EventType.WINDOWENTER, EventType.WINDOWFOCUSGAINED, EventType.WINDOWRESIZED):
            self.render_needed = True
