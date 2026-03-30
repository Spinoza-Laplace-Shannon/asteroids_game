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
        pygame.draw.polygon(screen, "white", self.triangle(), LINE_WIDTH)
        if self.shield_active:
            # pulsing glow using alpha
            pulse = (math.sin(self.shield_pulse * SHIELD_PULSE_SPEED) + 1) / 2
            alpha = int(80 + 120 * pulse)
            radius = self.radius * 1.5 + 4 * pulse

            # color transitions from green -> yellow -> red based on remaining shield time
            remaining = self.shield_timer / SHIELD_DURATION_SECONDS
            r = int((1.0 - remaining) * 255)
            g = int(remaining * 255)
            b = 50

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
            pygame.draw.polygon(screen, (r, g, b), self.triangle(), 2)

    # Moving around the screen
    def rotate(self, dt):
        self.rotation += PLAYER_TURN_SPEED * dt

    def update(self, dt):
        if not self.active:
            return

        keys = pygame.key.get_pressed()

        # Rotation
        if keys[pygame.K_LEFT]:
            self.rotate(-dt)
        if keys[pygame.K_RIGHT]:
            self.rotate(dt)

        # Thrust
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
        self.velocity += self.acceleration * dt

        # Apply friction and max speed
        if self.acceleration.length_squared() == 0:
            self.velocity *= PLAYER_FRICTION

        if self.velocity.length() > PLAYER_MAX_SPEED:
            self.velocity.scale_to_length(PLAYER_MAX_SPEED)

        self.position += self.velocity * dt
        self.wrap()

        # Decrease the shield timer
        if self.shield_active:
            self.shield_timer = max(0, self.shield_timer - dt)
            self.shield_pulse += dt
            if self.shield_timer <= 0:
                self.shield_active = False
                self.shield_expired = True

        # Decrease the shoot cooldown timer each frame.
        self.shot_cooldown_timer = max(0, self.shot_cooldown_timer - dt)

        # Decrease the bomb cooldown timer each frame.
        self.bomb_cooldown_timer = max(0, self.bomb_cooldown_timer - dt)

        # Weapon selection
        if keys[pygame.K_1]:
            self.weapon = WEAPON_SINGLE
        elif keys[pygame.K_2]:
            self.weapon = WEAPON_SPREAD
        elif keys[pygame.K_3]:
            self.weapon = WEAPON_RAPID

        if keys[pygame.K_SPACE]:
            self.shoot()

        if keys[pygame.K_b]:
            self.drop_bomb()

    def move(self, dt):
        unit_vector = pygame.Vector2(0, 1)
        rotated_vector = unit_vector.rotate(self.rotation)
        rotated_with_speed_vector = rotated_vector * PLAYER_SPEED * dt
        self.position += rotated_with_speed_vector

    def __point_line_distance(self, point, a, b):
        ap = point - a
        ab = b - a
        t = max(0, min(1, ap.dot(ab) / ab.length_squared()))
        closest = a + ab * t
        return point.distance_to(closest)

    def __point_in_triangle(self, pt, v1, v2, v3):
        d1 = (pt.x - v2.x) * (v1.y - v2.y) - (v1.x - v2.x) * (pt.y - v2.y)
        d2 = (pt.x - v3.x) * (v2.y - v3.y) - (v2.x - v3.x) * (pt.y - v3.y)
        d3 = (pt.x - v1.x) * (v3.y - v1.y) - (v3.x - v1.x) * (pt.y - v1.y)
        has_neg = (d1 < 0) or (d2 < 0) or (d3 < 0)
        has_pos = (d1 > 0) or (d2 > 0) or (d3 > 0)
        return not (has_neg and has_pos)

    def collides_with(self, other):
        # triangular hitbox for player
        if isinstance(other, CircleShape):
            tri = self.hit_triangle()
            # check if circle center is inside triangle
            if self.__point_in_triangle(
                other.position,
                pygame.Vector2(tri[0]),
                pygame.Vector2(tri[1]),
                pygame.Vector2(tri[2]),
            ):
                return True

            # edge-to-circle collision
            for i in range(len(tri)):
                a = pygame.Vector2(tri[i])
                b = pygame.Vector2(tri[(i + 1) % len(tri)])
                if self.__point_line_distance(other.position, a, b) <= other.radius:
                    return True
            return False

        return super().collides_with(other)

    def shoot(self):
        # If the cooldown is still active, do not shoot.
        if self.shot_cooldown_timer > 0:
            return None

        unit_vector = pygame.Vector2(0, 1).rotate(self.rotation)

        if self.weapon == WEAPON_SPREAD:
            self.shot_cooldown_timer = 0.8
            angles = [-15, 0, 15]
            for angle in angles:
                shot_velocity = unit_vector.rotate(angle) * (PLAYER_SHOOT_SPEED * 0.9)
                Shot(self.position, shot_velocity, WEAPON_COLOR_SPREAD)
            return None

        if self.weapon == WEAPON_RAPID:
            self.shot_cooldown_timer = 0.15
            shot_velocity = unit_vector * (PLAYER_SHOOT_SPEED * 1.4)
            Shot(self.position, shot_velocity, WEAPON_COLOR_RAPID)
            return None

        # Default single shot
        self.shot_cooldown_timer = PLAYER_SHOOT_COOLDOWN_SECONDS
        shot_velocity = unit_vector * PLAYER_SHOOT_SPEED
        return Shot(self.position, shot_velocity, WEAPON_COLOR_SINGLE)

    def drop_bomb(self):
        if self.bomb_cooldown_timer > 0:
            return None

        from bomb import Bomb

        self.bomb_cooldown_timer = BOMB_COOLDOWN_SECONDS
        bomb = Bomb(self.position.x, self.position.y, self.velocity.copy())
        return bomb
