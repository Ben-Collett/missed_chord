from config_wrapper import ConfigWrapper
from my_frozen_dict import MyFrozenDict
from my_key_event import TERMINATE_EVENT
from buffer import RingBuffer
import send_notification
from logger import log_warning
from queue import Queue
from my_key_event import MyKeyEvent
from commands import Command
from modifier_utils import DownMods
from itertools import combinations
from utils import dicts_to_strings, overlap_count


def _upper_count(s: str):
    count = 0
    for ch in s:
        if ch.isalpha() and ch.isupper():
            count += 1
    return count


def is_captlized(s: str):
    return s != "" and s[0].isupper()


def _all_caps(s: str):
    for ch in s:
        if ch.isalpha() and not ch.isupper():
            return False
    return True


def _all_lower(iter):
    for ch in iter:
        if ch.isalpha() and not ch.islower():
            return False
    return True


def _uncapitlze(s: str):
    if s == "":
        return ""
    return s[0].lower() + s[1:]


def capitalizeith(s: str, i: int) -> str:
    if i >= len(s):
        return s

    return s[:i] + s[i].upper() + s[i+1:]


def _valid_capitlized(inputs: list[MyFrozenDict], config_wrapper: ConfigWrapper) -> list[MyFrozenDict]:
    out: list[MyFrozenDict] = []
    input_strs: list[str] = dicts_to_strings(inputs)
    for inp in input_strs:
        # uncapping the character can only work if all lower, in fuzzy chips
        if _all_lower(inp):
            for i in range(len(inp)):
                tmp = capitalizeith(inp, i)
                # if chip has exact match it doesn't work for uncapping
                if not config_wrapper.has_chip(tmp):
                    out.append(MyFrozenDict.from_string(tmp))
                    break
    return out


def _valid_upper_case(inputs: list[MyFrozenDict], config_wrapper: ConfigWrapper):
    out: list[MyFrozenDict] = []
    input_strs: list[str] = dicts_to_strings(inputs)
    for inp in input_strs:
        # uncapping the character can only work if all lower, in fuzzy chips
        if _all_lower(inp):

            def no_chip(trig):
                return not config_wrapper.has_chip(trig)
            tmp = _find_match_captitle_iter(inp, no_chip)
            if tmp is not None:
                out.append(MyFrozenDict.from_string(tmp))
    return out


def _find_match_captitle_iter(s, condition):
    # vibed function
    """
    iterate over all possible captlization combinations of a lower case string until hitting
    one that matches the condition, what ever condition returns is returned or none is returned if there is no match
    positions with nonalphanumeric characters are ignored by the mask
    """
    # only letters can actually change case
    positions = [i for i, c in enumerate(s) if c.isalpha() and c.islower()]

    chars = list(s)

    # choose 2 or more positions to capitalize
    for r in range(2, len(positions) + 1):
        for combo in combinations(positions, r):

            # copy original
            candidate = chars.copy()

            # capitalize selected positions
            for i in combo:
                candidate[i] = candidate[i].upper()

            result = ''.join(candidate)

            if condition(result):
                return result

    return None


def _probable_chip(prev_word: str, config_wrapper: ConfigWrapper) -> str | None:
    chip = config_wrapper.get_chip(prev_word)

    upper_count = _upper_count(prev_word)

    if not chip and upper_count > 1:
        lower_result = config_wrapper.get_chip(prev_word.lower())
        if lower_result:
            chip = lower_result.upper()
    elif not chip:
        lower_result = config_wrapper.get_chip(prev_word.lower())
        if lower_result:
            chip = capitalizeith(lower_result, 0)
    return chip


class _ExpectedString:
    def __init__(self):
        self._value: list[str] = []

    def set_value(self, value: str):
        self._value[:] = value

    def clear(self):
        self._value.clear()

    def is_empty(self):
        return len(self._value) == 0

    def starts_with(self, ch: str):
        if self.is_empty():
            return False
        return self._value[0] == ch

    def should_clear(self, ch: str | None):
        if ch is None:
            return False
        return not self.starts_with(ch)

    def clear_if_should(self, ch: str | None):
        if self.should_clear(ch):
            self.clear()

    def toggle_case(self):
        self._no_remove_since_update = True
        if self.is_empty():
            return
        start = self._value[0]
        if start.isupper():
            self._value[0] = start.lower()
        else:
            self._value[0] = start.upper()

    def safe_remove_first(self):
        if not self.is_empty():
            self._value.pop(0)
            self._no_remove_since_update = False

    def append(self, ch: str):
        self._no_remove_since_update = True
        self._value.append(ch)


