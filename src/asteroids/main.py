import io
import math
import wave
import struct
import pygame
import random
import os
from pathlib import Path
from .constants import *
from .logger import log_state, log_event
from .player import *
from .asteroid import Asteroid, Explosion
from .asteroidfield import AsteroidField
from .powerup import PowerUp
from .bomb import Bomb
from .menu import Menu
from sys import exit
from .shot import Shot


# Get the project root directory (two levels up from this file)
PROJECT_ROOT = Path(__file__).parent.parent.parent
ASSETS_DIR = PROJECT_ROOT / "assets"
DATA_DIR = PROJECT_ROOT / "data"


def main():
    """Main game function - sets up and runs the entire Asteroids game"""
    print(f"Starting Asteroids with pygame version: {pygame.version.ver}")
    print(f"Screen width: {SCREEN_WIDTH} \nScreen height: {SCREEN_HEIGHT}")
    pygame.init()  # Initialize all Pygame modules
    pygame.mixer.init()  # Initialize sound system

    screen = pygame.display.set_mode(
        (SCREEN_WIDTH, SCREEN_HEIGHT)
    )  # Create game window
    pygame.display.set_caption("ASTEROIDS")  # Set window title
    clock = pygame.time.Clock()  # Used to control game speed (60 FPS)

    # SHOW MENU - Display menu and wait for player to select Play
    menu = Menu()
    menu_running = True
    while menu_running:
        action = menu.handle_input()  # Check for menu input (up/down/enter/quit)
        if action == "quit":
            return  # Exit game
        elif action == "play":
            menu_running = False  # Exit menu loop and start game
        menu.draw(screen)  # Draw menu on screen
        pygame.display.flip()  # Update display
        clock.tick(60)  # Run at 60 FPS

    # Get selected difficulty from menu
    difficulty = menu.difficulty
    print(f"Starting game with difficulty: {difficulty}")

    # AUDIO SETUP - Generate game sound effects
    def make_tone(freq, duration=0.2, volume=0.5, sample_rate=44100, waveform="sine"):
        """Create a sound effect by generating audio waveform
        This creates real sound data that Pygame can play

        Parameters:
        - freq: frequency in Hz (higher = higher pitch)
        - duration: how long sound plays in seconds
        - volume: how loud (0.0 to 1.0)
        - waveform: "sine", "triangle", or "square" (different shapes = different tones)
        """
        # Calculate total number of audio samples needed
        n_samples = int(sample_rate * duration)
        buf = bytearray()  # Store all audio samples here

        # Generate each audio sample
        for i in range(n_samples):
            t = i / sample_rate  # Current time in seconds
            phase = 2.0 * math.pi * freq * t  # Wave position

            # Create different wave shapes
            if waveform == "sine":
                value = math.sin(phase)  # Smooth wave
            elif waveform == "triangle":
                period = 1.0 / freq
                x = (t / period) % 1.0
                value = 4.0 * abs(x - 0.5) - 1.0  # Zig-zag wave
            elif waveform == "square":
                value = 1.0 if math.sin(phase) >= 0 else -1.0  # On/off wave
            else:
                value = math.sin(phase)

            sample = int(volume * 32767.0 * value)
            buf.extend(struct.pack("<h", sample))

        bio = io.BytesIO()
        with wave.open(bio, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(bytes(buf))
        bio.seek(0)
        return pygame.mixer.Sound(file=bio)

    pickup_sound = make_tone(
        880, duration=0.15, volume=SOUND_VOLUME_PICKUP, waveform="triangle"
    )
    block_sound = make_tone(
        440, duration=0.12, volume=SOUND_VOLUME_BLOCK, waveform="square"
    )
    shield_expire_sound = make_tone(
        660, duration=0.2, volume=SOUND_VOLUME_SHIELD_EXPIRE, waveform="sine"
    )

    # Load background image (optional)
    background = None
    try:
        bg_path = ASSETS_DIR / "images" / "backgrounds" / "5446991.jpg"
        if bg_path.exists():
            background = pygame.image.load(str(bg_path)).convert()
            background = pygame.transform.scale(background, (SCREEN_WIDTH, SCREEN_HEIGHT))
    except Exception as e:
        print(f"Could not load background image: {e}")
        background = None

    clock = pygame.time.Clock()
    dt = 0

    x = SCREEN_WIDTH / 2
    y = SCREEN_HEIGHT / 2

    score = 0
    lives = PLAYER_LIVES
    invulnerable_timer = 0
    respawn_timer = 0
    debug_draw_hitbox = False
    paused = False
    pause_selected = 0
    font = pygame.font.Font(None, 30)

    # Groups:
    updatable = pygame.sprite.Group()
    drawable = pygame.sprite.Group()
    asteroids = pygame.sprite.Group()
    shots = pygame.sprite.Group()
    powerups = pygame.sprite.Group()
    bombs = pygame.sprite.Group()

    Player.containers = (updatable, drawable)
    Asteroid.containers = (asteroids, updatable, drawable)
    AsteroidField.containers = updatable
    Shot.containers = (shots, updatable, drawable)
    Explosion.containers = (updatable, drawable)
    PowerUp.containers = (powerups, updatable, drawable)
    Bomb.containers = (bombs, updatable, drawable)

    asteroid_field = AsteroidField()

    # Create player instance:
    player = Player(x, y)
    powerup_spawn_timer = 0.0
    shield_ready_timer = 0.0
    shield_expire_text_timer = 0.0

    # Game loop:
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                paused = not paused
                pause_selected = 0
            if event.type == pygame.KEYDOWN and event.key == pygame.K_d:
                debug_draw_hitbox = not debug_draw_hitbox

            # Pause menu input
            if paused:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        pause_selected = (pause_selected - 1) % 2
                    elif event.key == pygame.K_DOWN:
                        pause_selected = (pause_selected + 1) % 2
                    elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        if pause_selected == 0:
                            paused = False
                        elif pause_selected == 1:
                            return

        if paused:
            # Draw pause menu overlay
            screen.fill("black")
            pause_title = font_large = pygame.font.Font(None, 80)
            title_text = pause_title.render("PAUSED", True, pygame.Color("yellow"))
            screen.blit(
                title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 100)
            )

            y_offset = 300
            pause_options = ["RESUME", "RETURN TO MENU"]
            for i, option in enumerate(pause_options):
                color = (
                    pygame.Color("yellow")
                    if i == pause_selected
                    else pygame.Color("white")
                )
                text = font.render(option, True, color)
                x = SCREEN_WIDTH // 2 - text.get_width() // 2
                screen.blit(text, (x, y_offset + i * 80))
                if i == pause_selected:
                    indicator = font.render(">", True, pygame.Color("yellow"))
                    screen.blit(indicator, (x - 60, y_offset + i * 80))
                    screen.blit(
                        indicator, (x + text.get_width() + 20, y_offset + i * 80)
                    )

            pygame.display.flip()
            clock.tick(60)
            continue

        dt = clock.tick(60) / 1000

        if background:
            screen.blit(background, (0, 0))
        else:
            screen.fill("black")

        # Draw HUD
        score_text = font.render(f"Score: {score}", True, pygame.Color("white"))
        screen.blit(score_text, (10, 10))

        lives_text = font.render(f"Lives: {lives}", True, pygame.Color("white"))
        screen.blit(lives_text, (10, 40))

        weapon_text = font.render(
            f"Weapon: {player.weapon}", True, pygame.Color("white")
        )
        screen.blit(weapon_text, (10, 70))

        weapon_color = pygame.Color("white")
        if player.weapon == WEAPON_SINGLE:
            weapon_color = pygame.Color(*WEAPON_COLOR_SINGLE)
        elif player.weapon == WEAPON_SPREAD:
            weapon_color = pygame.Color(*WEAPON_COLOR_SPREAD)
        elif player.weapon == WEAPON_RAPID:
            weapon_color = pygame.Color(*WEAPON_COLOR_RAPID)

        pygame.draw.circle(screen, weapon_color, (200, 80), 6)

        if invulnerable_timer > 0:
            invul_text = font.render("INVULNERABLE", True, pygame.Color("yellow"))
            screen.blit(invul_text, (10, 100))

        if respawn_timer > 0:
            respawn_text = font.render(
                f"RESPAWNING... {respawn_timer:.1f}s", True, pygame.Color("cyan")
            )
            screen.blit(respawn_text, (10, 100))

        if shield_ready_timer > 0:
            shield_ready_text = font.render("Shield Ready!", True, pygame.Color("lime"))
            screen.blit(shield_ready_text, (SCREEN_WIDTH // 2 - 80, 30))
            shield_ready_timer = max(0, shield_ready_timer - dt)

        help_text = font.render(
            "Arrows=Move, 1=Single 2=Spread 3=Rapid, Space=Fire, B=Bomb, ESC=Pause",
            True,
            pygame.Color("lightgray"),
        )
        screen.blit(help_text, (10, SCREEN_HEIGHT - 30))

        for object in drawable:
            if isinstance(object, Player) and not player.active:
                continue
            object.draw(screen)

        if debug_draw_hitbox and player.active:
            pygame.draw.polygon(
                screen, pygame.Color("yellow"), player.hit_triangle(), 1
            )

        if shield_expire_text_timer > 0:
            expired_text = font.render("Shield Expired", True, pygame.Color("red"))
            screen.blit(expired_text, (SCREEN_WIDTH // 2 - 90, 60))

        # Handle respawn timer and player active state
        if respawn_timer > 0:
            respawn_timer = max(0, respawn_timer - dt)
            player.active = False
            if respawn_timer == 0:
                player.active = True
                invulnerable_timer = PLAYER_RESPAWN_INVULNERABLE_SECONDS

        # Power-up spawn timer
        powerup_spawn_timer += dt
        if powerup_spawn_timer >= POWERUP_SPAWN_RATE_SECONDS:
            powerup_spawn_timer = 0
            x = random.uniform(100, SCREEN_WIDTH - 100)
            y = random.uniform(100, SCREEN_HEIGHT - 100)
            PowerUp(x, y)
            shield_ready_timer = 2.0

        for object in updatable:
            object.update(dt)

        # Player catches power-up
        for powerup in list(powerups):
            if player.collides_with(powerup):
                powerup.kill()
                player.shield_active = True
                player.shield_timer = SHIELD_DURATION_SECONDS
                player.shield_expired = False
                pickup_sound.play()
                log_event("shield_picked", shield_timer=player.shield_timer)

        # shield expired effect
        if hasattr(player, "shield_expired") and player.shield_expired:
            shield_expire_sound.play()
            shield_expire_text_timer = SHIELD_EXPIRE_TEXT_DURATION
            player.shield_expired = False

        if respawn_timer <= 0 and invulnerable_timer <= 0:
            for asteroid in list(asteroids):
                if player.collides_with(asteroid):
                    if player.shield_active:
                        player.shield_active = False
                        player.shield_timer = 0
                        block_sound.play()
                        log_event(
                            "shield_block",
                            asteroid_pos=[
                                round(asteroid.position.x, 2),
                                round(asteroid.position.y, 2),
                            ],
                        )
                        asteroid.split()
                        continue

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
                        # Save high score if current score is better
                        if score > menu.high_score:
                            menu.save_high_score(score)
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

        if shield_expire_text_timer > 0:
            shield_expire_text_timer = max(0, shield_expire_text_timer - dt)

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

        # Handle bomb explosions
        for bomb in list(bombs):
            if bomb.exploded:
                # Create explosion visual at bomb location
                Explosion(bomb.position.x, bomb.position.y)
                log_event(
                    "bomb_exploded",
                    bomb_pos=[round(bomb.position.x, 2), round(bomb.position.y, 2)],
                )

                # Damage all nearby asteroids
                for asteroid in list(asteroids):
                    distance = bomb.position.distance_to(asteroid.position)
                    if distance <= BOMB_DAMAGE_RADIUS:
                        asteroid.split()

        log_state()
        pygame.display.flip()


if __name__ == "__main__":
    main()
