import os
import uos
import time
from machine import RTC
from micropython import const
platform = "circuitpython"
supervisor = None
try:
    import supervisor
except:
    platform = "micropython"
    print("micropython, no supervisor module exists, use time.ticks_ms instead")

from .ntp import get_ntp_time

_TICKS_PERIOD = const(1<<29)
_TICKS_MAX = const(_TICKS_PERIOD-1)
_TICKS_HALFPERIOD = const(_TICKS_PERIOD//2)
_PATH = "/"


def ticks_ms():
    if supervisor:
        return supervisor.ticks_ms()
    else:
        return time.ticks_ms()


def sleep_ms(t):
    time.sleep(t / 1000.0)


def ticks_add(ticks, delta):
    # "Add a delta to a base number of ticks, performing wraparound at 2**29ms."
    return (ticks + delta) % _TICKS_PERIOD


def ticks_diff(ticks1, ticks2):
    # "Compute the signed difference between two ticks values, assuming that they are within 2**28 ticks"
    diff = (ticks1 - ticks2) & _TICKS_MAX
    diff = ((diff + _TICKS_HALFPERIOD) & _TICKS_MAX) - _TICKS_HALFPERIOD
    return diff


def ticks_less(ticks1, ticks2):
    # "Return true iff ticks1 is less than ticks2, assuming that they are within 2**28 ticks"
    return ticks_diff(ticks1, ticks2) < 0


def getcwd():
    return _PATH


def chdir(p):
    global _PATH
    _PATH = p


def exists(path):
    r = False
    try:
        if uos.stat(path):
            r = True
    except OSError:
        pass
    return r


def abs_path(path):
    if path.startswith("/"):
        return path
    if path.startswith("./"):
        path = path[2:]
    cwd = _PATH
    if cwd == "/":
        return "/" + path
    return cwd + "/" + path


def path_join(*args):
    path = args[0]
    for p in args[1:]:
        if path.endswith("/"):
            path = path[:-1]
        p = p.strip("/")
        if p.startswith(".."):
            path = "/".join(path.split("/")[:-1])
            if p[2:].startswith("/"):
                path += p[2:]
            else:
                path += "/" + p[2:]
        elif p.startswith("./"):
            path += p[1:]
        else:
            path += "/" + p
    if args[-1].endswith("/"):
        if not path.endswith("/"):
            path += "/"
    return path


def isfile(path):
    return uos.stat(path)[0] == 32768


def isdir(path):
    return uos.stat(path)[0] == 16384


def path_split(path):
    parts = path.split("/")
    #if path.startswith("/"):
    #    parts[0] = "/"
    dir_path, name = "/".join(parts[:-1]), parts[-1]
    if dir_path == "":
        dir_path = "/"
    return dir_path, name


def mkdirs(path):
    if len(path) > 1 and path.endswith("/"):
        path = path[:-1]
    root, _ = path_split(path)
    if not exists(root):
        mkdirs(root)
    if not exists(path):
        uos.mkdir(path)


def ram_size(size):
    if size > 1024 * 1024:
        return "%6.2fM" % (size / 1024.0 / 1024.0, )
    elif size > 1024:
        return "%6.2fK" % (size / 1024.0, )
    else:
        return "%6.2fB" % size


def get_size(size):
    if size > 1024 * 1024:
        return "%7.2fM" % (size / 1024.0 / 1024.0, )
    elif size > 1024:
        return "%7.2fK" % (size / 1024.0, )
    else:
        return "%7.2fB" % size


def copyfile(source, target):
    yield source
    with open(source, "rb") as s:
        with open(target, "wb") as t:
            buf_size = 2048
            buf = s.read(buf_size)
            while buf:
                t.write(buf)
                buf = s.read(buf_size)


def copydir(source, target):
    yield source
    if not exists(target):
        mkdirs(target)
        for f in uos.ilistdir(source):
            f = f[0]
            #print(path_join(source, f))
            s_path = path_join(source, f)
            t_path = path_join(target, f)
            if isfile(s_path):
                for output in copyfile(s_path, t_path):
                    yield output
            else:
                for output in copydir(s_path, t_path):
                    yield output


def copy(source, target):
    n = 1
    if exists(source):
        if not exists(target):
            if isfile(source):
                for output in copyfile(source, target):
                    yield "%s: %s" % (n, output)
                    n += 1
            else:
                for output in copydir(source, target):
                    yield "%s: %s" % (n, output)
                    n += 1
        else:
            yield "%s already exists!" % target
    else:
        yield "%s not exists!" % source
    
    
def rmtree(target):
    if exists(target):
        if isfile(target):
            uos.remove(target)
            yield target
            #uos.unlink(target)
        else:
            for f in uos.ilistdir(target):
                p = path_join(target, f[0])
                for output in rmtree(p):
                    yield output
            uos.rmdir(target)
            yield target


def sha1(data, is_file=False):
    """Generate SHA1 hash of a string or file"""
    if not data:
        return ""
    
    import uhashlib
    import ubinascii
    h = uhashlib.sha1()
    if is_file:
        with open(data, 'rb') as f:
            while True:
                chunk = f.read(512)
                if not chunk:
                    break
                h.update(chunk)
    else:
        h.update(data.encode())
    return ubinascii.hexlify(h.digest()).decode()

            
class Resource(object):
    display = None
    keyboard = None
    

class ClipBoard(object):
    path = "/.cache/clipboard.cache"

    @classmethod
    def set(cls, content):
        with open(cls.path, "w") as fp:
            fp.write(content)

    @classmethod
    def get(cls):
        with open(cls.path, "r") as fp:
            return fp.read()

    @classmethod
    def get_line(cls):
        with open(cls.path, "r") as fp:
            return fp.readline().strip()

    @classmethod
    def iter_lines(cls):
        with open(cls.path, "r") as fp:
            line = fp.readline()
            while line:
                yield line
                line = fp.readline()

    @classmethod
    def get_file(cls):
        return open(cls.path, "w")


class Time(object):
    days  = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
    rtc = None
    machine_rtc = RTC()
    start_at = 0
    
    @classmethod
    def now(cls):
        now = cls.machine_rtc.datetime()
        if cls.rtc:
            now = cls.rtc.datetime()
        return "%04d-%02d-%02d %02d:%02d:%02d %s" % (now[0], now[1], now[2], now[4], now[5], now[6], cls.days[now[3]])
    
    @classmethod
    def sync(cls):
        try:
            n = get_ntp_time()
            cls.machine_rtc.datetime((n[0], n[1], n[2], n[6], n[3], n[4], n[5], n[7]))
            if cls.rtc:
                cls.rtc.datetime((n[0], n[1], n[2], n[6], n[3], n[4], n[5], n[7]))
        except:
            return False
        return True

    @classmethod
    def sync_machine_rtc(cls):
        try:            
            if cls.rtc:
                n = cls.rtc.datetime()
                cls.machine_rtc.datetime((n[0], n[1], n[2], n[6], n[3], n[4], n[5], n[7]))
        except:
            return False
        return True
