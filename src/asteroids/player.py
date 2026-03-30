import math
import pygame
from .constants import (
    PLAYER_RADIUS,
    LINE_WIDTH,
    PLAYER_TURN_SPEED,
    PLAYER_SPEED,
    PLAYER_ACCELERATION,
    PLAYER_FRICTION,
    PLAYER_MAX_SPEED,
    PLAYER_SHOOT_SPEED,
    PLAYER_SHOOT_COOLDOWN_SECONDS,
    WEAPON_SINGLE,
    WEAPON_SPREAD,
    WEAPON_RAPID,
    WEAPON_COLOR_SINGLE,
    WEAPON_COLOR_SPREAD,
    WEAPON_COLOR_RAPID,
    PLAYER_HITBOX_SCALE,
    SHIELD_PULSE_SPEED,
    BOMB_COOLDOWN_SECONDS,
    SHIELD_DURATION_SECONDS,
)
from .circleshape import CircleShape
from .shot import Shot


# ============================================================================
# The Player class represents the spaceship that the player controls
# It handles movement, rotation, shooting, shields, and collision detection
# ============================================================================
class Player(CircleShape):
    """The player's spaceship - shoot asteroids and avoid collisions!

    Features:
    - Rotation with arrow keys (LEFT/RIGHT)
    - Acceleration with UP arrow
    - Multiple weapon types
    - Shield power-up
    - Bombs that explode asteroids
    """

    def __init__(self, x, y):
        """Create a player at position (x, y)"""
        super().__init__(x, y, PLAYER_RADIUS)  # Call parent CircleShape class
        self.rotation = 0  # Current angle the ship is pointing (0-360 degrees)
        self.shot_cooldown_timer = 0  # Count down until next shot allowed
        self.velocity = pygame.Vector2(0, 0)  # Current speed and direction
        self.acceleration = pygame.Vector2(0, 0)  # Current thrust force
        self.active = True  # Is this player active?
        self.weapon = WEAPON_SINGLE  # Current weapon type
        self.shield_active = False  # Is shield protecting the player?
        self.shield_timer = 0  # How long shield has been active
        self.shield_pulse = 0  # Animation counter for shield glow
        self.shield_expired = False  # Did shield just expire?
        self.bomb_cooldown_timer = 0  # Count down until next bomb allowed

    def triangle(self):
        """Calculate the 3 points that make up the visible ship triangle
        
        The ship is drawn as a triangle pointing in the direction of rotation.
        We need to calculate where the 3 corners of this triangle are.
        
        VISUAL EXPLANATION (when rotation = 0, ship points UP):
        
                    a (nose/front)
                    *
                   / \\
                  /   \\
              b *-------* c (back corners)
              (left)  (right)
        
        The math:
        - "forward" = direction the ship is pointing
        - "right" = perpendicular direction (90 degrees from forward)
        - We multiply these by the radius to get the three points
        
        When the player rotates:
        - self.rotation changes (0 to 360 degrees)
        - forward vector rotates with .rotate(self.rotation)
        - This makes the triangle rotate too!
        """
        # Create a vector pointing UP (0, 1), then rotate it by current rotation angle
        forward = pygame.Vector2(0, 1).rotate(self.rotation)

        # Create a vector pointing RIGHT (perpendicular to forward)
        # 90 degrees is quarter turn from forward
        right = pygame.Vector2(0, 1).rotate(self.rotation + 90) * self.radius / 1.5

        # Calculate the three corner points:
        # a = front of ship (nose)
        a = self.position + forward * self.radius
        # b = back-left corner
        b = self.position - forward * self.radius - right
        # c = back-right corner
        c = self.position - forward * self.radius + right

        return [a, b, c]

    def hit_triangle(self):
        """Calculate the collision detection triangle (may be smaller than visual)

        This is like triangle() but SMALLER for more precise collision detection.
        We use PLAYER_HITBOX_SCALE (usually 0.9 = 90%) to make hitbox 90% of visual size.

        WHY? Because collision is more forgiving to the player this way.
        Players expect bullets to hit them only if they REALLY touch the ship.
        A smaller hitbox makes the game feel more fair.
        """
        # Scale factor (0.9 = 90%)
        scale = PLAYER_HITBOX_SCALE

        # Same calculation as triangle(), but multiply each point by scale
        forward = pygame.Vector2(0, 1).rotate(self.rotation)
        right = pygame.Vector2(0, 1).rotate(self.rotation + 90) * self.radius / 1.5

        # Scale all the points down
        a = self.position + forward * self.radius * scale
        b = self.position - forward * self.radius * scale - right * scale
        c = self.position - forward * self.radius * scale + right * scale

        return [a, b, c]

    def draw(self, screen):
        """Draw the ship, then add a pulsing shield bubble if needed.

        Drawing order matters in games:
        1. Draw the shield glow first so it sits behind the ship.
        2. Draw the ship outline on top so it stays easy to see.

        The shield uses two visual tricks:
        - sine wave pulse: math.sin(...) smoothly grows and shrinks the glow
        - colour gradient: green at first, then yellow, then red near the end
        """
        pygame.draw.polygon(screen, "white", self.triangle(), LINE_WIDTH)

        if self.shield_active:
            # math.sin returns a value between -1 and +1.
            # Adding 1 and dividing by 2 remaps it to 0 -> 1.
            # That gives us a nice smooth pulse value for animation.
            pulse = (math.sin(self.shield_pulse * SHIELD_PULSE_SPEED) + 1) / 2

            # Alpha controls transparency.
            # 80 = faint, 200 = much more visible.
            alpha = int(80 + 120 * pulse)

            # The shield is bigger than the ship and slightly expands/contracts.
            radius = self.radius * 1.5 + 4 * pulse

            # remaining goes from 1.0 down to 0.0 as the shield runs out.
            remaining = self.shield_timer / SHIELD_DURATION_SECONDS

            # We blend from green to red over time:
            # start:   red=0,   green=255
            # middle:  red~128, green~128
            # end:     red=255, green=0
            r = int((1.0 - remaining) * 255)
            g = int(remaining * 255)
            b = 50

            # To draw transparent shapes in pygame, we often draw them on a
            # temporary surface that supports alpha, then copy that surface
            # onto the main screen.
            glow_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(
                glow_surface,
                (r, g, b, alpha),
                (radius, radius),
                int(radius),
            )
            screen.blit(
                glow_surface,
                (self.position.x - radius, self.position.y - radius),
            )

            # Redraw the ship outline in the same colour as the shield so the
            # player can instantly tell how much shield time is left.
            pygame.draw.polygon(screen, (r, g, b), self.triangle(), 2)

    # Moving around the screen
    def rotate(self, dt):
        """Turn the ship.

        PLAYER_TURN_SPEED is measured in degrees per second.
        Multiplying by dt makes turning frame-rate independent.

        Example:
        If dt is about 0.016 seconds at 60 FPS,
        300 * 0.016 is about 4.8 degrees this frame.
        """
        self.rotation += PLAYER_TURN_SPEED * dt

    def update(self, dt):
        """Run one full update step for the player.

        This method is the heart of the ship logic. Each frame it:
        1. reads the keyboard
        2. rotates the ship
        3. computes thrust
        4. updates velocity and position
        5. applies cooldowns and shield timers
        6. handles weapon switching and firing

        Using dt everywhere keeps the game speed stable on different computers.
        """
        if not self.active:
            return

        # pygame.key.get_pressed gives the current state of every key.
        keys = pygame.key.get_pressed()

        # Rotation changes the ship's angle, but not its position directly.
        if keys[pygame.K_LEFT]:
            self.rotate(-dt)
        if keys[pygame.K_RIGHT]:
            self.rotate(dt)

        # Thrust creates acceleration in the direction the ship is facing.
        # No key pressed means acceleration stays at zero.
        thrust_vector = pygame.Vector2(0, 0)
        if keys[pygame.K_UP]:
            thrust_vector = (
                pygame.Vector2(0, 1).rotate(self.rotation) * PLAYER_ACCELERATION
            )
        if keys[pygame.K_DOWN]:
            thrust_vector = (
                pygame.Vector2(0, -1).rotate(self.rotation) * PLAYER_ACCELERATION
            )

        self.acceleration = thrust_vector

        # Physics rule:
        # new velocity = old velocity + acceleration * time
        self.velocity += self.acceleration * dt

        # Friction only applies when not thrusting.
        # That makes the ship glide, but slowly lose speed.
        if self.acceleration.length_squared() == 0:
            self.velocity *= PLAYER_FRICTION

        # If the player somehow goes too fast, clamp the speed while keeping
        # the same direction of travel.
        if self.velocity.length() > PLAYER_MAX_SPEED:
            self.velocity.scale_to_length(PLAYER_MAX_SPEED)

        # Position changes by velocity * time.
        self.position += self.velocity * dt
        self.wrap()

        # Shield timing and pulse animation
        if self.shield_active:
            self.shield_timer = max(0, self.shield_timer - dt)
            self.shield_pulse += dt
            if self.shield_timer <= 0:
                self.shield_active = False
                self.shield_expired = True

        # Cooldowns count down toward zero.
        self.shot_cooldown_timer = max(0, self.shot_cooldown_timer - dt)
        self.bomb_cooldown_timer = max(0, self.bomb_cooldown_timer - dt)

        # Number keys switch weapon mode.
        if keys[pygame.K_1]:
            self.weapon = WEAPON_SINGLE
        elif keys[pygame.K_2]:
            self.weapon = WEAPON_SPREAD
        elif keys[pygame.K_3]:
            self.weapon = WEAPON_RAPID

        # Holding the key keeps trying to fire, but cooldowns prevent spam.
        if keys[pygame.K_SPACE]:
            self.shoot()

        if keys[pygame.K_b]:
            self.drop_bomb()

    def move(self, dt):
        """Older movement helper kept for compatibility.

        This version moves directly in the facing direction at a fixed speed.
        The game now uses acceleration + velocity in update(), which feels more
        like movement in space.
        """
        unit_vector = pygame.Vector2(0, 1)
        rotated_vector = unit_vector.rotate(self.rotation)
        rotated_with_speed_vector = rotated_vector * PLAYER_SPEED * dt
        self.position += rotated_with_speed_vector

    def __point_line_distance(self, point, a, b):
        """Return the shortest distance between a point and a segment.

        Why do we need this?
        An asteroid can hit the side of the triangular ship without its centre
        entering the triangle. This helper lets us test the distance from the
        asteroid centre to each ship edge.

        Idea:
        - project the point onto the line
        - clamp that projection so it stays on the segment
        - measure distance to the closest point found

        ASCII PICTURE:

             point P
                *
                |
                | shortest distance
                |
            A -------X---------------- B
                ^
               closest point on segment

        VECTOR IDEA:
        - AB tells us the direction of the segment
        - AP tells us where the point is relative to A
        - the dot product helps answer:
          "how far along AB should we walk to get closest to P?"

        FORMULA:
            t = dot(AP, AB) / |AB|^2

        Then:
        - t < 0  means the closest point would be before A, so we clamp to A
        - t > 1  means the closest point would be after B, so we clamp to B
        - 0 <= t <= 1 means the closest point is really on the segment
        """
        ap = point - a
        ab = b - a
        t = max(0, min(1, ap.dot(ab) / ab.length_squared()))
        closest = a + ab * t
        return point.distance_to(closest)

    def __point_in_triangle(self, pt, v1, v2, v3):
        """Return True if pt lies inside the triangle.

        This uses the sign of 2D cross products.
        If the point is on the same side of all three triangle edges,
        it is inside the triangle.

                ASCII IDEA:

                                             v1
                                            /  \
                                         /  pt\
                                        /      \
                                    v2--------v3

                Imagine walking around the triangle edge by edge.
                Each cross product asks whether pt is to the left or to the right of
                the current directed edge.

                If the answers stay consistent for all 3 edges, pt is inside.

                SAME SIGN  -> inside
                MIXED SIGN -> outside

                This works because a triangle is convex: it has no inward dents.
        """
        d1 = (pt.x - v2.x) * (v1.y - v2.y) - (v1.x - v2.x) * (pt.y - v2.y)
        d2 = (pt.x - v3.x) * (v2.y - v3.y) - (v2.x - v3.x) * (pt.y - v3.y)
        d3 = (pt.x - v1.x) * (v3.y - v1.y) - (v3.x - v1.x) * (pt.y - v1.y)
        has_neg = (d1 < 0) or (d2 < 0) or (d3 < 0)
        has_pos = (d1 > 0) or (d2 > 0) or (d3 > 0)
        return not (has_neg and has_pos)

    def collides_with(self, other):
        """Use a triangular hitbox for the ship instead of a circle.

        The ship is visually a triangle, so a triangle hitbox feels fairer.
        We use two checks:
        1. Is the other object's centre inside the triangle?
        2. Is the other object's circular edge touching one triangle side?

        COMBINED STRATEGY:

            circle center inside triangle?   yes -> collision
                                  no
                                  |
                                  v
            circle edge touches a triangle side? yes -> collision
                                           no  -> no collision

        This two-step method is more accurate than pretending the player ship
        is just one big circle.
        """
        if isinstance(other, CircleShape):
            tri = self.hit_triangle()

            # First test: the other circle's centre is inside the ship triangle.
            if self.__point_in_triangle(
                other.position,
                pygame.Vector2(tri[0]),
                pygame.Vector2(tri[1]),
                pygame.Vector2(tri[2]),
            ):
                return True

            # Second test: the circle might touch one of the triangle edges.
            for i in range(len(tri)):
                a = pygame.Vector2(tri[i])
                b = pygame.Vector2(tri[(i + 1) % len(tri)])
                if self.__point_line_distance(other.position, a, b) <= other.radius:
                    return True
            return False

        return super().collides_with(other)

    def shoot(self):
        """Fire the currently selected weapon.

        Weapon summary:
        - SINGLE: one normal bullet
        - SPREAD: three bullets at different angles
        - RAPID: one faster bullet with a shorter cooldown

        Cooldown prevents one key hold from creating hundreds of shots per
        second. The timer is reduced in update().
        """
        if self.shot_cooldown_timer > 0:
            return None

        # Build a unit vector that points in the same direction as the ship.
        unit_vector = pygame.Vector2(0, 1).rotate(self.rotation)

        if self.weapon == WEAPON_SPREAD:
            # Longer cooldown because three bullets are fired at once.
            self.shot_cooldown_timer = 0.8
            angles = [-15, 0, 15]
            for angle in angles:
                shot_velocity = unit_vector.rotate(angle) * (PLAYER_SHOOT_SPEED * 0.9)
                Shot(self.position, shot_velocity, WEAPON_COLOR_SPREAD)
            return None

        if self.weapon == WEAPON_RAPID:
            # Short cooldown and faster bullet for a more aggressive feel.
            self.shot_cooldown_timer = 0.15
            shot_velocity = unit_vector * (PLAYER_SHOOT_SPEED * 1.4)
            Shot(self.position, shot_velocity, WEAPON_COLOR_RAPID)
            return None

        # Default single shot: simple and balanced.
        self.shot_cooldown_timer = PLAYER_SHOOT_COOLDOWN_SECONDS
        shot_velocity = unit_vector * PLAYER_SHOOT_SPEED
        return Shot(self.position, shot_velocity, WEAPON_COLOR_SINGLE)

    def drop_bomb(self):
        """Drop a bomb that keeps the ship's current motion.

        self.velocity.copy() is important: it gives the bomb its own Vector2.
        Without copy(), the bomb and the player could accidentally share the
        same velocity object.

        The import is inside the method to avoid circular import problems.
        """
        if self.bomb_cooldown_timer > 0:
            return None

        from .bomb import Bomb

        self.bomb_cooldown_timer = BOMB_COOLDOWN_SECONDS
        bomb = Bomb(self.position.x, self.position.y, self.velocity.copy())
        return bomb
