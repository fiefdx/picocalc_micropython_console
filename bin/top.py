import gc
import sys
from machine import Pin, I2C

from scheduler import Condition, Message
from common import Resource

coroutine = True


def main(*args, **kwargs):
    task = args[0]
    name = args[1]
    result = "invalid parameters"
    shell_id = kwargs["shell_id"]
    shell = kwargs["shell"]
    shell.enable_cursor = False
    width, height = 40, 28
    try:
        app_exit = False
        while not app_exit:
            try:
                frame = []
                gc.collect()
                ram_free = gc.mem_free()
                ram_used = gc.mem_alloc()
                ram_total = ram_free + ram_used
                b = Resource.keyboard.battery_status()
                plugged_in = b["charging"]
                level = b["level"]
                monitor_msg = "CPU%s:%3d%% RAM:%3d%% BATTERY[%s]: %3d%%" % (shell.scheduler.cpu, int(100 - shell.scheduler.idle), int(100 - (ram_free * 100 / ram_total)), "C" if plugged_in else "D", level)
                padding = " " * ((width - len(monitor_msg)) // 2)
                frame.append(padding + monitor_msg)
                if shell.scheduler.current is not None:
                    frame.append("%03d %36s" % (shell.scheduler.current.id, shell.scheduler.current.name))
                for i, t in enumerate(shell.scheduler.tasks):
                    frame.append("%03d %36s"  % (t.id, t.name))
                for i in range(0, height - len(frame)):
                    frame.append("")
                yield Condition.get().load(sleep = 1000, wait_msg = False, send_msgs = [
                    Message.get().load({"output_part": "\n".join(frame[:height])}, receiver = shell_id)
                ])
                yield Condition.get().load(sleep = 1000)
                msg = task.get_message()
                if msg:
                    if msg.content["msg"] == "ES":
                        app_exit = True
                    msg.release()
            except Exception as e:
                print(e)
        yield Condition.get().load(sleep = 0, send_msgs = [
            Message.get().load({"output": ""}, receiver = shell_id)
        ])
        shell.enable_cursor = True
        shell.loading = True
    except Exception as e:
        yield Condition.get().load(sleep = 0, send_msgs = [
            Message.get().load({"output": sys.print_exception(e)}, receiver = shell_id)
        ])
        shell.enable_cursor = True
        shell.loading = True
