import sys
import signal
import queue
import argparse
from config_wrapper import ConfigWrapper
from notification_modes import NotificationMode
from my_key_event import MyKeyEvent, TERMINATE_EVENT
import keyboard


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--update-chords", action="store_true",
                        help="update chord backup from charachorder device")
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("-c", "--force-chara", action="store_true",
                            help="force charachorder mode regardless of config")
    mode_group.add_argument("-f", "--force-fuzzy", action="store_true",
                            help="force fuzzy chips mode regardless of config")
    args = parser.parse_args()

    if args.update_chords:
        # has to be in here to avoid hard requirement on
        # pyserial
        from update_chord_backup import update_chord_backup
        update_chord_backup()
        return

    config_wrapper = ConfigWrapper(
        force_chara=args.force_chara,
        force_fuzzy=args.force_fuzzy,
    )
    keyboard.init(windows_synetic_mode=keyboard.WindowsSyntheticModes.REAL)
    key_queue = queue.Queue()

    def add_to_queue(event: keyboard.KeyboardEvent):
        key_queue.put_nowait(MyKeyEvent.from_keyboard_event(event))

    keyboard.hook(add_to_queue)

    def kill_key_reader():
        key_queue.put_nowait(TERMINATE_EVENT)
        keyboard.unhook_all()

    if config_wrapper.qt_mode():

        from PySide6 import QtWidgets, QtCore
        from qt_notification_manager import QTNotificationManager
        from qt_bridge import bridge
        from worker import MainWorker

        app = QtWidgets.QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(False)

        sigint_timer = QtCore.QTimer()
        sigint_timer.start(100)
        sigint_timer.timeout.connect(lambda: None)
        worker = MainWorker(key_queue, config_wrapper)

        def handle_sigint(sig, frame):
            kill_key_reader()
            worker.wait()
            app.quit()

        signal.signal(signal.SIGINT, handle_sigint)

        manager = QTNotificationManager()
        bridge.notify.connect(manager.send_notification)

        worker.start()

        sys.exit(app.exec())

    else:
        from key_event_loop import key_loop

        try:
            key_loop(key_queue, config_wrapper)
        except KeyboardInterrupt:
            kill_key_reader()


if __name__ == "__main__":
    main()
