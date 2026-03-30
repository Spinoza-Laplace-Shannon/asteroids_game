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

        Args:
        - other: Another CircleShape object to check collision with

        Returns:
        - True if colliding, False otherwise
        """
        # Calculate distance between this object's center and other's center
        distance = self.position.distance_to(other.position)

        # If distance is less than both radii combined, they touch!
        return distance < self.radius + other.radius

    def wrap(self):
        """Make object reappear on opposite side of screen when it goes off-screen

        This creates a toroidal (donut-shaped) world like in classic Asteroids.
        Objects on left edge appear on right edge, top appears on bottom, etc.
        """
        # Check LEFT EDGE
        if self.position.x < 0:
            self.position.x = SCREEN_WIDTH  # Wrap to right
        # Check RIGHT EDGE
        elif self.position.x > SCREEN_WIDTH:
            self.position.x = 0  # Wrap to left

        # Check TOP EDGE
        if self.position.y < 0:
            self.position.y = SCREEN_HEIGHT  # Wrap to bottom
        # Check BOTTOM EDGE
        elif self.position.y > SCREEN_HEIGHT:
            self.position.y = 0  # Wrap to top
