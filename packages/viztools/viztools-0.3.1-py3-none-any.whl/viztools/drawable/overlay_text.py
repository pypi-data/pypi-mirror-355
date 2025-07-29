from enum import StrEnum

import pygame as pg
import numpy as np

from viztools.coordinate_system import CoordinateSystem
from viztools.drawable import Drawable


class OverlayPosition(StrEnum):
    TOP = 'top'
    LEFT = 'left'
    RIGHT = 'right'
    BOT = 'bot'
    RIGHTTOP = 'righttop'
    LEFTTOP = 'lefttop'
    LEFTBOT = 'leftbot'
    RIGHTBOT = 'rightbot'


class OverlayText(Drawable):
    def __init__(
            self, text: str, position: np.ndarray | OverlayPosition, font_name: str = '',
            font_size: int = 16, background_color: np.ndarray | None = None,
            border_color: np.ndarray | None = None, border_width: int = 2
    ):
        super().__init__()
        self.text = text
        self.position = position
        font_name = font_name or pg.font.get_default_font()
        self.font = pg.font.Font(font_name, font_size)
        self.background_color = background_color
        self.border_color = border_color
        self.border_width = border_width

    def draw(self, screen: pg.Surface, coordinate_system: CoordinateSystem):
        text_lines = self.text.split('\n')
        line_surfaces = [self.font.render(line, True, (255, 255, 255)) for line in text_lines]
        line_heights = [surface.get_height() for surface in line_surfaces]
        total_height = sum(line_heights)
        max_width = max(surface.get_width() for surface in line_surfaces)

        combined_rect = pg.Rect(0, 0, max_width, total_height)
        padding = self.border_width * 2 if self.border_color is not None else 0

        if isinstance(self.position, str):
            if self.position == OverlayPosition.TOP:
                combined_rect.midtop = (screen.get_width() // 2, 0)
            elif self.position == OverlayPosition.LEFT:
                combined_rect.midleft = (0, screen.get_height() // 2)
            elif self.position == OverlayPosition.RIGHT:
                combined_rect.midright = (screen.get_width()-padding, screen.get_height() // 2)
            elif self.position == OverlayPosition.BOT:
                combined_rect.midbottom = (screen.get_width() // 2, screen.get_height() - padding)
            elif self.position == OverlayPosition.RIGHTTOP:
                combined_rect.topright = (screen.get_width() - padding, 0)
            elif self.position == OverlayPosition.LEFTTOP:
                combined_rect.topleft = (0, 0)
            elif self.position == OverlayPosition.LEFTBOT:
                combined_rect.bottomleft = (0, screen.get_height() - padding)
            elif self.position == OverlayPosition.RIGHTBOT:
                combined_rect.bottomright = (screen.get_width() - padding, screen.get_height() - padding)
        else:
            combined_rect.topleft = self.position

        # Add padding for border
        combined_rect.width += padding
        combined_rect.height += padding

        if self.background_color is not None:
            background = pg.Surface(combined_rect.size, pg.SRCALPHA)
            background.fill(self.background_color)
            screen.blit(background, combined_rect)

        if self.border_color is not None:
            border_surface = pg.Surface(screen.get_size(), pg.SRCALPHA)
            pg.draw.rect(border_surface, self.border_color, combined_rect, self.border_width)
            screen.blit(border_surface, (0, 0))

        current_y = combined_rect.y + (padding // 2)
        for surface in line_surfaces:
            line_rect = surface.get_rect()
            line_rect.centerx = combined_rect.centerx
            line_rect.y = current_y
            screen.blit(surface, line_rect)
            current_y += line_rect.height
