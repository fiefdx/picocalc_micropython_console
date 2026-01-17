import os
import sys
import gc
import time
from time import ticks_ms, ticks_add, ticks_diff, sleep_ms
import uos
import framebuf
import socket
machine = None
microcontroller = None
try:
    import machine
except:
    try:
        import microcontroller
    except:
        print("no machine & microcontroller module support")
thread = None
try:
    import _thread as thread
except:
    print("no multi-threading module support")
from machine import Pin, SPI, PWM
from micropython import const

import sdcard
# import font8
# import font7
from display import ILI9488, Colors as C
from scheduler import Scheluder, Condition, Task, Message
from common import Resource
from shell import Shell
from keyboard import Keyboard
# from writer_fast import CWriter
sys.path.insert(0, "/bin")
sys.path.append("/")

if machine:
    machine.freq(250000000, 250000000)
    print("freq: %s mhz" % (machine.freq() / 1000000))
if microcontroller:
    microcontroller.cpu.frequency = 250000000
    print("freq: %s mhz" % (microcontroller.cpu.frequency / 1000000))


def monitor(task, name, scheduler = None, display_id = None):
    yield Condition.get().load(
            sleep = 2000
        )
    while True:
        gc.collect()
        ram_free = gc.mem_free()
        ram_used = gc.mem_alloc()
        ram_total = ram_free + ram_used
#         #print(int(100 - (gc.mem_free() * 100 / (264 * 1024))), gc.mem_free())
#         monitor_msg = "CPU%s:%3d%%  RAM:%3d%%" % (scheduler.cpu, int(100 - scheduler.idle), int(100 - (scheduler.mem_free() * 100 / ram_total)))
#         print(monitor_msg)
#         #print(len(scheduler.tasks))
#         #scheduler.add_task(Task.get().load(free.main, "test", condition = Condition.get(), kwargs = {"args": [], "shell_id": scheduler.shell_id}))
#         monitor_msg = "R%6.2f%%|F%7.2fk/%d|U%7.2fk/%d" % (100.0 - (ram_free * 100 / ram_total),
#                                                           ram_free / 1024,
#                                                           ram_free,
#                                                           ram_used / 1024,
#                                                           ram_used)
#         print(monitor_msg)
#         # print(Message.remain(), Condition.remain(), Task.remain())
#         # yield Condition.get().load(sleep = 1000)
        stat = os.statvfs("/")
        size = stat[1] * stat[2]
        free = stat[0] * stat[3]
        used = size - free
#         print("Total: %6.2fK, Used: %6.2fK, Free: %6.2fK" % (size / 1024.0, used / 1024.0, free / 1024.0))
#         yield Condition.get().load(
#             sleep = 2000
#         )
        plugged_in = False
        level = 0
        if Resource.keyboard:
            b = Resource.keyboard.battery_status()
            plugged_in = b["charging"]
            level = b["level"]
        yield Condition.get().load(
            sleep = 1000,
            send_msgs = [Message.get().load(
                {"stats": (scheduler.cpu, int(100 - scheduler.idle), 100.0 - (ram_free * 100 / (ram_total)), ram_free, ram_used, size, free, used, plugged_in, level)},
                receiver = scheduler.shell_id
            )]
        )


def render_bricks(name, msg, lcd):
    offset_x = msg.content[name]["offset_x"]
    offset_y = msg.content[name]["offset_y"]
    width = msg.content[name]["width"]
    height = msg.content[name]["height"]
    brick_size = msg.content[name]["size"]
    data = msg.content[name]["data"]
    for w in range(width):
        x = w * brick_size + offset_x
        for h in range(height):
            y = h * brick_size + offset_y
            if data[h][w] == "o":
                lcd.rect(x, y, brick_size, brick_size, C.black)
                lcd.rect(x + 2, y + 2, brick_size - 4, brick_size - 4, C.black)
            elif data[h][w] == "x":
                lcd.rect(x, y, brick_size, brick_size, C.white)
                lcd.rect(x + 2, y + 2, brick_size - 4, brick_size - 4, C.white)
