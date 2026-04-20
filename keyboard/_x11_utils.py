# WARNING: HEAVY AI USAGE
import ctypes
import time
from ctypes import c_void_p, c_int, c_uint, c_ulong, c_char_p, c_long, c_char
from ._canonical_names import normalize_name, canonical_names
from ._keyboard_event import KeyboardEvent, KEY_DOWN, KEY_UP

KEYSYM_ALIASES = {
    "backspace": "BackSpace",
    "enter": "Return",
    "return": "Return",
    "esc": "Escape",
    "escape": "Escape",
    "del": "Delete",
    "delete": "Delete",
    "space": "space",
    "tab": "Tab",
    "capslock": "Caps_Lock",
    "numlock": "Num_Lock",
    "scrolllock": "Scroll_Lock",
    "left": "Left",
    "right": "Right",
    "up": "Up",
    "down": "Down",
    "pageup": "Page_Up",
    "pagedown": "Page_Down",
    "home": "Home",
    "end": "End",
    "insert": "Insert",
    "printscreen": "Print",
    "pause": "Pause",
}


def reverse_dict(d: dict, exclude=None):
    """
    Reverse a dictionary (values -> keys).

    If duplicate values exist, the later key overrides earlier ones.
    Keys listed in `exclude` are ignored.

    :param d: Original dictionary
    :param exclude: Iterable of values to exclude
    :return: Reversed dictionary
    """
    if exclude is None:
        exclude = set()
    else:
        exclude = set(exclude)

    reversed_dict = {}

    for key, value in d.items():
        if value in exclude:
            continue
        reversed_dict[value] = key  # later overrides earlier

    return reversed_dict


reversed_names = reverse_dict(canonical_names, exclude=[
                              "backspace", "tab", "space"])
# Constants
XI_KeyPress = 13
XI_KeyRelease = 14
XIAllMasterDevices = 1
GENERIC_EVENT = 35
XkbUseCoreKbd = 0x0100

XkbNewKeyboardNotifyMask = 1 << 0
XkbMapNotifyMask = 1 << 1
XkbStateNotifyMask = 1 << 2
XkbControlsNotifyMask = 1 << 3

AutoRepeatModeOff = 0
AutoRepeatModeOn = 1
AutoRepeatModeDefault = 2

MODIFIER_KEYSYMS = {
    "Shift_L": "shift",
    "Shift_R": "shift",
    "Control_L": "ctrl",
    "Control_R": "ctrl",
    "Alt_L": "alt",
    "Alt_R": "alt_gr",
    "ISO_Level3_Shift": "alt_gr",
    "Super_L": "super",
    "Super_R": "super",
    "Meta_L": "meta",
    "Meta_R": "meta",
}

MODIFIER_KEYCODES = {
    "left shift": ["Shift_L"],
    "right shift": ["Shift_R"],
    "shift": ["Shift_L", "Shift_R"],
    "ctrl": ["Control_L", "Control_R"],
    "alt": ["Alt_L"],
    "alt_gr": ["ISO_Level3_Shift", "Alt_R"],
    "windows": ["Super_L", "Super_R"],
}

# Structs


class XIEventMask(ctypes.Structure):
    _fields_ = [
        ("deviceid", c_int),
        ("mask_len", c_int),
        ("mask", ctypes.POINTER(ctypes.c_ubyte)),
    ]


class XGenericEventCookie(ctypes.Structure):
    _fields_ = [
        ("type", c_int),
        ("serial", c_ulong),
        ("send_event", c_int),
        ("display", c_void_p),
        ("extension", c_int),
        ("evtype", c_int),
        ("cookie", c_uint),
        ("data", c_void_p),
    ]


class XEvent(ctypes.Union):
    _fields_ = [
        ("type", c_int),
        ("xcookie", XGenericEventCookie),
        ("pad", c_long * 24),
    ]


class XkbAnyEvent(ctypes.Structure):
    _fields_ = [
        ("type", c_int),
        ("xkb_type", c_int),
        ("serial", c_ulong),
        ("send_event", c_int),
        ("display", c_void_p),
        ("time", c_ulong),
        ("device", c_int),
    ]


class XkbEvent(ctypes.Union):
    _fields_ = [
        ("any", XkbAnyEvent),
        ("pad", c_long * 32),
    ]


