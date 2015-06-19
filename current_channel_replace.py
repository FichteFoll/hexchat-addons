import hexchat


__module_name__ = 'Current Channel Replace'
__module_version__ = '0.1'
__module_description__ = 'Replaces "#" with current channel'

KEY_TAB = 65289
KEY_SPACE = 32


def debug(*args, **kwargs):
    if args:
        args = list(args)
        args[0] = "\00314" + str(args[0])
    print(*args, **kwargs)


def on_key_press(word, word_eol, userdata):
    """Perform substitution of # on tab key.
    """
    msg = hexchat.get_info('inputbox')
    key = int(word[0])
    if msg is None:
        return

    if msg.endswith("#") and key in (KEY_TAB, KEY_SPACE):
        msg = msg[:-1] + hexchat.get_info('channel')
        # debug("Replacing with", hexchat.get_info('channel'))
        hexchat.command("settext %s" % msg)
        hexchat.command("setcursor %s" % len(msg))


hexchat.hook_print('Key Press', on_key_press)

print("\00304%s successfully loaded." % __module_name__)
