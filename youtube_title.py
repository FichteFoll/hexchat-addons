import re

import requests

import hexchat

try:
    from .plugin_pref import PluginPref
except SystemError:
    # Add addons path to sys.path for win32
    # See https://github.com/hexchat/hexchat/issues/1396
    import os
    import sys

    if sys.platform == "win32":
        addons_path = os.path.join(hexchat.get_info("configdir"), "addons")
        if addons_path not in sys.path:
            sys.path.append(addons_path)

    from plugin_pref import PluginPref


################################################################################


__module_name__        = "YouTube Title"
__module_version__     = "0.2.2"
__module_description__ = "Scans text for YouTube video urls and displays or announces the titles"
__module_author__      = "FichteFoll <fichtefoll2@googlemail.com>"


API_KEY = ""

HELP_STR = """\
Usage:
/ytt \002get\002 <url> {<url>} - Get titles of passed url(s)
/ytt \002announce\002 [add | remove | list] <channel> - Manage list of channels where video titles should be announced
/ytt \002mute\002 [add | remove | list] <channel> - Manage list of channels where video urls should be ignored
By default, YouTube Title will only print the video's title for you.
"""

HELP_MAP = dict(zip(("get", "announce", "mute"), HELP_STR.splitlines()[1:-1]))

PRINT_PREFIX = "*ytt*"


################################################################################


def print(*args, **kwargs):
    """Use rocket science to prepend 'PRINT_PREFIX\t' to each line for `print`.
    """
    if args:
        args = list(args)
        for i, arg in enumerate(args):
            if isinstance(args[0], str) and "\n" in args[0]:
                args[i] = ("\n" + PRINT_PREFIX + "\t").join(arg.splitlines())
        args[0] = PRINT_PREFIX + "\t" + str(args[0])
    __builtins__.print(*args, **kwargs)


def delayed_command(context, timeout, cmd):
    handler = None

    def callback(userdata):
        nonlocal handler, context, cmd
        hexchat.unhook(handler)
        context.command(cmd)

    handler = hexchat.hook_timer(timeout, callback)


################################################################################


def yt_api(path, **params):
    params.setdefault("key", API_KEY)
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

    return [mapping[vid] if vid in mapping else "Video not found"
            for vid in vids]


# These regular expressions have been simplified
# TODO: more accurate regex?
normal = re.compile(r"(?:&|\?|/)v(?:=|/)([\w\-]{11})")
short = re.compile(r"(?:(?:https?\://)?(?:\w+\.)?(?:youtube|youtu)(?:\.\w+){1,2}/)([\w\-]{11})")


def find_ids(text):
    """Finds all (unique) video ids in a given text, sorted by start pos."""
    ids = set()

    for reg in (normal, short):
        for m in reg.finditer(text):
            ids.add((m.start(1), m.group(1)))

    return [vid for pos, vid in sorted(ids, key=lambda x: x[0])]


def say_yt_title(title):
    message = "\002Title:\002 " + title

    # Delay our "say" because otherwise it will occur before we actuallysent the video
    # url.
    context = hexchat.get_context()
    delayed_command(context, 50, "say {message}".format(**locals()))


def print_yt_title(title):
    message = "\002Title:\002 " + title
    print(message)


def process_vids(vids, title_handler):
    titles = get_yt_titles(vids)
    for title in titles:
        title_handler(title)


def manage_list_setting(name, action, items=[]):
    list_ = prefs.get(name, "").split(",")

    if action == "list":
        list_str = " ".join(list_)
        print("{name} list: {list_str}".format(**locals()))
    elif items and action == "add":
        for item in items:
            if item not in list_:
                list_.append(item)
                print("Added {item} to {name} list".format(**locals()))
            else:
                print("{item} already in {name} list".format(**locals()))
    elif items and action == "remove":
        for item in items:
            if item in list_:
                list_.remove(item)
                print("Removed {item} from {name} list".format(**locals()))
            else:
                print("{item} not in {name} list".format(**locals()))
    else:
        print(HELP_MAP[name])

    prefs[name] = ",".join(list_)

################################################################################


def msg_cb(word, word_eol, userdata):
    channel = hexchat.get_info('channel')
    callback = print_yt_title

    if channel in prefs.get('mute', "").split(","):
        return
    if channel in prefs.get('announce', "").split(","):
        callback = say_yt_title

    vids = find_ids(word[1])
    if vids:
        process_vids(vids, callback)


def privmsg_cb(word, word_eol, userdata):
    vids = find_ids(word[1])
    if vids:
        process_vids(vids, print_yt_title)


def yttcmd_cb(word, word_eol, userdata):
    # Standardize args
    args = tuple(map(str.lower, word[1:]))

    if not args:
        print(HELP_STR)
        return hexchat.EAT_HEXCHAT

    if args[0] == "get":
        if len(args) == 1:
            print(HELP_MAP[args[0]])
            return hexchat.EAT_HEXCHAT

        vids = find_ids(word_eol[2])
        if not vids:
            print("Could not find any video id in input")
        else:
            process_vids(vids, print_yt_title)
    elif args[0] in ("announce", "mute"):
        if len(args) < 2:
            print(HELP_MAP[args[0]])
            return hexchat.EAT_HEXCHAT
        manage_list_setting(args[0], args[1], args[2:])
    else:
        print(HELP_STR)

    return hexchat.EAT_HEXCHAT


pref_prefix = __module_name__.replace(" ", "_").lower()
prefs = PluginPref(pref_prefix)


################################################################################


# Hooking
hexchat.hook_command("ytt", yttcmd_cb, help=HELP_STR)

private_msg_events = ("Notice", "Private Message", "Private Action")
for event in private_msg_events:
    hexchat.hook_print(event, privmsg_cb)

public_msg_events = ("Channel Message", "Action", "Your Message", "Your Action")
for event in public_msg_events:
    hexchat.hook_print(event, msg_cb)


print(__module_name__, __module_version__, "loaded")