#     if brick_size == 6:
#         for w in range(width):
#             x = w * brick_size + offset_x
#             for h in range(height):
#                 y = h * brick_size + offset_y
#                 if data[h][w] == "o":
#                     lcd.rect(x, y, brick_size, brick_size, C.black)
#                 elif data[h][w] == "x":
#                     lcd.rect(x, y, brick_size, brick_size, C.white)
#     elif brick_size == 4:
#         for w in range(width):
#             x = w * brick_size + offset_x
#             for h in range(height):
#                 y = h * brick_size + offset_y
#                 if data[h][w] == "o":
#                     lcd.rect(x, y, brick_size, brick_size, C.black)
#                 elif data[h][w] == "x":
#                     lcd.rect(x, y, brick_size, brick_size, C.white)


def render_texts(name, msg, lcd):
    for text in msg.content[name]:
        x = text["x"]
        y = text["y"]
        c = text["c"]
        s = text["s"]
        color = text["C"] if "C" in text else 0
        if isinstance(c, int):
            lcd.clear_line(x, y, C.black, line_height = 8, width_offset = -2, x_offset = 1, y_offset = 0, length = c)
        if isinstance(s, int):
            lcd.clear_line(x, y, C.black, line_height = 8, width_offset = -2, x_offset = 1, y_offset = 0, length = s)
        else:
            lcd.text(s, x, y, color)


def render_lines(name, msg, lcd):
    for line in msg.content[name]:
        xs, ys, xe, ye, color = line
        lcd.line(xs, ys, xe, ye, color)


def render_rects(name, msg, lcd):
    for rect in msg.content[name]:
        x, y, w, h, color = rect
        lcd.rect(x, y, w, h, color)


def render(category, msg, lcd, refresh):
    name, render_type = category
    renders = {
        "bricks": (render_bricks, [name, msg, lcd]),
        "texts": (render_texts, [name, msg, lcd]),
        "lines": (render_lines, [name, msg, lcd]),
        "rects": (render_rects, [name, msg, lcd]),
    }
    if render_type in renders:
        renders[render_type][0](*renders[render_type][1])
        refresh = True
    return refresh

        
def display(task, name, scheduler = None):
    try:
        cs = Pin(13, Pin.OUT, value = 1)
        dc = Pin(14, Pin.OUT)
        rst = Pin(15, Pin.OUT)
        sck = Pin(10)
        mosi = Pin(11)
        spi = SPI(1, baudrate = 62_500_000, sck = sck, mosi = mosi)
        lcd = ILI9488(spi, cs, dc, rst)
        Resource.display = lcd
        lcd.fill(lcd.rgb(0, 0, 0))
        lcd.show()
        
#         wri = CWriter(lcd, font8)
#         wri.wrap = False
#         wri.setcolor(fgcolor = lcd.rgb(1, 1, 1), bgcolor = lcd.rgb(0, 0, 0))
        width, height = 8, 8 # 6, 8
        x_offset, y_offset = 1, 1
        line_height = 11
        
        frame_previous = None
        clear_line = const("                                                     ")
        cursor_previous = None
        while True:
            yield Condition.get().load(sleep = 0, wait_msg = True)
            msg = task.get_message()
            while True:
                try:
                    refresh = False
                    if "clear" in msg.content:
                        lcd.fill(lcd.rgb(0, 0, 0))
                    if "frame" in msg.content:                   
                        frame = msg.content["frame"]
#                         lines = [False for i in range(len(frame))]
#                         if frame_previous:
#                             if len(frame) < len(frame_previous):
#                                 lines = [False for i in range(len(frame_previous))]
#                             for n, l in enumerate(frame):
#                                 if n < len(frame_previous):
#                                     if l != frame_previous[n]:
#                                         lines[n] = l
#                                         if l == "":
#                                             lines[n] = clear_line
#                                 else:
#                                     lines[n] = l
#                             if len(frame_previous) > len(frame):
#                                 for n in range(len(frame), len(frame_previous)):
#                                     lines[n] = clear_line
#                         else:
#                             lines = frame
                        lines = frame
                        x = 0
                        for n, l in enumerate(lines):
#                             if l:
                            if l == "":
#                                     lcd.text(clear_line, x, n * line_height, lcd.rgb(1, 1, 1))
                                lcd.rect(0 , n * line_height + y_offset, 320, (n + 1) * line_height, lcd.rgb(0, 0, 0), True)
