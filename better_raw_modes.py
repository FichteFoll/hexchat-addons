"""Transforms raw mode messages to remove redundant information.

FichteFoll sets mode #channel +o FichteFoll => FichteFoll sets mode +o FichteFoll
FichteFoll sets mode FichteFoll +i => FichteFoll sets mode :+i

Requires the irc_raw_modes setting to be enabled
(`/set irc_raw_modes 1`).
"""
import hexchat

try:
    from .util import print_event
except SystemError:
    # Add addons path to sys.path for win32
    # See https://github.com/hexchat/hexchat/issues/1396
    import os
    import sys

    if sys.platform == "win32":
        addons_path = os.path.join(hexchat.get_info("configdir"), "addons")
        if addons_path not in sys.path:
            sys.path.append(addons_path)

    from util import print_event


###############################################################################

__module_name__ = "Better Raw Modes"
__module_author__ = "FichteFoll"
__module_version__ = "0.3.0"
__module_description__ = "Improves display of the 'Raw Modes' text event"


def split_irc_message(message):
    if message.startswith(":"):
        return [message]
    first, _, last = message.partition(" :")
    args = list(filter(None, first.split(" ")))
    if last:
        args.append(last)
    return args


def raw_modes_cb(word, word_eol, event):
    """
    ['FichteFoll', '#channel +o FichteFoll'] => ['FichteFoll', '+o FichteFoll']
    ['FichteFoll', 'FichteFoll :+Tix'] => ['FichteFoll', ':+Tix']
    ['FichteFoll', 'FichteFoll +Tix'] => ['FichteFoll', ':+Tix']
    """
    target, *mode_args = split_irc_message(word[1])
    if target not in (hexchat.get_info('channel'), hexchat.get_info('nick')):
        return hexchat.EAT_NONE

    print_event('Raw Modes', word[0], " ".join(mode_args))
    return hexchat.EAT_ALL


def main():
    hexchat.hook_print('Raw Modes', raw_modes_cb, priority=hexchat.PRI_LOWEST)

    print(__module_name__, __module_version__, "loaded")

if __name__ == '__main__':
    main()
