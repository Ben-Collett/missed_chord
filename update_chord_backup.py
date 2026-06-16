from pathlib import Path
from chara_utils import chord_backup_map, get_all_chords, list_chara_devices_with_desc, open_connection, chord_to_list
from config_manager import ConfigManager
from typing import Any
from constants import PROJECT_NAME, CHARA_FILE_NAME
import json
from config_wrapper import get_config_file_path


def prompt_user_to_select_device(devices: list[str], descriptions: list[str]) -> str:
    if len(devices) == 1:
        return devices[0]
    elif len(devices) == 0:
        print("no charachorders detected")
        exit(1)
    else:
        print("devices:")
        for i in range(len(devices)):
            print(f"{i+1} {devices[i]} - {descriptions[i]}")
        index = input("select device from the index> ")

        try:
            int_index = int(index)
        except BaseException:
            print(index, "is not a valid integer index")
            exit(1)

        if int_index <= 0:
            print("out of range min index 1")
            exit(1)
        if int_index > len(devices):
            print("out of range max index", len(devices))
            exit(1)

        return devices[int_index-1]


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)


def update_chord_backup():
    device = prompt_user_to_select_device(*list_chara_devices_with_desc())
    file_path: Path = get_config_file_path(
        ConfigManager(PROJECT_NAME), CHARA_FILE_NAME)

    print("connecting to charachorder")
    success = False
    with open_connection(device) as connection:
        print("reading chords from device")
        chords = get_all_chords(connection)
        print("restructuring data")
        structured_chords = []
        for chord in chords:
            structured_chords.append(chord_to_list(*chord))
        backup_data = chord_backup_map(structured_chords)
        print("writing chara.json at", file_path.absolute())
        write_json(file_path, backup_data)
        success = True
    print()
    if success:
        print("done.")
    else:
        print("failed")
