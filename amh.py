#!/usr/bin/python
# -*- coding: utf-8 -*-

# Python 3.3
# HexChat 2.9.6

__module_name__ = "Anti Massive Highlight"
__module_version__ = "1.1"
__module_description__ = "Hides messages that contain lots of nicknames."

import hexchat


def privmsg(word, word_eol, userdata, attrs):
    ctx = hexchat.get_context()
    users = ctx.get_list('users')
    nicks = {user.nick.lower() for user in users}
    words = {w.lower() for w in word_eol[3][1:].split()}
    highlights = nicks & words
    nick, *_ = word[0][1:].partition("!")

    if len(highlights) >= 5:
        return hexchat.EAT_ALL
    elif len(highlights) >= 3 and nick[-3:].isdigit():
        # Recent freenode spammers sometimes have less than 5 highlights,
        # but they all have three digits at the end of their nicks.
        return hexchat.EAT_ALL
    return hexchat.EAT_NONE


hexchat.hook_server_attrs('PRIVMSG', privmsg)
