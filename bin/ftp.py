import uos
import time
import machine

from lib.common import exists, path_join, isfile, isdir, path_split, mkdirs, copy

coroutine = False


def main(*args, **kwargs):
    scheduler = kwargs["scheduler"]
    if exists("/main.ftp.py"):
        uos.rename("/main.py", "/main.shell.py")
        time.sleep_ms(100)
        uos.rename("/main.ftp.py", "/main.py")
        time.sleep_ms(100)
        machine.soft_reset()
