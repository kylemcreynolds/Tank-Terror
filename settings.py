# Window settings
WIDTH = 900
HEIGHT = 600
FPS = 60

# Tank settings
TANK_SPEED = 3
ROTATION_SPEED = 3  # degrees
TANK_SIZE = 24

# Maze / level settings
CELL_SIZE = 30  # size of one maze cell in pixels
WALL_COLOR = (100, 100, 100)
EXIT_COLOR = (50, 200, 50)

# Enemy settings
ENEMY_SPEED = 2.0
ENEMY_ROTATION_SPEED = 2.5
ENEMY_FIRE_COOLDOWN = 90  # frames
ENEMY_BASE_COUNT = 1

# Gameplay
PLAYER_LIVES = 3

# Game progression
MAX_LEVELS = 5  # total number of levels (0..MAX_LEVELS-1)

# Bullet settings
BULLET_LIFETIME = 3  # seconds bullets persist (can bounce during this time)

# Level themes: each level has a background color, wall color, and exit color
# Format: (background_color, wall_color, exit_color)
LEVEL_THEMES = [
    ((34, 139, 34), (70, 100, 70), (50, 200, 50)),        # Level 0: Forest (dark green bg, darker green walls, bright green exit)
    ((25, 25, 112), (30, 60, 150), (100, 150, 255)),      # Level 1: Ocean (midnight blue bg, darker blue walls, light blue exit)
    ((139, 69, 19), (101, 50, 15), (255, 165, 0)),        # Level 2: Desert (brown bg, darker brown walls, orange exit)
    ((75, 0, 130), (100, 20, 150), (200, 100, 255)),      # Level 3: Mystic (indigo bg, purple walls, bright purple exit)
    ((70, 70, 70), (40, 40, 40), (255, 255, 0)),          # Level 4: Steel (gray bg, dark gray walls, yellow exit)
]
