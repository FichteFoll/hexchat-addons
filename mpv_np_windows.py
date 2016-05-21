import ctypes as c
import ctypes.wintypes as cw
import re

import hexchat

__module_name__ = "mpv now playing (Windows)"
__module_version__ = "0.1.0"
__module_description__ = "Announces filename currently loaded in mpv"
# based on: https://github.com/kuehnelth/xchat_mpv_np/blob/master/xchat_mpv_np_windows.py

MPV_TITLE_REGEX = "^(.*) - mpv$"

user32 = c.windll.user32

# https://msdn.microsoft.com/en-us/library/windows/desktop/ms633498(v=vs.85).aspx
WNDENUMPROC = c.WINFUNCTYPE(cw.BOOL, cw.HWND, cw.LPARAM)  # EnumWindowsProc callback

# https://msdn.microsoft.com/en-us/library/windows/desktop/ms633497(v=vs.85).aspx
EnumWindows = user32.EnumWindows
EnumWindows.argtypes = (WNDENUMPROC, cw.LPARAM)
EnumWindows.restype = cw.BOOL

# https://msdn.microsoft.com/en-us/library/windows/desktop/ms633520%28v=vs.85%29.aspx
GetWindowText = user32.GetWindowTextW
# for some reason, cw.LPSTR causes errors here for *some* (!) windows
# GetWindowText.argtypes = (cw.HWND, cw.LPSTR, c.c_int)
GetWindowText.restype = c.c_int

# https://msdn.microsoft.com/en-us/library/windows/desktop/ms633521(v=vs.85).aspx
GetWindowTextLength = user32.GetWindowTextLengthW
GetWindowTextLength.argtypes = (cw.HWND,)
GetWindowTextLength.restype = c.c_int

# https://msdn.microsoft.com/en-us/library/windows/desktop/ms633530(v=vs.85).aspx
IsWindowVisible = user32.IsWindowVisible
IsWindowVisible.argtypes = (cw.HWND,)
IsWindowVisible.restype = cw.BOOL


def match_window_title(pattern):
    """Find a window by title.

    Returns the hwnd and match object,
    or `(None, None)`.
    """
    handle = None
    match = None

    @WNDENUMPROC
    def enum_windows_proc(hwnd, l_param):
        nonlocal handle, match
        if IsWindowVisible(hwnd):
            length = GetWindowTextLength(hwnd)
            buff = c.create_unicode_buffer(length + 1)
            GetWindowText(hwnd, buff, length + 1)

            m = re.search(pattern, buff.value)
            if m:
                handle = hwnd
                match = m
                return 0  # stop enumeration
        return 1

    EnumWindows(enum_windows_proc, 0)
    return handle, match


def mpv_np(caller, callee, helper):
    hwnd, match = match_window_title(MPV_TITLE_REGEX)

    if not hwnd or not match:
        print("mpv is not runnung")
    else:
        filename = match.group(1)
        hexchat.command("me now playing \x02{}\x0F".format(filename))

    return hexchat.EAT_ALL


if __name__ == '__main__':
    hexchat.hook_command("mpv", mpv_np, help="Usage: /mpv")
    print(__module_name__, __module_version__, "loaded")
