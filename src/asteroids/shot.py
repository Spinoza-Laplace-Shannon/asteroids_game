import pygame
import pygame
from .circleshape import CircleShape
from .constants import SHOT_RADIUS, SCREEN_WIDTH, SCREEN_HEIGHT, LINE_WIDTH


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
        """Draw shot as a small colored circle
        
        VISUAL REPRESENTATION:
        ======================
        Bullets are tiny circles (usually 2 pixels radius)
        Color varies by weapon type:
        - White = Standard weapon
        - Green = Rapid fire weapon
        - Red = Spread shot weapon
        
        Small size helps player see where bullets are going
        Different colors distinguish weapon types visually
        """
        # Draw small filled circle at bullet position
        # Uses weapon-specific color for visual distinction
        pygame.draw.circle(
            screen,
            self.color,                          # Use weapon-specific color
            (self.position.x, self.position.y),
            self.radius,                         # Bullet radius (usually 2 px)
            LINE_WIDTH,                          # Outline thickness
        )

    def update(self, dt):
        """Update shot: move it forward and wrap around screen
        
        BULLET PHYSICS:
        ===============
        Bullets travel in a STRAIGHT LINE at CONSTANT VELOCITY
        No acceleration, no drag - just pure physics
        
        TRAJECTORY CALCULATION:
        Each frame: new_position = current_position + (velocity * time_elapsed)
        
        EXAMPLE:
        - Position: (200, 300)
        - Velocity: (300, 0) pixels/second (moving right)
        - dt: 0.0167 seconds (1/60th fps)
        - New position: (200, 300) + (300, 0) * 0.0167
        -            = (200, 300) + (5, 0)
        -            = (205, 300)  ← Moves 5 pixels right each frame at 60 FPS
        
        At 60 FPS: Bullet travels 300 pixels per second = 5 pixels per frame
        """
        # Step 1: MOVE BULLET
        # Position changes based on velocity and time delta
        # This makes bullet movement frame-rate independent
        # (Moves same distance per second regardless of FPS)
        self.position += self.velocity * dt

        # Step 2: WRAP AROUND SCREEN
        # If bullet goes off one edge, appears from opposite edge
        # Toroidal wrapping (like Pac-Man, 1980s arcade style)
        # Allows bullets to wrap around and hit asteroids from behind
        self.wrap()
