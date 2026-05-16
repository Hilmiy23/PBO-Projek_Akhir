import abc
import math
import pygame


class Entity(abc.ABC):
    def __init__(self, x: float, y: float, radius: int):
        self._x = float(x)
        self._y = float(y)
        self._radius = radius
        self._alive = True

    @property
    def x(self) -> float:
        return self._x

    @property
    def y(self) -> float:
        return self._y

    @property
    def radius(self) -> int:
        return self._radius

    @property
    def alive(self) -> bool:
        return self._alive

    @property
    def position(self) -> tuple[float, float]:
        return self._x, self._y

    def kill(self) -> None:
        self._alive = False

    def collides_with(self, ox: float, oy: float, o_radius: float) -> bool:
        return math.hypot(self._x - ox, self._y - oy) < self._radius + o_radius

    @abc.abstractmethod
    def update(self, *args, **kwargs) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def draw(self, surface: pygame.Surface) -> None:
        raise NotImplementedError
