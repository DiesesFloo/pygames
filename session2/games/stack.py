import random as rd
import pygame

GAME_NAME = "Stack"

WIDTH = 800
HEIGHT = 600


class Block:

  def __init__(self):
    self.width = 300
    self.height = 30
    self.x = WIDTH // 2 - 150
    self.y = HEIGHT - 10 - self.height
    self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
    self.space_gedrueckt = False
    self.speed = 5
    self.color = (130, 238, 120)
    self.gameover = False
    self.score = 0
    self.positionen = []
    self.font = pygame.font.SysFont(None, 36)

  def update(self):
    if self.rect.width <= 0:
      return
    self.rect.x += self.speed
    if (
        self.rect.right >= WIDTH
        or self.rect.left <= 0
        or (len(self.positionen) > 0 and self.rect.right >= self.positionen[-1][0] + self.positionen[-1][2] + self.width)
        or (len(self.positionen) > 0 and self.rect.left <= self.positionen[-1][0] - self.width)
    ):
        self.speed *= -1


  def draw(self, screen):
    # Gestapelte Blöcke und Zahlen gemeinsam zeichnen
    for x, y, width, height, color, score in self.positionen:
        block_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(screen, color, block_rect)

        text = self.font.render(str(score), True, (255, 255, 255))

        if width <= 30:
            screen.blit(text, text.get_rect(center=(block_rect.centerx - 30, block_rect.centery)))
        else:
            screen.blit(text, text.get_rect(center=block_rect.center))

    # Aktuellen, beweglichen Block zeichnen
    pygame.draw.rect(screen, self.color, self.rect)

  def save_position(self):
    if len(self.positionen) >= 10:
      self.positionen.pop(0)
      previous_top = self.positionen[-1][1]
      for position in self.positionen:
        position[1] += self.height
      self.positionen.append([
          self.rect.x,
          previous_top,
          self.rect.width,
          self.rect.height,
          self.color,
          self.score,
      ])
      return True

    self.positionen.append([
        self.rect.x,
        self.rect.y,
        self.rect.width,
        self.rect.height,
        self.color,
        self.score,
    ])
    return False

  def new_block(self, keys):
    placed = False
    if keys[pygame.K_SPACE]:
      if not self.space_gedrueckt:
        overlap = self.compare_blocks()
        if overlap is not None:
          self.score += 1
          placed = True
          self.rect = overlap
          scrolled = self.save_position()
          if scrolled:
            self.rect.y = self.positionen[-1][1] - self.height
          else:
            self.rect.y -= self.height
        else:
          self.gameover = True

        self.color = (
            rd.randint(0, 100),
            rd.randint(120, 255),
            rd.randint(0, 100),
        )
        self.space_gedrueckt = True
    else:
      self.space_gedrueckt = False
    return placed

  def compare_blocks(self):
    if len(self.positionen) < 1:
      return self.rect.copy()

    previous = pygame.Rect(*self.positionen[-1][:4])
    overlap_left = max(self.rect.left, previous.left)
    overlap_right = min(self.rect.right, previous.right)
    overlap_width = overlap_right - overlap_left

    if overlap_width <= 0:
      self.rect.width = 0
      return None

    return pygame.Rect(
        overlap_left,
        self.rect.y,
        overlap_width,
        self.rect.height,
    )


class Game:

  def __init__(self, api):
    self.api = api
    self.block = Block()
    self.font = pygame.font.Font(None, 36)
    self.start_ticks = pygame.time.get_ticks()
    self.vergangene_sekunden = 0

  def handle_event(self, event):
    pass

  def update(self, dt, keys):
    placed = self.block.new_block(keys)
    self.block.update()

    self.vergangene_sekunden = (
        pygame.time.get_ticks() - self.start_ticks
    ) / 1000

    if placed:
      self.api.log_event("block_placed", self.block.score)
      self.api.log_event("time_block_placed", self.vergangene_sekunden)
      self.api.log_event("block_size", self.block.rect.width)

    if self.block.gameover:
      self.api.end_game(self.block.score)


  def draw(self, screen):
    screen.fill("black")
    self.block.draw(screen)

    # Timer anzeigen
    timer_text = self.font.render(
        f"Zeit: {round(self.vergangene_sekunden)}s", True, (255, 255, 255)
    )
    screen.blit(timer_text, timer_text.get_rect(topright=(WIDTH - 20, 20)))

