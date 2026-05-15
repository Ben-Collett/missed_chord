from config_wrapper import ConfigWrapper
from qt_notification_data import QtNotificationData
from utils import uncapitalize, safe_expand_user
from pathlib import Path
from sudo_send import sudo_safe_send_notification, sudo_safe_send_progress_notification

missed_chords: dict[str, int] = {}


def display_message(chord: str, triggers: list[str], config_wrapper: ConfigWrapper):
    chord_lower = uncapitalize(chord)
    config = config_wrapper.config

    if config_wrapper.filtered(chord_lower):
        return

    title: str = config.notification.title
    message: str = config_wrapper.make_message(triggers, chord)

    if message not in missed_chords:
        missed_chords[message] = 0
    missed_chords[message] += 1
    should_print = config.logging.log_to_stdout
    should_write_to_file = config.logging.log_to_path != ""
    if should_print or should_write_to_file:
        sorted_chords = sorted(missed_chords.items(),
                               key=lambda x: x[1], reverse=True)
        if should_print:
            _print_map(sorted_chords)

        if should_write_to_file:
            _write_log_to_file(sorted_chords, config.logging.log_to_path)

    notification_duration = config.notification.duration.milliseconds
    update_frequency = config.experimental.notification_bar_update_frequency.milliseconds
    if config_wrapper.qt_mode():
        from qt_bridge import bridge
        qt = config.qt
        max_notifications = qt.max_notifications
        data = QtNotificationData(title=title, content=message, duration_ms=notification_duration,
                                  width=qt.notification_width, height=qt.notification_height, duration_height=qt.duration_height)
        bridge.notify.emit(data, max_notifications)
    elif update_frequency > 0:
        sudo_safe_send_progress_notification(
            title, message, notification_duration, update_frequency)
    else:
        sudo_safe_send_notification(title, message, notification_duration)


def _print_map(sorted_chords):
    for k, v in sorted_chords:
        print(k, v)
    print("-------------------------------")


def _write_log_to_file(sorted_chords, path: str):

    log_path = safe_expand_user(Path(path))

    log_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [f"{k} {v}" for k, v in sorted_chords]
    log_path.write_text("\n".join(lines) + "\n")
