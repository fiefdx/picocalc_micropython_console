import sys
import uos
from io import StringIO
import struct
import wave
from machine import Pin, PWM
import time
from time import ticks_diff, ticks_us, ticks_cpu, sleep_us
import array

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
                    default_freq = 2000000
                    left_pwm.freq(default_freq)
                    right_pwm.freq(default_freq)
                    frame_interval = int(1000000 / framerate)
                    buf = bytearray(6)
                    Resource.keyboard.readinto(buf)
                    keys = bytes(buf)
                    # duties = {}
                    # for i in range(-32768, 1):
                    #     duties[i] = i + 32768
                    frames_length = 1024 * channels * samplewidth
                    if channels == 2:
                        while b"ES" not in keys:
                            t = ticks_cpu()
                            frames = f.readframes(1024)
                            if not frames:
                                break
#                             frames_mv = memoryview(frames)
#                             frames_array = array.array('<H', frames_mv)
#                             for i in :
#                                 s = i * bytes_per_frame
#                                 e = (i + 1) * bytes_per_frame
#                                 frame = frames[s:e]
#                                 left_sample, right_sample = struct.unpack('<hh', frame)
# #                                 left_pwm.duty_u16((left_sample ^ 0x8000) & 0xff)
# #                                 right_pwm.duty_u16((right_sample ^ 0x8000) & 0xff)
#                                 left_pwm.duty_u16(left_sample + 32768)
#                                 right_pwm.duty_u16(right_sample + 32768)
#                                 # left_pwm.duty_u16(duties[left_sample])
#                                 # right_pwm.duty_u16(duties[right_sample])
#                                 sleep_time = frame_interval - ticks_diff(ticks_cpu(), t)
#                                 if sleep_time > 0:
#                                     time.sleep_us(sleep_time)
#                                 t = ticks_cpu()
                            frames_count = 1024
                            if len(frames) != frames_length:
                                frames_count = int(len(frames) / channels / samplewidth)
                            i = 0
                            while i < frames_count:
                                s = i * bytes_per_frame
#                                 e = (i + 1) * bytes_per_frame
#                                 frame = frames[s:e]
                                left_sample, right_sample = struct.unpack_from('<hh', frames, s)
#                                 left_pwm.duty_u16((left_sample ^ 0x8000) & 0xff)
#                                 right_pwm.duty_u16((right_sample ^ 0x8000) & 0xff)
                                left_pwm.duty_u16(left_sample + 32768)
                                right_pwm.duty_u16(right_sample + 32768)
                                # left_pwm.duty_u16(duties[left_sample])
                                # right_pwm.duty_u16(duties[right_sample])
                                sleep_time = frame_interval - ticks_diff(ticks_cpu(), t)
                                if sleep_time > 0:
                                    time.sleep_us(sleep_time)
                                t = ticks_cpu()
                                i += 1
                            buf = bytearray(6)
                            Resource.keyboard.readinto(buf)
                            keys = bytes(buf)
                        result = "exit"
                    elif channels == 1:
                        while b"ES" not in keys:
                            t = ticks_cpu()
                            frames = f.readframes(1024)
                            if not frames:
                                break
                            frames_count = 1024
                            if len(frames) != frames_length:
                                frames_count = int(len(frames) / channels / samplewidth)
                            for i in range(frames_count):
                                s = i * bytes_per_frame
#                                 e = (i + 1) * bytes_per_frame
#                                 frame = frames[s:e]
                                left_sample, = struct.unpack_from('<h', frames, s)
                                v = left_sample + 32768
                                left_pwm.duty_u16(v)
                                right_pwm.duty_u16(v)
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
