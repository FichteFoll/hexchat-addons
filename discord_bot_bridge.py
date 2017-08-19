__module_name__ = "Discord Bot Bridge"
__module_author__ = "FichteFoll"
__module_version__ = "0.1.1"
__module_description__ = "Translates messages bridged from Discord into the native IRC protocol"

import re

import hexchat

# associates channels where this functionality is active with the nickname of the bot
BOT_MAP = {
    "#nanaone": "_dc_"
}

MODE_CHAR = "⇔"
REVERSE_COLOR = "\026"
ITALICS = "\035"


def msg_cb(word, word_eol, event_name, attrs):
    nick, text, _, *other_word = word
    channel = hexchat.get_info('channel')

    if channel not in BOT_MAP:
        return hexchat.EAT_NONE
    elif hexchat.nickcmp(nick, BOT_MAP[channel]):
        return hexchat.EAT_NONE

    match = re.match(r"^<([^>]+)> (.*)", text)
    if not match:
        return hexchat.EAT_NONE
    original_nick, message = match.groups()

    if original_nick == hexchat.get_info('nick'):
        event_name = 'Your Message'
    else:
        userlist = hexchat.get_list('users')
        if original_nick not in userlist:
            # TODO test if emit_print also works
            spaceless_nick = original_nick.replace(" ", "_")
            hexchat.command("RECV {nick}!someone\@discord.server JOIN {channel}"
                            .format(nick=spaceless_nick, channel=channel))

    # try to decect actions
    if message.startswith(REVERSE_COLOR) and message.endswith(REVERSE_COLOR):
        message = message.strip(REVERSE_COLOR)
        event_name = event_name.replace("Message", "Action").replace("Msg", "Action")

    # replace with proper escape code
    message = message.replace(REVERSE_COLOR, ITALICS)

    hexchat.emit_print(event_name, original_nick, message, MODE_CHAR, *other_word, time=attrs.time)

    return hexchat.EAT_ALL


if __name__ == '__main__':
    for event in ('Channel Action', 'Channel Msg Hilight'):
        hexchat.hook_print_attrs(event, msg_cb, event, hexchat.PRI_HIGHEST)

    print(__module_name__, __module_version__, "loaded")
