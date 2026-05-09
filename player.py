# ============================================================
#  player.py  –  Player entity with movement, shooting & HUD
# ============================================================

import math
import pygame
from settings import *
from bullet import Bullet


class Player:
    POWERUP_DURATION = 360   # 6 s at 60 fps

    def __init__(self, x: float, y: float):
        self.x      = float(x)
        self.y      = float(y)
        self.radius = PLAYER_RADIUS
        self.speed  = float(PLAYER_SPEED)
        self.hp     = PLAYER_HP
        self.max_hp = PLAYER_HP
        self.alive  = True
        self.angle  = 0.0

        self.shoot_cd     = 0
        self.shoot_cd_max = PLAYER_SHOOT_COOLDOWN
        self.bullets: list[Bullet] = []

        self.invincible = 0

        self.rapid_fire_timer  = 0
        self.speed_boost_timer = 0
        self.shield_timer      = 0

        # Roguelike skill tracker: {skill_id: stack_count}
        self.skills: dict[str, int] = {}

        self.image = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        pygame.draw.rect(self.image, BLUE, (0, 0, self.radius * 2, self.radius * 2))

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def has_rapid_fire(self) -> bool:
        return self.rapid_fire_timer > 0

    @property
    def has_speed_boost(self) -> bool:
        return self.speed_boost_timer > 0

    @property
    def has_shield(self) -> bool:
        return self.shield_timer > 0

    # ------------------------------------------------------------------
    # Skills
    # ------------------------------------------------------------------

    def apply_skill(self, skill_id: str) -> None:
        """Terapkan skill roguelike yang dipilih pemain."""
        self.skills[skill_id] = self.skills.get(skill_id, 0) + 1
        stack = self.skills[skill_id]

        if skill_id == "fire_rate_up":
            self.shoot_cd_max = max(4, PLAYER_SHOOT_COOLDOWN - stack * 2)
        elif skill_id == "speed_up":
            # Reset ke base lalu tambah per stack
            self.speed = PLAYER_SPEED + stack * 0.8
        elif skill_id == "max_hp_up":
            self.max_hp += 3
            self.hp = min(self.hp + 3, self.max_hp)
        # Skill lain ditangani secara dinamis saat digunakan:
        # damage_up → try_shoot
        # double_shot / triple_shot → try_shoot
        # piercing / bouncing → try_shoot (set flag pada Bullet)
        # lifesteal → game.py _on_enemy_killed
        # shield_up  → apply_powerup

    # ------------------------------------------------------------------
    # Input & movement
    # ------------------------------------------------------------------

    def handle_input(self, keys) -> None:
        spd = self.speed * (1.55 if self.has_speed_boost else 1.0)
        dx, dy = 0.0, 0.0

        if keys[pygame.K_w] or keys[pygame.K_UP]:    dy -= spd
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:  dy += spd
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:  dx -= spd
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx += spd

        if dx and dy:
            mag = math.hypot(dx, dy)
            dx, dy = dx / mag * spd, dy / mag * spd

        self.x = max(self.radius, min(SCREEN_WIDTH  - self.radius, self.x + dx))
        self.y = max(self.radius, min(SCREEN_HEIGHT - self.radius, self.y + dy))

        mx, my = pygame.mouse.get_pos()
        self.angle = math.atan2(my - self.y, mx - self.x)

    # ------------------------------------------------------------------
    # Shooting
    # ------------------------------------------------------------------

    def try_shoot(self) -> None:
        if self.shoot_cd > 0:
            return

        cd  = self.shoot_cd_max // 2 if self.has_rapid_fire else self.shoot_cd_max
        dmg = PLAYER_BULLET_DAMAGE + self.skills.get("damage_up", 0)

        # Tentukan sudut tembak berdasarkan skill multi-shot
        has_triple = "triple_shot" in self.skills
        has_double = "double_shot" in self.skills

        if has_triple:
            fire_angles = [self.angle - 0.22, self.angle, self.angle + 0.22]
        elif has_double:
            fire_angles = [self.angle - 0.12, self.angle + 0.12]
        else:
            fire_angles = [self.angle]

        for ang in fire_angles:
            c, s = math.cos(ang), math.sin(ang)
            bx   = self.x + c * (self.radius + 6)
            by   = self.y + s * (self.radius + 6)
            b    = Bullet(bx, by, c, s,
                          PLAYER_BULLET_SPEED, dmg, CYAN, 5, "player")
            b.piercing = "piercing" in self.skills
            b.bouncing = "bouncing" in self.skills
            self.bullets.append(b)

        self.shoot_cd = cd

    # ------------------------------------------------------------------
    # Damage & power-ups
    # ------------------------------------------------------------------

    def take_damage(self, damage: int) -> None:
        if self.invincible > 0 or self.has_shield:
            return
        self.hp -= damage
        self.invincible = 70
        if self.hp <= 0:
            self.hp    = 0
            self.alive = False

    def apply_powerup(self, kind: str) -> None:
        dur = self.POWERUP_DURATION
        if kind == "rapid_fire":
            self.rapid_fire_timer  = dur
        elif kind == "speed":
            self.speed_boost_timer = dur
        elif kind == "shield":
            # Skill Aegis Core melipatgandakan durasi shield
            mult = 3 if "shield_up" in self.skills else 1
            self.shield_timer = dur * mult
        elif kind == "health":
            self.hp = min(self.hp + 2, self.max_hp)

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self) -> None:
        if self.shoot_cd > 0:          self.shoot_cd -= 1
        if self.invincible > 0:        self.invincible -= 1
        if self.rapid_fire_timer > 0:  self.rapid_fire_timer -= 1
        if self.speed_boost_timer > 0: self.speed_boost_timer -= 1
        if self.shield_timer > 0:      self.shield_timer -= 1

        for b in self.bullets: b.update()
        self.bullets = [b for b in self.bullets if b.alive]

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------

    def draw(self, surface: pygame.Surface) -> None:
        if self.invincible > 0 and (self.invincible // 5) % 2 == 0:
            return

        ix, iy = int(self.x), int(self.y)

        rotated = pygame.transform.rotate(self.image, -math.degrees(self.angle))
        rect    = rotated.get_rect(center=(ix, iy))
        surface.blit(rotated, rect.topleft)

        if self.has_shield:
            pulse = int(200 + 55 * math.sin(pygame.time.get_ticks() * 0.008))
            pygame.draw.circle(surface, (0, pulse, pulse),
                               (ix, iy), self.radius + 18, 2)
        if self.has_rapid_fire:
            pygame.draw.circle(surface, YELLOW, (ix, iy), self.radius + 12, 2)
        if self.has_speed_boost:
            pygame.draw.circle(surface, GREEN,  (ix, iy), self.radius + 15, 2)

        for b in self.bullets:
            b.draw(surface)

    # ------------------------------------------------------------------
    # HUD
    # ------------------------------------------------------------------

    def draw_hud(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        bw, bh = 160, 16
        bx, by = 10, 10

        pygame.draw.rect(surface, GRAY, (bx, by, bw, bh), border_radius=5)
        ratio    = self.hp / self.max_hp
        r        = int(220 * (1 - ratio))
        g        = int(200 * ratio)
        hp_color = (r, g, 40)
        pygame.draw.rect(surface, hp_color,
                         (bx, by, int(bw * ratio), bh), border_radius=5)
        pygame.draw.rect(surface, WHITE, (bx, by, bw, bh), 2, border_radius=5)

        label = font.render(f"HP {self.hp}/{self.max_hp}", True, WHITE)
        surface.blit(label, (bx + 5, by + 2))

        # Power-up timers
        py = by + bh + 6
        if self.has_rapid_fire:
            t = font.render(f"RAPID {self.rapid_fire_timer // 60 + 1}s", True, YELLOW)
            surface.blit(t, (bx, py)); py += 18
        if self.has_speed_boost:
            t = font.render(f"SPEED {self.speed_boost_timer // 60 + 1}s", True, GREEN)
            surface.blit(t, (bx, py)); py += 18
        if self.has_shield:
            t = font.render(f"SHIELD {self.shield_timer // 60 + 1}s", True, CYAN)
            surface.blit(t, (bx, py)); py += 18

        # Skill HUD (daftar skill yang dimiliki)
        if self.skills:
            py += 4
            hdr = font.render("SKILLS", True, (160, 80, 220))
            surface.blit(hdr, (bx, py)); py += 18
            for sid, count in self.skills.items():
                sdef  = SKILL_DEFINITIONS[sid]
                label_str = sdef["name"]
                if count > 1:
                    label_str += f"  x{count}"
                s = font.render(label_str, True, sdef["color"])
                surface.blit(s, (bx, py)); py += 16