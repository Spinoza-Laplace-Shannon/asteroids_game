import pygame
from circleshape import CircleShape
from constants import POWERUP_SHIELD_RADIUS, SCREEN_WIDTH, SCREEN_HEIGHT


class PowerUp(CircleShape):
    def __init__(self, x, y):
        super().__init__(x, y, POWERUP_SHIELD_RADIUS)

    def draw(self, screen):
        # glowing green circle
        pygame.draw.circle(
            screen, (50, 220, 50), (self.position.x, self.position.y), self.radius
        )
        pygame.draw.circle(
            screen, (0, 150, 0), (self.position.x, self.position.y), self.radius, 2
        )

    def update(self, dt):
        # stationary, keep wrapping
        self.wrap()
