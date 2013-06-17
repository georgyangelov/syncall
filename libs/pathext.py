import os.path


def split_iter(path):
    "Generator splitting a path"
    dirname, basename = os.path.split(path)
    if path == dirname:
        # stop recursivity
        yield path
    elif dirname:
        # continue recursivity
        for i in split_iter(dirname):
            yield i
    if basename:
        # return tail
        yield basename


def split(path):
    """Return the folder list of the given path

    >>> split(os.path.join('a', 'b'))
    ('a', 'b')
    """
    return tuple(split_iter(path))


def join(iterable):
    """Join iterable's items as a path string

    >>> join(('a', 'b')) == os.path.join('a', 'b')
    True
    """
    items = tuple(iterable)
    if not items:
        return ''

    return os.path.join(*items)


def common_prefix(path1, path2):
    component1 = split(path1)
    component2 = split(path2)
    common = []

    for i in range(min(len(component1), len(component2))):
        if component1[i] == component2[i]:
            common.append(component1[i])
        else:
            break

    return join(common)


def longest_prefix(target_path, paths):
    longest = ''

    for path in paths:
        common = common_prefix(target_path, path)

        if len(common) > len(longest):
            longest = common

    return longest


def normalize(path):
    return os.path.normcase(os.path.normpath(path)).replace('\\', '/')


def str_compare(path1, path2):
    norm_path1 = normalize(path1)
    norm_path2 = normalize(path2)

    return norm_path1 == norm_path2


def is_direct_child(path, subpath):
    path_split = split(normalize(path))
    subpath_split = split(normalize(subpath))

    if len(path_split) != len(subpath_split) - 1:
        return False

    for i in range(len(path_split)):
        if path_split[i] != subpath_split[i]:
            return False

    return True
