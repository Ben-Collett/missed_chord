from my_key_event import MyKeyEvent
from dataclasses import dataclass
from typing import Self


@dataclass
class DownMods:
    shift_down: bool = False
    ctrl_down: bool = False
    alt_down: bool = False
    meta_down: bool = False

    def update_from_mod(self, mod: str):
        if "shift" in mod:
            self.shift_down = True
        elif "ctrl" in mod:
            self.ctrl_down = True
        elif "alt" in mod:
            self.alt_down = True
        elif "windows" in mod:
            self.meta_down = True

    @staticmethod
    def from_event(event: MyKeyEvent) -> Self:

        out = DownMods()
        if event.is_down_event:
            out.update_from_mod(event.name)

        modifiers = event.modifiers
        for mod in modifiers:
            out.update_from_mod(mod)

        return out
