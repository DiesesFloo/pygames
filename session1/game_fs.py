import pygame
import random

# Mini-Pong mit Extras
# Kern: Ball prallt an Wänden und Schläger ab, fällt er unten raus, geht ein Leben weg.
# Extras: grüne Dreiecke lassen den Ball wachsen (+5 Punkte), rote schrumpfen ihn (-5 Punkte).
#         Regentropfen färben den Schläger um.
# Aufbau: __init__ = feste Werte, reset_game/reset_ball = Startzustand,
#         update = Logik (60x pro Sekunde), draw = Darstellung.

# Konstanten für Fenster
WIDTH = 800
HEIGHT = 600

# Ball
BALL_X = 100.0
BALL_Y = 240.0
BALL_START_RADIUS = 25.0
BALL_MIN = 5.0
BALL_MAX = 50.0
BALL_STEP = 3.0          # Wachsen/Schrumpfen pro Dreieck
BALL_START_VX = 300.0
BALL_START_VY = -300.0
BALL_MAX_VX = 500.0      # max. Seitengeschwindigkeit nach Schlägertreffer

# Dreiecke
TRI_VISIBLE_TIME = 5.0   # so lange ist ein Dreieck sichtbar
TRI_PAUSE = 2.0          # Pause bis zum nächsten Dreieck

# Regen
DROP_LENGTH = 10

