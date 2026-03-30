import pygame
import random
from constants import *
from logger import log_event
from player import *
from circleshape import CircleShape


# ============================================================================
# The Asteroid class represents floating rocks in space that the player must
# destroy. Asteroids have randombumpy shapes and split into smaller pieces
# when shot.
# ============================================================================
class Asteroid(CircleShape):
    """A floating space rock with an irregular, bumpy shape

    Features:
    - Procedurally generated bumpy surface (not perfectly round)
    - Random size variations for organic appearance
    - Breaks into smaller asteroids when shot until they're too small
    - Wraps around screen edges
    - Worth more points when bigger
    """

    def __init__(self, x, y, radius):
        """Create an asteroid at position (x, y) with given radius"""
        super().__init__(x, y, radius)  # Initialize as CircleShape
        # Create an irregular shape by setting random number of vertices
        self.vertex_count = random.randint(8, 14)  # 8-14 points around the asteroid
        self.jaggedness = 0.35  # How much shape varies (0.35 = ±35% variation)

        # Generate random offsets for each vertex to make bumpy shape
        # Each offset is a random multiplier 0.65 to 1.35 that affects
        # how far out each point sticks from the center
        self.offsets = [
            random.uniform(1 - self.jaggedness, 1 + self.jaggedness)
            for _ in range(self.vertex_count)
        ]

        # Make line thickness vary per asteroid for variety
        self.outline_width = random.randint(1, 4)

        # Two-color scheme for depth effect
        self.color_inner = (120, 120, 120)  # Darker gray inside
        self.color_outer = (200, 200, 200)  # Lighter gray overlay

    def draw(self, screen):
        """Draw the asteroid as a bumpy polygon with two-layer shading"""
        # CALCULATE POLYGON POINTS - Generate the bumpy shape
        points = []
        for i, offset in enumerate(self.offsets):
            # Calculate angle for this vertex (spread evenly around circle)
            angle = (360 / self.vertex_count) * i

            # Create direction vector pointing outward from asteroid center
            direction = pygame.Vector2(0, -1).rotate(angle)

            # Distance = radius * random offset
            # This makes some points stick out more (lumpy)
            distance = self.radius * offset

            # Convert to actual x, y coordinate on screen
            points.append(
                (
                    self.position.x + direction.x * distance,
                    self.position.y + direction.y * distance,
                )
            )

        # LAYER 1: Draw inner fill (dark gray)
        pygame.draw.polygon(screen, self.color_inner, points)

        # LAYER 2: Draw translucent overlay for depth
        # Create a special surface that supports transparency (alpha)
        surface = pygame.Surface(
            (self.radius * 2 + 4, self.radius * 2 + 4), pygame.SRCALPHA
        )
        # Adjust points to surface coordinate system
        offset_points = [
            (
                p[0] - self.position.x + self.radius + 2,
                p[1] - self.position.y + self.radius + 2,
            )
            for p in points
        ]
        # Draw light gray overlay that's semi-transparent (120 alpha = 47% opaque)
        pygame.draw.polygon(surface, (*self.color_outer, 120), offset_points)
        screen.blit(
            surface,
            (self.position.x - self.radius - 2, self.position.y - self.radius - 2),
        )

        # LAYER 3: Draw outline (white border)
        outline_color = (255, 255, 255)
        pygame.draw.polygon(screen, outline_color, points, self.outline_width)

    def split(self):
        """When shot, break this asteroid into two smaller pieces"""
        # Remove this asteroid from game
        self.kill()

        # STOP IF TOO SMALL - If already small, don't split further
        # (Small asteroids are destroyed completely)
        if self.radius <= ASTEROID_MIN_RADIUS:
            return

        # LOG THE EVENT - For debugging/statistics
        log_event("asteroid_split")

        # CALCULATE velocities for split pieces
        # Rotate velocity in opposite directions so pieces spread apart
        angle = random.uniform(20, 50)  # Random spread angle

        # First piece goes clockwise, slightly faster
        first_velocity = self.velocity.rotate(angle) * 1.2
        # Second piece goes counter-clockwise, slightly faster
        second_velocity = self.velocity.rotate(-angle) * 1.2

        # New asteroids are smaller by ASTEROID_MIN_RADIUS amount
        new_radius = self.radius - ASTEROID_MIN_RADIUS

        # CREATE TWO NEW ASTEROIDS at same position
        asteroid_1 = Asteroid(self.position.x, self.position.y, new_radius)
        asteroid_2 = Asteroid(self.position.x, self.position.y, new_radius)

        # Set their velocities
        asteroid_1.velocity = first_velocity
        asteroid_2.velocity = second_velocity

    def update(self, dt):
        """Update asteroid: move it forward and wrap around screen edges"""
        # MOVE ASTEROID - Travel in current direction at current velocity
        self.position += self.velocity * dt

        # SCREEN WRAP - If goes off edge, appear on opposite side
        # (Makes the game world toroidal - like Pac-Man)
        self.wrap()


# ============================================================================
# The Explosion class is a visual effect that shows destruction
# It appears when asteroids or enemies are destroyed
# ============================================================================
class Explosion(CircleShape):
    """An expanding orange circle that shows where something exploded

    Features:
    - Expands and fades out over 0.5 seconds
    - Orange color
    - Visual feedback for player actions
    """

    def __init__(self, x, y):
        """Create explosion at position (x, y)"""
        super().__init__(x, y, 0)  # Start with 0 radius (point)
        self.life = 0.5  # Lasts 0.5 seconds
        self.growth_rate = 240  # Expands at 240 pixels/second

    def update(self, dt):
        """Update explosion: shrink lifetime and expand radius"""
        self.life -= dt  # Count down remaining time
        self.radius += self.growth_rate * dt  # Expand outward

        # When time runs out, remove explosion from game
        if self.life <= 0:
            self.kill()

    def draw(self, screen):
        """Draw the explosion as expanding orange circle with fading alpha"""
        # Calculate transparency based on remaining life
        # At full life (0.5s): alpha = 255 (fully opaque)
        # At zero life: alpha = 0 (fully transparent)
        alpha = max(0, int(255 * (self.life / 0.5)))

        # Orange color
        color = (255, 180, 0)

        # Create transparent surface for the explosion
        surface = pygame.Surface(
            (self.radius * 2 + 2, self.radius * 2 + 2), pygame.SRCALPHA
        )

        # Draw outline circle (not filled)
        pygame.draw.circle(
            surface,
            color + (alpha,),  # Add alpha for transparency
            (int(self.radius + 1), int(self.radius + 1)),
            int(self.radius),
            2,  # Line width of 2
        )

        # Blit onto screen at correct position
        screen.blit(
            surface,
            (self.position.x - self.radius - 1, self.position.y - self.radius - 1),
        )
