from utils import uncapitalize
import subprocess
from config import current_config

missed_chords: dict[str, int] = {}


def display_message(chord: str, triggers: list[str]):
    if uncapitalize(chord) in current_config.excluded_chords:
        return

    title = current_config.notification_title
    message = current_config.notification_message(triggers, chord)

    if message not in missed_chords:
        missed_chords[message] = 0
    missed_chords[message] += 1
    _print_map()

    if current_config.qt_mode:
        from qt_bridge import bridge
        bridge.notify.emit(title, message)
    else:
        subprocess.run(
            ['notify-send', '-t',
                str(int(current_config.duration.milliseconds)), title, message]
        )


def _print_map():
    for k, v in missed_chords.items():
        print(k, v)
    print("-------------------------------")
