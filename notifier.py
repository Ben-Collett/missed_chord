import json
from dataclasses import dataclass
from pathlib import Path
from config_wrapper import ConfigWrapper
from logging_modes import LoggingMode
from send_notification import display_notification
from utils import safe_expand_user, uncapitalize


class NotificationSender:
    def send_notification(self, chord: str, triggers: list[str]):
        raise NotImplementedError()


@dataclass(frozen=True)
class MissedKey:
    """Identity of a missed chord/chip: its output word and trigger set."""
    chord: str
    triggers: tuple[str, ...]

    @staticmethod
    def of(chord: str, triggers: list[str]) -> "MissedKey":
        return MissedKey(chord, tuple(sorted(triggers)))


def _safe_increment(map: dict, key, increment=1):
    map[key] = map.get(key, 0)+increment


class ConfigNotificationSender(NotificationSender):
    """
    _baseline stores the results of loading the json 
    _missed is the changes in this session they must be different to avoid reprinting missed events from previous sessions.
    """

    def __init__(self, config_wrapper: ConfigWrapper):
        self.config_wrapper = config_wrapper
        self._missed: dict[MissedKey, int] = {}
        self._baseline: dict[MissedKey, int] = {}
        self._path: Path | None = None
        logging = config_wrapper.config.logging
        self._mode: LoggingMode = logging.mode

        if config_wrapper.chara_mode():
            json_path = logging.chara_path
        else:
            json_path = logging.chip_path
        self._init_path(json_path)

    def _init_path(self, raw_path: str):
        """
        initializes the chara/fuzzchip's json path
        based on the Logging mode and chara_mode
        """
        if raw_path == "":
            return

        path = safe_expand_user(Path(raw_path))
        if self._mode == LoggingMode.INCREMENT:
            self._path = _next_increment_path(path)
        else:
            self._path = path

        if self._mode == LoggingMode.LOAD:
            self._baseline = _load_json_counts(self._path)

    def format_message(self, chord: str, triggers: list[str]):
        return self.config_wrapper.make_message(triggers, chord)

    def should_filter(self, chord: str, triggers: list[str]) -> bool:
        chord_lower = uncapitalize(chord)
        return self.config_wrapper.filtered(chord_lower)

    def send_notification(self, chord: str, triggers: list[str]):
        if self.should_filter(chord, triggers):
            return

        config = self.config_wrapper.config
        key = MissedKey.of(chord, triggers)
        _safe_increment(self._missed, key)

        message = self.format_message(key.chord, list(key.triggers))
        should_print = config.logging.log_to_stdout
        should_write_to_file = config.logging.log_to_path != ""
        if should_print or should_write_to_file:
            sorted_misses = self._sorted_misses()
            if should_print:
                _print_map(sorted_misses)
            if should_write_to_file:
                _write_log_to_file(sorted_misses, config.logging.log_to_path)

        if self._path is not None:
            _write_json_file(self._json_counts(), self._path)

        title = config.notification.title
        display_notification(title, message, self.config_wrapper)

    def _sorted_misses(self) -> list[tuple[str, int]]:
        return sorted(
            ((self.format_message(k.chord, list(k.triggers)), c)
             for k, c in self._missed.items()),
            key=lambda x: (-x[1], x[0]))

    def _json_counts(self) -> dict[MissedKey, int]:
        if self._mode != LoggingMode.LOAD:
            return dict(self._missed)

        counts = dict(self._baseline)
        for key, count in self._missed.items():
            _safe_increment(counts, key, count)
        return counts


def _print_map(sorted_misses):
    for k, v in sorted_misses:
        print(k, v)
    print("-------------------------------")


def _write_log_to_file(sorted_misses, path: str):
    lines = [f"{k} {v}" for k, v in sorted_misses]
    _write_text(Path(path), "\n".join(lines) + "\n")


def _write_text(path: Path, text: str):
    path = safe_expand_user(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def _next_increment_path(path: Path) -> Path:
    if not path.exists():
        return path

    counter = 1
    while True:
        candidate = path.with_name(f"{path.stem}_{counter}{path.suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def _load_json_counts(path: Path) -> dict[MissedKey, int]:
    # the json is stored as a list of json objects
    if not path.exists():
        return {}

    try:
        entries = json.loads(path.read_text())
    except (OSError, ValueError):
        return {}

    if not isinstance(entries, list):
        return {}

    counts: dict[MissedKey, int] = {}
    for entry in entries:
        parsed = _parse_json_entry(entry)
        if parsed is None:
            # a corrupt file is ignored and later overwritten
            return {}
        key, count = parsed
        _safe_increment(counts, key, count)
    return counts


def _parse_json_entry(entry) -> tuple[MissedKey, int] | None:
    if not isinstance(entry, dict):
        return None

    chord = entry.get("chord")
    triggers = entry.get("triggers")
    count = entry.get("count")

    if not isinstance(chord, str):
        return None
    if isinstance(count, bool) or not isinstance(count, int):
        return None
    if not isinstance(triggers, list) or not all(
            isinstance(t, str) for t in triggers):
        return None

    return MissedKey.of(chord, triggers), count


def _write_json_file(counts: dict[MissedKey, int], path: Path):
    entries = [{"triggers": list(k.triggers), "chord": k.chord, "count": c}
               for k, c in counts.items()]
    entries.sort(key=lambda e: (-e["count"], e["chord"], e["triggers"]))

    _write_text(path, json.dumps(entries, indent=2) + "\n")
