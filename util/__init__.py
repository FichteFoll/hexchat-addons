"""Selected utility functions for hexchat plugin development.

Exported decorators:

- only_on
- no_recursion

Exported functions:

- set_timeout
- event_text_to_format_string
- print_text
"""

from collections import defaultdict
import functools
import re
import threading

import hexchat


__version__ = "0.2.0"
versioninfo = tuple(map(int, __version__.split(".")))
__author__ = "FichteFoll <fichtefoll2@googlemail.com>"

__all__ = (
    'only_on',
    'no_recursion',
    'set_timeout',
    'event_text_to_format_string',
    'print_event',
)


def only_on(servers=(), channels=()):
    """Decorator function that only forwards for certain servers/channels."""
    # ensure filters are enumerable
    if isinstance(servers, str):
        servers = (servers,)
    if isinstance(channels, str):
        channels = (channels,)

    def server_filter(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if servers:
                for server in servers:
                    for host in (hexchat.get_info('host'), hexchat.get_info('server')):
                        if host and server in host:
                            break
                    else:
                        continue
                    break
                else:
                    return hexchat.EAT_NONE

            if channels:
                curr_chan = hexchat.get_info('channel')
                for channel in channels:
                    if channel != curr_chan:
                        break
                else:
                    return hexchat.EAT_NONE

            return func(*args, **kwargs)

        return wrapper

    return server_filter


# Threaded version not needed in hexchat
def no_recursion_threaded(func):
    """Per-thread recursion prevention through Lock objects, as a decorator."""
    setattr(func, '_thread_locks', defaultdict(threading.Lock))

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        cur_thread = threading.current_thread()
        if func._thread_locks[cur_thread].acquire(0):
            try:
                return func(*args, **kwargs)
            finally:
                func._thread_locks[cur_thread].release()
                del func._thread_locks[cur_thread]
    return wrapper


def no_recursion(func):
    """Recursion prevention through Lock objects, as a decorator."""
    setattr(func, '_lock', threading.Lock())

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if func._lock.acquire(0):
            try:
                return func(*args, **kwargs)
            finally:
                func._lock.release()
    return wrapper


def set_timeout(callback, delay=0, args=(), kwargs={}):
    """Delay executiong of a function for `delay` ms.

    Useful for emitting print events in print event hooks
    that should occur after the hooked event has been printed.
    A delay of 0 (default) will suffice in most cases.
    """
    def callback_handler(userdata):
        callback(*args, **kwargs)
        return False  # remove hook

    hexchat.hook_timer(delay, callback_handler)


def event_text_to_format_string(text):
    """Convert an event_text to a Python format string that can be printed.

    See print_event for example usage.
    """
    cmap = {
        'C': '\003',
        'O': '\017',
        'H': '\010',
        'R': '\026',
        'B': '\002',
        'I': '\035',
        'U': '\037',
        '%': '%',
    }

    def percent(match):
        c = match.group(1)
        if c in cmap:
            return cmap[c]
        else:
            return match.group(0)

    def dollar(match):
        c = match.group(1)
        if c == 't':
            return "\t"
        elif c[0] == 'a':
            return chr(int(c[1:]))
        else:
            return "{%d}" % (int(c) - 1)  # formatting group
        return match.group(0)

    text = text.replace("{", "{{").replace("}", "}}")  # escape formatting braces
    text = re.sub(r"%(.)", percent, text)
    text = re.sub(r"\$(t|a\d{3}|\d)", dollar, text)
    return text


def print_event(event_name, *word, context=hexchat):
    """Similar to `hexchat.emit_print` except that no hooks will be called.

    A context may be specified using the `context` keyword argument.
    """
    # TODO doesn't handle `&n`, where n is a number
    fmt = event_text_to_format_string(context.get_info("event_text %s" % event_name))
    context.prnt(fmt.format(*word))
