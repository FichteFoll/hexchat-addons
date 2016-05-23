# requires Python 3
from abc import ABCMeta, abstractmethod
import json
import os.path
import socket
import sys

import hexchat


__module_name__ = "mpv now playing"
__module_version__ = "0.3.0"
__module_description__ = "Announces info of the currently loaded 'file' in mpv"

# # Configuration # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

# Paths to mpv's IPC socket or named pipe.
# Set the same path in your mpv.conf `input-ipc-server` setting
# or adjust these values.
WIN_PIPE_PATH = R"\\.\pipe\mpvsocket"
UNIX_PIPE_PATH = "/tmp/mpvsocket"  # variables are expanded

# The command that is being executed with the title found.
# `{title}` will be replaced with the title.
CMD_FMT = "me is playing \x02{title}\x0F"


# # The Script # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

# If asynchronous IO was to be added,
# the Win32API would need to be used on Windows.
# Details:
# - https://msdn.microsoft.com/en-us/library/windows/desktop/aa365683%28v=vs.85%29.aspx
# Examples:
# - https://msdn.microsoft.com/en-us/library/windows/desktop/aa365690%28v=vs.85%29.aspx
# - https://msdn.microsoft.com/en-us/library/windows/desktop/aa365592%28v=vs.85%29.aspx
# - https://github.com/mpv-player/mpv/blob/master/input/ipc-win.c
class MpvIpcClient(metaclass=ABCMeta):

    """Work with an open MPC instance via its JSON IPC.

    In a blocking way.

    Classmethod `for_platform`
    will resolve to one of WinMpvIpcClient or UnixMpvIpcClient,
    depending on the current platform
    """

    def __init__(self, path):
        self.path = path
        self._connect()

    @classmethod
    def for_platform(cls, platform=sys.platform, path=None):
        if platform == 'win32':
            return WinMpvIpcClient(path or WIN_PIPE_PATH)
        else:
            return UnixMpvIpcClient(path or UNIX_PIPE_PATH)

    @abstractmethod
    def _connect(self):
        pass

    @abstractmethod
    def _write_line(self):
        pass

    @abstractmethod
    def _read_line(self):
        pass

    @abstractmethod
    def close(self):
        pass

    def command(self, command, *params):
        data = json.dumps({"command": [command] + list(params)})
        self._write_line(data)
        while 1:
            # read until a result line is found (containing "error" key)
            result_line = self._read_line()
            result = json.loads(result_line)
            if 'error' in result:
                break
        if result['error'] != "success":
            raise RuntimeError("mpv returned an error", result['error'])

        return result['data']

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


class WinMpvIpcClient(MpvIpcClient):

    def _connect(self):
        self._f = open(self.path, "w+t", newline='', encoding='utf-8')

    def _write_line(self, line):
        self._f.write(line.strip())
        self._f.write("\n")
        self._f.flush()

    def _read_line(self):
        return self._f.readline()

    def close(self):
        self._f.close()


class UnixMpvIpcClient(MpvIpcClient):

    buffer = ""

    def _connect(self):
        self._sock = socket.socket(socket.AF_UNIX)
        self.expanded_path = os.path.expanduser(os.path.expandvars(self.path))
        self._sock.connect(self.expanded_path)

    def _write_line(self, line):
        self._sock.sendall(line.strip().encode('utf-8'))
        self._sock.send(b"\n")

    def _read_line(self):
        while 1:
            if b"\n" in self.buffer:
                line, _, self.buffer = self.buffer.partition(b"\n")
                return line.encode('utf-8')
            self.buffer += self._sock.recv(4096)

    def close(self):
        self._sock.close()


###############################################################################


def mpv_np(caller, callee, helper):
    try:
        with MpvIpcClient.for_platform() as mpv:
            title = mpv.command("get_property", "media-title")
            hexchat.command(CMD_FMT.format(title=title))
    except OSError:
        # import traceback; traceback.print_exc()
        print("mpv IPC not running or bad configuration (/help mpv)")

    return hexchat.EAT_ALL


if __name__ == '__main__':
    help_str = (
        "Usage: /mpv\n"
        "Setup: set `input-ipc-server={path}` in your mpv.conf file "
        "(or adjust the path in the script source)."
        .format(path=WIN_PIPE_PATH if sys.platform == 'win32' else UNIX_PIPE_PATH)
    )
    hexchat.hook_command("mpv", mpv_np, help=help_str)
    print(__module_name__, __module_version__, "loaded")
