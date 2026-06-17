from dataclasses import dataclass

from chara_utils import get_all_chords


@dataclass
class DeviceWrapper:
    device: str | None = None
    first_call = True

    def get_data(self) -> dict | None:
        try:
            from chara_utils import chord_backup_map, open_connection, hex_chords_to_list, list_chara_devices
        except ModuleNotFoundError:
            print("can't import chara utils")
            print("is pyserial installed?")
            return

        if self.first_call:
            self.prompt_select()

        device = self.device
        if not self.first_call and device is None:
            devices = list_chara_devices()
            if len(devices) == 1:
                device = devices[0]

        if device is not None:
            with open_connection(device) as conn:
                hex_chords: list[list[str]] = get_all_chords(conn)

            structured_chords = hex_chords_to_list(hex_chords)
            data = chord_backup_map(structured_chords)

            # this if statement should never be true
            # consider it an assert
            if "chords" not in data:
                print("no chords in data somehow?")
                return None

            return data

    def prompt_select(self):
        try:
            from chara_utils import list_chara_devices_with_desc
        except ModuleNotFoundError:
            print("can't import chara utils")
            print("is pyserial installed?")
            return
        from update_chord_backup import prompt_user_to_select_device
        self.device = prompt_user_to_select_device(
            *list_chara_devices_with_desc())
