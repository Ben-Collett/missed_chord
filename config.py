# auto generated
import math
from chording_modes import ChordingMode
from duration import Duration
from parse_command_section import parse_command_section
from notification_modes import NotificationMode

class _ExpectedField:
    def __init__(self, default_value=None, cftype=None):
        self.default_value = default_value
        self.cftype = cftype


class _ExpectedList:
    def __init__(self, default_value=None, cftype=None, min_length=0, max_length=math.inf):
        default_value = default_value or []
        self.default_value = default_value
        self.cftype = cftype
        self.min_length = min_length
        self.max_length = max_length


class _ExpectedDict:
    def __init__(self, default_value=None, key_type=None, value_type=None, min_length=0, max_length=math.inf):
        default_value = default_value or {}
        self.default_value = default_value
        self.key_type = key_type
        self.cftype = value_type
        self.min_length = min_length
        self.max_length = max_length

def _check_type(value, expected_type) -> bool:
    if expected_type is None:
        return True
    if expected_type == bool:
        return isinstance(value, bool)
    if expected_type == int:
        return isinstance(value, int) and not isinstance(value, bool)
    if expected_type == str:
        return isinstance(value, str)
    if expected_type == float:
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected_type == list:
        return isinstance(value, list)
    if expected_type == dict:
        return isinstance(value, dict)
    return isinstance(value, expected_type)

def _merge_expected(config_map: dict, expected_map: dict, ignored_sections=set(), ignored_keys=set()) -> dict:
    result = {}

    for section_name, section_expected in expected_map.items():
        result[section_name] = {}
        for field_name, field_expected in section_expected.items():
            result[section_name][field_name] = field_expected.default_value

    for section_name, section_config in config_map.items():
        if section_name not in expected_map:
            if section_name in ignored_sections:
                result[section_name] = section_config.copy()
            else:
                print(f"Unused section: {section_name}")
            continue

        if not isinstance(section_config, dict):
            print(f"Type error in section '{section_name}': expected dict, got {type(section_config).__name__}")
            continue

        for field_name, field_value in section_config.items():
            if field_name not in expected_map[section_name]:
                if field_name in ignored_keys or section_name in ignored_sections:
                    result[section_name][field_name] = field_value
                else:
                    print(f"Unused field: {section_name}.{field_name}")
                continue

            field_expected = expected_map[section_name][field_name]

            if isinstance(field_expected, _ExpectedField):
                if _check_type(field_value, field_expected.cftype):
                    result[section_name][field_name] = field_value
                else:
                    print(f"Type error: {section_name}.{field_name} expected {field_expected.cftype}, got {type(field_value).__name__}")

            elif isinstance(field_expected, _ExpectedList):
                if not isinstance(field_value, list):
                    print(f"Type error: {section_name}.{field_name} expected list, got {type(field_value).__name__}")
                elif field_expected.cftype and not all(_check_type(v, field_expected.cftype) for v in field_value):
                    print(f"Type error: {section_name}.{field_name} expected list of {field_expected.cftype}")
                elif not (field_expected.min_length <= len(field_value) <= field_expected.max_length):
                    print(f"Length error: {section_name}.{field_name} length {len(field_value)} not in range [{field_expected.min_length}, {field_expected.max_length}]")
                else:
                    result[section_name][field_name] = field_value

            elif isinstance(field_expected, _ExpectedDict):
                if not isinstance(field_value, dict):
                    print(f"Type error: {section_name}.{field_name} expected dict, got {type(field_value).__name__}")
                elif field_expected.key_type and not all(_check_type(k, field_expected.key_type) for k in field_value.keys()):
                    print(f"Type error: {section_name}.{field_name} expected dict with keys of {field_expected.key_type}")
                elif field_expected.cftype and not all(_check_type(v, field_expected.cftype) for v in field_value.values()):
                    print(f"Type error: {section_name}.{field_name} expected dict with values of {field_expected.cftype}")
                elif not (field_expected.min_length <= len(field_value) <= field_expected.max_length):
                    print(f"Length error: {section_name}.{field_name} length {len(field_value)} not in range [{field_expected.min_length}, {field_expected.max_length}]")
                else:
                    result[section_name][field_name] = field_value

    return result

def _get_expected_map():
    return {"general": {"mode": _ExpectedField("charachorder", str)}, "notification": {"mode": _ExpectedField("auto", str), "title": _ExpectedField("possible missed chord", str), "message": _ExpectedField("$triggers = $chord", str), "duration": _ExpectedField(None)}, "filter": {"blocked": _ExpectedList([], str), "allowed": _ExpectedList([], str)}, "qt": {"duration_height": _ExpectedField(8, int), "max_notifications": _ExpectedField(3, int), "notification_width": _ExpectedField(400, int), "notification_height": _ExpectedField(100, int)}, "logging": {"log_to_stdout": _ExpectedField(False, bool), "log_to_path": _ExpectedField("", str)}, "experimental": {"notification_bar_update_frequency": _ExpectedField(None)}}

class Config:
    def __init__(self, config_map: dict | None = None):
        if not config_map:
            config_map = {}
        merged = _merge_expected(
            config_map, _get_expected_map()
            , ignored_sections={'commands'}
        )
        self.general = GeneralSection(merged["general"])
        self.notification = NotificationSection(merged["notification"])
        self.filter = FilterSection(merged["filter"])
        self.qt = QtSection(merged["qt"])
        self.logging = LoggingSection(merged["logging"])
        self.experimental = ExperimentalSection(merged["experimental"])
        self.commands = parse_command_section(merged)

    def update(self, config_map: dict | None = None):
        if not config_map:
            config_map = {}
        merged = _merge_expected(
            config_map, _get_expected_map()
            , ignored_sections={'commands'}
        )
        self.general.update(merged["general"])
        self.notification.update(merged["notification"])
        self.filter.update(merged["filter"])
        self.qt.update(merged["qt"])
        self.logging.update(merged["logging"])
        self.experimental.update(merged["experimental"])
        self.commands = parse_command_section(merged)

class GeneralSection:
    def __init__(self, smap: dict):
        self.update(smap)

    def update(self, smap: dict):
        self.mode: ChordingMode = ChordingMode.parse(smap["mode"])

class NotificationSection:
    def __init__(self, smap: dict):
        self.update(smap)

    def update(self, smap: dict):
        self.mode: NotificationMode = NotificationMode.parse(smap["mode"])
        self.title: str = smap["title"]
        self.message: str = smap["message"]
        self.duration: Duration = Duration.parse(smap["duration"], Duration(3000))

class FilterSection:
    def __init__(self, smap: dict):
        self.update(smap)

    def update(self, smap: dict):
        self.blocked: list[str] = smap["blocked"]
        self.allowed: list[str] = smap["allowed"]

class QtSection:
    def __init__(self, smap: dict):
        self.update(smap)

    def update(self, smap: dict):
        self.duration_height: int = smap["duration_height"]
        self.max_notifications: int = smap["max_notifications"]
        self.notification_width: int = smap["notification_width"]
        self.notification_height: int = smap["notification_height"]

class LoggingSection:
    def __init__(self, smap: dict):
        self.update(smap)

    def update(self, smap: dict):
        self.log_to_stdout: bool = smap["log_to_stdout"]
        self.log_to_path: str = smap["log_to_path"]

class ExperimentalSection:
    def __init__(self, smap: dict):
        self.update(smap)

    def update(self, smap: dict):
        self.notification_bar_update_frequency: Duration = Duration.parse(smap["notification_bar_update_frequency"], Duration(0))
