import itertools
import math
import random
from fractions import Fraction
from typing import *
from multipledispatch import dispatch
import numpy as np

PI = 2 * np.arccos(0)
Degrees = PI / 180


def summation(n: float | int, i: float | int, expr: Callable) -> float:
    total = 0
    for j in range(n, i + 1):
        total += expr(j)
    return total

def product(n: int, i: int, expr: Callable) -> float:
    total = 1
    for j in range(n, i):
        total *= expr(j)
    return total

def clamp(num: float, low: float, high: float) -> float:
    if num < low:
        return low
    if num > high:
        return high
    return num

def sign(num: float) -> int:
    return int(num / abs(num))

def factorial(num: int) -> int:
    if num == 0:
        return 1
    if num == 1:
        return 1
    return num * factorial(num - 1)

def mapRange(value: int | float,
             min1: float,
             max1: float,
             min2: float,
             max2: float) -> float:
    return (value - min1) / (max1 - min1) * (max2 - min2) + min2

def isPrime(n: int) -> bool:
    if n <= 1:
        return False
    for i in range(2, int(n ** 0.5) + 1):
        if n % i == 0:
            return False
    return True

def getFactors(num: int):
    factors = []
    for i in range(1, num + 1):
        if num % i == 0:
            factors.append(i)

    return factors

def decToFraction(dec: float):
    return Fraction(dec).limit_denominator()

def radToDeg(num: float):
    return num * (180 / PI)

def degToRad(num: float):
    return num * (PI / 180)

def getDigits(num: int):
    return [int(i) for i in list(str(num))]

class SampleSpace:
    """WARNING: Not suitable for large sample spaces"""

    def __init__(self, space: list) -> None:
        self.space: list = space

    def __repr__(self):
        return str(self.space).replace("[", "{").replace("]", "}")

    def getIf(self, func: Callable[[Any], bool]) -> list:
        items = []
        for i in self.get():
            if func(i):
                items.append(i)
        return items

    def __len__(self) -> int:
        return len(self.space)

    def get(self) -> list:
        return self.space

    @classmethod
    def generate(cls, possibility: list | str, length: int, repeat: bool = True) -> Self:
        if repeat:
            combs = list(itertools.product(possibility, repeat=length))
        else:
            combs = list(itertools.permutations(possibility, r=length))

        for i in range(len(combs)):
            isStr = []
            for j in combs[i]:
                if type(j) == str:
                    isStr.append(True)
                else:
                    isStr.append(False)

            if all(isStr):
                combs[i] = "".join(combs[i])

        return SampleSpace(combs)

def probability(sampleSpace: SampleSpace, favourable: list):
    for i in favourable:
        if i not in sampleSpace.get():
            return 0
    return len(favourable) / len(sampleSpace)


