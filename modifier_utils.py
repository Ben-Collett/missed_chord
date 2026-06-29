from dataclasses import dataclass


@dataclass
class DownMods:
    shift_down: bool = False
    ctrl_down: bool = False
    alt_down: bool = False
    meta_down: bool = False

    def update_from_mod(self, mod: str):
        if "shift" in mod.lower():
            self.shift_down = True
        elif "ctrl" in mod.lower():
            self.ctrl_down = True
        elif "alt" in mod.lower():
            self.alt_down = True
        elif "windows" in mod.lower():
            self.meta_down = True

    @staticmethod
    def from_event_data(event_name: str, is_down: bool, modifiers: list[str]) -> "DownMods":

        out = DownMods()
        if is_down:
            out.update_from_mod(event_name)

        modifiers = modifiers
        for mod in modifiers:
            out.update_from_mod(mod)

        return out
