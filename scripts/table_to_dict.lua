-- Watch out for mutual recursion.
local encode


local function is_indexed_table(tab)
    for k in pairs(tab) do
        if type(k) ~= "number" then
            return false
        end
    end
    return true
end


local function encode_indexed_tab(tab)
    local result = "["
    for i, v in ipairs(tab) do
        if i > 1 then
            result = result .. ", "
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
            result = result .. ", "
        end
        result = result .. string.format("%s: %s", encode(k), encode(v))
    end
    result = result .. "}"
    return result
end


local function encode_string(text)
    return string.format(
        '"""%s"""', string.gsub(string.gsub(text, "\\", "\\\\"), '"', '\\"')
    )
end


local function encode_number(num)
    return num
end


-- Now we give the previouly declared local a proper definition.
function encode(data)
    if type(data) == "string" then
        return encode_string(data)
    elseif type(data) == "number" then
        return encode_number(data)
    elseif type(data) == "table" then
        if is_indexed_table(data) then
            return encode_indexed_tab(data)
        else
            return encode_hashed_tab(data)
        end
    else
        return nil
    end
end


return {encode = encode}
