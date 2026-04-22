from utils import uncapitalize
from config import current_config
from pathlib import Path
from sudo_send import sudo_safe_send_notification, sudo_safe_send_progress_notification

missed_chords: dict[str, int] = {}


def display_message(chord: str, triggers: list[str]):
    chord_lower = uncapitalize(chord)
    if chord_lower in current_config.excluded_chords:
        return

    if current_config.white_listed and chord_lower not in current_config.white_listed:
        return

    title: str = current_config.notification_title
    message: str = current_config.notification_message(triggers, chord)

    if message not in missed_chords:
        missed_chords[message] = 0
    missed_chords[message] += 1
    _print_map()
    _write_log_to_file()

    if current_config.qt_mode:
        from qt_bridge import bridge

        bridge.notify.emit(title, message)
    elif current_config.notification_bar_update_frequency > 0 :
        sudo_safe_send_progress_notification(title, message,int(current_config.duration.milliseconds), current_config.notification_bar_update_frequency)
    else:
        sudo_safe_send_notification(title, message,int(current_config.duration.milliseconds))



def _print_map():
    sorted_chords = sorted(missed_chords.items(),
                           key=lambda x: x[1], reverse=True)
    for k, v in sorted_chords:
        if current_config.log_to_stdout:
            print(k, v)
    if current_config.log_to_stdout:
        print("-------------------------------")


def _write_log_to_file():
    if not current_config.log_to_path:
        return

    log_path = Path(current_config.log_to_path).expanduser()

    log_path.parent.mkdir(parents=True, exist_ok=True)

    sorted_chords = sorted(missed_chords.items(),
                           key=lambda x: x[1], reverse=True)
    lines = [f"{k} {v}" for k, v in sorted_chords]
    log_path.write_text("\n".join(lines) + "\n")
