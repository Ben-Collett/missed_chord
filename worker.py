from PySide6 import QtCore

from config_wrapper import ConfigWrapper


class MainWorker(QtCore.QThread):
    def __init__(self, key_itr, config_wrapper: ConfigWrapper):
        super().__init__()
        self.key_itr = key_itr
        self.config_wrapper = config_wrapper

    def run(self):
        import key_event_loop
        key_event_loop.key_loop(self.key_itr, self.config_wrapper)

    def stop(self):
        self.running.value = False
