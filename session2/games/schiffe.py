"""Schiffe versenken
    Ziel: Flotte des Computers versenken
    Score: Anzahl der Schüsse --> weniger ist besser """

import pygame
import random

GAME_NAME = "Schiffe versenken"

# Spielfeld
GRID_SIZE = 10
# Größe einer Zelle in Pixeln
CELL_SIZE = 40
# Abstand zum Fensterrand --> Spielfeld mittig
MARGIN_X = (800 - GRID_SIZE * CELL_SIZE) // 2
MARGIN_Y = 120
# Ein Eintrag pro Schiff
SHIP_SIZES = [5, 4, 3, 3, 2]

# Zustände eines Felds
WATER = 0 # unbeschossenes Wasser
SHIP = 1 # unbeschossenes Schiff (wie Wasser gezeichnet)
HIT = 2 # getroffenes Schiffsteil
MISS = 3 # Fehlschuss oder Wasser um versenktes Schiff
SUNK = 4 # versunkenes Schiffsteil

# Liefert alle Zellen rund um ein Schiff ("Rahmen")
def get_neighbors_for_ship(ship_cells):
    # Set statt Liste: Jede Zelle nur einmal (auch wenn sie an mehrere Schiffsteile grenzt)
    result = set()
    for r, c in ship_cells:
        # dr / dc: Verschiebung um -1, 0 oder +1 --> alle 8 Nachbarn einer Zelle
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                nr, nc = r + dr, c + dc
                # nur Zellen im Spielfeld, die nicht selbst zum Schiff gehören
                if 0 <= nr < GRID_SIZE and 0 <= nc < GRID_SIZE and (nr, nc) not in ship_cells:
                    result.add((nr, nc))
    return result


# Liefert True, wenn alle angegebenen Zellen den angegebenen Zustand haben
def all_cells_have_state(field, cells, state):
    for r, c in cells:
        if field[r][c] != state:
            return False
    return True


# Erzeugt ein leeres Feld und platziert die Schiffe zufällig darauf
# Rückgabe: Feld und die Liste der Schiffe (jedes Schiff = Liste seiner Zellen)
def place_ships(grid_size, ship_sizes):
    field = [[WATER] * grid_size for _ in range(grid_size)]
    ships = []
    for ship_size in ship_sizes:
        # so lange neu würfeln, bis das Schiff an einen freien Platz passt
        while True:
            # Startposition so wählen, dass das Schiff noch ins Feld passt
            if random.choice([True, False]): # horizontal
                row = random.randrange(grid_size)
                col = random.randrange(grid_size - ship_size + 1)
                ship_cells = [(row, col + i) for i in range(ship_size)]
            else: # vertikal
                row = random.randrange(grid_size - ship_size + 1)
                col = random.randrange(grid_size)
                ship_cells = [(row + i, col) for i in range(ship_size)]
            # Schiff und sein Rahmen müssen frei sein, damit sich Schiffe nicht berühren
            cells_to_check = ship_cells + list(get_neighbors_for_ship(ship_cells))
            if all_cells_have_state(field, cells_to_check, WATER):
                for r, c in ship_cells:
                    field[r][c] = SHIP
                ships.append(ship_cells)
                break # Schiff gesetzt --> nächstes Schiff
    return field, ships


# Rechnet Mauskoordinaten in Zellenkoordinaten um (None, wenn außerhalb des Spielfelds)
def pixel_to_cell(x, y):
    col = (x - MARGIN_X) // CELL_SIZE
    row = (y - MARGIN_Y) // CELL_SIZE
    if 0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE:
        return row, col
    return None


class Game:
    def __init__(self, api):
        # Für Plattform, api-Objekt merken
        self.api = api
        self.field, self.ships = place_ships(GRID_SIZE, SHIP_SIZES)
        self.shots = 0
        self.sunk_ships = 0
        self.font = pygame.font.Font(None, 32)

    def update(self, dt: float, keys) -> None:
        pass

    def handle_event(self, event):
        # Linksklick = Schuss
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            x, y = event.pos
            cell = pixel_to_cell(x, y)
            # Klick neben das Feld
            if cell is None:
                return
            row, col = cell
            # Schon beschossen --> zählt nicht
            if self.field[row][col] in (HIT, MISS, SUNK):
                return
            self.shots += 1
            if self.field[row][col] == WATER:
                self.field[row][col] = MISS
                self.api.log_event("miss", f"{row},{col}")
            elif self.field[row][col] == SHIP:
                self.field[row][col] = HIT
                self.api.log_event("hit", f"{row},{col}")
                self.check_sunk(row, col)

    # Prüft, ob das getroffene Schiff komplett versenkt ist
    def check_sunk(self, row, col):
        for ship in self.ships:
            # Schiff zur getroffenen Zelle suchen
            if (row, col) in ship:
                # Wenn alle Zellen des Schiffs getroffen: Schiff gesunken und Rahmen (Wasser) um Schiff zeichnen
                if all_cells_have_state(self.field, ship, HIT):
                    for r, c in ship:
                        self.field[r][c] = SUNK
                    for r, c in get_neighbors_for_ship(ship):
                        self.field[r][c] = MISS
                    self.api.log_event("ship_sunk", len(ship))
                    self.sunk_ships += 1
                    # Alle Schiffe versenkt --> Spielende
                    if self.sunk_ships == len(self.ships):
                        self.api.end_game(self.shots)
                return

    def draw(self, screen: pygame.Surface) -> None:
        screen.fill("black")
        # Schiff und Wasser haben dieselbe Farbe --> Schiffe versteckt
        colors = {WATER: "steelblue", SHIP: "steelblue", HIT: "red", MISS: "white", SUNK: "green"}
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                rect = pygame.Rect(MARGIN_X + col * CELL_SIZE, MARGIN_Y + row * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(screen, colors[self.field[row][col]], rect)
                pygame.draw.rect(screen, "white", rect, 1)
        text = self.font.render(f"Schüsse: {self.shots}", True, "white")
        screen.blit(text, (MARGIN_X, 60))

        # Schiffsübersicht rechts neben dem Feld
        legend_x = MARGIN_X + GRID_SIZE * CELL_SIZE + 30    # 30 Pixel rechts vom Feld

        # Anzahl offener Schiffe
        open_ships = len(self.ships) - self.sunk_ships
        text = self.font.render(f"Offen: {open_ships}", True, "white")
        screen.blit(text, (legend_x, 60))

        # jedes Schiff als Reihe kleiner Kästchen: grau = offen, grün = versenkt
        y = MARGIN_Y
        for ship in self.ships:
            if all_cells_have_state(self.field, ship, SUNK):
                color = "green"
            else:
                color = "gray"
            for i in range(len(ship)):          # ein Kästchen pro Schiffsteil
                rect = pygame.Rect(legend_x + i * 20, y, 18, 18)
                pygame.draw.rect(screen, color, rect)
            y += 30                             # nächstes Schiff eine Zeile tiefer
