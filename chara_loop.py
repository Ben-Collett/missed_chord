import utils
from my_key_event import TERMINATE_EVENT, MyKeyEvent
from config import current_config
import keyboard_utils
from collections import deque
import send_notification
from queue import Queue
from buffer import RingBuffer
from commands import Commands
from modifier_utils import DownMods
from logger import log_warning


def chara_key_loop(key_queue: Queue):

    buffer = RingBuffer(100)
    backspace_queue = deque()

    probably_chording = False

    prev_chord = ""
    probably_chording_string = ""
    expected_chording_string = ""
    just_shifted = False
    changing_case = False
    backspace_counter = 0
    bc = 0

    def process_event(event: MyKeyEvent):
        nonlocal backspace_counter
        nonlocal probably_chording
        nonlocal expected_chording_string
        nonlocal probably_chording_string
        nonlocal prev_chord
        nonlocal changing_case
        nonlocal just_shifted
        nonlocal bc

        name: str = event.name
        pressed_key = event.is_down_event
        pressed_or_held_key = pressed_key
        released_key = event.is_up_event
        is_space = keyboard_utils.is_space(name)
        chords = current_config.data
        reversed_chords = current_config.reversed
        down_modes = DownMods.from_event(event)

        is_backspace = event.name == "backspace"
        utf = None
        if len(event.name) == 1:
            utf = event.name
            if down_modes.shift_down:
                utf = utf.upper()
        if is_space:
            utf = " "

        if is_backspace and released_key:
            return
        if is_backspace and changing_case and pressed_or_held_key:
            backspace_counter += 1
            if backspace_counter > len(prev_chord)+1:
                backspace_counter = 0
                changing_case = False
            if len(buffer) > 0:
                buffer.backspace()
            return
        if backspace_counter > 0:
            backspace_queue.clear()
            changing_case = False
            if utf is not None:
                backspace_counter -= 1
                buffer.add(utf)
            return

        is_shift = keyboard_utils.is_shift(name)

        if is_shift and pressed_or_held_key:
            just_shifted = True
        elif is_shift and just_shifted:
            changing_case = True
            just_shifted = False
        else:
            just_shifted = False

        # TODO: shift,both ways

        if is_backspace and pressed_or_held_key:
            if len(buffer) > 0:
                backspace_queue.append(buffer.backspace())
                if frozenset(backspace_queue) in chords.keys():
                    probably_chording = True
                    expected_chording_string = chords[frozenset(
                        backspace_queue)]
                return

        if (not is_backspace) and pressed_or_held_key:
            backspace_queue.clear()

        if released_key:
            return
        if down_modes.meta_down or keyboard_utils.is_arrow(name):
            buffer.clear()
            return

        if utf is not None and utf.isprintable():
            buffer.add(utf)
            if probably_chording:
                if len(probably_chording_string) == 0:
                    probably_chording_string = utf.lower()
                else:
                    probably_chording_string += utf
            elif keyboard_utils.is_space(name):
                tmp = ""
                # using 2 because need to skip the first element in the negative direction which is always a " "
                for i in range(2, current_config.max_output_length+1):
                    if i > len(buffer):
                        break
                    ls = buffer.get()
                    tmp = ls[-i]+tmp
                    behind_is_space = True  # default to true if the buffer is to small
                    if i+1 <= len(ls):
                        behind_is_space = ls[-i-1] == " "

                    if utils.uncapitalize(tmp) in reversed_chords.keys() and behind_is_space:
                        inputs = reversed_chords[utils.uncapitalize(tmp)]
                        options = utils.sets_to_string(inputs)
                        send_notification.display_message(tmp, options)

            if name == "space" and buffer.get_trailing_white_space() == " ":
                prev_word = buffer.get_prev_word()
                if prev_word in current_config.command_map.keys():
                    for command in current_config.command_map[prev_word]:
                        if command == Commands.RELOAD:
                            current_config.reload()
                        elif command == Commands.CLEAR_BUFFER:
                            buffer.clear()
                        else:
                            log_warning("unknown command somehow", command)

            # auto handles stopping when typign space
            if not expected_chording_string.startswith(probably_chording_string):
                if expected_chording_string == probably_chording_string.strip():
                    prev_chord = expected_chording_string
                probably_chording_string = ""
                expected_chording_string = ""
                probably_chording = False

    # Process output line by line as it arrives
    while True:
        event = key_queue.get()
        if event == TERMINATE_EVENT:
            break
        process_event(event)
