import pygame

# Ein einfaches Spiel (na ja, schon ein sehr einfaches)
# Der Ball kann mit "Pfeil rechts" bewegt werden.

# Erste Erweiterung: Ball wieder (mit Pfeil links) zurück bewegen.

HEIGHT = 600
WIDTH = 800
P_WIDTH = 120
P_HEIGHT = 20
R_BALL = 10

class Game:
    def __init__(self):
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
            self.next_life()


    # draw new state
    def draw(self, screen: pygame.Surface) -> None:
        screen.fill("black")
        pygame.draw.rect(screen,"pink",pygame.Rect(self.px,self.py,P_WIDTH,P_HEIGHT))
        pygame.draw.circle(screen, "orange", (self.x, self.y), R_BALL)

def main():
    pygame.init()

    # Falls nichts angezeigt wird, die folgenden Zeilen aktivieren, um die SDL- und pygame-Versionen zu prüfen.
    # print("SDL driver:", pygame.display.get_driver())
    # print("pygame:", pygame.version.ver)
    # print("SDL:", pygame.get_sdl_version())

    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    game = Game()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        dt = clock.tick(60) / 2000
        game.update(dt, pygame.key.get_pressed())
        if (game.lifes <= 0):
            running = False
            print(f"Game over !!    {game.points} Punkte")
        game.draw(screen)
        pygame.display.flip()
    pygame.quit()

if __name__ == "__main__":
    main()