#                                     wri.set_textpos(lcd, n, 0)
#                                     wri.printstring(clear_line)
                            else:
                                lcd.rect(0 , n * line_height + y_offset, 320, (n + 1) * line_height, lcd.rgb(0, 0, 0), True)
                                lcd.text(l, x, n * line_height + y_offset, lcd.rgb(1, 1, 1))
#                                     wri.set_textpos(lcd, n, 0)
#                                     wri.printstring(clear_line)
#                                     wri.set_textpos(lcd, n, 0)
#                                     wri.printstring(l)
#                                 t = ticks_ms()
#                                 if l == clear_line:
#                                     CWriter.set_textpos(lcd, n * line_height + 1, x)
# #                                     wri.printstring(clear_line)
#                                     wri.clear_line(53)
#                                 else:
#                                     CWriter.set_textpos(lcd, n * line_height + 1, x)
# #                                     wri.printstring(clear_line)
#                                     wri.clear_line(53)
# #                                     CWriter.set_textpos(lcd, n * 8 + 1, x)
#                                     wri.printstring(l)
# #                                 tt = ticks_ms()
# #                                 print("update line: ", tt - t)
                        refresh = True
                        frame_previous = frame
                    if "cursor" in msg.content:
                        refresh = True
                        x, y, c = msg.content["cursor"]
                        if c == "hide":
                            lcd.line(x * width + 1, (y + 1) * line_height - 3 + y_offset, (x + 1) * width - 1, (y + 1) * line_height - 3 + y_offset, C.black)
                        else:
                            if cursor_previous:
                                xp, yp, cp = cursor_previous
                                lcd.line(xp * width + 1, (yp + 1) * line_height - 3 + y_offset, (xp + 1) * width - 1, (yp + 1) * line_height - 3 + y_offset, C.black)
                            lcd.line(x * width + 1, (y + 1) * line_height - 3 + y_offset, (x + 1) * width - 1, (y + 1) * line_height - 3 + y_offset, C.green if c else C.black)
                            cursor_previous = [x, y, c]
#                         if c == "hide":
#                             lcd.line(x * width - 1, y * line_height, x * width - 1, y * line_height + line_height - 3, lcd.rgb(0, 0, 0))
#                         else:
#                             if cursor_previous:
#                                 xp, yp, cp = cursor_previous
#                                 lcd.line(xp * width - 1, yp * line_height, xp * width - 1, yp * line_height + line_height - 3, lcd.rgb(0, 0, 0))
#                             lcd.line(x * width - 1, y * line_height, x * width - 1, y * line_height + line_height - 3, lcd.rgb(1, 1, 1) if c else lcd.rgb(0, 0, 0))
#                             cursor_previous = [x, y, c]
                    if "render" in msg.content:
                        for category in msg.content["render"]:
                            refresh = render(category, msg, lcd, refresh)
                    if refresh:
                        lcd.show()
                    msg.release()
                    break
                except Exception as e:
                    msg.release()
                    sys.print_exception(e)
    except Exception as e:
        sys.print_exception(e)
        
        
def storage(task, name, scheduler = None):
    spi = SPI(0, baudrate=13200000, sck=Pin(18), mosi=Pin(19), miso=Pin(16))
    sd = None
    vfs = None
    sd_cs = Pin(17)
    try:
        sd = sdcard.SDCard(spi, Pin(17), baudrate=13200000)
        vfs = uos.VfsFat(sd)
        uos.mount(vfs, "/sd")
