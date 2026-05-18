import os
from pathlib import Path
import sys
from config_manager import ConfigManager
from load_config_map import parse
from commands import Command
from my_frozen_dict import MyFrozenDict


def reverse_dict(d: dict):
    """Reverse the key/value mapping of a dictionary.

    If multiple keys share the same value, the reversed dict maps that value
    to a list of all original keys.
    """
    rev = {}
    for k, v in d.items():
        rev.setdefault(v, []).append(k)
    return rev


def flat_inplace_merge_dicts(dict1: dict | None, dict2: dict | None) -> None:
    """
    stores in dict1
    """

    if dict1 is None or dict2 is None:
        return

    for key, val in dict2.items():
        if key not in dict1:
            dict1[key] = val


def dicts_to_strings(dicts: list[MyFrozenDict]) -> list[str]:
    """
   dicts should be frequency frozen dicts, from each key to it's corresponding 
   frequency ex {"h":3}
    """
    out = []
    for d in dicts:
        out.append("")
        for char, freq in d.items():
            for _ in range(freq):
                out[-1] += char
    return out


def uncapitalize(s: str) -> str:
    return s[:1].lower() + s[1:]


def load_json(config_manager: ConfigManager) -> dict:
    FILE_NAME = "chords.json"
    path = Path(FILE_NAME)
    if not path.exists():
        path = config_manager.find_config_file(FILE_NAME)

    empty_chords = {"chords": []}
    if not path.exists():
        return empty_chords

    data = parse(path, defaults=empty_chords) or empty_chords

    return data


def load_chips(config_manager: ConfigManager) -> tuple[dict, dict]:

    FILE_NAME = "chips.toml"

    path = Path(FILE_NAME)
    if not path.exists():
        path = config_manager.find_config_file(FILE_NAME)

    if not path.exists():
        path = ConfigManager("fuzzy_chips").find_config_file("config.toml")

    if not path.exists():
        print("could not find any chips")
        return {}, {}

    empty_chips = {"chips": {}}
    data = parse(path, defaults=empty_chips) or empty_chips

    out = {}
    commands = {}
    chips: dict[str, str] = data["chips"]

    for key, val in chips.items():
        if isinstance(val, str):
            out[MyFrozenDict.from_string(key)] = val
        elif isinstance(val, list):
            current_commands: list[Command] = []
            for cmd in val:
                if cmd == "restart" or cmd == "reload_config":
                    current_commands.append(Command.RELOAD)
                elif cmd == "clear_buffer":
                    current_commands.append(Command.CLEAR_BUFFER)
            if len(current_commands) > 0:
                commands[key] = current_commands

    return out, commands


# returns none if not printable str
def _to_str(input: list[int]) -> str | None:

    output = ""
    for val in input:
        # charachorder uses zeros for padding
        if val == 0:
            continue

        if val < 32 or val >= 127:
            return None
        output += chr(val)
    return output


def ascii_only(data: dict) -> dict[MyFrozenDict, str]:
    # TODO: this should use a frozen dict not a set
    # format: key combinations are stored as a list of integers, with 0 to fix there length I think atleast for the input part
    # these are stored in a list with two elements the trigger followed by the output
    # these are then all stored in the list of chords
    chords: list[list[list[int]]] = data["chords"]
    out: dict[MyFrozenDict, str] = {}
    for pair in chords:
        trig = _to_str(pair[0])
        if not trig:
            continue

        output = _to_str(pair[1])
        if not output:
            continue
        out[MyFrozenDict.from_string(trig.lower())] = uncapitalize(output)
    return out


def is_on_linux():
    return sys.platform == "linux"


def safe_expand_user(path: Path) -> Path:

    if is_on_linux():
        import pwd
        expanded = str(path)
        if expanded.startswith("~"):
            if "SUDO_USER" in os.environ:
                sudo_user = os.environ["SUDO_USER"]
                user_home = pwd.getpwuid(pwd.getpwnam(sudo_user).pw_uid).pw_dir
                expanded = expanded.replace("~", user_home, 1)
            else:
                expanded = os.path.expanduser(expanded)
            return Path(expanded)
    return path


def overlap_count(s1, s2):
    count = 0

    for i in range(min(len(s1), len(s2))):
        if s1[i] != s2[i]:
            break
        count += 1
    return count
