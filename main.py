import sys
import signal
from config import current_config
import queue
from my_key_event import MyKeyEvent, TERMINATE_EVENT
import threading
import keyboard


def main():
    keyboard.init(windows_synetic_mode=keyboard.WindowsSyntheticModes.REAL)
    key_queue = queue.Queue()

    def add_to_queue(event: keyboard.KeyboardEvent):
        value = 0
        if event.event_type == keyboard.KEY_DOWN:
            value = 1
        my_event = MyKeyEvent(event.name, value, event.modifiers)
        key_queue.put_nowait(my_event)

    keyboard.hook(add_to_queue)

    def kill_key_reader():
        key_queue.put_nowait(TERMINATE_EVENT)
        keyboard.unhook_all()

    if current_config.qt_mode:

        from PySide6 import QtWidgets, QtCore
        from qt_notification_manager import QTNotificationManager
        from qt_bridge import bridge
        from worker import MainWorker

        app = QtWidgets.QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(False)

        sigint_timer = QtCore.QTimer()
        sigint_timer.start(100)
        sigint_timer.timeout.connect(lambda: None)
        worker = MainWorker(key_queue)

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
            key_loop(key_queue)
        except KeyboardInterrupt:
            kill_key_reader()


if __name__ == "__main__":
    main()
