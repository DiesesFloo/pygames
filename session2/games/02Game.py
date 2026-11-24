import pygame
from random import randint, sample, choice
import array

GAME_NAME = "Breakout"

POWERUPS = {
    "leben": {"name": "Extra-Leben", "farbe": "hotpink", "dauer": 0, "symbol": "+"},
    "breit": {"name": "Breit", "farbe": "limegreen", "dauer": 10, "symbol": "<>"},
    "schmal": {"name": "Schmal", "farbe": "magenta", "dauer": 10, "symbol": "><"},
    "langsam": {"name": "Langsam", "farbe": "deepskyblue", "dauer": 8, "symbol": "S"},
    "durchschlag": {"name": "Durchschlag", "farbe": "red", "dauer": 5, "symbol": "D"}
}

Breite = 800
Hoehe = 600

# Erzeugt einen Retro-Ton (Rechteckwelle) mit Tonhöhe in Hz und Dauer in Sekunden
def ton(frequenz, dauer):
    if pygame.mixer.get_init() is None:
        pygame.mixer.init(22050, -16, 1, 256)
    rate, format, kanaele = pygame.mixer.get_init()
    anzahl = int(rate * dauer)
    periode = int(rate / frequenz)
    daten = array.array("h")
    for i in range(anzahl):
        lautstaerke = int(6000 * (1 - i / anzahl))
        if (i % periode) < periode // 2:
            wert = lautstaerke
        else:
            wert = -lautstaerke
        for k in range(kanaele):
            daten.append(wert)
    return pygame.mixer.Sound(buffer=daten.tobytes())

# Baut aus einer Liste von (Tonhöhe, Dauer) eine Melodie. Tonhöhe 0 = Pause
def melodie(noten, laut=2500):
    if pygame.mixer.get_init() is None:
        pygame.mixer.init(22050, -16, 1, 256)
    rate, format, kanaele = pygame.mixer.get_init()
    daten = array.array("h")
    for frequenz, dauer in noten:
        anzahl = int(rate * dauer)
        if frequenz > 0:
            periode = int(rate / frequenz)
        for i in range(anzahl):
            lautstaerke = int(laut * (1 - i / anzahl))
            if frequenz == 0:
                wert = 0
            elif (i % periode) < periode // 2:
                wert = lautstaerke
            else:
                wert = -lautstaerke
            for k in range(kanaele):
                daten.append(wert)
    return pygame.mixer.Sound(buffer=daten.tobytes())

NOTEN = [(262, 0.2), (330, 0.2), (392, 0.2), (523, 0.2),
         (392, 0.2), (330, 0.2), (262, 0.2), (0, 0.2),
         (220, 0.2), (262, 0.2), (330, 0.2), (440, 0.2),
         (330, 0.2), (262, 0.2), (220, 0.2), (0, 0.2)]


