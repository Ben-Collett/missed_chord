import sys
import signal
import queue
from config_wrapper import ConfigWrapper
from notification_modes import NotificationMode
from my_key_event import MyKeyEvent, TERMINATE_EVENT
import keyboard


def main():
    config_wrapper = ConfigWrapper()
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
