import sys
from datetime import datetime


def show_colors():
    for i in range(0, 16):
        for j in range(0, 16):
            code = str(i * 16 + j)
            sys.stdout.write(u"\u001b[38;5;" + code + "m " + code.ljust(4))
    print(u"\u001b[0m")  # clear and new line


class Colors(object):
    SUCCESS_COLOR = "82"
    WARNING_COLOR = "185"
    ERROR_COLOR = "196"
    FATAL_COLOR = "207"


def get_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def info(msg):
    sys.stdout.write(f'[I] {get_time()} >> {msg}\n')


def suc(msg):
    sys.stdout.write(f'[S] {get_time()} >> ' + u"\u001b[38;5;" + Colors.SUCCESS_COLOR + "m" + msg + u"\u001b[0m" + "\n")


def warn(msg):
    sys.stdout.write(f'[W] {get_time()} >> ' + u"\u001b[38;5;" + Colors.WARNING_COLOR + "m" + msg + u"\u001b[0m" + "\n")


def err(msg):
    sys.stdout.write(f'[E] {get_time()} >> ' + u"\u001b[38;5;" + Colors.ERROR_COLOR + "m" + msg + u"\u001b[0m" + "\n")


def fatal(msg):
    sys.stdout.write(f'[F] {get_time()} >> ' + u"\u001b[38;5;" + Colors.FATAL_COLOR + "m" + msg + u"\u001b[0m" + "\n")
