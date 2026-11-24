# CROSSY ROAD

import pygame
from random import randint
import os
import time

HIGHSCORE_DATEI = os.path.join(os.path.dirname(os.path.abspath(__file__)), "highscore.txt")

GAME_NAME = "Crossy Road"

CARS_PER_ROW = 20
SLOT = 180            # Platz pro Auto (Auto ist 50 breit -> nie Überlappung)
RING = CARS_PER_ROW * SLOT   # Länge des Rings = 1000
LEFT = -150           # linkes Ende des Rings (außerhalb des Bildes)

class Game:
    def __init__(self, api):
        self.api = api
        self.score = 0
        self.rect_x = 400
        self.rect_y = 550
        self.score = 0
        self.leben = 2
        self.speed = 200
        self.car_speed = 150
        self.höchste_zeile = 500
        #Scrollen:
        self.offset = 0
        self.scroll_rest = 0

        self.y_werte = [-100, 0 , 100, 200, 300, 400, 500]
        self.zeilengröße = 100

        self.highscore = 0
        try:
            with open(HIGHSCORE_DATEI) as f:
                self.highscore = int(f.read().strip())
        except (FileNotFoundError, ValueError):
            pass   # noch keine Datei oder kaputter Inhalt -> bei 0 anfangen

        # pro Zeile 10 Autos, jedes in seinem eigenen Slot mit zufälligem Versatz
        self.x_werte = []
        for _ in self.y_werte:
            for k in range(CARS_PER_ROW):
                self.x_werte.append(LEFT + k * SLOT + randint(30, 120))

        self.richtungen = []
        for i in range(len(self.y_werte)):
            if i % 2 == 0:
                self.richtungen.append(1)
            else:
                self.richtungen.append(-1)
        
        #Bilder
        self.huhn = pygame.image.load("Huhn_transparent.png").convert_alpha()
        self.huhn = pygame.transform.scale(self.huhn, (35, 35))
        self.background = pygame.image.load("rasen.jpg").convert_alpha()
        self.street = pygame.image.load("street.jpg").convert_alpha()
        self.street = pygame.transform.scale(self.street, (800, 100))
        self.autorot = pygame.image.load("autorot.png").convert_alpha()
        self.autorot = pygame.transform.scale(self.autorot, (80, 40))
        self.autoblau = pygame.image.load("autoblau.png").convert_alpha()
        self.autoblau = pygame.transform.scale(self.autoblau, (90, 55))
       
        

    def handle_event(self, event):
        #if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
        #      self.score += 1
        self.api.log_event("score", self.score)


    def update(self, dt, keys):
        if keys[pygame.K_UP]:
            self.rect_y -= self.speed * dt
        elif keys[pygame.K_DOWN]:
            self.rect_y += self.speed * dt
        if keys[pygame.K_LEFT]:
            self.rect_x -= self.speed * dt
        elif keys[pygame.K_RIGHT]:
            self.rect_x += self.speed * dt

        if self.rect_x > 800 - 20:
            self.rect_x = 800 - 20
        elif self.rect_x < 0:
            self.rect_x = 0
        if self.rect_y > 600 + 20:
            self.rect_y = 600 - 20
        elif self.rect_y < 0:
            self.rect_y = 0

        for i in range(len(self.y_werte)):
            for j in range(i * CARS_PER_ROW, (i+1) * CARS_PER_ROW):
                self.x_werte[j] += self.richtungen[i] * self.car_speed * dt
                if self.x_werte[j] >= LEFT + RING:   # rechts aus dem Ring
                    self.x_werte[j] -= RING          # links wieder einsetzen
                if self.x_werte[j] < LEFT:   # links aus dem Ring
                    self.x_werte[j] += RING          # rechts wieder raus

        # Scroll starten
        if self.scroll_rest == 0 and self.rect_y + 20 < self.höchste_zeile - self.zeilengröße:
            self.scroll_rest = 100
            self.score += 1
            self.car_speed += 10

        # Scrollen: Welt und Spieler gemeinsam nach unten schieben
        if self.scroll_rest > 0:
            schritt = min(self.scroll_rest, 300 * dt)   # 300 Pixel pro Sekunde
            self.scroll_rest -= schritt
            self.offset += schritt
            self.rect_y += schritt

            if self.scroll_rest <= 0:
                # fertig: neue Zeile oben einfügen, unten abschneiden
                self.offset = 0
                for k in range(CARS_PER_ROW):
                    self.x_werte.append(LEFT + k * SLOT + randint(30, 120))
                self.richtungen.insert(0, -self.richtungen[0])
                #self.x_werte[0:0] = [LEFT + k * SLOT + randint(30, 120) for k in range(CARS_PER_ROW)]
                # überzählige Zeilen unten abschneiden
                del self.x_werte[len(self.y_werte) * CARS_PER_ROW:]
                del self.richtungen[len(self.y_werte):]

                #Kollision:
        #for i in range(len(self.y_werte)):
        for j in range(len(self.x_werte)):
            y = self.y_werte[j // CARS_PER_ROW] + self.offset #Ganzzahldivision (Rundung)
            if (self.rect_x + 20 > self.x_werte[j] and
            self.rect_x < self.x_werte[j] + 50 and
            self.rect_y + 20 > y and
            self.rect_y < y + 30):
                self.leben -= 1
                self.rect_x = 400     # zurück zum Start, sonst zählt jedes Frame
                self.rect_y = 550
                time.sleep(0.5)
                break       

        if self.leben <= 0:
            if self.score > self.highscore:
                self.highscore = self.score
                with open(HIGHSCORE_DATEI, "w") as f:
                    f.write(str(self.highscore))
            self.api.end_game(self.score)

    def draw(self, screen):
        screen.blit(self.background, (0,0))
        for y in self.y_werte:
            screen.blit(self.street, (0, y-30 + self.offset))
        screen.blit(self.huhn, (self.rect_x, self.rect_y))

    
        font = pygame.font.SysFont(None, 36)
        text = font.render(f"Score: {self.score}   Highscore: {max(self.score, self.highscore)}   Leben: {self.leben}", True, "black")
        screen.blit(text, (10, 10))

        for i in range(len(self.y_werte)):
            for j in range(i * CARS_PER_ROW, (i + 1) * CARS_PER_ROW):
                if self.richtungen[i] == 1:
                    screen.blit(self.autorot, (self.x_werte[j], self.y_werte[i] + self.offset, 50, 30))
                else:
                    screen.blit(self.autoblau, (self.x_werte[j], self.y_werte[i] + self.offset, 50, 30))