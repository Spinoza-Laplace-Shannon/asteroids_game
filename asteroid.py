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
            color="white",
            center=(self.position.x, self.position.y),
            radius=self.radius,
            width=LINE_WIDTH,
        )
