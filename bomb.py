import pygame
from circleshape import CircleShape
from constants import BOMB_RADIUS, LINE_WIDTH


class Bomb(CircleShape):
    def __init__(self, x, y, velocity):
        super().__init__(x, y, BOMB_RADIUS)
        self.velocity = velocity
        self.fuse_time = 2.0  # explodes after 2 seconds
        self.exploded = False

    def draw(self, screen):
        # draw bomb as red circle with pulsing effect
        pygame.draw.circle(
            screen,
            (255, 100, 0),
            (self.position.x, self.position.y),
            self.radius,
            LINE_WIDTH,
        )
        # fuse indicator (inner circle shrinking as timer counts down)
        fuse_ratio = max(0, self.fuse_time / 2.0)
        inner_radius = int(self.radius * 0.6 * fuse_ratio)
        if inner_radius > 0:
            pygame.draw.circle(
                screen,
                (255, 200, 0),
                (self.position.x, self.position.y),
                inner_radius,
            )

    def update(self, dt):
        self.position += self.velocity * dt
        self.wrap()
        self.fuse_time -= dt
        if self.fuse_time <= 0:
            self.exploded = True
            self.kill()
