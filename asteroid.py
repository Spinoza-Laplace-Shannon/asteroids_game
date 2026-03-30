import pygame
import random
from constants import *
from logger import log_event
from player import *
from circleshape import CircleShape


# Asteroids Class:
class Asteroid(CircleShape):
    def __init__(self, x, y, radius):
        super().__init__(x, y, radius)
        self.vertex_count = random.randint(8, 14)
        self.jaggedness = 0.35
        self.offsets = [
            random.uniform(1 - self.jaggedness, 1 + self.jaggedness)
            for _ in range(self.vertex_count)
        ]
        self.outline_width = random.randint(1, 4)
        self.color_inner = (120, 120, 120)
        self.color_outer = (200, 200, 200)

    def draw(self, screen):
        points = []
        for i, offset in enumerate(self.offsets):
            angle = (360 / self.vertex_count) * i
            direction = pygame.Vector2(0, -1).rotate(angle)
            distance = self.radius * offset
            points.append(
                (
                    self.position.x + direction.x * distance,
                    self.position.y + direction.y * distance,
                )
            )

        # inner fill
        pygame.draw.polygon(screen, self.color_inner, points)

        # second fill overlay for depth with translucency using surface
        surface = pygame.Surface(
            (self.radius * 2 + 4, self.radius * 2 + 4), pygame.SRCALPHA
        )
        offset_points = [
            (
                p[0] - self.position.x + self.radius + 2,
                p[1] - self.position.y + self.radius + 2,
            )
            for p in points
        ]
        pygame.draw.polygon(surface, (*self.color_outer, 120), offset_points)
        screen.blit(
            surface,
            (self.position.x - self.radius - 2, self.position.y - self.radius - 2),
        )

        # outline
        outline_color = (255, 255, 255)
        pygame.draw.polygon(screen, outline_color, points, self.outline_width)

    def split(self):
        # This asteroid is destroyed immediately
        self.kill()

        # If the radius of the asteroid is less than or equal to ASTEROID_MIN_RADIUS, just return; this was a small asteroid and we're done.
        if self.radius <= ASTEROID_MIN_RADIUS:
            return

        # Otherwise, we need to spawn 2 new asteroids like so:
        log_event("asteroid_split")

        # random rotation 20..50 degrees
        angle = random.uniform(20, 50)

        first_velocity = self.velocity.rotate(angle) * 1.2
        second_velocity = self.velocity.rotate(-angle) * 1.2

        new_radius = self.radius - ASTEROID_MIN_RADIUS

        asteroid_1 = Asteroid(self.position.x, self.position.y, new_radius)
        asteroid_2 = Asteroid(self.position.x, self.position.y, new_radius)

        asteroid_1.velocity = first_velocity
        asteroid_2.velocity = second_velocity

    def update(self, dt):
        # move in a straight line at constant velocity
        self.position += self.velocity * dt
        self.wrap()


class Explosion(CircleShape):
    def __init__(self, x, y):
        super().__init__(x, y, 0)
        self.life = 0.5
        self.growth_rate = 240

    def update(self, dt):
        self.life -= dt
        self.radius += self.growth_rate * dt
        if self.life <= 0:
            self.kill()

    def draw(self, screen):
        alpha = max(0, int(255 * (self.life / 0.5)))
        color = (255, 180, 0)
        surface = pygame.Surface(
            (self.radius * 2 + 2, self.radius * 2 + 2), pygame.SRCALPHA
        )
        pygame.draw.circle(
            surface,
            color + (alpha,),
            (int(self.radius + 1), int(self.radius + 1)),
            int(self.radius),
            2,
        )
        screen.blit(
            surface,
            (self.position.x - self.radius - 1, self.position.y - self.radius - 1),
        )
