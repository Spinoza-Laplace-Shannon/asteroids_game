import pygame
import json
from pathlib import Path
from .constants import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    DIFFICULTIES,
    DIFFICULTY_NORMAL,
    SOUND_VOLUME_MENU_NAV,
)
import math


# Path to data directory for saving high scores
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
HIGH_SCORE_FILE = DATA_DIR / "high_score.json"


# ============================================================================
# The Menu class handles everything the player sees BEFORE and AFTER the game:
# the main menu, settings, tutorial, and game-over screen.
#
# STATE MACHINE CONCEPT:
# A "state machine" is a system that can be in exactly ONE state at a time.
# The menu switches between states depending on what the player does:
#
#   ┌──────────────────────────────────────────────────────┐
#   │  "main"  ──PLAY──▶  (starts the game)               │
#   │     │    ──TUTORIAL─▶  "tutorial"  ──ESC──▶  "main" │
#   │     │    ──SETTINGS─▶  "settings"  ──ESC──▶  "main" │
#   │     └────QUIT──▶  (closes the game)                 │
#   └──────────────────────────────────────────────────────┘
#
# Only one screen is drawn at a time based on self.state.
#
# KEYBOARD NAVIGATION MAP:
#
#   MAIN MENU
#   +----------------------+
#   |  PLAY         <- 0   |
#   |  TUTORIAL     <- 1   |
#   |  SETTINGS     <- 2   |
#   |  QUIT         <- 3   |
#   +----------------------+
#        ^           |
#        |           |
#        +-- UP/DOWN-+
#
#   ENTER / SPACE -> choose current line
#   ESC           -> go back from sub-screens
#
# The cursor never gets "stuck" at the top or bottom because modulo (%)
# makes the selection wrap around.
# ============================================================================
class Menu:
    def __init__(self):
        """Set up fonts, initial selections, and load saved high score.

        This runs ONCE when Menu() is created at game startup.
        Think of __init__ as the "constructor" – it builds the object.
        """
        # ── FONTS ───────────────────────────────────────────────────────────
        # pygame.font.Font(None, size) creates a font using the system default
        # The number is the SIZE in pixels (bigger = larger text on screen)
        # We have three sizes for hierarchy: title > subtitle > body text
        self.font_large = pygame.font.Font(None, 60)  # Big headings (e.g. "ASTEROIDS")
        self.font_medium = pygame.font.Font(None, 40)  # Menu options (e.g. "PLAY")
        self.font_small = pygame.font.Font(None, 30)  # Small labels / hints

        # ── MENU SELECTION ──────────────────────────────────────────────────
        # self.selected tracks WHICH option the yellow cursor is on
        # 0 = first option, 1 = second option, etc.
        self.selected = 0

        # The list of options shown in the main menu
        # The ORDER matters: index 0 → PLAY, index 1 → TUTORIAL, etc.
        self.options = ["PLAY", "TUTORIAL", "SETTINGS", "QUIT"]

        # ── STATE MACHINE ───────────────────────────────────────────────────
        # self.state controls WHICH screen is currently visible
        # Starts at "main" (the main menu screen)
        self.state = "main"  # possible values: 'main', 'settings', 'tutorial'

        # ── DIFFICULTY ──────────────────────────────────────────────────────
        # Default difficulty (usually "Normal")
        self.difficulty = DIFFICULTY_NORMAL
        self.difficulty_selected = 1  # Cursor position inside the difficulty list

        # ── PERSISTENT DATA ─────────────────────────────────────────────────
        # Load the previously saved high score from disk (returns 0 if no file)
        self.high_score = self.load_high_score()

        # ── SOUND ───────────────────────────────────────────────────────────
        # Generate a tiny beep sound for cursor movement (created in code, no file needed)
        self.menu_nav_sound = self.create_menu_sound()

    def create_menu_sound(self):
        """Generate a short beep sound entirely in code (no audio file needed).

        HOW DIGITAL AUDIO WORKS:
        ========================
        Sound is a pressure wave travelling through air.
        Speakers reproduce sound by vibrating rapidly back and forth.
        A computer controls that vibration by sending a stream of NUMBERS
        called "samples". Each sample tells the speaker how far to move.

        A SINE WAVE creates the smoothest, purest tone:

            amplitude
              1.0 ┤    ╭───╮           ╭───╮
                  │  ╭╯   ╰╮         ╭╯   ╰╮
              0.0 ┼──╯     ╰╮       ╭╯     ╰╮──▶ time
                  │         ╰╮   ╭──╯
             -1.0 ┤          ╰───╯

        The formula: sample = sin(2π × frequency × time)
        - frequency = how many complete waves per second (Hz)
        - 1000 Hz = 1000 waves/sec → a high-pitched beep
        - 440 Hz = concert A note

        sample_rate = 44100 means we send 44 100 numbers per second
        to the speaker (CD quality standard).
        """
        try:
            sample_rate = 44100  # Samples per second (CD quality)
            freq = 1000  # Frequency in Hz (1000 Hz = high beep)
            duration = 0.1  # Length of beep: 0.1 seconds
            volume = SOUND_VOLUME_MENU_NAV  # Loudness (0.0 to 1.0)

            # Total samples = rate × duration
            # EXAMPLE: 44100 × 0.1 = 4410 samples for a 0.1s beep
            n_samples = int(sample_rate * duration)
            buf = bytearray()  # Raw byte buffer that will hold all sample data

            for i in range(n_samples):
                # t = current time in seconds
                # EXAMPLE: sample 2205 → t = 2205/44100 = 0.05 seconds
                t = i / sample_rate

                # Sine wave formula (value swings between -1.0 and +1.0)
                # 2π × freq × t creates the right number of cycles per second
                raw = math.sin(2.0 * math.pi * freq * t)

                # Scale from (-1.0 … 1.0) to an integer that fits in 16 bits
                # 16-bit audio range: -32768 to 32767
                # volume shrinks the range so it's not at full blast
                sample = int(volume * 32767.0 * raw)

                # Pack the integer into TWO bytes (little-endian 16-bit)
                # & 0xFF keeps only the lowest 8 bits (the "ones" byte)
                # >> 8 shifts right by 8 bits to get the "tens" byte
                buf.extend(bytes([sample & 0xFF, (sample >> 8) & 0xFF]))

            # Hand the raw byte buffer to Pygame so it can play it
            sound = pygame.mixer.Sound(buffer=buf)
            return sound
        except Exception:
            # If anything goes wrong (e.g. audio system not available), just skip sound
            return None

    def load_high_score(self):
        """Load the best-ever score from a JSON file on disk.

        WHY A FILE? Variables in Python disappear when the program closes.
        To remember data between sessions we write it to a FILE on disk.

        JSON FORMAT (what the file looks like inside):
            {"score": 1250}
        JSON is just plain text structured as key-value pairs.
        Python's json module converts between JSON text ↔ Python dicts.

        SAFE PATTERN: We wrap everything in try/except so a missing file,
        corrupted data, or permission error never crashes the game.
        """
        try:
            # HIGH_SCORE_FILE is a pathlib.Path object pointing to data/high_score.json
            # .exists() returns True only if the file is actually there
            if HIGH_SCORE_FILE.exists():
                with open(HIGH_SCORE_FILE, "r") as f:  # "r" = read mode (text)
                    data = json.load(f)  # Parse JSON text → Python dict
                    # .get("score", 0) reads the "score" key
                    # If the key doesn't exist, return 0 as a safe default
                    return data.get("score", 0)
        except Exception:
            pass  # Something went wrong → act as if no high score exists
        return 0  # Default: no high score yet

    def save_high_score(self, score):
        """Write the new best score to the JSON file on disk.

        This is called from main.py only when the player beats their record.
        We also update self.high_score so the Game Over screen shows the
        new best immediately without needing to reload from disk.
        """
        try:
            # Create the data/ folder automatically if it doesn't exist yet
            # parents=True  → also create parent folders if needed
            # exist_ok=True → don't raise an error if folder already exists
            DATA_DIR.mkdir(parents=True, exist_ok=True)

            with open(HIGH_SCORE_FILE, "w") as f:  # "w" = write mode (overwrites)
                json.dump({"score": score}, f)  # Convert dict → JSON text and write

            # Update the in-memory value so the UI reflects the new record right away
            self.high_score = score
        except Exception:
            pass  # If saving fails (e.g. read-only filesystem), silently ignore

    def handle_input(self):
        """Process keyboard/mouse events while the menu is on screen.

        EVENT-DRIVEN INPUT:
        ===================
        In Pygame, the OS collects all keyboard/mouse actions into an "event queue".
        pygame.event.get() empties that queue and gives us a list of events.
        We loop over the list and react to whichever events we care about.

        WHY A LOOP? Multiple events can happen between two frames
        (e.g. player presses two keys very quickly). The loop processes all of them.

        RETURN VALUES (tells the caller what happened):
        - "play"  → player pressed Enter on PLAY → start the game
        - "quit"  → player closed the window or pressed QUIT
        - None    → nothing significant happened this frame

                NAVIGATION DIAGRAM:

                        UP key              DOWN key
                             ^                   |
                             |                   v

                    [ PLAY ]
                    [ TUTORIAL ]
                    [ SETTINGS ]
                    [ QUIT ]

                With wrap-around behaviour:
                - pressing UP on the first item jumps to the last item
                - pressing DOWN on the last item jumps to the first item

                That makes menu navigation feel continuous instead of blocked.
        """
        # Drain the event queue – process every pending input this frame
        for event in pygame.event.get():
            # ── Player closes the window (clicks the ✕ button) ──────────────
            if event.type == pygame.QUIT:
                return "quit"

            # ── A key was just pressed (not held – only the initial press) ──
            if event.type == pygame.KEYDOWN:
                # ── UP ARROW: move cursor one option higher ─────────────────
                if event.key == pygame.K_UP:
                    if self.state == "main":
                        # Modulo (%) creates "wrap-around" behaviour
                        # EXAMPLE with 4 options: (0 - 1) % 4 = -1 % 4 = 3
                        # So pressing UP on the first item jumps to the LAST item
                        self.selected = (self.selected - 1) % len(self.options)
                    else:
                        # Same wrap-around logic for the difficulty list
                        self.difficulty_selected = (self.difficulty_selected - 1) % len(
                            DIFFICULTIES
                        )
                    if self.menu_nav_sound:
                        self.menu_nav_sound.play()  # Short beep feedback

                # ── DOWN ARROW: move cursor one option lower ─────────────────
                elif event.key == pygame.K_DOWN:
                    if self.state == "main":
                        # (last_index + 1) % total wraps back to 0 (the first item)
                        self.selected = (self.selected + 1) % len(self.options)
                    else:
                        self.difficulty_selected = (self.difficulty_selected + 1) % len(
                            DIFFICULTIES
                        )
                    if self.menu_nav_sound:
                        self.menu_nav_sound.play()

                # ── ENTER or SPACE: confirm the highlighted option ───────────
                elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    if self.state == "main":
                        # self.selected tells us WHICH option the cursor is on
                        # (matches the order in self.options)
                        if self.selected == 0:  # "PLAY"
                            return "play"  # Signal main.py to start the game
                        elif self.selected == 1:  # "TUTORIAL"
                            self.state = "tutorial"  # Switch to tutorial screen
                        elif self.selected == 2:  # "SETTINGS"
                            self.state = "settings"
                            self.selected = 0
                            # Pre-select the difficulty that's already active
                            self.difficulty_selected = DIFFICULTIES.index(
                                self.difficulty
                            )
                        elif self.selected == 3:  # "QUIT"
                            return "quit"

                    elif self.state == "settings":
                        # Player confirmed a difficulty → save it and return to main
                        if self.difficulty_selected < len(DIFFICULTIES):
                            self.difficulty = DIFFICULTIES[self.difficulty_selected]
                        self.state = "main"
                        self.selected = (
                            2  # Put cursor back on "SETTINGS" for convenience
                        )

                # ── ESCAPE: go back to main menu from any sub-screen ─────────
                elif event.key == pygame.K_ESCAPE:
                    if self.state in ("settings", "tutorial"):
                        self.state = "main"
                        self.selected = 1  # Reset cursor to a sensible position

        # Nothing important happened this frame
        return None

    def draw(self, screen):
        """Draw the correct sub-screen based on the current state.

        This is the DISPATCHER: it looks at self.state and calls the
        matching draw method.  Only one screen is drawn per frame.

        Clearing the screen first (fill black) prevents the previous
        frame's image from "bleeding through" onto the new frame.
        """
        screen.fill("black")  # Erase everything from the previous frame
        if self.state == "main":
            self.draw_main(screen)  # Draw main menu (PLAY / TUTORIAL / …)
        elif self.state == "settings":
            self.draw_settings(screen)  # Draw difficulty picker
        elif self.state == "tutorial":
            self.draw_tutorial(screen)  # Draw controls / tips page

    def draw_main(self, screen):
        """Draw the main menu: title, high score, option list, and hint.

        CENTERING FORMULA:
        To center any piece of text horizontally:
            x = (screen_width / 2) - (text_width / 2)
        This places the LEFT edge of the text so its center aligns with
        the center of the screen.

        EXAMPLE: screen=800px wide, text=200px wide
            x = 800//2 - 200//2 = 400 - 100 = 300
            Text spans pixels 300–500 → centered on pixel 400 ✓

        SCREEN LAYOUT:

            +--------------------------------------+
            |              ASTEROIDS               |
            |            Best Score: 1250          |
            |                                      |
            |              > PLAY <                |
            |                TUTORIAL              |
            |                SETTINGS              |
            |                QUIT                  |
            |                                      |
            |  Use UP/DOWN to select, ENTER...     |
            +--------------------------------------+
        """
        # ── TITLE ───────────────────────────────────────────────────────────
        # font.render(text, antialias, color) → creates a Surface (image of text)
        # antialias=True smooths the edges of letters
        title = self.font_large.render("ASTEROIDS", True, pygame.Color("white"))
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 50))

        # ── HIGH SCORE ──────────────────────────────────────────────────────
        # f-string: f"Best Score: {self.high_score}" inserts the value of
        # self.high_score directly into the string at runtime
        hs_text = self.font_small.render(
            f"Best Score: {self.high_score}", True, pygame.Color("cyan")
        )
        screen.blit(hs_text, (SCREEN_WIDTH // 2 - hs_text.get_width() // 2, 130))

        # ── OPTION LIST ─────────────────────────────────────────────────────
        # enumerate(list) gives us both the index i AND the value option
        # EXAMPLE: enumerate(["PLAY","QUIT"]) → (0,"PLAY"), (1,"QUIT")
        y_offset = 250  # Vertical starting position for the first option
        for i, option in enumerate(self.options):
            # Highlight the currently selected option in yellow
            # All others stay white
            color = (
                pygame.Color("yellow") if i == self.selected else pygame.Color("white")
            )
            text = self.font_medium.render(option, True, color)

            # Center this option horizontally
            x = SCREEN_WIDTH // 2 - text.get_width() // 2

            # Stack options 80 pixels apart vertically
            # EXAMPLE: option 0 → y=250, option 1 → y=330, option 2 → y=410
            screen.blit(text, (x, y_offset + i * 80))

            # Draw " > OPTION < " arrows around the selected option
            if i == self.selected:
                indicator = self.font_medium.render(">", True, pygame.Color("yellow"))
                screen.blit(indicator, (x - 60, y_offset + i * 80))  # Left arrow
                screen.blit(
                    indicator, (x + text.get_width() + 20, y_offset + i * 80)
                )  # Right arrow

        # ── HINT AT BOTTOM ──────────────────────────────────────────────────
        controls = self.font_small.render(
            "Use UP/DOWN to select, ENTER to proceed", True, pygame.Color("lightgray")
        )
        screen.blit(
            controls,
            (SCREEN_WIDTH // 2 - controls.get_width() // 2, SCREEN_HEIGHT - 50),
        )

    def draw_settings(self, screen):
        """Draw the difficulty selection screen.

        The idea is almost the same as the main menu:
        - a title at the top
        - a list of choices in the middle
        - one highlighted choice showing the current cursor position
        - a small instruction line at the bottom

        SCREEN LAYOUT:

            +--------------------------------------+
            |               SETTINGS               |
            |                                      |
            |             DIFFICULTY:              |
            |                                      |
            |               > EASY                 |
            |                 NORMAL               |
            |                 HARD                 |
            |                                      |
            |      ENTER to confirm, ESC ...       |
            +--------------------------------------+
        """
        # Large title so the player instantly knows which screen they are on.
        title = self.font_large.render("SETTINGS", True, pygame.Color("white"))
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 80))

        # Label above the list to explain what is being changed.
        difficulty_label = self.font_medium.render(
            "DIFFICULTY:", True, pygame.Color("white")
        )
        screen.blit(
            difficulty_label,
            (SCREEN_WIDTH // 2 - difficulty_label.get_width() // 2, 200),
        )

        # Draw each difficulty option one under the other.
        y_offset = 280
        for i, diff in enumerate(DIFFICULTIES):
            color = (
                pygame.Color("yellow")
                if i == self.difficulty_selected
                else pygame.Color("white")
            )
            text = self.font_small.render(diff, True, color)
            x = SCREEN_WIDTH // 2 - text.get_width() // 2
            screen.blit(text, (x, y_offset + i * 60))

            # Arrow marks the currently selected difficulty.
            if i == self.difficulty_selected:
                indicator = self.font_small.render(">", True, pygame.Color("yellow"))
                screen.blit(indicator, (x - 50, y_offset + i * 60))

        # Reminder controls: confirm with Enter, leave with Escape.
        back_text = self.font_small.render(
            "ENTER to confirm, ESC to cancel", True, pygame.Color("lightgray")
        )
        screen.blit(
            back_text,
            (SCREEN_WIDTH // 2 - back_text.get_width() // 2, SCREEN_HEIGHT - 50),
        )

    def draw_tutorial(self, screen):
        """Draw a simple text-based tutorial page.

        Instead of teaching through animation, this screen uses a list of short
        lines. Some lines are section titles like OBJECTIVE: or CONTROLS:,
        while others are ordinary explanations.

        PAGE STRUCTURE:

            TUTORIAL
            --------
            OBJECTIVE:
            CONTROLS:
            WEAPONS:
            POWER-UPS:
            TIPS:

        This is similar to notes on a classroom handout:
        short sections, short lines, easy to scan quickly.
        """
        # Title at the top of the screen.
        title = self.font_large.render("TUTORIAL", True, pygame.Color("white"))
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 40))

        # Each line is drawn one after another vertically.
        # Empty strings act as visual spacing between sections.
        tutorial_lines = [
            "OBJECTIVE:",
            "Destroy all asteroids to survive. Avoid collisions.",
            "",
            "CONTROLS:",
            "LEFT/RIGHT arrows - Rotate ship",
            "UP arrow - Thrust forward",
            "Space - Fire primary weapon",
            "1/2/3 - Switch weapons (Single/Spread/Rapid)",
            "B - Drop a bomb",
            "",
            "WEAPONS:",
            "Single: One bullet straight ahead",
            "Spread: Three bullets in a cone",
            "Rapid: Fast firing projectiles",
            "",
            "POWER-UPS:",
            "Green Shield - Protects you from damage",
            "Bomb - Explodes asteroids nearby",
            "",
            "TIPS:",
            "Use screen wrap to escape danger",
            "Destroy big asteroids for more points",
        ]

        y_offset = 120
        for line in tutorial_lines:
            # Blank line = just move downward a bit without drawing text.
            if line == "":
                y_offset += 15
                continue

            # Section headers are drawn in cyan so they stand out from the body text.
            if line.endswith(":") and line.isupper():
                color = pygame.Color("cyan")
                font = self.font_small
            else:
                color = pygame.Color("lightgray")
                font = self.font_small

            text = font.render(line, True, color)
            screen.blit(text, (50, y_offset))
            y_offset += 25

        # Final reminder so the player knows how to go back.
        back_text = self.font_small.render(
            "ESC to return to menu", True, pygame.Color("lightgray")
        )
        screen.blit(
            back_text,
            (SCREEN_WIDTH // 2 - back_text.get_width() // 2, SCREEN_HEIGHT - 50),
        )

    # -------------------------------------------------------------------------
    # GAME OVER SCREEN
    # -------------------------------------------------------------------------

    def handle_game_over_input(self, selected):
        """Handle keyboard input on the Game Over screen.

        DESIGN PATTERN – RETURNING DATA INSTEAD OF ACTING:
        ====================================================
        This method does NOT restart the game itself. Instead it returns
        a value that tells main.py what the player decided.
        main.py then acts on that decision.
        This keeps each piece of code responsible for ONE thing:
        - menu.py  → what the player wants
        - main.py  → what actually happens in the game

        Return values:
        - "restart"           → player confirmed TRY AGAIN
        - "quit"              → player confirmed EXIT (or closed window)
        - ("move", new_idx)   → player moved the cursor (pass new index back)
        - None                → nothing relevant happened this frame

        NAVIGATION MAP:

            selected = 0  -> TRY AGAIN
            selected = 1  -> EXIT

                 UP or DOWN
               flips 0 <-> 1

        Because there are only TWO choices, both arrow keys simply toggle.
        That is why the code can use:

            1 - selected

        since:
            1 - 0 = 1
            1 - 1 = 0
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_UP, pygame.K_DOWN):
                    # Both arrows toggle the cursor: 0 ↔ 1
                    # "1 - selected" flips between 0 and 1:
                    #   1 - 0 = 1 (was on TRY AGAIN, now on EXIT)
                    #   1 - 1 = 0 (was on EXIT, now on TRY AGAIN)
                    if self.menu_nav_sound:
                        self.menu_nav_sound.play()
                    return ("move", 1 - selected)
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    # selected == 0 → TRY AGAIN, anything else → EXIT
                    return "restart" if selected == 0 else "quit"
                if event.key == pygame.K_ESCAPE:
                    return "quit"  # Escape acts the same as EXIT
        return None

    def draw_game_over(self, screen, score, is_new_high, selected):
        """Draw the Game Over screen after the player runs out of lives.

        PARAMETERS:
        - screen     : the Pygame display surface (the visible window)
        - score      : the final score this session
        - is_new_high: True if the player just beat their previous record
        - selected   : which option has the cursor (0=TRY AGAIN, 1=EXIT)

        LAYOUT (top to bottom):
        ┌─────────────────────────────────────────────┐
        │           GAME OVER!          ← big red title      │
        │           Score: 1250         ← white, centered     │
        │        NEW HIGH SCORE!        ← cyan (if record)    │
        │           Best: 1250          ← lightgray           │
        │        > TRY AGAIN            ← yellow if selected  │
        │          EXIT                 ← white or yellow     │
        │ UP/DOWN to choose…            ← hint at bottom      │
        └─────────────────────────────────────────────┘

                SELECTION EXAMPLE:

                        if selected == 0:
                                > TRY AGAIN <
                                    EXIT

                        if selected == 1:
                                    TRY AGAIN
                                > EXIT <

                The yellow arrows act like a visual cursor.
        """
        # Blank out the screen (must do this every frame or old image shows through)
        screen.fill("black")

        # ── TITLE ──────────────────────────────────────────────────────────
        # Font size 90 = very large, immediately draws the eye
        # Red color signals danger / failure (color psychology)
        font_title = pygame.font.Font(None, 90)
        title = font_title.render("GAME OVER!", True, pygame.Color("red"))
        # Center formula: x = half_screen_width - half_text_width
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 80))

        # ── CURRENT SCORE ──────────────────────────────────────────────────
        # f-string inserts the value of `score` into the text at runtime
        score_text = self.font_medium.render(
            f"Score: {score}", True, pygame.Color("white")
        )
        screen.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, 200))

        # ── NEW HIGH SCORE BADGE (only when player breaks the record) ──────
        # y_badge tracks the vertical position so content below shifts down
        # when the badge is visible (to avoid overlapping text)
        y_badge = 260
        if is_new_high:
            # Cyan color = positive highlight (different from white body text)
            badge = self.font_medium.render(
                "NEW HIGH SCORE!", True, pygame.Color("cyan")
            )
            screen.blit(badge, (SCREEN_WIDTH // 2 - badge.get_width() // 2, y_badge))
            y_badge += 50  # Push "Best:" line further down to make room

        # ── ALL-TIME BEST ──────────────────────────────────────────────────
        # If is_new_high is True, self.high_score was already updated by
        # menu.save_high_score() before this method was called,
        # so it already shows the new record value.
        hs_text = self.font_small.render(
            f"Best: {self.high_score}", True, pygame.Color("lightgray")
        )
        screen.blit(hs_text, (SCREEN_WIDTH // 2 - hs_text.get_width() // 2, y_badge))

        # ── MENU OPTIONS (TRY AGAIN / EXIT) ───────────────────────────────
        # Same yellow-highlight + arrow pattern as the main menu
        # enumerate() gives both index i and the text value option
        options = ["TRY AGAIN", "EXIT"]
        y_options = 380
        for i, option in enumerate(options):
            # Yellow = cursor is here ; White = not selected
            color = pygame.Color("yellow") if i == selected else pygame.Color("white")
            text = self.font_medium.render(option, True, color)
            x = SCREEN_WIDTH // 2 - text.get_width() // 2
            screen.blit(text, (x, y_options + i * 70))  # 70 px gap between options
            # Draw "> OPTION <" arrows only around the selected option
            if i == selected:
                arrow = self.font_medium.render(">", True, pygame.Color("yellow"))
                screen.blit(arrow, (x - 50, y_options + i * 70))  # Left
                screen.blit(
                    arrow, (x + text.get_width() + 14, y_options + i * 70)
                )  # Right

        # ── HINT ───────────────────────────────────────────────────────────
        # Placed at the very bottom (SCREEN_HEIGHT - 50)
        # "gray" keeps it subtle so it doesn't compete with the main content
        hint = self.font_small.render(
            "UP/DOWN to choose, ENTER to confirm", True, pygame.Color("gray")
        )
        screen.blit(
            hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, SCREEN_HEIGHT - 50)
        )
