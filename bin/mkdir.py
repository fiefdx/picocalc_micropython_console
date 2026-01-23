import uos

from lib.common import exists, path_join, mkdirs, getcwd, abs_path

coroutine = False


def main(*args, **kwargs):
    result = "already exists!"
    cwd = getcwd()
    if len(args) > 0:
        path = abs_path(args[0])
        if path.endswith("/"):
            path = path[:-1]
        if not exists(path):
            mkdirs(path)
            result = path
    return result
