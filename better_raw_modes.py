"""Remove redundant target information if it's obvious from context.

FichteFoll sets mode #channel +o FichteFoll => FichteFoll sets mode +o FichteFoll
FichteFoll sets mode FichteFoll +ix => FichteFoll sets mode +ix

Requires the irc_raw_modes setting to be enabled
(`/set irc_raw_modes 1`).
"""
import os
import sys

import hexchat

# Make imports work (see https://github.com/hexchat/hexchat/issues/1396)
addons_path = os.path.join(hexchat.get_info("configdir"), "addons")
if addons_path not in sys.path:
    sys.path.append(addons_path)

from util import print_event  # noqa: E402


###############################################################################

__module_name__ = "Better Raw Modes"
__module_author__ = "FichteFoll"
__module_version__ = "0.3.1"
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
    """Eat the target part of the message, if it's obvious from context."""
    target, *mode_args = split_irc_message(word[1])
    if target not in (hexchat.get_info('channel'), hexchat.get_info('nick')):
        return hexchat.EAT_NONE

    print_event('Raw Modes', word[0], " ".join(mode_args))
    return hexchat.EAT_HEXCHAT


def main():
    hexchat.hook_print('Raw Modes', raw_modes_cb, priority=hexchat.PRI_LOWEST)

    print(__module_name__, __module_version__, "loaded")


if __name__ == '__main__':
    main()
