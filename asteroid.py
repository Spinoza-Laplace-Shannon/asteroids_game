import pygame
from constants import *
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

    def update(self, dt):
        # move in a straight line at constant velocity
        self.position += self.velocity * dt
