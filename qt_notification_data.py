from dataclasses import dataclass


@dataclass
class QtNotificationData:
    title: str
    content: str
    duration_ms: int
    width: int
    height: int
    duration_height: int
