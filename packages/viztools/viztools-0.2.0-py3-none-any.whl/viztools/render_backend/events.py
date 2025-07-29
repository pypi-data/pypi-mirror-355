from enum import StrEnum

import numpy as np


class EventType(StrEnum):
    QUIT = 'QUIT'
    KEYDOWN = 'KEYDOWN'
    KEYUP = 'KEYUP'
    MOUSEBUTTONDOWN = 'MOUSEBUTTONDOWN'
    MOUSEBUTTONUP = 'MOUSEBUTTONUP'
    MOUSEMOTION = 'MOUSEMOTION'
    WINDOWENTER = 'WINDOWENTER'
    WINDOWFOCUSGAINED = 'WINDOWFOCUSGAINED'
    WINDOWRESIZED = 'WINDOWRESIZED'
    MOUSEWHEEL = 'MOUSEWHEEL'


class Event:
    def __init__(
            self, event_type: EventType, mouse_pos: np.ndarray | None = None, mouse_rel: np.ndarray | None = None,
            scroll: int | None = None, button: int | None = None,
    ):
        self.type = event_type
        self.mouse_pos = mouse_pos
        self.mouse_rel = mouse_rel
        self.scroll = scroll
        self.button = button
