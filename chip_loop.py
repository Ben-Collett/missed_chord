from config import current_config
from my_key_event import TERMINATE_EVENT
from buffer import RingBuffer
import send_notification
from logger import log_warning
from queue import Queue
from my_key_event import MyKeyEvent
from commands import Commands


def chip_key_loop(key_queue: Queue):

    buffer = RingBuffer(200)
    shift_down = False
    meta_down = False
    expected_string = []

    def process_event(event: MyKeyEvent):
        nonlocal expected_string, buffer
        nonlocal shift_down, meta_down
        name = event.name
        value = event.value

        chips = current_config.data
        reversed_chips = current_config.reversed
        ch = None
        if value == 1:
            if name == "space":
                ch = " "
            elif len(name) == 1 and shift_down:
                ch = name.upper()
            elif len(name) == 1:
                ch = name
            if ch and len(expected_string) > 0 and ch != expected_string[0]:
                expected_string = []

        expanding = len(expected_string) != 0

        if "windows" in event.name:
            meta_down = event.value == 1

        if meta_down:
            buffer.clear()
            return

        if value == 0 and "shift" in name:
            shift_down = False
        elif value == 1 and "shift" in name:
            shift_down = True
            return

        prev_word = buffer.get_prev_word()

        if value == 0 and "shift" in name and not expanding:
            expected_string = list(prev_word)
            expected_string.append(" ")
            if expected_string[0].isupper():
                expected_string[0] = expected_string[0].lower()
            else:
                expected_string[0] = expected_string[0].upper()

        elif value == 0:
            return
        # guaranteed to be a down event past this point

        if name == "backspace":
            buffer.backspace()
            return

        if name == "space" and not expanding:
            white_space = buffer.get_trailing_white_space()
            prev_word_set = frozenset(prev_word)
            if prev_word_set in chips.keys() and white_space == "":
                expected_string = list(chips[prev_word_set])
                to_remove_count = 0

                for i in range(min(len(expected_string), len(prev_word))):
                    if expected_string[i] != prev_word[i]:
                        break
                    to_remove_count += 1

                for i in range(0, to_remove_count):
                    expected_string.pop(0)

                expected_string.append(" ")
                buffer.add(" ")
                return
            elif prev_word in reversed_chips.keys() and white_space == "":
                inputs = reversed_chips[prev_word]
                inputs_list: list[str] = []
                for input in inputs:
                    inputs_list.append(''.join(input))
                send_notification.display_message(prev_word, inputs_list)

        if ch:
            if len(expected_string) > 0:
                expected_string.pop(0)
            buffer.add(ch)
        if name == "space" and buffer.get_trailing_white_space() == " " and prev_word in current_config.command_map:
            commands = current_config.command_map[prev_word]
            for command in commands:
                if command == Commands.RELOAD:
                    current_config.reload()
                elif command == Commands.CLEAR_BUFFER:
                    buffer.clear()
                else:
                    log_warning("unknown command somehow", command)

    while True:
        event = key_queue.get()
        if event == TERMINATE_EVENT:
            break
        process_event(event)
