local to_json = require "table_to_json"


local function get_file()
  local file_name = arg[1]
  if not file_name then
    return nil
  end

  local func = loadfile(file_name)
  if not func then
    return nil
  end

  local result = func()
  return result
end


local function main()
  local result = get_file()
  if not result then
    return nil
  end

  return to_json.encode(result)
end


print(main())