class Vector2:
    def __init__(self,
                 x: float | int,
                 y: float | int = None):
        self._x = x
        self._y = y
        if y is None:
            self._y = x

    @property
    def x(self):
        return self._x

    @property
    def y(self):
        return self._y

    @property
    def xy(self):
        return (self._x, self._y)

    @x.setter
    def x(self, value):
        self._x = value

    @y.setter
    def y(self, value):
        self._y = value

    def __repr__(self) -> str:
        return f"({self.x}, {self.y})"

    def __add__(self, other: Self) -> Self:
        return Vector2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Self) -> Self:
        return Vector2(self.x - other.x, self.y - other.y)

    def __mul__(self, other: float | int) -> Self:
        return Vector2(self.x * other, self.y * other)

    def __truediv__(self, other: float | int):
        return Vector2(self.x / other, self.y / other)

    def __iter__(self):
        return iter([self.x, self.y])

    def angle(self):
        return math.atan2(self.y, self.x)

    def magnitude(self):
        return math.sqrt(self.x * self.x + self.y * self.y)

    def normalize(self) -> Self:
        if self.magnitude() == 0:
            return Vector2.zero()
        return Vector2(self._x / self.magnitude(), self._y / self.magnitude())

    def toInt(self):
        return Vector2(int(self._x), int(self._y))

    def __round__(self, n=None):
        return Vector2(round(self._x, n), round(self._y, n))

    def round(self, n=None):
        return Vector2(round(self._x, n), round(self._y, n))

    def toMat(self):
        mat = Matrix(2, 1)
        mat.set([[self._x], [self._y]])
        return mat

    def toNumpy(self):
        return np.array([self._x, self._y])

    # ---Class Methods---
    @classmethod
    def zero(cls):
        return Vector2(0, 0)

    @classmethod
    def one(cls):
        return Vector2(1, 1)

    @classmethod
    def distance(cls, a: Self, b: Self):
        dx = b._x - a._x
        dy = b._y - a._y
        return math.sqrt(dx * dx + dy * dy)

    @classmethod
    def dot(cls, a: Self, b: Self):
        return Vector2(a._x * b._x, a._y * b._y)

    @classmethod
    def cross(cls, a: Self, b: Self):
        return a._x * b._y - a._y * b._x

    @classmethod
    def angleBetween(cls, a: Self, b: Self):
        dotProduct = cls.dot(a, b)
        magA = a.magnitude()
        magB = b.magnitude()
        return math.acos(dotProduct / (magA * magB))

    @classmethod
    def interpolate(cls, a: Self, b: Self, t: float):
        v = b - a
        pdx = a._x + v._x * t
        pdy = a._y + v._y * t
        return Vector2(pdx, pdy)

class Vector3:
    def __init__(self,
                 x: float | int,
                 y: float | int = None,
                 z: float | int = None):
        self._x = x
        self._y = y
        self._z = z
        if y is None and z is None:
            self._y = x
            self._z = x
        elif z is None and y is not None:
            raise Exception(self._z, "z Missing")

    @property
    def x(self):
        return self._x

    @property
    def y(self):
        return self._y

    @property
    def z(self):
        return self._z

    @property
    def xyz(self):
        return (self._x, self._y, self._z)

    @x.setter
    def x(self, value):
        self._x = value

    @y.setter
    def y(self, value):
        self._y = value

    @z.setter
    def z(self, value):
        self._z = value

    def __repr__(self) -> str:
        return f"({self._x}, {self._y}, {self._z})"

    def __add__(self, other: Self) -> Self:
        return Vector3(self._x + other._x, self._y + other._y, self._z + other._z)

    def __sub__(self, other: Self) -> Self:
        return Vector3(self._x - other._x, self._y - other._y, self._z - other._z)

    def __mul__(self, other: float | int) -> Self:
        return Vector3(self._x * other, self._y * other, self._z * other)

    def __truediv__(self, other: float | int):
        return Vector3(self._x / other, self._y / other, self._z / other)

    def __iter__(self):
        return iter([self._x, self._y, self._z])

    def magnitude(self):
        return math.sqrt(self._x * self._x + self._y * self._y + self._z * self._z)

    def normalize(self) -> Self:
        if self.magnitude() == 0:
            return Vector3.zero()
        return Vector3(self._x / self.magnitude(), self._y / self.magnitude(), self._z / self.magnitude())

    def toInt(self):
        return Vector3(int(self._x), int(self._y), int(self._z))

    def __round__(self, n=None):
        return Vector3(round(self._x, n), round(self._y, n), round(self._z, n))

    def toMat(self):
        mat = Matrix(3, 1)
        mat.set([[self._x], [self._y], [self._z]])
        return mat

    def toNumpy(self):
        return np.array([self._x, self._y, self._z])

    # ---Class Methods---
    @classmethod
    def zero(cls):
        return Vector3(0, 0, 0)

    @classmethod
    def one(cls):
        return Vector3(1, 1, 1)

    @classmethod
    def distance(cls, a: Self, b: Self):
        dx = b._x - a._x
        dy = b._y - a._y
        dz = b._z - a._z
        return math.sqrt(dx * dx + dy * dy + dz * dz)

    @classmethod
    def dot(cls, a: Self, b: Self):
        return Vector3(a._x * b._x, a._y * b._y, a._z * b._z)

    @classmethod
    def cross(cls, a: Self, b: Self) -> Self:
        i = a._y * b._z - a._z * b._y
        j = a._z * b._x - a._x * b._z
        k = a._x * b._y - a._y * b._x
        return Vector3(i, j, k)

    @classmethod
    def angleBetween(cls, a: Self, b: Self):
        dotProduct = cls.dot(a, b)
        magA = a.magnitude()
        magB = b.magnitude()
        return math.acos(dotProduct / (magA * magB))

    @classmethod
    def interpolate(cls, a: Self, b: Self, t: float):
        v = b - a
        pdx = a._x + v._x * t
        pdy = a._y + v._y * t
        pdz = a._z + v._z * t
        return Vector3(pdx, pdy, pdz)


