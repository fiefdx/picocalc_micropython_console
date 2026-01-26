import os
import sys
import socket
import traceback
import logging
import math
import time
import random
import pygame
import threading
from threading import Thread
from queue import Queue, Empty

import logger

LOG = logging.getLogger(__name__)

__version__ = "0.0.1"

os.environ['SDL_VIDEO_CENTERED'] = '1'

TaskQueue = Queue(5)
ResultQueue = Queue(5)

KEYS_MAP = {
    b'\x61' : "a",
    b'\x62' : "b",
    b'\x63' : "c",
    b'\x64' : "d",
    b'\x65' : "e",
    b'\x66' : "f",
    b'\x67' : "g",
    b'\x68' : "h",
    b'\x69' : "i",
    b'\x6a' : "j",
    b'\x6b' : "k",
    b'\x6c' : "l",
    b'\x6d' : "m",
    b'\x6e' : "n",
    b'\x6f' : "o",
    b'\x70' : "p",
    b'\x71' : "q",
    b'\x72' : "r",
    b'\x73' : "s",
    b'\x74' : "t",
    b'\x75' : "u",
    b'\x76' : "v",
    b'\x77' : "w",
    b'\x78' : "x",
    b'\x79' : "y",
    b'\x7a' : "z",
    b'\x41' : "A",
    b'\x42' : "B",
    b'\x43' : "C",
    b'\x44' : "D",
    b'\x45' : "E",
    b'\x46' : "F",
    b'\x47' : "G",
    b'\x48' : "H",
    b'\x49' : "I",
    b'\x4a' : "J",
    b'\x4b' : "K",
    b'\x4c' : "L",
    b'\x4d' : "M",
    b'\x4e' : "N",
    b'\x4f' : "O",
    b'\x50' : "P",
    b'\x51' : "Q",
    b'\x52' : "R",
    b'\x53' : "S",
    b'\x54' : "T",
    b'\x55' : "U",
    b'\x56' : "V",
    b'\x57' : "W",
    b'\x58' : "X",
    b'\x59' : "Y",
    b'\x5a' : "Z",
    b'\x60' : "`",
    b'\x31' : "1",
    b'\x32' : "2",
    b'\x33' : "3",
    b'\x34' : "4",
    b'\x35' : "5",
    b'\x36' : "6",
    b'\x37' : "7",
    b'\x38' : "8",
    b'\x39' : "9",
    b'\x30' : "0",
    b'\x2d' : "-",
    b'\x3d' : "=",
    b'\x5b' : "[",
    b'\x5d' : "]",
    b'\x5c' : "\\",
    b'\x3b' : ";",
    b'\x27' : "'",
    b'\x2c' : ",",
    b'\x2e' : ".",
    b'\x2f' : "/",
    b'\x7e' : "~",
    b'\x21' : "!",
    b'\x40' : "@",
    b'\x23' : "#",
    b'\x24' : "$",
    b'\x25' : "%",
    b'\x5e' : "^",
    b'\x26' : "&",
    b'\x2a' : "*",
    b'\x28' : "(",
    b'\x29' : ")",
    b'\x5f' : "_",
    b'\x2b' : "+",
    b'\x7b' : "{",
    b'\x7d' : "}",
    b'\x7c' : "|",
    b'\x3a' : ":",
    b'\x22' : "\"",
    b'\x3c' : "<",
    b'\x3e' : ">",
    b'\x3f' : "?",
    b'\x20' : " ",
    b'\x08' : "\b",
    b'\t'   : "\t",
    b'\n'   : "\n",
    # b'\xd4': "DEL",
    b'\xb1': "ES",
    b'\xb5': "UP",
    b'\xb6': "DN",
    b'\xb4': "LT",
    b'\xb7': "RT",
    b'\x13': "SAVE",
    b'\x01': "Ctrl-A",
    b'\x02': "Ctrl-B",
    b'\x03': "Ctrl-C",
    b'\x07': "Ctrl-G",
    b'\r'  : "Ctrl-M",
    b'\x11': "Ctrl-Q",
    b'\x14': "Ctrl-T",
    b'\x16': "Ctrl-V",
    b'\x18': "Ctrl-X",
    b'\x1a': "Ctrl-Z",
    b'\x0f': "Ctrl-/",
    b'\x83': "BY",
    b'\x85': "BA",
    b'\x84': "BX",
    b'\xd4': "BB",
    b'\x81': "F1",
    b'\x82': "F2",
    # b'\x83': "F3",
    # b'\x84': "F4",
    # b'\x85': "F5",
    # b'\x86': "F6",
    # b'\x87': "F7",
    b'\x88': "F8",
    b'\x89': "F9",
    b'\x90': "F10",
    b'\xd2': "HOME",
    b'\xd5': "END",
    b'\xd0': "BRK",
    b'\xd1': "INS",
}


class StoppableThread(Thread):
    def __init__(self):
        super(StoppableThread, self).__init__()
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()


