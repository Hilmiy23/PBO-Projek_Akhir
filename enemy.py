import math
import random
import pygame
from settings import *
from bullet import Bullet
from entity import Entity


class Enemy(Entity):
    """
    A basic enemy that chases the player.

    Variants are created externally by passing different parameters;
    this keeps the class generic and avoids deep sub-class trees.

    Parameters
    ----------
    shoot_cd_max : int
        0 = melee-only enemy; >0 = can fire projectiles.
    """

    def __init__(
        self,
        x: float, y: float,
        speed: float,
        hp: int,
        damage: int,
        color: tuple,
        radius: int,
        shoot_cd_max: int = 0,
        bullet_speed: float = 0.0,
    ):
        super().__init__(x, y, radius)
        self._speed   = speed
        self._hp      = hp
        self._max_hp  = hp
        self._damage  = damage
        self._color   = color
        self.angle    = 0.0   # visual facing direction

        self.shoot_cd_max = shoot_cd_max
        self.shoot_cd     = random.randint(0, max(1, shoot_cd_max))
        self.bullet_speed = bullet_speed
        self.bullets: list[Bullet] = []

        # Temporary asset – kotak warna sesuai tipe enemy
        # Ganti dengan:
        #   self.image = pygame.image.load("assets/enemy_standard.png").convert_alpha()
        #   self.image = pygame.transform.scale(self.image, (self.radius*2, self.radius*2))
        self.image = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        pygame.draw.rect(self.image, self.color, (0, 0, self.radius * 2, self.radius * 2))

    @property
    def hp(self) -> int:
        return self._hp

    @property
    def max_hp(self) -> int:
        return self._max_hp

    @property
    def damage(self) -> int:
        return self._damage

    @property
    def color(self) -> tuple:
        return self._color

    @property
    def speed(self) -> float:
        return self._speed

    def update(self, px: float, py: float) -> None:
        # Move toward player
        dx, dy = px - self.x, py - self.y
        dist   = math.hypot(dx, dy)
        if dist > 0:
            self.angle = math.atan2(dy, dx)
            nx, ny     = dx / dist, dy / dist
            self._x    += nx * self._speed
            self._y    += ny * self._speed

        # Shoot
        if self.shoot_cd_max > 0:
            if self.shoot_cd <= 0:
                self._fire(px, py)
                self.shoot_cd = self.shoot_cd_max
            else:
                self.shoot_cd -= 1

        for b in self.bullets: b.update()
        self.bullets = [b for b in self.bullets if b.alive]

    def _fire(self, tx: float, ty: float) -> None:
        dx, dy = tx - self.x, ty - self.y
        dist   = math.hypot(dx, dy)
        if dist == 0:
            return
        nx, ny = dx / dist, dy / dist
        self.bullets.append(
            Bullet(
                self._x + nx * (self.radius + 6),
                self._y + ny * (self.radius + 6),
                nx, ny,
                self.bullet_speed, self.damage,
                ORANGE, 5, "enemy",
            )
        )

    def take_damage(self, dmg: int) -> None:
        self._hp -= dmg
        if self._hp <= 0:
            self._hp    = 0
            self._alive = False

    def draw(self, surface: pygame.Surface) -> None:
        ix, iy = int(self.x), int(self.y)

        # Sprite enemy (rotasi mengikuti arah gerak)
        rotated = pygame.transform.rotate(self.image, -math.degrees(self.angle))
        rect    = rotated.get_rect(center=(ix, iy))
        surface.blit(rotated, rect.topleft)

        # HP bar (only when damaged)
        if self.hp < self.max_hp:
            bw = self.radius * 2
            bx = ix - self.radius
            by = iy - self.radius - 9
            pygame.draw.rect(surface, GRAY, (bx, by, bw, 5))
            fw = int(bw * self.hp / self.max_hp)
            pygame.draw.rect(surface, RED,  (bx, by, fw, 5))

        # Bullets
        for b in self.bullets:
            b.draw(surface)


