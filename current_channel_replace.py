import hexchat


__module_name__ = 'Current Channel Replace'
__module_version__ = '0.2'
__module_description__ = 'Replaces "#" with current channel'

KEY_TAB = 65289
KEY_SPACE = 32

KEY_MOD_SHIFT = 1
KEY_MOD_CTRL = 4
KEY_MOD_ALT = 8


def debug(*args, **kwargs):
    if args:
        args = list(args)
        args[0] = "\00314" + str(args[0])
    print(*args, **kwargs)


def on_key_press(word, word_eol, userdata):
    """Performs substitution of "#" on tab and space keys, unless shift is hold.
    """
    msg = hexchat.get_info('inputbox')
    # https://github.com/hexchat/hexchat/issues/869
    key = int(word[0])
    modifier = int(word[1])

    if msg is None:
        return

    if (
        msg.endswith("#")
        and key in (KEY_TAB, KEY_SPACE)
        and not (modifier & KEY_MOD_SHIFT)
    ):
        msg = msg[:-1] + hexchat.get_info('channel')
        # debug("Replacing with", hexchat.get_info('channel'))
        hexchat.command("settext %s" % msg)
        hexchat.command("setcursor %s" % len(msg))


hexchat.hook_print('Key Press', on_key_press)

print("%s %s loaded" % (__module_name__, __module_version__))