def closestFromArrayNumber(arr: Sequence[float], num: float | int):
    def difference(a):
        return abs(a - num)

    return min(arr, key=difference)

def closestFromArrayVec2(arr: Sequence[Vector2], num: Vector2):
    def difference(a: Vector2):
        return Vector2(abs(a.x - num.x), abs(a.y - num.y)).magnitude

    return min(arr, key=difference)

def closestFromArrayVec3(arr: Sequence[Vector3], num: Vector3):
    def difference(a: Vector3):
        return Vector3(a.x - num.x, a.y - num.y, a.z - num.z).magnitude

    return min(arr, key=difference)

def arrayToVec2array(arr: Sequence[Sequence[int]]):
    result = []
    for i in arr:
        if len(i) != 2:
            raise Exception("length has to be 2")
        else:
            result.append(Vector2(*i))
    return result

def arrayToVec3array(arr: Sequence[Sequence[int]]):
    result = []
    for i in arr:
        if len(i) != 3:
            raise Exception("length has to be 3")
        else:
            result.append(Vector3(*i))
    return result

def vec2arrayToArray(arr: Sequence[Vector2]):
    return [[a.x, a.y] for a in arr]

def vec3arrayToArray(arr: Sequence[Vector3]):
    return [[a.x, a.y, a.z] for a in arr]

def angleToDirection2(angle: float):
    x = math.cos(angle)
    y = math.sin(angle)
    return Vector2(x, y)

def angleToDirection3(theta: float, phi: float):
    x = math.sin(theta) * math.cos(phi)
    y = math.sin(theta) * math.sin(phi)
    z = math.cos(theta)
    return Vector3(x, y, z)

def lerp(a, b, t: float):
    return (1 - t) * a + t * b

def lerp2D(p1: Vector2, p2: Vector2, t: float):
    return p1 + (p2 - p1) * t

def lerp3D(p1: Vector3, p2: Vector3, t: float):
    return p1 + (p2 - p1) * t

