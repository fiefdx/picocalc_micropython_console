import sys
import uos
from io import StringIO
import struct
import wave
from machine import Pin, PWM
import time
from time import ticks_diff, ticks_us, ticks_cpu, sleep_us

from common import exists, path_join, Resource

coroutine = False


def main(*args, **kwargs):
    result = "invalid parameters"
    try:
        if len(args) > 0:
            path = args[0]
            if exists(path) and path.lower().endswith(".wav"):
                left_pin = Pin(26)
                right_pin = Pin(27)
                left_pwm = PWM(left_pin)
                right_pwm = PWM(right_pin)
                try:
                    f = wave.open(path, 'rb')
                    print("Channels: %d, Sample width: %d, Frames: %d, Rate: %d" % (f.getnchannels(), f.getsampwidth(), f.getnframes(), f.getframerate()))
                    print("Length: %ds" % (f.getnframes() / f.getframerate()))
                    framerate = f.getframerate()
                    channels = f.getnchannels()
                    samplewidth = f.getsampwidth()
                    bytes_per_frame = samplewidth * channels
                    left_pwm.freq(100000)
                    right_pwm.freq(100000)
                    frame_interval = int(1000000 / framerate)
                    buf = bytearray(6)
                    Resource.keyboard.readinto(buf)
                    keys = bytes(buf)
                    if channels == 2:
                        t = ticks_cpu()
                        while b"ES" not in keys:
                            frames = f.readframes(1024)
                            if not frames:
                                break
                            
                            frames_count = int(len(frames) / channels / samplewidth)
                            for i in range(frames_count):
                                s = i * bytes_per_frame
                                e = (i + 1) * bytes_per_frame
                                frame = frames[s:e]
                                left = frame[0:2]
                                right = frame[2:4]
                                left_sample, = struct.unpack('<h', left)
                                right_sample, = struct.unpack('<h', right)
                                left_pwm.duty_u16(left_sample + 32768)
                                right_pwm.duty_u16(right_sample + 32768)
                                sleep_time = frame_interval - ticks_diff(ticks_cpu(), t)
                                if sleep_time > 0:
                                    time.sleep_us(sleep_time)
                                t = ticks_cpu()
                            buf = bytearray(6)
                            Resource.keyboard.readinto(buf)
                            keys = bytes(buf)
                        result = "exit"
                    elif channels == 1:
                        t = ticks_cpu()
                        while b"ES" not in keys:
                            frames = f.readframes(1024)
                            if not frames:
                                break
                            
                            frames_count = int(len(frames) / channels / samplewidth)
                            for i in range(frames_count):
                                s = i * bytes_per_frame
                                e = (i + 1) * bytes_per_frame
                                frame = frames[s:e]
                                left_sample, = struct.unpack('<h', frame)
                                left_pwm.duty_u16(left_sample + 32768)
                                right_pwm.duty_u16(left_sample + 32768)
                                sleep_time = frame_interval - ticks_diff(ticks_cpu(), t)
                                if sleep_time > 0:
                                    time.sleep_us(sleep_time)
                                t = ticks_cpu()
                            buf = bytearray(6)
                            Resource.keyboard.readinto(buf)
                            keys = bytes(buf)
                        result = "exit"
                except Exception as e:
                    print(f"Error playing file: {e}")
                finally:
                    f.close()
                    left_pwm.deinit()
                    right_pwm.deinit()
    except Exception as e:
        print(e)
        buf = StringIO()
        sys.print_exception(e, buf)
        result = buf.getvalue()
    return result
