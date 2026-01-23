import gc

from lib.scheduler import Condition, Message

coroutine = True


def main(*args, **kwargs):
    task = args[0]
    name = args[1]
    shell_id = kwargs["shell_id"]
    shell = kwargs["shell"]
    try:
        shell.clear_cache()
        gc.collect()
        yield Condition.get().load(sleep = 0, send_msgs = [
            Message.get().load({"output": ""}, receiver = shell_id)
        ])
    except Exception as e:
        yield Condition.get().load(sleep = 0, send_msgs = [
            Message.get().load({"output": sys.print_exception(e)}, receiver = shell_id)
        ])
