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


def strip_nonalnum(word: str) -> str:
    """Remove leading/trailing non-alphanumeric characters."""
    start = 0
    end = len(word)
    while start < end and not word[start].isalnum():
        start += 1
    while end > start and not word[end - 1].isalnum():
        end -= 1
    return word[start:end]


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


def _lookup_triggers(
    primary: str,
    fallback: str,
    config_wrapper: ConfigWrapper,
) -> tuple[list[MyFrozenDict], bool]:
    """Try triggers for `primary`; if none and primary != fallback, try `fallback`.

    Returns (inputs, used_fallback). `inputs` is the matched triggers, and
    used_fallback is True only when the fallback spelling was the one that
    matched (so the caller knows to display `fallback` instead of `primary`).
    """
    inputs: list[MyFrozenDict] = config_wrapper.get_triggers(primary) or []
    used_fallback = False
    if len(inputs) == 0 and primary != fallback:
        fb = config_wrapper.get_triggers(fallback) or []
        if len(fb) > 0:
            inputs, used_fallback = fb, True
    return inputs, used_fallback


def find_triggers_for_word(
    stripped_prev: str,
    prev_word: str,
    backspaced_word: str,
    backspaced_chip: str,
    config_wrapper: ConfigWrapper,
) -> tuple[list[MyFrozenDict], str]:
    """Resolve matching triggers (and the word to display) for a space press.

    Tries, in order: exact stripped match, a capitalized variant, then an
    all-caps variant. Each step falls back to the raw prev_word spelling when
    the stripped spelling yields nothing and the two differ. Returns
    (inputs, lookup_word); inputs is empty when nothing matched.
    """
    # skip when toggling the capitalization of the previous word
    if capitalizeith(backspaced_word, 0) == prev_word or capitalizeith(backspaced_chip, 0) == prev_word:
        return [], stripped_prev

    lookup_word = stripped_prev
    inputs, used_fallback = _lookup_triggers(
        stripped_prev, prev_word, config_wrapper)
    if used_fallback:
        lookup_word = prev_word

    if len(inputs) == 0 and stripped_prev != "" and stripped_prev[0].isupper():
        cap_inputs, used_fallback = _lookup_triggers(
            uncapitlze(stripped_prev), uncapitlze(prev_word), config_wrapper)
        if used_fallback:
            lookup_word = prev_word
        inputs = valid_capitlized(cap_inputs, config_wrapper)

    if len(inputs) == 0 and is_all_caps(stripped_prev):
        lower_inputs, used_fallback = _lookup_triggers(
            stripped_prev.lower(), prev_word.lower(), config_wrapper)
        if used_fallback:
            lookup_word = prev_word
        inputs = valid_upper_case(lower_inputs, config_wrapper)

    return inputs, lookup_word


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
