from config_wrapper import ConfigWrapper
from my_frozen_dict import MyFrozenDict
import utils
from my_key_event import TERMINATE_EVENT, MyKeyEvent
from collections import deque
import send_notification
from queue import Queue
from buffer import RingBuffer
from commands import Command
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


def _handle_commands(prev_word, buffer, config_wrapper: ConfigWrapper):
    for command in config_wrapper.get_commands(prev_word):
        if command == Command.RELOAD:
            config_wrapper.reload(log=True)
        elif command == Command.CLEAR_BUFFER:
            buffer.clear()
        else:
            log_warning("unknown command somehow", command)


def _process_event(event: MyKeyEvent, data: CharaLoopData, config_wrapper: ConfigWrapper):
    buffer = data.buffer
    backspace_queue = data.backspace_queue
    possible_chords = data.possible_chords

    meta_down = event.modifiers.meta_down
    is_arrow = event.is_arrow

    if meta_down or is_arrow:
        buffer.clear()
        possible_chords.clear()
        backspace_queue.clear()
        return

    if event.is_up:
        return

    if event.is_backspace:
        data.just_backspaced = True
        ch = buffer.backspace()
        if ch is not None:
            # lower makes it work if user presses shift while chording
            backspace_queue.append(ch.lower())
        backspaced = "".join(backspace_queue)
        chord = config_wrapper.get_chord(backspaced)

        if chord is not None:
            append_captlized_and_uncaptlized(possible_chords, chord)
        if ch == " " or ch is None:
            backspace_queue.clear()
            possible_chords.clear()

    utf = event.to_utf()
    if not utf:
        return

    buffer.add(utf)

    prev_word = buffer.get_prev_word()
    if buffer.get_trailing_white_space() == " ":
        inputs: list[MyFrozenDict] | None = config_wrapper.get_triggers(
            prev_word)

        if inputs is None:
            prev_uncap = utils.uncapitalize(prev_word)
            inputs = config_wrapper.get_triggers(prev_uncap)

        if config_wrapper.has_command(prev_word):
            _handle_commands(prev_word, buffer, config_wrapper)
        elif inputs and prev_word not in possible_chords:
            options = utils.dicts_to_strings(inputs)
            send_notification.display_message(
                prev_word, options, config_wrapper)
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


def _process_event_wrapper(event: MyKeyEvent, data: CharaLoopData, config_wrapper: ConfigWrapper):
    _process_event(event, data, config_wrapper)


def chara_key_loop(key_queue: Queue, config_wrapper: ConfigWrapper):

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
        _process_event_wrapper(event, data, config_wrapper)
