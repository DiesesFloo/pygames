"""CSV-Logger fuer eine lokale Plattforminstanz. Keine pygame-Abhaengigkeit."""
import csv
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


SESSION_FIELDS = ('session_id', 'nickname', 'game', 'started_at',
                  'ended_at', 'duration_s', 'score', 'status')
EVENT_FIELDS = ('session_id', 'timestamp', 'event', 'value')


def now_iso():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec='milliseconds')


def append_row(path: Path, columns, row):
    path.parent.mkdir(parents=True, exist_ok=True)
    new_file = not path.exists() or path.stat().st_size == 0
    with path.open('a', encoding='utf-8', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        if new_file:
            writer.writeheader()
        writer.writerow(row)


class SessionLogger:
    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)
        self.session_file = self.data_dir / 'sessions.csv'
        self.event_file = self.data_dir / 'events.csv'
        self.current = None

    def start(self, nickname, game):
        if self.current is not None:
            raise RuntimeError('Eine Session laeuft bereits')
        start = datetime.now(timezone.utc)
        self.current = {
            'session_id': uuid4().hex,
            'nickname': nickname,
            'game': game,
            'start': start,
        }
        self.event('game_started')
        return self.current['session_id']

    def event(self, name, value=None):
        if self.current is None:
            return
        append_row(self.event_file, EVENT_FIELDS, {
            'session_id': self.current['session_id'],
            'timestamp': now_iso(),
            'event': name,
            'value': '' if value is None else str(value),
        })

    def finish(self, score=None, status='completed'):
        if self.current is None:
            return
        current = self.current
        end = datetime.now(timezone.utc)
        duration = (end - current['start']).total_seconds()
        try:
            self.event('game_finished', status)
            append_row(self.session_file, SESSION_FIELDS, {
                'session_id': current['session_id'],
                'nickname': current['nickname'],
                'game': current['game'],
                'started_at': current['start'].astimezone().isoformat(timespec='milliseconds'),
                'ended_at': end.astimezone().isoformat(timespec='milliseconds'),
                'duration_s': f'{duration:.3f}',
                'score': '' if score is None else score,
                'status': status,
            })
        finally:
            self.current = None
