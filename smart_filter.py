"""Mutes events from users that never talk.

- Muted events are: Joins, Parts, Renames and Mode Changes.
- If a recently joined user starts talking,
  his 'Join' event is late-emitted with the original timestamp.
- Handles renames.
- If a user that previously talked
  parts and joins again (or renames),
  the events are shown.
- Events for nicks in your notify list are always shown.
- Default threshold is 60 minutes.

Works with ZNC bouncers
and also works with *buffextras module
using [buffextras.py][].

[buffextras.py]: https://github.com/knitori/tools/blob/master/hexchat/buffextras.py
"""

import functools
import time
import hexchat

__module_name__ = 'SmartFilter'
__module_author__ = 'FichteFoll'
__module_version__ = '3.0.1'
__module_description__ = 'Intelligently hide parts, joins, user modes, and nick changes'

# TODO only hide +-qaohv in Raw Modes

LASTTALK_THRESHOLD = 1 * 60 * 60  # in seconds
CLEAN_INTERVAL = 5 * 60  # in seconds


def expand_server_channel(forward_context=False):
    def decorator(func, forward_context=False):
        @functools.wraps(func)
        def wrapper(*args, context=hexchat, **kwargs):
            kwargs.setdefault('server', context.get_info('server'))
            kwargs.setdefault('channel', context.get_info('channel'))
            if forward_context:
                kwargs['context'] = context
            return func(*args, **kwargs)
        return wrapper
    if callable(forward_context):
        return decorator(forward_context)
    else:
        return decorator


class TimestampMap(object):

    def __init__(self, val=()):
        super().__init__()
        self._d = dict(val)

    @expand_server_channel
    def add(self, nick, tmstmp, data=None, server=None, channel=None):
        self._d[(server, channel, nick)] = (tmstmp, data)

    def clean(self):
        ref_time = time.time()
        for key in list(self._d.keys()):
            if (ref_time - self._d[key][0]) > LASTTALK_THRESHOLD:
                del self._d[key]
        return True  # loopable

    @expand_server_channel
    def rename(self, old_nick, new_nick, server=None, channel=None):
        item = self.pop(old_nick, server=server, channel=channel)
        if item:
            self._d[(server, channel, new_nick)] = item

    @expand_server_channel
    def pop(self, nick, default=None, server=None, channel=None):
        item = self._d.pop((server, channel, nick), None)
        return item if item and (time.time() - item[0]) < LASTTALK_THRESHOLD else default

    @expand_server_channel
    def get(self, nick, default=None, server=None, channel=None):
        item = self._d.get((server, channel, nick), None)
        return item if item and (time.time() - item[0]) < LASTTALK_THRESHOLD else default

    def __str__(self):
        return "%s(%s)" % (self.__class__.__name__, self._d)


class JoinMap(TimestampMap):

    def __init__(self, val=()):
        super().__init__(val)
        self.is_emitting = False

    @expand_server_channel
    def rename(self, old_nick, new_nick, server=None, channel=None):
        item = self.get(old_nick, server=server, channel=channel)
        if item:
            item[1][0] = new_nick
        super().rename(old_nick, new_nick, server=server, channel=channel)

    @expand_server_channel(True)
    def pop_and_emit(self, nick, server=None, channel=None, context=hexchat):
        item = self.pop(nick, server=server, channel=channel)
        if item:
            tmstmp, data = item
            self.is_emitting = True
            context.emit_print('Join', *data, time=tmstmp)
            self.is_emitting = False

tmap = TimestampMap()
jmap = JoinMap()


def get_user(nick, list_, context=hexchat):
    for user in context.get_list(list_):
        if hexchat.nickcmp(user.nick, nick) == 0:
            return user


def check_notify(nick):
    return get_user(nick, 'notify') is not None


def check_lasttalk(nick):
    item = tmap.get(nick)
    if item is None:
        return hexchat.EAT_HEXCHAT
    else:
        return hexchat.EAT_NONE


def check_you(nick):
    return not hexchat.nickcmp(hexchat.get_info('nick'), nick)


def check_mode(source_nick, target_nick):
    if check_you(source_nick) or check_you(target_nick):
        return hexchat.EAT_NONE
    elif check_notify(target_nick):
        return hexchat.EAT_NONE
    else:
        return check_lasttalk(target_nick)


def nick_cb(word, word_eol, userdata):
    source_nick = hexchat.strip(word[0])
    target_nick = hexchat.strip(word[1])

    target_lasttalk = check_lasttalk(target_nick)
    tmap.rename(source_nick, target_nick)
    jmap.rename(source_nick, target_nick)
    if check_notify(source_nick) or check_notify(target_nick):
        return hexchat.EAT_NONE

    return target_lasttalk or check_lasttalk(target_nick)


def mode_cb(word, word_eol, userdata):
    source_nick = hexchat.strip(word[0])
    target_nick = hexchat.strip(word[1])
    return check_mode(source_nick, target_nick)


def raw_mode_cb(word, word_eol, userdata):
    source_nick = hexchat.strip(word[0])
    # do some rough nick extraction
    target_nicks = [x for x in word[1].split() if not x.startswith(('+', '-', '#'))]
    for nick in target_nicks:
        if check_mode(source_nick, nick) == hexchat.EAT_NONE:
            return hexchat.EAT_NONE
    else:
        return hexchat.EAT_HEXCHAT


def msg_cb(word, word_eol, event, attrs):
    nick = hexchat.strip(word[0])
    tmap.add(nick, attrs.time or int(time.time()))
    jmap.pop_and_emit(nick)
    return hexchat.EAT_NONE


def join_cb(word, word_eol, userdata, attrs):
    if jmap.is_emitting:
        return hexchat.EAT_NONE
    nick = hexchat.strip(word[0])
    if check_notify(nick):
        return hexchat.EAT_NONE
    else:
        eat = check_lasttalk(nick)
        if eat:
            jmap.add(nick, attrs.time or int(time.time()), word)
        return eat


def part_cb(word, word_eol, userdata):
    nick = hexchat.strip(word[0])
    if check_notify(nick):
        return hexchat.EAT_NONE
    # do not pop from tmap (in case user rejoins)
    jmap.pop(nick)

    return check_lasttalk(word[0])

if __name__ == '__main__':
    for event in ('Quit', 'Part', 'Part with Reason'):
        hexchat.hook_print(event, part_cb)
    for event in ('Channel Operator', 'Channel Voice', 'Channel Half-Operator'):
        hexchat.hook_print(event, mode_cb)
    for event in ('Channel Action', 'Channel Action Hilight',
                  'Channel Message', 'Channel Message Hilight'):
        hexchat.hook_print_attrs(event, msg_cb, event)
    hexchat.hook_print('Raw Modes', raw_mode_cb)
    hexchat.hook_print_attrs('Join', join_cb)
    hexchat.hook_print('Change Nick', nick_cb)

    hexchat.hook_timer(CLEAN_INTERVAL * 1000, lambda x: jmap.clean())
    hexchat.hook_timer(CLEAN_INTERVAL * 1000, lambda x: tmap.clean())

    print(__module_name__, __module_version__, "loaded")
