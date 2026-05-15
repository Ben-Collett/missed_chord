from PySide6 import QtCore
from qt_notification_data import QtNotificationData


class NotificationBridge(QtCore.QObject):
    notify = QtCore.Signal(QtNotificationData, int)


bridge = NotificationBridge()
