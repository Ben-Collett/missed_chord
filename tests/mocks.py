from commands import Command
from config_wrapper import ConfigWrapper
from my_frozen_dict import MyFrozenDict
from notifier import NotificationSender
from queue import Queue

from utils import reverse_dict


class ChordTrig:
    def __init__(self, output, triggers):
        self.output = output
        self.triggers = list(sorted(triggers))

    def __eq__(self, o):
        if isinstance(o, ChordTrig):
            return self.output == o.output and self.triggers == o.triggers
        return False

    def __str__(self):
        return f'ChordTrig({self.output=}, {self.triggers=})'

    def __repr__(self):
        return str(self)


class NotificationSenderMock(NotificationSender):
    def __init__(self):
        self.sent: list[ChordTrig] = []

    def send_notification(self, chord: str, triggers: list[str]):
        self.sent.append(ChordTrig(chord, triggers))


class SimpleConfigWrapperMock(ConfigWrapper):
    def __init__(self, data: None | dict[MyFrozenDict, str] = None, commands=None):
        self.data: dict[MyFrozenDict, str] = data or {}
        self._commands: dict[str, list[Command]] = {}
        if commands:
            for key, val in commands.items():
                self._commands[key] = [
                    Command(cmd) if isinstance(cmd, str) else cmd for cmd in val
                ]
        self.reversed_data: dict[str,
                                 list[MyFrozenDict]] = reverse_dict(self.data)
        print(self.data)
        self.has_reloaded = False

    def __getattr__(self, name):
        if name == "config":
            raise NotImplementedError
        raise AttributeError(
            f"'{type(self).__name__}' object has no attribute '{name}'")

    def get_commands(self, key: str) -> list:
        return self._commands.get(key, [])

    def has_command(self, key: str) -> bool:
        return key in self._commands

    def qt_mode(self) -> bool:
        raise NotImplementedError

    def chara_mode(self) -> bool:
        raise NotImplementedError

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

    def reload(self, log=False):
        self.has_reloaded = True
