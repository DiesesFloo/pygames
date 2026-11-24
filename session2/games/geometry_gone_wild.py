import pygame
import random
import time
from pathlib import Path

GAME_NAME = "Geometry Gone Wild"

WIDTH = 800
HEIGHT = 600
BACKGROUND = "black"
TEXT_COLOUR = "white"

class Game:
    def __init__(self, api):

        # Für Plattform, api-Objekt merken
        self.api = api
        self.basket()
        self.ball()
        self.triangle()
        self.square()
        self.diamond()
        self.ball_var()
        self.larger()
        self.pace_ball()
        self.timer()
        self.lives = 3
        self.score = 0
        
        self.game_start_time = None
        self.game_end_time = None
        self.play_time = 0.0
        
        self.game_start = False
        self.game_over = False
        
        self.font_start_info = pygame.font.SysFont("Bahnschrift", 18)
        self.font_start_direc = pygame.font.SysFont("Bahnschrift", 15)
        self.font_end_info = pygame.font.SysFont("Bahnschrift", 24)
        
        self.font_score = pygame.font.SysFont("Bahnschrift", 36)
        self.font_game_over = pygame.font.SysFont("Algerian", 50)
        
        game_folder = Path(__file__).parent
        
        hearts_length = (40, 40)
        
        # Herzbilder laden
        self.heart = pygame.image.load(game_folder / "heart.png").convert_alpha()
        self.heart_empty = pygame.image.load(game_folder / "heart_empty.png").convert_alpha()
        self.heart = pygame.transform.smoothscale(self.heart, hearts_length)
        self.heart_empty = pygame.transform.smoothscale(self.heart_empty, hearts_length)
       

    def update(self, dt: float, keys) -> None:
        
        if self.game_over:
            return
        
        if self.game_start == False:
            return
            
        
        # basket nach  rechts
        if keys[pygame.K_RIGHT]:
            self.basket_x += self.basket_speed * dt
        
        # basket nach links
        if keys[pygame.K_LEFT]:
            self.basket_x -= self.basket_speed * dt

        # basket nicht nach rechts oder links aus Bildschirm
        if self.basket_x < 0 :
            self.basket_x = 0
        if self.basket_x + self.basket_width >= WIDTH:
            self.basket_x = WIDTH - self.basket_width
    
        # Ball runter
        self.update_balls(dt)

        # Dreieck runter
        self.update_triangles(dt)

        # Viereck runter
        self.update_squares(dt)

        self.update_diamonds(dt)
        
        self.update_balls_var(dt)
        
        self.update_larger_ob(dt)
        
        self.update_pace_ball(dt)
                
# basket
    def basket(self):
        self.basket_width = 100
        self.basket_height = 10
        self.basket_x = WIDTH/2 - self.basket_width/2
        self.basket_y = HEIGHT - self.basket_height - 40
        self.basket_speed = 400.0

# Ball
    def ball(self):
        self.ball_colour = "#3826d9"
        self.balls = []
        self.ball_timer = 0.0
        self.ball_radius = 20 
        self.ball_x = random.randint(self.ball_radius, WIDTH - self.ball_radius)
        self.ball_y = -self.ball_radius
        self.ball_speed = 100

    def update_balls(self, dt):
        self.ball_timer -= dt
        if self.ball_timer <= 0:
            self.balls.append({
                "x": random.randint(self.ball_radius, WIDTH - self.ball_radius),
                "y": self.ball_y,
                "vy": self.ball_speed
            })
            self.ball_timer = random.uniform(1, 3)

        for ball in self.balls:
            ball["y"] += ball["vy"] * dt

        remaining = []
        for ball in self.balls:
            bottom = ball["y"] + self.ball_radius
            hit = (self.basket_x <= ball["x"] <= self.basket_x + self.basket_width and self.basket_y <= bottom <= self.basket_y + self.basket_height) 
            if hit:
                self.score += 1
                self.api.log_event("ball_caught", self.score)
            elif ball["y"] < HEIGHT:
                remaining.append(ball)
        self.balls = remaining

