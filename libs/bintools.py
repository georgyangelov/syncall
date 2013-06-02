import hashlib


def decode_object(obj, encoding='utf-8', except_keys=tuple()):
    if isinstance(obj, bytes):
        return str(obj, encoding=encoding)

    elif isinstance(obj, dict):
        res = dict()

        for key, value in obj.items():
            new_key = decode_object(key, encoding, except_keys)

            if new_key in except_keys:
                res[new_key] = value
            else:
                res[new_key] = decode_object(value, encoding, except_keys)

        return res

    elif isinstance(obj, list) or isinstance(obj, tuple):
        res = []

        for value in obj:
            res.append(decode_utf_object(value, except_keys))

        if isinstance(obj, tuple):
            res = tuple(res)

        return res
    else:
        return obj


def hash_file(file_path):
    hash = hashlib.md5()

    with open(file_path, 'rb') as file:
        while True:
            data = file.read(8192)

            if not data:
                break

            hash.update(data)

    return hash.digest()
