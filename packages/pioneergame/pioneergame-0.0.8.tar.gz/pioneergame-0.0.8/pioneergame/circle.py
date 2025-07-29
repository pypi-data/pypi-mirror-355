import pygame as pg
from .window import Window


class Circle(pg.Rect):  # just to have some benefits, like colliderect method
    def __init__(self, window: Window, x, y, radius,
                 color: str | pg.Color | tuple[int, int, int] = (255, 0, 255), thickness: int = 0):
        super().__init__(x - radius, y - radius, radius * 2, radius * 2)

        self.window = window
        self.color = color
        self.thickness = thickness

    def draw(self) -> None:
        pg.draw.circle(self.window.screen, self.color, self.center, self.width / 2, self.thickness)

    def draw_box(self) -> None:
        pg.draw.rect(self.window.screen, self.color, self)

    def draw_outline(self, color: str | pg.Color | tuple[int, int, int] = (255, 0, 255), width: int = 1):
        pg.draw.rect(self.window.screen, color, self, width)

    # TODO: better collision checking and maybe some cool effects