class XKeyboardState(ctypes.Structure):
    _fields_ = [
        ("key_click_percent", c_int),
        ("bell_percent", c_int),
        ("bell_pitch", c_uint),
        ("bell_duration", c_uint),
        ("led_mask", c_ulong),
        ("global_auto_repeat", c_int),
        ("auto_repeats", c_char * 32),
    ]


class XIDeviceEvent(ctypes.Structure):
    _fields_ = [
        ("type", c_int),
        ("serial", c_ulong),
        ("send_event", c_int),
        ("display", c_void_p),
        ("extension", c_int),
        ("evtype", c_int),
        ("time", c_ulong),
        ("deviceid", c_int),
        ("sourceid", c_int),
        ("detail", c_int),  # keycode
        ("root", c_ulong),
        ("event", c_ulong),
        ("child", c_ulong),
        ("root_x", ctypes.c_double),
        ("root_y", ctypes.c_double),
        ("event_x", ctypes.c_double),
        ("event_y", ctypes.c_double),
        ("flags", c_int),
        ("mods", ctypes.c_byte * 8),  # XIGroupState (simplified)
        ("group", ctypes.c_byte * 4),
        ("buttons", c_void_p),
        ("valuators", c_void_p),
    ]


# Load libraries
libX11 = ctypes.CDLL("libX11.so.6")
libXtst = ctypes.CDLL("libXtst.so.6")
libXi = ctypes.CDLL("libXi.so.6")

# ---- X11 function prototypes ----
libX11.XOpenDisplay.argtypes = [c_char_p]
libX11.XOpenDisplay.restype = c_void_p

libX11.XCloseDisplay.argtypes = [c_void_p]
libX11.XCloseDisplay.restype = c_int

libX11.XFlush.argtypes = [c_void_p]
libX11.XFlush.restype = c_int

libX11.XKeysymToKeycode.argtypes = [c_void_p, c_ulong]
libX11.XKeysymToKeycode.restype = c_uint

libX11.XStringToKeysym.argtypes = [c_char_p]
libX11.XStringToKeysym.restype = c_ulong

libX11.XDefaultRootWindow.argtypes = [c_void_p]
libX11.XDefaultRootWindow.restype = c_ulong

libX11.XNextEvent.argtypes = [c_void_p, ctypes.POINTER(XEvent)]
libX11.XNextEvent.restype = c_int

libX11.XGetEventData.argtypes = [c_void_p, ctypes.POINTER(XGenericEventCookie)]
libX11.XGetEventData.restype = c_int

libX11.XFreeEventData.argtypes = [
    c_void_p, ctypes.POINTER(XGenericEventCookie)]
libX11.XFreeEventData.restype = None

libX11.XkbKeycodeToKeysym.argtypes = [
    c_void_p,  # Display*
    c_uint,  # Keycode
    c_int,  # Group
    c_int,  # Level
]
libX11.XkbKeycodeToKeysym.restype = c_ulong

libX11.XkbQueryExtension.argtypes = [
    c_void_p,
    ctypes.POINTER(c_int),  # opcode
    ctypes.POINTER(c_int),  # event_base
    ctypes.POINTER(c_int),  # error_base
    ctypes.POINTER(c_int),  # major
    ctypes.POINTER(c_int),  # minor
]
libX11.XkbQueryExtension.restype = c_int

libX11.XkbSelectEvents.argtypes = [
    c_void_p,
    c_uint,  # deviceSpec
    c_ulong,  # affect
    c_ulong,  # values
]
libX11.XkbSelectEvents.restype = c_int
libX11.XKeysymToString.argtypes = [c_ulong]
libX11.XKeysymToString.restype = c_char_p

libX11.XGetKeyboardControl.argtypes = [
    c_void_p, ctypes.POINTER(XKeyboardState)]
libX11.XGetKeyboardControl.restype = c_int

libX11.XkbGetAutoRepeatRate.argtypes = [
    c_void_p,
    c_uint,
    ctypes.POINTER(c_uint),
    ctypes.POINTER(c_uint),
]
libX11.XkbGetAutoRepeatRate.restype = c_int


libX11.XQueryKeymap.argtypes = [
    c_void_p,
    ctypes.POINTER(ctypes.c_char),
]
libX11.XQueryKeymap.restype = c_int

# ---- XTest ----(for writing events)
libXtst.XTestFakeKeyEvent.argtypes = [
    c_void_p,  # Display*
    c_uint,  # keycode
    c_int,  # is_press
    c_ulong,  # delay
]
libXtst.XTestFakeKeyEvent.restype = c_int

