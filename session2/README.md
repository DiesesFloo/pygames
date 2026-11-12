# Game-Plattform für pygame-ce

Lokale Spieleplattform: ein Fenster, eine pygame-Ereignisschleife, dynamisch geladene Spiele und CSV-Logging.

## Installation und Start

**Windows (PowerShell)**

```powershell
py -3.13 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

Wenn `py -3.13` nicht verfügbar ist, die installierte Python-Version mit `py --list` prüfen und den Befehl entsprechend anpassen. Falls PowerShell die Aktivierung sperrt, kann die virtuelle Umgebung auch ohne Aktivierung verwendet werden: `.venv\Scripts\python.exe -m pip install -r requirements.txt` und `.venv\Scripts\python.exe main.py`.

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

Auf Linux kann für pygame zusätzlich die systemseitige SDL-/Grafikumgebung relevant sein. Der Start erfolgt in einem Desktop-Terminal mit einer laufenden grafischen Sitzung.

## Bedienung

1. Nickname eingeben und Enter drücken.
2. Spiel mit Pfeil hoch/runter auswählen; Enter startet es.
3. In den Spielen Pfeiltasten oder WASD verwenden.
4. ESC bricht das laufende Spiel ab.
5. Nach dem Ergebnis führt Enter zurück ins Menü; dort ändert `N` den Nickname.
6. Das Fenster schließen, um die Plattform zu beenden.

## Projektstruktur

- `main.py`: Fenster, zentrale Schleife, Menü und Zustandswechsel.
- `game_manager.py`: findet Spiele automatisch über `importlib` und `pkgutil`.
- `game_api.py`: kleine API für die Studierenden.
- `logger.py`: Sessions und Events als CSV.
- `games/snake.py`: einfaches Snake.
- `games/pong.py`: Solo-Pong mit Paddle.
- `data/`: wird bei ersten Ereignissen mit CSV-Dateien gefüllt.

## API für neue Spiele

Eine neue Datei `games/mein_spiel.py` genügt:

```python
import pygame

GAME_NAME = "Mein Spiel"

class Game:
    def __init__(self, api):
        self.api = api
        self.score = 0

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            self.score += 1
            self.api.log_event("space_pressed", self.score)
            if self.score >= 10:
                self.api.end_game(self.score)

    def update(self, dt, keys):
        pass

    def draw(self, screen):
        screen.fill("navy")
```

**Vertrag:**

- `GAME_NAME`: Anzeigename des Spiels (Zeichenkette).
- `Game(api)`: erzeugt das Spiel. `api.nickname` ist der aktuelle Nickname.
- `handle_event(event)`: Tastatur-/Mausevents verarbeiten.
- `update(dt, keys)`: Spiellogik (dt in Sekunden, keys = `pygame.key.get_pressed()`).
- `draw(screen)`: zeichnet auf die bereitgestellte `pygame.Surface`.
- `api.log_event(name, value=None)`: optionales Ereignis mit Zeitstempel.
- `api.end_game(score=0)`: Spiel beenden und Ergebnis übermitteln. Mehrfachaufrufe werden ignoriert.

**Nicht im Spiel aufrufen:** `pygame.init()`, `pygame.quit()`, `pygame.display.set_mode()`, `pygame.display.flip()` oder eine eigene Hauptschleife. Die Plattform übernimmt das alles. ESC ist als Abbruch reserviert.

## Logging

`data/sessions.csv` speichert pro Durchlauf eine Zeile:

`session_id,nickname,game,started_at,ended_at,duration_s,score,status`

`data/events.csv` speichert einzelne Ereignisse:

`session_id,timestamp,event,value`

Zeitstempel sind ISO-8601 mit Zeitzonenoffset. Status ist `completed`, `aborted` oder `error`. Jede Session erhält eine zufällige ID. Die CSV-Dateien sind für einen einzelnen lokalen Prozess ausgelegt, nicht für gleichzeitige Schreibzugriffe vieler Rechner auf eine gemeinsame Datei.

Die Nicknames sind frei gewählte Pseudonyme, keine Authentifizierung. Die Daten bleiben lokal im `data/`-Ordner. Für eine spätere zentrale Sammlung sollten Datenschutz, Löschfristen und eine sichere Übertragung separat geplant werden.

## Bewusste Einschränkungen

- Spielmodule laufen im selben Prozess wie die Plattform: Abstürze werden oft abgefangen, Endlosschleifen oder ein `sys.exit()` im Spiel können die Plattform aber stoppen.
- Neue Spiele werden beim Plattformstart entdeckt; nach Hinzufügen einer Datei neu starten.
- Importierte Module sind vertrauenswürdiger Python-Code, keine Sandbox.
- Alle Spiele nutzen eine Fenstergröße von 800 × 600 Pixeln.
- Nach einer mit `ESC` abgebrochenen Session bleibt der Punktestand im CSV leer; abgeschlossene Sessions enthalten einen Score.
