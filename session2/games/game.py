import pygame
from random import randint, choice

# Ein einfaches Spiel (na ja, schon ein sehr einfaches)
# Der Ball kann mit "Pfeil rechts" bewegt werden. 

# Erste Erweiterung: Ball wieder (mit Pfeil links) zurück bewegen.

GAME_NAME = "LaserPong"

class Game:
    def __init__(self, api):
        self.api = api
        self.length = 85
        self.height = 10
        self.x = 400.0 
        self.y = 570.0     
        self.speed = 300.0     # px/s

        self.ball_x = float(randint(20, 750))
        self.ball_y = float(randint(20, 200))
        self.ball_vx = 250.0
        self.ball_vy = 250.0

        self.ziel_x = float(randint(0 + 40, 770 - 40)) # -40: ganz am Rand kann nichts getroffen werden
        self.ziel_y = float(randint(100, 300))
        self.ziel_speed = 30.0
        self.ziel_vx = 30.0
        self.ziel_length = 30

        self.score = 0
        self.highscore = 0
        self.font = pygame.font.SysFont("Arial", 30) # Schriftart & Größe
        self.font1 = pygame.font.SysFont("Segoe UI Symbol", 50)
        self.font2 = pygame.font.SysFont("Arial", 25)

        self.hit_timer = 0.0
        self.hit_x = 0.0
        self.hit_y = 0.0
        self.laser_cooldown = 0.0
        self.laser_timer = 0.0
        self.laser_kann_treffen = True
        self.lost_life_timer = 0.0
        self.lost_life_x = 0.0
        self.lost_life_y = 530.0
        self.laser_shot = 0
        self.laser_combo = 0

        self.timer = 0.0
        self.stufe = 1
        self.leben = 3
        self.paddle_color = "red"

        self.drop_powerup = 0
        self.powerup_x = 0.0
        self.powerup_y = 0.0
        self.powerup_speed = 100.0
        self.radius_powerup = 10
        self.powerup_timer = 0.0
        self.powerup_active = False
        self.powerup_color = "white"
        self.powerup_wkeit = 3
        self.powerup_auswahl = 1
        self.powerup_count = 0
        self.magnet_kraft = 400.0

        self.tri_x = randint(100, 700)
        self.tri_y = randint(0, 200)
        self.tri_speed = 50.0
        self.tri_length = 30.0

        self.spiel_gestartet = False
        self.faktor_1 = 1.1
        self.faktor_2 = 1.05

    def handle_event(self, event): 
        if not self.spiel_gestartet:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    self.faktor_1 = 1.05
                    self.faktor_2 = 1.01
                    self.api.log_event("difficulty", 1)
                    self.spiel_gestartet = True
                    self.powerup_wkeit = 2
                    self.ziel_length = 50
                elif event.key == pygame.K_2:
                    self.api.log_event("difficulty", 2)
                    self.spiel_gestartet = True
                    self.ziel_length = 44
                elif event.key == pygame.K_3:
                    self.speed *= 1.1
                    self.faktor_1 = 1.3
                    self.faktor_2 = 1.2
                    self.api.log_event("difficulty", 3)
                    self.spiel_gestartet = True
                    self.ziel_length = 38
    # update state
    def update(self, dt: float, keys) -> bool:
        if not self.spiel_gestartet:
            return 
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.x += self.speed * dt
            if self.x > 800 - self.length: # rechte obere Ecke zählt; Schlägerlänge = 85
                self.x = 800 - self.length
        elif keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.x -= self.speed * dt
                if self.x < 0:
                    self.x = 0

        self.timer += dt # vergangene Zeit seit letztem Frame addieren
        if self.timer >= 6.0:
            self.ball_vx *= self.faktor_1
            self.ball_vy *= self.faktor_1
            self.speed *= self.faktor_2
            self.tri_speed *= self.faktor_1
            self.stufe += 1
            self.ziel_speed += self.faktor_1
            self.ziel_vx *= self.faktor_2
            self.timer = 0.0
            self.api.log_event("level_up", self.stufe)

        self.ball_x += self.ball_vx * dt
        self.ball_y += self.ball_vy * dt

        if self.powerup_wkeit != 2:
            self.tri_y += self.tri_speed *dt

        self.ziel_y += self.ziel_speed *dt
        self.ziel_x += self.ziel_vx *dt
        if randint(0, 100) == 0:
            self.ziel_vx *= -1

        if self.ziel_x < 40: #nicht über die Seiten raus
            self.ziel_x = 40
            self.ziel_vx *= -1
        elif self.ziel_x > 700:
            self.ziel_x = 700
            self.ziel_vx *= -1

        if self.ball_x < 20:
            self.ball_vx = abs(self.ball_vx)
        if self.ball_x > 780:
            self.ball_vx = - abs(self.ball_vx)
        if self.ball_y < 20:
            self.ball_vy = abs(self.ball_vy)


        paddle_rect = pygame.Rect(self.x, self.y, self.length, self.height) # unsichtabre Hitboxen erstellen
        ball_rect = pygame.Rect(self.ball_x - 20, self.ball_y - 20, 40, 40) # 20 = radius
        ziel_rect = pygame.Rect(self.ziel_x, self.ziel_y, self.ziel_length, 10)
        shot_rect = pygame.Rect(self.x + self.length / 2 - 3, 0, 6, self.y)
        powerup_rect = pygame.Rect(self.powerup_x - self.radius_powerup, self.powerup_y - self.radius_powerup, 20, 20)
        tri_rect = pygame.Rect(self.tri_x, self.tri_y, self.tri_length, self.tri_length)

        if powerup_rect.colliderect(paddle_rect) and self.powerup_timer <= 0 and self.powerup_active == False and self.drop_powerup == 1:
            self.powerup_active = True
            self.drop_powerup = 0
            self.powerup_timer = 6.0
            if self.powerup_auswahl == 1: # längerer Schläger
                self.length += 25
                if self.x > 800 - self.length:
                    self.x = 800 - self.length
                self.powerup_count += 1
                self.api.log_event("picked_up_longer_paddle", self.powerup_count)
            elif self.powerup_auswahl == 2: # langsamerer Ball
                self.ball_vx /= 2
                self.ball_vy /= 2
                self.powerup_count += 1
                self.api.log_event("picked_up_slower_ball", self.powerup_count)
            elif self.powerup_auswahl == 3:
                self.powerup_count += 1
                self.api.log_event("picked_up_magnet", self.powerup_count)
                
                
        if self.ball_vy > 0 and self.powerup_active and self.powerup_auswahl == 3:
            schlaeger_mitte = self.x + (self.length / 2)
            
            if self.ball_x < schlaeger_mitte:
                self.ball_vx += 400.0 * dt
            elif self.ball_x > schlaeger_mitte:
                self.ball_vx -= 400.0 * dt

            # Seitliche Geschwindigkeit begrenzen, damit der Ball danach nicht zu extrem rast
            max_vx = abs(self.ball_vy) * 1.2
            self.ball_vx = max(-max_vx, min(max_vx, self.ball_vx))


        if self.powerup_timer > 0:
            self.powerup_timer -= dt

        if self.powerup_timer <=0 and self.powerup_active == True:
            if self.powerup_auswahl == 1:
                self.length = 85
            if self.powerup_auswahl == 2:
                self.ball_vx *= 2
                self.ball_vy *= 2
            self.powerup_active = False

        if self.powerup_y > 600:
            self.drop_powerup = 0

        if ziel_rect.colliderect(shot_rect) and self.laser_timer > 0 and self.laser_kann_treffen:
            if self.laser_shot == 1:
                self.laser_combo += 1
                self.laser_shot = 0
            if self.laser_shot > 1:
                self.laser_combo = 1
                self.laser_shot = 0
            self.laser_kann_treffen = False # wenn ein anderes Ziel in der selben Linie spwant kann es nicht getroffen werden
            self.laser_cooldown -= 0.3 # kürzerer Cooldown bei Treffer
            self.ziel_vx *= choice([-1, 1])
            self.hit_timer = 0.8
            if self.drop_powerup != 1 and self.powerup_active == False:
                self.drop_powerup = randint(1, self.powerup_wkeit)
                if self.drop_powerup == 1:
                    self.powerup_x = self.ziel_x + self.ziel_length / 2 # Mittig am Ziel
                    self.powerup_y = self.ziel_y
                    self.powerup_auswahl = randint(1, 3)
                    if self.powerup_auswahl == 1:
                        self.powerup_color = "white"
                    elif self.powerup_auswahl == 2: 
                        self.powerup_color = "yellow"
                    elif self.powerup_auswahl == 3: 
                        self.powerup_color = "cyan"

            self.hit_x = self.ziel_x
            self.hit_y = self.ziel_y
            self.ziel_x = float(randint(0 + 40, 770 - 40))
            self.ziel_y = float(randint(100, 300))
            if self.laser_combo >= 4:
                self.score += self.laser_combo
            else: 
                self.score += 3
            if self.laser_combo >=4:
                laser_log_string = "target_hit_combo"
            else:
                laser_log_string = "target_hit"
            self.api.log_event(laser_log_string, self.score)

        if self.hit_timer > 0:
            self.hit_timer -= dt
            self.hit_y -= 40 * dt

        if self.drop_powerup == 1:
            self.powerup_y += self.powerup_speed *dt

        if keys [pygame.K_SPACE] and self.laser_cooldown <= 0:
            self.laser_kann_treffen = True
            self.laser_shot += 1
            self.laser_cooldown = 1.0
            self.laser_timer = 0.15
            self.api.log_event("Shot laser", self.laser_shot)

        if self.laser_timer > 0:
            self.laser_timer -= dt
        if self.laser_cooldown > 0 and self.laser_timer <= 0:
            self.laser_cooldown -= dt

        # Rechteck von rechter oberer Ecke gezeichnet, Ball vom Mittelpunkt aus
        if ball_rect.colliderect(paddle_rect) and self.ball_vy > 0: # >0 sonst wird die Richtung ständig umgekehrt
            self.ball_vy = - abs(self.ball_vy)
            self.score += 1
            self.api.log_event("paddle hit", self.score)

        if keys[pygame.K_LSHIFT]:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.x = 0
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.x = 800 - self.length

        if self.tri_y >= 800:
            self.tri_x = randint(100, 700)
            self.tri_y = randint(0, 200)

        if self.ball_y > 600 or self.ziel_y >= 570 or paddle_rect.colliderect(tri_rect):
            if self.ball_y > 600:
                self.lost_life_x = min(self.ball_x, 690)
                self.api.log_event("lost_life_due_to_ball", self.leben - 1)
            elif self.ziel_y >= 570:
                self.lost_life_x = min(self.ziel_x, 690)
                self.api.log_event("lost_life_due_to_object", self.leben - 1)
            else:
                self.lost_life_x = min(self.tri_x, 690)
                self.api.log_event("lost_life_due_to_spike", self.leben - 1)
            self.ball_x = float(randint(20, 750))
            self.ball_y = float(randint(20, 200))
            self.ball_vx = 250.0
            self.ball_vy = 250.0
            if self.powerup_wkeit == 4: # bei Schwierigkeit 3 Geschwindigkeit höher setzen
                self.speed = 300 * 1.1
            else:
                self.speed = 300.0
            self.stufe = 1
            self.timer = 0.0
            self.leben -= 1
            self.ziel_x = float(randint(0 + 40, 770 - 40))
            self.ziel_y = float(randint(100, 300))
            self.lost_life_timer = 0.8
            self.lost_life_y = 530.0
            self.ziel_speed = 30.0
            self.ziel_vx = 30.0 * choice([-1, 1])
            self.powerup_active = False
            self.powerup_timer = 0.0
            self.drop_powerup = 0
            self.length = 85
            self.tri_x = randint(100, 700)
            self.tri_y = randint(0, 200)
            self.tri_speed = 50.0
            self.tri_length = 30.0
            self.laser_combo = 0
            self.laser_shot = 0
            if self.score > self.highscore:
                self.highscore = self.score
            self.score = 0
            if self.leben <= 0:
                self.api.end_game(self.highscore)

        if self.lost_life_timer > 0:
            self.lost_life_timer -= dt
            self.lost_life_y -= 40 * dt

    # draw new state
    def draw(self, screen: pygame.Surface) -> None:
        screen.fill("black")
        if not self.spiel_gestartet:
            start_ausgabe = self.font2.render("Schwierigkeitsgrad auswählen: \n 1: Leicht \n 2: Mittel \n 3: Schwer \n\nRegeln:\nBall darf den Boden nicht berühren\nLila Ziel muss abgeschossen werden\nPowerup dropt random; kann aufgesammet werden\nDreieckiges Hinderniss darf nicht berührt werden\nSteuerung:\nPfeiltasten l/r oder a/d\nLeertaste für Laser-Schuss\nLSHIFT + Pfeiltasten/a,d für Teleportation in eine Ecke", True, "white")
            start_ausgabe_rect = start_ausgabe.get_rect(center=(400, 300))
            screen.blit(start_ausgabe, start_ausgabe_rect)
        else:
            if self.laser_cooldown > 0 and self.laser_timer <= 0:
                self.paddle_color = "darkred"
            else:
                self.paddle_color = "red"
            pygame.draw.rect(screen, self.paddle_color, (self.x, self.y, self.length, self.height))
            if self.powerup_auswahl == 3 and self.powerup_timer > 0:
                pygame.draw.rect(screen, "cyan", (self.x, self.y, self.length, self.height), 2)
            ball_color = "orange"
            if self.powerup_auswahl == 2 and self.powerup_timer > 0:
                ball_color = "purple"
            pygame.draw.circle(screen, ball_color, (self.ball_x, self.ball_y), 20)
            pygame.draw.rect(screen, "magenta", (self.ziel_x, self.ziel_y, self.ziel_length, 10))

            if self.drop_powerup == 1:
                pygame.draw.circle(screen, self.powerup_color, (self.powerup_x, self.powerup_y), self.radius_powerup)

            if self.laser_timer > 0:
                pygame.draw.rect(screen, "dodgerblue", (self.x + self.length / 2 - 3, 0, 6, self.y))
                pygame.draw.rect(screen, "white", (self.x + self.length / 2 - 1, 0, 2, self.y))
            score_text = self.font.render(f"Score: {self.score}", True, "white")
            highscore_text = self.font.render(f"Highscore: {self.highscore}", True, "white")

            if self.powerup_wkeit != 2:
                pygame.draw.polygon(screen, "crimson", [(self.tri_x, self.tri_y), (self.tri_x + self.tri_length, self.tri_y), (self.tri_x + self.tri_length / 2, self.tri_y + self.tri_length)])
            color_stufe = "green"
            if self.stufe >=4 and self.stufe < 7:
                        color_stufe = "yellow"
            elif self.stufe >= 7 and self.stufe < 10:
                color_stufe = "orange"
            elif self.stufe >= 10:
                color_stufe = "red"
            color_leben = "white"
            if self.leben == 2:
                color_leben = "orange"
            elif self.leben == 1:
                color_leben = "red"
            stufe_text = self.font.render(f"Stufe: {self.stufe}", True, color_stufe)
            leben_anzeige = self.font1.render("❤", True, color_leben)
            for i in range(self.leben):
                screen.blit(leben_anzeige, (640 + i * 50, 5))
            screen.blit(score_text, (10,5))
            screen.blit(highscore_text, (10,35))
            screen.blit(stufe_text, (10,65))
            if self.powerup_active == True:
                timer_text = self.font.render(f"Powerup Timer: {round(self.powerup_timer, 2)}", True, "white")
                screen.blit(timer_text, (300, 5))

            if self.hit_timer > 0:
                if self.laser_combo >= 4:
                    ziel_hit_text = self.font.render(f"Combo! \nScore +{self.laser_combo}", True, "gold")
                else:
                    ziel_hit_text = self.font.render("Score +3", True, "yellow")
                screen.blit(ziel_hit_text, (self.hit_x, self.hit_y))
            if self.lost_life_timer > 0:
                lost_life_text = self.font.render("-1 Leben", True, "red")
                screen.blit(lost_life_text, (self.lost_life_x, self.lost_life_y))