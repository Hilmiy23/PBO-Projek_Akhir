import random
import math
from settings import *
from enemy import Enemy, Boss


class Stage:
    """
    Encapsulates one stage of the game.

    Responsibilities
    ----------------
    - Track how many enemies need to be defeated.
    - Decide spawn timing, enemy variety, and difficulty scaling.
    - Flag completion so the Game can transition to the next stage.
    """

    def __init__(self, number: int):
        self.number        = number
        self.enemies_killed = 0
        self.is_boss_stage  = (number % BOSS_EVERY_N_STAGES == 0)
        self.boss_spawned   = False
        self.completed      = False

        # Normal-stage kill quota (scales up)
        self.kill_quota = ENEMIES_PER_STAGE + (number - 1) * 4

        # Spawn frequency (floor at 45 frames)
        self.spawn_interval = max(45, 130 - (number - 1) * 6)

        # Max simultaneous enemies on screen (boss stages allow fewer)
        if self.is_boss_stage:
            self.max_on_screen = 0   # boss only; no regular spawns
        else:
            self.max_on_screen = min(14, 3 + number)

    # ------------------------------------------------------------------
    # Difficulty helpers
    # ------------------------------------------------------------------

    def _enemy_speed(self) -> float:
        return ENEMY_BASE_SPEED + (self.number - 1) * 0.14

    def _enemy_hp(self) -> int:
        return max(1, ENEMY_HP + (self.number - 1) // 2)

    # ------------------------------------------------------------------
    # Spawning
    # ------------------------------------------------------------------

    def can_spawn(self, current_count: int) -> bool:
        return (not self.is_boss_stage) and (current_count < self.max_on_screen)

    def spawn_enemy(self) -> Enemy:
        """Create a regular enemy from a random off-screen edge."""
        side = random.randint(0, 3)
        margin = 30
        if side == 0:   x, y = random.randint(0, SCREEN_WIDTH), -margin
        elif side == 1: x, y = random.randint(0, SCREEN_WIDTH), SCREEN_HEIGHT + margin
        elif side == 2: x, y = -margin, random.randint(0, SCREEN_HEIGHT)
        else:           x, y = SCREEN_WIDTH + margin, random.randint(0, SCREEN_HEIGHT)

        hp    = self._enemy_hp()
        speed = self._enemy_speed()

        # Randomly pick a variant
        roll = random.random()
        if self.number >= 3 and roll < 0.15:
            # Tank – slow, high HP, no shooting
            return Enemy(x, y, speed * 0.55, hp + 3, ENEMY_DAMAGE + 1,
                         (180, 80, 30), ENEMY_RADIUS + 5)
        elif self.number >= 2 and roll < 0.35:
            # Shooter – slow, fires bullets
            return Enemy(x, y, speed * 0.65, hp + 1, ENEMY_DAMAGE,
                         (180, 80, 220), ENEMY_RADIUS - 1,
                         ENEMY_SHOOT_COOLDOWN, ENEMY_BULLET_SPEED)
        elif roll < 0.55:
            # Fast scout – very quick, low HP
            return Enemy(x, y, speed * 1.85, max(1, hp - 1), ENEMY_DAMAGE,
                         (255, 90, 90), ENEMY_RADIUS - 3)
        else:
            # Standard
            return Enemy(x, y, speed, hp, ENEMY_DAMAGE,
                         (210, 55, 55), ENEMY_RADIUS)

    def spawn_boss(self) -> Boss:
        self.boss_spawned = True
        return Boss(SCREEN_WIDTH // 2, -60, self.number)

    # ------------------------------------------------------------------
    # Progress tracking
    # ------------------------------------------------------------------

    def register_kill(self) -> None:
        self.enemies_killed += 1
        if not self.is_boss_stage and self.enemies_killed >= self.kill_quota:
            self.completed = True

    def register_boss_kill(self) -> None:
        self.completed = True