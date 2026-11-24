import pygame
from pygame.surface import Surface
import random

GAME_NAME = "BetterTetris"
SCREEN_HEIGHT = 600
SCREEN_WIDTH = 800
MAX_LEVEL = 9
HEIGHT = 20
WIDTH = 10
BLOCK_SIZE = SCREEN_HEIGHT // HEIGHT
X_ZERO = SCREEN_WIDTH//2-((WIDTH//2)*BLOCK_SIZE)
POINTS = [10, 100, 250, 500, 700]
HUD_X = SCREEN_WIDTH // 80
HUD_TOP = SCREEN_HEIGHT // 60
HUD_LINE_HEIGHT = SCREEN_HEIGHT // 15
HUD_FONT_SIZE = SCREEN_HEIGHT // 18
FALL_MODULO = 3

class MovingPiece(): 
    def __init__(self, piece:list[list[str | None]], x: int, y: int) -> None: 
        self.piece = piece 
        self.x = x 
        self.y = y 

    def rotate_clockwise(self) -> None:
        self.piece = [list(row) for row in zip(*self.piece[::-1])]

    def rotate_counter_clockwise(self) -> None:
        self.piece = [list(row) for row in zip(*self.piece)][::-1]


    def set_piece(self, piece:list[list[str | None]]) -> None: 
        self.piece = piece 

class Canvas: 
    def __init__(self) -> None:
        self.canvas_m: list[list[str | None]] = [[None for _ in range(WIDTH)] for _ in range(HEIGHT)]

    def get(self, x: int, y: int) -> str | None: 
        return self.canvas_m[y][x]

    def set(self, x: int, y: int, value: str | None) -> None: 
        self.canvas_m[y][x] = value

    def is_collided(self, piece: MovingPiece) -> bool: 
        if self.is_on_floor(piece): 
                    return True 

        if self.collides_with_canvas(piece): 
            return True 

        return False 

    def collides_with_canvas(self, piece: MovingPiece): 
        for y in range(len(piece.piece)): 
            for x in range(len(piece.piece[y])): 
                item = piece.piece[y][x]
                if not item: 
                    continue
                try:
                    if self.canvas_m[piece.y + y][piece.x + x]:
                        return True
                except IndexError:
                    return True 
        return False 
                        
    def is_on_floor(self, piece: MovingPiece) -> bool: 
        return ((piece.y + len(piece.piece)) > HEIGHT)

    def merge(self, piece: MovingPiece) -> int: 
        for y in range(len(piece.piece)): 
            for x in range(len(piece.piece[y])): 
                item = piece.piece[y][x]
                if item: 
                    self.canvas_m[piece.y + y][piece.x + x] = item

        return self.check_lines()

    def check_lines(self) -> int: 
        count = 0 
        for i in range(len(self.canvas_m)):
            if self.canvas_m[i].count(None) != 0:
                continue

            count += 1 
            self.canvas_m.pop(i)
            self.canvas_m.insert(0, [None for _ in range(WIDTH)])
        return count
                

