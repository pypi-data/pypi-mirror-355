import warnings
from typing import List, Tuple, Self

import numpy as np

try:
    import OpenGL.GL
    import OpenGL.GLU
    import OpenGL.GLUT
except ImportError:
    warnings.warn('OpenGL module not found, OpenGL backend will not be available.')
    OpenGL = None

from .base_render_backend import RenderBackend, Surface, Font
from .events import Event, EventType


class OpenglFont(Font):
    def __init__(self, font, font_name: str, font_size: int):
        super().__init__(font_name, font_size)
        self.font = font

    def render(self, text: str, color: np.ndarray, antialias: bool, background: np.ndarray = None) -> Surface:
        pass


class OpenglSurface(Surface):
    def __init__(self, surface):
        super().__init__()
        pass

    def get_size(self) -> Tuple[int, int]:
        pass

    def fill(self, color: np.ndarray):
        pass

    def line(self, color: np.ndarray, start: np.ndarray, end: np.ndarray):
        pass

    def circle(self, color: np.ndarray, pos: Tuple[int, int] | np.ndarray, radius: int):
        pass

    def blit(self, surface: Self, pos: Tuple[int, int]):
        pass


class OpenglBackend(RenderBackend):
    def init(self):
        OpenGL.GLUT.glutInit()
        OpenGL.GLUT.glutInitDisplayMode(OpenGL.GLUT.GLUT_RGBA | OpenGL.GLUT.GLUT_DOUBLE)

    def quit(self):
        OpenGL.GLUT.glutLeaveMainLoop()

    def get_font(self, font_size: int, font_name: str = '') -> OpenglFont:
        if font_name == '':
            font = OpenGL.GLUT.GLUT_BITMAP_HELVETICA_12 if font_size <= 12 else OpenGL.GLUT.GLUT_BITMAP_HELVETICA_18
        else:
            font = OpenGL.GLUT.GLUT_BITMAP_HELVETICA_12  # Default to Helvetica if custom font not found
        return OpenglFont(font, font_name, font_size)

    def set_key_repeat(self, delay: int, interval: int):
        # Not directly supported in OpenGL, would need custom implementation
        warnings.warn('set_key_repeat is not supported in OpenGL, ignoring call to set_key_repeat()')

    def create_window(self, title: str, size: Tuple[int, int] = (0, 0)) -> OpenglSurface:
        OpenGL.GLUT.glutInitWindowSize(*size)
        window = OpenGL.GLUT.glutCreateWindow(title)
        OpenGL.GL.glClearColor(0.0, 0.0, 0.0, 0.0)
        OpenGL.GL.glMatrixMode(OpenGL.GL.GL_PROJECTION)
        OpenGL.GL.glLoadIdentity()
        OpenGL.GLU.gluOrtho2D(0, size[0], size[1], 0)
        return OpenglSurface(window)

    def create_surface(self, size: Tuple[int, int], enable_alpha: bool = True) -> Surface:
        # Create an OpenGL texture/framebuffer object
        texture = OpenGL.GL.glGenTextures(1)
        OpenGL.GL.glBindTexture(OpenGL.GL.GL_TEXTURE_2D, texture)
        if enable_alpha:
            OpenGL.GL.glTexImage2D(OpenGL.GL.GL_TEXTURE_2D, 0, OpenGL.GL.GL_RGBA,
                                   size[0], size[1], 0, OpenGL.GL.GL_RGBA,
                                   OpenGL.GL.GL_UNSIGNED_BYTE, None)
        else:
            OpenGL.GL.glTexImage2D(OpenGL.GL.GL_TEXTURE_2D, 0, OpenGL.GL.GL_RGB,
                                   size[0], size[1], 0, OpenGL.GL.GL_RGB,
                                   OpenGL.GL.GL_UNSIGNED_BYTE, None)
        return OpenglSurface(texture)

    def swap_buffers(self):
        OpenGL.GLUT.glutSwapBuffers()

    def get_events(self) -> List[Event]:
        events = []
        while OpenGL.GLUT.glutMainLoopEvent():
            # Process GLUT events and convert them to our Event format
            event = Event(EventType.QUIT)  # Placeholder
            events.append(event)
        return events
