import pygame
import random
import math

GAME_NAME = "Space Invaders Remix"

DEFAULT_FONT = pygame.font.SysFont("arial", 32)

WIDTH = 800
HEIGHT = 600
E_SIZE = 20
F_SIZE = 5
S_SIZE = 10
SAFE_DIST = E_SIZE+S_SIZE
ENEMY_SPEED = 50

class Game:
    def __init__(self, api):

        self.api = api
        self.x = WIDTH/2          
        self.speed = 250.0      # px/s
        self.shots = []
        self.enemies = [] # coordinates of enemy spaceships resp. asteroids
        self.enemy_speed = ENEMY_SPEED
        self.points = 0
        self.shots_fired = 0
        self.frames = 0

    # calculate position and action for shots
    def move_shots(self,dt):
        self.shots[:] = [
            (x,y-dt*self.speed) 
            for x, y in self.shots 
            if (y+dt*self.speed) >= 0 ]

    def move_enemies(self,dt):
        self.enemies[:] = [
             (x,y+dt*self.enemy_speed) 
             for x, y in self.enemies 
             if (y+dt*self.enemy_speed) >= 0 ]

    def draw_text(self, surface, text, pos, color=(255, 255, 255), font=DEFAULT_FONT):
        font = pygame.font.SysFont("arial", 36)
        text_surface = font.render(str(text), True, (255,255,255))
        surface.blit(text_surface, pos)

    # update state
    def update(self, dt: float, keys) -> None:
        self.frames += 1
        if (random.random() < 0.03):
            self.enemies.append((random.randint(10,WIDTH-50),0 ))

        if keys[pygame.K_RIGHT]:
            self.x += self.speed * dt
            if self.x > WIDTH:
                self.x = WIDTH
        elif keys[pygame.K_LEFT]:
            self.x -= self.speed * dt
            if self.x < 0:
                self.x = 0

        self.move_shots(dt)
        self.move_enemies(dt)

        passing_enemies = [e for e in self.enemies if e[1] >= HEIGHT]
        if (len(passing_enemies) > 0):
            self.api.end_game(self.points)

        # check for collisions of shot and enemy ...
        remaining_shots = []
        for shot in self.shots:
            # Find all enemies that were NOT hit by this shot
            surviving_enemies = [e for e in self.enemies if math.dist(e, shot) >= SAFE_DIST]
            
            # If the list got shorter, this shot hit at least one enemy
            if len(surviving_enemies) < len(self.enemies):
                self.points += (len(self.enemies) - len(surviving_enemies))
                self.enemies = surviving_enemies  # Update enemies (removes hit ones)
            else:
                remaining_shots.append(shot)      # Shot missed, so keep it

        if ((self.frames % 200) == 0):
            self.api.log_event("shots fired", len(self.shots))
            self.enemy_speed *= 1.02
            self.api.log_event("speed increased to",self.enemy_speed)
            if (self.shots_fired > 0): self.api.log_event("hit rate", self.points/self.shots_fired)

        self.shots = remaining_shots
        
        
    # draw new state
    def draw(self, screen: pygame.Surface) -> None:
        screen.fill("black")
        pygame.draw.rect(screen, "red", (self.x, HEIGHT-50,20,20))
        
        for (x,y) in self.shots: 
            pygame.draw.circle(screen, "blue", (x,y), S_SIZE)

        for(x,y) in self.enemies:
            pygame.draw.circle(screen,"white", (x,y),E_SIZE)

        self.draw_text(screen, f"{self.points} points", (10, 20), color=(255, 255, 255))

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            self.shots.append((self.x,550))
            self.shots_fired += 1
