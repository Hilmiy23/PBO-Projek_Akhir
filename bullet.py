import math
import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, YELLOW, ORANGE


class Bullet:
    BULLET_W = 8
    BULLET_H = 16

    def __init__(
        self,
        x: float, y: float,
        dx: float, dy: float,
        speed: float,
        damage: int,
        color: tuple,
        radius: int = 5,
        owner: str = "player",
    ):
        self.x      = x
        self.y      = y
        self.dx     = dx
        self.dy     = dy
        self.speed  = speed
        self.damage = damage
        self.color  = color
        self.radius = radius
        self.owner  = owner
        self.alive  = True
        self.angle  = math.degrees(math.atan2(dy, dx)) + 90

        # --- Skill flags ---
        self.piercing = False   # menembus musuh
        self.bouncing = False   # memantul dari tepi layar
        self.bounced  = False   # hanya memantul sekali

        bullet_color = YELLOW if owner == "player" else ORANGE
        self.image = pygame.Surface((self.BULLET_W, self.BULLET_H), pygame.SRCALPHA)
        pygame.draw.rect(self.image, bullet_color,
                         (0, 0, self.BULLET_W, self.BULLET_H))

    def update(self) -> None:
        self.x += self.dx * self.speed
        self.y += self.dy * self.speed

        # Pantulan dari tepi layar
        if self.bouncing and not self.bounced:
            hit_wall = False
            if self.x < 0 or self.x > SCREEN_WIDTH:
                self.dx = -self.dx
                self.x  = max(1.0, min(float(SCREEN_WIDTH - 1), self.x))
                hit_wall = True
            if self.y < 0 or self.y > SCREEN_HEIGHT:
                self.dy = -self.dy
                self.y  = max(1.0, min(float(SCREEN_HEIGHT - 1), self.y))
                hit_wall = True
            if hit_wall:
                self.bounced = True
                self.angle = math.degrees(math.atan2(self.dy, self.dx)) + 90

        margin = 60
        if (self.x < -margin or self.x > SCREEN_WIDTH  + margin or
                self.y < -margin or self.y > SCREEN_HEIGHT + margin):
            self.alive = False

    def draw(self, surface: pygame.Surface) -> None:
        if not self.alive:
            return
        rotated = pygame.transform.rotate(self.image, -self.angle)
        rect    = rotated.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(rotated, rect.topleft)

    def collides_with(self, ox: float, oy: float, o_radius: float) -> bool:
        return math.hypot(self.x - ox, self.y - oy) < self.radius + o_radius