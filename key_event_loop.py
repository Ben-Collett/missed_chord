import chara_loop
import chip_loop
from config import current_config
from chording_modes import ChordingModes
from my_key_event import TERMINATE_EVENT


def key_loop(key_queue):

    should_restart = True
    current_mode = current_config.mode

    def on_config_update():
        nonlocal should_restart, current_mode

        if current_mode != current_config.mode:
            should_restart = True
            current_mode = current_config.mode
            key_queue.put(TERMINATE_EVENT)

    current_config.on_reload.append(on_config_update)
    while should_restart:
        should_restart = False
        if current_mode == ChordingModes.CHARA_CHORDER:
            chara_loop.chara_key_loop(key_queue)
        elif current_mode == ChordingModes.FUZZY_CHIPS:
            chip_loop.chip_key_loop(key_queue)