#         print(uos.listdir("/sd"))
    except Exception as e:
        print(e)
    while True:
        yield Condition.get().load(sleep = 0, wait_msg = True)
        msg = task.get_message()
        try:
            if "cmd" in msg.content:
                cmd = msg.content["cmd"]
                args = cmd.split(" ")
                module = args[0].split(".")[0]
                #if "/sd/usr" not in sys.path:
                #    sys.path.insert(0, "/sd/usr")
                if module not in sys.modules:
                    import_str = "import %s; sys.modules['%s'] = %s" % (module, module, module)
                    exec(import_str)
                if module in ("mount", "umount"):
                    output, sd, vfs = sys.modules["%s" % module].main(*args[1:], shell_id = scheduler.shell_id, sd = sd, vfs = vfs, spi = spi, sd_cs = sd_cs)
                else:
                    output = sys.modules["%s" % module].main(*args[1:], shell_id = scheduler.shell_id, scheduler = scheduler)
                exec("del %s" % module)
                del sys.modules["%s" % module].main
                del sys.modules["%s" % module]
                gc.collect()
                yield Condition.get().load(sleep = 0, send_msgs = [
                    Message.get().load({"output": output}, receiver = scheduler.shell_id)
                ])
        except Exception as e:
            yield Condition.get().load(sleep = 0, send_msgs = [
                Message.get().load({"output": str(e)}, receiver = scheduler.shell_id)
            ])
        msg.release()
        
        
def cursor(task, name, interval = 500, scheduler = None, display_id = None, storage_id = None):
    yield Condition.get().load(sleep = 1500)
    flash = 0
    enabled = True
    while True:
        msg = task.get_message()
        if msg:
            if msg.content["enabled"]:
                enabled = True
            else:
                enabled = False
        if enabled:
            scheduler.shell.set_cursor_color(flash)
            if flash == 0:
                flash = 1
            else:
                flash = 0
            if scheduler.shell.enable_cursor:
                yield Condition.get().load(sleep = interval, send_msgs = [Message.get().load({"cursor": scheduler.shell.get_cursor_position()}, receiver = display_id)])
            else:
                x, y, _ = scheduler.shell.get_cursor_position()
                yield Condition.get().load(sleep = interval, send_msgs = [Message.get().load({"cursor": (x, y, "hide")}, receiver = display_id)])
        else:
            yield Condition.get().load(sleep = interval)
        if msg:
            msg.release()
        
        
def shell(task, name, shell_id = 0, scheduler = None, display_id = None, storage_id = None):
    yield Condition.get().load(sleep = 1000)
    width, height = 39, 28 # 52, 29 for 6x8 font
    s = Shell(display_size = (width, height), cache_size = (-1, 200), history_length = 100, scheduler = scheduler, storage_id = storage_id, display_id = display_id)
    s.write_line("           Welcome to TinyShell")
    s.write_char("\n")
#     s.write_line("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890`-=~!@#$%^&*()_+[]\\{}|;':\",./<>?")
#     s.write_char("\n")
    yield Condition.get().load(sleep = 0, send_msgs = [Message.get().load(s.get_display_frame(), receiver = display_id)])
#     cursor_id = scheduler.add_task(Task.get().load(cursor, "cursor", kwargs = {"interval": 500, "s": s, "display_id": display_id, "storage_id": storage_id}))
#     scheduler.shell = s
    if hasattr(scheduler, "shells"):
        scheduler.shells[shell_id] = (task.id, s)
    else:
        scheduler.shells = {shell_id: (task.id, s)}
    scheduler.shell = scheduler.shells[0][1]
    scheduler.current_shell_id = scheduler.shells[0][0]
