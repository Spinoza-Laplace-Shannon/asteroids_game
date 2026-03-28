import pygame
from constants import *
from logger import log_state
from player import *
from asteroid import Asteroid
from asteroidfield import AsteroidField


def main():
    print(f"Starting Asteroids with pygame version: {pygame.version.ver}")
    print(f"Screen width: {SCREEN_WIDTH} \nScreen height: {SCREEN_HEIGHT}")
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()
    dt = 0

    x = SCREEN_WIDTH / 2
    y = SCREEN_HEIGHT / 2

    # Groups:
    updatable = pygame.sprite.Group()
    drawable = pygame.sprite.Group()
    asteroids = pygame.sprite.Group()

    Player.containers = (updatable, drawable)
    Asteroid.containers = (asteroids, updatable, drawable)
    AsteroidField.containers = updatable

    asteroid_field = AsteroidField()

    # Create player instance:
    player = Player(x, y)

    # Game loop:
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            clock.tick(60)
            dt = clock.tick(60) / 1000

        screen.fill("black")
        for object in drawable:
            object.draw(screen)
        for object in updatable:
            object.update(dt)
        log_state()
        pygame.display.flip()


if __name__ == "__main__":
    main()
