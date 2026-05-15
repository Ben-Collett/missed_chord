# TODO: add some type safety inforcment
def parse_command_section(config: dict) -> dict[str, list[str]]:
    commands = config.get("commands")
    default_value = {"RL": ["reload_config"], "CB": ["clear_buffer"]}
    return commands or default_value
