"""Tests for pluginpref module.

Run using `/py load pluginpref/test.py`.
"""

import hexchat

try:
    from . import PluginPref
except SystemError:
    # Add addons path to sys.path for win32
    # See https://github.com/hexchat/hexchat/issues/1396
    import os
    import sys

    if sys.platform == "win32":
        addons_path = os.path.join(hexchat.get_info("configdir"), "addons")
        if addons_path not in sys.path:
            sys.path.append(addons_path)

    from pluginpref import PluginPref

__module_name__        = "PluginPref tests"
__module_version__     = "0.2.0"
__module_description__ = "tests for PluginPref abstraction"
__module_author__      = "FichteFoll <fichtefoll2@googlemail.com>"


# Testing
prefs = PluginPref("prefs_test")
if prefs:
    for key in prefs:
        del prefs[key]
assert not prefs  # Should be empty!

other_prefs = hexchat.list_pluginpref()

assert list(prefs.items()) == []
assert "mute" not in prefs
try:
    prefs["mute"] = None
    assert False, "should have raised"
except ValueError:
    pass
prefs["mute"] = "#test"
assert "mute" in prefs
assert hexchat.get_pluginpref(prefs.prefix + "mute") == "#test" == prefs["mute"]

assert prefs.get("mute", 12) == "#test"
assert prefs.get("mute2", 12) == 12
assert prefs.setdefault("mute", 32) == "#test"
assert prefs.setdefault("mute2", 32) == 32

assert set(prefs.items()) == set([('mute2', 32), ('mute', '#test')])
all_prefs = set(map(lambda x: prefs.prefix + x, prefs.keys())) | set(other_prefs)
assert all_prefs == set(hexchat.list_pluginpref())
assert len(prefs) == 2

del prefs["mute"]
assert "mute" not in prefs
try:
    del prefs["mute"]
    assert False, "should have raised"
except KeyError:
    pass
prefs.delete("mute2")
assert not prefs
assert other_prefs == hexchat.list_pluginpref()

print("all pref_tests passed!")
