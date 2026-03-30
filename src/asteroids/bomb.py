import pygame
from .circleshape import CircleShape
from .constants import BOMB_RADIUS, LINE_WIDTH


# ============================================================================
# The Bomb class represents an explosive weapon the player can drop
# It has a 2-second fuse, then explodes damaging nearby asteroids
# ============================================================================
class Bomb(CircleShape):
    """A timed explosive weapon with area-of-effect damage

    Features:
    - 2 second fuse timer shown visually
    - Explodes and damages all asteroids nearby
    - Different from bullets - affects multiple targets
    - Strategic tool for crowd control
    """

    def __init__(self, x, y, velocity):
        """Create a bomb at position (x, y) with given velocity"""
        super().__init__(x, y, BOMB_RADIUS)  # Initialize as small circle
        self.velocity = velocity  # Bomb travels in this direction
        self.fuse_time = 2.0  # Count down from 2 seconds to explosion
        self.exploded = False  # Has this bomb already gone off?

    def draw(self, screen):
        """Draw the bomb as orange circle with yellow fuse indicator"""
        # DRAW BOMB BODY - Orange circle
        pygame.draw.circle(
            screen,
            (255, 100, 0),  # Orange
            (self.position.x, self.position.y),
            self.radius,
            LINE_WIDTH,
        )

        # DRAW FUSE INDICATOR - Yellow circle that shrinks as time runs out
        # This shows player how much time until explosion
        fuse_ratio = max(0, self.fuse_time / 2.0)  # 1.0 = full, 0.0 = empty
        inner_radius = int(self.radius * 0.6 * fuse_ratio)  # Make it smaller

        # Only draw if there's something to draw
        if inner_radius > 0:
            pygame.draw.circle(
                screen,
                (255, 200, 0),  # Yellow
                (self.position.x, self.position.y),
                inner_radius,
            )

    def update(self, dt):
        """Update bomb: move it, count down fuse, and explode when ready"""
        # MOVE BOMB - Travel in given direction
        self.position += self.velocity * dt

        # WRAP AROUND SCREEN - Like asteroids
        self.wrap()

        # COUNT DOWN FUSE
        self.fuse_time -= dt

        # CHECK IF TIME TO EXPLODE
        if self.fuse_time <= 0:
            self.exploded = True  # Mark bomb as exploded
            self.kill()  # Remove from game (explosion handled in main.py)
