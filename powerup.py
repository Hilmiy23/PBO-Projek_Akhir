# ============================================================
#  powerup.py  –  Collectible power-up drops
# ============================================================

import math
import random
import pygame
from settings import *


class PowerUp:
    """
    A floating collectible that drops from defeated enemies.

    Types
    -----
    rapid_fire  – halves shooting cooldown for 6 s
    speed       – increases movement speed for 6 s
    shield      – absorbs damage for 6 s
    health      – instantly restores 2 HP
    """

    _TYPES: list[str] = ["rapid_fire", "speed", "shield", "health"]
    _WEIGHTS           = [30, 30, 20, 20]   # weighted random selection

    _COLOR: dict[str, tuple] = {
        "rapid_fire": YELLOW,
        "speed":      GREEN,
        "shield":     CYAN,
        "health":     RED,
    }
    _LABEL: dict[str, str] = {
        "rapid_fire": "RF",
        "speed":      "SP",
        "shield":     "SH",
        "health":     "HP",
    }

    LIFETIME = 420   # frames (~7 s)

    def __init__(self, x: float, y: float, kind: str | None = None):
        self.x      = float(x)
        self.y      = float(y)
        self.kind   = kind or random.choices(self._TYPES, self._WEIGHTS)[0]
        self.color  = self._COLOR[self.kind]
        self.label  = self._LABEL[self.kind]
        self.radius = 13
        self.alive  = True
        self.timer  = self.LIFETIME
        self._bob   = 0.0   # sin phase for bobbing animation

    # ------------------------------------------------------------------

    def update(self) -> None:
        self._bob += 0.08
        self.timer -= 1
        if self.timer <= 0:
            self.alive = False

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        if not self.alive:
            return

        bob_y = self.y + math.sin(self._bob) * 4
        ix, iy = int(self.x), int(bob_y)

        # Fade out in last 90 frames
        fade = min(255, self.timer * 3)

        # Glow
        g_r  = self.radius * 3
        glow = pygame.Surface((g_r * 2, g_r * 2), pygame.SRCALPHA)
        alpha = max(0, int(50 * abs(math.sin(self._bob))) * fade // 255)
        pygame.draw.circle(glow, (*self.color, alpha), (g_r, g_r), g_r)
        surface.blit(glow, (ix - g_r, iy - g_r))

        # Body
        body_surf = pygame.Surface(
            (self.radius * 2 + 2, self.radius * 2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(
            body_surf, (*self.color, fade),
            (self.radius + 1, self.radius + 1), self.radius)
        pygame.draw.circle(
            body_surf, (255, 255, 255, fade),
            (self.radius + 1, self.radius + 1), self.radius, 2)
        surface.blit(body_surf, (ix - self.radius - 1, iy - self.radius - 1))

        # Label
        txt = font.render(self.label, True,
                          (255, 255, 255, fade) if fade < 200 else WHITE)
        surface.blit(txt, (ix - txt.get_width() // 2,
                           iy - txt.get_height() // 2))

    # ------------------------------------------------------------------

    def collides_with(self, px: float, py: float, pr: float) -> bool:
        return math.hypot(self.x - px, self.y - py) < self.radius + pr