import uos

from lib.common import exists, path_join, chdir, abs_path

coroutine = False


def main(*args, **kwargs):
    result = "path invalid"
    path = "/"
    if len(args) > 0:
        path = args[0]
    apath = abs_path(path)
    if exists(apath) and uos.stat(apath)[0] == 16384:
        chdir(apath)
        result = path
    return result
