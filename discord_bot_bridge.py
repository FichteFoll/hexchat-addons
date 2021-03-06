__module_name__ = "Discord Bot Bridge"
__module_author__ = "FichteFoll"
__module_version__ = "0.3.5"
__module_description__ = "Translates messages bridged from Discord into the native IRC protocol"

import re

import hexchat

# associates channels where this functionality is active with the nickname of the bot
# using a case-insensitive regular expression
BOT_MAP = {
    "#nanaone": r"_dc_\d*",
    "#pa-subs": r"Benji\d*",
}

MODE_CHAR = "⇔"
REVERSE_COLOR = "\026"
ITALICS = "\035"


def iter_fill(iterable, n, fillvalue=None):
    """Iterate over iterable and append fillvalue until n values have been yielded."""
    for x in iterable:
        yield x
        n -= 1
    yield from (fillvalue,) * n
    # for _ in range(n):
    #     yield fillvalue


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
    bot_regex = BOT_MAP.get(channel)
    if not bot_regex or not re.search(bot_regex, hexchat.strip(nick), re.IGNORECASE):
        return hexchat.EAT_NONE

    match = re.match(r"^<([^>]+)> (.*)", text)
    if not match:
        return hexchat.EAT_NONE
    original_nick, message = match.groups()
    spaceless_nick = original_nick.replace(" ", "_")  # IRC doesn't like spaces in nicks at all

    gui_color = 2
    if spaceless_nick == hexchat.get_info('nick'):
        event_name = 'Your Message'
        gui_color = 0
    else:
        if not is_user_in_channel(spaceless_nick):
            # TODO test if emit_print also works
            # TODO cannot specify timestamp of msg event
            hexchat.command("RECV :{nick}!someone@discord.server JOIN {channel}"
                            .format(nick=spaceless_nick, channel=channel))
        if "Hilight" in event_name:
            gui_color = 3

    # Manually mark channel as having activity (or highlight)
    # because we consume the original event.
    if gui_color:
        hexchat.command("GUI color {}".format(gui_color))

    # try to decect actions
    if message.startswith(REVERSE_COLOR) and message.endswith(REVERSE_COLOR):
        message = message.strip(REVERSE_COLOR)
        event_name = event_name.replace("Message", "Action").replace("Msg", "Action")

    # replace with proper escape code
    message = message.replace(REVERSE_COLOR, ITALICS)

    hexchat.emit_print(event_name, spaceless_nick, message, MODE_CHAR, identified_text,
                       time=attrs.time)

    return hexchat.EAT_ALL


# Without the @no_recursion utility,
# this is beeing called twice,
# but shouldn't loop regardless.
# I just chose to not add a dependency for some performance loss.
def my_msg_cb(word, word_eol, _):
    """Add "@" before nicks sourced from discord."""
    channel = hexchat.get_info('channel')
    if channel not in BOT_MAP:
        return hexchat.EAT_NONE

    discord_nicks = {user.nick for user in hexchat.get_list('users')
                     if user.host == "someone@discord.server"}
    if not discord_nicks:
        return hexchat.EAT_NONE

    nick_regex = r"\b(?<!@)({})\b".format("|".join(map(re.escape, discord_nicks)))
    original_text = word_eol[0]

    text = re.sub(nick_regex, r"@\1", original_text)
    if text == original_text:
        return hexchat.EAT_NONE
    else:
        hexchat.command("SAY {}".format(text))
        return hexchat.EAT_ALL


if __name__ == '__main__':
    for event in ('Channel Message', 'Channel Msg Hilight',
                  'Channel Action', 'Channel Action Hilight'):
        hexchat.hook_print_attrs(event, msg_cb, event, hexchat.PRI_HIGHEST)

    hexchat.hook_command('', my_msg_cb)

    print(__module_name__, __module_version__, "loaded")
