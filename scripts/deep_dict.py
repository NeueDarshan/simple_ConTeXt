def update(dict_, new_dict):
    for k, v in new_dict.items():
        if isinstance(v, dict):
            if k not in dict_:
                dict_[k] = {}
            update(dict_[k], v)
        else:
            dict_[k] = v
    return dict_


def iter_(dict_):
    for k, v in dict_.items():
        if isinstance(v, dict):
            for key, val in iter_(v):
                yield [k] + key, val
        else:
            yield [k], v


def get(dict_, keys):
    if not keys:
        return dict_
    elif len(keys) == 1:
        return dict_[keys[0]]
    return get(dict_[keys[0]], keys[1:])


def get_safe(dict_, keys):
    if not keys:
        return dict_
    elif len(keys) == 1:
        return dict_.get(keys[0])
    dict_.setdefault(keys[0], {})
    return get_safe(dict_[keys[0]], keys[1:])


def set_(dict_, keys, value):
    if len(keys) <= 1:
        dict_[keys[0]] = value
    else:
        set_(dict_[keys[0]], keys[1:], value)


def set_safe(dict_, keys, value):
    if len(keys) <= 1:
        dict_[keys[0]] = value
    else:
        dict_.setdefault(keys[0], {})
        set_safe(dict_[keys[0]], keys[1:], value)


def in_(dict_, keys):
    if len(keys) <= 1:
        return keys[0] in dict_
    return in_(dict_[keys[0]], keys[1:])


def del_(dict_, keys):
    if len(keys) <= 1:
        del dict_[keys[0]]
    else:
        del_(dict_[keys[0]], keys[1:])


def del_safe(dict_, keys):
    if len(keys) <= 1:
        try:
            del dict_[keys[0]]
        except KeyError:
            pass
    else:
        dict_.setdefault(keys[0], {})
        del_safe(dict_[keys[0]], keys[1:])
