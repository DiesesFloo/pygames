import pygame

# Ein einfaches Spiel (na ja, schon ein sehr einfaches)
# Der Ball kann mit "Pfeil rechts" bewegt werden. 

# Erste Erweiterung: Ball wieder (mit Pfeil links) zurück bewegen.

class Game:
    def __init__(self):
        self.x = 100.0          
        self.speed = 200.0      # px/s

    # update state
    def update(self, dt: float, keys) -> None:
        if keys[pygame.K_RIGHT]:
            self.x += self.speed * dt

    # draw new state
    def draw(self, screen: pygame.Surface) -> None:
        screen.fill("black")
        pygame.draw.circle(screen, "orange", (self.x, 240), 20)

def main():
    pygame.init()

    # Falls nichts angezeigt wird, die folgenden Zeilen aktivieren, um die SDL- und pygame-Versionen zu prüfen.
    # print("SDL driver:", pygame.display.get_driver())
    # print("pygame:", pygame.version.ver)
    # print("SDL:", pygame.get_sdl_version())

    screen = pygame.display.set_mode((800, 600))
    clock = pygame.time.Clock()
    game = Game()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        dt = clock.tick(60) / 1000
        game.update(dt, pygame.key.get_pressed())
        game.draw(screen)
        pygame.display.flip()
    pygame.quit()

if __name__ == "__main__":
    main()
