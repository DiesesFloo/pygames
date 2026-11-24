
import pygame
from random import randint, choice

GAME_NAME = "2048"

# Fenstergröße auf 800 x 600 Pixel festlegen
BREITE = 800
HOEHE = 600


rect_breite = 120
rect_hoehe = 120

class Game:
    def __init__(self, api):
        self.api = api

        self.value_matrix = Rects()
        self.rects = []
        self.fill_rects()
        self.font = pygame.font.Font(None, 48)
        self.colors = {
            0:   "#E6E1D6",  
            2:   "#CDE7F0",  
            4:   "#FDE2B8",  
            8:   "#F7B267",  
            16:  "#F79256",  
            32:  "#F25C54",  
            64:  "#D64045",  
            128: "#2A9D8F",  
            256: "#1D6373"  
        }

        #score
        self.score = 0
        self.moves = 0
        self.score_rect = pygame.Rect(650, 25, 100, 50)
        self.score_value_rect = pygame.Rect(675, 75, 100, 50)
        self.moves_rect = pygame.Rect(650, 125, 100, 50)
        self.move_value_rect = pygame.Rect(675, 175, 100, 50)


        #animation
        self.animations = []
        self.anim_step = 0
        self.anim_max_steps = 10   # Dauer: 10 Frames (ca. 0,16 Sek. bei 60 FPS)
        self.pending_score = 0
    def update(self, dt, keys):
        pass
        
       

    def fill_rects(self):
        for zeile in range(4):
            zeilen_liste = []  # Neue Liste für diese Zeile erstellen

            for spalte in range(4):
                x = 25 + spalte * (rect_breite + 25)
                y = 25 + zeile * (rect_hoehe + 25)

                zeilen_liste.append(pygame.Rect(x, y, rect_breite, rect_hoehe))
            self.rects.append(zeilen_liste)
    def handle_event(self, event):
            if self.animations:
                return
            
            if event.type == pygame.KEYDOWN:
                ergebnis = None
                if event.key == pygame.K_LEFT:
                    ergebnis = self.value_matrix.update("left")
                    self.api.log_event("move_left", self.score)
                    print(self.value_matrix.max_value)

                elif event.key == pygame.K_RIGHT:
                    self.value_matrix.spiegeln()
                    ergebnis = self.value_matrix.update("left")
                    self.value_matrix.spiegeln()
                    if ergebnis != "game_end":
                        score, anims = ergebnis
                        ergebnis = (score, [(w, sr, 3 - sc, zr, 3 - zc) for w, sr, sc, zr, zc in anims])
                    self.api.log_event("move_right", self.score)

                elif event.key == pygame.K_UP:
                    self.value_matrix.transponieren()
                    ergebnis = self.value_matrix.update("left")
                    self.value_matrix.transponieren()
                    # Zeilen und Spalten für die Animation wieder zurücktauschen
                    if ergebnis != "game_end":
                        score, anims = ergebnis
                        ergebnis = (score, [(w, sc, sr, zc, zr) for w, sr, sc, zr, zc in anims])
                    self.api.log_event("move_up", self.score)
                elif event.key == pygame.K_DOWN:
                    self.value_matrix.transponieren()
                    self.value_matrix.spiegeln()
                    ergebnis = self.value_matrix.update("left")
                    self.value_matrix.spiegeln()
                    self.value_matrix.transponieren()
                    # Erst zurückspiegeln (3 - c), dann zurücktauschen
                    if ergebnis != "game_end":
                        score, anims = ergebnis
                        ergebnis = (score, [(w, 3 - sc, sr, 3 - zc, zr) for w, sr, sc, zr, zc in anims])
                    self.api.log_event("move_down", self.score)

                if ergebnis == "game_end":
                        print(f"Game Over, Score: {self.score}")
                        self.api.log_event("moves", self.moves)
                        self.api.log_event("highest_value", self.value_matrix.max_value)
                        self.api.end_game(self.score)
                elif ergebnis is not None:
                        
                        new_score, animations = ergebnis
                        if animations:
                            self.moves += 1
                            self.animations = animations
                            self.anim_step = 1
                            self.pending_score = new_score
                


    def draw(self, screen: pygame.Surface):
        screen.fill("brown")

        for row in self.rects:
            for rect in row:
                pygame.draw.rect(screen, "beige", rect, border_radius=15)

        if self.animations:
            t = self.anim_step / self.anim_max_steps
            t = 1 - (1 - t) ** 3 

            for wert, sr, sc, zr, zc in self.animations:
                start_rect = self.rects[sr][sc]
                ziel_rect = self.rects[zr][zc]

                aktuelles_x = start_rect.x + (ziel_rect.x - start_rect.x) * t
                aktuelles_y = start_rect.y + (ziel_rect.y - start_rect.y) * t

                bewegtes_rect = pygame.Rect(aktuelles_x, aktuelles_y, rect_breite, rect_hoehe)
                farbe = self.colors.get(wert, "#1D6373")
                pygame.draw.rect(screen, farbe, bewegtes_rect, border_radius=15)

                text_surface = self.font.render(str(wert), True, "black")
                text_rect = text_surface.get_rect(center=bewegtes_rect.center)
                screen.blit(text_surface, text_rect)

            self.anim_step += 1


            if self.anim_step > self.anim_max_steps:
                self.animations = []
                self.anim_step = 0
                self.score += self.pending_score
                self.pending_score = 0
                self.value_matrix.spawn_new_2()


        else:
            for row1, row2 in zip(self.rects, self.value_matrix.values):
                for rect, value in zip(row1, row2):
                    if value != 0:
                        pygame.draw.rect(screen, self.colors.get(value, "#1D6373"), rect, border_radius=15)
                        text_surface = self.font.render(str(value), True, "black")
                        text_rect = text_surface.get_rect(center=rect.center)
                        screen.blit(text_surface, text_rect)


        pygame.draw.rect(screen, "brown", self.score_rect)
        text_score = self.font.render("Score", True, "beige")
        screen.blit(text_score, (self.score_rect.x + 10, self.score_rect.y + 10))
        pygame.draw.rect(screen, "brown", self.score_value_rect)
        text_score_value = self.font.render(f"{self.score}", True, "beige")
        screen.blit(text_score_value, (self.score_value_rect.x + 10, self.score_value_rect.y + 10))
        pygame.draw.rect(screen, "brown", self.moves_rect)
        text_moves = self.font.render("Moves", True, "beige")
        screen.blit(text_moves, (self.moves_rect.x + 10, self.moves_rect.y + 10))
        pygame.draw.rect(screen, "brown", self.move_value_rect)
        text_move_value = self.font.render(f"{self.moves}", True, "beige")
        screen.blit(text_move_value, (self.move_value_rect.x + 10, self.move_value_rect.y + 10))


