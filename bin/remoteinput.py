import sys
import socket

from lib.scheduler import Task, Condition, Message
from lib.common import exists, path_join, KEYS_MAP

coroutine = True


def remote_input(task, name, scheduler = None, interval = 50):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('0.0.0.0', 8888))
    s.listen(1)
    s.setblocking(False)
    conn = None
    stop = False
    while not stop:
        yield Condition.get().load(sleep = interval)
        msg = task.get_message()
        if msg:
            if msg.content["msg"] == "stop":
                stop = True
            msg.release()
        try:
            if conn is None:
                conn, addr = s.accept()
                #print(dir(conn))
                #print('connect form', addr)
                conn.setblocking(False)
            else:
                keys = conn.recv(6)
                for b in keys:
                    key = KEYS_MAP.get(bytes([b]))
                    if not key:
                        conn.close()
                        conn = None
                    elif key != "":
                        if (key not in ("ES", "UP", "DN", "LT", "RT", "BX", "BB", "BY", "BA", "SAVE", "SUP", "SDN") and not key.startswith("Ctrl-")) and len(key) > 1:
                            for k in key:
                                # print("key: ", k)
                                if scheduler.shell and scheduler.shell.session_task_id and scheduler.exists_task(scheduler.shell.session_task_id):
                                    yield Condition.get().load(sleep = 0, send_msgs = [Message.get().load({"msg": k, "keys": []}, receiver = scheduler.shell.session_task_id)])
                                else:
                                    yield Condition.get().load(sleep = 0, send_msgs = [Message.get().load({"char": k}, receiver = scheduler.current_shell_id)])
                        else:
                            # print("key: ", key)
                            if scheduler.shell and scheduler.shell.session_task_id and scheduler.exists_task(scheduler.shell.session_task_id):
                                yield Condition.get().load(sleep = 0, send_msgs = [Message.get().load({"msg": key, "keys": []}, receiver = scheduler.shell.session_task_id)])
                            else:
                                yield Condition.get().load(sleep = 0, send_msgs = [Message.get().load({"char": key}, receiver = scheduler.current_shell_id)])
        except OSError as e:
            pass
    s.close()


def main(*args, **kwargs):
    result = "invalid parameters"
    args = kwargs["args"]
    shell_id = kwargs["shell_id"]
    shell = kwargs["shell"]
    scheduler = shell.scheduler
    try:
        if len(args) > 0:
            if args[0] == "start":
                task_id = scheduler.add_task(Task.get().load(remote_input, "remote_keyboard", condition = Condition.get(), kwargs = {"scheduler": scheduler, "interval": 50}))
                result = f"remote keyboard({task_id}): 0.0.0.0:8888"
            elif args[0] == "stop":
                result = "task not found"
                for i, t in enumerate(scheduler.tasks):
                    if t.name == "remote_keyboard":
                        yield Condition.get().load(sleep = 0, send_msgs = [
                            Message.get().load({"msg": "stop"}, receiver = t.id)
                        ])
                        result = f"send stop signal to task({t.id})"
                        break
            elif args[0] == "status":
                result = "stopped"
                for i, t in enumerate(scheduler.tasks):
                    if t.name == "remote_keyboard":
                        result = f"running({t.id}): 0.0.0.0:8888"
                        break
            else:
                result = "Usage: remoteinput start|stop|status"
            yield Condition.get().load(sleep = 0, send_msgs = [
                Message.get().load({"output": result}, receiver = shell_id)
            ])
        else:
            yield Condition.get().load(sleep = 0, send_msgs = [
                Message.get().load({"output": "Usage: remoteinput start|stop|status"}, receiver = shell_id)
            ])
    except Exception as e:
        yield Condition.get().load(sleep = 0, send_msgs = [
            Message.get().load({"output": str(sys.print_exception(e))}, receiver = shell_id)
        ])
