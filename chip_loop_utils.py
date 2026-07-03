from dataclasses import dataclass
from itertools import combinations
from buffer import RingBuffer
from config_wrapper import ConfigWrapper
from my_frozen_dict import MyFrozenDict
from my_key_event import MyKeyEvent
from notifier import NotificationSender
from utils import dicts_to_strings


def count_upper_case(s: str):
    count = 0
    for ch in s:
        if ch.isalpha() and ch.isupper():
            count += 1
    return count


def is_captlized(s: str):
    return s != "" and s[0].isupper()


def is_all_caps(s: str):
    for ch in s:
        if ch.isalpha() and not ch.isupper():
            return False
    return True


def is_all_lower(iter):
    for ch in iter:
        if ch.isalpha() and not ch.islower():
            return False
    return True


def uncapitlze(s: str):
    if s == "":
        return ""
    return s[0].lower() + s[1:]


def capitalizeith(s: str, i: int) -> str:
    if i >= len(s):
        return s

    return s[:i] + s[i].upper() + s[i+1:]


def valid_capitlized(inputs: list[MyFrozenDict], config_wrapper: ConfigWrapper) -> list[MyFrozenDict]:
    out: list[MyFrozenDict] = []
    input_strs: list[str] = dicts_to_strings(inputs)
    for inp in input_strs:
        # uncapping the character can only work if all lower, in fuzzy chips
        if is_all_lower(inp):
            for i in range(len(inp)):
                tmp = capitalizeith(inp, i)
                # if chip has exact match it doesn't work for uncapping
                if not config_wrapper.has_chip(tmp):
                    out.append(MyFrozenDict.from_string(tmp))
                    break
    return out


def valid_upper_case(inputs: list[MyFrozenDict], config_wrapper: ConfigWrapper):
    out: list[MyFrozenDict] = []
    input_strs: list[str] = dicts_to_strings(inputs)
    for inp in input_strs:
        # uncapping the character can only work if all lower, in fuzzy chips
        if is_all_lower(inp):

            def no_chip(trig):
                return not config_wrapper.has_chip(trig)
            tmp = find_match_captitle_iter(inp, no_chip)
            if tmp is not None:
                out.append(MyFrozenDict.from_string(tmp))
    return out


def find_match_captitle_iter(s, condition):
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


def probable_chip(prev_word: str, config_wrapper: ConfigWrapper) -> str | None:
    chip = config_wrapper.get_chip(prev_word)

    upper_count = count_upper_case(prev_word)

    if not chip and upper_count > 1:
        lower_result = config_wrapper.get_chip(prev_word.lower())
        if lower_result:
            chip = lower_result.upper()
    elif not chip:
        lower_result = config_wrapper.get_chip(prev_word.lower())
        if lower_result:
            chip = capitalizeith(lower_result, 0)
    return chip


class ExpectedString:
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


@dataclass
class ChipLoopData:
    # not changed by loop
    config_wrapper: ConfigWrapper
    notification_sender: NotificationSender
    # changed by process event
    buffer: RingBuffer
    backspace_list: list[str]
    expacted_string: ExpectedString

    # changed by process_event_wrapper
    current_event: MyKeyEvent | None
    prev_event:  MyKeyEvent | None = None

    # TODO: ugly, nice for testing but sending notification from
    # data is ugly
    def send_notification(self, chord, triggers):
        self.notification_sender.send_notification(chord, triggers)
