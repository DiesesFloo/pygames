import json
import random
from pathlib import Path

import pygame

try:
    import cv2
except ImportError:
    cv2 = None

GAME_NAME = "Snake"

WIDTH = 800
HEIGHT = 600
CELL = 20
COLS = WIDTH // CELL
ROWS = HEIGHT // CELL

BASE_STEP_TIME = 0.12
TURBO_FACTOR = 2
SPEEDUP_FACTOR = 0.95
MIN_STEP_TIME = 0.05

APPLE_START_VALUE = 10
APPLE_DECAY_PER_SECOND = 1
APPLE_MIN_VALUE = 1
GOLDEN_MULTIPLIER = 2

GOLDEN_MIN = 2
GOLDEN_MAX = 10

TIME_ATTACK_SECONDS = 60
ROCK_COUNT = 30

COUNTDOWN_SECONDS = 3
DYING_SECONDS = 1.5

APPLE_RED = (220, 30, 30)
APPLE_GOLD = (255, 200, 0)
ROCK_COLOR = (90, 90, 95)
ROCK_EDGE = (60, 60, 65)
DEAD_COLOR = (230, 40, 40)
TEXT_COLOR = (255, 255, 255)
ACCENT = (255, 210, 90)
MUTED = (200, 190, 175)

DATA_FILE = Path(__file__).with_name("snake_data.json")

GAMES_DIR = Path(__file__).parent
ASSET_DIRS = [GAMES_DIR / "assets", GAMES_DIR.parent / "assets", GAMES_DIR]

def find_asset(filename: str) -> Path:
    for folder in ASSET_DIRS:
        path = folder / filename
        if path.exists():
            return path
    return ASSET_DIRS[0] / filename

TRAILER_VIDEO = find_asset("snake_trailer.mp4")
TRAILER_AUDIO = find_asset("snake_trailer.ogg")

SOUND_FILES = {
    "apple": find_asset("snake_apple.ogg"),
    "golden": find_asset("snake_golden.ogg"),
    "fail": find_asset("snake_fail.ogg"),
}

MODES = [
    {"id": "classic", "name": "Klassik",
     "info": "Wände und der eigene Körper sind tödlich."},
    {"id": "wrap", "name": "Ohne Wände",
     "info": "Am Rand kommst du auf der anderen Seite wieder raus."},
    {"id": "time", "name": "Zeitangriff",
     "info": f"{TIME_ATTACK_SECONDS} Sekunden - so viele Punkte wie möglich."},
    {"id": "rocks", "name": "Hindernisse",
     "info": "Zufällige Steine auf dem Feld sind tödlich."},
    {"id": "speedup", "name": "Beschleunigung",
     "info": "Mit jedem Apfel wird die Schlange schneller."},
]

SKINS = [
    {"name": "Grün", "head": (90, 255, 90), "body": (20, 150, 20)},
    {"name": "Blau", "head": (120, 200, 255), "body": (30, 90, 200)},
    {"name": "Pink", "head": (255, 150, 220), "body": (210, 60, 150)},
    {"name": "Lila", "head": (200, 150, 255), "body": (120, 50, 190)},
    {"name": "Regenbogen", "head": (255, 255, 255), "body": None},
]

BOARDS = [
    {"name": "Erde", "light": (150, 105, 65), "dark": (125, 85, 50)},
    {"name": "Wiese", "light": (110, 170, 70), "dark": (90, 145, 55)},
    {"name": "Sand", "light": (225, 200, 140), "dark": (205, 180, 120)},
    {"name": "Eis", "light": (190, 220, 240), "dark": (165, 200, 225)},
    {"name": "Ozean", "light": (40, 90, 140), "dark": (30, 75, 120)},
    {"name": "Nacht", "light": (45, 50, 70), "dark": (35, 40, 58)},
]

END_TEXTS = {
    "wall": "Gegen die Wand!",
    "self": "Selbst gebissen!",
    "rock": "Gegen einen Stein!",
    "time_up": "Zeit abgelaufen!",
    "board_full": "Feld voll - gewonnen!",
}


