import pygame
import random
from .asteroid import Asteroid
from .constants import *


# ============================================================================
# The AsteroidField class spawns asteroids continuously during the game
# It's like an invisible spawner that creates waves of enemies
# ============================================================================
class AsteroidField(pygame.sprite.Sprite):
    """Spawns asteroids from the edges of the screen continuously

    How it works:
    - Tracks time since last spawn
    - When time exceeds ASTEROID_SPAWN_RATE_SECONDS, spawn one
    - Asteroids appear from random edges with random speeds
    - Creates feeling of never-ending waves
    """

    # EDGES - Where asteroids can spawn from (4 edges of screen)
    # This is a 2D array where each edge has TWO COMPONENTS:
    # [0] = Direction vector (which way asteroid travels from this edge)
    # [1] = Lambda function (calculates random spawn position along edge)
    #
    # WHAT'S A LAMBDA? It's a "throwaway function" written inline
    # Instead of: def get_left_edge(y): return pygame.Vector2(..., y * SCREEN_HEIGHT)
    # We use:      lambda y: pygame.Vector2(...)  ← shorter, one-line function
    #
    # VISUALIZATION OF SCREEN EDGES:
    # ┌─────────────────────────────────────┐
    # │ TOP EDGE (y=0) ←──── Asteroids      │
    # │  ↓ ↓ ↓ ↓ ↓ ↓ ↓                      │
    # │                                     │
    # │ LEFT ←──  GAME  ──→ RIGHT           │
    # │ (x=0)           (x=800)             │
    # │                                     │
    # │  ↑ ↑ ↑ ↑ ↑ ↑ ↑                      │
    # │ BOTTOM EDGE (y=600) ←──── Asteroids │
    # └─────────────────────────────────────┘
    
    edges = [
        # ===== LEFT EDGE =====
        # Asteroids come FROM left side, moving RIGHT into the screen
        [
            pygame.Vector2(1, 0),  # Direction: right (1,0) means x increases
            # Lambda: Place asteroid off-screen left at random vertical position
            # y=0 → top of screen, y=1 → bottom of screen
            # EXAMPLE: if y=0.5 → spawn at (y * 600) = 300 pixels down
            lambda y: pygame.Vector2(
                -ASTEROID_MAX_RADIUS,  # x position: off-screen left (negative x)
                y * SCREEN_HEIGHT       # y position: random height
            ),
        ],
        
        # ===== RIGHT EDGE =====
        # Asteroids come FROM right side, moving LEFT into the screen
        [
            pygame.Vector2(-1, 0),  # Direction: left (-1,0) means x decreases
            # Lambda: Place asteroid off-screen right
            lambda y: pygame.Vector2(
                SCREEN_WIDTH + ASTEROID_MAX_RADIUS,  # x position: off-screen right
                y * SCREEN_HEIGHT                     # y position: random height
            ),
        ],
        
        # ===== TOP EDGE =====
        # Asteroids come FROM top, moving DOWN into the screen
        [
            pygame.Vector2(0, 1),  # Direction: down (0,1) means y increases
            # Lambda: Place asteroid off-screen top at random horizontal position
            # x=0 → left side, x=1 → right side
            lambda x: pygame.Vector2(
                x * SCREEN_WIDTH,            # x position: random width
                -ASTEROID_MAX_RADIUS         # y position: off-screen top (negative y)
            ),
        ],
        
        # ===== BOTTOM EDGE =====
        # Asteroids come FROM bottom, moving UP into the screen
        [
            pygame.Vector2(0, -1),  # Direction: up (0,-1) means y decreases
            # Lambda: Place asteroid off-screen bottom
            lambda x: pygame.Vector2(
                x * SCREEN_WIDTH,                    # x position: random width
                SCREEN_HEIGHT + ASTEROID_MAX_RADIUS  # y position: off-screen bottom
            ),
        ],
    ]

    def __init__(self):
        """Initialize the asteroid field spawner"""
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.spawn_timer = 0.0  # Count up until time to spawn

    def spawn(self, radius, position, velocity):
        """Create a new asteroid at given position with given velocity"""
        asteroid = Asteroid(position.x, position.y, radius)
        asteroid.velocity = velocity

    def update(self, dt):
        """Update spawner: count down timer and spawn when ready
        
        SPAWNING SYSTEM:
        ================
        This spawner creates a continuous stream of asteroids
        It uses a TIMER that counts up until it's time to spawn
        
        CALCULATION FLOW:
        1. Add elapsed time (dt) to spawn_timer
        2. When spawn_timer exceeds threshold, it's time to spawn
        3. Create new asteroid with random properties
        4. Reset timer and repeat
        
        WHY DO THIS?
        - Asteroids don't appear all at once (overwhelming)
        - They spawn continuously at controlled rate
        - Creates escalating difficulty as game progresses
        """
        # Step 1: COUNT UP TIMER
        # dt = "delta time" = seconds since last update
        # At 60 FPS: dt ≈ 0.0167 seconds (1/60th)
        self.spawn_timer += dt

        # Step 2: TIME TO SPAWN?
        # Check if timer exceeds spawn rate threshold
        # If ASTEROID_SPAWN_RATE_SECONDS = 1.5:
        #   Every 1.5 seconds, spawn an asteroid
        if self.spawn_timer > ASTEROID_SPAWN_RATE_SECONDS:
            self.spawn_timer = 0  # Reset timer for next asteroid

            # Step 3: PICK A RANDOM EDGE
            # Choose one of [LEFT, RIGHT, TOP, BOTTOM] randomly
            # This makes asteroids appear from unpredictable directions
            edge = random.choice(self.edges)

            # Step 4: CALCULATE SPEED
            # Random speed between 40-100 pixels per second
            # Faster asteroids are harder to destroy
            # EXAMPLE: 70 pixels/second = travels 70 pixels in 1 second
            speed = random.randint(40, 100)

            # Step 5: CREATE VELOCITY VECTOR
            # Velocity = direction * speed
            # EXAMPLE: edge[0] = (1, 0), speed = 50
            #          → velocity = (50, 0) - moving right 50 px/sec
            velocity = edge[0] * speed

            # Step 6: ADD ANGLE VARIATION
            # Without this: all asteroids from one edge move in straight lines
            # With this: they spread out in a fan pattern
            # Rotate velocity by random angle (-30° to +30°)
            # EXAMPLE: asteroid meant for left edge but rotated +20°
            #          → comes from upper-left instead of straight left
            velocity = velocity.rotate(random.randint(-30, 30))

            # Step 7: CALCULATE SPAWN POSITION
            # edge[1] is a lambda function that takes a random factor (0.0 to 1.0)
            # EXAMPLE - LEFT EDGE:
            #   random.uniform(0, 1) = 0.7 (70% down the screen)
            #   → lambda y: Vector2(-ASTEROID_MAX_RADIUS, y * SCREEN_HEIGHT)
            #   → Vector2(-50, 0.7 * 600) = Vector2(-50, 420)
            #   Spawns off-screen left, 70% down from top
            position = edge[1](random.uniform(0, 1))

            # Step 8: PICK ASTEROID SIZE
            # random.randint(1, ASTEROID_KINDS) gives size 1, 2, or 3
            # Where ASTEROID_KINDS typically = 3
            # size 1 = small (most asteroids)
            # size 2 = medium
            # size 3 = large (biggest asteroids)
            # EXAMPLE: if size = 2 and ASTEROID_MIN_RADIUS = 10
            #          → asteroid radius = 10 * 2 = 20 pixels
            kind = random.randint(1, ASTEROID_KINDS)
            self.spawn(ASTEROID_MIN_RADIUS * kind, position, velocity)
