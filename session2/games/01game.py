import random
from math import ceil
from pathlib import Path

import pygame


Feldbreite = 800
Feldhöhe = 600
GAME_NAME = "FrancoJump"

STAGE_ZEITLIMIT = (9.0, 8.0, 7.0, 6.5)
STAGE_ANZEIGE_DAUER = 2.0
STAGE_ENDE_DAUER = 0.5
SIEG_STAGE = 20

normale_plaetze = (40, 240, 440, 640)
versetzte_plaetze = (140, 340, 540)
plattformreihen = (
    (475, normale_plaetze),
    (395, versetzte_plaetze),
    (315, normale_plaetze),
    (235, versetzte_plaetze),
)
plattformbreite = 120


class Game:
    def __init__(self, api):
        self.api = api
        self.sidelength = 50
        self.vx = 200.0
        self.accy = 1300.0

        self.stage = 0
        self.stages_abgeschlossen = 0
        self.spieldauer = 0.0
        self.points = 0
        self.gamelifes = 3
        self.gewonnen = False

        spielerpfad = Path(__file__).with_name("spieler.jpeg")
        spielerbild = pygame.image.load(str(spielerpfad)).convert()
        self.spielerbild = pygame.transform.smoothscale(
            spielerbild, (self.sidelength, self.sidelength)
        )

        bildpfad = Path(__file__).with_name("gameover.jpg")
        bild = pygame.image.load(str(bildpfad))
        self.game_over_bild = pygame.transform.scale(
            bild, (Feldbreite, Feldhöhe)
        )

        siegbildpfad = Path(__file__).with_name("winning.png")
        siegbild = pygame.image.load(str(siegbildpfad)).convert()
        self.siegbild = pygame.transform.smoothscale(
            siegbild, (Feldbreite, Feldhöhe)
        )

        self.font = pygame.font.Font(None, 64)
        self.punkte_font = pygame.font.Font(None, 28)

        self.sprung_sounds = []
        self.coin_sounds = []
        if pygame.mixer.get_init():
            soundordner = Path(__file__).with_name("sounds")
            self.sprung_sounds = [
                pygame.mixer.Sound(str(soundordner / f"boing{nummer}.ogg"))
                for nummer in range(1, 4)
            ]
            self.coin_sounds = [
                pygame.mixer.Sound(str(soundordner / f"coin{nummer}.ogg"))
                for nummer in range(1, 3)
            ]

            for sound in self.sprung_sounds:
                sound.set_volume(0.1)

            for sound in self.coin_sounds:
                sound.set_volume(0.1)

        self.neue_stage()

    def neue_stage(self, leben_verloren=False):
        self.stage += 1
        self.leben_verloren = leben_verloren
        self.stage_anzeige_restzeit = STAGE_ANZEIGE_DAUER
        self.stage_ende_restzeit = 0.0
        self.neuer_versuch()

        self.plattformen = [
            pygame.Rect(0, 550, Feldbreite, 20),  # Boden
        ]

        for y, plaetze in plattformreihen:
            anzahl = random.randint(2, 3)
            ausgewaehlte_x = random.sample(plaetze, anzahl)

            for x in ausgewaehlte_x:
                self.plattformen.append(
                    pygame.Rect(x, y, plattformbreite, 8)
                )

        self.frannycoins = []

        for plattform in self.plattformen[1:]:
            anzahl = random.randint(0, 2)

            for nummer in range(1, anzahl + 1):
                x = plattform.left + plattform.width * nummer // (anzahl + 1)
                coin = pygame.Rect(0, 0, 20, 20)
                coin.midbottom = (x, plattform.top - 8)
                self.frannycoins.append(coin)

        # Jede Stage hat mindestens eine Münze.
        if not self.frannycoins:
            plattform = random.choice(self.plattformen[1:])
            coin = pygame.Rect(0, 0, 20, 20)
            coin.midbottom = (plattform.centerx, plattform.top - 8)
            self.frannycoins.append(coin)

    def neuer_versuch(self):
        zeit_index = min((self.stage - 1) // 5, len(STAGE_ZEITLIMIT) - 1)
        self.stage_restzeit = STAGE_ZEITLIMIT[zeit_index]

        self.x = 375.0
        self.y = 500.0
        self.vy = 0.0
        self.am_boden = True
        self.luftsprung_bereit = True

    def jump(self):
        if not self.am_boden:
            if not self.luftsprung_bereit:
                return
            self.luftsprung_bereit = False

        self.vy = -500.0
        self.am_boden = False

        if self.sprung_sounds:
            random.choice(self.sprung_sounds).play()

        self.api.log_event("space_pressed", self.points)

    def handle_event(self, event):
        if self.gewonnen or self.gamelifes == 0:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                self.api.end_game(
                    self.points,
                    details=(
                        f"Spielzeit: {self.spieldauer:.1f} s",
                        f"Erreichte Stage: {self.stage}",
                        f"Abgeschlossene Stages: {self.stages_abgeschlossen}",
                        f"Spiel gemeistert: {'Ja' if self.gewonnen else 'Nein'}",
                    ),
                )
            return

        if self.stage_anzeige_restzeit > 0 or self.stage_ende_restzeit > 0:
            return

        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            self.jump()

    def update(self, dt, keys):
        if self.gewonnen or self.gamelifes == 0:
            return

        if self.stage_anzeige_restzeit > 0:
            self.stage_anzeige_restzeit = max(
                0.0, self.stage_anzeige_restzeit - dt
            )
            return

        if self.stage_ende_restzeit > 0:
            self.stage_ende_restzeit -= dt
            if self.stage_ende_restzeit <= 0:
                if self.stage >= SIEG_STAGE:
                    self.gewonnen = True
                    self.ergebnis_loggen()
                else:
                    self.neue_stage()
            return

        dt = min(dt, self.stage_restzeit)
        self.stage_restzeit -= dt
        self.spieldauer += dt

        if keys[pygame.K_d]:
            self.x += self.vx * dt
        elif keys[pygame.K_a]:
            self.x -= self.vx * dt

        self.x = max(0, min(self.x, Feldbreite - self.sidelength))

        alte_fuesse = self.y + self.sidelength
        self.vy += self.accy * dt
        self.y += self.vy * dt
        neue_fuesse = self.y + self.sidelength
        self.am_boden = False

        spieler_rect = self.spielerbild.get_rect(
            topleft=(int(self.x), int(self.y))
        )

        for coin in self.frannycoins.copy():
            if spieler_rect.colliderect(coin):
                self.points += 1
                self.frannycoins.remove(coin)

                if self.coin_sounds:
                    random.choice(self.coin_sounds).play()

                self.api.log_event("gesammelte Coins", self.points)

        if not self.frannycoins:
            self.stages_abgeschlossen += 1
            self.stage_ende_restzeit = STAGE_ENDE_DAUER
            return

        if self.stage_restzeit <= 0:
            self.gamelifes -= 1
            if self.gamelifes > 0:
                self.neue_stage(leben_verloren=True)
            else:
                self.ergebnis_loggen()
            return

        # Beim Aufsteigen kann die Figur durch Plattformen springen.
        if self.vy < 0:
            return

        spieler_rechts = self.x + self.sidelength
        landekanten = []

        for plattform in self.plattformen:
            if keys[pygame.K_s] and plattform is not self.plattformen[0]:
                continue

            ueberlappt_x = (
                spieler_rechts > plattform.left
                and self.x < plattform.right
            )
            erreicht_oberkante = alte_fuesse <= plattform.top <= neue_fuesse

            if ueberlappt_x and erreicht_oberkante:
                landekanten.append(plattform.top)

        if landekanten:
            self.y = min(landekanten) - self.sidelength
            self.vy = 0.0
            self.am_boden = True
            self.luftsprung_bereit = True

    def ergebnis_loggen(self):
        self.api.log_event("score", self.points)
        self.api.log_event("gesamtspielzeit_s", round(self.spieldauer, 2))
        self.api.log_event("stage_erreicht", self.stage)
        self.api.log_event("spiel_gemeistert", int(self.gewonnen))

    def draw_game_over(self, screen):
        screen.blit(self.game_over_bild, (0, 0))
        pygame.draw.rect(
            screen, (24, 24, 24), (210, 175, 380, 250), border_radius=12
        )

        titel = self.font.render("Game Over", True, "white")
        screen.blit(titel, titel.get_rect(center=(Feldbreite // 2, 225)))

        zeilen = (
            f"Punkte: {self.points}",
            f"Abgeschlossene Stages: {self.stages_abgeschlossen}",
            f"Spielzeit: {self.spieldauer:.1f} s",
            "Enter: Ergebnis anzeigen",
        )

        for nummer, zeile in enumerate(zeilen):
            text = self.punkte_font.render(zeile, True, "white")
            position = text.get_rect(center=(Feldbreite // 2, 275 + nummer * 33))
            screen.blit(text, position)

    def draw_sieg(self, screen):
        screen.blit(self.siegbild, (0, 0))
        mitte_x = Feldbreite // 2
        schriftfarbe = (53, 29, 9)

        titel = self.font.render("Gewonnen!", True, schriftfarbe)
        screen.blit(titel, titel.get_rect(center=(mitte_x, 464)))

        zeilen = (
            f"Punkte: {self.points}    ·    Abgeschlossene Stages: {self.stages_abgeschlossen}",
            f"Spielzeit: {self.spieldauer:.1f} s",
            "Enter: Ergebnis anzeigen",
        )

        for nummer, zeile in enumerate(zeilen):
            text = self.punkte_font.render(zeile, True, schriftfarbe)
            screen.blit(text, text.get_rect(center=(mitte_x, 512 + nummer * 26)))

    def draw(self, screen):
        if self.gewonnen:
            self.draw_sieg(screen)
            return

        if self.gamelifes == 0:
            self.draw_game_over(screen)
            return

        screen.fill("light blue")

        if self.stage_anzeige_restzeit > 0:
            mitte_x = Feldbreite // 2
            mitte_y = Feldhöhe // 2

            if self.leben_verloren:
                hinweis = self.punkte_font.render("Lost a life!", True, "white")
                screen.blit(
                    hinweis, hinweis.get_rect(center=(mitte_x, mitte_y - 50))
                )

            text = self.font.render(f"Stage {self.stage}", True, "white")
            screen.blit(text, text.get_rect(center=(mitte_x, mitte_y)))

            zeitlimit_text = self.punkte_font.render(
                f"Zeitlimit: {self.stage_restzeit:g} s", True, "white"
            )
            screen.blit(
                zeitlimit_text,
                zeitlimit_text.get_rect(center=(mitte_x, mitte_y + 48)),
            )

            if self.stage == 1:
                steuerung = (
                    "A / D: Nach links / rechts",
                    "S: Durch Plattformen fallen",
                    "Leertaste: Sprung / Doppelsprung",
                )
                for nummer, zeile in enumerate(steuerung):
                    hinweis = self.punkte_font.render(zeile, True, "white")
                    position = hinweis.get_rect(
                        center=(mitte_x, mitte_y + 92 + nummer * 28)
                    )
                    screen.blit(hinweis, position)

            return

        for plattform in self.plattformen:
            pygame.draw.rect(screen, "brown", plattform)

        for coin in self.frannycoins:
            pygame.draw.rect(screen, "orange", coin)

        screen.blit(self.spielerbild, (int(self.x), int(self.y)))

        punktestand = self.punkte_font.render(
            f"Punkte: {self.points}", True, "white"
        )
        leben = self.punkte_font.render(
            f"Leben: {self.gamelifes}", True, "white"
        )
        stage_text = self.punkte_font.render(
            f"Stage: {self.stage}", True, "white"
        )
        zeit_text = self.punkte_font.render(
            f"Zeit: {ceil(self.stage_restzeit)} s", True, "white"
        )

        screen.blit(punktestand, (20, 20))
        screen.blit(leben, (20, 45))
        screen.blit(stage_text, (20, 70))
        screen.blit(zeit_text, zeit_text.get_rect(topright=(Feldbreite - 20, 20)))