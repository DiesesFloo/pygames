import pygame
import random
import math
from pathlib import Path
import cv2

GAME_NAME = "EJD - Evil Johannes Dodge"

class Game:
    def __init__(self, api):
        self.api = api
        self.game_won = False

        bildpfad = Path(__file__).resolve().parent / "assets"

        #Trailer
        self.intro_playing = True

        #Zufällige Trailerauswahl (50/50)
        trailer = random.choice(["trailer1", "trailer2"])

        #Video laden
        self.intro_video = cv2.VideoCapture(
            str(bildpfad / f"{trailer}.mp4")
        )

        self.intro_fps = self.intro_video.get(cv2.CAP_PROP_FPS) or 30
        self.intro_timer = 0.0
        self.intro_frame = None

        #Audio laden
        if not pygame.mixer.get_init():
            pygame.mixer.init()

        self.intro_sound = pygame.mixer.Sound(
            str(bildpfad / f"{trailer}.ogg")
        )

        self.intro_channel = self.intro_sound.play()

        #Texturen
        self.background_color = (16, 78, 139)

        self.backgrounds = {
            1: pygame.image.load(str(bildpfad / "lvl1.png")),
            2: pygame.image.load(str(bildpfad / "lvl2.png")),
            3: pygame.image.load(str(bildpfad / "lvl3.png")),
            4: pygame.image.load(str(bildpfad / "lvl4.png"))
        }

        for level in self.backgrounds:
            self.backgrounds[level] = pygame.transform.scale(
                self.backgrounds[level], (800, 600)
            )

        #Fensterränder
        self.wall_right = 800
        self.wall_left = 0
        self.wall_upper = 0
        self.wall_lower = 600

        #Ballgröße
        self.ball_size = 40
        self.ball_radius = self.ball_size / 2

        #Balltextur
        self.ball_image = pygame.image.load(
            str(bildpfad / "balltexture.png")
        )

        self.ball_image = pygame.transform.scale(
            self.ball_image, (self.ball_size, self.ball_size)
        )

        #Ball rund ausschneiden
        mask = pygame.Surface(
            (self.ball_size, self.ball_size), pygame.SRCALPHA
        )

        pygame.draw.circle(
            mask, "white",
            (self.ball_radius, self.ball_radius),
            self.ball_radius
        )

        self.ball_image = self.ball_image.convert_alpha()
        self.ball_image.blit(
            mask, (0, 0),
            special_flags=pygame.BLEND_RGBA_MULT
        )

        #Projektile
        self.proj_spawnrate = 2.0
        self.proj_size = 10
        self.proj_radius = self.proj_size / 2
        self.proj_speed = 100.0  # px/s
        self.proj_color = (255, 0, 0)
        self.proj_right = 5
        self.proj_top = 0
        self.proj_bottom = 0
        self.projectiles = []

        #Lootbox
        self.lootbox = None
        self.lootbox_size = 30
        self.lootbox_message = ""
        self.lootbox_message_timer = 0.0

        #Spawnpunkt
        self.x = 100.0
        self.y = 300.0

        #Ballgeschwindigkeit    
        self.speed = 200.0      # px/s

        #Spieltimer
        self.proj_timer = 0.0
        self.game_timer = 0.0

        #Score
        self.score = 0

        #Schriftart
        self.font = pygame.font.SysFont(None, 48)
        self.font2 = pygame.font.SysFont(None, 20)

        #
        self.completed_events = set()

        #Levelsystem
        self.level = 1
        self.level_timer = 0.0
        self.levels = {
        1: {
            15: {"speed": 1.50,},
            25: {"speed": 1.20, "size": 4},
            35: {"projectiles": 1, "size": 0.25},
            45: {"projectiles": 1, "speed": 1.15}
            },

        2: {
            15: {"speed": 1.20, "size": 3},
            25: {"speed": 1.20, "size": 0.4},
            35: {"speed": 1.15, "projectiles_top": 1},
            45: {"speed": 1.20}
            },

        3: {
            15: {"projectiles": 2, "lootbox": True},
            25: {"speed": 1.20,},
            35: {"projectiles_top": 1},
            45: {"projectiles_top": 1}
            },

        4: {
            15: {"size": 1.15, "speed": 1.15},
            25: {"size": 1.15, "speed": 1.15},
            35: {"projectiles_top": 1},
            45: {"projectiles_top": 1, "speed": 1.15}
            }}

        #Instant Lose
        self.instant_lose = False
        self.instant_lose_timer = 3.0
        
        #Übergang
        self.in_transition = False
        self.transition_timer = 0.0

    def end_intro(self):
        self.intro_playing = False
        self.intro_video.release()

        if self.intro_channel is not None:
            self.intro_channel.stop()

    def update_difficulty(self):
        events = self.levels.get(self.level, {})

        for time, changes in events.items():

            if self.level_timer >= time and time not in self.completed_events:

                if "speed" in changes:
                    self.proj_speed *= changes["speed"]
                    self.api.log_event("projectile_speed_increase", self.proj_speed)

                if "projectiles" in changes:
                    self.proj_right += changes["projectiles"]
                    self.api.log_event("projectile_qty_increase", self.proj_right)

                if "projectiles_top" in changes:
                    self.proj_top += changes["projectiles_top"]
                    self.api.log_event("projectile_top_qty_increase", self.proj_top)

                if "size" in changes:
                    self.proj_size *= changes["size"]
                    self.proj_radius = self.proj_size / 2
                    self.api.log_event("projectile_size_increase", self.proj_size)

                if "lootbox" in changes:
                    if random.random() < 0.8:
                        self.lootbox = (
                            random.randint(100, 700),
                            random.randint(100, 500)
                        )
                        self.api.log_event("lootbox_spawned", True)
                    else:
                        self.api.log_event("lootbox_spawned", False)

                self.completed_events.add(time)

    def open_lootbox(self):
        effect = random.choices([
            "speed_up",
            "speed_down",
            "speed_down_big",
            "player_speed_up",
            "less_right",
            "bottom_projectiles",
            "bottom_and_top_projectiles",
            "instant_lose",
            "rdm_teleport"
        ],
        weights=[30, 15, 5, 10, 10, 10, 20, 0.1, 6],
        k=1
        )[0]
        if effect == "speed_up":
            self.proj_speed *= 1.10
            self.lootbox_message = "Projektil-Geschwindigkeit +10%"

        elif effect == "speed_down":
            self.proj_speed *= 0.85
            self.lootbox_message = "Projektil-Geschwindigkeit -15%"

        elif effect == "speed_down_big":
            self.proj_speed *= 0.70
            self.lootbox_message = "Projektil-Geschwindigkeit -30%"

        elif effect == "less_right":
            self.proj_right = max(0, self.proj_right - 1)
            self.lootbox_message = "-1 Projektil von rechts"

        elif effect == "bottom_projectiles":
            self.proj_bottom += 2
            self.lootbox_message = "+2 Projektile von unten"

        elif effect == "player_speed_up":
            self.speed *= 1.15
            self.lootbox_message = "Spieler-Geschwindigkeit +15%"

        elif effect == "bottom_and_top_projectiles":
            self.proj_bottom += 2
            self.proj_top += 1
            self.lootbox_message = "+2 Projektile von unten, +1 Projektil von oben"

        elif effect == "instant_lose":
            self.instant_lose = True
            self.lootbox = None
            self.api.log_event("lootbox_opened", effect)
            return

        elif effect == "rdm_teleport":
            new_x = random.randint(100, 700)
            new_y = random.randint(100, 500)
            self.x = new_x
            self.y = new_y
            self.lootbox_message = f"Teleportiert zu x-{new_x}/y-{new_y}"

        self.api.log_event("lootbox_opened", effect)

        self.lootbox_message_timer = 3.0
        self.lootbox = None

    def ckeck_collision(self):

        for x, y, richtung in self.projectiles:

            d = math.sqrt(
                (x - self.x)**2 +
                (y - self.y)**2)

            if d <= self.ball_radius + self.proj_radius:
                self.api.log_event("collision_direction", richtung)
                self.api.log_event("collision_x", self.x)
                self.api.log_event("collision_y", self.y)
                return True

        return False
            

    # update state
    def update(self, dt: float, keys) -> None:

        #Trailer abspielen
        if self.intro_playing:

            #Trailer überspringen
            if keys[pygame.K_SPACE]:
                self.end_intro()
                return

            self.intro_timer += dt

            while self.intro_timer >= 1 / self.intro_fps:

                self.intro_timer -= 1 / self.intro_fps
                success, frame = self.intro_video.read()

                if not success:
                    self.end_intro()
                    return

                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = cv2.resize(frame, (800, 600))

                self.intro_frame = pygame.surfarray.make_surface(
                    frame.swapaxes(0, 1)
                )

            return

        # Levelübergang
        if self.in_transition:

            self.transition_timer -= dt

            if self.transition_timer <= 0:
                self.level += 1
                self.api.log_event("level_start", self.level)
                self.level_timer = 0.0
                self.completed_events.clear()
                self.proj_timer = 0.0
                self.in_transition = False

            return

        # Timer
        self.game_timer += dt
        self.level_timer += dt

        #Punkte aktualisieren
        self.score = min(int(self.game_timer), 180)

        # Schwierigkeit erhöhen
        self.update_difficulty()

        # Level nach 45 Sekunden beenden
        if self.level_timer >= 45:
            self.api.log_event("level_completed", self.level)

            # Spiel nach Level 4 beenden
            if self.level == 4:
                self.score = 200
                self.game_won = True
                self.api.log_event("game_won", self.score)
                self.api.end_game(self.score)
                return

            # Sonst nächstes Level vorbereiten
            self.in_transition = True
            self.transition_timer = 5.0

            self.projectiles.clear()
            self.proj_timer = 0.0


        # WASD-Steuerung
        if keys[pygame.K_d]:
            self.x += self.speed * dt
        if keys[pygame.K_a]:
            self.x -= self.speed * dt
        if keys[pygame.K_s]:
            self.y += self.speed * dt
        if keys[pygame.K_w]:
            self.y -= self.speed * dt

        # Wandkollision
        if self.x > self.wall_right - self.ball_radius:
            self.x = self.wall_right - self.ball_radius

        if self.x < self.wall_left + self.ball_radius:
            self.x = self.wall_left + self.ball_radius

        if self.y > self.wall_lower - self.ball_radius:
            self.y = self.wall_lower - self.ball_radius

        if self.y < self.wall_upper + self.ball_radius:
            self.y = self.wall_upper + self.ball_radius

        # Projektiltimer
        self.proj_timer += dt

        # Projektile erschaffen
        if self.proj_timer >= self.proj_spawnrate:

            # Projektile von rechts
            for n in range(self.proj_right):

                for versuch in range(100):
                    y = random.randint(5, 595)

                    if all(
                        (self.wall_right - px)**2 + (y - py)**2
                        >= (2 * self.proj_radius + 5)**2
                        for px, py, richtung in self.projectiles
                    ):
                        self.projectiles.append(
                            (self.wall_right, y, "right")
                        )
                        break

            # Projektile von oben
            for n in range(self.proj_top):
                for versuch in range(100):
                    x = random.randint(5, 795)

                    if all(
                        (x - px)**2 + (self.wall_upper - py)**2
                        >= (2 * self.proj_radius + 5)**2
                        for px, py, richtung in self.projectiles
                    ):
                        self.projectiles.append(
                            (x, self.wall_upper, "top")
                        )
                        break

            #Projektile von unten
            for n in range(self.proj_bottom):
                for versuch in range(100):
                    x = random.randint(5, 795)

                    if all(
                        (x - px)**2 + (self.wall_lower - py)**2
                        >= (2 * self.proj_radius + 5)**2
                        for px, py, richtung in self.projectiles
                    ):
                        self.projectiles.append(
                            (x, self.wall_lower, "bottom")
                        )
                        break
            self.proj_timer -= self.proj_spawnrate

        # Projektile bewegen
        new_projectiles = []

        for x, y, richtung in self.projectiles:

            if richtung == "right":
                x -= self.proj_speed * dt

            elif richtung == "top":
                y += self.proj_speed * dt
  
            elif richtung == "bottom":
                y -= self.proj_speed * dt

            if (
                -self.proj_radius <= x <= self.wall_right + self.proj_radius
                and
                -self.proj_radius <= y <= self.wall_lower + self.proj_radius
            ):
                new_projectiles.append((x, y, richtung))

        self.projectiles = new_projectiles

        #Lootbox einsammeln
        if self.lootbox is not None:

            lx, ly = self.lootbox

            distance = math.sqrt(
                (self.x - lx)**2 +
                (self.y - ly)**2
            )

            if distance <= self.ball_radius + self.lootbox_size / 2:
                self.open_lootbox()
                if self.instant_lose:
                    return

        #Lootbox-Nachricht Timer
        if self.lootbox_message_timer > 0:
            self.lootbox_message_timer -= dt

        # Kollision prüfen
        if self.ckeck_collision():
            self.api.log_event("collision", self.score)
            self.api.end_game(self.score)

        #Instant Lose
        if self.instant_lose:
            self.instant_lose_timer -= dt

            if self.instant_lose_timer <= 0:
                self.api.end_game(self.score)

            return

    # draw new state
    def draw(self, screen: pygame.Surface) -> None:

        #Trailer anzeigen
        if self.intro_playing:

            screen.fill("black")

            if self.intro_frame is not None:
                screen.blit(self.intro_frame, (0, 0))

            #Skip-Anzeige
            skip_text = self.font.render(
                "SPACE to skip", True, "white"
            )

            rect = skip_text.get_rect(bottomright=(790, 590))
            screen.blit(skip_text, rect)

            return

        #Hintergrund zeichnen
        screen.blit(self.backgrounds[self.level], (0, 0))

        #Spieler zeichnen
        screen.blit(
            self.ball_image,
            (self.x - self.ball_radius,
            self.y - self.ball_radius)
        )

        for x, y, richtung in self.projectiles:
            pygame.draw.circle(
                screen, self.proj_color,
                (x, y), self.proj_radius
            )

            # Umrandung
            pygame.draw.circle(
                screen, "white",
                (x, y), self.proj_radius, 2
            )

        # Spielzeit anzeigen
        timer_text = self.font.render(
            f"Zeit: {self.game_timer:.1f}s",
            True, "white"
        )
        screen.blit(timer_text, (10, 10))

        # Level anzeigen
        level_text = self.font.render(
            f"Level: {self.level}",
            True, "white"
        )
        screen.blit(level_text, (600, 10))

        #Steuerung anzeigen
        controls_text = self.font2.render("up-W left-A down-S right-D", True, "white")
        screen.blit(controls_text, (
            800 - controls_text.get_width() - 10,
            600 - controls_text.get_height() - 10
        ))

        # Levelübergang anzeigen
        if self.in_transition:

            countdown = math.ceil(self.transition_timer)

            text = self.font.render(
                f"Level {self.level + 1} in {countdown}",
                True, "white"
            )

            rect = text.get_rect(center=(400, 300))
            screen.blit(text, rect)

        #Lootbox zeichnen
        if self.lootbox is not None:

            lx, ly = self.lootbox

            rect = pygame.Rect(0, 0, 30, 30)
            rect.center = (lx, ly)

            pygame.draw.rect(screen, "purple", rect)
            pygame.draw.rect(screen, "gold", rect, 2)

            text = self.font.render("?", True, "white")
            screen.blit(text, text.get_rect(center=rect.center))

        #Item-Anzeige
        if self.lootbox_message_timer > 0:
            text = self.font.render(
                self.lootbox_message, True, "yellow"
            )

            screen.blit(
                text, text.get_rect(center=(400, 100))
            )

        #Instant Lose Screen
        if self.instant_lose:
            screen.fill("black")

            text = self.font.render(
                "INSTANT LOSE", True, "red"
            )
            screen.blit(
                text, text.get_rect(center=(400, 250))
            )

            #Drop-Chance anzeigen
            chance_text = self.font2.render(
                "Drop Chance: 0.1%", True, "white"
            )
            screen.blit(
                chance_text, chance_text.get_rect(center=(400, 300))
            )

            countdown = self.font2.render(
                f"Game ending in {math.ceil(self.instant_lose_timer)}...",
                True, "white"
            )
            screen.blit(
                countdown, countdown.get_rect(center=(400, 550))
            )

            return

    def handle_event(self, event):
        pass