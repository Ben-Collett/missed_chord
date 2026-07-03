from pathlib import Path
from config_wrapper import ConfigWrapper
from send_notification import display_notification
from utils import safe_expand_user, uncapitalize


class NotificationSender:
    def send_notification(self, chord: str, triggers: list[str]):
        raise NotImplementedError()


class ConfigNotificationSender(NotificationSender):
    def __init__(self, config_wrapper: ConfigWrapper):
        self.config_wrapper = config_wrapper
        self._missed_chords = {}

    def format_message(self, chord: str, triggers: list[str]):
        return self.config_wrapper.make_message(triggers, chord)

    def should_filter(self, chord: str, triggers: list[str]) -> bool:
        chord_lower = uncapitalize(chord)
        return self.config_wrapper.filtered(chord_lower)

    def send_notification(self, chord: str, triggers: list[str]):
        if not self.should_filter(chord, triggers):
            missed_chords = self._missed_chords
            config = self.config_wrapper.config
            title = config.notification.title
            message = self.format_message(chord, triggers)

            if message not in missed_chords:
                missed_chords[message] = 0

            missed_chords[message] += 1

            should_print = config.logging.log_to_stdout
            should_write_to_file = config.logging.log_to_path != ""
            if should_print or should_write_to_file:
                # TODO: it would be better to just keep the map sorted
                sorted_chords = sorted(missed_chords.items(),
                                       key=lambda x: x[1], reverse=True)
                if should_print:
                    _print_map(sorted_chords)

                if should_write_to_file:
                    _write_log_to_file(
                        sorted_chords, config.logging.log_to_path)
            display_notification(title, message, self.config_wrapper)


def _print_map(sorted_chords):
    for k, v in sorted_chords:
        print(k, v)
    print("-------------------------------")


def _write_log_to_file(sorted_chords, path: str):

    log_path = safe_expand_user(Path(path))

    log_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [f"{k} {v}" for k, v in sorted_chords]
    log_path.write_text("\n".join(lines) + "\n")