class Game:
    def __init__(self, api):
        self.api = api
        self.score = 0
        self.verloren = False

        # Sounds
        self.sound_wand = ton(180, 0.06)
        self.sound_schlaeger = ton(440, 0.08)
        self.sound_block = melodie([(660, 0.04), (990, 0.07)], 6000)
        self.sound_leben = melodie([(400, 0.15), (300, 0.15), (200, 0.25)], 6000)
        self.sound_powerup = melodie([(523, 0.06), (659, 0.06), (784, 0.06), (1047, 0.1)], 6000)

        # Hintergrundmusik
        self.musik = melodie(NOTEN)
        self.musik.set_volume(0.4)
        self.musik.play()

        # Rechteck
        self.x = Breite // 2 - 50
        self.y = 570.0         
        self.speed = 400.0      # px/s

        #Ball
        self.radius = 20
        self.bx = 400.0
        self.by = 300.0
        self.vx = randint(150, 300) * (1 if randint(0, 1) == 1 else -1)
        self.vy = randint(150, 300)

        self.fallende = []       # Liste von Dictionaries: {"x":..., "y":..., "typ":...}
        self.aktiv = {}          # Typ -> Restzeit, z.B. {"breit": 7.3}
        self.font_klein = pygame.font.Font(None, 24)

        # Gitter aus 3 Reihen mit je 10 Feldern
        felder = []
        for reihe in range(3):
            for spalte in range(10):
                felder.append((spalte, reihe))

        # 5 zufällige Felder werden zu Punkten, alle anderen zu Blöcken
        punkt_felder = sample(felder, 5)

        self.bloecke = []
        self.punkte = []
        self.punkt_radius = 8

        self.partikel = []
        self.spur = []

        for spalte, reihe in felder:
            block = pygame.Rect(spalte * 80 + 5, 50 + reihe * 30, 70, 20)
            if (spalte, reihe) in punkt_felder:
                self.punkte.append(block.center)
            else:
                self.bloecke.append(block)

        # Schrift für die Anzeige
        self.font = pygame.font.Font(None, 36)

        self.font = pygame.font.Font(None, 36)
        self.font_gross = pygame.font.Font(None, 96)

        #Timer
        self.timer = 0.0
        self.timer2 = 3.0

        #Leben
        self.leben = 3
        self.leben_zeit = 0.0

        #Verloren
        self.verloren = False

        #Anhalten
        self.angehalten = False

        #Spielzeit
        self.spielzeit = 0.0

        #Level
        self.level = 1
        self.punkt_radius = 8
        self.baue_gitter()

    def handle_event(self, event):
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                self.score += 1
                self.api.log_event("space_pressed", self.score)
                if self.score >= 10:
                    self.api.end_game(self.level)
                    

    # update state
    def update(self, dt: float, keys) -> None:

        # Musik neu starten, sobald sie zu Ende ist (nur solange man spielt)
        if not self.verloren and self.musik.get_num_channels() == 0:
            self.musik.play()

        # Animationen laufen immer weiter, auch im Countdown
        for p in self.partikel[:]:
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["leben"] -= dt
            if p["leben"] <= 0:
                self.partikel.remove(p)

        #Neustart
        if self.verloren:
            self.musik.stop()
            return

        #Timer2
        if self.timer2 > 0:
            self.timer2 -= dt
            self.spur = []
            return

        if self.angehalten:
            return

        self.spielzeit += dt

        b = self.schlaeger_breite()
        
        # Restzeiten der Power-ups herunterzählen
        for typ in list(self.aktiv):
            self.aktiv[typ] -= dt
            if self.aktiv[typ] <= 0:
                del self.aktiv[typ]

        if keys[pygame.K_RIGHT]:
            self.x += self.speed * dt
        elif keys[pygame.K_LEFT]:
            self.x -= self.speed * dt
        
        # Ränder
        if self.x < 0:
            self.x = 0
        elif self.x + b > Breite:
            self.x = Breite - b
        elif self.y < 0:
            self.y = 0
        elif self.y + 20 > Hoehe:
            self.y = Hoehe - 20

        #Ball bewegen
        faktor = 0.6 if "langsam" in self.aktiv else 1.0
        self.bx += self.vx * dt * faktor
        self.by += self.vy * dt * faktor

        self.spur.append((self.bx, self.by))
        if len(self.spur) > 12:
            self.spur.pop(0)

        #Ball an den rändern abprallen lassen
        if self.bx - self.radius < 0:
            self.bx = self.radius
            self.vx = -self.vx
            self.sound_wand.play()
        elif self.bx + self.radius > Breite:
            self.bx = Breite - self.radius
            self.vx = -self.vx
            self.sound_wand.play()
        elif self.by - self.radius < 0:
            self.by = self.radius
            self.vy = -self.vy
            self.sound_wand.play()
        elif self.by + self.radius > Hoehe:
            self.leben -= 1
            self.sound_leben.play()
            Dauer = self.timer - self.leben_zeit
            self.api.log_event("leben_dauer", round(Dauer, 1))
            self.leben_zeit = self.timer
            if self.leben == 0:
                self.verloren = True
                self.verloren = True
                self.api.end_game(self.level)
            else:
                self.bx = 400.0
                self.by = 300.0
                self.vx = randint(150, 300) * (1 if randint(0, 1) == 1 else -1)
                self.vy = randint(150, 300)
                self.x = Breite // 2 - 50
                self.timer = 0.0
                self.timer2 = 3.0


        #Kollision Rechteck -- Ball
        schlaeger = pygame.Rect(self.x, self.y, b, 20)
        ball = pygame.Rect(self.bx - self.radius, self.by - self.radius,
                           2 * self.radius, 2 * self.radius)

        if ball.colliderect(schlaeger) and self.vy > 0:
            t = (self.bx - (self.x + b / 2)) / (b / 2)
            t = max(-1, min(1, t))
            tempo = (self.vx ** 2 + self.vy ** 2) ** 0.5
            self.vx = t * tempo * 0.7
            self.vy = -((tempo ** 2 - self.vx ** 2) ** 0.5)
            self.by = self.y - self.radius
            self.sound_schlaeger.play()

        # Kollision Ball <-> Blöcke
        for block in self.bloecke[:]:
            if ball.colliderect(block):
                self.bloecke.remove(block)
                self.sound_block.play()
                self.partikel_erzeugen(block.centerx, block.centery, "blue")
                if randint(1, 100) <= 10:       # 10 % Chance
                    self.fallende.append({"x": block.centerx,
                                          "y": block.centery,
                                          "typ": choice(list(POWERUPS))})
                if "durchschlag" not in self.aktiv:
                    self.vy = -self.vy
                    break

        for p in self.fallende[:]:
            p["y"] += 150 * dt
            kasten = pygame.Rect(p["x"] - 14, p["y"] - 14, 28, 28)
            if kasten.colliderect(schlaeger):
                self.aktiviere(p["typ"])
                self.fallende.remove(p)
            elif p["y"] > Hoehe:
                self.fallende.remove(p)

        # Punkte einsammeln
        self.punkte = [p for p in self.punkte
                       if (self.bx - p[0]) ** 2 + (self.by - p[1]) ** 2
                          > (self.radius + self.punkt_radius) ** 2]

        #Timer
        self.timer += dt
        if self.timer >= 5:
            self.timer -= 5
            self.vx *= 1.1
            self.vy *= 1.1

        if len(self.punkte) == 0:
            self.neues_level()

    def partikel_erzeugen(self, x, y, farbe, anzahl=8):
        for _ in range(anzahl):
            self.partikel.append({"x": x, "y": y,
                                  "vx": randint(-150, 150),
                                  "vy": randint(-150, 150),
                                  "leben": 0.5,
                                  "farbe": farbe})

    def baue_gitter(self):
        reihen = min(2 + self.level, 6)               # Level 1: 3 Reihen, höchstens 6
        anzahl_punkte = min(4 + self.level, 10)       # Level 1: 5 Punkte, höchstens 10

        felder = []
        for reihe in range(reihen):
            for spalte in range(10):
                felder.append((spalte, reihe))

        punkt_felder = sample(felder, anzahl_punkte)

        self.bloecke = []
        self.punkte = []
        for spalte, reihe in felder:
            block = pygame.Rect(spalte * 80 + 5, 50 + reihe * 30, 70, 20)
            if (spalte, reihe) in punkt_felder:
                self.punkte.append(block.center)
            else:
                self.bloecke.append(block)

    def ball_zuruecksetzen(self):
        faktor = 1 + 0.1 * (self.level - 1)           # jedes Level 10 % schneller
        self.bx = 400.0
        self.by = 300.0
        self.vx = randint(150, 300) * faktor * (1 if randint(0, 1) == 1 else -1)
        self.vy = randint(150, 300) * faktor
        self.x = Breite // 2 - 50
        self.y = 570.0
        self.timer = 0.0
        self.timer2 = 3.0

        self.fallende = []
        self.aktiv = {}
        self.spur = []

    def schlaeger_breite(self) -> int:
        if "breit" in self.aktiv:
            return 150
        if "schmal" in self.aktiv:
            return 60
        return 100

    def aktiviere(self, typ: str) -> None:
        self.sound_powerup.play()
        if typ == "leben":
            self.leben += 1
            return
        self.aktiv[typ] = POWERUPS[typ]["dauer"]
        # Breit und Schmal heben sich gegenseitig auf
        if typ == "breit":
            self.aktiv.pop("schmal", None)
        elif typ == "schmal":
            self.aktiv.pop("breit", None)

    def neues_level(self):
        self.level += 1
        self.baue_gitter()
        self.ball_zuruecksetzen()


    # draw new state
    def draw(self, screen: pygame.Surface) -> None:
        
        screen.fill("black")
        pygame.draw.circle(screen, "orange", (self.bx, self.by), self.radius)

        #Punkte
        for p in self.punkte:
            pygame.draw.circle(screen, "yellow", p, self.punkt_radius)
        
        #Blöcke
        for block in self.bloecke:
            pygame.draw.rect(screen, "blue", block)

        for p in self.partikel:
            groesse = max(1, int(p["leben"] * 10))
            pygame.draw.circle(screen, p["farbe"], (p["x"], p["y"]), groesse)

        #Anzeige oben rechts
        Punkte_text = self.font.render(f"Punkte: {len(self.punkte)}", True, "white")
        screen.blit(Punkte_text, Punkte_text.get_rect(topright=(Breite - 10, 10)))

        #Anzeige oben links
        Leben_text = self.font.render(f"Leben: {self.leben}", True, "white")
        screen.blit(Leben_text, Leben_text.get_rect(topleft=(10, 10)))

        #Sekunden bis Start
        if self.timer2 > 0:
            zahl = int(self.timer2) + 1
            countdown = self.font_gross.render(str(zahl), True, "white")
            screen.blit(countdown, countdown.get_rect(center=(Breite // 2, Hoehe // 2 - 100)))

        #Pause
        if self.angehalten:
            text = self.font_gross.render("Pause", True, "white")
            screen.blit(text, text.get_rect(center=(Breite // 2, Hoehe // 2)))

        #Spielzeit
        zeit_text = self.font.render(f"Zeit: {self.spielzeit:.1f}s", True, "white")
        screen.blit(zeit_text, zeit_text.get_rect(midtop=(Breite // 2, 10)))

        # Farben je nach aktivem Power-up
        farbe_schlaeger = "orange"
        if "breit" in self.aktiv:
            farbe_schlaeger = POWERUPS["breit"]["farbe"]
        elif "schmal" in self.aktiv:
            farbe_schlaeger = POWERUPS["schmal"]["farbe"]

        farbe_ball = "orange"
        if "durchschlag" in self.aktiv:
            farbe_ball = POWERUPS["durchschlag"]["farbe"]
        elif "langsam" in self.aktiv:
            farbe_ball = POWERUPS["langsam"]["farbe"]


        basis = pygame.Color(farbe_ball)
        for i, (sx, sy) in enumerate(self.spur):
            anteil = (i + 1) / len(self.spur)           # 0 = alt, 1 = neu
            farbe = (int(basis.r * anteil * 0.6),
                     int(basis.g * anteil * 0.6),
                     int(basis.b * anteil * 0.6))
            pygame.draw.circle(screen, farbe, (sx, sy), int(self.radius * anteil))

        pygame.draw.circle(screen, farbe_ball, (self.bx, self.by), self.radius)
        pygame.draw.rect(screen, farbe_schlaeger,
                         (self.x, self.y, self.schlaeger_breite(), 20))

        # Fallende Power-ups
        for p in self.fallende:
            info = POWERUPS[p["typ"]]
            pygame.draw.circle(screen, info["farbe"], (p["x"], p["y"]), 14)
            symbol = self.font_klein.render(info["symbol"], True, "black")
            screen.blit(symbol, symbol.get_rect(center=(p["x"], p["y"])))

        # Aktive Power-ups mit Restzeit (unten links)
        for i, (typ, rest) in enumerate(self.aktiv.items()):
            info = POWERUPS[typ]
            text = self.font_klein.render(f"{info['name']}: {rest:.1f}s", True, info["farbe"])
            screen.blit(text, (10, Hoehe - 30 - i * 24))

