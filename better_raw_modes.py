import hexchat

try:
    from .util import no_recursion
except SystemError:
    # Add addons path to sys.path for win32
    # See https://github.com/hexchat/hexchat/issues/1396
    import os
    import sys

    if sys.platform == "win32":
        addons_path = os.path.join(hexchat.get_info("configdir"), "addons")
        if addons_path not in sys.path:
            sys.path.append(addons_path)

    from util import no_recursion


###############################################################################

__module_name__ = "Better Raw Modes"
__module_author__ = "FichteFoll"
__module_version__ = "0.1.0"
__module_description__ = "Enhances display of the 'Raw Modes' text event"


@no_recursion
def raw_modes_cb(word, word_eol, event):
    """Transforms mode messages to remove redundant information.

    Self-modes get ":" prepended.

    ['FichteFoll', '#channel +o FichteFoll'] => ['FichteFoll', '+o FichteFoll']
    ['FichteFoll', 'FichteFoll :+Tix'] => ['FichteFoll', ':+Tix']
    ['FichteFoll', 'FichteFoll +Tix'] => ['FichteFoll', ':+Tix']
    """
    mode_args = word[1].split()
    if mode_args[0] == hexchat.get_info('channel'):
        del mode_args[0]
    elif mode_args[0] == hexchat.get_info('nick'):
        mode_args[1] = ":" + mode_args[1].lstrip(":")
        del mode_args[0]
    else:
        return hexchat.EAT_NONE

    hexchat.emit_print(event, word[0], " ".join(mode_args))
    return hexchat.EAT_HEXCHAT


def main():
    hexchat.hook_print('Raw Modes', raw_modes_cb, 'Raw Modes')
    hexchat.get_info("")

    print(__module_name__, __module_version__, "loaded")

if __name__ == '__main__':
    main()