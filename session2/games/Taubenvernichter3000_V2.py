import pygame
from random import randint, choice


GAME_NAME = "Taubenvernichter 3000"
WIDTH = 800
HEIGHT = 600

class Game:
    def __init__(self, api):
        self.api = api
        self.score = 0
        self.crosshair = pygame.image.load("games/TV3000_Assets/TV3000_Crosshair.png").convert_alpha()
        self.crosshair = pygame.transform.smoothscale(self.crosshair, (40, 40))
        self.cloud = pygame.image.load("games/TV3000_Assets/TV3000_Cloud.png").convert_alpha()
        self.cloud = pygame.transform.smoothscale(self.cloud, (WIDTH+200, HEIGHT))
        self.sfx_shot = pygame.mixer.Sound("games/TV3000_Assets/Shot.ogg")
        self.sfx_hit = pygame.mixer.Sound("games/TV3000_Assets/Pigeon_Hit_V2.ogg")
        self.sfx_hit_sheep = pygame.mixer.Sound("games/TV3000_Assets/Sheep_Hit.ogg")
        self.sfx_lose = pygame.mixer.Sound("games/TV3000_Assets/Game_Over.ogg")
        pygame.mouse.set_visible(False)
        timer = pygame.time.set_timer(pygame.USEREVENT, 1000)
        pig1 = Pigeon()
        pig2 = Pigeon()
        pig3 = Pigeon()
        pig4 = Pigeon()
        pig5 = Pigeon()
        pig6 = Pigeon()

        sheep1 = Sheep()
        sheep2 = Sheep()
        sheep3 = Sheep()
        sheep4 = Sheep()
        sheep5 = Sheep()
        sheep6 = Sheep()

        self.end = False
        self.seconds = 0

        self.pigeons = [pig1, pig2, pig3, pig4, pig5, pig6]
        self.sheeps = [sheep1, sheep2, sheep3, sheep4, sheep5, sheep6]
        self.incre = 2

        #TelemetrieDaten
        self.deadsheep = 0
        self.shots = 0
        self.hits = 0
        self.lives = 6
        self.font = pygame.font.SysFont("Arial", 40)
        self.api.log_event("Spielbeginn")


    def handle_event(self, event):
        if event.type==pygame.USEREVENT:
            self.seconds += 1
            x = 0
            for sheep in self.sheeps:
                if sheep.shot == True or sheep.pos_y < 50:
                    x += 1

            if x == 6:
                self.sfx_lose.play()
                self.api.end_game(score=self.hits)

            
            for pigeon in self.pigeons:
                if pigeon.active == False:
                    pigeon.active = True
                    if self.lives > 0:
                        pigeon.spawn(self.sheeps, self.incre)
                    else: 
                        self.end = True
                    break
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.shots += 1
            self.api.log_event("Schüsse:", self.shots)
            self.sfx_shot.play()
            for sheep in self.sheeps:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                if( sheep.pos_x < mouse_x < sheep.pos_x + sheep.sheep.get_width() and sheep.pos_y < mouse_y < sheep.pos_y + sheep.sheep.get_height() and mouse_y > 110 and sheep.shot == False):
                    sheep.shot = True
                    sheep.raptured = True
                    self.sfx_hit_sheep.play()
                    self.hits += 1
                    self.deadsheep += 1
                    self.api.log_event("Treffer:", self.hits)
                    if self.hits != 0 and self.hits % 10 == 0:
                        self.incre += 1
            for pigeon in self.pigeons:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                if( pigeon.pos_x < mouse_x < pigeon.pos_x + pigeon.pigeon.get_width() and pigeon.pos_y < mouse_y < pigeon.pos_y + pigeon.pigeon.get_height() and mouse_y > 110 and pigeon.active == True):
                    pigeon.kill()
                    self.sfx_hit.play()
                    self.hits += 1
                    self.api.log_event("Treffer:", self.hits)
                    if self.hits != 0 and self.hits % 10 == 0:
                        self.incre += 1
            
                



    def update(self, dt, keys):
        r = 0
        pos_gesamt = 0
        for sheep in self.sheeps:
            pos_gesamt += sheep.pos_y
            if self.end == True and pos_gesamt < 6 * 100:
                self.api.log_event("Ende")
                self.api.log_event("Schüsse gesamt: ", self.shots )
                self.api.log_event("Treffer gesamt: ", self.hits)
                if self.shots == 0:
                    self.api.log_event("Genauigkeit: ", 0)
                else:
                    self.api.log_event("Genauigkeit: ", self.hits/self.shots)
                self.api.log_event("Spielzeit in Sekunden: ", self.seconds)
                #self.api.end_game(score=self.hits)
            if sheep.raptured == False:
                r += 1
        self.lives = r

    def showScore(self, screen):
        score_text = f"Punkte: {self.hits}"
        text_surface = self.font.render(score_text, True, "Black")
        screen.blit(text_surface, (WIDTH - text_surface.get_width()- 10, 10))

    def drawCrosshair(self, screen):
        mouse_x, mouse_y = pygame.mouse.get_pos()
        if pygame.mouse.get_focused() != 0:
            screen.blit(self.crosshair, (mouse_x - (self.crosshair.get_width() / 2), mouse_y - (self.crosshair.get_height() / 2)))

    def draw(self, screen):
        screen.fill((135, 206, 235))
        screen.fill((34, 139, 34), rect=(0, (HEIGHT * 0.75), WIDTH, (HEIGHT * 0.25)))
        for sheep in self.sheeps:
            sheep.draw(screen)

        for pigeon in self.pigeons: 
                pigeon.draw(screen, self.sheeps, self.incre)

        screen.blit(self.cloud, (-100, -1*HEIGHT+110))
        self.drawCrosshair(screen)
        self.showScore(screen)
    


