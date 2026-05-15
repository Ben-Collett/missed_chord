from enum import Enum
from logger import log_warning
from utils import is_on_linux


class NotificationMode(Enum):
    QT = "qt"
    NOTIFY = "notify"

    @staticmethod
    def parse(mode: str):

        modes = [member.value for member in NotificationMode]
        modes.append("auto")
        if mode not in modes:
            log_warning(
                f"invalid mode selected, {mode} not in {modes} , defaulting to auto")
            mode = "auto"

        if mode == "auto":
            if is_on_linux():
                mode = "notify"
            else:
                mode = "qt"

        return NotificationMode(mode)
