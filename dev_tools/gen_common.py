from config_generator import Builder, GenAny, GenStr, GenList, GenCustom, GenInt, build_python, build_toml
from pathlib import Path


def make_builder() -> Builder:

    import_statements = [
        "from chording_modes import ChordingMode",
        "from duration import Duration",
        "from parse_command_section import parse_command_section",
        "from notification_modes import NotificationMode"]
    chord_mode = GenCustom(
        parse_command="ChordingMode.parse($value)", config_value=GenStr("charachorder"), code_type="ChordingMode")

    notification_mode = GenCustom(
        parse_command="NotificationMode.parse($value)", config_value=GenStr("auto"), code_type="NotificationMode")
    duration = GenCustom(
        parse_command="Duration.parse($value, Duration(3000))", config_value=GenAny(GenInt(3000)), code_type="Duration")
    update_frequency = GenCustom(
        parse_command="Duration.parse($value, Duration(0))", config_value=GenAny(GenInt(0)), code_type="Duration")

    # Initialize builder with TOML formatting settings matching the example
    builder = Builder(
        code_indent="    ",
        config_indent="  ",
        config_new_line="\n",
        code_new_line="\n",
        config_comment_sep=" ",
        import_statements=import_statements,
    )
    builder.comment(" general notification config(not qt specific)")
    builder.add_section("general")
    builder.comment(
        ' used to set between "charachorder" mode and "fuzzy chips", later may support different chording methods in charachroder,defaults to charachorder')
    builder.comment(
        " if using charachorder mode will parse chords.json file to get chords")
    builder.comment(
        " or parse them from your charachorder if none is detected")
    builder.comment(
        ' if in "fuzzy chips" mode will parse chips.toml which should be your entire fuzzy chips config')
    builder.comment(
        ' this setting can be ignored by using -f to force fuzzy chips mode or -c to force charachorder mode')
    builder.add_field("mode", chord_mode)
    builder.new_line()

    builder.add_section("notification")
    builder.comment(
        " there are three values for notification mode: qt, notify, auto")
    builder.comment(
        " notify uses the notify-send command to send a notification and only works on linux, it")
    builder.comment(
        " qt creates notifications using qt windows, requires pyside6 to be installed")
    builder.comment(
        " auto selects the notification mode automatically, notify on linux, qt on other platforms")
    builder.add_field("mode", notification_mode)
    builder.add_str("title", "possible missed chord")
    builder.add_str("message", "$triggers = $chord")
    builder.comment(
        " duration can be specified as a integer in milliseconds or a string")
    builder.comment(
        " if you use a string you can append a s to use seconds instead")
    builder.comment(
        " if in seconds then it will be converted to the closes integer milliseconds by the program using bankers rounding")
    builder.comment(
        ' ex: duration = "3s", duration = 3000, duration = "3.0s", duration = "3000ms" are all equal')
    builder.add_field("duration", duration)
    builder.new_line()
    builder.add_section("filter")
    builder.comment(" the filter has two options blocked and allowed")
    builder.comment(" they filter the output chord/chip")
    builder.comment(" they're both list of strings")
    builder.comment(" the blocked list blocks any chords in it")
    builder.comment(
        " the allowed list allows only strings that are in it to be displayed")
    builder.comment(
        " if the allowed list is empty then any string that is not in the blocked list is allowed")
    builder.comment(
        " if something is in both in the blocked and allowed list then it will be blocked")
    builder.comment(' ex: blocked = ["I","have"]')
    builder.add_list("blocked", [], GenStr)
    builder.add_list("allowed", [], GenStr)

    builder.new_line()

    builder.comment(
        " settings that only apply to notifications created in qt mode")
    builder.add_section("qt")

    builder.add_int("duration_height", 8,
                    " height of duration bar set to 0 to hide, default = 8")

    builder.comment(
        " max_notifications is the max number of qt windows that will displayed if there are more notifications the older ones will be close. If <= 0 then unlimited")
    builder.add_int("max_notifications", 3)
    builder.add_int("notification_width", 400, " defaults to 400")
    builder.add_int("notification_height", 100, " defaults to 100")

    builder.new_line()
    builder.add_section("logging")
    builder.comment(
        " log missed chords to stdout (sorted by frequency), default = false")
    builder.add_bool("log_to_stdout", False)
    builder.comment(
        ' log to a file will create file/parent dirs if needed, default = ""')
    builder.add_str("log_to_path", "")

    builder.new_line()
    builder.comment(
        " these features are experimental and do not work the best in all environments")
    builder.add_section("experimental")
    builder.comment(
        " adds a duration bar to the notifications, when using notify-send, on linux")
    builder.comment(
        " uses the same rules for setting it as the notification.duration field")
    builder.comment(
        " 0 = disabled, if you set the value to low like 1, then it will feel laggy, if you set it to high it will feel laggy.")
    builder.comment(
        " I would recommend somewhere in the 20-50 ms range for most people if they use this setting")
    builder.comment("")
    builder.comment(
        " WARNING: only really works well with dunst, and even then feels buggy")
    builder.comment(
        " in swaync it works but the notification's orders change constantly")
    builder.add_field("notification_bar_update_frequency", update_frequency)

    builder.new_line()

    builder.comment(
        " if the internal buffer ends with one of the keys as a word it will execute the command.")
    builder.comment(
        " most users can ignore the clear buffer command but may want to set up a reload config command")
    builder.comment(
        ' in this case if you type "<space>RL<space>" it will reload the config in most situations')
    builder.add_custom_section("commands", "parse_command_section($map)")
    builder.add_field("RL", GenList([GenStr("reload_config")]))
    builder.add_field("CB", GenList([GenStr("clear_buffer")]))

    return builder


def example_config_path() -> str:
    return str(_root_dir()/"example_configs"/"config.toml")


def python_path() -> str:
    return str(_root_dir()/"config.py")


def make_python(builder: Builder) -> str:
    return build_python(builder)


def make_toml(builder: Builder) -> str:
    return build_toml(builder)


def _root_dir():
    return Path(__file__).resolve().parent.parent
