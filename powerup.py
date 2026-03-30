import pygame
from circleshape import CircleShape
from constants import POWERUP_SHIELD_RADIUS, SCREEN_WIDTH, SCREEN_HEIGHT


# ============================================================================
# The PowerUp class represents items the player can collect for benefits
# Currently only shields, but could be extended with other power-ups
# ============================================================================
class PowerUp(CircleShape):
    """A collectible shield power-up that protects the player from one hit

    Features:
    - Glowing green appearance
    - Spawns randomly on screen
    - Stays stationary (doesn't move)
    - Player gets shield when touching it
    """

    def __init__(self, x, y):
        """Create a power-up at position (x, y)"""
        super().__init__(x, y, POWERUP_SHIELD_RADIUS)  # Initialize as CircleShape

    def draw(self, screen):
        """Draw the power-up as a glowing green circle"""
        # Bright green filled circle
        pygame.draw.circle(
            screen, (50, 220, 50), (self.position.x, self.position.y), self.radius
        )
        # Darker green outline for definition
        pygame.draw.circle(
            screen, (0, 150, 0), (self.position.x, self.position.y), self.radius, 2
        )

    def update(self, dt):
        """Update power-up: stays in place but wraps around screen"""
        # Power-ups don't move, but we wrap in case they're placed off-screen
        self.wrap()
