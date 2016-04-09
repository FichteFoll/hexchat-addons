"""Personal Twitch enhancements.

Mutes +o and -o mode messages,
because the server spams these regularly
for no apparent reason (probably netsplits).

Also mutes join and part events for channels
with more users than a specified threshold.

Requires `/CAP req :twitch.tv/membership`
to be sent on the network
(suggested to add to "Connect Commands").
"""
import hexchat

try:
    from .util import only_on, set_timeout
except SystemError:
    # Add addons path to sys.path for win32
    # See https://github.com/hexchat/hexchat/issues/1396
    import os
    import sys

    if sys.platform == "win32":
        addons_path = os.path.join(hexchat.get_info("configdir"), "addons")
        if addons_path not in sys.path:
            sys.path.append(addons_path)

    from util import only_on, set_timeout


###############################################################################

__module_name__ = "My Twitch Enhancements"
__module_author__ = "FichteFoll"
__module_version__ = "0.4.2"
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
    # ['FichteFoll', '+o FichteFoll']  # my raw modes modifications
    if word[1].split()[-2] in ('+o', '-o'):
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


def caps_cb(word, word_eol, userdata):
    # Hexchat 2.12.0 automatically requests the membership CAP
    hc_version = tuple(int(x) for x in hexchat.get_info('version').split("."))
    if hc_version > (2, 12):
        return hexchat.EAT_NONE

    desired_caps = {'twitch.tv/membership'}  # , 'twitch.tv/commands'}
    available_caps = set(word[1].split())
    require_caps_str = " ".join(desired_caps & available_caps)
    if require_caps_str:
        hexchat.command("CAP REQ :%s" % require_caps_str)
        context = hexchat.get_context()
        set_timeout(lambda: context.emit_print('Capability Request', require_caps_str))
    return hexchat.EAT_NONE


def main():
    for evt in ('Join', 'Part'):  # 'Part with Reason' likely not necessary
        hexchat.hook_print(evt, joinpart_cb, evt, priority=hexchat.PRI_HIGH)

    # Hook modes
    hexchat.hook_print('Raw Modes', raw_modes_cb, priority=hexchat.PRI_HIGH)
    for evt in ('Channel Operator', 'Channel DeOp'):
        hexchat.hook_print(evt, eat_all_cb, evt, priority=hexchat.PRI_HIGH)

    hexchat.hook_print('Capability List', caps_cb)

    print(__module_name__, __module_version__, "loaded")

if __name__ == '__main__':
    main()
