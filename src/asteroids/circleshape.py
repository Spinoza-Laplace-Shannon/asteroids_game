import pygame
from .constants import SCREEN_WIDTH, SCREEN_HEIGHT


# ============================================================================
# CircleShape is the BASE CLASS for all moving game objects
# (Player, Asteroids, Shots, Bombs, etc.)
#
# In object-oriented programming, a base class is like a template.
# All game objects inherit ("copy") basic properties and methods from it.
# ============================================================================
class CircleShape(pygame.sprite.Sprite):
    """Base class for all circular game objects

    This class handles:
    - Position (x, y) and velocity (direction + speed)
    - Drawing on screen
    - Collision detection
    - Screen wrapping (objects reappear on opposite side)

    Other classes like Player, Asteroid, Shot extend this class
    and add their own special behavior.
    """

    def __init__(self, x, y, radius):
        """Initialize a circular game object at position (x, y)

        Args:
        - x, y: Starting position on screen
        - radius: Size of object (used for collision detection)
        """
        # This adds object to sprite groups automatically
        # (Groups are used to draw/update all objects at once)
        if hasattr(self, "containers"):
            super().__init__(self.containers)
        else:
            super().__init__()

        # PROPERTIES OF THIS OBJECT
        self.position = pygame.Vector2(x, y)  # Current x, y location
        self.velocity = pygame.Vector2(0, 0)  # Speed and direction of movement
        self.radius = radius  # Size - used for drawing and collisions

    def draw(self, screen):
        """Override this method in child classes to draw the object"""
        # Subclasses (Player, Asteroid, etc.) implement their own draw method
        pass

    def update(self, dt):
        """Override this method in child classes to update the object

        dt = delta time (time since last frame, usually ~0.016 seconds at 60 FPS)
        """
        # Subclasses implement their own update method
        pass

    def collides_with(self, other):
        """Check if this object collides with another object

        Uses circle collision detection:
        - If distance between centers < sum of radii, they collide!

        EXAMPLE:
        - Player radius = 20 pixels
        - Asteroid radius = 30 pixels
        - Player at (100, 100), Asteroid at (140, 100)
        - Distance = 40 pixels
        - Sum of radii = 20 + 30 = 50 pixels
        - 40 < 50 → COLLISION! ✓
        
        VERSUS:
        - If Asteroid was at (160, 100)
        - Distance = 60 pixels
        - 60 > 50 → NO COLLISION ✗
        
        Args:
        - other: Another CircleShape object to check collision with
        
        Returns:
        - True if colliding, False otherwise
        """
        # Calculate distance between this object's center and other's center
        # distance_to() is a built-in Pygame method
        distance = self.position.distance_to(other.position)
        
        # If distance is less than both radii combined, they touch!
        # self.radius = how big THIS object is
        # other.radius = how big THE OTHER object is
        return distance < self.radius + other.radius

    def wrap(self):
        """Make object reappear on opposite side of screen when it goes off-screen
        
        This creates a toroidal (donut-shaped) world like in classic Asteroids.
        Objects on left edge appear on right edge, top appears on bottom, etc.
        
        VISUAL EXAMPLE:
        
        When object goes off LEFT (x < 0):
        ┌─────────────[SCREEN]─────────────┐
        │                                   │
        │                              ●    │ ← Reappears here!
        │                                   │
        └─────────────────────────────────┘
        
        When object comes back from LEFT:
        ┌─────────────[SCREEN]─────────────┐
        │  ●                                │ ← Goes off here
        │                                   │
        │                                   │
        └─────────────────────────────────┘
        """
        # Check LEFT EDGE - if object goes too far left
        if self.position.x < 0:
            # Teleport to right side of screen
            self.position.x = SCREEN_WIDTH
        # Check RIGHT EDGE - if object goes too far right
        elif self.position.x > SCREEN_WIDTH:
            # Teleport to left side of screen
            self.position.x = 0

        # Check TOP EDGE - if object goes too far up
        if self.position.y < 0:
            # Teleport to bottom of screen
            self.position.y = SCREEN_HEIGHT
        # Check BOTTOM EDGE - if object goes too far down
        elif self.position.y > SCREEN_HEIGHT:
            # Teleport to top of screen
            self.position.y = 0
