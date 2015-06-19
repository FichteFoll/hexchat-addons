import re

import requests

import hexchat


__module_name__        = "Youtube Title Display"
__module_version__     = "0.1"
__module_description__ = "Reads and displays video info from an URL."
__module_author__      = "FichteFoll <fichtefoll2@googlemail.com>"


API_KEY = ""


################################################################################


def delayed_command(context, timeout, cmd):
    handler = None

    def callback(userdata):
        nonlocal handler, context, cmd
        hexchat.unhook(handler)
        context.command(cmd)

    handler = hexchat.hook_timer(timeout, callback)


def yt_api(path, **params):
    params.setdefault("key", API_KEY)
    return requests.get("https://www.googleapis.com/youtube/v3/" + path,
                        params=params)


def get_yt_titles(vids):
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
    # TODO channel restictions, say vs print
    # channel = hexchat.get_info('channel')

    # Delay our "say" because otherwise it will occur before we actuallysent the video
    # url.
    context = hexchat.get_context()
    delayed_command(context, 50, "say {message}".format(**locals()))


def print_yt_title(title):
    message = "*YT*\t\002Title:\002 " + title
    print(message)


def process_vids(vids, title_handler):
    titles = get_yt_titles(vids)
    for title in titles:
        title_handler(title)

################################################################################


def msg_cb(word, word_eol, userdata):
    vids = find_ids(word[1])
    if vids:
        process_vids(vids, say_yt_title)


def privmsg_cb(word, word_eol, userdata):
    vids = find_ids(word[1])
    if vids:
        process_vids(vids, print_yt_title)


def ytcmd_cb(word, word_eol, userdata):
    if len(word) < 2:
        print("/yt <url> {<url>} to get video info(s)")
    else:
        vids = find_ids(word_eol[1])
        if not vids:
            print("Could not find any video id in input")
        else:
            process_vids(vids, print_yt_title)

    return hexchat.EAT_HEXCHAT


################################################################################


# Hooking
hexchat.hook_command("yt", ytcmd_cb, help="/yt <url> {<url>} to get video info(s)")

private_msg_events = ("Notice", "Private Message", "Private Action")
for event in private_msg_events:
    hexchat.hook_print(event, privmsg_cb)

public_msg_events = ("Channel Message", "Action", "Your Message", "Your Action")
for event in public_msg_events:
    hexchat.hook_print(event, msg_cb)


print(__module_name__, __module_version__, "loaded")
