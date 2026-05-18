from chording_modes import ChordingMode
from commands import Command
from config import Config
from my_frozen_dict import MyFrozenDict
from notification_modes import NotificationMode
from pathlib import Path
from load_config_map import parse
from logger import log_warning

from constants import PROJECT_NAME, CONFIG_FILE_NAME

from config_manager import ConfigManager
from utils import ascii_only, flat_inplace_merge_dicts, load_chips, load_json, reverse_dict


def _get_config_file_path(manager: ConfigManager, file_name: str) -> Path | None:
    path = Path(file_name)
    if not path.exists():
        path = manager.find_config_file(file_name)
    if not path.exists():
        path = None
    return path


def _parse_config(manager: ConfigManager) -> dict:
    path = _get_config_file_path(manager, CONFIG_FILE_NAME)
    if not path or not path.exists():
        return {}
    return parse(path) or {}


class ConfigWrapper:
    def __init__(self):
        self._manager = ConfigManager(PROJECT_NAME)

        self.data: dict[MyFrozenDict, str] = {}
        self.reversed_data: dict[str, list[MyFrozenDict]] = {}
        self._commands = {}

        self.on_reload = []
        self.config = Config()
        self.reload()

    def get_commands(self, key: str) -> list[Command]:
        commands = self._commands.get(key)
        if not commands:
            return []
        return commands

    def has_command(self, key: str) -> bool:
        return key in self._commands

    def qt_mode(self) -> bool:
        return self.config.notification.mode == NotificationMode.QT

    def chara_mode(self) -> bool:
        return self.config.general.mode == ChordingMode.CHARA_CHORDER

    def has_chord(self, trigger: str) -> bool:
        return MyFrozenDict.from_string(trigger) in self.data

    def get_chord(self, trigger: str) -> str | None:
        return self.data.get(MyFrozenDict.from_string(trigger))

    def has_chip(self, trigger: str) -> bool:
        return self.has_chord(trigger)

    def get_chip(self, trigger: str) -> str | None:
        return self.get_chord(trigger)

    def get_triggers(self, output: str) -> list[MyFrozenDict] | None:
        return self.reversed_data.get(output)

    def filtered(self, s: str) -> bool:
        blocked = self.config.filter.blocked
        allowed = self.config.filter.allowed
        if s in blocked:
            return True

        if len(allowed) != 0 and s not in allowed:
            return True
        return False

    def make_message(self, triggers: list[str] | str, val: str):
        out = self.config.notification.message.replace(
            "$triggers", str(triggers))
        out = out.replace("$chord", val)
        return out

    def reload(self, log=False):
        if log:
            print("reloading...")
        self.config.update(_parse_config(self._manager))
        self._commands.clear()

        external_commands: dict[str, list[Command]] | None = None
        if self.chara_mode():
            self.data = ascii_only(load_json(self._manager))
        else:
            self.data, external_commands = load_chips(self._manager)

        self.reversed_data = reverse_dict(self.data)

        command_map = self.config.commands.copy()
        flat_inplace_merge_dicts(command_map, external_commands)

        for key, val in command_map.items():
            commands = []
            for command_str in val:
                try:
                    command = Command(command_str)
                    commands.append(command)
                except ValueError:
                    log_warning(f"invalid command name: {
                                command_str}, skipping")
            self._commands[key] = commands

        for c in self.on_reload:
            c()
