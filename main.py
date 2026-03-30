import pygame
from constants import *
from logger import log_state, log_event
from player import *
from asteroid import Asteroid
from asteroidfield import AsteroidField
from sys import exit
from shot import Shot


def main():
    print(f"Starting Asteroids with pygame version: {pygame.version.ver}")
    print(f"Screen width: {SCREEN_WIDTH} \nScreen height: {SCREEN_HEIGHT}")
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()
    dt = 0

    x = SCREEN_WIDTH / 2
    y = SCREEN_HEIGHT / 2

    score = 0
    font = pygame.font.Font(None, 30)

    # Groups:
    updatable = pygame.sprite.Group()
    drawable = pygame.sprite.Group()
    asteroids = pygame.sprite.Group()
    shots = pygame.sprite.Group()

    Player.containers = (updatable, drawable)
    Asteroid.containers = (asteroids, updatable, drawable)
    AsteroidField.containers = updatable
    Shot.containers = (shots, updatable, drawable)

    asteroid_field = AsteroidField()

    # Create player instance:
    player = Player(x, y)

    # Game loop:
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return

        dt = clock.tick(60) / 1000

        screen.fill("black")

        # Draw HUD
        score_text = font.render(f"Score: {score}", True, pygame.Color("white"))
        screen.blit(score_text, (10, 10))

        for object in drawable:
            object.draw(screen)
        for object in updatable:
            object.update(dt)
        for asteroid in list(asteroids):
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

        for asteroid in list(asteroids):
            for shot in list(shots):
                if asteroid.collides_with(shot):
                    if asteroid.radius <= ASTEROID_MIN_RADIUS:
                        points = SCORE_SMALL_ASTEROID
                    elif asteroid.radius <= ASTEROID_MIN_RADIUS * 2:
                        points = SCORE_MEDIUM_ASTEROID
                    else:
                        points = SCORE_LARGE_ASTEROID

                    score += points

                    log_event(
                        "asteroid_shot",
                        points=points,
                        score=score,
                        asteroid_radius=asteroid.radius,
                    )

                    shot.kill()
                    asteroid.split()

        log_state()
        pygame.display.flip()


if __name__ == "__main__":
    main()
