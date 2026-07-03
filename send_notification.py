from config_wrapper import ConfigWrapper
from qt_notification_data import QtNotificationData
from sudo_send import sudo_safe_send_notification, sudo_safe_send_progress_notification

missed_chords: dict[str, int] = {}


def display_notification(title: str, message: str, config_wrapper: ConfigWrapper):
    config = config_wrapper.config

    notification_duration = config.notification.duration.milliseconds
    update_frequency = config.experimental.notification_bar_update_frequency.milliseconds
    if config_wrapper.qt_mode():
        from qt_bridge import bridge
        qt = config.qt
        max_notifications = qt.max_notifications
        data = QtNotificationData(title=title, content=message, duration_ms=notification_duration,
                                  width=qt.notification_width, height=qt.notification_height, duration_height=qt.duration_height)
        bridge.notify.emit(data, max_notifications)
    elif update_frequency > 0:
        sudo_safe_send_progress_notification(
            title, message, notification_duration, update_frequency)
    else:
        sudo_safe_send_notification(title, message, notification_duration)