class Game:
    # Spielzustand
    # Hier kommt alles rein, was man sich merken muss, um das Spiel zu spielen.
    def __init__(self):
        self.font_big = pygame.font.Font(None, 72)
        self.font_small = pygame.font.Font(None, 32)
        # Schläger (Paddle)
        self.paddle_width = 150.0
        self.paddle_height = 20.0
        self.paddle_x = 100.0
        self.paddle_y = HEIGHT - 20.0 - self.paddle_height
        self.paddle_speed = 300.0
        self.paddle_color = "blue"
        # Dreieck zum Fressen (es gibt immer höchstens eins)
        self.tri_size = 15.0
        self.tri_x = 0.0
        self.tri_y = 0.0
        self.tri_good = True
        # Leben, Ball und Dreieck-Timer werden in reset_game gesetzt
        self.reset_game()

    # Logik:
    # keys ist aktueller Zustand aller Tasten (gedrückt oder nicht).
    # dt ist die Zeit seit dem letzten Frame in Sekunden (Geschwindigkeit ist unabhängig von der Framerate).
    def update(self, dt: float, keys) -> None:
        # Wenn kein Leben mehr vorhanden, Spiel vorbei
        if self.game_over:
            if keys[pygame.K_SPACE]:
                self.reset_game()
            return
        # Sich selbst bewegender Ball
        self.ball_x += self.ball_vx * dt
        self.ball_y += self.ball_vy * dt

        self.bounce_at_walls()

        if keys[pygame.K_RIGHT]:
            self.paddle_x += self.paddle_speed * dt
        elif keys[pygame.K_LEFT]:
            self.paddle_x -= self.paddle_speed * dt

        self.keep_paddle_in_box()
        self.bounce_at_paddle()
        self.check_ball_lost()

        self.update_triangle(dt)
        self.eat_triangle()

        self.update_rain(dt)

    # Ball an den Wänden abprallen lassen (wie bei Pong)
    def bounce_at_walls(self):
        if self.ball_x - self.ball_radius < 0:
            self.ball_x = self.ball_radius
            self.ball_vx = -self.ball_vx
        elif self.ball_x + self.ball_radius > WIDTH:
            self.ball_x = WIDTH - self.ball_radius
            self.ball_vx = -self.ball_vx
        if self.ball_y - self.ball_radius < 0:
            self.ball_y = self.ball_radius
            self.ball_vy = -self.ball_vy
        # Ball nicht mehr unten abprallen lassen
        #elif self.ball_y + self.ball_radius > HEIGHT:
        #    self.ball_y = HEIGHT - self.ball_radius
        #    self.ball_vy = -self.ball_vy

    # Ball auf Höhe des Schlägers, abprallen lassen
    def bounce_at_paddle(self):
        if (self.ball_vy > 0  # fliegt nach unten
                and self.ball_y + self.ball_radius >= self.paddle_y  # berührt Oberkante
                and self.ball_y <= self.paddle_y + self.paddle_height  # noch nicht durch
                and self.ball_x + self.ball_radius >= self.paddle_x  # nicht links daneben
                and self.ball_x - self.ball_radius <= self.paddle_x + self.paddle_width):  # nicht rechts daneben
            self.ball_y = self.paddle_y - self.ball_radius
            self.ball_vy = -abs(self.ball_vy)
            # Trefferstelle: -1 = linker Rand, 0 = Mitte, +1 = rechter Rand
            paddle_center = self.paddle_x + self.paddle_width / 2
            offset = (self.ball_x - paddle_center) / (self.paddle_width / 2)
            offset = max(-1.0, min(offset, 1.0))
            self.ball_vx = offset * BALL_MAX_VX
            self.score += 1

    # Paddle nur am unteren Rand des Fensters bewegen, nicht darüber hinaus
    def keep_paddle_in_box(self):
        self.paddle_x = max(0.0, min(self.paddle_x, WIDTH - self.paddle_width))

    # Leben abziehen, wenn Ball unten rausfällt. Wenn keine Leben mehr, Spiel vorbei.
    def lose_life(self):
        self.lives -= 1
        if self.lives <= 0:
            self.game_over = True
        else:
            self.reset_ball()

    # Überprüfen, ob Ball komplett unten rausgefallen ist. Wenn ja, Leben abziehen.
    def check_ball_lost(self):
        if self.ball_y - self.ball_radius > HEIGHT:
            self.lose_life()

    # Ball zurücksetzen auf Startwerte
    def reset_ball(self):
        self.ball_x = BALL_X
        self.ball_y = BALL_Y
        self.ball_vx = BALL_START_VX
        self.ball_vy = BALL_START_VY
        self.ball_radius = BALL_START_RADIUS

    # Spiel zurücksetzen: Leben, Ball, Dreieck
    def reset_game(self):
        self.lives = 3
        self.game_over = False
        self.reset_ball()
        self.tri_visible = False
        self.tri_time_left = TRI_PAUSE    # Pause bis zum ersten Dreieck
        self.drops = []
        self.drop_timer = 0.0
        self.score = 0

    # Neues Dreieck an zufälliger Position, zufällig gut oder böse
    def spawn_triangle(self):
        self.tri_visible = True
        self.tri_time_left = TRI_VISIBLE_TIME    # so lange bleibt es sichtbar
        self.tri_x = random.uniform(self.tri_size, WIDTH - self.tri_size)
        self.tri_y = random.uniform(self.tri_size, self.paddle_y - 50)
        self.tri_good = random.choice([True, False])

    # Countdown: sichtbar -> verschwinden, Pause vorbei -> neues Dreieck
    def update_triangle(self, dt):
        self.tri_time_left -= dt
        if self.tri_time_left <= 0:
            if self.tri_visible:
                self.tri_visible = False
                self.tri_time_left = TRI_PAUSE    # Pause
            else:
                self.spawn_triangle()

    # Ball berührt Dreieck: grün -> wachsen, rot -> schrumpfen
    def eat_triangle(self):
        if not self.tri_visible:
            return
        dx = self.ball_x - self.tri_x
        dy = self.ball_y - self.tri_y
        if dx * dx + dy * dy <= (self.ball_radius + self.tri_size*1.5) ** 2:
            if self.tri_good:
                self.ball_radius = min(self.ball_radius + BALL_STEP, BALL_MAX)
                self.score += 5
            else:
                self.ball_radius -= BALL_STEP
                if self.ball_radius < BALL_MIN:
                    self.lose_life()
                    self.score -= 5
            self.tri_visible = False
            self.tri_time_left = TRI_PAUSE    # Pause, bevor das nächste kommt

    # Regen: zufällige Tropfen, die auf den Schläger fallen. Wenn getroffen, Schlägerfarbe ändern.
    def update_rain(self, dt):
        # neuer Tropfen in kurzen, zufälligen Abständen
        self.drop_timer -= dt
        if self.drop_timer <= 0:
            self.drops.append({
                "x": random.uniform(0, WIDTH),
                "y": -10.0,
                "vy": random.uniform(200, 400)
            })
            self.drop_timer = random.uniform(0.1, 0.3)

        # alle Tropfen fallen lassen
        for drop in self.drops:
            drop["y"] += drop["vy"] * dt

        # neue Liste: nur Tropfen, die weder den Schläger getroffen haben noch unten raus sind
        remaining = []
        for drop in self.drops:
            bottom = drop["y"] + DROP_LENGTH    # unteres Ende des Strichs
            hit = (self.paddle_x <= drop["x"] <= self.paddle_x + self.paddle_width
                   and self.paddle_y <= bottom <= self.paddle_y + self.paddle_height)
            if hit:
                self.paddle_color = random.choice(["blue", "purple", "cyan", "yellow", "pink"])
            elif drop["y"] < HEIGHT:
                remaining.append(drop)
        self.drops = remaining

    # Darstellung:
    # In jedem Frame wird ganzes Bild neu gezeichnet --> schwarz übermalen, dann Elemente
    # (ball_x, ball_y) ist der Mittelpunkt des Balls.
    # Beim Rechteck ist (paddle_x, paddle_y) die Ecke oben links, nicht der Mittelpunkt.
    # Koordinatensystem hat Ursprung links oben und wächst nach rechts und unten. (0, 0) ist linke obere Ecke, (800, 600) ist rechte untere Ecke.
    def draw(self, screen: pygame.Surface) -> None:
        screen.fill("black")
        for drop in self.drops:
            pygame.draw.line(screen, "lightblue", (drop["x"], drop["y"]), (drop["x"], drop["y"] + DROP_LENGTH))
        for i in range(self.lives):
            pygame.draw.circle(screen, "green", (WIDTH - 30 - i * 30, 30), 10)
        score_text = self.font_small.render(f"Punkte: {self.score}", True, "white")
        screen.blit(score_text, (20, 20))
        if self.tri_visible:
            color = "green" if self.tri_good else "red"
            pygame.draw.polygon(screen, color, [
                (self.tri_x, self.tri_y - self.tri_size),
                (self.tri_x - self.tri_size, self.tri_y + self.tri_size),
                (self.tri_x + self.tri_size, self.tri_y + self.tri_size)
            ])
        pygame.draw.circle(screen, "orange", (self.ball_x, self.ball_y), self.ball_radius)
        pygame.draw.rect(screen, self.paddle_color, (self.paddle_x, self.paddle_y, self.paddle_width, self.paddle_height))
        if self.game_over:
            text = self.font_big.render("GAME OVER", True, "red")
            screen.blit(text, text.get_rect(center=(WIDTH / 2, HEIGHT / 2 - 30)))

            hint = self.font_small.render("Leertaste für Neustart", True, "white")
            screen.blit(hint, hint.get_rect(center=(WIDTH / 2, HEIGHT / 2 + 30)))

            score_text = self.font_small.render(f"Punkte: {self.score}", True, "white")
            screen.blit(score_text, score_text.get_rect(center=(WIDTH / 2, HEIGHT / 2 + 70)))

def main():
    pygame.init()

    # Falls nichts angezeigt wird, die folgenden Zeilen aktivieren, um die SDL- und pygame-Versionen zu prüfen.
    # print("SDL driver:", pygame.display.get_driver())
    # print("pygame:", pygame.version.ver)
    # print("SDL:", pygame.get_sdl_version())

    # Game Loop: Eingabe --> Update --> Zeichnen --> Anzeigen

    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    game = Game()
    running = True
    while running:
        # Events abholen: Fenster schließen
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        # max. 60fps (ms --> s)
        dt = clock.tick(60) / 1000
        game.update(dt, pygame.key.get_pressed())
        game.draw(screen)
        # gezeichnetes Bild anzeigen (davor wird alles in einem "versteckten" Bild gezeichnet, das dann auf den Bildschirm kopiert wird)
        pygame.display.flip()
    pygame.quit()

# Main nur ausführen, wenn Datei direkt gestartet wird
# Wichtig für Session2: Plattform hat eigene Hauptschleife, beim Import soll nicht gestartet werden.
if __name__ == "__main__":
    main()
