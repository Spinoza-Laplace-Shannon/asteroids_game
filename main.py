import pygame
from constants import *
from logger import log_state, log_event
from player import *
from asteroid import Asteroid, Explosion
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
    lives = PLAYER_LIVES
    invulnerable_timer = 0
    respawn_timer = 0
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
    Explosion.containers = (updatable, drawable)

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

        lives_text = font.render(f"Lives: {lives}", True, pygame.Color("white"))
        screen.blit(lives_text, (10, 40))

        if invulnerable_timer > 0:
            invul_text = font.render("INVULNERABLE", True, pygame.Color("yellow"))
            screen.blit(invul_text, (10, 70))

        if respawn_timer > 0:
            respawn_text = font.render(
                f"RESPAWNING... {respawn_timer:.1f}s", True, pygame.Color("cyan")
            )
            screen.blit(respawn_text, (10, 100))

        for object in drawable:
            if isinstance(object, Player) and not player.active:
                continue
            object.draw(screen)

        # Handle respawn timer and player active state
        if respawn_timer > 0:
            respawn_timer = max(0, respawn_timer - dt)
            player.active = False
            if respawn_timer == 0:
                player.active = True
                invulnerable_timer = PLAYER_RESPAWN_INVULNERABLE_SECONDS

        for object in updatable:
            object.update(dt)

        if respawn_timer <= 0 and invulnerable_timer <= 0:
            for asteroid in list(asteroids):
                if player.collides_with(asteroid):
                    lives -= 1
                    log_event(
                        "player_hit",
                        lives=lives,
                        player_pos=[
                            round(player.position.x, 2),
                            round(player.position.y, 2),
                        ],
                        asteroid_pos=[
                            round(asteroid.position.x, 2),
                            round(asteroid.position.y, 2),
                        ],
                    )

                    if lives <= 0:
                        print("Game over!")
                        exit()

                    # Respawn player in center and reset velocity
                    player.position = pygame.Vector2(
                        SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2
                    )
                    player.rotation = 0
                    player.velocity = pygame.Vector2(0, 0)
                    invulnerable_timer = PLAYER_RESPAWN_INVULNERABLE_SECONDS

                    # Remove active shots to avoid instant death on respawn
                    for shot in list(shots):
                        shot.kill()
                    break

        if invulnerable_timer > 0:
            invulnerable_timer = max(0, invulnerable_timer - dt)

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

                    # Add explosion effect when asteroid is hit
                    Explosion(asteroid.position.x, asteroid.position.y)

                    shot.kill()
                    asteroid.split()

        log_state()
        pygame.display.flip()


if __name__ == "__main__":
    main()
