import io
import math
import wave
import struct
import pygame
import random
from pathlib import Path
from .constants import (
    ASTEROID_MIN_RADIUS,
    BOMB_DAMAGE_RADIUS,
    PLAYER_LIVES,
    PLAYER_RESPAWN_INVULNERABLE_SECONDS,
    POWERUP_SPAWN_RATE_SECONDS,
    SCORE_LARGE_ASTEROID,
    SCORE_MEDIUM_ASTEROID,
    SCORE_SMALL_ASTEROID,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    SHIELD_DURATION_SECONDS,
    SHIELD_EXPIRE_TEXT_DURATION,
    SOUND_VOLUME_BLOCK,
    SOUND_VOLUME_PICKUP,
    SOUND_VOLUME_SHIELD_EXPIRE,
    WEAPON_COLOR_RAPID,
    WEAPON_COLOR_SINGLE,
    WEAPON_COLOR_SPREAD,
    WEAPON_RAPID,
    WEAPON_SINGLE,
    WEAPON_SPREAD,
)
from .logger import log_state, log_event
from .player import Player
from .asteroid import Asteroid, Explosion
from .asteroidfield import AsteroidField
from .powerup import PowerUp
from .bomb import Bomb
from .menu import Menu
from .shot import Shot


# Get the project root directory (two levels up from this file)
PROJECT_ROOT = Path(__file__).parent.parent.parent
ASSETS_DIR = PROJECT_ROOT / "assets"

# ============================================================================
# COMPLETE GAME LOOP - BIG PICTURE MAP
# ============================================================================
#
#                   +----------------------+
#                   |   Program starts     |
#                   +----------+-----------+
#                              |
#                              v
#                   +----------------------+
#                   | pygame.init()        |
#                   | sounds, screen, menu |
#                   +----------+-----------+
#                              |
#                              v
#                   +----------------------+
#                   |  Main menu loop      |
#                   |  PLAY / QUIT / etc.  |
#                   +----------+-----------+
#                              |
#                              v
#              +---------------------------------------+
#              |         MAIN GAME LOOP (60 FPS)       |
#              +---------------------------------------+
#                              |
#                              v
#        +---------------------------------------------------------+
#        | 1. Read events                                          |
#        |    - window close?                                      |
#        |    - pause/unpause?                                     |
#        |    - debug toggle?                                      |
#        +-----------------------------+---------------------------+
#                                      |
#                                      v
#        +---------------------------------------------------------+
#        | 2. Compute dt                                             |
#        |    dt = seconds since previous frame                      |
#        |    Example: 0.016 s at 60 FPS                             |
#        +-----------------------------+---------------------------+
#                                      |
#                                      v
#        +---------------------------------------------------------+
#        | 3. Draw background + HUD                                 |
#        |    score, lives, weapon, help text                       |
#        +-----------------------------+---------------------------+
#                                      |
#                                      v
#        +---------------------------------------------------------+
#        | 4. Update gameplay timers                                |
#        |    respawn, invulnerability, power-up spawn, messages    |
#        +-----------------------------+---------------------------+
#                                      |
#                                      v
#        +---------------------------------------------------------+
#        | 5. Update all sprites                                    |
#        |    player, asteroids, shots, bombs, explosions, etc.     |
#        +-----------------------------+---------------------------+
#                                      |
#                                      v
#        +---------------------------------------------------------+
#        | 6. Check collisions                                       |
#        |    player <-> powerups                                    |
#        |    player <-> asteroids                                   |
#        |    shots  <-> asteroids                                   |
#        |    bombs  <-> asteroids                                   |
#        +-----------------------------+---------------------------+
#                                      |
#                                      v
#        +---------------------------------------------------------+
#        | 7. Draw sprites + optional debug hitbox                  |
#        +-----------------------------+---------------------------+
#                                      |
#                                      v
#        +---------------------------------------------------------+
#        | 8. Log state + display.flip()                            |
#        |    Screen shows the fully built frame                    |
#        +-----------------------------+---------------------------+
#                                      |
#                                      v
#                         +----------------------+
#                         |  Loop repeats again  |
#                         +----------------------+
#
# IDEA TO REMEMBER:
# A game is not "draw once". It is a very fast cycle repeated many times
# per second. That repetition creates motion, input response, and animation.
# ============================================================================


