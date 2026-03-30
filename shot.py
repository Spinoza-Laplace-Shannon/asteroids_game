import pygame
import pygame
from circleshape import CircleShape
from constants import SHOT_RADIUS, SCREEN_WIDTH, SCREEN_HEIGHT, LINE_WIDTH


# ============================================================================
# The Shot class represents a bullet fired from the player's ship
# Different weapons create shots with different colors
# ============================================================================
class Shot(CircleShape):
    """A projectile fired from the player's spaceship

    Features:
    - Different colors based on weapon type (white/green/red)
    - Travels in straight line at constant speed
    - Wraps around screen edges
    - Destroyed when it hits an asteroid
    """

    def __init__(self, position, velocity, color=(255, 255, 255)):
        """Create a shot at given position traveling at given velocity

        Args:
        - position: pygame.Vector2 of starting x, y
        - velocity: pygame.Vector2 of speed and direction
        - color: RGB tuple (default white)
        """
        super().__init__(
            position.x, position.y, SHOT_RADIUS
        )  # Initialize as CircleShape
        self.velocity = velocity  # Direction and speed of travel
        self.color = color  # Color - varies by weapon type

    def draw(self, screen):
        """Draw shot as a small colored circle"""
        pygame.draw.circle(
            screen,
            self.color,  # Use weapon-specific color
            (self.position.x, self.position.y),
            self.radius,
            LINE_WIDTH,
        )

    def update(self, dt):
        """Update shot: move it forward and wrap around screen"""
        # MOVE SHOT - Travel in its direction at constant velocity
        self.position += self.velocity * dt

        # WRAP AROUND - If goes off screen, appear on opposite side
        self.wrap()
