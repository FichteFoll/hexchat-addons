"""Python 3 plugin for Hexchat that prints or announces titles of YouTube URLs.
"""

import builtins
import re
import os
import sys

import hexchat

import requests

# Make imports work (see https://github.com/hexchat/hexchat/issues/1396)
addons_path = os.path.join(hexchat.get_info("configdir"), "addons")
if addons_path not in sys.path:
    sys.path.append(addons_path)

from pluginpref import PluginPref, JSONPluginPref  # noqa: E402
from util import set_timeout  # noqa: E402


###############################################################################


__module_name__        = "YouTube Title"
__module_version__     = "0.3.3"
__module_description__ = "Scans text for YouTube video urls and displays or announces the titles"
__module_author__      = "FichteFoll <fichtefoll2@googlemail.com>"

versioninfo = tuple(map(int, __module_version__.split(".")))


# TODO improve this
HELP_STR = """\
Usage:
/YTT \002GET\002 <url> {<url>} - Get titles of passed url(s)
/YTT \002ANNOUNCE\002 [ LIST | [ADD | REMOVE] <channel> {<channel>} ] - Manage list of channels where video titles should be announced
/YTT \002MUTE\002 [ LIST | [ADD | REMOVE] <channel> {<channel>} ] - Manage list of channels where video urls should be ignored
/YTT \002KEY\002 [GET | SET <key>] - Get/Set the YouTube API key
By default, YouTube Title will only print the video's title for you."""

HELP_MAP = dict(zip(('get', 'announce', 'mute', 'key'),
                    HELP_STR.splitlines()[1:-1]))

PRINT_PREFIX = "*ytt*"

# global
prefs = None


###############################################################################
# General Ultilities

def print(*args, context=None, **kwargs):
    """Use rocket science to prepend 'PRINT_PREFIX\t' to each line for `print`.
    """
    prefix = PRINT_PREFIX + "\t"
    if args:
        args = list(args)
        for i, arg in enumerate(args):
            if isinstance(arg, str):
                args[i] = arg.replace("\n", "\n" + prefix)
        args[0] = prefix + str(args[0])
    if context:
        context.prnt(" ".join(args))
    else:
        builtins.print(*args, **kwargs)


###############################################################################
# Other Functions

def yt_api(path, **params):
    params.setdefault('key', prefs.get('key'))
    if not params['key']:
        raise TypeError("You must set an API key using `/ytt key set <key>`")
    return requests.get("https://www.googleapis.com/youtube/v3/" + path,
                        params=params)


def get_yt_titles(vids):
    # https://developers.google.com/youtube/v3/docs/videos/list
    req = yt_api('videos',
                 id=','.join(vids),
                 part="snippet",
                 fields="items(id,snippet(title))")
    req.raise_for_status()
    data = req.json()

    if 'error' in data:
        print("Errors trying to fetch video information")
        for error in data['error']['errors']:
            print("  " + error['message'])
        return []

    mapping = {video['id']: video['snippet']['title']
               for video in data['items']}

    return [mapping.get(vid, "Video for %s not found" % vid)
            for vid in vids]


# These regular expressions have been simplified
# TODO: more accurate regex?
normal = re.compile(r"(?:&|\?|/)v(?:=|/)([\w\-]{11})")
short = re.compile(r"(?:(?:https?\://)?(?:\w+\.)?(?:youtube|youtu)(?:\.\w+){1,2}/)([\w\-]{11})")


def find_ids(text):
    """Find all (unique) video ids in a given text, sorted by start pos."""
    ids = set()

    for reg in (normal, short):
        for m in reg.finditer(text):
            ids.add((m.start(1), m.group(1)))

    return [vid for (pos, vid) in sorted(ids, key=lambda x: x[0])]


def say_yt_title(title):
    message = "\002Title:\002 " + title

    # Delay our "say" because otherwise it will occur before we have actually
    # sent the video url.
    context = hexchat.get_context()
    set_timeout(lambda: context.command("say {message}".format(message=message)))


def print_yt_title(title):
    message = "\002Title:\002 " + title
    # Same as in say_yt_title, except the print would otherwise be printed before
    # the received message.
    context = hexchat.get_context()
    set_timeout(lambda: print(message, context=context))


