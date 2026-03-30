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

    def draw(self, screen):
        pygame.draw.circle(
            screen,
            "white",
            (self.position.x, self.position.y),
            self.radius,
            LINE_WIDTH,
        )

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
