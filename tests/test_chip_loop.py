from queue import Queue
from buffer import RingBuffer
from chip_loop import chip_loop, process_event
from chip_loop_utils import ChipLoopData, ExpectedString
import pytest
from modifier_utils import DownMods
from my_frozen_dict import MyFrozenDict
from my_key_event import MyKeyEvent
from .mocks import SimpleConfigWrapperMock, NotificationSenderMock, ChordTrig
from .utils import events_from_text, list_to_queue, create_event_queue_str


class ChipLoopMock(ChipLoopData):
    def __init__(self, content: str, chords: dict[MyFrozenDict, str], commands: dict[str, list]):
        self.notification_sender = NotificationSenderMock()
        self.config_wrapper = SimpleConfigWrapperMock(
            data=chords, commands=commands)
        self.buffer = RingBuffer(200)
        for ch in content:
            self.buffer.add(ch)
        self.backspace_list = []
        self.expacted_string = ExpectedString()
        self.current_event = None

        if len(content) > 0:
            self.prev_event = MyKeyEvent(content[-1], False, DownMods())
        else:
            self.prev_event = None


def _basic_chip_loop_data(initial_data: str) -> ChipLoopMock:
    STR_CHORDS = {"t": "the", "s": "these",
                  "th": "that", "h": "here", "s.": "shallow", "lg": "long", "lg.": "superlong.", "ths": "that's"}
    COMMANDS = {"RL": ["reload_config"]}
    chords = {}
    for key, val in STR_CHORDS.items():
        chords[MyFrozenDict.from_string(key)] = val

    return ChipLoopMock(initial_data, chords, COMMANDS)


class TestProcessEvent:

    def test_type_windows(self):
        events = create_event_queue_str("hello there<windows>")
        data = _basic_chip_loop_data("")
        chip_loop(events, data)
        print(data.buffer.get())
        assert data.buffer.is_empty()

    @pytest.mark.parametrize(
        ("event", "expected"),
        [
            (MyKeyEvent("h", True, DownMods()), "hello thereh"),
            (MyKeyEvent("h", True, DownMods(meta_down=True)), "")
        ],
    )
    def test_clear_buffer(self, event: MyKeyEvent, expected: str):
        data = _basic_chip_loop_data("hello there")
        data.current_event = event
        process_event(data)
        assert "".join(data.buffer.get()) == expected

    @pytest.mark.parametrize(
        ("initial", "expected", "down_mods"),
        [
            ("hello", "hell", DownMods()),
            ("", "", DownMods()),
            ("\n\n", "\n", DownMods()),
            ("\n\n ", "\n\n", DownMods()),
            ("hello", "hell", DownMods(shift_down=True)),
            # TODO: is this the best behaviour, this could delete a word
            ("hello", "hell", DownMods(ctrl_down=True)),
        ],
    )
    def test_backspace(self, initial: str, expected: str, down_mods: DownMods):
        data = _basic_chip_loop_data(initial)
        data.current_event = MyKeyEvent("backspace", True, down_mods)
        process_event(data)
        assert "".join(data.buffer.get()) == expected


