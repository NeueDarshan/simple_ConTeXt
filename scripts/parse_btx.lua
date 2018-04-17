local to_json = require "table_to_json"


local P, R, S, V = lpeg.P, lpeg.R, lpeg.S, lpeg.V
local C, Ct = lpeg.C, lpeg.Ct
local match = lpeg.match


local bibtex

do
  local space = S " \t\r\n"
  local equal = P "="
  local at = P "@"
  local hash = P "#"
  local punct = S "_-:"
  local letter = R "az" + R "AZ"
  local number = R "09"
  local comma = P ","
  local quote = P '"'
  local l_brace = P "{"
  local r_brace = P "}"
  local braces = S "{}"
  local end_of_string = P(-1)

  local ident = letter * (letter + number + punct)^0
  local integer = number^1
  local spaces = space^0
  local type_ = ident
  local key = ident
  local name = ident


  local not_quotes = 1 - quote
  local not_braces = 1 - braces

  local quote_content = P { quote * C( (not_quotes + V(1))^0 ) * quote }
  local brace_content = P { l_brace * C( (not_braces + V(1))^0 ) * r_brace }
  local brace_no_content = P { l_brace * (not_braces + V(1))^0 * r_brace }

  -- We take some care to keep track of abbreviations.
  local string_name = ident
  local function indicate_string(x) return {x} end
  local concat_part =
    quote_content + C(string_name) / indicate_string
  local concat_content = Ct(
    concat_part * (spaces * hash * spaces * concat_part)^0
  )

  local content = brace_content + concat_content + C(integer)


  local entry_start =
    at * C(type_) * spaces * l_brace * spaces * C(key) * spaces * comma

  local entry_tag =
    Ct( C(name) * spaces * equal * spaces * content * (spaces * comma)^-1 )

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
    Ct(entry_start * spaces * (entry_tag * spaces)^0 * r_brace) /
    format_main_entry


  local comment = at * P "comment" * spaces * brace_no_content

  -- Let's ignore the preamble.
  local preamble = at * P "preamble" * spaces * brace_no_content


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
      at * P "string" * spaces * l_brace * spaces * (entry_tag * spaces)^0 *
      r_brace
    ) / format_string


  local entry = comment + string + preamble + main_entry

  bibtex = Ct(spaces * (entry * spaces)^0 * end_of_string)
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
    local mode = type(val)
    if mode == "string" then
      result[key] = val
    elseif mode == "table" then
      local str = ""
      for _, v in ipairs(val) do
        local m = type(v)
        if m == "string" then
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
      local type_ = type(value)
      if type_ == "string" then
        result[tag][key] = value
      elseif type_ == "table" then
        local str = ""
        for _, val in ipairs(value) do
          local mode = type(val)
          if mode == "string" then
            str = str .. val
          elseif mode == "table" then
            local v = string[val[1]]
            local m = type(v)
            if m == "string" then
              str = str .. v
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
      return to_json.encode(result)
    end
  end

  return nil
end


print(main())