class WorkThread(StoppableThread):
    def __init__(self, task_queue, result_queue):
        StoppableThread.__init__(self)
        Thread.__init__(self)
        self.task_queue = task_queue
        self.result_queue = result_queue

    def run(self):
        try:
            while True:
                if not self.stopped():
                    try:
                        task = self.task_queue.get(block = False)
                        if task:
                            time.sleep(0.1)
                        else:
                            time.sleep(0.1)
                    except Empty:
                        time.sleep(0.1)
                else:
                    break
        except Exception as e:
            print(e)


class UserInterface(object):
    def __init__(self, host, port, work_thread, task_queue, result_queue):
        pygame.init()
        pygame.mixer.init()
        self.window = pygame.display.set_mode((512, 128)) # pygame.FULLSCREEN | pygame.SCALED) # , pygame.RESIZABLE)
        pygame.display.set_caption("RemoteKeyboard - v%s" % __version__)
        pygame.display.set_icon(pygame.image.load("icon.png"))

        self.host = host
        self.port = port
        self.work_thread = work_thread
        self.font_command = pygame.font.SysFont('Arial', 70)
        self.font = pygame.font.SysFont('Arial', 20)
        self.chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ`1234567890-=[]\\;',./~!@#$%^&*()_+{}|:\"<>? \b\n"
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((self.host, self.port))
        self.input = ""
        self.input_max_length = 10

        self.keys = {
            pygame.K_ESCAPE:   (b'\xb1', b'\xb1'),   # ES
            pygame.K_RETURN:   (b'\n',   b'\n'),
            pygame.K_SPACE:    (b'\x20', b'\x20'),
            pygame.K_BACKSPACE:(b'\x08', b'\x08'),
            pygame.K_a: (b'\x61', b'\x41'),
            pygame.K_b: (b'\x62', b'\x42'),
            pygame.K_c: (b'\x63', b'\x43'),
            pygame.K_d: (b'\x64', b'\x44'),
            pygame.K_e: (b'\x65', b'\x45'),
            pygame.K_f: (b'\x66', b'\x46'),
            pygame.K_g: (b'\x67', b'\x47'),
            pygame.K_h: (b'\x68', b'\x48'),
            pygame.K_i: (b'\x69', b'\x49'),
            pygame.K_j: (b'\x6a', b'\x4a'),
            pygame.K_k: (b'\x6b', b'\x4b'),
            pygame.K_l: (b'\x6c', b'\x4c'),
            pygame.K_m: (b'\x6d', b'\x4d'),
            pygame.K_n: (b'\x6e', b'\x4e'),
            pygame.K_o: (b'\x6f', b'\x4f'),
            pygame.K_p: (b'\x70', b'\x50'),
            pygame.K_q: (b'\x71', b'\x51'),
            pygame.K_r: (b'\x72', b'\x52'),
            pygame.K_s: (b'\x73', b'\x53'),
            pygame.K_t: (b'\x74', b'\x54'),
            pygame.K_u: (b'\x75', b'\x55'),
            pygame.K_v: (b'\x76', b'\x56'),
            pygame.K_w: (b'\x77', b'\x57'),
            pygame.K_x: (b'\x78', b'\x58'),
            pygame.K_y: (b'\x79', b'\x59'),
            pygame.K_z: (b'\x7a', b'\x5a'),
            pygame.K_BACKQUOTE: (b'\x60', b'\x7e'),
            pygame.K_1: (b'\x31', b'\x21'),
            pygame.K_2: (b'\x32', b'\x40'),
            pygame.K_3: (b'\x33', b'\x23'),
            pygame.K_4: (b'\x34', b'\x24'),
            pygame.K_5: (b'\x35', b'\x25'),
            pygame.K_6: (b'\x36', b'\x5e'),
            pygame.K_7: (b'\x37', b'\x26'),
            pygame.K_8: (b'\x38', b'\x2a'),
            pygame.K_9: (b'\x39', b'\x28'),
            pygame.K_0: (b'\x30', b'\x29'),
            pygame.K_MINUS:        (b'\x2d', b'\x5f'),
            pygame.K_EQUALS:       (b'\x3d', b'\x2b'),
            pygame.K_LEFTBRACKET:  (b'\x5b', b'\x7b'),
            pygame.K_RIGHTBRACKET: (b'\x5d', b'\x7d'),
            pygame.K_BACKSLASH:    (b'\x5c', b'\x7c'),
            pygame.K_SEMICOLON:    (b'\x3b', b'\x3a'),
            pygame.K_QUOTE:        (b'\x27', b'\x22'),
            pygame.K_COMMA:        (b'\x2c', b'\x3c'),
            pygame.K_PERIOD:       (b'\x2e', b'\x3e'),
            pygame.K_SLASH:        (b'\x2f', b'\x3f'),
            pygame.K_UP:    (b'\xb5', b'\xb5'),  # UP
            pygame.K_DOWN:  (b'\xb6', b'\xb6'),  # DN
            pygame.K_LEFT:  (b'\xb4', b'\xb4'),  # LT
            pygame.K_RIGHT: (b'\xb7', b'\xb7'),  # RT
            pygame.K_PAGEUP:   (b'\x83', b'\x83'),  # BY / SUP
            pygame.K_PAGEDOWN: (b'\x85', b'\x85'),  # BA / SDN
        }

        self.key_pressed = None
        self.key_pressed_status = False
        self.key_pressed_interval = 5
        self.key_pressed_trigger = 10
        self.key_pressed_counter = 0

        self.clock = pygame.time.Clock()
        self.key = ""
        self.running = True

    def quit(self):
        self.s.close()
        self.work_thread.stop()
        self.running = False

    def process_key(self, event):
        self.key = self.keys[event.key][0]
        if event.mod & pygame.KMOD_CAPS:
            self.key = self.keys[event.key][1]
        elif event.mod & pygame.KMOD_SHIFT:
            self.key = self.keys[event.key][1]
        self.s.sendall(self.key.encode())
        self.input += self.key
        self.key_pressed = event.key
        self.key_pressed_counter = 0
        if len(self.input) >= self.input_max_length:
            self.input = self.input[-self.input_max_length:]
        print(KEYS_MAP[self.key])

    def process_input(self):
        self.key_pressed_counter += 1
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit()
                break
            elif event.type == pygame.KEYDOWN:
                if event.key in self.keys:
                    # self.process_key(event)
                    self.key = self.keys[event.key][0]
                    if event.mod & pygame.KMOD_CAPS:
                        self.key = self.keys[event.key][1]
                    elif event.mod & pygame.KMOD_SHIFT:
                        self.key = self.keys[event.key][1]
                    elif event.mod & pygame.KMOD_CTRL:
                        if self.key == b'\x73' or self.key == b'\x53': # "s", "S"
                            self.key = b'\x13' # "SAVE"
                        elif b'\x7a' >= self.key >= b'\x61' or b'\x5a' >= self.key >= b'\x41': # "z", "a", "Z", "A"
                            self.key = bytes([self.key[0] & 0x1f]) # "Ctrl-" + 
                    self.s.sendall(self.key)
                    self.input += KEYS_MAP[self.key] if KEYS_MAP[self.key] != "\b" else " "
                    if KEYS_MAP[self.key] in self.chars:
                        self.key_pressed = self.key
                        self.key_pressed_counter = 0
                    if len(self.input) >= self.input_max_length:
                        self.input = self.input[-self.input_max_length:]
                    print(KEYS_MAP[self.key])
            elif event.type == pygame.KEYUP:
                if event.key in self.keys:
                    self.key = self.keys[event.key][0]
                    if event.mod & pygame.KMOD_CAPS:
                        self.key = self.keys[event.key][1]
                    elif event.mod & pygame.KMOD_SHIFT:
                        self.key = self.keys[event.key][1]
                    if self.key == self.key_pressed:
                        self.key_pressed = None
                        self.key_pressed_status = False
        if not self.key_pressed_status:
            if self.key_pressed_counter >= self.key_pressed_trigger:
                self.key_pressed_status = True
                self.key_pressed_counter = 0
                if self.key_pressed is not None:
                    self.s.sendall(self.key_pressed)
                    self.input += KEYS_MAP[self.key] if KEYS_MAP[self.key] != "\b" else " "
                    if len(self.input) >= self.input_max_length:
                        self.input = self.input[-self.input_max_length:]
                    print(KEYS_MAP[self.key_pressed])
        else:
            if self.key_pressed_counter >= self.key_pressed_interval:
                self.key_pressed_counter = 0
                if self.key_pressed is not None:
                    self.s.sendall(self.key_pressed)
                    self.input += KEYS_MAP[self.key] if KEYS_MAP[self.key] != "\b" else " "
                    if len(self.input) >= self.input_max_length:
                        self.input = self.input[-self.input_max_length:]
                    print(KEYS_MAP[self.key_pressed])

    def render(self):
        red = (180, 53, 53)
        yellow = (214, 199, 11)
        green = (81, 146, 3)
        offset_x = 0
        offset_y = 0
        self.window.fill((180, 180, 180))
        input_cache = self.font_command.render(self.input, True, (0, 0, 0))
        x = (512 - input_cache.get_width()) // 2
        self.window.blit(input_cache, (offset_x + x, offset_y + 20))
        pygame.display.update()

    def run(self):
        while self.running:
            self.process_input()
            self.render()
            self.clock.tick(30)

if __name__ == "__main__":
    logger.config_logging(file_name = "keyboard.log",
                          log_level = "INFO",
                          dir_name = "logs",
                          day_rotate = False,
                          when = "D",
                          interval = 1,
                          max_size = 20,
                          backup_count = 5,
                          console = True)
    LOG.info("start")
    host = "192.168.4.41"
    port = 8888
    if len(sys.argv) > 1:
        host = sys.argv[1]
    if len(sys.argv) > 2:
        port = int(sys.argv[2])
    worker = WorkThread(TaskQueue, ResultQueue)
    worker.start()
    UserInterface = UserInterface(host, port, worker, TaskQueue, ResultQueue)
    UserInterface.run()
    worker.join()
    pygame.quit()
    LOG.info("end")