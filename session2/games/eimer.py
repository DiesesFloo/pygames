import pygame
import random


GAME_NAME = "Regenfänger"

ANZAHL_TROPFEN = 10
SPIELZEIT = 30.0

EIMER_HALBBREITE = 60
EIMER_HALBBREITE_UNTEN = 45
EIMER_OBEN = 520
EIMER_UNTEN = 560
FANG_BIS = 580
BODEN = 600

PUNKTE_GUT = 1
PUNKTE_BOESE = -3
PUNKTE_SUPER = 10

CHANCE_BOESE = 0.3
CHANCE_SUPER = 0.2

TROPFEN_NORMAL = (12, 20)
TROPFEN_SUPER = (20, 25)


class Game:
    def __init__(self, api):
        self.api = api
        self.score = 0
        self.serie = 0
        self.bucket_x = 400.0
        self.bucket_speed = 400.0
        self.raindrops_x = [0] * ANZAHL_TROPFEN
        self.raindrops_y = [0] * ANZAHL_TROPFEN
        self.raindrops_speed_y = [0] * ANZAHL_TROPFEN
        self.raindrops_bad = [False] * ANZAHL_TROPFEN
        self.raindrops_super = [False] * ANZAHL_TROPFEN
        self.raindrops_eimer_start_x = [0] * ANZAHL_TROPFEN
        for i in range(ANZAHL_TROPFEN):
            self.neuer_tropfen(i)
        self.time_left = SPIELZEIT
        self.font = pygame.font.Font(None, 36)

    def handle_event(self, event):
        pass

    def tropfen_groesse(self, i):
        if self.raindrops_super[i]:
            return TROPFEN_SUPER
        return TROPFEN_NORMAL

    def neuer_tropfen(self, i):
        self.raindrops_x[i] = random.randint(0, 800)
        self.raindrops_y[i] = random.randint(0, 300)
        self.raindrops_eimer_start_x[i] = self.bucket_x
        self.raindrops_speed_y[i] = 350 - self.raindrops_y[i] * 0.5
        self.raindrops_bad[i] = random.random() < CHANCE_BOESE
        self.raindrops_super[i] = random.random() < CHANCE_SUPER and not self.raindrops_bad[i]

    def update(self, dt, keys):
        if keys[pygame.K_LEFT]:
            self.bucket_x -= self.bucket_speed * dt
        if keys[pygame.K_RIGHT]:
            self.bucket_x += self.bucket_speed * dt
        if self.bucket_x < 1:
            self.bucket_x = 799
        if self.bucket_x > 799:
            self.bucket_x = 1
        for i in range(ANZAHL_TROPFEN):
            self.raindrops_y[i] +=self.raindrops_speed_y[i] * dt
            breite = self.tropfen_groesse(i)[0]
            mitte = self.raindrops_x[i] + breite / 2
            if EIMER_OBEN < self.raindrops_y[i] < FANG_BIS and self.bucket_x - EIMER_HALBBREITE < mitte < self.bucket_x + EIMER_HALBBREITE:
                if self.raindrops_bad[i]:
                    self.score = self.score + PUNKTE_BOESE
                    self.serie = 0
                    self.api.log_event("boese_getroffen", self.score)
                elif self.raindrops_super[i]:
                    self.score = self.score + PUNKTE_SUPER
                    self.serie += 1
                    self.api.log_event("super_getroffen", self.score)
                    self.api.log_event("super_jagd_gefangen", round(abs(self.bucket_x - self.raindrops_eimer_start_x[i])))
                else:
                    self.score = self.score + PUNKTE_GUT
                    self.serie += 1
                    self.api.log_event("gute_getroffen", self.score)
                self.api.log_event("tempo_gefangen", round(self.raindrops_speed_y[i]))
                self.neuer_tropfen(i)
            elif self.raindrops_y[i] > BODEN:
                self.api.log_event("verpasst", "boese" if self.raindrops_bad[i] else "super" if self.raindrops_super[i] else "gut")
                self.api.log_event("tempo_verpasst", round(self.raindrops_speed_y[i]))
                if self.raindrops_super[i]:
                    self.api.log_event("super_jagd_verpasst", round(abs(self.bucket_x - self.raindrops_eimer_start_x[i])))
                self.neuer_tropfen(i)
        self.time_left -= dt
        if self.time_left <= 0:
            self.api.log_event("zeit_abgelaufen", self.score)
            self.api.end_game(self.score)

    def draw(self, screen):
        screen.fill("navy")
        corners_bucket = [
            (self.bucket_x - EIMER_HALBBREITE, EIMER_OBEN),
            (self.bucket_x - EIMER_HALBBREITE_UNTEN, EIMER_UNTEN),
            (self.bucket_x + EIMER_HALBBREITE_UNTEN, EIMER_UNTEN),
            (self.bucket_x + EIMER_HALBBREITE, EIMER_OBEN),
        ]
        pygame.draw.lines(screen, "white", False, corners_bucket, 3)
        for n in range(ANZAHL_TROPFEN):
            farbe = "red" if self.raindrops_bad[n] else "cyan"
            farbe = "yellow" if self.raindrops_super[n] else farbe
            pygame.draw.ellipse(
                screen,
                farbe,
                (
                    self.raindrops_x[n],
                    self.raindrops_y[n],
                    self.tropfen_groesse(n)[0],
                    self.tropfen_groesse(n)[1],
                ),
            )
        self.score_text = self.font.render("Punkte: " + str(self.score), True, "white")
        screen.blit(self.score_text, (60, 10))
        self.serie_text = self.font.render("Serie: " + str(self.serie), True, "white")
        screen.blit(self.serie_text, (60, 40))
        self.time_text = self.font.render("Zeit: " + str(int(self.time_left)), True, "white")
        screen.blit(self.time_text, (700, 10))

