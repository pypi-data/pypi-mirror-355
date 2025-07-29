from typing import Iterable, Tuple, Dict

import pygame as pg
import numpy as np

from viztools.coordinate_system import CoordinateSystem
from viztools.drawable import Drawable, _normalize_color


class Points(Drawable):
    def __init__(
            self, points: np.ndarray, size: int | float | Iterable[int | float] = 3,
            color: np.ndarray | None = None
    ):
        """
        Drawable to display a set of points.
        :param points: A list of points with the shape [N, 2] where N is the number of points.
        :param size: The radius of the points. If set to an integer, this is the radius on the screen in pixels. If set
                     to a float, this is the radius on the screen in units of the coordinate system. If set to a list,
                     it contains the sizes for each point.
        :param color: The color of the points.
        """
        # points
        if not isinstance(points, np.ndarray):
            raise TypeError(f'points must be a numpy array, not {type(points)}.')
        if points.ndim != 2 or points.shape[1] != 2:
            raise ValueError(f'points must be numpy array with shape (N, 2), not {points.shape}.')
        n_points = len(points)
        self._points = points

        # size
        if isinstance(size, (int, float)):
            is_relative_size = isinstance(size, float)
            size = np.repeat(np.array([[size, float(is_relative_size)]], dtype=np.float32), n_points, axis=0)
        elif isinstance(size, np.ndarray):
            if size.shape != (n_points,):
                raise ValueError(f'size must be a numpy array with shape ({n_points},), not {size.shape}.')
            is_relative_size = np.full(n_points, np.issubdtype(size.dtype, np.floating), dtype=np.float32)
            size = np.stack([size.astype(np.float32), is_relative_size], axis=1)
        elif isinstance(size, list):
            if len(size) != n_points:
                raise ValueError(f'size must be a list of length {n_points}, not {len(size)}.')
            size = [[s, isinstance(s, float)] for s in size]
            size = np.array(size, dtype=np.float32)
        else:
            raise TypeError(f'size must be an integer, float or iterable, not {type(size)}.')
        self._size = size

        # colors
        if color is None:
            color = np.array([77, 178, 11])
        if isinstance(color, np.ndarray):
            if color.shape == (3,):
                color = np.array([*color, 255], dtype=np.float32)
            if color.shape == (4,):
                color = np.repeat(color.reshape(1, -1), n_points, axis=0).astype(np.float32)
        else:
            color = np.array(color, dtype=np.float32)
        if color.shape != (n_points, 4):
            raise ValueError(f'colors must be a numpy array with shape ({n_points}, 4), not {color.shape}.')
        self._colors = color

        self._surface_parameters = {}
        for surf_params in self._get_surf_params():
            self._surface_parameters[surf_params.tobytes()] = surf_params

    def __len__(self):
        return len(self._points)

    def _get_surf_params(self) -> np.ndarray:
        return np.concatenate([self._size, self._colors], axis=1)

    def _get_surf_param(self, index: int) -> np.ndarray:
        return np.concatenate([self._size[index, :], self._colors[index, :]], axis=0)

    def set_color(self, color: np.ndarray | Tuple[int, int, int, int], index: int):
        self._colors[index, :] = _normalize_color(color)
        self._update_surf_params(index)

    def _update_surf_params(self, index: int):
        surf_params = self._get_surf_param(index)
        self._surface_parameters[surf_params.tobytes()] = surf_params

    def set_size(self, size: int | float, index: int):
        self._size[index, 0] = size
        self._size[index, 1] = isinstance(size, float)
        self._update_surf_params(index)

    def _create_point_surfaces(self, zoom_factor: float) -> Dict[bytes, pg.Surface]:
        surfaces = {}
        for k, surf_params in self._surface_parameters.items():
            draw_size = _get_draw_size(surf_params[0], zoom_factor, bool(surf_params[1]))
            color = surf_params[2:]

            # old version with per pixel alpha
            point_surface = pg.Surface((draw_size * 2, draw_size * 2), pg.SRCALPHA)
            pg.draw.circle(point_surface, color, (draw_size, draw_size), draw_size)

            surfaces[k] = point_surface
        return surfaces

    def _get_draw_sizes(self, zoom_factor: float) -> np.ndarray:
        """
        Computes the draw sizes for the given sizes and coordinate system.
        :param zoom_factor: A float defining the scale factor for relative sizes.
        size[i] must be multiplied with zoom_factor.
        :return: numpy array of integers of shape [N,] where N is the number of sizes.
        """
        draw_sizes = self._size[:, 0].copy()
        is_relative_size = self._size[:, 1] > 0.5
        draw_sizes[is_relative_size] *= zoom_factor
        return np.maximum(draw_sizes.astype(int), 1)

    def draw(self, screen: pg.Surface, coordinate_system: CoordinateSystem):
        draw_sizes = self._get_draw_sizes(coordinate_system.zoom_factor)
        screen_size = np.array(screen.get_size(), dtype=np.int32)

        # filter out invalid positions
        screen_points = coordinate_system.space_to_screen(self._points.T).T
        valid_positions = _get_valid_positions(screen_points, draw_sizes, screen_size)
        screen_points = screen_points[valid_positions]
        valid_colors = self._colors[valid_positions]
        valid_sizes = draw_sizes[valid_positions]
        screen_points -= valid_sizes.reshape(-1, 1)

        # create blit surfaces
        surfaces = self._create_point_surfaces(coordinate_system.zoom_factor)

        # draw
        for pos, size, color, surf_params in zip(
                screen_points, valid_sizes, valid_colors, self._get_surf_params()[valid_positions]
        ):
            surface = surfaces[surf_params.tobytes()]
            screen.blit(surface, pos)

    def clicked_points(self, event: pg.event.Event, coordinate_system: CoordinateSystem) -> np.ndarray:
        """
        Returns the indices of the points clicked by the mouse. Returns an empty array if no point was clicked.

        :param event: The event to check.
        :param coordinate_system: The coordinate system to use.
        """
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            return self.hovered_points(np.array(event.pos, dtype=np.int32), coordinate_system)
        return np.array([])

    def hovered_points(self, mouse_pos: np.ndarray, coordinate_system: CoordinateSystem) -> np.ndarray:
        draw_sizes = self._get_draw_sizes(coordinate_system.zoom_factor)

        screen_pos = mouse_pos.reshape(1, 2)
        screen_points = coordinate_system.space_to_screen(self._points.T).T
        distances = np.linalg.norm(screen_points - screen_pos, axis=1)
        return np.nonzero(distances < draw_sizes)[0]


def _get_draw_size(
        size: float, zoom_factor: float, is_relative_size: bool
) -> int:
    if is_relative_size:
        size = max(int(size * zoom_factor), 1)
    return int(size)


def _get_valid_positions(screen_points: np.ndarray, draw_sizes: np.ndarray, screen_size: np.ndarray) -> np.ndarray:
    return np.where(np.logical_and(
        np.logical_and(screen_points[:, 0] > -draw_sizes, (screen_points[:, 0] < screen_size[0] + draw_sizes)),
        np.logical_and(screen_points[:, 1] > -draw_sizes, (screen_points[:, 1] < screen_size[1] + draw_sizes))
    ))[0]
