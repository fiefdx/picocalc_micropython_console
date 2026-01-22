import machine

coroutine = False


def main(*args, **kwargs):
    result = "path invalid"
    if len(args) > 0:
        if args[0].isdigit():
            f = int(args[0]) * 1000000
            machine.freq(f, f)
            result = "CPU speed set to %.2f Mhz" % (machine.freq() / 1000000)
    else:
        result = "CPU speed is %.2f Mhz" % (machine.freq() / 1000000)
    return result
