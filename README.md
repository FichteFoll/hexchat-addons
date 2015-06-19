FichteFoll's Hexchat addons
===========================

This is just a compilation of addons for hexchat,
using it's Python plugin.


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

**Requires a Google API Key!**
(that you currently need to insert in the source)

By default, it will only print the title for you locally.

- `\ytt get` prints titles of the videos specified
- `\ytt announce` manages a list of channels
  where the title should be announced (i.e. `/say`)
- `\ytt mute` manages a list of channels
  where YouTube urls should be ignored