# Dreick 
    def triangle(self):
        self.triangles = []
        self.triangle_colour = "#3826d9"
        self.triangle_timer = 0.0
        self.triangle_size = 40  
        self.triangle_speed = 200

    def get_triangle_points(self, cx, cy):
        half = self.triangle_size / 2
        return [
            (cx, cy + half),         # Spitze unten
            (cx - half, cy - half),  # Unten links
            (cx + half, cy - half),  # Unten rechts
        ]

    def update_triangles(self, dt):
        self.triangle_timer -= dt
        if self.triangle_timer <= 0:
            spawn_x = random.randint(self.triangle_size // 2, WIDTH - self.triangle_size // 2)
            spawn_y = -self.triangle_size // 2
            self.triangles.append({
                "x": spawn_x,
                "y": spawn_y,
                "vy": self.triangle_speed
            })
            self.triangle_timer = random.uniform(1, 8)

        for tri in self.triangles:
            tri["y"] += tri["vy"] * dt

        remaining = []
        for tri in self.triangles:
            punkte = self.get_triangle_points(tri["x"], tri["y"])
            bottom = max(p[1] for p in punkte)
            left = min(p[0] for p in punkte)
            right = max(p[0] for p in punkte)

            # Treffer, wenn das Dreieck den basket berührt (Mitte oder horizontale Überschneidung)
            hit = (
                right >= self.basket_x
                and left <= self.basket_x + self.basket_width
                and self.basket_y <= bottom <= self.basket_y + self.basket_height
            )

            if hit:
                self.score += 2
                self.api.log_event("triangle_caught", self.score)
            elif tri["y"] < HEIGHT:
                remaining.append(tri)

        self.triangles = remaining

# Viereck
    def square(self):
        self.squares = []
        self.square_colour = "#3826d9"
        self.square_timer = 0.0
        self.square_width = 40  
        self.square_height = self.square_width
        self.square_x = random.randint(0, WIDTH - self.square_width)
        self.square_y = -self.square_height
        self.square_speed = 300

    def update_squares(self, dt):
        self.square_timer -= dt
        if self.square_timer <= 0:
            self.squares.append({
                "x": random.randint(0, WIDTH - self.square_width),
                "y": self.square_y,
                "vy": self.square_speed
            })
            self.square_timer = random.uniform(1, 12)

        for sq in self.squares:
            sq["y"] += sq["vy"] * dt

        remaining = []
        for sq in self.squares:
            rect = pygame.Rect(sq["x"], sq["y"], self.square_width, self.square_height)
        
            hit = (
                rect.right >= self.basket_x
                and rect.left <= self.basket_x + self.basket_width
                and self.basket_y <= rect.bottom <= self.basket_y + self.basket_height
            )

            if hit:
                self.score += 4
                self.api.log_event("square_caught", self.score)
            elif sq["y"] < HEIGHT:
                remaining.append(sq)

        self.squares = remaining

# Raute
    def diamond(self):
        self.diamonds = []
        self.diamond_colour = "#d9266e"
        self.diamond_timer = 0.0
        self.diamond_size = 60  
        self.diamond_speed = 200

    def get_diamond_points(self, cx, cy):
        half = self.diamond_size / 2
        return [
            (cx, cy - half),        # Oben
            (cx + half, cy),        # links
            (cx, cy + half),        # Unten
            (cx - half, cy),        # rechts
        ]

    def update_diamonds(self, dt):
        self.diamond_timer -= dt
        if self.diamond_timer <= 0:
            spawn_x = random.randint(self.diamond_size // 2, WIDTH - self.diamond_size // 2)
            spawn_y = -self.diamond_size // 2
            self.diamonds.append({
                "x": spawn_x,
                "y": spawn_y,
                "vy": self.diamond_speed
            })
            self.diamond_timer = random.uniform(1, 5)

        for diamond in self.diamonds:
            diamond["y"] += diamond["vy"] * dt

        remaining = []
        for diamond in self.diamonds:
            diamond_punkte = self.get_diamond_points(diamond["x"], diamond["y"])
            bottom = max(p[1] for p in diamond_punkte)
            left = min(p[0] for p in diamond_punkte)
            right = max(p[0] for p in diamond_punkte)

            hit = (
                right >= self.basket_x
                and left <= self.basket_x + self.basket_width
                and self.basket_y <= bottom <= self.basket_y + self.basket_height
            )

            if hit:
                self.lives -= 1
                # Verhindert negative Leben
                if self.lives < 0:
                    self.lives = 0

                self.api.log_event("life_lost", self.lives)

                if self.lives == 0:
                    self.game_over = True
                    self.game_end_time = time.perf_counter()

                    self.play_time = self.game_end_time - self.game_start_time

                    self.api.log_event("play_time_seconds", round(self.play_time, 2))
                                    
            elif diamond["y"] < HEIGHT:
                remaining.append(diamond)

            self.diamonds = remaining

# Ball, der den basket größer oder kleiner macht 
    def ball_var(self):
        self.balls_var = []
        self.ball_colour_var = "#9a26d9"
        self.ball_timer_var = 0.0
        self.ball_radius_var = 10 
        self.ball_x_var = random.randint(self.ball_radius_var, WIDTH - self.ball_radius_var)
        self.ball_y_var = -self.ball_radius_var
        self.ball_speed_var = 400

    def update_balls_var(self, dt):
        self.ball_timer_var -= dt
        if self.ball_timer_var <= 0:
            self.balls_var.append({
                "x": random.randint(self.ball_radius_var, WIDTH - self.ball_radius_var),
                "y": self.ball_y_var,
                "vy": self.ball_speed_var
            })
            self.ball_timer_var = random.uniform(1, 15)

        for ball_var in self.balls_var:
            ball_var["y"] += ball_var["vy"] * dt

        remaining = []
        for ball_var in self.balls_var:
            bottom = ball_var["y"] + self.ball_radius_var
            hit = (self.basket_x <= ball_var["x"] <= self.basket_x + self.basket_width and self.basket_y <= bottom <= self.basket_y + self.basket_height) 
            if hit:
                change = random.choice([10, -10, 20, -20, 30, 40]) 
                self.basket_width = max(20, min(200, self.basket_width + change))
                self.api.log_event("basket_width_changed", self.basket_width)
            elif ball_var["y"] < HEIGHT:
                remaining.append(ball_var)
        self.balls_var = remaining

# Ball, der Objekte größer macht (außer Rauten) 
    def larger(self):
        self.larger_ob = []
        self.larger_colour = "#c7d926"
        self.larger_timer = 0.0
        self.larger_radius = 10 
        self.larger_x = random.randint(self.larger_radius, WIDTH - self.larger_radius)
        self.larger_y = -self.larger_radius
        self.larger_speed = 400

    def update_larger_ob(self, dt):
        self.larger_timer -= dt
        if self.larger_timer <= 0:
            self.larger_ob.append({
                "x": random.randint(self.larger_radius, WIDTH - self.larger_radius),
                "y": self.larger_y,
                "vy": self.larger_speed
            })
            self.larger_timer = random.uniform(1, 15)

        for larger in self.larger_ob:
            larger["y"] += larger["vy"] * dt

        remaining = []
        for larger in self.larger_ob:
            bottom = larger["y"] + self.larger_radius
            hit = (
                self.basket_x <= larger["x"] <= self.basket_x + self.basket_width
                and self.basket_y <= bottom <= self.basket_y + self.basket_height
            )
            if hit:
                self.triangle_size = min(70, self.triangle_size + 10)
                self.square_width = min(70, self.square_width + 10)
                self.square_height = min(70, self.square_height + 10)
                self.ball_radius = min(40, self.ball_radius + 10)
                self.large_timer = 5.0
                self.api.log_event("objects_enlarged", 1)
            elif larger["y"] < HEIGHT:
                remaining.append(larger)

        if self.large_timer > 0:
            self.large_timer -= dt
            if self.large_timer <= 0:
                self.large_timer = 0.0
                self.triangle_size = self.original_triangle_size
                self.square_width = self.original_square_width
                self.square_height = self.original_square_height
                self.ball_radius = self.original_ball_radius

        self.larger_ob = remaining

    def timer(self):
        self.large_timer = 0.0
        self.original_triangle_size = self.triangle_size
        self.original_square_width = self.square_width
        self.original_square_height = self.square_height
        self.original_ball_radius = self.ball_radius
        
# Ball
    def pace_ball(self):
        self.pace_balls = []
        self.pace_ball_colour = "#26d991"
        self.pace_ball_timer = 0.0
        self.pace_ball_radius = 10
        self.pace_ball_x = random.randint(self.pace_ball_radius, WIDTH - self.pace_ball_radius)
        self.pace_ball_y = -self.pace_ball_radius
        self.pace_ball_speed = 300

    def update_pace_ball(self, dt):
        self.pace_ball_timer -= dt
        if self.pace_ball_timer <= 0:
            self.pace_balls.append({
                "x": random.randint(self.pace_ball_radius, WIDTH - self.pace_ball_radius),
                "y": self.pace_ball_y,
                "vy": self.pace_ball_speed
            })
            self.pace_ball_timer = random.uniform(1, 10)

        for pb in self.pace_balls:
            pb["y"] += pb["vy"] * dt

        remaining = []
        for pb in self.pace_balls:
            bottom = pb["y"] + self.pace_ball_radius
            hit = (self.basket_x <= pb["x"] <= self.basket_x + self.basket_width and self.basket_y <= bottom <= self.basket_y + self.basket_height) 
            if hit:
                change = random.choice([100, 200, -100, -200, -500, 500])
                self.basket_speed = max(100, min(800, self.basket_speed + change))
                self.api.log_event("basket_speed_changed", self.basket_speed)
            elif pb["y"] < HEIGHT:
                remaining.append(pb)
        self.pace_balls = remaining


    def draw(self, screen: pygame.Surface) -> None:
        screen.fill(BACKGROUND)
        pygame.draw.rect(screen,"gray", (self.basket_x, self.basket_y, self.basket_width, self.basket_height))
        for ball in self.balls:
            pygame.draw.circle(screen, self.ball_colour, (ball["x"], ball["y"]), self.ball_radius, 3)
        for tri in self.triangles:
            punkte = self.get_triangle_points(tri["x"], tri["y"])
            pygame.draw.polygon(screen, self.triangle_colour, punkte, 3)
        for sq in self.squares:
            pygame.draw.rect(screen, self.square_colour, (sq["x"], sq["y"], self.square_width, self.square_height), 3)
        for diamond in self.diamonds:
            diamond_punkte = self.get_diamond_points(diamond["x"], diamond["y"])
            pygame.draw.polygon(screen, self.diamond_colour, diamond_punkte, 3)
        for ball_var in self.balls_var:
            pygame.draw.circle(screen, self.ball_colour_var, (ball_var["x"], ball_var["y"]), self.ball_radius_var)
        for larger in self.larger_ob:
            pygame.draw.circle(screen, self.larger_colour, (larger["x"], larger["y"]), self.larger_radius)    
        for pb in self.pace_balls:
            pygame.draw.circle(screen, self.pace_ball_colour, (pb["x"], pb["y"]), self.pace_ball_radius)
            
        score_text = self.font_score.render(f"Score: {self.score}", True, TEXT_COLOUR)
        screen.blit(score_text, (10, 10))
        
        pygame.draw.rect(screen, "white", (0, 565, WIDTH, HEIGHT))
        
        s = 20
        p = 150
        d = 575
        start_info_points = self.font_start_info.render("+ Points (var)", True, "#3826d9")
        screen.blit(start_info_points, (s, d))
        start_info_danger = self.font_start_info.render("- Life", True, "#d9266e")
        screen.blit(start_info_danger, ((s + p + 20), d))
        start_info_speed = self.font_start_info.render("+/- Speed", True, "#26d991")
        screen.blit(start_info_speed, ((s + 2*p), d))
        start_info_larger = self.font_start_info.render("+ Growth", True, "#c7d926")
        screen.blit(start_info_larger, ((s + 3*p), d))
        start_info_basket = self.font_start_info.render("+/- Basket Length", True, "#9a26d9")
        screen.blit(start_info_basket, ((s + 4*p), d))
            
        #Herzen
        abstand = 20
        start_x = 650
        y = 10
        for i in range(3):
            x = start_x + i * (24 + abstand)
            if i < self.lives:
                screen.blit(self.heart, (x, y))
            else:
                screen.blit(self.heart_empty, (x, y))
        
        
        # Game Over anzeigen
        if self.game_over:
            screen.fill(BACKGROUND)
            score_text = self.font_score.render(f"Score: {self.score}", True, TEXT_COLOUR)
            score_rect = score_text.get_rect(
                center=(WIDTH // 2, HEIGHT // 2 + 150)
            )
            screen.blit(score_text, score_rect)
            game_over_text = self.font_game_over.render(
                "GAME OVER",
                True,
                "red"
            )

            text_rect = game_over_text.get_rect(
                center=screen.get_rect().center
            )

            screen.blit(game_over_text, text_rect)
            
            # ----- INFO ------    
            info_text = self.font_end_info.render(
                "------ PRESS ENTER TO EXIT ------",
                True,
                "white"
            )

            info_rect = info_text.get_rect(
                center=(WIDTH // 2, HEIGHT // 2 + 60)
            )

            screen.blit(info_text, info_rect)
            
        if not self.game_start:
            start_text = self.font_game_over.render(
                "PRESS ENTER",
                True,
                "white"
            )

            start_rect = start_text.get_rect(
                center=(WIDTH // 2, HEIGHT // 2)
            )

            screen.blit(start_text, start_rect)
            
            start_info_directions = self.font_start_direc.render(
                "press left or right to move",
                True,
                "white"
            )

            direc_rect = start_info_directions.get_rect(
                center=(WIDTH // 2, (HEIGHT // 2 ) + 30)
            )

            screen.blit(start_info_directions, direc_rect)
            

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN and not self.game_start:
                self.game_start = True
                self.game_start_time = time.perf_counter()

                self.api.log_event("game_started", 1)
            
            if event.key == pygame.K_RETURN and self.game_over:
                self.api.end_game(self.score)