"""Settings abstraction of hexchat's pluginpref in form of a MutableMapping.

Exported classes:

- PluginPref
"""

from collections.abc import MutableMapping

import hexchat


__version__ = (0, 2, 0)
__author__ = "FichteFoll <fichtefoll2@googlemail.com>"


__all__ = (
    "PluginPref",
)


class PluginPref(MutableMapping):
    """MutableMapping interface for hexchat's pluginpref storage system.

    All settings are internally prefixed with a string
    that is passed to the constructor.


    Limitations of pluginpref:

    - Only supports strings, numbers and booleans.
    - Not lists, dicts, `None`, or arbitrary objects.
      Use the json or pickle modules to serialize those to strings.
    - Booleans are converted to numbers.


    Example usage:

    >>> __module_name__ = "Your Awesome Addon Name"
    >>> pref = PluginPref(__module_name__)  # or __module_name__.replace(" ", "_").lower()
    >>> pref["a_setting"] = "a value"
    >>> "a_setting" in pref
    True
    >>> pref["a_setting"])
    'a value'
    >>> pref["a_number"] = 123
    >>> pref["a_number"]
    123
    >>> pref["a_boolean"] = True
    >>> list(pref.items())
    [("a_setting": "a_value"), ('a_number': 123), ('a_boolean': 1)]
    >>> pref.keys()
    {'a_setting', 'a_number', 'a_bool'}
    >>> for k in pref.keys(): del pref[k]
    >>> list(pref.items())
    []
    >>> del pref["doesn't exist"]
    KeyError: "doesn't exist"
    >>> pref.delete("doesn't exist")
    >>> pref.get("doesn't exist", NotImplemented)
    NotImplemented
    """

    def __init__(self, prefix):
        self.prefix = prefix + "_"

    def keys(self):
        """Return a set of all keys in this PluginPref instance."""
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
