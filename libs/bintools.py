def decode_object(obj, encoding='utf-8'):
    if isinstance(obj, bytes):
        return str(obj, encoding=encoding)

    elif isinstance(obj, dict):
        res = dict()

        for key, value in obj.items():
            res[decode_object(key, encoding)] = decode_object(value, encoding)

        return res

    elif isinstance(obj, list) or isinstance(obj, tuple):
        res = []

        for value in obj:
            res.append(decode_utf_object(value))

        if isinstance(obj, tuple):
            res = tuple(res)

        return res
    else:
        return obj