class Pigeon:
    def __init__(self):
        self.pigeon = pygame.image.load("games/TV3000_Assets/TV3000_Pigeon.png").convert_alpha()
        self.pigeon = pygame.transform.smoothscale(self.pigeon, (60, 70))
        self.blood = pygame.image.load("games//TV3000_Assets//TV3000_Blutnebel.png").convert_alpha()
        self.blood = pygame.transform.smoothscale(self.blood, (60, 70))
        self.sfx_spawn = pygame.mixer.Sound("games/TV3000_Assets/Spawn.ogg")
        self.sfx_rapture = pygame.mixer.Sound("games/TV3000_Assets/Sheep_Rapture.ogg")
        self.pos_x = 0
        self.pos_y = 0
        self.active = False
        self.ziel = None
        self.vec_x = 0
        self.vec_y = 400
        self.steigung = 0
        self.speed = 0

    def richtungGeben(self, incre):
        self.steigung_y = self.ziel.pos_y - self.pos_y
        self.steigung_x = self.ziel.pos_x - self.pos_x
        if self.steigung_x == 0:
            self.steigung_x += 0.1
        self.steigung = self.steigung_y / self.steigung_x
        self.speed = abs((self.ziel.pos_x - self.pos_x) / WIDTH * incre)


    def spawn(self, sheeps, incre):
        self.sfx_spawn.play()
        self.zielSuchen(sheeps)
        self.pos_x, self.pos_y = randint(30, WIDTH - 30), 0
        self.richtungGeben(incre)
        

    def zielSuchen(self, sheeps):
        x = 0
        for sheep in sheeps:
            if sheep.shot == True or sheep.pos_y < 50:
                x += 1
        self.ziel = choice(sheeps)
        if self.ziel.raptured == True and x < 5:
            self.zielSuchen(sheeps)

    def move(self, ziel, sheeps, incre):
        dis_x = abs(ziel.pos_x - self.pos_x) 
        dis_y = abs(ziel.pos_y - self.pos_y)         
        if ziel.raptured == True and (dis_x > 10 and dis_y > 10):
            self.zielSuchen(sheeps)
            self.richtungGeben(incre)
        if (dis_x >= 2 or dis_y >= 6) and self.active == True:
            if ziel.pos_x > self.pos_x:
                self.pos_x += 1 * self.speed
            else:
                self.pos_x -= 1 * self.speed
        else:
            if not ziel.played:
                self.sfx_rapture.play()
                ziel.played = True
            ziel.raptured = True
            ziel.rapture(self.pos_y)
            self.pos_y -= 6
            if self.pos_y < 0:
                self.kill()

        self.pos_y += abs(self.steigung) * self.speed

    def draw(self, screen, sheeps, incre):
        if self.active == True:
            screen.blit(self.pigeon, (self.pos_x, self.pos_y))
            self.move(self.ziel, sheeps, incre)
            if self.pos_y > HEIGHT:
                self.kill()
        else:
            screen.blit(self.blood, (self.pos_x, self.pos_y))

    def kill(self):
        self.active = False
        # blutnebel
    

        
class Sheep:
    def __init__(self):
        self.sheep = pygame.image.load("games/TV3000_Assets/TV3000_Sheep.png").convert_alpha()
        self.sheep = pygame.transform.smoothscale(self.sheep, (60, 70))
        self.blood = pygame.image.load("games//TV3000_Assets//TV3000_Blutnebel.png").convert_alpha()
        self.blood = pygame.transform.smoothscale(self.blood, (60, 70))
        self.pos_x = randint(50, WIDTH - 50)
        self.pos_y = randint(480, 530)
        self.raptured = False
        self.shot = False
        self.played = False

    def rapture(self, pig_y):
        self.pos_y = pig_y
        
    def draw(self, screen):
        if self.shot == False:
            screen.blit(self.sheep, (self.pos_x, self.pos_y))
        else:
            screen.blit(self.blood, (self.pos_x, self.pos_y))


        
