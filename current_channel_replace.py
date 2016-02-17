import hexchat


__module_name__ = 'Current Channel Replace'
__module_version__ = '1.0.0'
__module_description__ = ('Replaces "#" with current channel on tab and space keys, '
                          'unless shift is hold.')

KEY_TAB = 65289
KEY_SPACE = 32

KEY_MOD_SHIFT = 1 << 0
KEY_MOD_CTRL = 1 << 2
KEY_MOD_ALT = 1 << 3


def on_key_press(word, word_eol, userdata):
    msg = hexchat.get_info('inputbox')
    pos = hexchat.get_prefs('state_cursor')
    # If this fails for you, it's because of
    # https://github.com/hexchat/hexchat/issues/869
    key = int(word[0])
    modifier = int(word[1])

    if not msg:
        return

    if (
        pos
        and key in (KEY_TAB, KEY_SPACE)
        and not (modifier & KEY_MOD_SHIFT)
        and msg[pos - 1] == "#"
    ):
        channel = hexchat.get_info('channel')
        msg = msg[:pos - 1] + channel + msg[pos:]
        hexchat.command("settext %s" % msg)
        hexchat.command("setcursor %d" % (pos + len(channel) - 1))

if __name__ == '__main__':
    hexchat.hook_print('Key Press', on_key_press)

    print("%s %s loaded" % (__module_name__, __module_version__))
