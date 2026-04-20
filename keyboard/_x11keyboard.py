# WARNING: HEAVY AI USAGE
# WARNING: key repeats when holding a key down are attempted to be handled but aren't 100% reliable
# sometimes you will get one or two to many event other times you will miss one, this is because I can't find
# in x11 a way to listen to key repeat events so I have to try to take the timer and match it and inject fake events
# if the times get desynced from some sort of unlucky race condition with the schedular then the events will be desynced usually by one or two events
# If a user cares I would highly encourage not using repeated keys when held down maybe I can add an option to disable native handling on the x11 side
# and use keyboard.write to put real events ofcourse that would require a user be willing to disable or allow the program to disable that setting
import threading
import time
from ._x11_utils import X11, MODIFIER_KEYCODES
from ._keyboard_event import KeyboardEvent, KEY_DOWN, KEY_UP


def init():
    pass


x = None

x = X11()
x.open()
# used to release a key before typing it if a user pressed down the key
# won't work if the user pressed the key before the program started
# we have to store the down keys because if we send an up before a down in all
# cases it will actually send an up event even  if the key wasn't already down
down_keys = set()

# Auto-repeat tracking
# keycode -> (press_time, last_repeat_time, key_name, modifiers)

_repeating_keycode = None
_repeat_key_name = None
_repeat_press_time = 0.0
_repeat_timer = None

_repeat_lock = threading.Lock()
_repeating_keycode = None
_repeat_press_time = 0
_repeat_last_time = 0
_repeat_key_name = None
_auto_repeat_enabled = True
_auto_repeat_delay_ms = 500
_auto_repeat_interval_ms = 50
_auto_repeat_lock = threading.Lock()
_auto_repeat_thread = None
_auto_repeat_stop_event = threading.Event()
_user_callback = None


def _is_modifier(name: str) -> bool:
    if not name:
        return False
    name = name.lower()
    out = name in MODIFIER_KEYCODES.keys()
    return out


def _cancel_repeat():
    global _repeat_timer, _repeating_keycode

    if _repeat_timer:
        _repeat_timer.cancel()
        _repeat_timer = None

    _repeating_keycode = None


def _repeat_fire():
    global _repeat_timer

    with _repeat_lock:
        keycode = _repeating_keycode
        key_name = _repeat_key_name

        if keycode is None:
            return

        # Hard physical check (important)
        if not x.is_key_physically_down(keycode):
            _cancel_repeat()
            return

        now = time.monotonic()

        synthetic_event = KeyboardEvent(
            event_type=KEY_DOWN,
            scan_code=keycode,
            time=int(now * 1000),
            name=key_name,
            device="synthetic",
            modifiers=set(down_keys),
        )

        if _user_callback:
            _user_callback(synthetic_event)

        # Schedule next repeat
        interval = _auto_repeat_interval_ms / 1000.0
        _repeat_timer = threading.Timer(interval, _repeat_fire)
        _repeat_timer.daemon = True
        _repeat_timer.start()


def _start_repeat(keycode, key_name):
    global _repeating_keycode
    global _repeat_key_name
    global _repeat_press_time
    global _repeat_timer

    _cancel_repeat()

    _repeating_keycode = keycode
    _repeat_key_name = key_name
    _repeat_press_time = time.monotonic()

    delay = _auto_repeat_delay_ms / 1000.0

    _repeat_timer = threading.Timer(delay, _repeat_fire)
    _repeat_timer.daemon = True
    _repeat_timer.start()


def _update_auto_repeat_settings():
    """Query X11 for current auto-repeat settings."""
    global _auto_repeat_enabled, _auto_repeat_delay_ms, _auto_repeat_interval_ms
    try:
        enabled, delay_ms, interval_ms = x.get_auto_repeat_info()
        with _auto_repeat_lock:
            _auto_repeat_enabled = enabled
            _auto_repeat_delay_ms = delay_ms
            _auto_repeat_interval_ms = interval_ms
    except Exception:
        pass  # Use defaults if query fails


def map_name(name):
    return x.map_name(name)


def press(code: int, shiftpressed: bool = False):
    if code in down_keys:
        x.release_keycode(code)
    x.press_keycode(code)


def release(code: int, shiftpressed: bool = False):
    x.release_keycode(code)


def type_unicode(char):
    x.type_unicode(char)


def listen(callback):
    global _user_callback
    _user_callback = callback

    # Update auto-repeat settings from X11
    _update_auto_repeat_settings()

    def wrapper(event: KeyboardEvent):
        global _repeating_keycode
        global _repeat_press_time
        global _repeat_last_time
        global _repeat_key_name

        if event.event_type == KEY_DOWN:
            down_keys.add(event.scan_code)

            if event.device != "synthetic":
                is_modifier = _is_modifier(event.name)

                with _repeat_lock:
                    if not is_modifier:
                        _start_repeat(event.scan_code, event.name)

        elif event.event_type == KEY_UP:
            if event.scan_code in down_keys:
                down_keys.remove(event.scan_code)

            with _repeat_lock:
                # Stop repeating if this key was repeating
                if event.scan_code == _repeating_keycode:
                    _cancel_repeat()

        # Only forward real events
        if event.device != "synthetic":
            callback(event)

    # Define callback for when XKB controls change (auto-repeat settings)

    def on_controls_changed():
        _update_auto_repeat_settings()

    try:
        x.listen(wrapper, controls_changed_callback=on_controls_changed)
    finally:
        pass
