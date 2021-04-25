local lgi = require('lgi')
local Gio = lgi.require('Gio')
local GLib = lgi.require('GLib')


hexchat.register("viewlog", "1.2.2", "Open log file for the current context")


--[=[
    We would like to use Gio.AppInfo.get_recommended_for_type("text/plain"),
    but it doesn't work (on Windows).
    Gio.AppInfo.launch_default_for_uri also launches notepad on Windows, so no help.

    Instead, we require the user
    to provide a program (and arguments).
    The first `%s` occurance in a string or `nil`
    will be replaced with the logfile path.

    Note that on Windows,
    "notepad.exe" can not handle LF line breaks,
    which Hexchats writes in recent versions.

    Examples:
        local DEFAULT_PROGRAM = {[[e:\Program Files\Sublime Text 3\sublime_text.exe]]}
        local DEFAULT_PROGRAM = {"termite", "-e", "less -- '%s'"}
]=]
local DEFAULT_PROGRAM = {"alacritty", "-e", "less -- '%s'"} -- MODIFY THIS --


---------------------------------------------------------------------------------------------------

-- Relies on window pointer implementation to determine whether we're on Windows or not
-- (instead of using ffi.os, which is not available in vanilla lua).
local is_windows = hexchat.get_info('win_ptr') ~= hexchat.get_info('gtkwin_ptr')


-- util.c:rfc_strlower -> -- util.h:rfc_tolower -> util.c:rfc_tolowertab
-- https://github.com/hexchat/hexchat/blob/c79ce843f495b913ddafa383e6cf818ac99b4f15/src/common/util.c#L1079-L1081
local function rfc_strlower(str)
    -- almost according to rfc2812,
    -- except for ^ -> ~ (should be ~ -> ^)
    -- https://tools.ietf.org/html/rfc2812
    return str:gsub("[A-Z%[%]\\^]", function (letter)
        return string.char(letter:byte() + 0x20)
    end)
end


-- text.c:log_create_filename
local function log_create_filename(channame)
    if not channame then
        return channame
    elseif is_windows then
        return channame:gsub('[\\|/><:"*?]', "_")
    else
        channame = channame:gsub('/', "_")
        return rfc_strlower(channame)
    end
end


-- text.c:log_create_pathname
local function log_create_pathname(ctx)
    local network = log_create_filename(ctx:get_info('network')) or "NETWORK"
    local server  = log_create_filename(ctx:get_info('server'))
    local channel = log_create_filename(ctx:get_info('channel'))

    -- print(("n: %s, s: %s, c: %s"):format(network, server, channel))
    if not server then
        return nil
    end
    if server and hexchat.nickcmp(channel, server) == 0 then
        channel = 'server';
    end

    local logmask = hexchat.prefs['irc_logmask']
    local fname = logmask

    -- substitute variables after strftime expansion
    fname = fname:gsub("%%([scn])", "\001%1")
    fname = os.date(fname)  -- strftime

    -- text.c:log_insert_vars & text.c:log_escape_strcpy
    -- parentheses are required because gsub returns two values
    fname = fname:gsub("\001n", (network:gsub("%%", "%%%%")))
    fname = fname:gsub("\001s", (server:gsub("%%", "%%%%")))
    fname = fname:gsub("\001c", (channel:gsub("%%", "%%%%")))

    -- Calling GLib.filename_from_utf8 crashes on Windows
    -- (https://github.com/hexchat/hexchat/issues/1824)
    -- local config_dir = GLib.filename_from_utf8(hexchat.get_info('configdir'), -1)
    -- local log_path = GLib.build_filenamev({config_dir, GLib.filename_from_utf8("logs", -1)})
    local log_path = GLib.build_filenamev({hexchat.get_info('configdir'), "logs"})
    return Gio.File.new_for_commandline_arg_and_cwd(fname, log_path)
end


function subprocess(cmd)
    local launcher = Gio.SubprocessLauncher.new(0) -- Gio.SubprocessFlags.STDOUT_SILENCE
    return launcher:spawnv(cmd)
end


local function viewlog_cb(word, word_eol)
    local program
    if #word > 1 then
        program = {word_eol[2]} -- TODO what about arguments?
    else
        program = DEFAULT_PROGRAM
    end
    if not type(program) == 'table' or #program == 0 then
        hexchat.command('GUI MSGBOX "You need to specify a program to launch in the source code."')
        return hexchat.EAT_ALL
    end

    local logfile = log_create_pathname(hexchat.get_context())
    if logfile == nil then
        return hexchat.EAT_ALL
    end

    -- Build cmd and replace first '%s' or 'nil' in program.
    -- This will end up appending if there is no nil in the middle.
    local cmd = program
    for i = 1, #program + 1 do
        if cmd[i] == nil then
            cmd[i] = logfile:get_path()
            break
        elseif cmd[i]:find("%%s") then
            cmd[i] = cmd[i]:format(logfile:get_path())
            break
        end
    end

    if logfile:query_exists() then
        if subprocess(cmd) == nil then
            hexchat.command('GUI MSGBOX "Unable to launch program."')
        end
    else
        hexchat.command(('GUI MSGBOX "Log file for the current channel/dialog does not seem to '
                         .. 'exist.\n\n""%s""')
                        :format(logfile:get_path()))
    end

    return hexchat.EAT_ALL
end


hexchat.hook_command("viewlog", viewlog_cb,
                     "Usage: /viewlog [program] - Open log file of the current context in "
                     .. "'program' (path to executable). \n"
                     .. "You should set a default program (and arguments) in the script's source code.")
