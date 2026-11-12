""" Schnittstelle, die jedes Spiel von der Plattform erhaelt."""
from typing import Any, Callable


class GameAPI:
    def __init__(self, nickname: str, game_name: str,
                 log_callback: Callable[[str, Any], None],
                 finish_callback: Callable[[int, str], None]):
        self.nickname = nickname
        self.game_name = game_name
        self._log_callback = log_callback
        self._finish_callback = finish_callback
        self._finished = False

    def log_event(self, name: str, value: Any = None) -> None:
        """Meldet ein Ereignis, z.B. log_event('level', 2)."""
        if not self._finished:
            self._log_callback(str(name), value)

    def end_game(self, score: int = 0) -> None:
        """Beendet das Spiel nach dem aktuellen Callback (nicht pygame!)."""
        if not self._finished:
            self._finished = True
            self._finish_callback(int(score), 'completed')
