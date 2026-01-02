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
                    frames_length = 1024 * channels * samplewidth
                    if channels == 2:
                        analyze_frames = 0
                        analyze_loop = 10
                        ts = ticks_cpu()
                        while b"ES" not in keys and analyze_loop:
                            t = ticks_cpu()
                            frames = f.readframes(1024)
                            if not frames:
                                break
                            frames_count = 1024
                            if len(frames) != frames_length:
                                frames_count = int(len(frames) / channels / samplewidth)
                            for i in range(frames_count):
                                s = i * bytes_per_frame
                                left_sample, right_sample = struct.unpack_from('<hh', frames, s)
                                left_pwm.duty_u16(0)
                                right_pwm.duty_u16(0)
                            buf = bytearray(6)
                            Resource.keyboard.readinto(buf)
                            keys = bytes(buf)
                            analyze_loop -= 1
                            analyze_frames += frames_count
                        te = ticks_cpu()
                        analyzed_interval = round((analyze_frames * (1000000 / framerate) - ticks_diff(te, ts)) / analyze_frames) + 8
                        print(analyze_frames * (1000000 / framerate), ticks_diff(te, ts))
                        print("analyzed_interval: ", analyzed_interval, (analyze_frames * (1000000 / framerate) - ticks_diff(te, ts)) / analyze_frames)
                        f.setpos(0)
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
                                left_sample, right_sample = struct.unpack_from('<hh', frames, s)
                                left_pwm.duty_u16(left_sample + 32768)
                                right_pwm.duty_u16(right_sample + 32768)
                                time.sleep_us(analyzed_interval)
                            buf = bytearray(6)
                            Resource.keyboard.readinto(buf)
                            keys = bytes(buf)
                        result = "exit"
                    elif channels == 1:
                        analyze_frames = 0
                        analyze_loop = 10
                        ts = ticks_cpu()
                        while b"ES" not in keys and analyze_loop:
                            frames = f.readframes(1024)
                            if not frames:
                                break
                            frames_count = 1024
                            if len(frames) != frames_length:
                                frames_count = int(len(frames) / channels / samplewidth)
                            for i in range(frames_count):
                                s = i * bytes_per_frame
                                left_sample, = struct.unpack_from('<h', frames, s)
                                v = left_sample + 32768
                                left_pwm.duty_u16(0)
                                right_pwm.duty_u16(0)
                            buf = bytearray(6)
                            Resource.keyboard.readinto(buf)
                            keys = bytes(buf)
                            analyze_loop -= 1
                            analyze_frames += frames_count
                        te = ticks_cpu()
                        analyzed_interval = round((analyze_frames * (1000000 / framerate) - ticks_diff(te, ts)) / analyze_frames) + 8
                        print(analyze_frames * (1000000 / framerate), ticks_diff(te, ts))
                        print("analyzed_interval: ", analyzed_interval, (analyze_frames * (1000000 / framerate) - ticks_diff(te, ts)) / analyze_frames)
                        f.setpos(0)
                        while b"ES" not in keys:
                            frames = f.readframes(1024)
                            if not frames:
                                break
                            frames_count = 1024
                            if len(frames) != frames_length:
                                frames_count = int(len(frames) / channels / samplewidth)
                            for i in range(frames_count):
                                s = i * bytes_per_frame
                                left_sample, = struct.unpack_from('<h', frames, s)
                                v = left_sample + 32768
                                left_pwm.duty_u16(v)
                                right_pwm.duty_u16(v)
                                time.sleep_us(analyzed_interval)
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
