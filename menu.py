import pygame
import os
import json
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, DIFFICULTIES, DIFFICULTY_NORMAL, SOUND_VOLUME_MENU_NAV
import math


class Menu:
    def __init__(self):
        self.font_large = pygame.font.Font(None, 60)
        self.font_medium = pygame.font.Font(None, 40)
        self.font_small = pygame.font.Font(None, 30)
        self.selected = 0
        self.options = ["PLAY", "TUTORIAL", "SETTINGS", "QUIT"]
        self.state = "main"  # 'main', 'settings', 'tutorial', 'game'
        self.difficulty = DIFFICULTY_NORMAL
        self.difficulty_selected = 1  # index in DIFFICULTIES
        self.high_score = self.load_high_score()
        self.menu_nav_sound = self.create_menu_sound()

    def create_menu_sound(self):
        """Create a simple beep sound for menu navigation"""
        try:
            sample_rate = 44100
            freq = 1000
            duration = 0.1
            volume = SOUND_VOLUME_MENU_NAV
            n_samples = int(sample_rate * duration)
            buf = bytearray()
            for i in range(n_samples):
                sample = int(volume * 32767.0 * math.sin(2.0 * math.pi * freq * i / sample_rate))
                buf.extend(bytes([sample & 0xFF, (sample >> 8) & 0xFF]))
            sound = pygame.mixer.Sound(buffer=buf)
            return sound
        except:
            return None

    def load_high_score(self):
        """Load high score from file"""
        try:
            if os.path.exists("high_score.json"):
                with open("high_score.json", "r") as f:
                    data = json.load(f)
                    return data.get("score", 0)
        except:
            pass
        return 0

    def save_high_score(self, score):
        """Save high score to file"""
        try:
            with open("high_score.json", "w") as f:
                json.dump({"score": score}, f)
            self.high_score = score
        except:
            pass

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    if self.state == "main":
                        self.selected = (self.selected - 1) % len(self.options)
                    else:
                        self.difficulty_selected = (self.difficulty_selected - 1) % len(DIFFICULTIES)
                    if self.menu_nav_sound:
                        self.menu_nav_sound.play()
                elif event.key == pygame.K_DOWN:
                    if self.state == "main":
                        self.selected = (self.selected + 1) % len(self.options)
                    else:
                        self.difficulty_selected = (self.difficulty_selected + 1) % len(DIFFICULTIES)
                    if self.menu_nav_sound:
                        self.menu_nav_sound.play()
                elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    if self.state == "main":
                        if self.selected == 0:
                            return "play"
                        elif self.selected == 1:
                            self.state = "tutorial"
                        elif self.selected == 2:
                            self.state = "settings"
                            self.selected = 0
                            self.difficulty_selected = DIFFICULTIES.index(self.difficulty)
                        elif self.selected == 3:
                            return "quit"
                    elif self.state == "settings":
                        if self.difficulty_selected < len(DIFFICULTIES):
                            self.difficulty = DIFFICULTIES[self.difficulty_selected]
                        self.state = "main"
                        self.selected = 1
                elif event.key == pygame.K_ESCAPE:
                    if self.state == "settings" or self.state == "tutorial":
                        self.state = "main"
                        self.selected = 1
        return None

    def draw(self, screen):
        screen.fill("black")
        if self.state == "main":
            self.draw_main(screen)
        elif self.state == "settings":
            self.draw_settings(screen)
        elif self.state == "tutorial":
            self.draw_tutorial(screen)

    def draw_main(self, screen):
        title = self.font_large.render("ASTEROIDS", True, pygame.Color("white"))
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 50))

        # High score display
        hs_text = self.font_small.render(f"Best Score: {self.high_score}", True, pygame.Color("cyan"))
        screen.blit(hs_text, (SCREEN_WIDTH // 2 - hs_text.get_width() // 2, 130))

        y_offset = 250
        for i, option in enumerate(self.options):
            color = pygame.Color("yellow") if i == self.selected else pygame.Color("white")
            text = self.font_medium.render(option, True, color)
            x = SCREEN_WIDTH // 2 - text.get_width() // 2
            screen.blit(text, (x, y_offset + i * 80))
            
            # Add selection indicator
            if i == self.selected:
                indicator = self.font_medium.render(">", True, pygame.Color("yellow"))
                screen.blit(indicator, (x - 60, y_offset + i * 80))
                screen.blit(indicator, (x + text.get_width() + 20, y_offset + i * 80))

        controls = self.font_small.render("Use UP/DOWN to select, ENTER to proceed", True, pygame.Color("lightgray"))
        screen.blit(controls, (SCREEN_WIDTH // 2 - controls.get_width() // 2, SCREEN_HEIGHT - 50))

    def draw_settings(self, screen):
        title = self.font_large.render("SETTINGS", True, pygame.Color("white"))
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 80))

        difficulty_label = self.font_medium.render("DIFFICULTY:", True, pygame.Color("white"))
        screen.blit(difficulty_label, (SCREEN_WIDTH // 2 - difficulty_label.get_width() // 2, 200))

        y_offset = 280
        for i, diff in enumerate(DIFFICULTIES):
            color = pygame.Color("yellow") if i == self.difficulty_selected else pygame.Color("white")
            text = self.font_small.render(diff, True, color)
            x = SCREEN_WIDTH // 2 - text.get_width() // 2
            screen.blit(text, (x, y_offset + i * 60))
            
            if i == self.difficulty_selected:
                indicator = self.font_small.render(">", True, pygame.Color("yellow"))
                screen.blit(indicator, (x - 50, y_offset + i * 60))

        back_text = self.font_small.render("ENTER to confirm, ESC to cancel", True, pygame.Color("lightgray"))
        screen.blit(back_text, (SCREEN_WIDTH // 2 - back_text.get_width() // 2, SCREEN_HEIGHT - 50))

    def draw_tutorial(self, screen):
        title = self.font_large.render("TUTORIAL", True, pygame.Color("white"))
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 40))

        # Tutorial content
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
            if line == "":
                y_offset += 15
                continue
            
            # Make section headers yellow
            if line.endswith(":") and line.isupper():
                color = pygame.Color("cyan")
                font = self.font_small
            else:
                color = pygame.Color("lightgray")
                font = self.font_small
            
            text = font.render(line, True, color)
            screen.blit(text, (50, y_offset))
            y_offset += 25

        back_text = self.font_small.render("ESC to return to menu", True, pygame.Color("lightgray"))
        screen.blit(back_text, (SCREEN_WIDTH // 2 - back_text.get_width() // 2, SCREEN_HEIGHT - 50))