def main():
    """Set up the whole game, then run the main loop forever.

    Big picture of this function:
    1. initialize pygame, sound, window, and menu
    2. create all sprite groups and game objects
    3. run the main loop:
       - read player input
       - update objects
       - check collisions
       - draw everything
       - show the next frame

    In most games, this kind of function is called the "game loop" or the
    "main loop". It repeats many times per second until the player quits.
    """
    print(f"Starting Asteroids with pygame version: {pygame.version.ver}")
    print(f"Screen width: {SCREEN_WIDTH} \nScreen height: {SCREEN_HEIGHT}")
    pygame.init()  # Initialize all Pygame modules
    pygame.mixer.init()  # Initialize sound system

    screen = pygame.display.set_mode(
        (SCREEN_WIDTH, SCREEN_HEIGHT)
    )  # Create game window
    pygame.display.set_caption("ASTEROIDS")  # Set window title
    clock = pygame.time.Clock()  # Used to control game speed (60 FPS)

    # SHOW MENU - The game waits here until the player chooses PLAY or QUIT.
    # This is a separate loop before the actual gameplay begins.
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

    # After leaving the menu, keep the chosen difficulty for the game session.
    difficulty = menu.difficulty
    print(f"Starting game with difficulty: {difficulty}")

    # AUDIO SETUP - Generate simple sound effects in code.
    # No external .wav files are needed because make_tone builds them for us.
    def make_tone(freq, duration=0.2, volume=0.5, sample_rate=44100, waveform="sine"):
        """Create a sound effect by generating audio waveform
        This creates real sound data that Pygame can play

        Parameters:
        - freq: frequency in Hz (higher = higher pitch)
        - duration: how long sound plays in seconds
        - volume: how loud (0.0 to 1.0)
        - waveform: "sine", "triangle", or "square" (different shapes = different tones)

        BIG IDEA:
        A sound file is just a long list of numbers.
        Each number says where the speaker cone should be at one instant.

        time -->

        sine wave:       /\      /\      /\
                        /  \    /  \    /  \
                       /    \  /    \  /    \
                      /      \/      \/      \

        square wave:   ____    ____    ____
                      |    |  |    |  |    |
                      |    |__|    |__|    |__

        triangle:       /\      /\      /\
                       /  \    /  \    /  \
                      /    \  /    \  /    \
                      \    /  \    /  \    /
                       \  /    \  /    \  /
                        \/      \/      \/

        MAIN FORMULA:
            phase = 2 * pi * frequency * time

        Why this formula?
        - time increases steadily
        - frequency tells us how many cycles we want per second
        - 2*pi converts "cycles" into radians for math.sin()
        """
        # Calculate total number of audio samples needed
        n_samples = int(sample_rate * duration)
        buf = bytearray()  # Store all audio samples here

        # Generate each audio sample
        for i in range(n_samples):
            t = i / sample_rate  # Current time in seconds
            # phase tells us where we are on the wave at this exact instant.
            # If freq is larger, phase grows faster, so the wave oscillates faster.
            phase = 2.0 * math.pi * freq * t

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

            # 32767 is the maximum positive value for signed 16-bit audio.
            # We scale the waveform value (-1 to +1) into that integer range.
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

    # Load background image (optional).
    # If the file is missing or unreadable, the game simply falls back to black.
    background = None
    try:
        bg_path = ASSETS_DIR / "images" / "backgrounds" / "5446991.jpg"
        if bg_path.exists():
            background = pygame.image.load(str(bg_path)).convert()
            background = pygame.transform.scale(
                background, (SCREEN_WIDTH, SCREEN_HEIGHT)
            )
    except Exception as e:
        print(f"Could not load background image: {e}")
        background = None

    # We reuse a clock object during gameplay to measure frame time.
    # dt will store "delta time": how many seconds passed since last frame.
    clock = pygame.time.Clock()
    dt = 0

    # Start player in the centre of the screen.
    x = SCREEN_WIDTH / 2
    y = SCREEN_HEIGHT / 2

    # GAME STATE VARIABLES
    # These are the numbers and flags that describe the current match.
    score = 0
    lives = PLAYER_LIVES  # How many mistakes the player can still survive
    invulnerable_timer = 0  # Short grace period after respawn
    respawn_timer = 0  # Delay before the ship becomes active again
    debug_draw_hitbox = False  # Dev helper toggled with the D key
    paused = False  # Stops gameplay updates when True
    pause_selected = 0  # Which pause-menu option is highlighted
    font = pygame.font.Font(None, 30)

    # SPRITE GROUPS
    # Each group is a collection of objects.
    # Groups let us update or draw many sprites with a single loop.
    updatable = pygame.sprite.Group()
    drawable = pygame.sprite.Group()
    asteroids = pygame.sprite.Group()
    shots = pygame.sprite.Group()
    powerups = pygame.sprite.Group()
    bombs = pygame.sprite.Group()

    # CONTAINER REGISTRATION
    # Each class stores the groups it should join automatically when created.
    # Example: creating a Shot instantly adds it to shots, updatable, drawable.
    Player.containers = (updatable, drawable)
    Asteroid.containers = (asteroids, updatable, drawable)
    AsteroidField.containers = updatable
    Shot.containers = (shots, updatable, drawable)
    Explosion.containers = (updatable, drawable)
    PowerUp.containers = (powerups, updatable, drawable)
    Bomb.containers = (bombs, updatable, drawable)

    # The asteroid field is a hidden spawner, not something the player sees.
    AsteroidField()

    # Create the player in the middle of the screen.
    player = Player(x, y)
    powerup_spawn_timer = 0.0  # Counts up until the next shield power-up appears
    shield_ready_timer = 0.0  # Short "Shield Ready!" message duration
    shield_expire_text_timer = 0.0  # Short "Shield Expired" message duration

    # MAIN GAME LOOP
    # This runs until the player closes the window or returns from the game.
    while True:
        # EVENT LOOP
        # Events are one-time actions such as key presses or window close.
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                # ESC toggles pause on/off.
                paused = not paused
                pause_selected = 0
            if event.type == pygame.KEYDOWN and event.key == pygame.K_d:
                # D shows the exact triangle hitbox for debugging or teaching.
                debug_draw_hitbox = not debug_draw_hitbox

            # Pause menu input is handled only while paused is True.
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
            # When paused, we skip all gameplay updates and only draw a menu.
            screen.fill("black")
            pause_title = pygame.font.Font(None, 80)
            title_text = pause_title.render("PAUSED", True, pygame.Color("yellow"))
            screen.blit(
                title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 100)
            )

            y_offset = 300
            pause_options = ["RESUME", "RETURN TO MENU"]
            for i, option in enumerate(pause_options):
                # Yellow means "the cursor is here right now".
                color = (
                    pygame.Color("yellow")
                    if i == pause_selected
                    else pygame.Color("white")
                )
                text = font.render(option, True, color)
                x = SCREEN_WIDTH // 2 - text.get_width() // 2
                screen.blit(text, (x, y_offset + i * 80))
                if i == pause_selected:
                    # Decorative arrows make the selected line easier to spot.
                    indicator = font.render(">", True, pygame.Color("yellow"))
                    screen.blit(indicator, (x - 60, y_offset + i * 80))
                    screen.blit(
                        indicator, (x + text.get_width() + 20, y_offset + i * 80)
                    )

            pygame.display.flip()
            clock.tick(60)
            continue

        # dt = delta time = seconds since the previous frame.
        # clock.tick(60) also limits the loop to about 60 FPS.
        dt = clock.tick(60) / 1000

        # Draw the background first so all sprites appear on top of it.
        if background:
            screen.blit(background, (0, 0))
        else:
            screen.fill("black")

        # HUD = Heads-Up Display.
        # This is the information layer drawn on top of the action.
        score_text = font.render(f"Score: {score}", True, pygame.Color("white"))
        screen.blit(score_text, (10, 10))

        lives_text = font.render(f"Lives: {lives}", True, pygame.Color("white"))
        screen.blit(lives_text, (10, 40))

        weapon_text = font.render(
            f"Weapon: {player.weapon}", True, pygame.Color("white")
        )
        screen.blit(weapon_text, (10, 70))

        # Small coloured dot that matches the current weapon mode.
        weapon_color = pygame.Color("white")
        if player.weapon == WEAPON_SINGLE:
            weapon_color = pygame.Color(*WEAPON_COLOR_SINGLE)
        elif player.weapon == WEAPON_SPREAD:
            weapon_color = pygame.Color(*WEAPON_COLOR_SPREAD)
        elif player.weapon == WEAPON_RAPID:
            weapon_color = pygame.Color(*WEAPON_COLOR_RAPID)

        pygame.draw.circle(screen, weapon_color, (200, 80), 6)

        # Only one of these two messages will usually appear at a time.
        # INVULNERABLE = player can be touched without taking damage.
        if invulnerable_timer > 0:
            invul_text = font.render("INVULNERABLE", True, pygame.Color("yellow"))
            screen.blit(invul_text, (10, 100))

        # RESPAWNING means the ship is temporarily absent before coming back.
        if respawn_timer > 0:
            respawn_text = font.render(
                f"RESPAWNING... {respawn_timer:.1f}s", True, pygame.Color("cyan")
            )
            screen.blit(respawn_text, (10, 100))

        # This temporary message appears right after a new shield spawns.
        if shield_ready_timer > 0:
            shield_ready_text = font.render("Shield Ready!", True, pygame.Color("lime"))
            screen.blit(shield_ready_text, (SCREEN_WIDTH // 2 - 80, 30))
            shield_ready_timer = max(0, shield_ready_timer - dt)

        # A single line reminder of the controls is useful in arcade-style games
        # because the player spends most of the time looking at action, not menus.
        help_text = font.render(
            "Arrows=Move, 1=Single 2=Spread 3=Rapid, Space=Fire, B=Bomb, ESC=Pause",
            True,
            pygame.Color("lightgray"),
        )
        screen.blit(help_text, (10, SCREEN_HEIGHT - 30))

        # Draw every visible object.
        # The player is skipped while inactive during respawn.
        for object in drawable:
            if isinstance(object, Player) and not player.active:
                continue
            object.draw(screen)

        # Debug helper: draw the player's true collision triangle.
        if debug_draw_hitbox and player.active:
            pygame.draw.polygon(
                screen, pygame.Color("yellow"), player.hit_triangle(), 1
            )

        # Temporary warning text shown for a short time after shield expiry.
        if shield_expire_text_timer > 0:
            expired_text = font.render("Shield Expired", True, pygame.Color("red"))
            screen.blit(expired_text, (SCREEN_WIDTH // 2 - 90, 60))

        # ====== RESPAWN TIMER LOGIC ======
        # When player dies, they're invisible for 1 second before appearing
        # This prevents them from instantly dying again
        if respawn_timer > 0:
            respawn_timer = max(0, respawn_timer - dt)  # Count down timer
            player.active = False  # Make player invisible/inactive
            if respawn_timer == 0:  # When timer runs out:
                player.active = True  # Player becomes visible again
                invulnerable_timer = (
                    PLAYER_RESPAWN_INVULNERABLE_SECONDS  # Grant invulnerability
                )

        # ====== POWER-UP SPAWNING ======
        # This timer slowly counts upward during gameplay.
        # Once it reaches the spawn threshold, a new shield appears and the
        # timer is reset back to zero to begin the next cycle.
        powerup_spawn_timer += dt  # Add elapsed time since last frame
        if powerup_spawn_timer >= POWERUP_SPAWN_RATE_SECONDS:
            powerup_spawn_timer = 0  # Reset timer
            # Pick random position on screen (not too close to edges)
            x = random.uniform(100, SCREEN_WIDTH - 100)
            y = random.uniform(100, SCREEN_HEIGHT - 100)
            PowerUp(x, y)  # Create the power-up
            shield_ready_timer = 2.0

        # ====== UPDATE ALL GAME OBJECTS ======
        # Every object handles its own movement and timers inside its update().
        # This is a classic object-oriented design: each class is responsible
        # for its own behaviour.
        for object in updatable:
            object.update(dt)  # dt = how much time passed since last frame

        # ====== COLLISION: PLAYER CATCHES POWER-UP ======
        # We copy the group to a list before iterating because removing sprites
        # while looping directly over a group can be awkward and error-prone.
        for powerup in list(powerups):
            if player.collides_with(powerup):
                powerup.kill()  # Remove power-up from game
                player.shield_active = True  # Activate player's shield
                player.shield_timer = SHIELD_DURATION_SECONDS  # Start shield countdown
                player.shield_expired = False
                pickup_sound.play()  # Play success sound
                log_event("shield_picked", shield_timer=player.shield_timer)

        # ====== SHIELD EXPIRATION EFFECT ======
        # player.update() only sets a flag when the shield ends.
        # main.py reacts to that flag by playing sound and showing text.
        if hasattr(player, "shield_expired") and player.shield_expired:
            shield_expire_sound.play()  # Play expiration sound
            shield_expire_text_timer = SHIELD_EXPIRE_TEXT_DURATION  # Show message
            player.shield_expired = False

        # ====== COLLISION: PLAYER VS ASTEROIDS ======
        # We skip damage checks while the player is protected by respawn grace.
        if respawn_timer <= 0 and invulnerable_timer <= 0:
            for asteroid in list(asteroids):
                if player.collides_with(asteroid):
                    # CASE 1: Player has shield
                    if player.shield_active:
                        player.shield_active = False  # Deactivate shield
                        player.shield_timer = 0
                        block_sound.play()  # Play block sound
                        log_event(
                            "shield_block",
                            asteroid_pos=[
                                round(asteroid.position.x, 2),
                                round(asteroid.position.y, 2),
                            ],
                        )
                        asteroid.split()  # Destroy the asteroid
                        continue  # Skip the damage code below

                    # CASE 2: Player doesn't have shield - TAKE DAMAGE
                    lives -= 1  # Decrease lives by 1
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

                    # Check if the player has no lives remaining.
                    if lives <= 0:
                        # Save high score if the player beat their personal best
                        is_new_high = score > menu.high_score
                        if is_new_high:
                            menu.save_high_score(score)

                        # ── Show Game Over screen ─────────────────────────────
                        # Player chooses TRY AGAIN or EXIT with arrow keys + Enter
                        go_selected = 0  # 0 = "TRY AGAIN", 1 = "EXIT"
                        chose_restart = False
                        # This is a small temporary loop dedicated only to the
                        # Game Over screen. The normal gameplay loop is paused
                        # until the player chooses what to do next.
                        while True:
                            result = menu.handle_game_over_input(go_selected)
                            if result == "restart":
                                chose_restart = True
                                break
                            elif result == "quit":
                                return  # Close game immediately
                            elif isinstance(result, tuple) and result[0] == "move":
                                go_selected = result[1]  # Move cursor up/down
                            menu.draw_game_over(screen, score, is_new_high, go_selected)
                            pygame.display.flip()
                            clock.tick(60)

                        if not chose_restart:
                            return  # Player chose EXIT

                        # ── TRY AGAIN: reset all game state in place ──────────
                        # Instead of restarting Python, we simply rebuild the
                        # gameplay state so the same program keeps running.
                        score = 0
                        lives = PLAYER_LIVES
                        invulnerable_timer = 0
                        respawn_timer = 0
                        paused = False
                        pause_selected = 0
                        powerup_spawn_timer = 0.0
                        shield_ready_timer = 0.0
                        shield_expire_text_timer = 0.0

                        # Remove every old sprite from the game.
                        # kill() removes the sprite from every group it belongs to.
                        for s in list(updatable):
                            s.kill()
                        updatable.empty()
                        drawable.empty()
                        asteroids.empty()
                        shots.empty()
                        powerups.empty()
                        bombs.empty()

                        # Recreate the spawner and the player.
                        # Because containers are already configured above,
                        # these new objects register themselves automatically.
                        AsteroidField()
                        player = Player(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
                        break  # exit the 'for asteroid' loop → game resumes next frame

                    # Respawn player in the centre and reset movement.
                    # This gives the player a clean restart after taking damage.
                    player.position = pygame.Vector2(
                        SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2
                    )
                    player.rotation = 0
                    player.velocity = pygame.Vector2(0, 0)
                    invulnerable_timer = PLAYER_RESPAWN_INVULNERABLE_SECONDS

                    # Remove active bullets so the player does not respawn into
                    # a chaotic situation created by old shots still flying.
                    for shot in list(shots):
                        shot.kill()
                    break

        # Timers naturally count down to zero every frame.
        if invulnerable_timer > 0:
            invulnerable_timer = max(0, invulnerable_timer - dt)

        if shield_expire_text_timer > 0:
            shield_expire_text_timer = max(0, shield_expire_text_timer - dt)

        # ====== COLLISION: SHOTS (BULLETS) VS ASTEROIDS ======
        # This is a double loop: every asteroid is checked against every shot.
        # That is simple to understand, even if it is not the fastest method.
        for asteroid in list(asteroids):
            for shot in list(shots):
                if asteroid.collides_with(shot):
                    # Determine points based on asteroid size
                    # (Smaller asteroids = more points as reward for difficulty)
                    if asteroid.radius <= ASTEROID_MIN_RADIUS:
                        # Small asteroid = 100 points (hardest to hit)
                        points = SCORE_SMALL_ASTEROID
                    elif asteroid.radius <= ASTEROID_MIN_RADIUS * 2:
                        # Medium asteroid = 50 points (medium difficulty)
                        points = SCORE_MEDIUM_ASTEROID
                    else:
                        # Large asteroid = 20 points (easiest to hit)
                        points = SCORE_LARGE_ASTEROID

                    score += points  # Add points to player's score

                    log_event(
                        "asteroid_shot",
                        points=points,
                        score=score,
                        asteroid_radius=asteroid.radius,
                    )

                    # Add explosion effect (visual feedback)
                    Explosion(asteroid.position.x, asteroid.position.y)

                    shot.kill()  # Remove the bullet from game
                    asteroid.split()  # Split asteroid into smaller pieces (or remove if smallest)
                    break  # One bullet should only destroy one asteroid once

        # ====== COLLISION: BOMB EXPLOSIONS VS ASTEROIDS ======
        # Bomb.update() only marks the bomb as exploded.
        # main.py handles the area damage because it has access to the asteroid group.
        for bomb in list(bombs):
            if bomb.exploded:
                # Create an expanding visual effect at the bomb position.
                Explosion(bomb.position.x, bomb.position.y)
                log_event(
                    "bomb_exploded",
                    bomb_pos=[round(bomb.position.x, 2), round(bomb.position.y, 2)],
                )

                # Damage all asteroids inside the bomb damage radius.
                # This is an area-of-effect weapon: one bomb can affect many
                # asteroids at the same time.
                for asteroid in list(asteroids):
                    distance = bomb.position.distance_to(asteroid.position)
                    if distance <= BOMB_DAMAGE_RADIUS:
                        asteroid.split()

        # Record a lightweight debug snapshot for the JSONL log file.
        log_state()

        # flip() makes everything drawn this frame appear on screen at once.
        pygame.display.flip()


if __name__ == "__main__":
    main()
