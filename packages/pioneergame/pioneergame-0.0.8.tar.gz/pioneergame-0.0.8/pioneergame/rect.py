import pygame as pg
from .window import Window


class Rect(pg.Rect):  # add class circle
    def __init__(self, window: Window, x, y, width, height,
                 color: str | pg.Color | tuple[int, int, int] = (255, 0, 255)):
        super().__init__(x, y, width, height)

        self.window = window
        self.color = color

    def draw(self) -> None:
        pg.draw.rect(self.window.screen, self.color, self)

    def draw_outline(self, color: str | pg.Color | tuple[int, int, int] = (255, 0, 255), width: int = 1):
        pg.draw.rect(self.window.screen, color, self, width)

    @property
    def pos(self) -> tuple[int, int]:
        return self.x, self.y

    # TODO: better collision checking and maybe some cool effects
