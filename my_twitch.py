import hexchat

try:
    from .util import only_on
except SystemError:
    # Add addons path to sys.path for win32
    # See https://github.com/hexchat/hexchat/issues/1396
    import os
    import sys

    if sys.platform == "win32":
        addons_path = os.path.join(hexchat.get_info("configdir"), "addons")
        if addons_path not in sys.path:
            sys.path.append(addons_path)

    from util import only_on


###############################################################################

__module_name__ = "My Twitch Enhancements"
__module_author__ = "FichteFoll"
__module_version__ = "0.3.0"
__module_description__ = "Enhancements for Twitch.tv"

# TODO make configurable
USER_THRESHOLD = 15


# pre-build decorator
twitch_only = only_on(servers=["twitch.tv"])


@twitch_only
def joinpart_cb(word, word_eol, event):
    """Block Join/Part events for channels with more than X users."""
    curr_chan = hexchat.get_info('channel')
    channel_list = None
    for item in hexchat.get_list('channels'):
        if item.channel == curr_chan:
            channel_list = item
            break
    else:
        print("can't find channel")
        return hexchat.EAT_NONE

    if channel_list.users > USER_THRESHOLD:
        return hexchat.EAT_ALL
    else:
        return hexchat.EAT_NONE


@twitch_only
def eat_all_cb(word, word_eol, event):
    return hexchat.EAT_ALL


@twitch_only
def raw_modes_cb(word, word_eol, userdata):
    """Block unnecessarily spammy mode changes."""
    # ['FichteFoll', '#channel +o FichteFoll']
    if word[1].split()[1] in ("+o", "-o"):
        # Just block all mode events like this
        # because twitch's IRC is fucking broken
        # and sends mode changes for no reason
        # every few minutes occasionally.
        # Net splits potentially.
        return hexchat.EAT_ALL
        # nicks = [u.nick for u in hexchat.get_list('users')]
        # if not word[4] in nicks:
        #     return hexchat.EAT_ALL

    return hexchat.EAT_NONE


def main():
    for evt in ('Join', 'Part'):  # 'Part with Reason', likely not used
        hexchat.hook_print(evt, joinpart_cb, evt)

    # Hook modes
    hexchat.hook_print('Raw Modes', raw_modes_cb, hexchat.PRI_HIGH)
    for evt in ('Channel Operator', 'Channel DeOp'):
        hexchat.hook_print(evt, eat_all_cb, evt)

    print(__module_name__, __module_version__, "loaded")

if __name__ == '__main__':
    main()
