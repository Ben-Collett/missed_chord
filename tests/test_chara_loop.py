from collections import deque
from buffer import RingBuffer
from chara_loop import CharaLoopData, process_event, chara_loop
import pytest
from modifier_utils import DownMods
from queue import Queue
from my_key_event import TERMINATE_EVENT, MyKeyEvent
from my_frozen_dict import MyFrozenDict
from .mocks import SimpleConfigWrapperMock, NotificationSenderMock, ChordTrig
from .utils import create_event_queue_str


class CharaLoopMock(CharaLoopData):
    def __init__(self, content: str, chords: dict[MyFrozenDict, str], commands: dict[str, list]):
        self.notification_sender = NotificationSenderMock()
        self.config_wrapper = SimpleConfigWrapperMock(
            data=chords, commands=commands)
        self.buffer = RingBuffer(200)
        for ch in content:
            self.buffer.add(ch)
        self.backspace_queue = deque()
        self.possible_chords = []
        self.just_backspaced = False
        self.event = None


def _basic_chara_loop_data(initial_data: str) -> CharaLoopMock:
    STR_CHORDS = {"te": "the", "sg": "these",
                  "th": "that", "ade": "here", "lg": "LONG"}
    COMMANDS = {"RL": ["reload_config"]}
    chords = {}
    for key, val in STR_CHORDS.items():
        chords[MyFrozenDict.from_string(key)] = val

    return CharaLoopMock(initial_data, chords, COMMANDS)


class TestCharaProcessEvent:

    @pytest.mark.parametrize(
        ("event", "expected"),
        [
            (MyKeyEvent("h", True, DownMods()), "hello thereh"),
            (MyKeyEvent("h", True, DownMods(meta_down=True)), "")
        ],
    )
    def test_clear_buffer(self, event: MyKeyEvent, expected: str):
        data = _basic_chara_loop_data("hello there")
        data.event = event
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
        data = _basic_chara_loop_data(initial)
        data.event = MyKeyEvent("backspace", True, down_mods)
        process_event(data)
        assert "".join(data.buffer.get()) == expected


class TestCharaLoop:
    def test_terminate(self):
        queue = Queue()
        queue.put(TERMINATE_EVENT)
        data = _basic_chara_loop_data("")
        chara_loop(queue, data)
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
        data = _basic_chara_loop_data("")
        chara_loop(queue, data)
        assert "".join(data.buffer.get()) == text

    @pytest.mark.parametrize(
        ("text", "toggled"),
        [
            ("the", "The"),
            ("that", "That"),
            ("thing", "Thing"),
            # TODO: I don't know what's happening here:
            # ("The", "the"),
            # ("That", "that"),
        ],
    )
    def test_toggle_case(self, text: str, toggled: str):

        text += " "
        toggled += " "
        data = _basic_chara_loop_data(text)
        queue = create_event_queue_str(f"<bs:{len(text)}>{toggled}")
        chara_loop(queue, data)
        assert "".join(data.buffer.get()) == toggled
        if isinstance(data.notification_sender, NotificationSenderMock):
            assert len(data.notification_sender.sent) == 0
        else:
            pytest.fail("notifier not a mock somehow")

    @pytest.mark.parametrize(
        ("text", "expected_chords"),
        [
            ("the ", [ChordTrig("the", ['te'])]),
            # single cap to uppercase
            ("The ", [ChordTrig("The", ['te'])]),
            ("That ", [ChordTrig("That", ['th'])]),
            # all caps can't be done with a single letter
            ("LONG ", [ChordTrig("LONG", ["lg"])]),
            ("THAT ", []),

            # no space
            ("the", []),
            # expand multiple words
            ("the that ", [ChordTrig("the", ['te']),
             ChordTrig("that", ['th'])]),
            ("onceuponatimeinthedaysofyore ", []),
            # avoid false positives
            ("te<bs:2>the ", []),
            ("ht<bs:2>that ", []),
            # in case the user presses shift while chording
            ("te<bs:2>The ", []),
            ("th<bs:2>That ", []),
            ("ht<bs:2>That ", []),


            ("ht<bs:2>that <bs> ", []),
            ("th that ", [ChordTrig("that", ['th'])]),
            ("that that ", [ChordTrig("that", ['th']),
             ChordTrig("that", ['th'])]),
            ("th that <bs>  <bs:2> ", [ChordTrig("that", ['th'])]),
            ("lt<bs:2>that ", [ChordTrig("that", ["th"])]),
        ],)
    def test_expand(self, text: str, expected_chords: list[ChordTrig]):
        queue = create_event_queue_str(text)
        data = _basic_chara_loop_data("")
        chara_loop(queue, data)

        assert isinstance(data.notification_sender,
                          NotificationSenderMock), "not a mock sender somehow"

        if expected_chords != data.notification_sender.sent and not text.endswith(" "):
            print(
                "\033[1;33mDID YOU FORGET TO PUT A SPACE AT THE END OF YOUR TEST EXPAND?\033[0m")
        assert expected_chords == data.notification_sender.sent

    def test_reload(self):
        queue = create_event_queue_str("RL ")
        data = _basic_chara_loop_data("")
        chara_loop(queue, data)

        if isinstance(data.config_wrapper, SimpleConfigWrapperMock):
            assert data.config_wrapper.has_reloaded
        else:
            pytest.fail("config wrapper wasn't a simple mock for some reason")
