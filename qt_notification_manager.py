from PySide6 import QtWidgets
from qt_notification import QtNotification, QtNotificationData


class QTNotificationManager:
    def __init__(self):
        self.notifications: list[QtNotification] = []

    def remove_window(self, window: QtNotification):
        self.notifications.remove(window)
        self.update_positions()

    def update_positions(self):
        for i, window in enumerate(self.notifications):
            number_before = len(self.notifications) - i - 1
            window.update_position(number_before)

    def send_notification(self, notification_data: QtNotificationData, max_notifications: int):
        widget = QtNotification(notification_data, self.remove_window)
        self.notifications.append(widget)

        while len(self.notifications) > max_notifications:
            # automatically gets removed from the list on close
            self.notifications[0].close()
        self.update_positions()

        widget.show()
