"""Settings abstraction of hexchat's pluginpref in form of a MutableMapping.

Exported classes:

- PluginPref
- SerializablePluginPref
- JSONPluginPref
"""

from abc import ABCMeta, abstractmethod
from collections.abc import MutableMapping
import json

import hexchat


__version__ = "0.3.1"
versioninfo = tuple(map(int, __version__.split(".")))
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


    Limitations of pluginpref (as provided by hexchat):

    - Only supports strings, numbers and booleans.
    - Not lists, dicts, `None`, or arbitrary objects.
      Use the json or pickle modules to serialize those to strings.
    - Booleans are converted to numbers.
    - Strings consisting of only digits are also converted to numbers.


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

    def __contains__(self, key):
        # More efficient than default
        return key in self.keys()

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

    def get_version(self):
        """Retrieve the currently stored preferences' version.

        Returns an integer or a tuple of integers, depending on what was set.
        Returns `None` if not set.
        Returns `NotImplemented` if parsing the version failed.

        Set the version with `set_version`.
        """
        version_str = hexchat.get_pluginpref(self.version_pref_name)
        if not version_str:
            return
        version_split = version_str.split('.')
        try:
            if len(version_split) == 1:
                return int(version_split[0])
            else:
                return tuple(map(int, version_split))
        except ValueError:
            return NotImplemented

    def set_version(self, version):
        """Set the currently stored preferences' version.

        `version` must be an integer or a tuple of integers
        for easier comparison.

        Set the version with `set_version`.
        """
        if isinstance(version, int):
            version_str = str(version)
        elif (isinstance(version, tuple)
              and all(isinstance(i, int) for i in version)):
            version_str = ".".join(map(str, version))
        else:
            raise TypeError("version must be an integer or a tuple of integers")

        return hexchat.set_pluginpref(self.version_pref_name, version_str)

    version = property(
        get_version,
        set_version,
        doc="""Property for permanent storage of the current preferences' version.

        Useful for migration.

        See get_version and set_version for details."""
    )


class SerializablePluginPref(PluginPref, metaclass=ABCMeta):
    """Abstract base class for serializable interfaces on top of PluginPref.

    Requires definitions of the two methods:
    - serialize(obj)
    - deserialize(obj)
    which get called before writing to
    and after reading from PluginPref respectively.
    """
    @abstractmethod
    def serialize(self, obj):
        """Serialize `obj` into another object."""
        return obj

    @abstractmethod
    def deserialize(self, obj):
        """Deserialize `obj` into another object."""
        return obj

    def __getitem__(self, key):
        value = super().__getitem__(key)
        return self.deserialize(value)

    def __setitem__(self, key, value):
        value = self.serialize(value)
        super().__setitem__(key, value)


class JSONPluginPref(SerializablePluginPref):
    """MutableMapping built on top of PluginPref with JSON serialization.

    Overcomes shortcomings of default PluginPref implementation
    by (de-)serializing all values as strings
    and thus supports all serializable formats.
    Notably: dict, list, real boolans, None

    Note that dictionary keys are converted to strings,
    as by `json.dumps`.

    Raises `json.JSONDecodeError` when decoding a value failed
    and `TypeError` if the specified value is not serializable.

    If you want to change JSON (de-)serialidation,
    subclass this class or SerializablePluginPref
    and override `serialize` and `deserialize`
    with a method of your choice.

    Usage of `super()` allows nesting of SerializablePluginPref subclasses
    other other interesting subclassing models.
    """

    def serialize(self, obj):
        obj = json.dumps(obj)
        return super().serialize(obj)

    def deserialize(self, obj):
        # For some reason, hexchat's pluginpref auto-converts strings
        # containing only digits to integers. We have to convert them back
        # here.
        if isinstance(obj, int):
            obj = str(obj)
        obj = super().serialize(obj)
        return json.loads(obj)