#     s.cursor_id = cursor_id
    while True:
        yield Condition.get().load(sleep = 0, wait_msg = True)
        msg = task.get_message()
        if "clear" in msg.content:
            if not scheduler.shell.disable_output:
                yield Condition.get().load(sleep = 0, send_msgs = [
                    Message.get().load({"clear": True}, receiver = display_id)
                ])
                yield Condition.get().load(sleep = 0, send_msgs = [
                    Message.get().load(scheduler.shell.get_display_frame(), receiver = display_id)
                ])
        if "char" in msg.content:
            c = msg.content["char"]
            scheduler.shell.input_char(c)
            if not scheduler.shell.disable_output:
                yield Condition.get().load(sleep = 0, send_msgs = [
                    Message.get().load(scheduler.shell.get_display_frame(), receiver = display_id)
                ])
        elif "output" in msg.content:
            output = msg.content["output"]
            scheduler.shell.write_lines(output, end = True)
            if not scheduler.shell.disable_output:
                yield Condition.get().load(sleep = 0, send_msgs = [
                    Message.get().load(scheduler.shell.get_display_frame(), receiver = display_id)
                ])
        elif "output_part" in msg.content:
            output = msg.content["output_part"]
            scheduler.shell.write_lines(output, end = False)
            if not scheduler.shell.disable_output:
                yield Condition.get().load(sleep = 0, send_msgs = [
                    Message.get().load(scheduler.shell.get_display_frame(), receiver = display_id)
                ])
        elif "output_char" in msg.content:
            c = msg.content["output_char"]
            scheduler.shell.write_char(c)
            if not scheduler.shell.disable_output:
                yield Condition.get().load(sleep = 0, send_msgs = [
                    Message.get().load(scheduler.shell.get_display_frame(), receiver = display_id)
                ])
        elif "frame" in msg.content:
            yield Condition.get().load(sleep = 0, send_msgs = [
                Message.get().load(msg.content, receiver = display_id)
            ])
        elif "stats" in msg.content:
            scheduler.shell.update_stats(msg.content["stats"])
            if not scheduler.shell.disable_output:
                yield Condition.get().load(sleep = 0, send_msgs = [
                    Message.get().load(scheduler.shell.get_display_frame(), receiver = display_id)
                ])
        msg.release()
        
        
def keyboard_input(task, name, scheduler = None, interval = 50, display_id = None):
    k = Keyboard()
    key_map_ignore = {
#         b'\x81': "F1",
#         b'\x82': "F2",
#         b'\x83': "F3",
#         b'\x84': "F4",
#         b'\x85': "F5",
        b'\x86': "F6",
        b'\x87': "F7",
        b'\x88': "F8",
        b'\x89': "F9",
        b'\x90': "F10",
        b'\xc1': "CAP",
        b'\x1b[F': "END",
        b'\x1b[H': "HOME",
        b'\xd0': "BREAK",
#         b'\x1b[3~': "DEL",
        b'\x1b\xd1': "INS",
    }
    key_map = {
        b'\x13': "SAVE",
        b'\x01': "Ctrl-A",
        b'\x02': "Ctrl-B",
        b'\x03': "Ctrl-C",
        b'\x07': "Ctrl-G",
        b'\x11': "Ctrl-Q",
        b'\x14': "Ctrl-T",
        b'\x16': "Ctrl-V",
        b'\x18': "Ctrl-X",
        b'\x1a': "Ctrl-Z",
        b'\x0f': "Ctrl-/",
        b'\x83': "BY",
        b'\x85': "BA",
        b'\x84': "BX",
        b'\x1b[3~': "BB",
        b'\x81': "F1",
        b'\x82': "F2",
    }
    Resource.keyboard = k
    yield Condition.get().load(sleep = 1000)
    key_sound = const(2000)
    keys = bytearray(30)
    while True:
        try:
            if k.disable:
                yield Condition.get().load(sleep = 1000)
            else:
                yield Condition.get().load(sleep = interval)
                n = k.readinto(keys)
                if n is not None:
                    # print("size: ", n)
                    # print("keys: ", keys[:n])
                    if n == 1 or n == 2 or n == 3 or n == 4:
                        code = bytes(keys[:n])
                        # print("code: ", code, code in key_map)
                        if code not in key_map_ignore:
                            try:
    #                             key = code.decode()
    #                             print("key1: ", key)
    #                             if n == 2 and code.find(b'\x1b') == 0:
    #                                 if key[1] == "S":
    #                                     key = "SAVE"
    #                                 elif key[1] == "C":
    #                                     key = "Ctrl-C"
    #                                 elif key[1] == "X":
    #                                     key = "Ctrl-X"
    #                                 elif key[1] == "V":
    #                                     key = "Ctrl-V"
                                if code in key_map:
                                    key = key_map[code]
                                else:
                                    key = code.decode()
                                # print("key2: ", key)
                                if key == 'F1': # F1
                                    yield Condition.get().load(sleep = 0, send_msgs = [Message.get().load({"freq": key_sound, "volume": 5000, "length": 5}, receiver = scheduler.sound_id)])
                                    scheduler.shell = scheduler.shells[0][1]
                                    scheduler.current_shell_id = scheduler.shells[0][0]
                                elif key == 'F2': # F2
                                    yield Condition.get().load(sleep = 0, send_msgs = [Message.get().load({"freq": key_sound, "volume": 5000, "length": 5}, receiver = scheduler.sound_id)])
                                    scheduler.shell = scheduler.shells[1][1]
                                    scheduler.current_shell_id = scheduler.shells[1][0]
                                else:
                                    if scheduler.shell and scheduler.shell.session_task_id and scheduler.exists_task(scheduler.shell.session_task_id):
                                        yield Condition.get().load(sleep = 0, send_msgs = [Message.get().load({"freq": key_sound, "volume": 5000, "length": 5}, receiver = scheduler.sound_id)])
                                        yield Condition.get().load(sleep = 0, send_msgs = [Message.get().load({"msg": key, "keys": [key]}, receiver = scheduler.shell.session_task_id)])
                                    else:
                                        yield Condition.get().load(sleep = 0, send_msgs = [Message.get().load({"freq": key_sound, "volume": 5000, "length": 5}, receiver = scheduler.sound_id)])
                                        yield Condition.get().load(sleep = 0, send_msgs = [Message.get().load({"char": key}, receiver = scheduler.current_shell_id)])
                            except:
                                pass
                                # print("Except: ", code)
        except Exception as e:
            print(e)
