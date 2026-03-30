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
        """Draw the bomb as orange circle with yellow fuse indicator
        
        VISUAL DESIGN:
        ==============
        The fuse indicator shows remaining time VISUALLY
        Instead of displaying a number, the yellow circle SHRINKS
        as time runs out. When yellow circle is gone → BOOM!
        
        FUSE VISUAL PROGRESSION (2 second fuse):
        ┌─────────────────────────────────────────┐
        │ t=2.0s: ●●●●●●● (full yellow circle)   │
        │ t=1.5s: ●●●●●   (smaller)              │
        │ t=1.0s: ●●●     (half size)            │
        │ t=0.5s: ●       (tiny)                 │
        │ t=0.0s: (gone)   → EXPLOSION!          │
        └─────────────────────────────────────────┘
        
        This gives player immediate visual feedback of danger!
        """
        # ===== LAYER 1: DRAW BOMB BODY =====
        # Orange circle with thin outline
        # This is the actual bomb (constant size)
        pygame.draw.circle(
            screen,
            (255, 100, 0),  # RGB: Orange
            (self.position.x, self.position.y),
            self.radius,    # 5 pixels (from constants.py)
            LINE_WIDTH,     # Usually 2 pixels (outline thickness)
        )

        # ===== LAYER 2: DRAW FUSE INDICATOR =====
        # This yellow circle SHRINKS as time ticks down
        # Calculation: inner_radius = 0.6 * radius * (fuse_time / 2.0)
        #
        # BREAKDOWN:
        # - fuse_ratio = fuse_time / 2.0 → ranges from 1.0 (start) to 0.0 (end)
        # - 0.6 * radius → make yellow circle 60% of bomb radius
        # - Multiply by fuse_ratio → shrink as time passes
        #
        # EXAMPLE: fuse_time = 1.0, radius = 5
        #   fuse_ratio = 1.0 / 2.0 = 0.5 (50% time elapsed)
        #   inner_radius = 0.6 * 5 * 0.5 = 1.5 pixels
        
        fuse_ratio = max(0, self.fuse_time / 2.0)  # Clamp to minimum 0
        inner_radius = int(self.radius * 0.6 * fuse_ratio)  # Convert to integer

        # Only draw if there's something to see (inner_radius > 0)
        # Otherwise, drawing a 0-pixel circle wastes processing
        if inner_radius > 0:
            pygame.draw.circle(
                screen,
                (255, 200, 0),  # RGB: Yellow (brighter than orange)
                (self.position.x, self.position.y),
                inner_radius,
                # No outline thickness parameter = filled circle (solid yellow)
            )

    def update(self, dt):
        """Update bomb: move it, count down fuse, and explode when ready
        
        COUNTDOWN LOGIC:
        ================
        This method handles the complete bomb lifecycle:
        1. Move bomb forward (it has initial velocity from where player threw it)
        2. Count down fuse timer
        3. Detect when fuse reaches zero
        4. Mark as exploded (main.py handles actual explosion)
        
        TIMELINE EXAMPLE:
        t=2.0s: Bomb spawned, fuse_time=2.0, yellow indicator full
        t=1.5s: fuse_time=1.5 (dt added 0.5 seconds)
        t=1.0s: fuse_time=1.0 (halfway to explosion)
        t=0.5s: fuse_time=0.5 (about to explode!)
        t=0.0s: fuse_time≤0 → Set exploded=True (handoff to main.py)
        """
        # Step 1: MOVE BOMB
        # Bombs inherit initial velocity from player's ship
        # Travel in given direction at current velocity
        # EXAMPLE: velocity=(100, 50) means move 100px right, 50px down per second
        self.position += self.velocity * dt

        # Step 2: WRAP AROUND SCREEN
        # Like asteroids, bombs wrap at screen edges
        # Allows bombs thrown off-screen to wrap around
        # (Toroidal world = pac-man style wrapping)
        self.wrap()

        # Step 3: COUNT DOWN FUSE
        # Each frame, subtract elapsed time from fuse timer
        # dt = "delta time" = seconds since last frame
        # At 60 FPS: dt ≈ 0.0167 (1/60th second)
        # At 4 FPS: dt ≈ 0.25 (slower frame rate)
        # This makes fuse countdown frame-rate independent
        # (Takes same 2 seconds regardless of FPS)
        self.fuse_time -= dt

        # Step 4: CHECK IF TIME TO EXPLODE
        # When fuse_time drops to zero or below, it's time!
        # We only SET a flag here - main.py handles actual explosion
        # Why? Main.py needs to check for nearby asteroids to damage
        if self.fuse_time <= 0:
            self.exploded = True  # Set flag indicating explosion occurred
            self.kill()  # Remove bomb from sprite groups
