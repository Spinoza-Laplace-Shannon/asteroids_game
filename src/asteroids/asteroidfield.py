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
    # Each edge defines:
    # - Direction (1 = toward center, -1 = away from center)
    # - Position calculation (lambda = function that calculates spawn location)
    edges = [
        # LEFT EDGE - asteroids come from left moving right
        [
            pygame.Vector2(1, 0),  # Direction: right
            lambda y: pygame.Vector2(
                -ASTEROID_MAX_RADIUS, y * SCREEN_HEIGHT
            ),  # Position: off-screen left
        ],
        # RIGHT EDGE - asteroids come from right moving left
        [
            pygame.Vector2(-1, 0),  # Direction: left
            lambda y: pygame.Vector2(
                SCREEN_WIDTH + ASTEROID_MAX_RADIUS,
                y * SCREEN_HEIGHT,  # Position: off-screen right
            ),
        ],
        # TOP EDGE - asteroids come from top moving down
        [
            pygame.Vector2(0, 1),  # Direction: down
            lambda x: pygame.Vector2(
                x * SCREEN_WIDTH, -ASTEROID_MAX_RADIUS
            ),  # Position: off-screen top
        ],
        # BOTTOM EDGE - asteroids come from bottom moving up
        [
            pygame.Vector2(0, -1),  # Direction: up
            lambda x: pygame.Vector2(
                x * SCREEN_WIDTH,
                SCREEN_HEIGHT + ASTEROID_MAX_RADIUS,  # Position: off-screen bottom
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
        """Update spawner: count down timer and spawn when ready"""
        # COUNT UP TIMER
        self.spawn_timer += dt

        # TIME TO SPAWN? Spawn when timer exceeds spawn rate
        if self.spawn_timer > ASTEROID_SPAWN_RATE_SECONDS:
            self.spawn_timer = 0  # Reset timer

            # SPAWN A NEW ASTEROID
            # Choose a random edge to spawn from
            edge = random.choice(self.edges)

            # Pick random speed (40-100 pixels/second)
            speed = random.randint(40, 100)

            # Create velocity from edge direction
            velocity = edge[0] * speed

            # Add random angle variation (+/- 30 degrees) so not all asteroids move straight
            velocity = velocity.rotate(random.randint(-30, 30))

            # Calculate spawn position using edge function
            position = edge[1](random.uniform(0, 1))  # Random position along edge

            # Pick asteroid size (1-3, where 3 is biggest)
            kind = random.randint(1, ASTEROID_KINDS)
            self.spawn(ASTEROID_MIN_RADIUS * kind, position, velocity)
