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
