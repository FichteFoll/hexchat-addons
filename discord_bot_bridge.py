__module_name__ = "Discord Bot Bridge"
__module_author__ = "FichteFoll"
__module_version__ = "0.2.0"
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


def iter_fill(iterable, n, fillvalue=None):
    """Iterate over iterable and append fillvalue until n values have been yielded."""
    for x in iterable:
        yield x
        n -= 1
    for _ in range(n):
        yield fillvalue


def is_user_in_channel(nick, context=hexchat):
    for user in context.get_list('users'):
        if hexchat.nickcmp(nick, user.nick) == 0:
            return True
    return False


def msg_cb(word, word_eol, event_name, attrs):
    # Trailing empty words are not included in the word list (here: mode_char, identified_text).
    # For our custom print event, we don't care about the mode_char
    # because we either override it mode char or don't do anything.
    colored_nick, text, _, identified_text = iter_fill(word, 4, "")
    nick = hexchat.strip(colored_nick)

    channel = hexchat.get_info('channel')
    # if channel in BOT_MAP:
    #     print("nick", repr(nick))
    #     print("nickcmp", nick, BOT_MAP[channel], hexchat.nickcmp(nick, BOT_MAP[channel]))
    #     print(".lower()==?", nick.lower() == BOT_MAP[channel].lower())

    if channel not in BOT_MAP:
        return hexchat.EAT_NONE
    elif hexchat.nickcmp(nick, BOT_MAP[channel]) != 0:
        return hexchat.EAT_NONE

    match = re.match(r"^<([^>]+)> (.*)", text)
    if not match:
        return hexchat.EAT_NONE
    original_nick, message = match.groups()

    if original_nick == hexchat.get_info('nick'):
        event_name = 'Your Message'
    else:
        if not is_user_in_channel(original_nick):
            # TODO test if emit_print also works
            spaceless_nick = original_nick.replace(" ", "_")
            print("making", spaceless_nick, "join")
            hexchat.command("RECV :{nick}!someone@discord.server JOIN {channel}"
                            .format(nick=spaceless_nick, channel=channel))

    # try to decect actions
    if message.startswith(REVERSE_COLOR) and message.endswith(REVERSE_COLOR):
        message = message.strip(REVERSE_COLOR)
        event_name = event_name.replace("Message", "Action").replace("Msg", "Action")

    # replace with proper escape code
    message = message.replace(REVERSE_COLOR, ITALICS)

    hexchat.emit_print(event_name, original_nick, message, MODE_CHAR, identified_text,
                       time=attrs.time)

    return hexchat.EAT_ALL


if __name__ == '__main__':
    for event in ('Channel Message', 'Channel Msg Hilight',
                  'Channel Action', 'Channel Action Hilight'):
        hexchat.hook_print_attrs(event, msg_cb, event, hexchat.PRI_HIGHEST)

    print(__module_name__, __module_version__, "loaded")
