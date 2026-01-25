import os
import gc
import sys
from io import StringIO
import time
from machine import SPI, soft_reset

import lib
from lib.wifi import WIFI
from lib import sdcard
from lib.display import ILI9488, Colors as C
from lib.keyboard import Keyboard
from lib import uftpd
from lib.common import exists
# import settings_pico2 as settings
import settings_esp32s2 as settings


def init_lcd():
    spi = SPI(settings.display_spi, baudrate = settings.display_baudrate, sck = settings.display_sck, mosi = settings.display_mosi)
    lcd = ILI9488(spi, settings.display_cs, settings.display_dc, settings.display_rst)
    lcd.fill(C.black)
    lcd.show()
    return lcd


def init_sd():
    spi = SPI(settings.sd_spi, baudrate = settings.sd_baudrate, sck = settings.sd_sck, mosi = settings.sd_mosi, miso = settings.sd_miso)
    sd = None
    vfs = None
    try:
        sd = sdcard.SDCard(spi, settings.sd_cs, baudrate = settings.sd_baudrate)
        vfs = os.VfsFat(sd)
        os.mount(vfs, "/sd")
#         print(uos.listdir("/sd"))
    except Exception as e:
        buf = StringIO()
        sys.print_exception(e, buf)
        reason = buf.getvalue()
        print(reason)
        del buf


def start(d):
    r = uftpd.start(splash = False)
    d[-1][2] = r[22:]
    status = "start"
    print("start")


def stop(d):
    r = uftpd.stop()
    d[-1][2] = r
    status = "stop"
    print("stop")
    

def connect(d):
    ssid = d[0][2]
    password = d[1][2]
    WIFI.connect(ssid, password)
    d[2][2] = "connecting ..."
    print("connect", ssid)

    
def show(data, lcd, x_offset = 0, y_offset = 0, line_height = 12, color = None, cursor_pos = 0, cursor_pos_previous = 0):
    if color is None:
        color = C.white
    for n, item in enumerate(data):
        lcd.text(item[0], x_offset, n * line_height + y_offset, color) # label
        if item[1] == "input" or item[1] == "text" or item[1] == "button":
            lcd.rect(x_offset + 72, n * line_height + y_offset, 8 * 26, 8, C.black, True)
            lcd.text(item[2], x_offset + 72, n * line_height + y_offset, color)
        elif item[1] == "input_hide":
            lcd.rect(x_offset + 72, n * line_height + y_offset, 8 * 26, 8, C.black, True)
            lcd.text("*" * len(item[2]), x_offset + 72, n * line_height + y_offset, color)
        if n == cursor_pos:
            if item[1].startswith("input"):
                lcd.rect(x_offset + 72, n * line_height + y_offset + 8, 8 * 26, 2, C.black, True)
                lcd.rect(x_offset + 72 + item[3] * 8, n * line_height + y_offset + 8, 8, 2, C.green, True)
        else:
            if item[1].startswith("input"):
                lcd.rect(x_offset + 72, n * line_height + y_offset + 8, 8 * 26, 2, C.black, True)
    x_cursor = x_offset - 2
    y_cursor = cursor_pos_previous * line_height + y_offset - ((line_height - 8) // 2)
    lcd.rect(x_cursor , y_cursor, 320 - 2 * x_cursor, line_height, C.black, False)
    y_cursor = cursor_pos * line_height + y_offset - ((line_height - 8) // 2)
    lcd.rect(x_cursor , y_cursor, 320 - 2 * x_cursor, line_height, C.cyan, False)
    lcd.show()


if __name__ == "__main__":
    all_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ`1234567890-=[]\\;',./~!@#$%^&*()_+{}|:\"<>? "
    lcd = init_lcd()
    init_sd()
    k = Keyboard(settings.keyboard_scl, settings.keyboard_sda, i2c = settings.keyboard_i2c, freq = settings.keyboard_baudrate)
    keys = bytearray(30)
    running = True
    
    def stop_running(d):
        global running
        running = False
        d[-1][2] = "exit ..."
    
    cursor_pos = 0
    cursor_pos_previous = 0
    x_offset = 20
    y_offset = 50
    line_height = 20
    refresh = False
    data = [
        ["    SSID", "input", "", 0],
        ["PASSWORD", "input_hide", "", 0],
        [" CONNECT", "button", "", connect],
        ["   START", "button", "", start],
        ["    STOP", "button", "", stop],
        ["    EXIT", "button", "", stop_running],
        ["  STATUS", "text", ""],
    ]

    WIFI.active(True)
    show(data, lcd, x_offset, y_offset, line_height, C.white, cursor_pos)
    while running:
        try:
            n = k.readinto(keys)
            if n and n <= 2:
                code = bytes(keys[:n])
                try:
                    key = code.decode()
                    if key == "UP":
                        cursor_pos_previous = cursor_pos
                        cursor_pos -= 1
                        if cursor_pos < 0:
                            cursor_pos = 0
                        refresh = True
                    elif key == "DN":
                        cursor_pos_previous = cursor_pos
                        cursor_pos += 1
                        if cursor_pos >= len(data):
                            cursor_pos = len(data) - 1
                        refresh = True
                    elif key == "\n":
                        if data[cursor_pos][1] == "button":
                            data[cursor_pos][3](data)
                            refresh = True
                    elif key == "\b":
                        if data[cursor_pos][1].startswith("input"):
                            pos = data[cursor_pos][3]
                            data[cursor_pos][2] = data[cursor_pos][2][:pos-1] + data[cursor_pos][2][pos:]
                            data[cursor_pos][3] -= 1
                            if data[cursor_pos][3] < 0:
                                data[cursor_pos][3] = 0
                            refresh = True
                    else:
                        if data[cursor_pos][1].startswith("input"):
                            if key in all_chars:
                                if len(data[cursor_pos][2]) < 25:
                                    pos = data[cursor_pos][3]
                                    data[cursor_pos][2] = data[cursor_pos][2][:pos] + key + data[cursor_pos][2][pos:]
                                    data[cursor_pos][3] += 1
                                    refresh = True
                except:
                    pass
            if WIFI.is_connect():
                if data[2][2] != WIFI.ifconfig()[0]:
                    data[2][2] = WIFI.ifconfig()[0]
                    refresh = True

            if refresh:
                show(data, lcd, x_offset, y_offset, 20, C.white, cursor_pos, cursor_pos_previous)
                refresh = False
        except Exception as e:
            buf = StringIO()
            sys.print_exception(e, buf)
            reason = buf.getvalue()
            print(reason)
            del buf
        time.sleep_ms(50)
    if exists("/main.shell.py"):
        os.rename("/main.py", "/main.ftp.py")
        os.rename("/main.shell.py", "/main.py")
        soft_reset()
