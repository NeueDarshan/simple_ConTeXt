local to_dict = require("table_to_dict")


local P, R, S = lpeg.P, lpeg.R, lpeg.S
local C, Ct, match = lpeg.C, lpeg.Ct, lpeg.match


local function CP(x) return C(P(x)) end
local function const(x) return function() return x end end


local UNDEF_CS_ERR = 1
local TEX_ERROR = 2
local MP_ERROR = 3
local LUA_ERROR = 4


local log

do
    local anything = P(1)
    local end_of_string = -anything
    local space = S(" \t")
    local line = S("\r\n\f\v")
    local whitespace = space + line
    local whatever = anything - line
    local digit = R("09")
    local number = digit^1
    local letter = R("az") + R("AZ")
    local other = S("_@!?")
    local slash = P("\\")
    local ctrl_seq = slash * (letter + other)^1
    local arrow = P(">")
    local sep = (space^1 * arrow * space^0) + (arrow * space^1)
    local char = anything - arrow - whitespace
    local text = char^1 * (space^1 * char^1)^0
    local blank_line = space^0 * line
    local non_blank_line = space^0 * (whatever - space)^1 * whatever^0 * line
    local exclam = P("!")
    local colon = P(":")

    local function spaced(x, f)
        return space^0 * (type(f) == "function" and f(x) or x) * space^0
    end
    local function not_prefixed_line(x)
        return space^0 * (whatever^0 - x) * line
    end

    local error_snippet = (space^0 * number * whatever^0 * line)^0
    local error_text = char^1 * space^0 * P("error")
    local file_name = spaced( (whatever - (colon * whitespace))^0 )

    local file_context =
        spaced("on", P) * C(P("line") * space^0 * number) *
        spaced("in file", P) * file_name * colon
    local line_context =
        not_prefixed_line(spaced("l.", P) * number)^0 * spaced("l.", P) *
        spaced(number)
    local trailing_lines = non_blank_line^0 * blank_line^0

    local tex_error_init = space^0 * P("tex error") * sep
    local tex_error_preamble =
        tex_error_init * CP("tex error") / const(TEX_ERROR) * file_context *
        spaced(exclam) * C(whatever^1) * line * blank_line^0
    local tex_error_line = line_context * whatever^0 * line * trailing_lines
    local tex_error =
        Ct(tex_error_preamble * (tex_error_line * error_snippet)^-1)

    local undef_cs_preamble =
        tex_error_init * P("tex error") * file_context * spaced(exclam) *
        ( spaced("Undefined control sequence", CP) / const(UNDEF_CS_ERR) ) *
        line * blank_line^0
    local undef_cs_line =
        line_context * (C(ctrl_seq) + (whatever - slash)^1)^0 * line *
        trailing_lines
    local undef_cs_err = Ct(undef_cs_preamble * undef_cs_line * error_snippet)

    local lua_error_preamble =
        space^0 * P("lua error") * sep * CP("lua error") / const(LUA_ERROR) *
        file_context * whatever^0 * line * blank_line^0
    local lua_error_main =
        space^0 * P("[ctxlua]") * spaced(colon) * number * spaced(colon) *
        C(whatever^1) * line * trailing_lines
    local lua_error = Ct(lua_error_preamble * lua_error_main * error_snippet)

    local mp_error_preamble =
        spaced(error_text) * sep * CP("mp error") / const(MP_ERROR) *
        file_context * whatever^0 * line * blank_line^0
    local mp_error_main =
        not_prefixed_line(exclam)^0 * spaced(exclam) * C(whatever^1) * line *
        blank_line^0 * trailing_lines^-3
    local mp_error = Ct(mp_error_preamble * mp_error_main * error_snippet)

    local generic_error =
        Ct(spaced(error_text, C) * (sep * C(text) + sep)^1 * space^0 * line)

    local error_ =
        lua_error + mp_error + undef_cs_err + tex_error + generic_error
    local message =
        Ct(space^0 * C(text) * (sep * C(text) + sep)^1 * space^0 * line)

    log =
        Ct( (error_ + message + blank_line + non_blank_line)^0 ) *
        end_of_string
end


local function parse_log(text)
    return match(log, text .. "\n")
end


local function without_singletons(tab)
    local result = {}
    for _, t in ipairs(tab) do
        if type(t) == "table" then
            if #t > 1 then
                result[#result + 1] = t
            end
        else
            result[#result + 1] = t
        end
    end
    return result
end


local function get_line(s)
    return tonumber(string.sub(s, 6))
end


local function lower_first_char(s)
    return string.lower(string.sub(s, 1, 1)) .. string.sub(s, 2)
end


local function with_formatting(tab)
    local init = without_singletons(tab)
    local result = {}

    for _, t in ipairs(init) do
        if type(t) == "table" then
            if #t > 2 and t[2] == UNDEF_CS_ERR then
                result[#result + 1] = {
                    get_line(t[1]),
                    "TeX error",
                    string.format(
                        "undefined control sequence %s", tostring(t[#t])
                    ),
                }
            elseif #t > 2 and t[1] == TEX_ERROR then
                result[#result + 1] = {
                    get_line(t[2]),
                    "TeX error",
                    lower_first_char(t[#t]),
                }
            elseif #t > 2 and t[1] == MP_ERROR then
                result[#result + 1] = {
                    get_line(t[2]),
                    "MetaPost error",
                    lower_first_char(t[#t]),
                }
            elseif #t > 2 and t[1] == LUA_ERROR then
                result[#result + 1] = {
                    get_line(t[2]),
                    "Lua error",
                    lower_first_char(t[#t]),
                }
            else
                result[#result + 1] = t
            end
        end
    end

    return result
end


local function read_text_from_stdin()
    local text = io.read("*all")
    return text
end


local function main()
    local text = read_text_from_stdin()
    if not text then
        return nil
    end

    local init = parse_log(text)
    if init then
        local result = with_formatting(init)
        if result then
            return to_dict.encode(result)
        end
    end

    return nil
end


print(main())