class Game:
    def __init__(self, api):
        self.api = api
        self.score = 0
        self.level = 1 
        self.lines = 0 
        self.font = pygame.font.Font(None, HUD_FONT_SIZE)

        self.counter = 0 

        self.key_pressed = False

        self.canvas: Canvas = Canvas()
        self.init_pieces()

        self.cur_mov = self.new_peace()

    def init_pieces(self): 
        self.def_peaces:list[list[str | None]] = [
            [
                [None, None, "Orange"],
                ["Orange", "Orange", "Orange"],
            ],  # L-Stein
            [
                ["Blue", None, None],
                ["Blue", "Blue", "Blue"],
            ],  # J-Stein
            [
                ["Cyan", "Cyan", "Cyan", "Cyan"],
            ],  # I-Stein
            [
                ["Yellow", "Yellow"],
                ["Yellow", "Yellow"],
            ],  # O-Stein
            [
                [None, "Purple", None],
                ["Purple", "Purple", "Purple"],
            ],  # T-Stein
            [
                [None, "Green", "Green"],
                ["Green", "Green", None],
            ],  # S-Stein
            [
                ["Red", "Red", None],
                [None, "Red", "Red"],
            ],  # Z-Stein
        ]

    def handle_event(self, event):
        self.handle_move_events(event)

    def handle_move_events(self, event) -> None:
        if event.type != pygame.KEYDOWN: 
            return 

        if (event.key == pygame.K_LEFT or event.key == pygame.K_a) and self.cur_mov.x > 0: 
            self.cur_mov.x -= 1
            if self.canvas.is_collided(self.cur_mov): 
                self.cur_mov.x += 1 

        if (event.key == pygame.K_RIGHT or event.key == pygame.K_d) and self.cur_mov.x + len(self.cur_mov.piece[0]) < WIDTH: 
            self.cur_mov.x += 1 
            if self.canvas.is_collided(self.cur_mov): 
                self.cur_mov.x -= 1 

        if (event.key == pygame.K_SPACE) or (event.key == pygame.K_UP) or (event.key == pygame.K_w):
            self.cur_mov.rotate_clockwise()
            if self.canvas.is_collided(self.cur_mov): 
                self.cur_mov.rotate_counter_clockwise()

        

    def update(self, dt, keys):
        if self.counter % self.get_current_speed_modulo(keys) == 0: 
            self.cur_mov.y += 1 
            if(self.canvas.is_collided(self.cur_mov)):    
                self.cur_mov.y -= 1
                lines = self.canvas.merge(self.cur_mov)
                self.lines += lines 
                self.score += POINTS[lines]
                self.cur_mov = self.new_peace()
                self.check_game_over()
                self.update_level()
            self.counter = 0 

        self.counter += 1 

    def update_level(self) -> None: 
        if self.level >= MAX_LEVEL: 
            return 

        self.level = (self.lines//10) + 1 

    def get_current_speed_modulo(self, keys) -> int: 
        if keys[pygame.K_DOWN] or keys[pygame.K_s]: 
            return FALL_MODULO

        return 20 - (self.level-1)


    def check_game_over(self): 
        if not self.canvas.is_collided(self.cur_mov):
            return 

        self.api.end_game(score=self.score)

    def new_peace(self) -> MovingPiece: 
        return MovingPiece(random.choice(self.def_peaces), WIDTH//2, 0)

    def draw(self, screen: Surface):
        screen.fill("#555555")
        self.draw_labels(screen)
        self.draw_canvas(screen)
        self.draw_moving_block(screen)

    def draw_labels(self, screen: Surface):
        score_text = self.font.render(f"Score: {self.score}", True, "White")
        level_text = self.font.render(f"Level: {self.level}", True, "White")
        lines_text = self.font.render(f"Lines: {self.lines}", True, "White")
        screen.blit(score_text, (HUD_X, HUD_TOP))
        screen.blit(level_text, (HUD_X, HUD_TOP + HUD_LINE_HEIGHT))
        screen.blit(lines_text, (HUD_X, HUD_TOP + HUD_LINE_HEIGHT * 2))

    def draw_canvas(self, screen: Surface):
        for x in range(WIDTH):
            for y in range(HEIGHT): 
                item = self.canvas.get(x, y)
                if item: 
                    self.draw_block(screen, item, x, y)
                else:
                    self.draw_block(screen, "Black", x, y)

    def draw_moving_block(self, screen:Surface): 
        for y in range(len(self.cur_mov.piece)):
            for x in range(len(self.cur_mov.piece[y])): 
                item = self.cur_mov.piece[y][x] 
                if item: 
                    self.draw_block(screen, item, self.cur_mov.x + x, self.cur_mov.y + y)

    def draw_block(self, screen:Surface, color: str, x: int, y: int): 
        pygame.draw.rect(screen, color, ((X_ZERO + (x*BLOCK_SIZE)), y*BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE))