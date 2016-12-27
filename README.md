FichteFoll's Hexchat Addons
===========================

This is just a compilation of modules and addons for hexchat,
using its Python plugin.

All scripts are tested 
to work on **Hexchat 2.12.1**
with **Python 3.5** as plugin engine
(and Windows 7 as OS).
Lua scripts require the Lua plugin engine to be installed
(available since Hexchat 2.12).


## Installation

1. Click the link to opening the source file on Github
2. Right-clicking the "Raw" button on the right side
3. Select "Save Link as...".
4. Download the file to your Hexchat's *addons* folder,
   where they will automatically be loaded from on startup.  
   Example: `'C:\\Users\\Fichte\\AppData\\Roaming\\HexChat\\addons'`

The following Hexchat command 
will print the path to your addons folder:

```
/py exec import os; print(os.path.join(hexchat.get_info("configdir"), "addons"))
```

Scripts that use one or more other *modules*
require those to be downloaded as well.
Download every file in the module's directory,
like you would download a script,
and place them into the appropriate directory
in your addons folder.

**Make sure that the directory structure is preserved**
and create directories when necessary.


## Modules

Some of my scripts share utility functions 
that I branched into their own modules
for better code re-use.

### [pluginpref](./pluginpref/__init__.py)

Abstractions for hexchat's `hexchat.*_pluginpref` API,
wrapped in a MutableMapping,
so *the interface is essentially a `dict`*.

All settings are prefixed with the plugin name internally
to prevent collisions.
Supports being wrapped with a JSON serializer,
thus allowing to store lists and dictionaries too,
and can optionally version a settings schema for you.

For details, refer to docstring or tests (in same directory).

### [util](./util/__init__.py)

Collection of utility functions.

Refer to the source code and docstrings for details.


## Addons

### [better_raw_modes.py](./better_raw_modes.py)

Transforms raw mode messages
to remove redundant information,
i.e. the channel name.

Requires `/set irc_raw_modes 1`.

May cause incompatibilities with other scripts
that rely on a certain Raw Modes format.

Used modules: `util`


### [current_channel_replace.py](./current_channel_replace.py)

Expands a preceding `#` character to the current channel
when you press space or tab after it.
Hold shift key to insert literal space.


### [ff_twitch.py](./ff_twitch.py)

Mutes spammy +o, -o 
as well as join and part messages 
if there are more than a certain number of users in a channel.

Used modules: `util`


### [mpv_np.py](./mpv_np.py)

Executes a hexchat command 
subject to mpv's [property expansion][]
by using its IPC protocol.
This can be used to announces the currently loaded file.
Requires setting `input-ipc-server`
in mpv's config file
(refer to `/help mpv`).

UNIX systems are supported but untested
(and only support the legacy method as of now).

```
[00:32:07] * FichteFoll is playing NOMA - Brain Power [00:01:04 / 00:06:08]
```

[property expansion]: https://mpv.io/manual/stable/#property-expansion


### [smart_filter.py](./smart_filter.py)

Based on [smartparts.py][].

Mutes a variety of events for users that never talk,
or haven't talked in a certain period
(60 minutes by default).

- Muted events are:
  joins, parts, renames and mode changes.
- If a recently joined user starts talking,
  his 'Join' event is late-emitted with the original timestamp.
- Handles renames.
- If a user that previously talked 
  parts and joins again (or renames),
  the events are shown.
- Events for nicks in your notify list are always shown.
- Mode changes that affect the channel are always shown.

Works with ZNC bouncers 
and also with \*buffextras module 
using [buffextras.py][].

Also works with Python 2.7.
Requires Hexchat 2.12.2.

[smartparts.py]: https://github.com/TingPing/plugins/blob/master/HexChat/smartparts.py
[buffextras.py]: https://github.com/knitori/tools/blob/master/hexchat/buffextras.py


### [viewlog.lua](./viewlog.lua)

Improved Lua port of the [Perl script][].
Adds the `/viewlog` command,
which opens the log file
of the currently active context.

A default program for the log file
**must** be configured in the source code.
See the comments there for details.

[Perl script]: https://github.com/Farow/hexchat-scripts/blob/master/viewlog.pl


### [youtube_title.py](./youtube_title.py)

Print (or announce) a YouTube video's title.

**Requires a Google API key!**
See below on how to obtain one](#how-to-obtain-a-google-api-key).
Set it using `/ytt key set <key>`.

By default, it will only print the title for you locally.

- `/ytt get` prints titles of the videos specified
- `/ytt announce` manages a list of channels
  where the title should be announced (i.e. `/say`)
- `/ytt mute` manages a list of channels
  where YouTube urls should be ignored
- `/ytt key` manages the stored key

Used modules: `pluginpref`, `util`


#### How to obtain a Google API key

Prerequisites: A Google account

1. Create a project at https://console.developers.google.com/project
2. Browse "APIs & auth -> APIs" in the sidebar
3. Select "YouTube Data API"
4. Click "Enable API"
5. Browse "APIs & auth -> Credentials" in the sidebar
6. Click "Create new Key"
7. Select "Server Key" and leave the IP range input blank (or insert some IP range if you feel like it)
