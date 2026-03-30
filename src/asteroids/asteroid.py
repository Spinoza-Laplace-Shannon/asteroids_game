import pygame
import random
from .constants import *
from .logger import log_event
from .player import *
from .circleshape import CircleShape


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
        """Draw the asteroid as a bumpy polygon with two-layer shading
        
        HOW PROCEDURAL GENERATION WORKS:
        ================================
        Instead of drawing circles, we create a bumpy shape by:
        1. Placing vertices (points) around the center in a circle
        2. Applying random offsets to each vertex
        3. Connecting them to form an irregular polygon
        
        EXAMPLE VISUALIZATION (9-vertex asteroid):
                           128°
                             |
                        ●─────●─────●
                       /             \\
                      ●               ●
                     /                 \\
                    ●       (x,y)       ●
                     \\                 /
                      ●               ●
                       \\             /
                        ●─────●─────●
                            |
                           308°
        
        Each offset multiplies the radius (e.g., 1.2x makes point stick out more)
        """
        # CALCULATE POLYGON POINTS - Generate the bumpy shape
        points = []
        for i, offset in enumerate(self.offsets):
            # Calculate angle for this vertex (spread evenly around circle)
            # For a 10-vertex asteroid: vertex 0=0°, vertex 1=36°, vertex 2=72°, etc.
            angle = (360 / self.vertex_count) * i

            # Create direction vector pointing outward from asteroid center
            # Step 1: Start with vector pointing straight up: (0, -1)
            # Step 2: Rotate it by our calculated angle
            # EXAMPLE: angle=45° means rotate the (0,-1) vector 45° clockwise
            #          Result: vector now points toward upper-right
            direction = pygame.Vector2(0, -1).rotate(angle)

            # Distance from center to vertex = radius * random offset
            # Offset ranges from ~0.65 to ~1.35 (from self.jaggedness setting)
            # This makes some points stick out more (lumpy, uneven surface)
            # EXAMPLE: if radius=25, offset=1.2 → distance=30 pixels from center
            distance = self.radius * offset

            # Convert polar coordinates (angle + distance) to x,y coordinates
            # FORMULA: x = center_x + direction.x * distance
            #          y = center_y + direction.y * distance
            # EXAMPLE: center=(200,300), direction=(0.7,0.7), distance=30
            #          → point=(200 + 0.7*30, 300 + 0.7*30) = (221, 321)
            points.append(
                (
                    self.position.x + direction.x * distance,
                    self.position.y + direction.y * distance,
                )
            )

        # LAYER 1: Draw inner fill (dark gray)
        # This fills the entire polygon with solid dark gray
        pygame.draw.polygon(screen, self.color_inner, points)

        # LAYER 2: Draw translucent overlay for depth
        # Creates the illusion of 3D by adding a light gray shadow
        # Strategy: Draw on a transparent surface first, then place on screen
        # This lets us use "alpha" (transparency) which pygame.draw.polygon doesn't support
        
        # Create a transparent surface (SRCALPHA = supports alpha transparency)
        # Size = diameter of asteroid + 4 extra pixels for safety
        surface = pygame.Surface(
            (self.radius * 2 + 4, self.radius * 2 + 4), pygame.SRCALPHA
        )
        
        # Adjust points to surface coordinate system
        # Why? The surface has its own (0,0) coordinate system
        # We need to translate points from world coordinates to surface coordinates
        # FORMULA: surface_point = world_point - (surface_top_left) + (surface_center)
        offset_points = [
            (
                p[0] - self.position.x + self.radius + 2,
                p[1] - self.position.y + self.radius + 2,
            )
            for p in points
        ]
        
        # Draw the overlay polygon with light gray (200,200,200) and 120 alpha (47% opaque)
        # Alpha values:
        #   0 = completely transparent (invisible)
        #   127-128 = 50% transparent (like frosted glass)
        #   255 = completely opaque (solid)
        # 120 alpha ≈ 47% opaque means you can see the dark layer through it
        pygame.draw.polygon(surface, (*self.color_outer, 120), offset_points)
        
        # "Blit" = copy the transparent surface onto the main screen
        # It blends with what's already there because of the alpha channel
        screen.blit(
            surface,
            (self.position.x - self.radius - 2, self.position.y - self.radius - 2),
        )

        # LAYER 3: Draw outline (white border)
        # Final layer: Draw the outline in white
        # This makes the asteroid stand out and look more defined
        # LINE_WIDTH determines outline thickness (usually 1-2 pixels)
        outline_color = (255, 255, 255)
        pygame.draw.polygon(screen, outline_color, points, self.outline_width)

    def split(self):
        """When shot, break this asteroid into two smaller pieces
        
        SPLITTING LOGIC:
        ================
        When the player shoots an asteroid, it doesn't just disappear.
        It splits into TWO SMALLER asteroids that spread apart!
        
        SIZE PROGRESSION:
        - Large asteroid (radius=40) → splits to 2 Medium (radius=30 each)
        - Medium asteroid (radius=30) → splits to 2 Small (radius=20 each)
        - Small asteroid (radius=20) → destroyed (too small to split further)
        
        VELOCITY CALCULATION:
        The velocity vectors spread the chunks apart using rotation:
        
        Original velocity: going RIGHT
        ↓
        After rotation:     ↙ CHUNK 1    (rotated +35°, faster)
        ↓                   ↘ CHUNK 2    (rotated -35°, faster)
        
        The 1.2x multiplier makes chunks faster than parent
        This creates action-packed visual when asteroids explode
        """
        # Step 1: Remove this asteroid from game
        self.kill()

        # STOP IF TOO SMALL - If already small, don't split further
        # (Small asteroids are destroyed completely - no more chunks)
        if self.radius <= ASTEROID_MIN_RADIUS:
            return

        # LOG THE EVENT - For debugging/statistics
        log_event("asteroid_split")

        # Step 2: Calculate velocities for split pieces
        # Choose a random spread angle (20-50 degrees)
        # This variation makes each split feel different
        angle = random.uniform(20, 50)

        # First piece: rotate velocityClockwise (positive angle), speed it up by 20%
        # EXAMPLE: if original velocity = (40, 0) pointing right at angle 0°
        #          then rotate 35° clockwise + 1.2x speed = pointing upper-right faster
        first_velocity = self.velocity.rotate(angle) * 1.2
        
        # Second piece: rotate velocity counter-clockwise (negative angle), speed it up by 20%
        # Going opposite direction from first chunk
        second_velocity = self.velocity.rotate(-angle) * 1.2

        # Step 3: Calculate size of split pieces
        # New radius = original radius - one "unit" of asteroid size
        # EXAMPLE: 40 - 10 = 30 (medium from large)
        new_radius = self.radius - ASTEROID_MIN_RADIUS

        # Step 4: CREATE TWO NEW ASTEROIDS at same position where parent died
        asteroid_1 = Asteroid(self.position.x, self.position.y, new_radius)
        asteroid_2 = Asteroid(self.position.x, self.position.y, new_radius)

        # Step 5: Set their velocities (they'll spread apart)
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
#
# ANIMATION CONCEPT - "SHOCKWAVE" EFFECT:
# =========================================
# A real explosion radiates energy outward in a shockwave ring.
# We simulate this in 2D with an EXPANDING CIRCLE that FADES OUT.
#
# The math behind the animation:
#   radius(t) = growth_rate * (total_life - remaining_life)   ← grows over time
#   alpha(t)  = 255 * (remaining_life / total_life)           ← shrinks (fades)
#
# EXAMPLE TIMELINE (0.5 second lifespan):
#   t=0.00s: radius=  0px, alpha=255 (tiny, solid orange ring)
#   t=0.125s: radius= 30px, alpha=191 (expanding, slightly transparent)
#   t=0.25s: radius= 60px, alpha=127 (half size, 50% transparent)
#   t=0.375s: radius= 90px, alpha= 64 (large, almost invisible)
#   t=0.50s: radius=120px, alpha=  0 (gone! removed from game)
#
# VISUAL RESULT:
#   (t=0)   (t=0.25s)         (t=0.5s)
#    ●   →     ◯    →         (invisible large ring)
#   tiny    medium            → then disappears
#
# This creates a satisfying "pop" effect on destruction.
# ============================================================================
class Explosion(CircleShape):
    """An expanding shockwave ring that shows where something exploded

    Features:
    - Starts as a tiny point and expands outward
    - Fades from solid to transparent as it grows
    - Orange color (fire/heat visual metaphor)
    - Lasts exactly 0.5 seconds then removes itself
    - Visual feedback confirming player destroyed an asteroid
    """

    def __init__(self, x, y):
        """Create explosion at position (x, y)

        The explosion starts as a single point (radius=0)
        and immediately begins expanding outward.
        """
        super().__init__(x, y, 0)  # Start with radius=0 (invisible point)
        self.life = 0.5        # Total lifespan in seconds (half a second)
        self.growth_rate = 240 # Expansion speed: 240 pixels per second
        # Why 240? At 0.5s lifespan: final radius = 240 * 0.5 = 120 pixels
        # Large enough to be visible, small enough to not dominate the screen

    def update(self, dt):
        """Update explosion each frame: expand ring and count down timer

        TWO THINGS HAPPEN SIMULTANEOUSLY:
        1. Timer counts DOWN (life decreases toward zero)
        2. Radius grows UP (circle expands outward)

        They run in opposite directions to create the fade+expand effect.

        FORMULA:
            new_life   = current_life - dt
            new_radius = current_radius + (growth_rate * dt)

        FRAME-RATE INDEPENDENCE:
        We multiply by dt (delta time) so the animation plays at the same
        speed regardless of frame rate:
        - At 60 FPS: dt ≈ 0.0167s → radius grows 240 × 0.0167 = 4px per frame
        - At 30 FPS: dt ≈ 0.033s  → radius grows 240 × 0.033 = 8px per frame
        Same total growth in 0.5 seconds either way!
        """
        # Count down the lifetime
        self.life -= dt

        # Expand the radius outward (shockwave spreading)
        self.radius += self.growth_rate * dt

        # When lifetime reaches zero, remove explosion from all sprite groups
        # self.kill() removes it from ALL groups it belongs to (clean removal)
        if self.life <= 0:
            self.kill()

    def draw(self, screen):
        """Draw the explosion as an expanding orange ring that fades out

        TRANSPARENCY ANIMATION TECHNIQUE:
        ==================================
        To make the ring FADE OUT as it expands, we use ALPHA TRANSPARENCY.
        Alpha is a 4th color value (after R, G, B) controlling opacity:
            alpha = 0   → completely invisible (transparent)
            alpha = 127 → 50% transparent (like tinted glass)
            alpha = 255 → fully opaque (solid, no transparency)

        ALPHA CALCULATION:
            alpha = 255 × (remaining_life / total_life)

        EXAMPLE at t=0.25s (halfway through animation):
            remaining_life = 0.25s
            total_life     = 0.5s
            ratio = 0.25 / 0.5 = 0.5   (50% of time left)
            alpha = 255 × 0.5 = 127.5 → rounded to 127
            → Circle is 50% transparent (half faded)

        WHY USE A SEPARATE SURFACE?
        pygame.draw.circle doesn't support per-pixel alpha directly.
        To draw a semi-transparent circle, we must:
        1. Create a small helper surface with SRCALPHA mode (supports alpha)
        2. Draw the circle onto that surface
        3. Blit (copy+blend) the surface onto the main game screen
        This way, the alpha blending is handled automatically.
        """
        # ===== STEP 1: CALCULATE TRANSPARENCY =====
        # How much time is left as a fraction (1.0 = just started, 0.0 = finished)
        # EXAMPLE: life=0.35, total=0.5 → ratio = 0.35/0.5 = 0.70 → alpha = 178
        alpha = max(0, int(255 * (self.life / 0.5)))
        # max(0, ...) prevents negative alpha in case of floating point rounding errors

        # ===== STEP 2: DEFINE COLOR =====
        # Orange = mixture of full red + high green + no blue
        # (255, 180, 0) is a warm orange, reminiscent of fire/explosion
        color = (255, 180, 0)

        # ===== STEP 3: CREATE TRANSPARENT SURFACE =====
        # Size = diameter + 2 extra pixels (so outline doesn't get clipped at edges)
        # pygame.SRCALPHA flag enables alpha channel (transparency support)
        surface = pygame.Surface(
            (self.radius * 2 + 2, self.radius * 2 + 2), pygame.SRCALPHA
        )

        # ===== STEP 4: DRAW THE RING ONTO SURFACE =====
        # We draw a circle OUTLINE (ring), not a filled circle
        # Why a ring? Real shockwaves are pressure waves - a ring, not a solid disc
        # The ring also looks "cooler" than a filled circle
        #
        # color + (alpha,) uses tuple concatenation to add alpha channel:
        # EXAMPLE: (255, 180, 0) + (178,) = (255, 180, 0, 178)  ← RGBA
        pygame.draw.circle(
            surface,
            color + (alpha,),                                # RGBA color with transparency
            (int(self.radius + 1), int(self.radius + 1)),   # Center on the surface (+1 padding)
            int(self.radius),                               # Radius of the ring
            2,                                              # Ring thickness = 2 pixels
        )

        # ===== STEP 5: COPY (BLIT) SURFACE ONTO MAIN SCREEN =====
        # Offset calculation ensures ring is centered on explosion position:
        # FORMULA: blit_x = explosion_x - radius - 1  (1 = half of the 2px padding)
        #          blit_y = explosion_y - radius - 1
        # This places top-left corner of our surface at the right spot
        screen.blit(
            surface,
            (self.position.x - self.radius - 1, self.position.y - self.radius - 1),
        )
