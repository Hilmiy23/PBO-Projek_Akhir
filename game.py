# ============================================================
#  game.py  –  Game engine: loop, states, collision, rendering
# ============================================================

import sys
import math
import random
import pygame

from settings import *
from player    import Player
from enemy     import Enemy, Boss
from stage     import Stage
from powerup   import PowerUp
from highscore import HighScoreManager


# ------------------------------------------------------------------ #
#  Particle                                                            #
# ------------------------------------------------------------------ #

class Particle:
    __slots__ = ("x", "y", "dx", "dy", "color", "life", "max_life", "r")

    def __init__(self, x: float, y: float, color: tuple, r: int = 4):
        self.x    = float(x)
        self.y    = float(y)
        ang       = random.uniform(0, math.pi * 2)
        spd       = random.uniform(1.2, 5.5)
        self.dx   = math.cos(ang) * spd
        self.dy   = math.sin(ang) * spd
        self.color     = color
        self.life      = random.randint(18, 40)
        self.max_life  = self.life
        self.r         = r

    def update(self) -> None:
        self.x   += self.dx
        self.y   += self.dy
        self.dx  *= 0.93
        self.dy   = self.dy * 0.93 + 0.12
        self.life -= 1

    def draw(self, surface: pygame.Surface) -> None:
        frac  = self.life / self.max_life
        alpha = int(255 * frac)
        r     = max(1, int(self.r * frac))
        s     = pygame.Surface((r * 2 + 1, r * 2 + 1), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, alpha), (r, r), r)
        surface.blit(s, (int(self.x) - r, int(self.y) - r))


# ------------------------------------------------------------------ #
#  Game                                                                 #
# ------------------------------------------------------------------ #

