"""Tests for pluginpref module.

Run using `/py load pluginpref/test.py`.
"""

import json

import hexchat

try:
    from . import PluginPref, JSONPluginPref
except SystemError:
    # Add addons path to sys.path for win32
    # See https://github.com/hexchat/hexchat/issues/1396
    import os
    import sys

    if sys.platform == "win32":
        addons_path = os.path.join(hexchat.get_info("configdir"), "addons")
        if addons_path not in sys.path:
            sys.path.append(addons_path)

    import pluginpref
    from imp import reload
    reload(pluginpref)

    from pluginpref import PluginPref, JSONPluginPref

__module_name__        = "PluginPref tests"
__module_version__     = "0.2.0"
__module_description__ = "tests for PluginPref abstraction"
__module_author__      = "FichteFoll <fichtefoll2@googlemail.com>"


def core_pluginpref_tests(prefs):
    # initial cleanup
    for key in prefs:
        prefs.delete(key)
    assert not prefs  # Should be empty!

    other_pref_keys = hexchat.list_pluginpref()

    assert list(prefs.items()) == []
    assert "mute" not in prefs
    prefs["mute"] = "#test"
    assert "mute" in prefs
    assert (prefs["mute"] == "#test")

    assert prefs.get("mute", 12) == "#test"
    assert prefs.get("mute2", 12) == 12
    assert prefs.setdefault("mute", 32) == "#test"
    assert prefs.setdefault("mute2", 32) == 32

    assert dict(prefs.items()) == dict([('mute2', 32), ('mute', '#test')])
    all_prefs = (set(map(lambda x: prefs.prefix + prefs.prefix_sep + x, prefs.keys()))
                 | set(other_pref_keys))
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
    assert other_pref_keys == hexchat.list_pluginpref()


def test_pluginpref():
    prefs = PluginPref("prefs_test")
    core_pluginpref_tests(prefs)

    prefs["mute"] = "#test"
    assert hexchat.get_pluginpref(prefs.prefix + prefs.prefix_sep + "mute") == "#test"
    del prefs["mute"]
    # specific to the default implementation
    try:
        prefs["mute"] = None
        assert False, "should have raised"
    except ValueError:
        pass
    try:
        prefs["mute"] = [1, 2, 3]
        assert False, "should have raised"
    except RuntimeError:
        pass

    print("test_pluginpref passed")


def test_jsonpluginpref():
    prefs = JSONPluginPref("json_prefs_test")
    other_pref_keys = hexchat.list_pluginpref()

    # perform core tests too
    core_pluginpref_tests(prefs)

    # additional tests
    a_list = list(range(10))
    a_dict = {chr(ord('A') + i): i for i in range(10)}

    prefs['a_list'] = a_list
    assert hexchat.get_pluginpref(prefs.prefix + prefs.prefix_sep + "a_list") == json.dumps(a_list)

    prefs['a_dict'] = a_dict
    assert hexchat.get_pluginpref(prefs.prefix + prefs.prefix_sep + "a_dict") == json.dumps(a_dict)
    prefs['null'] = None
    assert hexchat.get_pluginpref(prefs.prefix + prefs.prefix_sep + "null") == 'null'

    assert dict(prefs.items()) == dict([('a_list', a_list),
                                        ('a_dict', a_dict),
                                        ('null', None)])

    for key in prefs:
        prefs.delete(key)
    assert not prefs

    assert other_pref_keys == hexchat.list_pluginpref()
    print("test_jsonpluginpref passed")


def main():
    test_pluginpref()
    test_jsonpluginpref()
    print("all tests passed!")

if __name__ == '__main__':
    main()