class TestChipLoop:
    def test_terminate(self):
        queue = create_event_queue_str("")
        data = _basic_chip_loop_data("")
        chip_loop(queue, data)
        assert True

    @pytest.mark.parametrize(
        ("text"),
        [
            "hello",
            "there",
            "ThInG",
            "long"
        ],
    )
    def test_type_str(self, text):
        queue = create_event_queue_str(text)
        data = _basic_chip_loop_data("")
        chip_loop(queue, data)
        assert "".join(data.buffer.get()) == text

    @pytest.mark.parametrize(
        ("text", "toggled"),
        [
            ("the ", "The "),
            ("that ", "That "),
            ("the <shift>", "The "),
            ("that <shift>", "That "),
            ("thing ", "Thing "),
            ("The <shift>", "the "),
            ("That <shift>", "that "),
        ],
    )
    def test_toggle_case(self, text: str, toggled: str):
        prefix = ""
        if text.endswith("<shift>"):
            prefix = "<shift>"
            text = text.removesuffix("<shift>")

        text += " "
        toggled += " "
        data = _basic_chip_loop_data(text)
        queue = create_event_queue_str(f"{prefix}<bs:{len(text)}>{toggled}")
        chip_loop(queue, data)
        assert "".join(data.buffer.get()) == toggled
        if isinstance(data.notification_sender, NotificationSenderMock):
            assert len(data.notification_sender.sent) == 0
        else:
            pytest.fail("notifier not a mock somehow")

    @pytest.mark.parametrize(
        ("text", "expected_chords"),
        [
            ("the ", [ChordTrig("the", ['t'])]),
            # single cap to uppercase
            ("The ", [ChordTrig("The", ['T'])]),
            ("That ", [ChordTrig("That", ['Th'])]),
            # all caps can't be done with a single letter
            ("THE ", []),
            ("THAT ", [ChordTrig("THAT", ['TH'])]),
            ("the", []),
            # expand multiple words
            ("the that ", [ChordTrig("the", ['t']),
             ChordTrig("that", ['th'])]),
            ("onceuponatimeinthedaysofyore ", []),
            # avoid false positives
            ("t <bs>he ", []),
            ("ht <bs:3>that ", []),
            # TODO:
            # in case of autocaptlization after puncuation, could be refined
            # so that it only works after punctuation instead of always
            # being negative
            ("t <bs:2>The ", []),
            ("th <bs:3>That ", []),
            ("ht <bs:3>That ", []),

            ("that. ", [ChordTrig("that", ['th'])]),
            ("these@ ", [ChordTrig("these", ['s'])]),
            ("th. <bs:2>at. ", []),
            ("th, <bs:2>at, ", []),
            ("ht, <bs:4>that, ", []),
            ("s. <bs:2>shallow", []),
            ("these. ", [ChordTrig("these", ['s'])]),
            ("These. ", [ChordTrig("These", ['S'])]),
            ("shallow ", [ChordTrig("shallow", ["s."])]),
            ("th <bs:3>that ", [ChordTrig("that", ['th'])]),
            ("lt <bs:3>that ", [ChordTrig("that", ["th"])]),
            ("s, <bs:2>these, ", []),
            (".these ", [ChordTrig("these", ['s'])]),
            (".s <bs:2>these ", []),

            ("THAT ", [ChordTrig("THAT", ['TH'])]),
            ("superlong. ", [ChordTrig("superlong.", ["lg."])]),
            ("Superlong. ", [ChordTrig("Superlong.", ["Lg."])]),
            ("SUPERLONG. ", [ChordTrig("SUPERLONG.", ["LG."])]),
            ("lg. <bs:3>superlong. ", []),
            ("that <bs> ", [ChordTrig("that", ["th"])]),
            ("that. <bs> ", [ChordTrig("that", ["th"])]),
            ("that <windows>that ", [
             ChordTrig("that", ["th"]), ChordTrig("that", ["th"])]),

            ("that that ", [
             ChordTrig("that", ["th"]), ChordTrig("that", ["th"])]),
            ("th <bs>at <bs> ", []),
            ("th. <bs:2>at. <bs> ", []),
            ("that <bs>'s ", [ChordTrig("that", ["th"]),
             ChordTrig("that's", ["ths"])]),
            ("t <bs>he . <bs:3>. ", []),
            ("th <bs>at .!. <bs:5>.!. ", []),
            # the append characters don't have to match the original
            ("th <bs>at .. <bs:4>??? ", []),

            ("th <bs>at. th <bs:3>That  ", []),
            ("th <bs>at. th <bs:3>That <bs>. ", []),
        ],)
    def test_expand(self, text: str, expected_chords: list[ChordTrig]):
        queue = create_event_queue_str(text)
        data = _basic_chip_loop_data("")
        chip_loop(queue, data)

        assert isinstance(data.notification_sender,
                          NotificationSenderMock), "not a mock sender somehow"

        if expected_chords != data.notification_sender.sent and not text.endswith(" "):
            print(
                "\033[1;33mDID YOU FORGET TO PUT A SPACE AT THE END OF YOUR TEST EXPAND?\033[0m")

        assert expected_chords == data.notification_sender.sent

    def test_reload(self):
        queue = create_event_queue_str("RL ")
        data = _basic_chip_loop_data("")
        chip_loop(queue, data)

        if isinstance(data.config_wrapper, SimpleConfigWrapperMock):
            assert data.config_wrapper.has_reloaded
        else:
            pytest.fail("config wrapper wasn't a simple mock for some reason")
