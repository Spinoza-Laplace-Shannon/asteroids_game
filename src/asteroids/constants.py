# ============================================================================
# CONSTANTS.PY
# This file stores all the "tunable" numbers used throughout the game
# Think of it as a configuration file - change these to adjust game behavior!
#
# Tip for students: Change these values to test different gameplay!
# Make asteroids spawn faster? Lower ASTEROID_SPAWN_RATE_SECONDS
# Want harder movement? Lower PLAYER_FRICTION
# ============================================================================

# SCREEN - Game window dimensions in pixels
# 1280x720 is a common 16:9 format, wide enough to feel spacious.
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720

# VISUALS - Basic drawing sizes
PLAYER_RADIUS = 20  # Size of player ship
LINE_WIDTH = 2  # Thickness of drawn outlines

# PLAYER MOVEMENT - Numbers that control how the ship feels to play
# Bigger acceleration = more responsive thrust
# Bigger friction close to 1.0 = longer sliding in space
PLAYER_TURN_SPEED = 300  # Rotation speed (degrees per second)
PLAYER_SPEED = 200  # Legacy constant (kept for compatibility)
PLAYER_ACCELERATION = 400  # How quickly player accelerates when pressing UP
PLAYER_FRICTION = 0.98  # Drag that slows player (0.98 = 2% slowdown per frame)
PLAYER_MAX_SPEED = 450  # Cap on how fast player can go

# ASTEROIDS - How they spawn and behave
ASTEROID_MIN_RADIUS = 20  # Smallest asteroid size
ASTEROID_KINDS = 3  # Number of asteroid size levels (1=small, 2=medium, 3=large)
ASTEROID_SPAWN_RATE_SECONDS = 0.8  # How often new asteroids appear (seconds)
ASTEROID_MAX_RADIUS = ASTEROID_MIN_RADIUS * ASTEROID_KINDS  # Biggest asteroid

# SCORING - Points for destroying asteroids
SCORE_SMALL_ASTEROID = 100  # Points for small asteroid
SCORE_MEDIUM_ASTEROID = 50  # Points for medium asteroid
SCORE_LARGE_ASTEROID = 20  # Points for large asteroid

# BULLETS - Projectiles fired by the player
SHOT_RADIUS = 5  # Size of bullet
PLAYER_SHOOT_SPEED = 500  # How fast bullets travel
PLAYER_SHOOT_COOLDOWN_SECONDS = 0.3  # Must wait this long between shots

# BOMB SYSTEM
# The bomb has a small body, then later affects a larger area around it.
BOMB_RADIUS = 8
BOMB_COOLDOWN_SECONDS = 1.0
BOMB_EXPLOSION_RADIUS = 150
BOMB_DAMAGE_RADIUS = 120

# Weapon mode names are strings so the code can clearly compare states.
WEAPON_SINGLE = "SINGLE"
WEAPON_SPREAD = "SPREAD"
WEAPON_RAPID = "RAPID"

# RGB colour tuples: (red, green, blue)
# Each value goes from 0 to 255.
WEAPON_COLOR_SINGLE = (255, 255, 255)
WEAPON_COLOR_SPREAD = (0, 255, 0)
WEAPON_COLOR_RAPID = (255, 0, 0)

# Player hitbox tuning
# 0.9 means the collision shape is 90% of the visible ship size.
# This gives the player a small forgiveness margin.
PLAYER_HITBOX_SCALE = 0.9

# Shield power-up
# The shield lasts a few seconds, pulses visually, then disappears.
POWERUP_SHIELD_RADIUS = 12
POWERUP_SPAWN_RATE_SECONDS = 10
SHIELD_DURATION_SECONDS = 6
SHIELD_PULSE_SPEED = 4.0
SHIELD_EXPIRE_TEXT_DURATION = 2.0

# Sound volumes
SOUND_VOLUME_PICKUP = 0.7
SOUND_VOLUME_BLOCK = 0.7
SOUND_VOLUME_SHIELD_EXPIRE = 0.8
SOUND_VOLUME_MENU_NAV = 0.5

# Difficulty levels
DIFFICULTY_EASY = "EASY"
DIFFICULTY_NORMAL = "NORMAL"
DIFFICULTY_HARD = "HARD"
DIFFICULTIES = [DIFFICULTY_EASY, DIFFICULTY_NORMAL, DIFFICULTY_HARD]

# Difficulty multipliers
# 0.7 means 70% of the base value, so the game is slower and easier.
# 1.5 means 150% of the base value, so the game is faster and harder.
DIFFICULTY_MULT = {
    DIFFICULTY_EASY: 0.7,
    DIFFICULTY_NORMAL: 1.0,
    DIFFICULTY_HARD: 1.5,
}

# Player lives and respawn rules
# After losing a life, the player waits briefly, then respawns with a short
# invulnerability window to avoid dying again instantly.
PLAYER_LIVES = 3
PLAYER_RESPAWN_DELAY_SECONDS = 1.0  # pause before reactivating
PLAYER_RESPAWN_INVULNERABLE_SECONDS = 2.0

# Optional background image loaded from the project root if present
BACKGROUND_IMAGE_PATH = "background.png"  # place image in project root
