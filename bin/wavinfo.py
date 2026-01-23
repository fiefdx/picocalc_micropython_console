from lib import wave
from lib.common import abs_path

coroutine = False


def main(*args, **kwargs):
    result = "path invalid"
    if len(args) > 0:
        path = abs_path(args[0])
        f = wave.open(path, 'r')
        result = "Channels: %d\nSample width: %d\nFrames: %d\nFramerate: %d" % (
        	f.getnchannels(), f.getsampwidth(), f.getnframes(), f.getframerate()
        )
        f.close()
    return result
