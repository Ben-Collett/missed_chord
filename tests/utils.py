from queue import Queue
from modifier_utils import DownMods
from my_key_event import MyKeyEvent, TERMINATE_EVENT
_NAMED_EVENTS = {
    "bs": "backspace",
    "tab": "tab",
    "enter": "enter",
    "return": "enter",
    "esc": "escape",
    "escape": "escape",
    "del": "delete",
    "delete": "delete",
    "up": "up",
    "down": "down",
    "left": "left",
    "right": "right",
    "home": "home",
    "end": "end",
    "pgup": "page up",
    "pgdn": "page down",
}


def list_to_queue(elements: list) -> Queue:
    queue = Queue()
    for element in elements:
        queue.put(element)
    return queue


def ev(name: str, is_down=True, down_mods=None) -> MyKeyEvent:
    if down_mods is None:
        down_mods = DownMods()
    return MyKeyEvent(name, is_down, down_mods)


def events_from_text(text: str, terminate=True) -> list[MyKeyEvent]:
    out = []
    i = 0
    while i < len(text):
        if text[i] == '<':
            end = text.find('>', i)
            if end == -1:
                ch = text[i]
                shift_down = ch.isupper()
                out.append(ev(ch, True, DownMods(shift_down=shift_down)))
                out.append(ev(ch, False))
                i += 1
                continue

            inner = text[i + 1:end]

            if ':' in inner:
                name, count_str = inner.split(':', 1)
                try:
                    count = int(count_str)
                except ValueError:
                    count = 1
            else:
                name = inner
                count = 1

            resolved_name = _NAMED_EVENTS.get(name, name)

            for _ in range(count):
                out.append(ev(resolved_name, True))
                out.append(ev(resolved_name, False))

            i = end + 1
        else:
            ch = text[i]
            shift_down = ch.isupper()
            if ch == " ":
                ch = "space"
            elif ch == "\t":
                ch = "tab"
            elif ch == "\n":
                ch = "enter"
            out.append(ev(ch, True, DownMods(shift_down=shift_down)))

            out.append(ev(ch, False))
            i += 1
    if terminate:
        out.append(TERMINATE_EVENT)
    return out


def create_event_queue_str(text: str, terminate=True):
    return list_to_queue(events_from_text(text, terminate))
