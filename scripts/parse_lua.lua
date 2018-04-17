local function get_file()
  local file_name = arg[1]
  if file_name == nil then
    return nil
  end

  local func = loadfile(file_name)
  if func == nil then
    return nil
  end

  local result = func()
  return result
end


-- Watch out for mutual recursion.
local encode = nil


local function is_indexed_table(tab)
  for k in pairs(tab) do
    if type(k) == "string" then
      return false
    end
  end
  return true
end


local function encode_indexed_tab(tab)
  local result = "["
  for i, v in ipairs(tab) do
    if i > 1 then
      result = result .. ","
    end
    result = result .. encode(v)
  end
  result = result .. "]"
  return result
end


local function encode_hashed_tab(tab)
  local result = "{"
  local first = true
  for k, v in pairs(tab) do
    if first then
      first = false
    else
      result = result .. ","
    end
    result = result .. string.format('%s:%s', encode(k), encode(v))
  end
  result = result .. "}"
  return result
end


local function encode_string(text)
  return string.format('"%s"', string.gsub(text, '"', '\\"'))
end


local function encode_number(num)
  return tostring(num)
end


-- Now we give the previouly declared local a proper definition.
function encode(data)
  local mode = type(data)
  if mode == "string" then
    return encode_string(data)
  elseif mode == "number" then
    return encode_number(data)
  elseif mode == "table" then
    if is_indexed_table(data) then
      return encode_indexed_tab(data)
    else
      return encode_hashed_tab(data)
    end
  else
    return nil
  end
end


local function main()
  local result = get_file()
  if type(result) ~= "table" then
    return nil
  end

  return encode(result)
end


print(main())
