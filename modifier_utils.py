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

    @staticmethod
    def from_down_mods(other: "DownMods", shift_down: bool = None, **kwargs) -> "DownMods":
        out = DownMods(
            shift_down=other.shift_down,
            ctrl_down=other.ctrl_down,
            alt_down=other.alt_down,
            meta_down=other.meta_down,
        )
        if shift_down is not None:
            out.shift_down = shift_down
        for key, value in kwargs.items():
            setattr(out, key, value)
        return out
