import keyboard
import sys


def output_event(event: keyboard.KeyboardEvent):
    value = 0
    if event.event_type == keyboard.KEY_DOWN:
        value = 1
    print(event.name, value, " ".join(event.modifiers), sep=" ")
    for mod in event.modifiers:
        print


def main():
    keyboard.hook(output_event)
    try:
        keyboard.wait()
    except KeyboardInterrupt:
        pass
    finally:
        keyboard.unhook_all()
        sys.exit(0)


if __name__ == "__main__":
    main()