#         yield Condition.get().load(sleep = interval)
        
        
def sound_output(task, name, scheduler = None):
    while True:
        try:
            yield Condition.get().load(sleep = 0, wait_msg = True)
            msg = task.get_message()
            tone_freq = msg.content["freq"]
            tone_length = msg.content["length"]
            tone_volume = msg.content["volume"]
            left_pwm = PWM(Pin(26))
            right_pwm = PWM(Pin(27))
            if tone_freq >= 20:
                left_pwm.freq(tone_freq)
                right_pwm.freq(tone_freq)
                left_pwm.duty_u16(tone_volume)
                right_pwm.duty_u16(tone_volume)
            if tone_length < 10:
                sleep_ms(tone_length)
            else:
                yield Condition.get().load(sleep = tone_length)
            left_pwm.duty_u16(0)
            right_pwm.duty_u16(0)
            left_pwm.deinit()
            right_pwm.deinit()
            msg.release()
        except Exception as e:
            print(e)


if __name__ == "__main__":
    try:
        led = machine.Pin("LED", machine.Pin.OUT)
        Message.init_pool(25)
        Condition.init_pool(15)
        Task.init_pool(15)
        s = Scheluder(cpu = 0)
        display_id = s.add_task(Task.get().load(display, "display", condition = Condition.get(), kwargs = {"scheduler": s}))
        monitor_id = s.add_task(Task.get().load(monitor, "monitor", condition = Condition.get(), kwargs = {"scheduler": s, "display_id": display_id}))
        storage_id = s.add_task(Task.get().load(storage, "storage", condition = Condition.get(), kwargs = {"scheduler": s}))
        sound_id = s.add_task(Task.get().load(sound_output, "sound_output", condition = Condition.get(), kwargs = {"scheduler": s}))
        s.sound_id = sound_id
        shell_id_0 = s.add_task(Task.get().load(shell, "shell:0", condition = Condition.get(), kwargs = {"shell_id": 0, "scheduler": s, "display_id": display_id, "storage_id": storage_id}))
        s.shell_id = shell_id_0
        shell_id_1 = s.add_task(Task.get().load(shell, "shell:1", condition = Condition.get(), kwargs = {"shell_id": 1, "scheduler": s, "display_id": display_id, "storage_id": storage_id}))
#         s.shell_id = shell_id_0
#         s.set_log_to(shell_id)
        cursor_id = s.add_task(Task.get().load(cursor, "cursor", condition = Condition.get(), kwargs = {"interval": 500, "scheduler": s, "display_id": display_id, "storage_id": storage_id}))
        s.cursor_id = cursor_id
        keyboard_id = s.add_task(Task.get().load(keyboard_input, "keyboard_input", condition = Condition.get(), kwargs = {"scheduler": s, "interval": 50, "display_id": display_id}))
        led.on()
        # led.off()
        s.run()
    except Exception as e:
        import sys
        print("main exit: %s" % sys.print_exception(e))
    print("core0 exit")
