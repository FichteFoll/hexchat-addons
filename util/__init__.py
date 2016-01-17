"""Selected utility functions for hexchat plugin development.

Exported decorators:

- only_on
- no_recursion
"""

from collections import defaultdict
import functools
import threading

import hexchat


__version__ = "0.1.0"
versioninfo = tuple(map(int, __version__.split(".")))
__author__ = "FichteFoll <fichtefoll2@googlemail.com>"

__all__ = (
    'only_on',
    'no_recursion'
)


def only_on(servers=tuple(), channels=tuple()):
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