def chip_key_loop(key_queue: Queue, config_wrapper: ConfigWrapper):
    BUFFER_SIZE = 200

    buffer = RingBuffer(BUFFER_SIZE)
    # just a list for performance really a string
    expected_string: _ExpectedString = _ExpectedString()
    backspace_list = []
    prev_event: MyKeyEvent | None = None

    def process_event(event: MyKeyEvent):
        nonlocal buffer, expected_string
        name = event.name
        value = event.value
        down_modes = DownMods.from_event(event)
        shift_down = down_modes.shift_down
        meta_down = down_modes.meta_down

        expanding = not expected_string.is_empty()
        ch = None
        if value == 1:
            if name == "space":
                ch = " "
            elif len(name) == 1 and shift_down:
                ch = name.upper()
            elif len(name) == 1:
                ch = name

            expected_string.clear_if_should(ch)

        if meta_down:
            buffer.clear()
            return

        prev_word = buffer.get_prev_word()

        if prev_event is not None:
            just_shifted = prev_event.is_down_event and "shift" in prev_event.name
        else:
            just_shifted = False

        is_shift_release_event = event.is_up_event and "shift" in name
        if just_shifted and is_shift_release_event and not expanding:
            expected_string.set_value(prev_word+" ")
            expected_string.toggle_case()
        elif value == 0:
            return
        # guaranteed to be a down event past this point

        if name == "backspace":
            backspaced = buffer.backspace()
            if backspaced:
                if backspaced.isspace():
                    backspace_list.clear()
                else:
                    backspace_list.append(backspaced)

            return

        if name == "space" and not expanding:
            white_space = buffer.get_trailing_white_space()
            chip = _probable_chip(prev_word, config_wrapper)
            if white_space == "" and chip is not None:
                overlap = overlap_count(chip, prev_word)
                non_overlap = chip[overlap:]+" "
                expected_string.set_value(non_overlap)

                buffer.add(" ")
                return
            elif white_space == "":
                """
                here is the ruff approach if there is an exact match the user could have used a chip
                if there is not an exact match but the first word was captlized or in allcaps then 
                maybe there was a match if it's in all caps then maybe there was an approah
                instead of checking all cases I'm only going to handle when the inputs are all lower case
                and I'm only checking cpatlizing the first 1 or 2 character
                """

                changing_case = is_captlized(prev_word) and _uncapitlze(
                    prev_word) == "".join(reversed(backspace_list))
                if not changing_case:

                    backspaced_word = "".join(backspace_list)
                    backspaced_chip = config_wrapper.get_chip(
                        backspaced_word) or ""
                    if capitalizeith(backspaced_word, 0) != prev_word and capitalizeith(backspaced_chip, 0) != prev_word:
                        inputs: list[MyFrozenDict] = config_wrapper.get_triggers(
                            prev_word) or []

                        if len(inputs) == 0 and prev_word[0].isupper():
                            uncapped = _uncapitlze(prev_word)
                            uncapped_triggers = config_wrapper.get_triggers(
                                uncapped) or []

                            inputs = _valid_capitlized(
                                uncapped_triggers, config_wrapper)
                        if len(inputs) == 0 and _all_caps(prev_word):
                            lower = prev_word.lower()
                            lower_triggers = config_wrapper.get_triggers(
                                lower) or []
                            inputs = _valid_upper_case(
                                lower_triggers, config_wrapper)

                        inputs_list: list[str] = dicts_to_strings(inputs)

                        if len(inputs_list) > 0:
                            send_notification.display_message(
                                prev_word, inputs_list, config_wrapper)
        if name == "space":
            backspace_list.clear()

        if ch:
            expected_string.safe_remove_first()
            buffer.add(ch)

        if name == "space" and buffer.get_trailing_white_space() == " ":
            commands = config_wrapper.get_commands(prev_word)
            for command in commands:
                if command == Command.RELOAD:
                    config_wrapper.reload(log=True)
                elif command == Command.CLEAR_BUFFER:
                    buffer.clear()
                else:
                    log_warning("unknown command somehow", command)

    def process_event_wrapper(event: MyKeyEvent):
        nonlocal prev_event, expected_string
        process_event(event)
        prev_event = event
    while True:
        event = key_queue.get()
        if event == TERMINATE_EVENT:
            break
        process_event_wrapper(event)
