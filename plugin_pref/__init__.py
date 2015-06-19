"""TODOC
"""

import collections.abc

import hexchat


__version__ = (0, 2, 0)
__author__ = "FichteFoll <fichtefoll2@googlemail.com>"


__all__ = (
    "PluginPref",
)


class PluginPref(collections.abc.MutableMapping):
    """MutableMapping interface for hexchat's pluginpref storage system.

    pluginpref does not allow setting `None`
    since it's returned by get_pluginpref
    if the key has not been assigned a value.
    """

    def __init__(self, prefix):
        self.prefix = prefix + "_"

    def keys(self):
        all_keys = hexchat.list_pluginpref(self.prefix)
        keys = set()
        for key in all_keys:
            if key.startswith(self.prefix):
                keys.add(key[len(self.prefix):])
        return keys

    def __iter__(self):
        return iter(self.keys())

    def __len__(self):
        return len(self.keys())

    def __getitem__(self, key):
        if not isinstance(key, str):
            raise TypeError("Key must be a string")
        val = hexchat.get_pluginpref(self.prefix + key)
        if val is None:
            raise KeyError(key)
        return val

    def __setitem__(self, key, value):
        if not isinstance(key, str):
            raise TypeError("Key must be a string")
        if value is None:
            raise ValueError("Can not set `None`")
        if not hexchat.set_pluginpref(self.prefix + key, value):
            raise RuntimeError("Could not set %s" % value)

    def __delitem__(self, key):
        if not isinstance(key, str):
            raise TypeError("Key must be a string")
        if key not in self:
            raise KeyError(key)
        else:
            self.delete(key)

    def delete(self, key):
        """Unlike `del`, this does not raise if the key does not exist.
        """
        if not isinstance(key, str):
            raise TypeError("Key must be a string")
        if not hexchat.del_pluginpref(self.prefix + key):
            raise RuntimeError("Could not delete %s" + key)
