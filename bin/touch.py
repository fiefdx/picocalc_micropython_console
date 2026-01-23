import uos

from lib.common import exists, path_join, abs_path

coroutine = False


def main(*args, **kwargs):
    result = "invalid parameters"
    if len(args) > 0:
        path = abs_path(args[0])
        if not exists(path):
            with open(path, "w") as fp:
                pass
            result = path
    return result


