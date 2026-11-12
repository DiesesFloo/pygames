"""Spielmodule im Paket 'games' automatisch finden und laden."""
import importlib
import pkgutil
import games


def discover_games():
    """Liefert eine Liste (Modulname, Anzeigename), alphabetisch sortiert."""
    found = []
    for info in pkgutil.iter_modules(games.__path__, games.__name__ + '.'):
        if info.ispkg or info.name.rsplit('.', 1)[-1].startswith('_'):
            continue
        try:
            module = importlib.import_module(info.name)
            if not isinstance(getattr(module, 'GAME_NAME', None), str):
                continue
            if not callable(getattr(module, 'Game', None)):
                continue
            found.append((info.name, module.GAME_NAME))
        except Exception as exc:
            print(f'Spielmodul {info.name} kann nicht geladen werden: {exc}')
    return found


def new_game(module_name, api):
    module = importlib.import_module(module_name)
    return module.Game(api)
