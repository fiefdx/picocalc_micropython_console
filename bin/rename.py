import uos

from lib.common import exists, path_join, isfile, isdir, path_split, mkdirs, copy, abs_path

coroutine = False


def main(*args, **kwargs):
    result = "invalid parameters"
    if len(args) == 2:
        t_path = abs_path(args[0])
        new_name = args[1]
        new_path = path_join(path_split(t_path)[0], new_name)
        uos.rename(t_path, new_path)
        result = new_name
    return result