class Rects: 
    def __init__(self):
        self.values = [[0, 0, 0, 0],
                      [0, 0, 2, 0],
                      [0, 0, 0, 0],
                      [0, 2, 0, 0]]

        self.max_value = 2
    def spawn_new_2(self): 
        zeros = []
        for i in range(4): 
            for j in range(4):
                if self.values[i][j] == 0: 
                    zeros.append({"i": i,
                                  "j": j})
        new_2 = choice(zeros)
        self.values[new_2["i"]][new_2["j"]] = 2

    def update(self, keys):
        alte_matrix = [zeile[:] for zeile in self.values]
        animations = []

        if keys == "left":
            score = 0
            for r, row in enumerate(self.values):
                i = 0
                original_row = row
                result = []
                # Wert und Start-Spalte c merken
                row = [(value, c) for c, value in enumerate(row) if value != 0]

                while i < len(row):
                    ziel_c = len(result)
                    if i + 1 < len(row) and row[i][0] == row[i+1][0]:
                        result.append(row[i][0] * 2)
                        score += row[i][0] * 2
                        if self.max_value < row[i][0] * 2:
                            self.max_value = row[i][0] * 2
                            
                        animations.append((row[i][0], r, row[i][1], r, ziel_c))
                        animations.append((row[i+1][0], r, row[i+1][1], r, ziel_c))
                        i += 2
                    else:
                        result.append(row[i][0])
                        animations.append((row[i][0], r, row[i][1], r, ziel_c))
                        i += 1

                while len(result) < 4:
                    result.append(0)
                original_row[:] = result

        if self.values != alte_matrix:
            return score, animations
        if self.full():
            return "game_end"
        else: 
            return 0, []

    def full(self):
        for i in range(4):
            for j in range(4): 
                if self.values[i][j] == 0:
                    return False 
                if j + 1 < 4 and self.values[i][j] == self.values[i][j + 1]:
                    return False
                if i + 1 < 4 and self.values[i][j] == self.values[i + 1][j]:
                    return False
        return True
    
    def transponieren(self):
        transponiert = []
        for row in zip(*self.values):
            transponiert.append(list(row))
        self.values = transponiert

    def spiegeln(self):
        for i in range(len(self.values)):
            self.values[i] = self.values[i][::-1]
        

                        
                    
        


        


        




