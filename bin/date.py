import sys
from machine import Pin, I2C

from lib.scheduler import Condition, Message
from lib.common import exists, path_join, Time

coroutine = True


def main(*args, **kwargs):
    result = "invalid parameters"
    args = kwargs["args"]
    shell_id = kwargs["shell_id"]
    try:
        if len(args) > 0:
            if args[0] == "-s":
                if Time.sync():
                    yield Condition.get().load(sleep = 0, send_msgs = [
                        Message.get().load({"output": Time.now()}, receiver = shell_id)
                    ])
                else:
                    yield Condition.get().load(sleep = 0, send_msgs = [
                        Message.get().load({"output": "sync failed"}, receiver = shell_id)
                    ])
            else:
                yield Condition.get().load(sleep = 0, send_msgs = [
                    Message.get().load({"output": Time.now()}, receiver = shell_id)
                ])
        else:
            yield Condition.get().load(sleep = 0, send_msgs = [
                Message.get().load({"output": Time.now()}, receiver = shell_id)
            ])
    except Exception as e:
        yield Condition.get().load(sleep = 0, send_msgs = [
            Message.get().load({"output": str(sys.print_exception(e))}, receiver = shell_id)
        ])
