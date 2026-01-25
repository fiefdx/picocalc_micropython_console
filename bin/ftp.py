import uos
import machine

from lib.common import exists, path_join, isfile, isdir, path_split, mkdirs, copy

coroutine = False


def main(*args, **kwargs):
    scheduler = kwargs["scheduler"]
    if exists("/main.ftp.py"):
        uos.rename("/main.py", "/main.shell.py")
        uos.rename("/main.ftp.py", "/main.py")
        machine.soft_reset()