class Game:
    """
    States
    ------
    intro        – title screen
    playing      – active gameplay
    skill_select – pilih skill setelah boss mati   ← BARU
    stage_clear  – transisi antar stage
    game_over    – game over overlay
    """

    # Dimensi kartu skill
    _CARD_W   = 200
    _CARD_H   = 248
    _CARD_GAP = 24

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()

        self.f_huge  = pygame.font.SysFont("monospace", 56, bold=True)
        self.f_large = pygame.font.SysFont("monospace", 38, bold=True)
        self.f_mid   = pygame.font.SysFont("monospace", 26, bold=True)
        self.f_small = pygame.font.SysFont("monospace", 15)
        self.f_tiny  = pygame.font.SysFont("monospace", 13)

        self.hs = HighScoreManager()

        self.stars = [
            (random.randint(0, SCREEN_WIDTH),
             random.randint(0, SCREEN_HEIGHT),
             random.randint(1, 2),
             random.uniform(0.001, 0.004))
            for _ in range(100)
        ]

        self.state = "intro"
        self._reset_game()

    # ----------------------------------------------------------------
    # Reset
    # ----------------------------------------------------------------

    def _reset_game(self) -> None:
        self.player    = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.enemies:  list[Enemy]    = []
        self.powerups: list[PowerUp]  = []
        self.particles: list[Particle] = []
        self.boss:     Boss | None    = None

        self.score         = 0
        self.stage_num     = 1
        self.stage         = Stage(self.stage_num)
        self.spawn_timer   = 0
        self.cleared_stage = 0
        self.sc_timer      = 0
        self.new_hs        = False

        # Skill select state
        self.skill_options: list[str] = []   # 3 skill ID yang ditampilkan

    # ----------------------------------------------------------------
    # Helpers
    # ----------------------------------------------------------------

    def _burst(self, x: float, y: float, color: tuple,
                count: int = 12, r: int = 4) -> None:
        for _ in range(count):
            self.particles.append(Particle(x, y, color, r))

    # ----------------------------------------------------------------
    # Skill card helpers
    # ----------------------------------------------------------------

    def _skill_card_rects(self) -> list[pygame.Rect]:
        """Kembalikan daftar Rect untuk setiap kartu skill."""
        n         = len(self.skill_options)
        total_w   = n * self._CARD_W + (n - 1) * self._CARD_GAP
        start_x   = SCREEN_WIDTH  // 2 - total_w // 2
        card_y    = SCREEN_HEIGHT // 2 - self._CARD_H // 2 + 30
        return [
            pygame.Rect(start_x + i * (self._CARD_W + self._CARD_GAP),
                        card_y, self._CARD_W, self._CARD_H)
            for i in range(n)
        ]

    def _get_clicked_card(self, pos: tuple) -> int | None:
        for i, rect in enumerate(self._skill_card_rects()):
            if rect.collidepoint(pos):
                return i
        return None

    def _generate_skill_options(self) -> None:
        """Pilih 3 skill secara acak yang belum dimaksimalkan."""
        available = [
            sid for sid, sdef in SKILL_DEFINITIONS.items()
            if self.player.skills.get(sid, 0) < sdef["max_stack"]
        ]
        count = min(3, len(available))
        self.skill_options = random.sample(available, count) if count else []

    def _on_skill_selected(self, skill_id: str) -> None:
        self.player.apply_skill(skill_id)
        self.skill_options = []
        self.stage.register_boss_kill()   # tandai stage selesai
        self._advance_stage()

    # ----------------------------------------------------------------
    # Events
    # ----------------------------------------------------------------

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._quit()

            if event.type == pygame.KEYDOWN:
                if self.state == "intro":
                    self.state = "playing"
                elif self.state == "game_over":
                    if event.key == pygame.K_r:
                        self._reset_game()
                        self.state = "playing"
                    elif event.key in (pygame.K_ESCAPE, pygame.K_q):
                        self._quit()
                elif self.state == "playing":
                    if event.key == pygame.K_ESCAPE:
                        self._quit()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.state == "intro":
                    self.state = "playing"
                elif self.state == "skill_select":
                    idx = self._get_clicked_card(event.pos)
                    if idx is not None:
                        self._on_skill_selected(self.skill_options[idx])

    # ----------------------------------------------------------------
    # Update
    # ----------------------------------------------------------------

    def _update(self) -> None:
        if self.state == "playing":
            self._update_playing()
        elif self.state == "stage_clear":
            self.sc_timer -= 1
            if self.sc_timer <= 0:
                self.state = "playing"
        elif self.state == "skill_select":
            pass   # game di-freeze, menunggu pilihan

    def _update_playing(self) -> None:
        keys = pygame.key.get_pressed()
        self.player.handle_input(keys)

        if pygame.mouse.get_pressed()[0]:
            self.player.try_shoot()
        self.player.update()

        if not self.player.alive:
            self.new_hs = self.hs.update(self.score)
            self._burst(self.player.x, self.player.y, CYAN, 35, 5)
            self.state = "game_over"
            return

        # Spawn musuh
        if self.stage.is_boss_stage and not self.stage.boss_spawned:
            self.spawn_timer += 1
            if self.spawn_timer >= 90:
                self.boss = self.stage.spawn_boss()
        elif not self.stage.is_boss_stage:
            self.spawn_timer += 1
            if self.spawn_timer >= self.stage.spawn_interval:
                self.spawn_timer = 0
                if self.stage.can_spawn(len(self.enemies)):
                    self.enemies.append(self.stage.spawn_enemy())

        # Update musuh biasa
        for enemy in self.enemies:
            enemy.update(self.player.x, self.player.y)
            self._check_enemy_vs_player(enemy)

        # Update boss
        if self.boss and self.boss.alive:
            self.boss.update(self.player.x, self.player.y)
            self._check_enemy_vs_player(self.boss)

        # Peluru pemain vs musuh (mendukung piercing)
        for bullet in self.player.bullets:
            if not bullet.alive:
                continue

            for enemy in self.enemies:
                if enemy.alive and bullet.collides_with(
                        enemy.x, enemy.y, enemy.radius):
                    if not bullet.piercing:
                        bullet.alive = False   # peluru berhenti di musuh pertama
                    enemy.take_damage(bullet.damage)
                    self._burst(enemy.x, enemy.y, enemy.color, 8)
                    if not enemy.alive:
                        self._on_enemy_killed(enemy)
                    if not bullet.alive:
                        break   # berhenti cek musuh lain jika bukan piercing

            if bullet.alive and self.boss and self.boss.alive:
                if bullet.collides_with(self.boss.x, self.boss.y, self.boss.radius):
                    if not bullet.piercing:
                        bullet.alive = False
                    self.boss.take_damage(bullet.damage)
                    self._burst(self.boss.x, self.boss.y, PURPLE, 6)
                    if not self.boss.alive:
                        self._on_boss_killed()

        # Power-up
        for pu in self.powerups:
            pu.update()
            if pu.alive and pu.collides_with(
                    self.player.x, self.player.y, self.player.radius):
                self.player.apply_powerup(pu.kind)
                pu.alive = False
                self._burst(int(pu.x), int(pu.y), pu.color, 10)

        # Partikel
        for p in self.particles: p.update()

        # Bersihkan objek mati
        self.enemies   = [e for e in self.enemies   if e.alive]
        self.powerups  = [p for p in self.powerups  if p.alive]
        self.particles = [p for p in self.particles if p.life > 0]

        # Cek stage selesai (hanya stage biasa; boss stage ditangani via skill select)
        if self.stage.completed:
            self._advance_stage()

    # ----------------------------------------------------------------
    # Collision helpers
    # ----------------------------------------------------------------

    def _check_enemy_vs_player(self, enemy: Enemy) -> None:
        for bullet in enemy.bullets:
            if bullet.alive and bullet.collides_with(
                    self.player.x, self.player.y, self.player.radius):
                bullet.alive = False
                self.player.take_damage(bullet.damage)
                self._burst(self.player.x, self.player.y, RED, 6)

        if math.hypot(enemy.x - self.player.x,
                      enemy.y - self.player.y) < enemy.radius + self.player.radius:
            self.player.take_damage(enemy.damage)
            self._burst(self.player.x, self.player.y, ORANGE, 4)

    # ----------------------------------------------------------------
    # Kill callbacks
    # ----------------------------------------------------------------

    def _on_enemy_killed(self, enemy: Enemy) -> None:
        self.score += SCORE_PER_KILL
        self.stage.register_kill()
        if random.random() < 0.14:
            self.powerups.append(PowerUp(enemy.x, enemy.y))
        # Lifesteal skill
        if "lifesteal" in self.player.skills and random.random() < 0.30:
            self.player.hp = min(self.player.hp + 1, self.player.max_hp)

    def _on_boss_killed(self) -> None:
        """
        Setelah boss mati → tampilkan skill select.
        register_boss_kill() dipanggil setelah pemain memilih skill.
        """
        self.score += SCORE_PER_BOSS_KILL
        self._burst(self.boss.x, self.boss.y, PURPLE, 50, 6)
        if random.random() < 0.6:
            self.powerups.append(PowerUp(self.boss.x, self.boss.y))

        self._generate_skill_options()
        if self.skill_options:
            self.state = "skill_select"
        else:
            # Semua skill sudah dimaks → langsung lanjut
            self.stage.register_boss_kill()

    # ----------------------------------------------------------------
    # Stage progression
    # ----------------------------------------------------------------

    def _advance_stage(self) -> None:
        self.score        += SCORE_PER_STAGE
        self.cleared_stage = self.stage_num
        self.stage_num    += 1
        self.stage         = Stage(self.stage_num)
        self.boss          = None
        self.enemies.clear()
        self.spawn_timer   = 0
        self.sc_timer      = 150
        self.state         = "stage_clear"

    # ----------------------------------------------------------------
    # Drawing
    # ----------------------------------------------------------------

    def _draw(self) -> None:
        self._draw_background()

        if self.state in ("playing", "stage_clear", "game_over", "skill_select"):
            for pu in self.powerups: pu.draw(self.screen, self.f_tiny)
            for en in self.enemies:  en.draw(self.screen)
            if self.boss and self.boss.alive:
                self.boss.draw(self.screen)
            for pt in self.particles: pt.draw(self.screen)
            self.player.draw(self.screen)
            self._draw_hud()

        if   self.state == "intro":        self._draw_intro()
        elif self.state == "skill_select": self._draw_skill_select()
        elif self.state == "stage_clear":  self._draw_stage_clear()
        elif self.state == "game_over":    self._draw_game_over()

        pygame.display.flip()

    def _draw_background(self) -> None:
        self.screen.fill((0, 0, 0))

    # ---- HUD -------------------------------------------------------

    def _draw_hud(self) -> None:
        self.player.draw_hud(self.screen, self.f_small)

        sc_surf = self.f_mid.render(f"SCORE {self.score:07d}", True, WHITE)
        self.screen.blit(sc_surf, (SCREEN_WIDTH - sc_surf.get_width() - 10, 10))

        hs_surf = self.f_small.render(
            f"BEST  {self.hs.high_score:07d}", True, YELLOW)
        self.screen.blit(hs_surf, (SCREEN_WIDTH - hs_surf.get_width() - 10, 40))

        stg = self.f_small.render(f"STAGE  {self.stage_num}", True, CYAN)
        self.screen.blit(stg, (SCREEN_WIDTH // 2 - stg.get_width() // 2, 10))

        if self.stage.is_boss_stage:
            lbl = self.f_small.render("!! BOSS STAGE !!", True, RED)
            self.screen.blit(lbl, (SCREEN_WIDTH // 2 - lbl.get_width() // 2, 28))
        else:
            ratio = self.stage.enemies_killed / max(1, self.stage.kill_quota)
            pw, ph = 140, 7
            px2, py2 = SCREEN_WIDTH // 2 - pw // 2, 28
            pygame.draw.rect(self.screen, GRAY,  (px2, py2, pw, ph), border_radius=3)
            pygame.draw.rect(self.screen, CYAN,
                             (px2, py2, int(pw * ratio), ph), border_radius=3)
            cnt = self.f_tiny.render(
                f"{self.stage.enemies_killed}/{self.stage.kill_quota}", True, LIGHT_GRAY)
            self.screen.blit(cnt, (SCREEN_WIDTH // 2 - cnt.get_width() // 2, 38))

        if self.boss and self.boss.alive:
            bw, bh2 = 320, 14
            bx2 = SCREEN_WIDTH // 2 - bw // 2
            by2 = SCREEN_HEIGHT - 55
            pygame.draw.rect(self.screen, DARK_GRAY, (bx2 - 2, by2 - 2, bw + 4, bh2 + 4))
            bc = RED if self.boss.phase == 2 else PURPLE
            pygame.draw.rect(self.screen, bc,
                             (bx2, by2, int(bw * self.boss.hp / self.boss.max_hp), bh2))
            pygame.draw.rect(self.screen, WHITE, (bx2, by2, bw, bh2), 1)
            blbl = self.f_small.render(
                f"BOSS   {self.boss.hp} / {self.boss.max_hp}", True, WHITE)
            self.screen.blit(blbl, (SCREEN_WIDTH // 2 - blbl.get_width() // 2, by2 - 20))

    # ---- Skill Select UI -------------------------------------------

    @staticmethod
    def _wrap_text(font: pygame.font.Font, text: str,
                   max_width: int) -> list[str]:
        """Pecah teks menjadi daftar baris agar muat dalam max_width px."""
        words  = text.split()
        lines: list[str] = []
        current = ""
        for word in words:
            test = (current + " " + word).strip()
            if font.size(test)[0] <= max_width:
                current = test
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines

    @staticmethod
    def _fit_text(font_big: pygame.font.Font, font_small: pygame.font.Font,
                  text: str, max_width: int) -> tuple[pygame.Surface, bool]:
        """Render teks; pakai font kecil jika terlalu lebar."""
        s = font_big.render(text, True, (0, 0, 0))
        if s.get_width() <= max_width:
            return s, False
        return font_small.render(text, True, (0, 0, 0)), True

    def _draw_skill_select(self) -> None:
        t = pygame.time.get_ticks()

        # Overlay gelap
        ov = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 18, 210))
        self.screen.blit(ov, (0, 0))

        # Header
        self._shadow_text(self.f_large, "BOSS DEFEATED!",
                          SCREEN_WIDTH // 2, 80, YELLOW)
        sub = self.f_mid.render("Choose an Upgrade", True, CYAN)
        self.screen.blit(sub, (SCREEN_WIDTH // 2 - sub.get_width() // 2, 128))

        mx, my = pygame.mouse.get_pos()
        rects  = self._skill_card_rects()

        PAD = 14   # padding horizontal dalam kartu

        for i, (sid, rect) in enumerate(zip(self.skill_options, rects)):
            sdef      = SKILL_DEFINITIONS[sid]
            color     = sdef["color"]
            hovered   = rect.collidepoint(mx, my)
            stack     = self.player.skills.get(sid, 0)
            max_stk   = sdef["max_stack"]
            inner_w   = rect.w - PAD * 2   # lebar isi kartu

            # Glow saat hover
            if hovered:
                pulse  = 0.55 + 0.45 * math.sin(t * 0.007)
                g_pad  = int(10 + 5 * pulse)
                glow_s = pygame.Surface(
                    (rect.w + g_pad * 2, rect.h + g_pad * 2), pygame.SRCALPHA)
                pygame.draw.rect(
                    glow_s, (*color, int(70 * pulse)),
                    (0, 0, rect.w + g_pad * 2, rect.h + g_pad * 2),
                    border_radius=20)
                self.screen.blit(glow_s, (rect.x - g_pad, rect.y - g_pad))

            # Latar kartu
            bg = (42, 42, 66) if hovered else (24, 24, 40)
            pygame.draw.rect(self.screen, bg, rect, border_radius=14)

            # Header band berwarna (atas 64px)
            hdr_rect = pygame.Rect(rect.x, rect.y, rect.w, 64)
            pygame.draw.rect(self.screen, color, hdr_rect, border_radius=14)
            pygame.draw.rect(self.screen, color,
                             (rect.x, rect.y + 50, rect.w, 14))

            # ── Nama skill: otomatis pakai f_small jika terlalu lebar ──
            name_s, _ = self._fit_text(
                self.f_mid, self.f_small, sdef["name"], inner_w)
            self.screen.blit(name_s,
                             (rect.x + rect.w // 2 - name_s.get_width() // 2,
                              rect.y + 14))

            # Tag badge
            tag_s = self.f_tiny.render(sdef["tag"], True, (20, 20, 20))
            tx = rect.x + rect.w // 2 - tag_s.get_width() // 2
            ty = rect.y + 46
            badge = pygame.Surface(
                (tag_s.get_width() + 10, tag_s.get_height() + 3), pygame.SRCALPHA)
            badge.fill((0, 0, 0, 90))
            self.screen.blit(badge, (tx - 5, ty - 1))
            self.screen.blit(tag_s, (tx, ty))

            # ── Deskripsi: word-wrap agar tidak keluar kartu ──
            desc_lines = self._wrap_text(self.f_tiny, sdef["desc"], inner_w)
            line_h     = self.f_tiny.get_linesize()
            desc_y     = rect.y + 80
            for line in desc_lines:
                dl = self.f_tiny.render(line, True, LIGHT_GRAY)
                self.screen.blit(dl,
                                 (rect.x + rect.w // 2 - dl.get_width() // 2,
                                  desc_y))
                desc_y += line_h

            # ── Indikator tumpukan (dot) untuk skill stackable ──
            dot_area_y = rect.y + 80 + len(desc_lines) * line_h + 10
            if max_stk > 1:
                dot_r    = 6
                dots_w   = max_stk * (dot_r * 2) + (max_stk - 1) * 5
                dx_start = rect.x + rect.w // 2 - dots_w // 2
                dot_y    = dot_area_y
                for d in range(max_stk):
                    cx_dot = dx_start + d * (dot_r * 2 + 5) + dot_r
                    if d < stack:
                        pygame.draw.circle(self.screen, color, (cx_dot, dot_y), dot_r)
                    else:
                        pygame.draw.circle(self.screen, GRAY,      (cx_dot, dot_y), dot_r)
                        pygame.draw.circle(self.screen, DARK_GRAY, (cx_dot, dot_y), dot_r - 2)
                lv_s = self.f_tiny.render(f"Level {stack} → {stack+1}", True, LIGHT_GRAY)
                self.screen.blit(lv_s,
                                 (rect.x + rect.w // 2 - lv_s.get_width() // 2,
                                  dot_y + dot_r + 4))

            # Border kartu
            b_color = WHITE if hovered else tuple(max(0, c - 70) for c in color)
            pygame.draw.rect(self.screen, b_color, rect,
                             3 if hovered else 2, border_radius=14)

            # Tombol "CHOOSE"
            btn   = pygame.Rect(rect.x + PAD, rect.bottom - 46, rect.w - PAD * 2, 32)
            btn_c = color if hovered else (40, 40, 62)
            pygame.draw.rect(self.screen, btn_c, btn, border_radius=8)
            btn_lbl = self.f_small.render("CHOOSE  \u25b6", True,
                                          (0, 0, 0) if hovered else GRAY)
            self.screen.blit(btn_lbl,
                             (btn.x + btn.w // 2 - btn_lbl.get_width() // 2,
                              btn.y + 8))

        # Tips bawah
        tip = self.f_tiny.render("Click a card to select your upgrade", True, GRAY)
        self.screen.blit(tip,
                         (SCREEN_WIDTH // 2 - tip.get_width() // 2,
                          SCREEN_HEIGHT - 28))

    # ---- Intro ---------------------------------------------------

    def _draw_intro(self) -> None:
        self._shadow_text(self.f_huge, "ASTRO SHOOTER",
                          SCREEN_WIDTH // 2, 120, CYAN)

        sub = self.f_mid.render("Top-Down Survival Shooter", True, LIGHT_GRAY)
        self.screen.blit(sub, (SCREEN_WIDTH // 2 - sub.get_width() // 2, 185))

        controls = [
            ("MOVE",  "WASD / Arrow Keys"),
            ("AIM",   "Mouse cursor"),
            ("SHOOT", "Hold Left Mouse Button"),
            ("QUIT",  "ESC"),
        ]
        for i, (key, val) in enumerate(controls):
            ky = self.f_small.render(key, True, YELLOW)
            vl = self.f_small.render(val, True, LIGHT_GRAY)
            cx = SCREEN_WIDTH // 2
            cy = 265 + i * 28
            self.screen.blit(ky, (cx - 180, cy))
            self.screen.blit(vl, (cx - 10, cy))

        legend = [
            ("Standard",  "(210, 55, 55)",  "Chases player"),
            ("Scout",     "(255, 90, 90)",   "Fast, low HP"),
            ("Shooter",   "(180, 80, 220)",  "Fires bullets"),
            ("Tank",      "(180, 80, 30)",   "Slow, high HP"),
            ("BOSS",      f"{str(PURPLE)}",  "Every 3rd stage – drops skill choice"),
        ]
        by3   = 390
        title3 = self.f_small.render("ENEMY TYPES", True, CYAN)
        self.screen.blit(title3, (SCREEN_WIDTH // 2 - title3.get_width() // 2, by3))
        for i, (name, color_str, desc) in enumerate(legend):
            color = eval(color_str)
            pygame.draw.circle(self.screen, color,
                               (SCREEN_WIDTH // 2 - 120, by3 + 22 + i * 22), 7)
            nl = self.f_tiny.render(f"{name:<12} {desc}", True, LIGHT_GRAY)
            self.screen.blit(nl, (SCREEN_WIDTH // 2 - 105, by3 + 15 + i * 22))

        hs_surf = self.f_small.render(
            f"High Score:  {self.hs.high_score:07d}", True, YELLOW)
        self.screen.blit(hs_surf,
                         (SCREEN_WIDTH // 2 - hs_surf.get_width() // 2, 520))

        if (pygame.time.get_ticks() // 500) % 2 == 0:
            prompt = self.f_mid.render("Press any key or click to start", True, WHITE)
            self.screen.blit(prompt,
                             (SCREEN_WIDTH // 2 - prompt.get_width() // 2, 566))

    # ---- Stage clear ---------------------------------------------

    def _draw_stage_clear(self) -> None:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 110))
        self.screen.blit(overlay, (0, 0))

        self._shadow_text(self.f_large, f"STAGE {self.cleared_stage} CLEAR!",
                          SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40, GREEN)

        nxt = self.f_mid.render(
            f"Entering Stage {self.stage_num}...", True, CYAN)
        self.screen.blit(nxt,
                         (SCREEN_WIDTH // 2 - nxt.get_width() // 2,
                          SCREEN_HEIGHT // 2 + 18))

        if self.stage.is_boss_stage:
            w = self.f_mid.render("BOSS INCOMING!", True, RED)
            self.screen.blit(w,
                             (SCREEN_WIDTH // 2 - w.get_width() // 2,
                              SCREEN_HEIGHT // 2 + 55))

    # ---- Game over -----------------------------------------------

    def _draw_game_over(self) -> None:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 165))
        self.screen.blit(overlay, (0, 0))

        self._shadow_text(self.f_huge, "GAME OVER",
                          SCREEN_WIDTH // 2, 140, RED)

        rows = [
            (f"SCORE      {self.score:07d}", WHITE),
            (f"HIGH SCORE {self.hs.high_score:07d}", YELLOW),
            (f"Stage reached:  {self.cleared_stage or self.stage_num}", CYAN),
        ]
        for i, (txt, col) in enumerate(rows):
            s = self.f_mid.render(txt, True, col)
            self.screen.blit(s, (SCREEN_WIDTH // 2 - s.get_width() // 2,
                                 240 + i * 42))

        if self.new_hs and self.score > 0:
            nh = self.f_mid.render("NEW HIGH SCORE!", True, YELLOW)
            self.screen.blit(nh, (SCREEN_WIDTH // 2 - nh.get_width() // 2, 375))

        opt = self.f_small.render(
            "[R]  Restart          [Q / ESC]  Quit", True, LIGHT_GRAY)
        self.screen.blit(opt, (SCREEN_WIDTH // 2 - opt.get_width() // 2, 440))

    # ----------------------------------------------------------------
    # Utility
    # ----------------------------------------------------------------

    def _shadow_text(self, font, text, cx, cy, color,
                     shadow_color=(0, 0, 0)) -> None:
        shadow = font.render(text, True, shadow_color)
        main   = font.render(text, True, color)
        self.screen.blit(shadow, (cx - main.get_width() // 2 + 3,
                                  cy - main.get_height() // 2 + 3))
        self.screen.blit(main,   (cx - main.get_width() // 2,
                                  cy - main.get_height() // 2))

    @staticmethod
    def _quit() -> None:
        pygame.quit()
        sys.exit()

    # ----------------------------------------------------------------
    # Main loop
    # ----------------------------------------------------------------

    def run(self) -> None:
        while True:
            self._handle_events()
            self._update()
            self._draw()
            self.clock.tick(FPS)