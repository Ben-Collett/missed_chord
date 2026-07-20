from config_wrapper import ConfigWrapper
from my_key_event import TERMINATE_EVENT
from buffer import RingBuffer
from logger import log_warning
from queue import Queue
from my_key_event import MyKeyEvent
from commands import Command
from notifier import ConfigNotificationSender
from utils import dicts_to_strings, overlap_count
from chip_loop_utils import ChipLoopData, probable_chip, capitalizeith, is_captlized, uncapitlze, ExpectedString, strip_nonalnum, find_triggers_for_word


def process_event_wrapper(event: MyKeyEvent, data: ChipLoopData):
    data.prev_event = data.current_event
    data.current_event = event
    process_event(data)


def process_event(data: ChipLoopData):
    event = data.current_event
    if event is None:
        return

    expected_string = data.expacted_string
    config_wrapper = data.config_wrapper
    prev_event = data.prev_event
    buffer = data.buffer
    name = event.name
    meta_down = event.modifiers.meta_down
    backspace_list = data.backspace_list

    expanding = not expected_string.is_empty()
    ch = None
    if event.is_down:
        ch = event.to_utf()
        expected_string.clear_if_should(ch)

    if meta_down:
        buffer.clear()
        data.last_chip_output = None
        return

    prev_word = buffer.get_prev_word()

    if prev_event is not None:
        just_shifted = prev_event.is_down and "shift" in prev_event.name
    else:
        just_shifted = False

    is_shift_release_event = event.is_up and "shift" in name
    if just_shifted and is_shift_release_event and not expanding:
        expected_string.set_value(prev_word+" ")
        expected_string.toggle_case()
    elif event.is_up:
        return
    # guaranteed to be a down event past this point

    if name == "backspace":
        backspaced = buffer.backspace()
        if backspaced:
            if backspaced.isspace():
                backspace_list.clear()
            else:
                backspace_list.append(backspaced)

        # the previous word was fully deleted, so any chip notified for it is
        # no longer "in play"; a later retype counts as a brand new word
        if buffer.get_prev_word() == "":
            data.last_chip_output = None

        return

    if name == "space" and not expanding:
        white_space = buffer.get_trailing_white_space()
        chip = probable_chip(prev_word, config_wrapper)
        if white_space == "" and chip is not None:
            overlap = overlap_count(chip, prev_word)
            non_overlap = chip[overlap:]+" "
            expected_string.set_value(non_overlap)

            data.last_chip_output = chip

            buffer.add(" ")
            return
        elif white_space == "":
            """
            here is the rough approach if there is an exact match the user could have used a chip
            if there is not an exact match but the first word was captlized or in allcaps then 
            maybe there was a match if it's in all caps then maybe there was an approah
            instead of checking all cases I'm only going to handle when the inputs are all lower case
            and I'm only checking cpatlizing the first 1 or 2 character
            """

            stripped_prev = strip_nonalnum(prev_word)

            # if the (stripped) word is itself a chip trigger, note its output so
            # that backspacing and re-forming the same chip isn't notified again
            stripped_chip = config_wrapper.get_chip(stripped_prev)
            if stripped_chip is not None:
                data.last_chip_output = stripped_chip

            changing_case = is_captlized(prev_word) and uncapitlze(
                prev_word) == "".join(reversed(backspace_list))
            if not changing_case:

                backspaced_word = "".join(backspace_list)
                backspaced_chip = config_wrapper.get_chip(
                    backspaced_word) or ""

                # if statement prevents triggering when toggling the captlizaiton of prev word
                if capitalizeith(backspaced_word, 0) != prev_word and capitalizeith(backspaced_chip, 0) != prev_word:

                    inputs, lookup_word = find_triggers_for_word(
                        stripped_prev, prev_word, backspaced_word, backspaced_chip, config_wrapper)

                    inputs_list: list[str] = dicts_to_strings(inputs)

                    if len(inputs_list) > 0 and not (
                        stripped_prev != prev_word and backspace_list
                    ):
                        # avoid re-notifying the same chip while the user is just
                        # refining a word they already saw a notification for.
                        # compare case-insensitively: "That" and "that" are the
                        # same chip (only capitalization differs, e.g. after a
                        # punctuation mark)
                        if lookup_word.casefold() != (data.last_chip_output or "").casefold():
                            data.send_notification(
                                lookup_word, inputs_list)
                        data.last_chip_output = lookup_word
    if name == "space":
        backspace_list.clear()

    if ch:
        # an alphanumeric typed right after a real word-separating space starts
        # a new word; clear the last chip so a later identical chip can notify.
        # skip when an expansion is still being completed (expected_string set)
        # and ignore non-alphanumeric chars (punctuation appended to a word
        # doesn't start a new word worth re-notifying)
        if ch.isalnum() and prev_event is not None and prev_event.name == "space" and expected_string.is_empty():
            data.last_chip_output = None
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


def chip_loop(event_queue: Queue, data: ChipLoopData):
    while True:
        event = event_queue.get()
        if event == TERMINATE_EVENT:
            break
        process_event_wrapper(event, data)


def chip_key_loop(key_queue: Queue, config_wrapper: ConfigWrapper):
    BUFFER_SIZE = 200
    buffer = RingBuffer(BUFFER_SIZE)
    expected_string = ExpectedString()
    notifier = ConfigNotificationSender(config_wrapper=config_wrapper)

    chip_data = ChipLoopData(config_wrapper=config_wrapper, current_event=None, prev_event=None, backspace_list=[
    ], expacted_string=expected_string, buffer=buffer, notification_sender=notifier)
    chip_loop(key_queue, chip_data)