class Boss(Enemy):
    """
    A multi-phase boss.

    Phase 1  –  standard approach + single-shot.
    Phase 2  –  erratic movement + 3-way spread (at <= 50% HP).
    """

    def __init__(self, x: float, y: float, stage_number: int):
        # Scale hp / speed with stage
        tier  = max(1, stage_number // BOSS_EVERY_N_STAGES)
        hp    = BOSS_HP    + (tier - 1) * 12
        speed = BOSS_SPEED + (tier - 1) * 0.18

        super().__init__(
            x, y, speed, hp, BOSS_DAMAGE,
            PURPLE, BOSS_RADIUS,
            BOSS_SHOOT_COOLDOWN,
            ENEMY_BULLET_SPEED + 1.5,
        )
        self.phase        = 1
        self._phase_tick  = 0
        self.stage_number = stage_number

        # Temporary asset – kotak ungu lebih besar
        # Ganti dengan:
        #   self.image = pygame.image.load("assets/boss.png").convert_alpha()
        #   self.image = pygame.transform.scale(self.image, (self.radius*2, self.radius*2))
        self.image = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        pygame.draw.rect(self.image, PURPLE, (0, 0, self.radius * 2, self.radius * 2))

    def update(self, px: float, py: float) -> None:
        self._phase_tick += 1

        # Phase transition
        if self.hp <= self.max_hp * 0.5 and self.phase == 1:
            self.phase        = 2
            self.shoot_cd_max = max(22, BOSS_SHOOT_COOLDOWN // 2)
            # Ganti warna kotak saat phase 2 (hapus saat sudah pakai asset)
            self.image.fill((0, 0, 0, 0))
            pygame.draw.rect(self.image, RED,
                             (0, 0, self.radius * 2, self.radius * 2))

        # Movement
        dx, dy = px - self.x, py - self.y
        dist   = math.hypot(dx, dy)
        if dist > 0:
            base_angle  = math.atan2(dy, dx)
            self.angle  = base_angle

            if self.phase == 2:
                wobble   = math.sin(self._phase_tick * 0.045) * 0.7
                move_ang = base_angle + wobble
                spd      = self.speed * 1.35
            else:
                move_ang = base_angle
                spd      = self.speed

            self._x += math.cos(move_ang) * spd
            self._y += math.sin(move_ang) * spd

        # Shooting
        if self.shoot_cd <= 0:
            if self.phase == 2:
                self._fire_spread(px, py)
            else:
                self._fire(px, py)
            self.shoot_cd = self.shoot_cd_max
        else:
            self.shoot_cd -= 1

        for b in self.bullets: b.update()
        self.bullets = [b for b in self.bullets if b.alive]

    def _fire_spread(self, tx: float, ty: float) -> None:
        """3-way spread shot (phase 2)."""
        base = math.atan2(ty - self.y, tx - self.x)
        for offset in (-0.35, 0.0, 0.35):
            ang = base + offset
            self.bullets.append(
                Bullet(
                    self._x, self._y,
                    math.cos(ang), math.sin(ang),
                    self.bullet_speed, self.damage,
                    RED, 7, "enemy",
                )
            )

    def draw(self, surface: pygame.Surface) -> None:
        ix, iy = int(self.x), int(self.y)

        # Sprite boss
        rotated = pygame.transform.rotate(self.image, -math.degrees(self.angle))
        rect    = rotated.get_rect(center=(ix, iy))
        surface.blit(rotated, rect.topleft)

        # HP bar boss
        bw = self.radius * 5
        bx = ix - bw // 2
        by = iy - self.radius - 18
        pygame.draw.rect(surface, DARK_GRAY, (bx - 1, by - 1, bw + 2, 11))
        fw     = int(bw * self.hp / self.max_hp)
        bar_c  = RED if self.phase == 2 else PURPLE
        pygame.draw.rect(surface, bar_c, (bx, by, fw, 9))
        pygame.draw.rect(surface, WHITE, (bx, by, bw, 9), 1)

        # Bullets
        for b in self.bullets:
            b.draw(surface)