class Game:
    def __init__(self, api):
        self.api = api

        self.font_small = pygame.font.Font(None, 26)
        self.font = pygame.font.Font(None, 36)
        self.font_big = pygame.font.Font(None, 80)
        self.font_huge = pygame.font.Font(None, 160)

        self.shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        self.shade.fill((0, 0, 0, 150))

        data = self.load_data()
        self.highscores = data.get("highscores", {})
        self.mode_index = int(data.get("last_mode", 0)) % len(MODES)
        self.skin_index = int(data.get("last_skin", 0)) % len(SKINS)
        self.board_index = int(data.get("last_board", 0)) % len(BOARDS)

        self.background = self.create_background()

        self.sounds = self.load_sounds()

        self.anim_time = 0.0

        self.turbo = False

        self.setup_time = 0.0

        self.state = "SETUP"

        self.reset_round()

        self.trailer = None
        self.trailer_audio = False
        self.start_trailer()

    def reset_round(self) -> None:
        self.mode = MODES[self.mode_index]["id"]

        start_x = COLS // 2
        start_y = ROWS // 2
        self.snake = [(start_x, start_y), (start_x - 1, start_y), (start_x - 2, start_y)]

        self.direction = (1, 0)
        self.next_direction = (1, 0)

        self.step_time = BASE_STEP_TIME
        self.step_timer = 0.0

        self.score = 0
        self.time_left = TIME_ATTACK_SECONDS

        self.rocks = set()

        self.apple = None
        self.golden_apple = None
        self.apple_age = 0.0
        self.spawns_until_golden = random.randint(GOLDEN_MIN, GOLDEN_MAX)

        self.countdown = COUNTDOWN_SECONDS
        self.dying_timer = 0.0
        self.end_reason = ""
        self.new_highscore = False
        self.finished = False

        self.play_time = 0.0
        self.turbo_time = 0.0
        self.turbo_started = 0.0
        self.pause_started = 0.0

    def start_round(self) -> None:
        self.reset_round()

        if self.mode == "rocks":
            self.create_rocks()

        self.spawn_apples()

        self.save_data()

        self.api.log_event("mode", self.mode)
        self.api.log_event("skin", SKINS[self.skin_index]["name"])
        self.api.log_event("board", BOARDS[self.board_index]["name"])
        self.api.log_event("setup_time", round(self.setup_time, 1))

        self.state = "COUNTDOWN"

    def load_sounds(self) -> dict:
        sounds = {}
        if not pygame.mixer.get_init():
            return sounds
        for name, path in SOUND_FILES.items():
            try:
                sounds[name] = pygame.mixer.Sound(str(path))
            except (pygame.error, FileNotFoundError):
                pass
        return sounds

    def play_sound(self, name: str) -> None:
        sound = self.sounds.get(name)
        if sound is not None:
            sound.play()

    def start_trailer(self) -> None:
        if cv2 is None or not TRAILER_VIDEO.exists():
            return

        capture = cv2.VideoCapture(str(TRAILER_VIDEO))
        if not capture.isOpened():
            return

        self.trailer = capture
        self.trailer_fps = capture.get(cv2.CAP_PROP_FPS) or 24
        self.trailer_frame = -1
        self.trailer_image = None
        self.trailer_time = 0.0

        try:
            pygame.mixer.music.load(str(TRAILER_AUDIO))
            pygame.mixer.music.play()
            self.trailer_audio = True
        except (pygame.error, FileNotFoundError):
            self.trailer_audio = False

        self.state = "TRAILER"

    def update_trailer(self, dt: float) -> None:
        if self.trailer_audio and pygame.mixer.music.get_busy():
            self.trailer_time = pygame.mixer.music.get_pos() / 1000
        else:
            self.trailer_time += dt

        target = int(self.trailer_time * self.trailer_fps)

        while self.trailer_frame < target:
            if self.trailer_frame < target - 1:
                ok = self.trailer.grab()
            else:
                ok, frame = self.trailer.read()
                if ok:
                    self.trailer_image = self.frame_to_surface(frame)
            if not ok:
                self.end_trailer("trailer_watched")
                return
            self.trailer_frame += 1

    def frame_to_surface(self, frame) -> pygame.Surface:
        height, width = frame.shape[:2]

        scale = min(WIDTH / width, HEIGHT / height)
        size = (int(width * scale), int(height * scale))
        if size != (width, height):
            frame = cv2.resize(frame, size, interpolation=cv2.INTER_AREA)

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        return pygame.image.frombytes(frame.tobytes(), size, "RGB")

    def end_trailer(self, event: str) -> None:
        self.stop_trailer()
        self.api.log_event(event, round(self.trailer_time, 1))
        self.state = "SETUP"

    def stop_trailer(self) -> None:
        if self.trailer is not None:
            self.trailer.release()
            self.trailer = None
        if self.trailer_audio:
            try:
                pygame.mixer.music.stop()
            except pygame.error:
                pass
            self.trailer_audio = False

    def __del__(self):
        if getattr(self, "trailer", None) is not None or getattr(self, "trailer_audio", False):
            self.stop_trailer()

    def create_background(self) -> pygame.Surface:
        board = BOARDS[self.board_index]
        background = pygame.Surface((WIDTH, HEIGHT))
        for row in range(ROWS):
            for col in range(COLS):
                color = board["light"] if (col + row) % 2 == 0 else board["dark"]
                pygame.draw.rect(background, color, (col * CELL, row * CELL, CELL, CELL))
        return background

    def load_data(self) -> dict:
        try:
            data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except (OSError, ValueError):
            return {}

    def save_data(self) -> None:
        data = {
            "highscores": self.highscores,
            "last_mode": self.mode_index,
            "last_skin": self.skin_index,
            "last_board": self.board_index,
        }
        try:
            DATA_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except OSError:
            pass

    def random_free_cell(self, exclude=()):
        blocked = set(self.snake) | self.rocks | set(exclude)

        free = [
            (col, row)
            for col in range(COLS)
            for row in range(ROWS)
            if (col, row) not in blocked
        ]
        if not free:
            return None
        return random.choice(free)

    def spawn_apples(self) -> None:
        self.apple = self.random_free_cell()
        self.golden_apple = None

        self.spawns_until_golden -= 1
        if self.spawns_until_golden <= 0 and self.apple is not None:
            self.golden_apple = self.random_free_cell(exclude=[self.apple])
            self.spawns_until_golden = random.randint(GOLDEN_MIN, GOLDEN_MAX)

            if self.golden_apple is not None:
                head_x, head_y = self.snake[0]
                distance = abs(self.golden_apple[0] - head_x) + abs(self.golden_apple[1] - head_y)
                self.api.log_event("golden_spawned", distance)

        self.apple_age = 0.0

    def apple_value(self) -> int:
        value = APPLE_START_VALUE - int(self.apple_age * APPLE_DECAY_PER_SECOND)
        return max(APPLE_MIN_VALUE, value)

    def create_rocks(self) -> None:
        head_x, head_y = self.snake[0]

        safe_zone = [
            (col, row)
            for col in range(head_x - 3, head_x + 11)
            for row in range(head_y - 2, head_y + 3)
        ]

        for _ in range(ROCK_COUNT):
            cell = self.random_free_cell(exclude=safe_zone)
            if cell is not None:
                self.rocks.add(cell)

    @staticmethod
    def direction_from_key(key):
        if key in (pygame.K_UP, pygame.K_w):
            return (0, -1)
        if key in (pygame.K_DOWN, pygame.K_s):
            return (0, 1)
        if key in (pygame.K_LEFT, pygame.K_a):
            return (-1, 0)
        if key in (pygame.K_RIGHT, pygame.K_d):
            return (1, 0)
        return None

    def handle_event(self, event) -> None:
        if event.type != pygame.KEYDOWN:
            return

        if self.state == "TRAILER":
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self.end_trailer("trailer_skipped")

        elif self.state == "SETUP":
            self.handle_setup_key(event.key)

        elif self.state in ("COUNTDOWN", "PLAYING"):
            if event.key == pygame.K_p and self.state == "PLAYING":
                self.state = "PAUSED"
                self.pause_started = self.anim_time
                self.api.log_event("pause", self.score)
                return

            new = self.direction_from_key(event.key)
            if new is None:
                return
            opposite = (-self.direction[0], -self.direction[1])
            if new != opposite:
                self.next_direction = new

        elif self.state == "PAUSED":
            if event.key == pygame.K_p:
                self.state = "PLAYING"
                self.api.log_event("resume", round(self.anim_time - self.pause_started, 1))

    def handle_setup_key(self, key) -> None:
        if key in (pygame.K_UP, pygame.K_w):
            self.mode_index = (self.mode_index - 1) % len(MODES)
        elif key in (pygame.K_DOWN, pygame.K_s):
            self.mode_index = (self.mode_index + 1) % len(MODES)
        elif key in (pygame.K_LEFT, pygame.K_a):
            self.skin_index = (self.skin_index - 1) % len(SKINS)
        elif key in (pygame.K_RIGHT, pygame.K_d):
            self.skin_index = (self.skin_index + 1) % len(SKINS)
        elif key == pygame.K_f:
            self.board_index = (self.board_index + 1) % len(BOARDS)
            self.background = self.create_background()
        elif key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
            self.start_round()

    def update(self, dt: float, keys) -> None:
        self.anim_time += dt

        if self.state == "TRAILER":
            self.update_trailer(dt)
            return

        if self.state == "SETUP":
            self.setup_time += dt
            return
        if self.state == "PAUSED":
            return

        if self.state == "COUNTDOWN":
            self.countdown -= dt
            if self.countdown <= 0:
                self.state = "PLAYING"
                self.api.log_event("round_started", self.mode)
            return

        if self.state == "DYING":
            self.dying_timer -= dt
            if self.dying_timer <= 0 and not self.finished:
                self.finished = True
                self.api.end_game(self.score)
            return

        self.apple_age += dt

        self.play_time += dt

        if self.mode == "time":
            self.time_left -= dt
            if self.time_left <= 0:
                self.time_left = 0
                self.end("time_up")
                return

        turbo_now = bool(keys[pygame.K_SPACE])

        if turbo_now and not self.turbo:
            self.turbo_started = self.play_time
            self.api.log_event("turbo_on", self.score)
        elif not turbo_now and self.turbo:
            self.api.log_event("turbo_off", round(self.play_time - self.turbo_started, 2))

        self.turbo = turbo_now
        if self.turbo:
            self.turbo_time += dt

        step_time = self.step_time / TURBO_FACTOR if self.turbo else self.step_time

        self.step_timer += dt
        if self.step_timer < step_time:
            return
        self.step_timer -= step_time

        self.step()

    def step(self) -> None:
        self.direction = self.next_direction

        head_x, head_y = self.snake[0]
        new_head = (head_x + self.direction[0], head_y + self.direction[1])

        if self.mode == "wrap":
            new_head = (new_head[0] % COLS, new_head[1] % ROWS)
        else:
            if not (0 <= new_head[0] < COLS and 0 <= new_head[1] < ROWS):
                self.end("wall")
                return

        if new_head in self.rocks:
            self.end("rock")
            return

        ate_red = new_head == self.apple
        ate_golden = new_head == self.golden_apple
        ate_apple = ate_red or ate_golden

        self.snake.insert(0, new_head)
        if not ate_apple:
            self.snake.pop()

        if new_head in self.snake[1:]:
            self.end("self")
            return

        if ate_apple:
            points = self.apple_value()
            if ate_golden:
                points *= GOLDEN_MULTIPLIER
            self.score += points

            self.play_sound("golden" if ate_golden else "apple")

            self.api.log_event("golden_apple_eaten" if ate_golden else "apple_eaten", points)
            self.api.log_event("apple_time", round(self.apple_age, 2))
            self.api.log_event("snake_length", len(self.snake))
            if ate_red and self.golden_apple is not None:
                self.api.log_event("golden_missed", self.score)

            if self.mode == "speedup":
                self.step_time = max(MIN_STEP_TIME, self.step_time * SPEEDUP_FACTOR)

            self.spawn_apples()

            if self.apple is None:
                self.end("board_full")

    def end(self, reason: str) -> None:
        if self.state == "DYING":
            return

        self.state = "DYING"
        self.dying_timer = DYING_SECONDS
        self.end_reason = reason

        self.play_sound("golden" if reason == "board_full" else "fail")
        self.api.log_event("game_over", reason)

        if self.turbo:
            self.api.log_event("turbo_off", round(self.play_time - self.turbo_started, 2))
        self.api.log_event("final_length", len(self.snake))
        self.api.log_event("play_time", round(self.play_time, 1))
        self.api.log_event("turbo_time", round(self.turbo_time, 1))
        if self.mode == "speedup":
            self.api.log_event("final_speed", round(BASE_STEP_TIME / self.step_time, 2))

        if self.score > self.highscores.get(self.mode, 0):
            self.highscores[self.mode] = self.score
            self.new_highscore = True
            self.api.log_event("new_highscore", self.score)
            self.save_data()

    def draw(self, screen: pygame.Surface) -> None:
        if self.state == "TRAILER":
            screen.fill((0, 0, 0))
            if self.trailer_image is not None:
                rect = self.trailer_image.get_rect(center=(WIDTH // 2, HEIGHT // 2))
                screen.blit(self.trailer_image, rect)
            self.draw_text(screen, "Enter: Überspringen", self.font_small, MUTED,
                           (WIDTH - 12, HEIGHT - 10), "bottomright")
            return

        screen.blit(self.background, (0, 0))

        if self.state == "SETUP":
            self.draw_setup(screen)
            return

        self.draw_rocks(screen)
        self.draw_apple(screen, self.apple, APPLE_RED)
        self.draw_apple(screen, self.golden_apple, APPLE_GOLD)
        self.draw_snake(screen, self.snake)
        self.draw_hud(screen)

        if self.state == "COUNTDOWN":
            screen.blit(self.shade, (0, 0))
            number = int(self.countdown) + 1
            self.draw_text(screen, str(number), self.font_huge, ACCENT,
                           (WIDTH // 2, HEIGHT // 2), "center")

        elif self.state == "PAUSED":
            screen.blit(self.shade, (0, 0))
            self.draw_text(screen, "PAUSE", self.font_big, ACCENT,
                           (WIDTH // 2, HEIGHT // 2 - 20), "center")
            self.draw_text(screen, "P: weiter    ESC: abbrechen", self.font_small, MUTED,
                           (WIDTH // 2, HEIGHT // 2 + 35), "center")

        elif self.state == "DYING":
            screen.blit(self.shade, (0, 0))
            self.draw_snake(screen, self.snake)
            text = END_TEXTS.get(self.end_reason, "Game Over")
            self.draw_text(screen, text, self.font_big, TEXT_COLOR,
                           (WIDTH // 2, HEIGHT // 2 - 40), "center")
            self.draw_text(screen, f"{self.score} Punkte", self.font, ACCENT,
                           (WIDTH // 2, HEIGHT // 2 + 20), "center")
            if self.new_highscore:
                self.draw_text(screen, "Neuer Highscore!", self.font, ACCENT,
                               (WIDTH // 2, HEIGHT // 2 + 60), "center")

    def draw_text(self, screen, text, font, color, pos, anchor="topleft") -> None:
        image = font.render(text, True, color)
        rect = image.get_rect(**{anchor: pos})
        shadow = font.render(text, True, (0, 0, 0))
        screen.blit(shadow, rect.move(2, 2))
        screen.blit(image, rect)

    def snake_color(self, index: int):
        if self.state == "DYING" and self.end_reason != "time_up" \
                and self.end_reason != "board_full" and int(self.anim_time * 8) % 2 == 0:
            return DEAD_COLOR

        skin = SKINS[self.skin_index]
        if index == 0:
            return skin["head"]
        if skin["body"] is not None:
            return skin["body"]

        hue = (index * 15 + self.anim_time * 120) % 360
        color = pygame.Color(0, 0, 0)
        color.hsva = (hue, 85, 95, 100)
        return color

    def draw_snake(self, screen, cells, origin=(0, 0)) -> None:
        for index, (x, y) in enumerate(cells):
            rect = (origin[0] + x * CELL, origin[1] + y * CELL, CELL - 1, CELL - 1)
            pygame.draw.rect(screen, self.snake_color(index), rect)

    def draw_apple(self, screen, cell, color) -> None:
        if cell is None:
            return
        col, row = cell
        center = (col * CELL + CELL // 2, row * CELL + CELL // 2)
        pygame.draw.circle(screen, color, center, CELL // 2 - 2)

    def draw_rocks(self, screen) -> None:
        for col, row in self.rocks:
            rect = pygame.Rect(col * CELL, row * CELL, CELL, CELL)
            pygame.draw.rect(screen, ROCK_COLOR, rect, border_radius=4)
            pygame.draw.rect(screen, ROCK_EDGE, rect, width=2, border_radius=4)

    def draw_hud(self, screen) -> None:
        self.draw_text(screen, f"Punkte: {self.score}", self.font, TEXT_COLOR, (10, 8))
        apple_text = f"Apfel: {self.apple_value()}"
        if self.golden_apple is not None:
            apple_text += f"   Gold: {self.apple_value() * GOLDEN_MULTIPLIER}"
        self.draw_text(screen, apple_text, self.font_small, ACCENT, (10, 40))

        best = self.highscores.get(self.mode, 0)
        self.draw_text(screen, MODES[self.mode_index]["name"], self.font_small, MUTED,
                       (WIDTH - 10, 8), "topright")
        self.draw_text(screen, f"Best: {best}", self.font_small, TEXT_COLOR,
                       (WIDTH - 10, 32), "topright")

        if self.mode == "time":
            self.draw_text(screen, f"Zeit: {int(self.time_left) + 1}", self.font, ACCENT,
                           (WIDTH - 10, 56), "topright")
        elif self.mode == "speedup":
            speed = BASE_STEP_TIME / self.step_time
            self.draw_text(screen, f"Tempo: x{speed:.1f}", self.font_small, ACCENT,
                           (WIDTH - 10, 56), "topright")

        if self.turbo and self.state == "PLAYING":
            self.draw_text(screen, ">> TURBO >>", self.font_small, ACCENT,
                           (WIDTH // 2, HEIGHT - 12), "midbottom")

    def draw_setup(self, screen) -> None:
        screen.blit(self.shade, (0, 0))

        self.draw_text(screen, "SNAKE", self.font_big, ACCENT, (WIDTH // 2, 30), "midtop")

        self.draw_text(screen, "Modus", self.font, TEXT_COLOR, (60, 130))
        for i, mode in enumerate(MODES):
            y = 175 + i * 40
            selected = i == self.mode_index
            prefix = "> " if selected else "   "
            color = ACCENT if selected else MUTED
            self.draw_text(screen, prefix + mode["name"], self.font, color, (60, y))
            best = self.highscores.get(mode["id"], 0)
            self.draw_text(screen, f"Best: {best}", self.font_small, color, (390, y + 5), "topright")

        self.draw_text(screen, MODES[self.mode_index]["info"], self.font_small, TEXT_COLOR,
                       (60, 385))

        self.draw_text(screen, "Farbe", self.font, TEXT_COLOR, (470, 130))
        self.draw_text(screen, f"<  {SKINS[self.skin_index]['name']}  >", self.font, ACCENT,
                       (610, 185), "midtop")

        preview = [(i, 0) for i in range(7, -1, -1)]
        self.draw_snake(screen, preview, origin=(530, 240))

        self.draw_text(screen, "Feld", self.font, TEXT_COLOR, (470, 290))
        self.draw_text(screen, f"F:  {BOARDS[self.board_index]['name']}", self.font, ACCENT,
                       (610, 335), "midtop")

        board = BOARDS[self.board_index]
        for row in range(2):
            for col in range(8):
                color = board["light"] if (col + row) % 2 == 0 else board["dark"]
                pygame.draw.rect(screen, color, (530 + col * CELL, 375 + row * CELL, CELL, CELL))
        self.draw_snake(screen, [(i, 0) for i in range(5, 1, -1)], origin=(530, 385))

        self.draw_text(screen,
                       f"Je schneller du frisst, desto mehr Punkte (max. {APPLE_START_VALUE}, Gold x{GOLDEN_MULTIPLIER})",
                       self.font_small, MUTED, (WIDTH // 2, 455), "midtop")
        self.draw_text(screen, "Hoch/Runter: Modus   Links/Rechts: Farbe   F: Feld   Enter: Start",
                       self.font_small, TEXT_COLOR, (WIDTH // 2, 500), "midtop")
        self.draw_text(screen, "Im Spiel:  Leertaste = Turbo    P = Pause    ESC = Abbrechen",
                       self.font_small, MUTED, (WIDTH // 2, 530), "midtop")
