import pygame
import pygame
from circleshape import CircleShape
from constants import SHOT_RADIUS, SCREEN_WIDTH, SCREEN_HEIGHT, LINE_WIDTH


class Shot(CircleShape):
    def __init__(self, position, velocity, color=(255, 255, 255)):
        super().__init__(position.x, position.y, SHOT_RADIUS)
        self.velocity = velocity
        self.color = color

    def draw(self, screen):
        pygame.draw.circle(
            screen,
            self.color,
            (self.position.x, self.position.y),
            self.radius,
            LINE_WIDTH,
        )

    def update(self, dt):
        self.position += self.velocity * dt
        self.wrap()
