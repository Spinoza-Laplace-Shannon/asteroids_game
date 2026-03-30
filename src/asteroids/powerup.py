import pygame
from .circleshape import CircleShape
from .constants import POWERUP_SHIELD_RADIUS


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
        """Draw the power-up as a glowing green circle

        VISUAL DESIGN - "GLOWING" SHIELD:
        =================================
        We draw TWO circles to create a "glowing" effect:
        1. Bright green filled circle (inner) - main body
        2. Darker green outline - defines the edge

        The contrast makes it POP and stand out from asteroids
        Players can easily spot power-ups on screen

        TYPICAL SHIELD APPEARANCE:
          ╱─────────────────╲
         ╱   ●●●●●●●●●●●    ╲  ← Bright green (inner, filled)
        │    ●           ●    │
        │   ●   SHIELD    ●   │
        │    ●           ●    │
         ╲    ●●●●●●●●●●●    ╱   ← Dark green outline
          ╲─────────────────╱
        """
        # ===== VISUAL LAYER 1: BRIGHT GREEN FILLED CIRCLE =====
        # Draw solid bright green circle - the main body
        # RGB(50, 220, 50) = green that's bright and saturated
        pygame.draw.circle(
            screen,
            (50, 220, 50),  # Bright green color
            (self.position.x, self.position.y),
            self.radius,  # Radius from constants (usually 15 pixels)
        )

        # ===== VISUAL LAYER 2: DARK GREEN OUTLINE =====
        # Draw dark green outline around the filled circle
        # This creates definition and makes power-up easier to see
        # RGB(0, 150, 0) = darker green for contrast
        # Line thickness: 2 pixels (defines border width)
        pygame.draw.circle(
            screen,
            (0, 150, 0),  # Dark green outline color
            (self.position.x, self.position.y),
            self.radius,  # Same radius as inner circle
            2,  # Line thickness = 2 pixels
        )

    def update(self, dt):
        """Update power-up: stays in place but wraps around screen

        POWER-UP MECHANICS:
        ===================
        Unlike asteroids and bombs, power-ups DON'T MOVE
        They sit stationary at their spawn location
        Why? So player can predict where to navigate to collect them

        WRAPPING: We do update wrapping in case power-up spawns off-screen
        This is a safety measure - shouldn't happen in normal play

        COLLISION: Main.py handles collision detection with player
        When player touches power-up → shield activated, power-up removed
        """
        # WRAP AROUND SCREEN
        # This is a safety measure in case power-up was placed off-screen
        # during initial spawn. Won't normally be called since power-ups
        # are placed on-screen by PowerUp spawner
        self.wrap()
