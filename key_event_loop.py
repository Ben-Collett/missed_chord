import chara_loop
import chip_loop
from chording_modes import ChordingMode
from config_wrapper import ConfigWrapper
from my_key_event import TERMINATE_EVENT


def key_loop(key_queue, config_wrapper: ConfigWrapper):

    should_restart = True
    current_mode = config_wrapper.config.general.mode

    def on_config_update():
        nonlocal should_restart, current_mode

        new_mode = config_wrapper.config.general.mode
        if current_mode != new_mode:
            should_restart = True
            current_mode = new_mode
            key_queue.put(TERMINATE_EVENT)

    config_wrapper.on_reload.append(on_config_update)
    while should_restart:
        should_restart = False
        if current_mode == ChordingMode.CHARA_CHORDER:
            chara_loop.chara_key_loop(key_queue, config_wrapper)
        elif current_mode == ChordingMode.FUZZY_CHIPS:
            chip_loop.chip_key_loop(key_queue, config_wrapper)
