import enum
import os
import errno
import ctypes
import platform


class KeyboardModes(enum.Enum):
    LINUX = "Linux",
    WINDOWS = "Windows",
    MAC = "Darwin",
    X11 = "X11",
    UNKNOWN = "UNKNOWN"


def auto_select_keyboard_mode():
    system = platform.system()

    # ---------------- Windows ----------------
    if system == "Windows":
        return KeyboardModes.WINDOWS

    # ---------------- macOS ----------------
    if system == "Darwin":
        return KeyboardModes.MAC

    # ---------------- Linux ----------------
    if system == "Linux":
        if can_use_evdev_uinput():
            return KeyboardModes.LINUX

        if can_use_x11():
            return KeyboardModes.X11

        raise RuntimeError(
            "Linux keyboard backend unavailable.\n"
            "Either:\n"
            "  • Run as root or with sudo\n"
            "  • Add user to the 'input' and 'tty' groups\n"
            "  • Enable uinput (modprobe uinput)\n"
            "  • Or run under X11"
        )

    # ---------------- Unknown OS ----------------
    # Try X11 first
    if can_use_x11():
        return KeyboardModes.X11

    # Then try Linux-style evdev/uinput
    if can_use_evdev_uinput():
        return KeyboardModes.LINUX

    raise RuntimeError(
        f"Unsupported operating system: {system}\n"
        "No supported keyboard backend detected.\n"
        "Tried X11 and evdev/uinput."
    )


def can_access_console():
    try:
        fd = os.open("/dev/console", os.O_RDONLY)
        os.close(fd)
        return True
    except OSError:
        return False

# needs to be able to dump keys, read a device and open a device


def can_use_evdev_uinput():

    # console access is needed to use dump-keys
    if not can_access_console():
        return False

    try:

        # evdev: can we read input devices?
        if not os.path.exists("/dev/input"):
            return False

        # must have at least one event device
        if not any(name.startswith("event") for name in os.listdir("/dev/input")):
            return False

        # uinput: can we open it?
        fd = os.open("/dev/uinput", os.O_WRONLY | os.O_NONBLOCK)
        os.close(fd)
        return True

    except OSError as e:
        if e.errno in (errno.EACCES, errno.EPERM):
            return False
        return False


def can_use_x11():
    if os.environ.get("WAYLAND_DISPLAY"):
        return False

    if os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland":
        return False

    if "DISPLAY" not in os.environ:
        return False

    try:
        x11 = ctypes.cdll.LoadLibrary("libX11.so.6")

        x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
        x11.XOpenDisplay.restype = ctypes.c_void_p

        x11.XCloseDisplay.argtypes = [ctypes.c_void_p]
        x11.XCloseDisplay.restype = ctypes.c_int

        display = x11.XOpenDisplay(None)
        if not display:
            return False

        x11.XCloseDisplay(display)
        return True

    except Exception:
        return False