# ---Xi2---(for reading events)


# function prototypes
libXi.XIQueryVersion.argtypes = [
    c_void_p, ctypes.POINTER(c_int), ctypes.POINTER(c_int)]
libXi.XIQueryVersion.restype = c_int

libXi.XISelectEvents.argtypes = [
    c_void_p,  # Display*
    c_ulong,  # Window
    ctypes.POINTER(XIEventMask),
    c_int,
]
libXi.XISelectEvents.restype = c_int


class X11Error(RuntimeError):
    pass


def _xi_set_mask(mask, event):
    mask[event >> 3] |= 1 << (event & 7)


class X11:
    def __init__(self, display_name=None):
        self.display_name = display_name
        self.display = None
        self.translator = None
        self._map_name_cache = {}

    def open(self):
        if self.display:
            return

        self.display = libX11.XOpenDisplay(
            self.display_name.encode() if self.display_name else None
        )
        if not self.display:
            raise X11Error("Failed to open X display")

        self.translator = KeyTranslator(self.display)
        self._enable_xkb_events()

    def close(self):
        if self.display:
            libX11.XCloseDisplay(self.display)
            self.display = None

    def is_key_physically_down(self, keycode: int) -> bool:
        self._require_display()

        keymap = (ctypes.c_char * 32)()

        libX11.XQueryKeymap(
            self.display,
            ctypes.cast(keymap, ctypes.POINTER(ctypes.c_char))
        )

        byte_index = keycode // 8
        bit_index = keycode % 8

        # Convert signed char → unsigned int
        byte = keymap[byte_index]
        if isinstance(byte, bytes):  # Python 3.14 returns b'\x00'
            byte = byte[0]

        return bool(byte & (1 << bit_index))

    def _require_display(self):
        if not self.display:
            raise X11Error("X11 not initialized (call open())")

    # ---- Key injection ----
    def press_keycode(self, keycode):
        self._require_display()
        libXtst.XTestFakeKeyEvent(self.display, keycode, 1, 0)
        libX11.XFlush(self.display)

    def release_keycode(self, keycode):
        self._require_display()
        libXtst.XTestFakeKeyEvent(self.display, keycode, 0, 0)
        libX11.XFlush(self.display)

    def tap_keycode(self, keycode):
        self.press_keycode(keycode)
        self.release_keycode(keycode)

    def _invalidate_layout_cache(self):
        self._map_name_cache.clear()
        self.translator.active_mods.clear()

    # ---- Keysym helpers ----

    def keysym_to_keycode(self, keysym_name: str) -> int:
        self._require_display()

        keysym = libX11.XStringToKeysym(keysym_name.encode())
        if not keysym:
            raise X11Error(f"Unknown keysym: {keysym_name}")

        keycode = libX11.XKeysymToKeycode(self.display, keysym)
        if not keycode:
            raise X11Error(f"No keycode for keysym: {keysym_name}")

        return keycode

    def keycode_to_name(self, code: int, pressed: bool) -> str:
        return self.translator.keycode_to_name(code, pressed)

    def get_auto_repeat_info(self):
        """
        Get X11 auto-repeat settings.
        Returns: (enabled: bool, delay_ms: int, interval_ms: int)
        """
        self._require_display()

        kb_state = XKeyboardState()
        if libX11.XGetKeyboardControl(self.display, ctypes.byref(kb_state)) == 0:
            return (False, 500, 50)  # defaults if query fails

        enabled = kb_state.global_auto_repeat == AutoRepeatModeOn

        delay = c_uint()
        interval = c_uint()
        if libX11.XkbGetAutoRepeatRate(
            self.display, XkbUseCoreKbd, ctypes.byref(
                delay), ctypes.byref(interval)
        ):
            delay_ms = delay.value
            interval_ms = interval.value
        else:
            delay_ms = 500
            interval_ms = 50

        return (enabled, delay_ms, interval_ms)

    def is_key_auto_repeat_enabled(self, keycode):
        """
        Check if auto-repeat is enabled for a specific key.
        Currently returns True for all keys if global auto-repeat is enabled.
        """
        self._require_display()

        kb_state = XKeyboardState()
        if libX11.XGetKeyboardControl(self.display, ctypes.byref(kb_state)) == 0:
            return False

        if kb_state.global_auto_repeat != AutoRepeatModeOn:
            return False

        if keycode < 8 or keycode > 255:
            return False

        auto_repeats_addr = ctypes.addressof(kb_state) + 28
        auto_repeats = (ctypes.c_ubyte * 32).from_address(auto_repeats_addr)

        byte_index = (keycode - 8) // 8
        bit_index = (keycode - 8) % 8

        return bool(auto_repeats[byte_index] & (1 << bit_index))

    def _enable_xkb_events(self):
        opcode = c_int()
        event_base = c_int()
        error_base = c_int()
        major = c_int(1)
        minor = c_int(0)

        if not libX11.XkbQueryExtension(
            self.display,
            ctypes.byref(opcode),
            ctypes.byref(event_base),
            ctypes.byref(error_base),
            ctypes.byref(major),
            ctypes.byref(minor),
        ):
            raise X11Error("XKB extension not available")

        self._xkb_event_base = event_base.value

        mask = (
            XkbNewKeyboardNotifyMask
            | XkbMapNotifyMask
            | XkbStateNotifyMask
            | XkbControlsNotifyMask
        )

        libX11.XkbSelectEvents(self.display, XkbUseCoreKbd, mask, mask)

    def listen(self, callback, controls_changed_callback=None):
        """
        Global keyboard listener using XInput2.
        Calls callback(event_dict) for each key press/release.

        Args:
            callback: Function called for key events
            controls_changed_callback: Optional function called when XKB controls
                                     change (e.g., auto-repeat settings)
        """
        self._require_display()

        # ---- Ensure XI2 is available ----
        major = c_int(2)
        minor = c_int(0)
        if (
            libXi.XIQueryVersion(self.display, ctypes.byref(
                major), ctypes.byref(minor))
            != 0
        ):
            raise X11Error("XInput2 not available")

        root = libX11.XDefaultRootWindow(self.display)

        # ---- Select raw key events ----
        mask_len = (XI_KeyPress >> 3) + 1
        mask = (ctypes.c_ubyte * mask_len)()

        _xi_set_mask(mask, XI_KeyPress)
        _xi_set_mask(mask, XI_KeyRelease)

        evmask = XIEventMask()
        evmask.deviceid = XIAllMasterDevices
        evmask.mask_len = len(mask)
        evmask.mask = ctypes.cast(mask, ctypes.POINTER(ctypes.c_ubyte))

        libXi.XISelectEvents(self.display, root, ctypes.byref(evmask), 1)
        libX11.XFlush(self.display)

        # ---- Event loop ----
        event = XEvent()

        while True:
            libX11.XNextEvent(self.display, ctypes.byref(event))

            if event.type != GENERIC_EVENT:
                continue

            # --- XKB layout change ---
            if event.type == self._xkb_event_base:
                xkb = ctypes.cast(
                    ctypes.byref(event), ctypes.POINTER(XkbEvent)
                ).contents

                if xkb.any.xkb_type in (
                    0,  # XkbNewKeyboardNotify
                    1,  # XkbMapNotify
                    2,  # XkbStateNotify
                ):
                    self._invalidate_layout_cache()
                elif xkb.any.xkb_type == 3:  # XkbControlsNotify
                    if controls_changed_callback:
                        controls_changed_callback()
                continue

            cookie = event.xcookie
            if not libX11.XGetEventData(self.display, ctypes.byref(cookie)):
                continue

            try:
                if cookie.evtype in (XI_KeyPress, XI_KeyRelease):
                    dev = ctypes.cast(
                        cookie.data, ctypes.POINTER(XIDeviceEvent)
                    ).contents

                    pressed = cookie.evtype == XI_KeyPress
                    event_type = KEY_DOWN if pressed else KEY_UP
                    code = dev.detail
                    t = dev.time
                    key_event = KeyboardEvent(
                        event_type=event_type,
                        scan_code=code,
                        time=t,
                        name=self.keycode_to_name(code, pressed),
                        device=dev.deviceid,
                        modifiers=tuple(sorted(self.translator.active_mods)),
                    )
                    callback(key_event)
            finally:
                libX11.XFreeEventData(self.display, ctypes.byref(cookie))

    def map_name(self, name):
        # name = normalize_name(name)
        # print(name)
        # if name in CHAR_TO_KEYSYM:
        #     name = CHAR_TO_KEYSYM[name]

        if name in reversed_names.keys():
            name = reversed_names[name]

        # ---- cache lookup ----
        cached = self._map_name_cache.get(name)
        if cached is not None:
            yield from cached
            return

        results = []

        # ---- modifiers ----
        if name in MODIFIER_KEYCODES:
            for ks in MODIFIER_KEYCODES[name]:
                try:
                    code = self.keysym_to_keycode(ks)
                    if code:
                        results.append((code, ()))
                except X11Error:
                    pass

            self._map_name_cache[name] = tuple(results)
            yield from results
            return

        # ---- uppercase letters ----
        if len(name) == 1 and name.isalpha() and name.isupper():
            base = name.lower()
            for code, mods in self.map_name(base):
                results.append((code, tuple(sorted(mods + ("shift",)))))

            self._map_name_cache[name] = tuple(results)
            yield from results
            return

        # ---- aliases ----
        keysym_name = KEYSYM_ALIASES.get(name, name)
        keysym = libX11.XStringToKeysym(keysym_name.encode())
        if not keysym:
            self._map_name_cache[name] = ()
            return

        # ---- expensive scan (cached!) ----
        for keycode in range(8, 256):
            for level, mods in (
                (0, ()),
                (1, ("shift",)),
                (2, ("alt_gr",)),
                (3, ("shift", "alt_gr")),
            ):
                ks = libX11.XkbKeycodeToKeysym(self.display, keycode, 0, level)
                if ks == keysym:
                    results.append((keycode, mods))

        self._map_name_cache[name] = tuple(results)
        yield from results

    def type_unicode(self, char: str, delay: float = 0.0):
        """
        Types a single Unicode character using:
        1) Direct keysym injection if available
        2) Ctrl+Shift+U hex input fallback
        """
        self._require_display()

        if len(char) != 1:
            raise X11Error("type_unicode expects a single character")

        # ---- Attempt 1: direct keysym ----
        keysym = libX11.XStringToKeysym(char.encode("utf-8"))
        if keysym:
            keycode = libX11.XKeysymToKeycode(self.display, keysym)
            if keycode:
                self.tap_keycode(keycode)
                if delay:
                    time.sleep(delay)
                return

        # ---- Attempt 2: Ctrl+Shift+U fallback ----
        # Resolve required keycodes
        ctrl = self.keysym_to_keycode("Control_L")
        shift = self.keysym_to_keycode("Shift_L")
        u = self.keysym_to_keycode("u")
        enter = self.keysym_to_keycode("Return")

        # Press Ctrl + Shift + U
        self.press_keycode(ctrl)
        self.press_keycode(shift)
        self.tap_keycode(u)

        # Type hexadecimal Unicode codepoint
        hex_digits = format(ord(char), "x")
        for digit in hex_digits:
            kc = self.keysym_to_keycode(digit)
            self.tap_keycode(kc)
            if delay:
                time.sleep(delay)

        # Confirm with Enter
        self.tap_keycode(enter)

        # Release modifiers
        self.release_keycode(shift)
        self.release_keycode(ctrl)


class KeyTranslator:
    def __init__(self, display):
        self.display = display
        self.active_mods = set()

    def _keysym_name(self, keysym):
        if not keysym:
            return None
        name = libX11.XKeysymToString(keysym)
        return name.decode() if name else None

    def _is_shift(self):
        return "shift" in self.active_mods

    def _is_altgr(self):
        return "alt_gr" in self.active_mods

    def keycode_to_name(self, keycode, pressed: bool):
        """
        Returns:
          - modifier name ("shift", "ctrl", ...)
          - regular key name ("a", "A", "F1", ...)
        """

        # Level selection:
        # level 0 = normal
        # level 1 = shift
        # level 2 = altgr
        level = 0
        if self._is_altgr():
            level = 2
        elif self._is_shift():
            level = 1

        keysym = libX11.XkbKeycodeToKeysym(
            self.display,
            keycode,
            0,  # group (keyboard layout group)
            level,
        )

        name = self._keysym_name(keysym)
        if not name:
            return None

        # Modifier?
        if name in MODIFIER_KEYSYMS:
            mod = MODIFIER_KEYSYMS[name]
            if pressed:
                self.active_mods.add(mod)
            else:
                self.active_mods.discard(mod)
            return mod

        return normalize_name(name.lower())
