local ffi = require('ffi')
local lgi = require('lgi')
local Gio = lgi.require('Gio')
local GLib = lgi.require('GLib')


hexchat.register('viewlog', '1.0.2', "Open log file for the current context")


local DEFAULT_PROGRAM = "notepad"
local DIR_SEP = ffi.os == 'Windows' and "\\" or "/"


-- util.c:rfc_strlower -> -- util.h:rfc_tolower -> util.c:rfc_tolowertab
-- https://github.com/hexchat/hexchat/blob/c79ce843f495b913ddafa383e6cf818ac99b4f15/src/common/util.c#L1079-L1081
local function rfc_strlower(str)
    -- almost according to rfc2812,
    -- except for ^ -> ~ (should be ~ -> ^)
    -- https://tools.ietf.org/html/rfc2812
    str = str:gsub("[A-Z%[%]\\^]", function (letter)
        return string.char(letter:byte() + 0x20)
    end)
end


-- text.c:log_create_filename
local function log_create_filename(channame)
    if not channame then
        return channame
    elseif ffi.os == 'Windows' then
        return channame:gsub('[\\|/><:"*?]', "_")
    else
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


function open_file(file, program)
    local cmd = ('"%s" "%s"'):format(program, file:get_path())
    if ffi.os == "Windows" then
        -- Windows requires the entire thing to be wrapped in quotes,
        -- for some reason
        cmd = ('"%s"'):format(cmd)
    end

    -- print("launching " .. cmd)
    io.popen(cmd)
    -- local result = os.execute(cmd)
    -- if result ~= 0 then
    --     hexchat.command(('GUI MSGBOX "Unable to launch program. Exit code: %d"')
    --                     :format(result))
    -- end
end


local function viewlog_cb(word, word_eol)
    local program = #word > 1 and word_eol[2] or DEFAULT_PROGRAM

    local logfile = log_create_pathname(hexchat.get_context())
    if not logfile then
        return hexchat.EAT_ALL
    end

    if logfile:query_exists() then
        open_file(logfile, program)
    else
        hexchat.command(('GUI MSGBOX "Log file for the current channel/dialog does not seem to exist.\n\n""%s""')
                        :format(logfile:get_path()))
    end

    return hexchat.EAT_ALL
end


hexchat.hook_command("viewlog", viewlog_cb,
                     "Usage: /viewlog [program] - Open log file of the current context in 'program' (path to executable)")