class Matrix:

    @dispatch(int, int, fill=float)
    def __init__(self, r: int, c: int, *, fill: int | float = 0) -> None:
        self.rows = r
        self.cols = c
        self.matrix = np.full([r, c], fill)

    @dispatch(list)
    def __init__(self, mat: np.ndarray | list[list[int | float]]) -> None:
        self.matrix = np.array(mat)
        self.rows = len(mat)
        self.cols = len(mat[0])

    def set(self, mat: np.ndarray | list[list[int | float]]) -> np.ndarray | ValueError:
        matRows = len(mat)
        matCols = len(mat[0])
        if matRows == self.rows and matCols == self.cols:
            self.matrix = mat
        else:
            raise ValueError(f"Expected matrix of dimensions ({self.rows}, {self.cols}) but got ({matRows}, {matCols})")

    def __repr__(self):
        txt = [""]  # ┌┘└┐
        if self.rows >= 20:
            for i in range(3):
                if self.cols >= 20:
                    row = []
                    for j in range(3):
                        row.append(float(self.matrix[i][j]))
                    row.append(f"... {self.cols-6}")
                    for j in range(self.cols-3, self.cols):
                        row.append(float(self.matrix[i][j]))
                    row = f"|{row}|\n"
                    row = row.replace("[", "").replace("]", "").replace(",", "")
                    txt.append(row)
                else:
                    row = f"|{[float(self.matrix[i][j]) for j in range(self.cols)]}|\n"
                    row = row.replace("[", "").replace("]", "").replace(",", "")
                    txt.append(row)
            txt.append(f"...{self.rows-6}\n")
            for i in range(self.rows-3, self.rows):
                if self.cols >= 20:
                    row = []
                    for j in range(3):
                        row.append(float(self.matrix[i][j]))
                    row.append(f"... {self.cols-6}")
                    for j in range(self.cols-3, self.cols):
                        row.append(float(self.matrix[i][j]))
                    row = f"|{row}|\n"
                    row = row.replace("[", "").replace("]", "").replace(",", "")
                    txt.append(row)
                else:
                    row = f"|{[float(self.matrix[i][j]) for j in range(self.cols)]}|\n"
                    row = row.replace("[", "").replace("]", "").replace(",", "")
                    txt.append(row)
        else:
            for i in range(self.rows):
                if self.cols >= 20:
                    row = []
                    for j in range(3):
                        row.append(float(self.matrix[i][j]))
                    row.append(f"... {self.cols-6}")
                    for j in range(self.cols-3, self.cols):
                        row.append(float(self.matrix[i][j]))
                    row = f"|{row}|\n"
                    row = row.replace("[", "").replace("]", "").replace(",", "")
                    txt.append(row)
                else:
                    row = f"|{[float(self.matrix[i][j]) for j in range(self.cols)]}|\n"
                    row = row.replace("[", "").replace("]", "").replace(",", "")
                    txt.append(row)
        return "".join(txt)

    def row(self, n):
        return self.matrix[n]

    def col(self, n):
        return [float(self.matrix[i][n]) for i in range(self.rows)]

    def __getitem__(self, item: tuple[int, int] | int):
        if type(item) == int:
            return self.matrix[item]
        elif type(item) == tuple:
            return self.matrix[item[0]][item[1]]

    def __setitem__(self, key: tuple[int | np.ndarray[Any], int | np.ndarray[Any]], value: int | float | np.ndarray[Any]):
        self.matrix[key[0]][key[1]] = value

    def __invert__(self):
        newMat = Matrix(self.cols, self.rows)
        for i in range(self.rows):
            for j in range(self.cols):
                newMat[j][i] = self.matrix[i][j]
        return newMat

    def __matmul__(self, other: Self):
        if self.cols != other.rows:
            raise TypeError(
                "Number of columns of the first matrix must be equal to number of rows of the second matrix")
        mat = Matrix(self.rows, other.cols)
        mat.matrix = np.dot(self.matrix, other.matrix)
        return mat

    def __add__(self, other):
        mat = Matrix(self.rows, self.cols)
        if self.rows != other.rows or self.cols != other.cols:
            raise ValueError("Sizes dont match")
        for i in range(self.rows):
            for j in range(self.cols):
                mat[i][j] = self.matrix[i][j] + other.matrix[i][j]

        return mat

    def __sub__(self, other):
        mat = Matrix(self.rows, self.cols)
        if self.rows != other.rows or self.cols != other.cols:
            raise ValueError("Sizes dont match")
        for i in range(self.rows):
            for j in range(self.cols):
                mat[i][j] = self.matrix[i][j] - other.matrix[i][j]

        return mat

    def __mul__(self, other):
        mat = Matrix(self.rows, self.cols)
        if self.rows != other.rows or self.cols != other.cols:
            raise ValueError("Sizes dont match")
        for i in range(self.rows):
            for j in range(self.cols):
                mat[i][j] = self.matrix[i][j] * other.matrix[i][j]

        return mat

    def toVec(self):
        if self.cols == 2:
            return Vector2(float(self[0, 0]), float(self[0, 1]))
        elif self.cols == 3:
            return Vector3(float(self[0, 0]), float(self[0, 1]), float(self[0, 2]))

    # Class Methods
    @classmethod
    def identity(cls, r, c):
        mat = Matrix(r, c)
        for i in range(r):
            for j in range(c):
                if i == j: mat.matrix[i][j] = 1
        return mat

    @classmethod
    def random(cls, r, c, mn: int | float , mx: int | float, t=Literal["int", "float"]):
        rand = RandomInt(mn, mx) if t == "int" else RandomFloat(mn, mx)
        mat = Matrix(r, c)
        for i in range(r):
            for j in range(c):
                mat.matrix[i][j] = rand.get()
        return mat

