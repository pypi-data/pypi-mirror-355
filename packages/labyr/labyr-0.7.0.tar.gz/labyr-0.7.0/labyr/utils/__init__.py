import msvcrt
import os
from os import system


def getch():
    return msvcrt.getch().decode("utf-8")


def getchar(d, arg):
    return d.get(arg, d["DEFAULTS"][arg])


def clsscr():
    system("cls" if os.name == "nt" else "clear")
