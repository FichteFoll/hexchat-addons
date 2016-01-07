"""Settings abstraction of hexchat's pluginpref in form of a MutableMapping.

Exported classes:

- PluginPref
"""

from collections.abc import MutableMapping

import hexchat


__version__ = (0, 2, 0, '+')
__author__ = "FichteFoll <fichtefoll2@googlemail.com>"


__all__ = (
    "PluginPref",
    "SerializablePluginPref",
    "JSONPluginPref",
)


class PluginPref(MutableMapping):
    """MutableMapping interface for hexchat's pluginpref storage system.

    All settings are internally prefixed with a string
    that is passed to the constructor.
    The prefix will usually be built from the module name
    but can be overridden.


    Limitations of pluginpref:

    - Only supports strings, numbers and booleans.
    - Not lists, dicts, `None`, or arbitrary objects.
      Use the json or pickle modules to serialize those to strings.
    - Booleans are converted to numbers.


    Example usage:

    >>> __module_name__ = "Your Awesome Addon Name"
    >>> pref = PluginPref(__module_name__)
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
    >>> hexchat.list_pluginpref()
    [..., 'your_awesome_addon_name.a_setting',
    'your_awesome_addon_name.a_number', 'your_awesome_addon_name.a_bool', ...]
    >>> for k in pref.keys(): del pref[k]
    >>> list(pref.items())
    []

    >>> del pref["doesn't exist"]
    KeyError: "doesn't exist"
    >>> pref.delete("doesn't exist")
    >>> pref.get("doesn't exist", NotImplemented)
    NotImplemented
    """

    def __init__(self, name=None, prefix_sep=".", prefix=None):
        """Build a new mutable PluginPref mapping.

        Arguments determine the prefix,
        which will usually be constructed from the `__module_name__`,
        given as the first parameter.

        The module name will have surrounding spaces stripped,
        spaces replaced by underscores,
        be lowercased,
        and have leading underscores stripped.

        If desired, prefix may be specified
        and will override unification of the passed module name.

        prefix_sep is inserted between the prefix and key names (default '.').
        """
        if not (name or prefix):
            raise TypeError("name or prefix must be provided")
        self.prefix = prefix or name.strip().replace(" ", "_").lower().lstrip("_")
        self.prefix_sep = prefix_sep
        self.version_pref_name = "_version.%s" % self.prefix

    def _keyname(self, key=""):
        return self.prefix + self.prefix_sep + key

    def keys(self):
        """Return a set of all keys in this PluginPref instance."""
        shared_prefix = self._keyname()
        all_keys = hexchat.list_pluginpref()
        keys = set()
        for key in all_keys:
            if key.startswith(shared_prefix):
                keys.add(key[len(shared_prefix):])
        return keys

    def __iter__(self):
        return iter(self.keys())

    def __len__(self):
        return len(self.keys())

    def __getitem__(self, key):
        if not isinstance(key, str):
            raise TypeError("Key must be a string")
        val = hexchat.get_pluginpref(self._keyname(key))
        if val is None:
            raise KeyError(key)
        return val

    def __setitem__(self, key, value):
        if not isinstance(key, str):
            raise TypeError("Key must be a string")
        if value is None:
            raise ValueError("Can not set `None`")
        if not hexchat.set_pluginpref(self._keyname(key), value):
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
        if not hexchat.del_pluginpref(self._keyname(key)):
            raise RuntimeError("Could not delete %s" + key)
