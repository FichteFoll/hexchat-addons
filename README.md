FichteFoll's Hexchat addons
===========================

This is just a compilation of modules and addons for hexchat,
using its Python plugin.


## Modules

### [pluginpref](./pluginpref)

Abstractions for hexchat's `hexchat.*_pluginpref` API,
wrapped in a MutableMapping.
All settings are prefixed with the plugin name internally
to prevent collisions.

The interface is essentially a `dict`.
For details, refer to docstring or tests (in same directory).


## Addons

### [current_channel_replace.py](./current_channel_replace.py)

Expands a preceding `#` character to the current channel
when you press space or tab after it.
Hold shift key to insert literal space.

Note: Only works if at the end of input.


### [youtube_title.py](./youtube_title.py)

Print (or announce) a YouTube video's title.

[**Requires a Google API key!**](#how-to-obtain-a-google-api-key)
Set it using `/ytt key set <key>`.

By default, it will only print the title for you locally.

- `/ytt get` prints titles of the videos specified
- `/ytt announce` manages a list of channels
  where the title should be announced (i.e. `/say`)
- `/ytt mute` manages a list of channels
  where YouTube urls should be ignored
- `/ytt key` manages the stored key


#### How to obtain a Google API key

Prerequisites: A Google account

1. Create a project at https://console.developers.google.com/project
2. Browse "APIs & auth -> APIs" in the sidebar
3. Select "YouTube Data API"
4. Click "Enable API"
5. Browse "APIs & auth -> Credentials" in the sidebar
6. Click "Create new Key"
7. Select "Server Key" and leave the IP range input blank (or insert some IP range if you feel like it)
