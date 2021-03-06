local to_dict = require("table_to_dict")


local P, R, S, V = lpeg.P, lpeg.R, lpeg.S, lpeg.V
local C, Ct, match = lpeg.C, lpeg.Ct, lpeg.match


local bibtex

do
    local end_of_string = P(-1)
    local space = S(" \t")
    local line = S("\r\n\f\v")
    local equal = P("=")
    local at = P("@")
    local hash = P("#")
    local punct = S("_-:")
    local letter = R("az") + R("AZ")
    local number = R("09")
    local comma = P(",")
    local quote = P('"')
    local l_brace = P("{")
    local r_brace = P("}")
    local brace = l_brace + r_brace

    local end_of_line = line + end_of_string
    local all_space = space + line
    local spaces = space^0
    local all_spaces = all_space^0
    local al_num = letter + number
    local al_num_pun = al_num + punct
    -- local identifier = al_num * al_num_pun^0
    local identifier = al_num_pun^1
    local integer = number^1
    local entry_type = identifier
    local entry_key = identifier
    local entry_name = identifier
    local function not_(x) return 1 - x end

    -- Similar to `P`, but ignores case.
    local function P_(str)
        local result = P ""
        for i = 1, #str do
            local c = str:sub(i, i)
            result = result * S(c:lower() .. c:upper())
        end
        return result
    end


    local quote_content = quote * C( not_(quote)^0 ) * quote
    local brace_content = P { l_brace * C( (V(1) + not_(brace))^0 ) * r_brace }
    local brace_no_content = P { l_brace * (V(1) + not_(brace))^0 * r_brace }

    -- We take some care to keep track of abbreviations.
    local string_name = identifier
    local function indicate_string(x) return {x} end

    local content_part =
        brace_content + quote_content + C(integer) +
        C(string_name) / indicate_string
    local content =
        Ct(content_part * (all_spaces * hash * all_spaces * content_part)^0)


    local entry_start =
        at * C(entry_type) * all_spaces * l_brace * all_spaces * C(entry_key) *
        all_spaces * comma

    local entry_tag =
        Ct(
            C(entry_name) * all_spaces * equal * all_spaces * content *
            (all_spaces * comma)^-1
        )

    local function format_main_entry(tab)
        local result = {category = tab[1], tag = tab[2]}
        local details = {}
        for i = 3, #tab do
            local k, v = tab[i][1], tab[i][2]
            details[k] = v
        end
        result.details = details
        return result
    end

    local main_entry =
        Ct(
            entry_start * all_spaces * (entry_tag * all_spaces)^0 * r_brace
        ) / format_main_entry


    -- Let's ignore the preamble.
    local preamble = at * P_("preamble") * all_spaces * brace_no_content
    local comment = at * P_("comment") * all_spaces * brace_no_content


    local function format_string(tab)
        local result = {}
        for _, val in ipairs(tab) do
            local k, v = val[1], val[2]
            result[k] = v
        end
        return {string = result}
    end

    local string =
        Ct(
            at * P_("string") * all_spaces * l_brace * all_spaces *
            (entry_tag * all_spaces)^0 * r_brace
        ) / format_string


    local entry =
        spaces * (comment + string + preamble + main_entry) * spaces *
        end_of_line
    local blank_line = spaces * line
    local comment_line = spaces * not_(at) * not_(line)^0 * end_of_line
    local ignore_line = blank_line + comment_line
    local component = entry + ignore_line

    bibtex = Ct(component^0 * all_spaces * end_of_string)
end


local function decode(text)
    return match(bibtex, text)
end


local function reformat_init(tab)
    local details = {}
    local string = {}
    for _, entry in ipairs(tab) do
        local str = entry.string
        local tag = entry.tag
        if str then
            for k, v in pairs(str) do
                string[k] = v
            end
        elseif tag then
            details[tag] = entry.details
            details[tag].category = entry.category
        end
    end
    return {details = details, string = string}
end


-- Ignore the possibility of strings that refer to one another for now.
local function reformat_string(tab)
    local result = {}
    for key, val in pairs(tab) do
        if type(val) == "string" then
            result[key] = val
        elseif type(val) == "table" then
            local str = ""
            for _, v in ipairs(val) do
                if type(v) == "string" then
                    str = str .. v
                end
            end
            result[key] = str
        end
    end
    return result
end


local function reformat(tab)
    local init = reformat_init(tab)
    local details, string = init.details, reformat_string(init.string)
    local result = {}

    for tag, entry in pairs(details) do
        result[tag] = {}
        for key, value in pairs(entry) do
            if type(value) == "string" then
                result[tag][key] = value
            elseif type(value) == "table" then
                local str = ""
                for _, val in ipairs(value) do
                    if type(val) == "string" then
                        str = str .. val
                    elseif type(val) == "table" then
                        local s = string[val[1]]
                        if type(s) == "string" then
                            str = str .. s
                        end
                    end
                end
                result[tag][key] = str
            end
        end
    end

    return result
end


local function get_file()
    local file_name = arg[1]
    if not file_name then
        return nil
    end

    local file = io.open(file_name, "r")
    if not file then
        return nil
    end
    local text = file:read("*all")
    file:close()

    return text
end


local function main()
    local text = get_file()
    if not text then
        return nil
    end

    local init = decode(text)
    if init then
        local result = reformat(init)
        if result then
            return to_dict.encode(result)
        end
    end

    return nil
end


print(main())
