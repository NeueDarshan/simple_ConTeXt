local to_dict = require("table_to_dict")


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

    return to_dict.encode(result)
end


print(main())
