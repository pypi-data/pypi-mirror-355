import datetime
import math
import os
import random
import time
from functools import partial
from typing import *


class Infix(object):
    def __init__(self, func: Callable) -> None:
        self.func = func

    def __or__(self, other: Self) -> Self:
        return self.func(other)

    def __ror__(self, other: Self) -> Self:
        return Infix(partial(self.func, other))

    def __call__(self, v1, v2):
        return self.func(v1, v2)


# ===Some Infix Operations===
percentOf = Infix(lambda x, y: x / 100 * y)  # x% of y
isDivisibleBy = Infix(lambda x, y: x % y == 0)  # checks if x is divisible by y


def ifelse(cond: bool, true: Any, false: Any):
    if cond:
        return true
    else:
        return false

def apply(itr: Iterable, func: Callable) -> list:
    return [func(x) for x in itr]


def apply2D(iter1: Sequence, iter2: Sequence, func: Callable) -> list:
    return [func(item1, item2) for item1, item2 in zip(iter1, iter2)]


def chunks(lst: MutableSequence, n: int):
    result = []
    for i in range(0, len(lst), n):
        result.append(lst[i:i + n])
    return result

def retry(func: Callable, retries: int = 3, args: list = []):
    i = 0
    if len(args) < retries:
        raise TypeError("Insufficient arguments")
    while True:
        if i >= retries:
            break
        try:
            func(*args[i])
        except:
            print(f"Test {i}: Failed")
            i += 1
        else:
            print(f"Test {i}: Passed")
            i += 1


def findCommonItems(*lsts: list) -> list:
    return list(set(lsts[0]).intersection(*lsts[1:]))

def swap(array: list, index1: int, index2: int):
    temp: int = array[index1]
    array[index1] = array[index2]
    array[index2] = temp

def hex2Dec(hx: str):
    res = 0
    n = len(hx)
    for i in range(n):
        num = hx[i]
        if num in ["a", "A"]: num = "10"
        if num in ["b", "B"]: num = "11"
        if num in ["c", "C"]: num = "12"
        if num in ["d", "D"]: num = "13"
        if num in ["e", "E"]: num = "14"
        if num in ["f", "F"]: num = "15"

        res += int(num) * 16**(n - i - 1)
    return res

def cycle(arr, ind, t: Literal["circ", "osc"] = "circ"):
    if t == "circ":
        return arr[ind % len(arr)]
    elif t == "osc":
        ...
    else:
        raise TypeError("Invalid t type. Possible types: circ, osc")

class Card:
    ACE = 1
    JACK = 11
    QUEEN = 12
    KING = 13

    HEARTS = 40
    DIAMONDS = 41
    SPADE = 42
    CLOVER = 43

    RED = 20
    BLACK = 21

    def __init__(self, number: int, symbol: int):
        self.n = number
        match self.n:
            case 1:
                self.n = "Ace"
            case self.JACK:
                self.n = "Jack"
            case self.QUEEN:
                self.n = "Queen"
            case self.KING:
                self.n = "King"

        self.symbol = symbol
        match self.symbol:
            case self.HEARTS:
                self.symbol = "Hearts"
            case self.DIAMONDS:
                self.symbol = "Diamonds"
            case self.SPADE:
                self.symbol = "Spade"
            case self.CLOVER:
                self.symbol = "Clover"

        self.color = self.RED if self.symbol in [self.HEARTS, self.DIAMONDS] else self.BLACK

    def __repr__(self):
        return f"{self.n} of {self.symbol}"

    @classmethod
    def deck(cls):
        cardDeck = []
        for a in [cls.HEARTS, cls.DIAMONDS, cls.CLOVER, cls.SPADE]:
            for n in range(1, 14):
                cardDeck.append(Card(n, a))
        return cardDeck


class Stopwatch:
    def __init__(self):
        self.t1 = 0
        self.t2 = 0
        self.laps = []

    def start(self):
        self.t1 = time.time()

    def lap(self):
        self.laps.append(self.end())
        self.t1 = 0
        self.t2 = 0
        self.start()

    def elapsed(self):
        return time.time() - self.t1

    def end(self):
        self.t2 = time.time()
        return self.t2 - self.t1

# === File Management ===

def timeConvert(atime):
    dt = atime
    newtime = datetime.datetime.fromtimestamp(dt)
    return newtime.date()


def sizeFormat(size):
    sizeUnits = ["KB", "MB", "GB", "TB"]
    i = 0
    size = size/1024
    for _ in range(3):
        if size >= 1024:
            size = size / 1024
            i += 1
    return f"{size:.3f} {sizeUnits[i]}"

class File:
    def __init__(self, fp: str | os.PathLike[str]):
        if not os.path.isfile(fp):
            raise ValueError("Provided path is not a file")
        if not os.path.exists(fp):
            raise ValueError("Provided path does not exist")
        self.path = fp
        self.stats = os.stat(self.path)
        self.name = os.path.basename(self.path)
        self.size = sizeFormat(self.stats.st_size)
        self.cdate = timeConvert(self.stats.st_ctime)
        self.mdate = timeConvert(self.stats.st_mtime)
        self.lastAccess = timeConvert(self.stats.st_atime)

    def __repr__(self):
        return f"{self.name}"

class Folder:
    def __init__(self, fp: str | os.PathLike[str]):
        if not os.path.isdir(fp):
            raise ValueError("Provided path is not a folder")
        if not os.path.exists(fp):
            raise ValueError("Provided path does not exist")
        self.path = fp
        self.stats = os.stat(self.path)
        self.name = os.path.basename(self.path)
        self.size = sizeFormat(self.getSize())
        self.cdate = timeConvert(self.stats.st_ctime)
        self.mdate = timeConvert(self.stats.st_mtime)
        self.lastAccess = timeConvert(self.stats.st_atime)


    def getSize(self):
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(self.path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                # skip if it is symbolic link
                if not os.path.islink(fp):
                    total_size += os.path.getsize(fp)

        return total_size
    def __repr__(self):
        return f"{self.name}"

def filesFromDir(dp: os.PathLike[str]):
    return os.listdir(dp)






