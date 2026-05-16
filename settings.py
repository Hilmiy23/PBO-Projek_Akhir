# --- Screen ---
SCREEN_WIDTH  = 900
SCREEN_HEIGHT = 650
FPS           = 60
TITLE         = "ASTRA SHOOTER"

# --- Colors ---
WHITE      = (255, 255, 255)
BLACK      = (0,   0,   0  )
RED        = (220, 50,  50 )
GREEN      = (50,  200, 80 )
BLUE       = (40,  80,  200)
YELLOW     = (255, 220, 0  )
ORANGE     = (255, 140, 0  )
PURPLE     = (170, 50,  220)
CYAN       = (0,   220, 230)
PINK       = (255, 80,  160)
DARK_GRAY  = (22,  22,  32 )
GRAY       = (90,  90,  110)
LIGHT_GRAY = (170, 170, 190)
DARK_BLUE  = (15,  20,  50 )

# --- Player ---
PLAYER_SPEED          = 4
PLAYER_HP             = 6
PLAYER_RADIUS         = 15
PLAYER_BULLET_SPEED   = 11
PLAYER_BULLET_DAMAGE  = 1
PLAYER_SHOOT_COOLDOWN = 12   # frames between shots

# --- Enemy ---
ENEMY_BASE_SPEED    = 1.4
ENEMY_RADIUS        = 13
ENEMY_HP            = 2
ENEMY_DAMAGE        = 1
ENEMY_SHOOT_COOLDOWN= 100   # frames (for shooter type)
ENEMY_BULLET_SPEED  = 3.5

# --- Boss ---
BOSS_RADIUS          = 32
BOSS_HP              = 24
BOSS_SPEED           = 0.9
BOSS_DAMAGE          = 2
BOSS_SHOOT_COOLDOWN  = 50

# --- Score ---
SCORE_PER_KILL      = 100
SCORE_PER_BOSS_KILL = 600
SCORE_PER_STAGE     = 300

# --- Stage ---
ENEMIES_PER_STAGE   = 12   # base count; increases each stage
BOSS_EVERY_N_STAGES = 3    # boss fight on stage 3, 6, 9, …

# --- Files ---
HIGHSCORE_FILE = "highscore.json"

# --- Skills (Roguelike) ---
# max_stack=1  → hanya bisa diambil sekali (UNIQUE)
# max_stack>1  → bisa ditumpuk beberapa kali (STACKABLE)
SKILL_DEFINITIONS: dict[str, dict] = {
    "damage_up": {
        "name":      "Power Core",
        "desc":      "+1 damage per bullet",
        "color":     (255, 110, 50),
        "max_stack": 5,
        "tag":       "STACKABLE",
    },
    "fire_rate_up": {
        "name":      "Rapid Barrel",
        "desc":      "Shoot cooldown -2 frames",
        "color":     (255, 220, 0),
        "max_stack": 5,
        "tag":       "STACKABLE",
    },
    "speed_up": {
        "name":      "Afterburner",
        "desc":      "+0.8 permanent move speed",
        "color":     (50, 200, 80),
        "max_stack": 4,
        "tag":       "STACKABLE",
    },
    "max_hp_up": {
        "name":      "Vital Implant",
        "desc":      "+3 max HP & restore health",
        "color":     (220, 60, 100),
        "max_stack": 5,
        "tag":       "STACKABLE",
    },
    "double_shot": {
        "name":      "Twin Barrel",
        "desc":      "Fire 2 bullets at once",
        "color":     (0, 210, 255),
        "max_stack": 1,
        "tag":       "UNIQUE",
    },
    "triple_shot": {
        "name":      "Spread Shot",
        "desc":      "Fire a 3-way bullet spread",
        "color":     (170, 60, 230),
        "max_stack": 1,
        "tag":       "UNIQUE",
    },
    "piercing": {
        "name":      "Armor Pierce",
        "desc":      "Bullets pass through enemies",
        "color":     (255, 160, 0),
        "max_stack": 1,
        "tag":       "UNIQUE",
    },
    "bouncing": {
        "name":      "Ricochet",
        "desc":      "Bullets bounce off screen edges",
        "color":     (80, 215, 255),
        "max_stack": 1,
        "tag":       "UNIQUE",
    },
    "lifesteal": {
        "name":      "Vampiric",
        "desc":      "30% chance: heal 1 HP on kill",
        "color":     (200, 50, 200),
        "max_stack": 1,
        "tag":       "UNIQUE",
    },
    "shield_up": {
        "name":      "Aegis Core",
        "desc":      "Shield powerup lasts 3x longer",
        "color":     (100, 210, 255),
        "max_stack": 1,
        "tag":       "UNIQUE",
    },
}