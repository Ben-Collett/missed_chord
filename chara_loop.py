import utils
from my_key_event import TERMINATE_EVENT, MyKeyEvent
from config import current_config
from collections import deque
import send_notification
from queue import Queue
from buffer import RingBuffer
from commands import Commands
from modifier_utils import DownMods
from logger import log_warning
from dataclasses import dataclass




def captlized_and_uncaptlized(word: str):
    assert word != "", "why are you trying captlized an empty word dummy"
    start, *rest = word
    rest = "".join(rest)
    return start.upper() + rest, start.lower() + rest


def append_captlized_and_uncaptlized(ls: list[str], word: str):
    cap, uncap = captlized_and_uncaptlized(word)
    ls.append(cap)
    ls.append(uncap)


@dataclass
class CharaLoopData:
    buffer: RingBuffer
    backspace_queue: deque[str]
    possible_chords: list[str]
    just_backspaced: bool = False


def _handle_commands(prev_word, buffer, config):
    for command in config.command_map[prev_word]:
        if command == Commands.RELOAD:
            current_config.reload()
        elif command == Commands.CLEAR_BUFFER:
            buffer.clear()
        else:
            log_warning("unknown command somehow", command)


def _process_event(event: MyKeyEvent, data: CharaLoopData):
    buffer = data.buffer
    backspace_queue = data.backspace_queue
    possible_chords = data.possible_chords

    down_mods = DownMods.from_event(event)
    meta_down = down_mods.meta_down
    shift_down = down_mods.shift_down
    is_arrow = event.is_arrow

    chords = current_config.data
    reversed_chords = current_config.reversed

    if meta_down or is_arrow:
        buffer.clear()
        possible_chords.clear()
        backspace_queue.clear()
        return

    if event.is_up_event:
        return

    if event.is_backspace:
        data.just_backspaced = True
        ch = buffer.backspace()
        if ch is not None:
            # lower makes it work if user presses shift while chording
            backspace_queue.append(ch.lower())
        s = frozenset(backspace_queue)
        if s in chords:
            append_captlized_and_uncaptlized(possible_chords, chords[s])
        if ch == " " or ch is None:
            backspace_queue.clear()
            possible_chords.clear()

    utf = event.to_utf(shift_down)
    if not utf:
        return

    buffer.add(utf)

    prev_word = buffer.get_prev_word()
    if buffer.get_trailing_white_space() == " ":
        prev_uncap = utils.uncapitalize(prev_word)
        inputs = None
        if prev_word in reversed_chords.keys():
            inputs = reversed_chords[prev_word]
        elif prev_uncap in reversed_chords.keys():
            inputs = reversed_chords[prev_uncap]

        if prev_word in current_config.command_map.keys():
            _handle_commands(prev_word, buffer, current_config)
        elif inputs and prev_word not in possible_chords:
            options = utils.sets_to_string(inputs)
            send_notification.display_message(prev_word, options)
            possible_chords.clear()

    # I need to check length in case the user backspaced while the buffer was empty
    if len(backspace_queue) > 0 and data.just_backspaced:
        word = "".join(reversed(backspace_queue))
        append_captlized_and_uncaptlized(possible_chords, word)

    index = len(prev_word) - 1
    possible_chords = [
        word for word in possible_chords if len(word) > index and word[index] == utf]
    if len(possible_chords) == 0:
        backspace_queue.clear()

    data.possible_chords = possible_chords
    # we early return with the if not utf check if we backspaced, so this is guaranteed to be false
    data.just_backspaced = False


def _process_event_wrapper(event: MyKeyEvent, data: CharaLoopData):
    _process_event(event, data)
    # print(data.buffer)
    # print(data.possible_chords)


def chara_key_loop(key_queue: Queue):

    buffer = RingBuffer(100)
    backspace_queue = deque()
    possible_chords = []
    just_backspaced = False

    data = CharaLoopData(buffer=buffer,
                         backspace_queue=backspace_queue,
                         possible_chords=possible_chords,
                         just_backspaced=just_backspaced)
    while True:
        event = key_queue.get()
        if event == TERMINATE_EVENT:
            break
        _process_event_wrapper(event, data)
