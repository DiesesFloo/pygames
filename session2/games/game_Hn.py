import pygame

# Ein einfaches Spiel (na ja, schon ein sehr einfaches)
# Der Ball kann mit "Pfeil rechts" bewegt werden.

# Erste Erweiterung: Ball wieder (mit Pfeil links) zurück bewegen.

HEIGHT = 600
WIDTH = 800
P_WIDTH = 120
P_HEIGHT = 20
R_BALL = 10

# Fuer Nutzung in der Plattform
GAME_NAME = "Tills pong"

class Game:
    def __init__(self, api):

        # Für Plattform, api-Objekt merken
        self.api = api

        self.x = WIDTH/2
        self.y = HEIGHT*0.25
        self.speedx = 70
        self.speedy = 300
        self.px = WIDTH/2
        self.py = HEIGHT-50
        self.speed = 700.0      # px/s
        self.lifes = 3
        self.points = 0

    def next_life(self):
        self.lifes -= 1
        self.x = WIDTH/2
        self.y = HEIGHT*0.25
        self.speedx = 35
        self.speedy = 150

    # update state
    def update(self, dt: float, keys) -> None:

        # Paddle bewegen
        if keys[pygame.K_RIGHT]:
            self.px = min(self.px+self.speed * dt,WIDTH)
        elif keys[pygame.K_LEFT]:
            self.px = max(self.px-self.speed * dt,0)

        self.x += self.speedx * dt
        self.y += self.speedy * dt

        # Links und rechts abprallen
        if (self.x-R_BALL <= 0):
            self.speedx *= -1
            self.x = R_BALL
        if (self.x+R_BALL >= WIDTH):
            self.speedx *= -1
            self.x = WIDTH - R_BALL

        # und oben
        if (self.y-R_BALL <= 0):
            self.y=R_BALL + 1 # get on the field again
            self.speedy *= -1

        # Paddle trifft Ball
        if (self.y+R_BALL >= self.py):
            if ((self.x >= self.px) and (self.x <= self.px + P_WIDTH)):
                self.y = self.py - R_BALL - 1
                self.speedy *= -1
                self.points += 1


        self.speedx = min(self.speedx*1.001,500)
        self.speedy = min(self.speedy*1.001,500)

        # oder nicht
        if (self.y+R_BALL >= HEIGHT):
            self.api.log_event("life lost", self.points)
            self.next_life()

        if (self.lifes <= 0):
                self.api.end_game(self.points)


    # draw new state
    def draw(self, screen: pygame.Surface) -> None:
        screen.fill("black")
        pygame.draw.rect(screen,"pink",pygame.Rect(self.px,self.py,P_WIDTH,P_HEIGHT))
        pygame.draw.circle(screen, "orange", (self.x, self.y), R_BALL)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            pass
