FichteFoll's Hexchat addons
===========================

This is just a compilation of modules and addons for hexchat,
using its Python plugin.


## Modules

### [pluginpref](./pluginpref)

Abstractions for hexchat's `hexchat.*_pluginpref` interface,
wrapped in a MutableMapping.
All settings are automatically prefixed with,
for example, the plugin name
to prevent collisions.

Its interface is essentially a `dict`.
For details, refer to docstring or tests (in same directory).


## Addons

### [current_channel_replace.py](./current_channel_replace.py)

Replace the `#` character with the current channel
when you press space or tab after it.
Insert literal space when holding shift key.

Note: Only works if at the end of input.


### [youtube_title.py](./current_channel_replace.py)

Print (or announce) a YouTube video's title.

[**Requires a Google API key!**](#how-to-obtain-a-google-api-key)
(which needs to be inserted in the source, for now)

By default, it will only print the title for you locally.

- `\ytt get` prints titles of the videos specified
- `\ytt announce` manages a list of channels
  where the title should be announced (i.e. `/say`)
- `\ytt mute` manages a list of channels
  where YouTube urls should be ignored


## How to obtain a Google API key

Prerequisites: A Google account

1. Create a project at https://console.developers.google.com/project
2. Browse "APIs & auth -> APIs" in the sidebar
3. Select "YouTube Data API"
4. Click "Enable API"
5. Browse "APIs & auth -> Credentials" in the sidebar
6. Click "Create new Key"
7. Select "Server Key" and leave the IP range input blank (or insert some IP range if you feel like it)