def process_vids(vids, title_handler):
    try:
        titles = get_yt_titles(vids)
    except (requests.exceptions.HTTPError, TypeError) as e:
        print("Could not retrieve video title(s):\n%s" % e)
    else:
        for title in titles:
            title_handler(title)


def manage_list_setting(name, action, items=[]):
    list_ = prefs.get(name, [])

    if action == 'list':
        list_str = " ".join(list_)
        print("{name} list: {list_str}".format(**locals()))
    elif items and action == 'add':
        for item in items:
            if item not in list_:
                list_.append(item)
                print("Added {item} to {name} list".format(**locals()))
            else:
                print("{item} already in {name} list".format(**locals()))
    elif items and action == 'remove':
        for item in items:
            if item in list_:
                list_.remove(item)
                print("Removed {item} from {name} list".format(**locals()))
            else:
                print("{item} not in {name} list".format(**locals()))
    else:
        print(HELP_MAP[name])

    prefs[name] = list_


###############################################################################
# Entry Points

def msg_cb(word, word_eol, userdata):
    channel = hexchat.get_info('channel').lower()

    if channel in prefs.get('mute', tuple()):
        return
    elif channel in prefs.get('announce', tuple()):
        callback = say_yt_title
    else:
        callback = print_yt_title

    vids = find_ids(word[1])
    if vids:
        process_vids(vids, callback)


def privmsg_cb(word, word_eol, userdata):
    vids = find_ids(word[1])
    if vids:
        process_vids(vids, print_yt_title)


def yttcmd_cb(word, word_eol, userdata):
    # print help if no sub-command
    if not len(word) > 1:
        print(HELP_STR)
        return hexchat.EAT_HEXCHAT

    sub_cmd, *args = word[1:]

    if sub_cmd == '_prefs':  # debug
        print(list(prefs.items()))
        print("prefs version:", prefs.version)
        return hexchat.EAT_HEXCHAT

    # print help for sub-commands or everything
    if not args:
        print(HELP_MAP.get(sub_cmd, HELP_STR))
        return hexchat.EAT_HEXCHAT

    # actual sub-commands
    if sub_cmd == 'get':
        vids = find_ids(word_eol[2])
        if not vids:
            print("Could not find any video id in input")
        else:
            process_vids(vids, print_yt_title)
    elif sub_cmd == 'key':
        if args[0].lower() == 'get':
            print(prefs.get('key', "No key set"))
        elif args[0].lower() == 'set' and len(args) == 2:
            prefs['key'] = args[1]
            print("Key set")
        else:
            print(HELP_MAP[sub_cmd])
    elif sub_cmd in ('announce', 'mute'):
        action, *channels = args
        # lowercase the channels before passing to list handler
        channels = map(str.lower, channels)
        manage_list_setting(sub_cmd, action, channels)
    else:
        print(HELP_STR)

    return hexchat.EAT_HEXCHAT


###############################################################################
# Script entry point

def main():
    ###########################################################################
    # Manage Preferences
    global prefs

    prefs = JSONPluginPref(__module_name__)

    if prefs.version is NotImplemented:
        print("There was an error retrieving the preferences' version.\n"
              "It is advised to seek help from the author (FichteFoll) "
              "and run around in circles.")
        return

    if prefs.version is None:  # before 0.3.0
        # convert preferences to JSON storage
        bare_prefs = PluginPref(__module_name__, prefix_sep="_")
        for key, value in bare_prefs.items():
            if key in ('announce', 'mute'):
                value = list(filter(None, value.split(",")))
            prefs[key] = value
            del bare_prefs[key]

        prefs.version = (0, 3, 0)  # hardcode for further migrations
        print("Converted preference storage to 0.3.0")

    # if prefs.version < (0, 3, 4):
    #     pass

    # Write current version at last
    prefs.version = versioninfo

    ###########################################################################
    # Register Hooks

    hexchat.hook_command("YTT", yttcmd_cb, help=HELP_STR)

    private_msg_events = ("Notice", "Private Message", "Private Action")
    for event in private_msg_events:
        hexchat.hook_print(event, privmsg_cb)

    public_msg_events = ("Channel Message", "Action", "Your Message", "Your Action")
    for event in public_msg_events:
        hexchat.hook_print(event, msg_cb)

    print(__module_name__, __module_version__, "loaded")


if __name__ == '__main__':
    main()
