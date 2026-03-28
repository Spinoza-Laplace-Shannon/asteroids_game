import pygame
from constants import *
from logger import log_state, log_event
from player import *
from asteroid import Asteroid
from asteroidfield import AsteroidField
from sys import exit


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
        for asteroid in asteroids:
            if player.collides_with(asteroid):
                log_event(
                    "player_hit",
                    player_pos=[
                        round(player.position.x, 2),
                        round(player.position.y, 2),
                    ],
                    asteroid_pos=[
                        round(asteroid.position.x, 2),
                        round(asteroid.position.y, 2),
                    ],
                )

                print("Game over!")
                exit()
        log_state()
        pygame.display.flip()


if __name__ == "__main__":
    main()
