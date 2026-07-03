from config_wrapper import ConfigWrapper
from my_frozen_dict import MyFrozenDict
from my_key_event import TERMINATE_EVENT
from buffer import RingBuffer
from logger import log_warning
from queue import Queue
from my_key_event import MyKeyEvent
from commands import Command
from notifier import ConfigNotificationSender
from utils import dicts_to_strings, overlap_count
from chip_loop_utils import ChipLoopData, probable_chip, capitalizeith, is_captlized, uncapitlze, valid_capitlized, valid_upper_case, ExpectedString, is_all_caps


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

        return

    if name == "space" and not expanding:
        white_space = buffer.get_trailing_white_space()
        chip = probable_chip(prev_word, config_wrapper)
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

            changing_case = is_captlized(prev_word) and uncapitlze(
                prev_word) == "".join(reversed(backspace_list))
            if not changing_case:

                backspaced_word = "".join(backspace_list)
                backspaced_chip = config_wrapper.get_chip(
                    backspaced_word) or ""
                if capitalizeith(backspaced_word, 0) != prev_word and capitalizeith(backspaced_chip, 0) != prev_word:
                    inputs: list[MyFrozenDict] = config_wrapper.get_triggers(
                        prev_word) or []

                    if prev_word != "" and len(inputs) == 0 and prev_word[0].isupper():
                        uncapped = uncapitlze(prev_word)
                        uncapped_triggers = config_wrapper.get_triggers(
                            uncapped) or []

                        inputs = valid_capitlized(
                            uncapped_triggers, config_wrapper)
                    if len(inputs) == 0 and is_all_caps(prev_word):
                        lower = prev_word.lower()
                        lower_triggers = config_wrapper.get_triggers(
                            lower) or []
                        inputs = valid_upper_case(
                            lower_triggers, config_wrapper)

                    inputs_list: list[str] = dicts_to_strings(inputs)

                    if len(inputs_list) > 0:
                        data.send_notification(
                            prev_word, inputs_list)
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