# === Random ===

class RandomInt:
    def __init__(self, start: int, stop: int):
        self.start = start
        self.stop = stop

    def get(self):
        return random.randint(self.start, self.stop)

class RandomFloat:
    def __init__(self, start: int, stop: int):
        self.start = start
        self.stop = stop

    def get(self):
        return random.uniform(self.start, self.stop)

class RandomVec2Int:
    def __init__(self, xRange: tuple[int, int], yRange: tuple[int, int]):
        self.xRange = xRange
        self.yRange = yRange

    def get(self):
        x = random.randint(self.xRange[0], self.xRange[1])
        y = random.randint(self.yRange[0], self.yRange[1])
        return Vector2(x, y)

class RandomVec3Int:
    def __init__(self, xRange: tuple[int, int], yRange: tuple[int, int], zRange: tuple[int, int]):
        self.xRange = xRange
        self.yRange = yRange
        self.zRange = zRange

    def get(self):
        x = random.randint(self.xRange[0], self.xRange[1])
        y = random.randint(self.yRange[0], self.yRange[1])
        z = random.randint(self.zRange[0], self.zRange[1])
        return Vector3(x, y, z)

class RandomVec2Float:
    def __init__(self, xRange: tuple[int | float, int | float], yRange: tuple[int | float, int | float]=None):
        self.xRange = xRange
        if yRange is None:
            self.yRange = xRange
        else:
            self.yRange = yRange

    def get(self):
        x = random.uniform(self.xRange[0], self.xRange[1])
        y = random.uniform(self.yRange[0], self.yRange[1])
        return Vector2(x, y)

class RandomVec3Float:
    def __init__(self, xRange: tuple[int, int], yRange: tuple[int, int] = None, zRange: tuple[int, int] = None):
        self.xRange = xRange
        if yRange is None and zRange is None:
            self.yRange = xRange
            self.zRange = xRange
        else:
            self.yRange = yRange
            self.zRange = zRange

    def get(self):
        x = random.uniform(self.xRange[0], self.xRange[1])
        y = random.uniform(self.yRange[0], self.yRange[1])
        z = random.uniform(self.zRange[0], self.zRange[1])
        return Vector3(x, y, z)

class RandomDir2:
    def __init__(self):
        self.theta = RandomFloat(0, 360)
    def get(self):
        x = math.cos(self.theta.get() * Degrees)
        y = math.sin(self.theta.get() * Degrees)
        return Vector2(x, y)

class RandomDir3:
    def __init__(self):
        self.theta = RandomFloat(0, 180)
        self.phi = RandomFloat(0, 360)
    def get(self):
        x = math.sin(self.theta.get() * Degrees) * math.cos(self.phi.get() * Degrees)
        y = math.sin(self.theta.get() * Degrees) * math.sin(self.phi.get() * Degrees)
        z = math.sin(self.theta.get() * Degrees)
        return Vector3(x, y, z)

class RandomDir2BetweenAngles:
    def __init__(self, a1: int | float, a2: int | float):
        self.start = a1
        self.stop = a2

    def get(self):
        angle = random.uniform(self.start, self.stop)
        x = math.cos(angle)
        y = math.sin(angle)
        return Vector2(x, y)
