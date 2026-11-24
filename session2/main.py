"""Game-Plattform: ein Fenster, eine Ereignisschleife, mehrere Spiele."""
from pathlib import Path
import traceback
import pygame

from game_api import GameAPI
from game_manager import discover_games, new_game
from logger import SessionLogger

WIDTH, HEIGHT = 800, 600
ROOT = Path(__file__).resolve().parent

# Farben
BG = (18, 25, 38)
FG = (235, 241, 247)
MUTED = (162, 177, 194)
ACCENT = (108, 195, 250)


class Platform:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption('DSKI-Game-Plattform · pygame-ce')
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 34)
        self.big_font = pygame.font.Font(None, 58)
        self.small_font = pygame.font.Font(None, 26)
        self.logger = SessionLogger(ROOT / 'data')
        self.games = discover_games()
        self.nickname = ''
        self.state = 'NICKNAME'
        self.selected = 0
        self.game = None
        self.pending_finish = None
        self.result_title = ''
        self.result_text = ''
        self.running = True

    def write(self, text, x, y, font=None, color=FG):
        image = (font or self.font).render(str(text), True, color)
        self.screen.blit(image, (x, y))

    def start_selected(self):
        if not self.games:
            return
        module_name, name = self.games[self.selected]
        try:
            self.logger.start(self.nickname, name)
            api = GameAPI(self.nickname, name, self.logger.event, self.request_finish)
            self.game = new_game(module_name, api)
            self.pending_finish = None
            self.state = 'PLAYING'
        except Exception as exc:
            traceback.print_exc()
            if self.logger.current is not None:
                self.logger.event('error', repr(exc))
                self.logger.finish(status='error')
            self.game = None
            self.result_title = 'Startfehler'
            self.result_text = f'{type(exc).__name__}: {exc}'
            self.state = 'RESULT'

    def request_finish(self, score=0, status='completed'):
        # Nicht mitten in einem Spiel-Callback die Spielinstanz wechseln.
        if self.state == 'PLAYING' and self.pending_finish is None:
            self.pending_finish = (score, status)

    def finish_game(self):
        if self.pending_finish is None:
            return
        score, status = self.pending_finish
        self.pending_finish = None
        name = self.logger.current['game'] if self.logger.current else 'Spiel'
        self.logger.finish(score, status)
        self.game = None
        self.result_title = name
        if status == 'completed':
            self.result_text = f'Ergebnis: {score} Punkte'
        elif status == 'aborted':
            self.result_text = 'Spiel abgebrochen'
        else:
            self.result_text = 'Spiel mit einem Fehler beendet'
        self.state = 'RESULT'

    def game_error(self, exc):
        traceback.print_exc()
        try:
            self.logger.event('error', f'{type(exc).__name__}: {exc}')
        except OSError:
            traceback.print_exc()
        self.request_finish(status='error')
        self.finish_game()

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
            return
        if self.state == 'NICKNAME':
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and self.nickname.strip():
                    self.nickname = self.nickname.strip()
                    self.state = 'MENU'
                elif event.key == pygame.K_BACKSPACE:
                    self.nickname = self.nickname[:-1]
                elif event.unicode and event.unicode.isprintable() and len(self.nickname) < 24:
                    self.nickname += event.unicode
        elif self.state == 'MENU':
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_DOWN, pygame.K_s) and self.games:
                    self.selected = (self.selected + 1) % len(self.games)
                elif event.key in (pygame.K_UP, pygame.K_w) and self.games:
                    self.selected = (self.selected - 1) % len(self.games)
                elif event.key == pygame.K_RETURN:
                    self.start_selected()
                elif event.key == pygame.K_n:
                    self.state = 'NICKNAME'
                    self.nickname = ''
        elif self.state == 'PLAYING':
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.request_finish(status='aborted')
            elif self.pending_finish is None:
                self.game.handle_event(event)
        elif self.state == 'RESULT':
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                self.state = 'MENU'

    def draw_menu(self):
        self.screen.fill(BG)
        self.write('Game-Plattform', 55, 42, self.big_font, ACCENT)
        self.write(f'Spieler: {self.nickname}', 58, 108, self.small_font, MUTED)
        if not self.games:
            self.write('Keine Spiele gefunden (Ordner games/).', 60, 220)
        else:
            for index, (_, name) in enumerate(self.games):
                y = 190 + index * 29
                selected = index == self.selected
                if selected:
                    pygame.draw.rect(self.screen, (39, 60, 81),
                                     (45, y - 9, 710, 28), border_radius=8)
                self.write(('> ' if selected else '   ') + name, 65, y,
                           color=ACCENT if selected else FG)
        self.write('Pfeiltasten: Auswahl    Enter: Spielen    N: Nickname',
                   50, 546, self.small_font, MUTED)

    def draw_nickname(self):
        self.screen.fill(BG)
        self.write('Willkommen!', 55, 70, self.big_font, ACCENT)
        self.write('Gib Deinen Nickname ein:', 58, 182)
        pygame.draw.rect(self.screen, (39, 60, 81),
                         (55, 238, 690, 62), border_radius=8)
        self.write(self.nickname + '|', 72, 252)
        self.write('Enter: weiter (max. 24 Zeichen)', 58, 340, self.small_font, MUTED)

    def draw_result(self):
        self.screen.fill(BG)
        self.write('Spiel beendet', 55, 75, self.big_font, ACCENT)
        self.write(self.result_title, 58, 196)
        # Laengere Fehlermeldungen werden nicht durch das Fenster gescrollt.
        self.write(self.result_text[:60], 58, 252, self.small_font)
        self.write('Enter: zurueck zum Menue', 58, 360, self.small_font, MUTED)

    def run(self):
        try:
            while self.running:
                dt = min(self.clock.tick(60) / 1000.0, 0.1)
                for event in pygame.event.get():
                    try:
                        self.handle_event(event)
                    except Exception as exc:
                        if self.state == 'PLAYING':
                            self.game_error(exc)
                        else:
                            traceback.print_exc()
                    if not self.running:
                        break
                if not self.running:
                    break
                if self.state == 'PLAYING':
                    if self.pending_finish is None:
                        try:
                            keys = pygame.key.get_pressed()
                            self.game.update(dt, keys)
                            if self.pending_finish is None:
                                self.game.draw(self.screen)
                        except Exception as exc:
                            self.game_error(exc)
                    self.finish_game()
                if self.state == 'NICKNAME':
                    self.draw_nickname()
                elif self.state == 'MENU':
                    self.draw_menu()
                elif self.state == 'RESULT':
                    self.draw_result()
                pygame.display.flip()
        finally:
            if self.logger.current is not None:
                self.logger.finish(status='aborted')
            pygame.quit()


if __name__ == '__main__':
    Platform().run()
