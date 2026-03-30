import pygame
from constants import SCREEN_WIDTH, SCREEN_HEIGHT


class Menu:
    def __init__(self):
        self.font_large = pygame.font.Font(None, 60)
        self.font_medium = pygame.font.Font(None, 40)
        self.font_small = pygame.font.Font(None, 30)
        self.selected = 0
        self.options = ["PLAY", "SETTINGS", "QUIT"]
        self.state = "main"  # 'main', 'settings', 'game'

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.selected = (self.selected - 1) % len(self.options)
                elif event.key == pygame.K_DOWN:
                    self.selected = (self.selected + 1) % len(self.options)
                elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    if self.state == "main":
                        if self.selected == 0:
                            return "play"
                        elif self.selected == 1:
                            self.state = "settings"
                            self.selected = 0
                        elif self.selected == 2:
                            return "quit"
                    elif self.state == "settings":
                        if self.selected == 0:
                            self.state = "main"
                            self.selected = 0
                elif event.key == pygame.K_ESCAPE:
                    if self.state == "settings":
                        self.state = "main"
                        self.selected = 0
        return None

    def draw(self, screen):
        screen.fill("black")
        if self.state == "main":
            self.draw_main(screen)
        elif self.state == "settings":
            self.draw_settings(screen)

    def draw_main(self, screen):
        title = self.font_large.render("ASTEROIDS", True, pygame.Color("white"))
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 100))

        y_offset = 300
        for i, option in enumerate(self.options):
            color = pygame.Color("yellow") if i == self.selected else pygame.Color("white")
            text = self.font_medium.render(option, True, color)
            screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, y_offset + i * 80))

        controls = self.font_small.render("Use UP/DOWN to select, ENTER to proceed", True, pygame.Color("lightgray"))
        screen.blit(controls, (SCREEN_WIDTH // 2 - controls.get_width() // 2, SCREEN_HEIGHT - 50))

    def draw_settings(self, screen):
        title = self.font_large.render("SETTINGS", True, pygame.Color("white"))
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 100))

        back_text = self.font_medium.render("BACK", True, pygame.Color("yellow"))
        screen.blit(back_text, (SCREEN_WIDTH // 2 - back_text.get_width() // 2, 300))

        info = self.font_small.render("More settings coming soon!", True, pygame.Color("lightgray"))
        screen.blit(info, (SCREEN_WIDTH // 2 - info.get_width() // 2, 400))

        controls = self.font_small.render("Press ENTER to go back or ESC", True, pygame.Color("lightgray"))
        screen.blit(controls, (SCREEN_WIDTH // 2 - controls.get_width() // 2, SCREEN_HEIGHT - 50))
