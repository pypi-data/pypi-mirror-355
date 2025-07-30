import enum
from os import PathLike

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.pyplot import contour
from matplotlib.widgets import Slider, Button

from pryttier.math import Vector2, Vector3
from pryttier.tools import *


class GraphStyle(enum.Enum):
    DEFAULT = 'default'
    CLASSIC = 'classic'
    GRAYSCALE = 'grayscale'
    GGPLOT = 'ggplot'
    SEABORN = 'seaborn-v0_8'
    FAST = 'fast'
    BMH = 'bmh'
    SOLARIZED_LIGHT = 'Solarize_Light2'
    SEABORN_NOTEBOOK = 'seaborn-v0_8-notebook'


class ColorMap(enum.Enum):
    ACCENT = "Accent"
    BLUES = "Blues"
    BRBG = "BrBG"
    BUGN = "BuGN"
    BUPU = "BuPu"
    CMRMAP = "CMRmap"
    DARK2 = "Dark_2"
    GNBU = "GnBu"
    GRAYS = "Grays"
    GREENS = "Greens"
    GREYS = "Greys"
    ORRD = "OrRd"
    ORANGES = "Oranges"
    PRGN = "PRGn"
    PAIRED = "Paired"
    PASTEL1 = "Pastel1"
    PASTEL2 = "Pastel2"
    PIYG = "PiYG"
    PUBU = "PuBu"
    PUBUGN = "PuBuGn"
    PUOR = "PuOr"
    PURD = "PuRd"
    PURPLES = "Purples"
    RDBU = "RdBu"
    RDGY = "RdGy"
    RDPU = "RdPu"
    RDYLBU = "RdYlBu"
    RDYLGN = "RdYlGn"
    REDS = "Reds"
    SET1 = "Set1"
    SET2 = "Set2"
    SET3 = "Set3"
    SPECTRAL = "Spectral"
    WISTIA = "Wistia"
    YLGN = "YlGn"
    YLGNBU = "YlGnBu"
    YLORBT = "YlOrBt"
    YLORRD = "YlOrRd"
    AFMHOT = "afmhot"
    AUTUMN = "autumn"
    BINARY = "binary"
    BONE = "bone"
    BRG = "brg"
    BWR = "bwr"
    CIVIDIS = "cividis"
    COOL = "cool"
    COOLWARM = "coolwarm"
    COPPER = "copper"
    CUBEHELIX = "cubehelix"
    FLAG = "flag"
    GIST_EARTH = "gist_earth"
    GIST_GRAY = "gist_gray"
    GIST_HEAT = "gist_heat"
    GIST_NCAR = "gist_ncar"
    GIST_RAINBOW = "gist_rainbow"
    GIST_STERN = "gist_stern"
    GIST_YARG = "gist_yarg"
    GIST_YERG = "gist_yerg"
    GNUPLOT = "gnuplot"
    GNUPLOT2 = "gnuplot_2"
    GRAY = "gray"
    GREY = "grey"
    HOT = "hot"
    HSV = "hsv"
    INFERNO = "inferno"
    JET = "jet"
    MAGMA = "magma"
    NIPY_SPECTRAL = "nipy_spectral"
    OCEAN = "ocean"
    PINK = "pink"
    PLASMA = "plasma"
    PRISM = "prism"
    RAINBOW = "rainbow"
    SEISMIC = "seismic"
    SPRING = "spring"
    SUMMER = "summer"
    TAB10 = "tab_10"
    TAB20 = "tab_20"
    TAB20B = "tab_20_b"
    TAB20C = "tab_20_c"
    TERRAIN = "terrain"
    TRUBO = "trubo"
    TWILIGHT = "twilight"
    TWILIGHT_SHIFTED = "twilight_shifted"
    VIRIDIS = "viridis"
    WINTER = "winter"


class ColorFunction(enum.Enum):
    MAGNITUDE = lambda u, v, z: np.sqrt(u ** 2 + v ** 2)
    SUM = lambda u, v, z: abs(u) + abs(v)
    DIFFERENCE = lambda u, v, z: abs(u) - abs(v)
    PRODUCT = lambda u, v, z: u * v

    @staticmethod
    def LINEAR(axis: str = "x"):
        if axis == "x":
            return lambda u, v, z: u
        elif axis == "y":
            return lambda u, v, z: v
        elif axis == "z":
            return lambda u, v, z: z
        else:
            raise ValueError("Invalid Axis")

    @staticmethod
    def QUADRATIC(axis: str = "x"):
        if axis == "x":
            return lambda u, v, z: u * u
        elif axis == "y":
            return lambda u, v, z: v * v
        elif axis == "z":
            return lambda u, v, z: z * z
        else:
            raise ValueError("Invalid Axis")


class Graph2D:
    def __init__(self, name: str = "Graph 2D", style: GraphStyle = GraphStyle.DEFAULT):
        plt.style.use(style.value)
        self.ax = None
        self.fig = None
        self.name = name
        self.subplots = 0
        self.xLim = (-10, 10)
        self.yLim = (-10, 10)
        self.zLim = (-10, 10)
        self.widgets = 0

    def clear(self):
        self.ax.cla()

    def addFigure(self):
        self.fig = plt.figure()

    def addAxes(self):
        self.ax = self.fig.add_subplot()
        self.ax.set_title(self.name)

    def addAxesForWidgets(self):
        self.ax = self.fig.add_subplot(1, 2, 1)
        self.ax.set_title(self.name)

    def setFig(self, fig):
        self.fig = fig

    def addSubplot(self, row: int, col: int, index: int = None, title: str = None):
        self.subplots += 1
        self.ax = self.fig.add_subplot(row, col, self.subplots if index is None else index)
        if title is not None:
            self.ax.set_title(title)

    def setTitle(self, title: str):
        self.ax.set_title(title)

    def setXlim(self, lim: tuple[float | int, float | int]):
        self.ax.set_xlim(lim)
        self.xLim = lim

    def setYlim(self, lim: tuple[float | int, float | int]):
        self.ax.set_ylim(lim)
        self.yLim = lim

    def setLims(self, limX: tuple[float | int, float | int], limY: tuple[float | int, float | int]):
        self.setXlim(limX)
        self.setYlim(limY)

    def setXLabel(self, label: str):
        self.ax.set_xlabel(label)

    def setYLabel(self, label: str):
        self.ax.set_ylabel(label)

    def setLabels(self, labelX: str, labelY: str):
        self.setXLabel(labelX)
        self.setYLabel(labelY)

    def save(self, name: str):
        self.fig.savefig(name)

    def plotPoint(self, point: Vector2, **kwargs):
        return self.ax.scatter(point.x, point.y, **kwargs)

    def plotPoints(self, *points: Vector2, **kwargs):
        return self.ax.scatter([i.x for i in points], [j.y for j in points], **kwargs)

    def drawLine(self, start: Vector2, end: Vector2, **kwargs):
        line = self.ax.plot([start.x, end.x], [start.y, end.y], **kwargs)
        return line

    def linePlot(self, xVals: Sequence, yVals: Sequence, **kwargs):
        if len(xVals) == len(yVals):
            return self.ax.plot(xVals, yVals, **kwargs)
        else:
            raise ValueError(f"Length of both arrays should be same. Lengths - X: {len(xVals)}, Y: {len(yVals)}")

    def linePlotFromPoints(self, *points: Vector2, **kwargs):
        self.linePlot([a.x for a in points], [a.y for a in points], **kwargs)

    def scatterPlot(self, xVals: Sequence, yVals: Sequence, **kwargs):
        if len(xVals) == len(yVals):
            sctr = self.ax.scatter(xVals, yVals, **kwargs)
        else:
            raise ValueError(f"Length of both arrays should be same. Lengths - X: {len(xVals)}, Y: {len(yVals)}")
        return sctr

    def scatterPlotCF(self, xVals: Sequence, yVals: Sequence,
                      cfunction: Callable | ColorFunction = (lambda x, y, z: x + y), cmap: ColorMap = ColorMap.VIRIDIS, **kwargs):
        c = [cfunction(item1, item2, 0) for item1, item2 in zip(xVals, yVals)]
        if len(xVals) == len(yVals):
            sctr = self.ax.scatter(xVals, yVals, cmap=cmap.value, c=c, **kwargs)
            return sctr
        else:
            raise ValueError(f"Length of both arrays should be same. Lengths - X: {len(xVals)}, Y: {len(yVals)}")

    def plotCSV(self, csvFilePath: Union[str, PathLike], xHeader: str, yHeader: str, color: str = 'blue',
                dots: bool = False, setAxisLabels: bool = True, label: str = None):
        data = pd.read_csv(csvFilePath)
        x = data[xHeader]
        y = data[yHeader]

        if setAxisLabels:
            self.setXLabel(xHeader)
            self.setXLabel(yHeader)

        if dots:
            self.ax.plot(x, y, color, marker="o")
        else:
            self.ax.plot(x, y, color)

    def contourPlot(self,
                    func: Callable[[np.array, np.array], float | int],
                    xRange: np.array = np.linspace(-10, 10, 100),
                    yRange: np.array = np.linspace(-10, 10, 100),
                    cmap: ColorMap | str = ColorMap.VIRIDIS,
                    fill: bool = False
                    ):
        X, Y = np.meshgrid(xRange, yRange)
        Z = func(X, Y)
        if fill:
            c = self.ax.contourf(X, Y, Z, cmap=cmap.value if isinstance(cmap, ColorMap) else cmap)
        else:
            c = self.ax.contour(X, Y, Z, cmap=cmap.value if isinstance(cmap, ColorMap) else cmap)
        return c

    def annotate(self, text: str, xy: tuple[float, float]):
        self.ax.annotate(text, xy)

    def addSlider(self, posX: float = None, posY: float = None, sizeX: float = None, sizeY: float = None,
                  label: str = "slider",
                  min: float | int = 0, max: float | int = 1, initialVal: float | int = 0, stepVal: float | int = 0.1):
        if posX is None:
            posX = 0.55
        if posY is None:
            posY = 0.8 - (0.1 * self.widgets)
        if sizeX is None:
            sizeX = 0.3
        if sizeY is None:
            sizeY = 0.05
        widgetAxes = self.fig.add_axes((posX, posY, sizeX, sizeY))
        self.widgets += 1
        return Slider(widgetAxes, label, min, max, valinit=initialVal, valstep=stepVal)

    def addButton(self, posX: float = None, posY: float = None, sizeX: float = None, sizeY: float = None,
                  label: str = "button", color=None, hoverColor=None):
        if posX is None:
            posX = 0.55
        if posY is None:
            posY = 0.8 - (0.1 * self.widgets)
        if sizeX is None:
            sizeX = 0.3
        if sizeY is None:
            sizeY = 0.05
        widgetAxes = self.fig.add_axes((posX, posY, sizeX, sizeY))
        self.widgets += 1
        return Button(widgetAxes, label=label, color=color, hovercolor=hoverColor)

    @staticmethod
    def showGrid():
        plt.grid()

    @staticmethod
    def legend(*args, **kwargs):
        plt.legend(*args, **kwargs)

    def imshow(self, *args, **kwargs):
        self.ax.imshow(*args, **kwargs)

    @staticmethod
    def show():
        plt.show()


class Graph3D:
    def __init__(self, name: str = "Graph 3D", style: GraphStyle = GraphStyle.DEFAULT):
        self.ax = None
        self.fig = plt.figure()
        plt.style.use(style.value)
        self.name = name
        self.subplots = 0
        self.xLim = (-10, 10)
        self.yLim = (-10, 10)
        self.zLim = (-10, 10)
        self.widgets = 0

    def clear(self):
        self.ax.cla()

    def addAxes(self):
        self.ax = self.fig.add_subplot(projection="3d")
        plt.title(self.name)

    def addAxesWithWidgets(self):
        self.ax = self.fig.add_subplot(1, 2, 1, projection="3d")

    def add2DAxes(self, twod: Graph2D) -> Graph2D:
        twod.setFig(self.fig)

    def addSubplot(self, row: int, col: int, index: int = None, title: str = None):
        self.subplots += 1
        self.ax = self.fig.add_subplot(row, col, self.subplots if index is None else index, projection='3d')
        if title is not None:
            self.ax.set_title(title)

    def setTitle(self, title: str):
        self.ax.set_title(title)

    def setXlim(self, lim: tuple[float | int, float | int]):
        self.xLim = lim
        self.ax.set_xlim(lim)

    def setYlim(self, lim: tuple[float | int, float | int]):
        self.yLim = lim
        self.ax.set_ylim(lim)

    def setZlim(self, lim: tuple[float | int, float | int]):
        self.zLim = lim
        self.ax.set_zlim(lim)

    def setLims(self,
                limX: tuple[float | int, float | int],
                limY: tuple[float | int, float | int],
                limZ: tuple[float | int, float | int]):
        self.setXlim(limX)
        self.setYlim(limY)
        self.setZlim(limZ)

    def setXLabel(self, label: str):
        self.ax.set_xlabel(label)

    def setYLabel(self, label: str):
        self.ax.set_ylabel(label)

    def setZLabel(self, label: str):
        self.ax.set_zlabel(label)

    def setLabels(self,
                  labelX: str,
                  labelY: str,
                  labelZ: str):
        self.setXLabel(labelX)
        self.setYLabel(labelY)
        self.setZLabel(labelZ)

    def save(self, name: str):
        self.fig.savefig(name)

    def point(self, point: Vector3, **kwargs):
        return self.ax.scatter3D(point.x, point.y, point.z, **kwargs)

    def points(self, *points: Vector3, **kwargs):
        sctr = self.ax.scatter3D([i.x for i in points], [j.y for j in points], [k.z for k in points], **kwargs)


    def linePlot(self, xVals: Sequence, yVals: Sequence, zVals: Sequence, **kwargs):
        if len(xVals) == len(yVals) == len(zVals):
            return self.ax.plot(xVals, yVals, zVals, **kwargs)
        else:
            raise ValueError(
                f"Length of arrays should be same. Lengths - X: {len(xVals)}, Y: {len(yVals)}, Z: {len(zVals)}")

    def scatterPlot(self, xVals: Sequence, yVals: Sequence, zVals: Sequence, **kwargs):
        if len(xVals) == len(yVals) == len(zVals):
            sctr = self.ax.scatter3D(xVals, yVals, zVals, **kwargs)
        else:
            raise ValueError(
                f"Length of arrays should be same. Lengths - X: {len(xVals)}, Y: {len(yVals)}, Z: {len(zVals)}")
        return sctr

    def scatterPlotCF(self, xVals: Sequence, yVals: Sequence, zVals: Sequence,
                      cfunction: Callable | ColorFunction = (lambda x, y, z: x + y), cmap: ColorMap = ColorMap.VIRIDIS,
                      colorBar: bool = False, **kwargs):
        c = [cfunction(item1, item2, item3) for item1, item2, item3 in zip(xVals, yVals, zVals)]
        if len(xVals) == len(yVals):
            sctr = self.ax.scatter3D(xVals, yVals, zVals, cmap=cmap.value, c=c, **kwargs)
            if colorBar:
                self.fig.colorbar(sctr)
        else:
            raise ValueError(f"Length of both arrays should be same. Lengths - X: {len(xVals)}, Y: {len(yVals)}")
        return sctr

    def annotate(self, text: str, xy: tuple[float, float]):
        self.ax.annotate(text, xy)

    def addSlider(self, posX: float = None, posY: float = None, sizeX: float = None, sizeY: float = None,
                  label: str = "slider",
                  min: float | int = 0, max: float | int = 1, initialVal: float | int = 0, stepVal: float | int = 0.1):
        if posX is None:
            posX = 0.55
        if posY is None:
            posY = 0.8 - (0.1 * self.widgets)
        if sizeX is None:
            sizeX = 0.3
        if sizeY is None:
            sizeY = 0.05
        widgetAxes = self.fig.add_axes((posX, posY, sizeX, sizeY))
        self.widgets += 1
        return Slider(widgetAxes, label, min, max, valinit=initialVal, valstep=stepVal)

    def addButton(self, posX: float = None, posY: float = None, sizeX: float = None, sizeY: float = None,
                  label: str = "button", color=(1, 1, 1), hoverColor=(0.4, 0.4, 0.4)):
        if posX is None:
            posX = 0.55
        if posY is None:
            posY = 0.8 - (0.1 * self.widgets)
        if sizeX is None:
            sizeX = 0.3
        if sizeY is None:
            sizeY = 0.05
        widgetAxes = self.fig.add_axes((posX, posY, sizeX, sizeY))
        self.widgets += 1
        return Button(widgetAxes, label=label, color=color, hovercolor=hoverColor)

    @staticmethod
    def showGrid():
        plt.grid()

    @staticmethod
    def legend(*args, **kwargs):
        plt.legend(*args, **kwargs)

    @staticmethod
    def show():
        plt.show()


def generateFaceColors(graph: Graph3D,
                       values: Sequence[Vector3] | tuple[
                           Sequence[int | float], Sequence[int | float], Sequence[int | float]]):
    if isinstance(graph, Graph2D):
        raise ValueError(f"Graph must be of type {Graph3D.__name__} not {Graph2D.__name__}")
    if not ((graph.xLim == (0, 1)) and (graph.yLim == (0, 1)) and (graph.zLim == (0, 1))):
        raise Exception(f"Graph's axes limits must be (0, 1). Got X:{graph.xLim} Y:{graph.yLim} Z:{graph.zLim}")
    if type(values[0]) == Vector3:
        return [[a.x, a.y, a.z] for a in values]
    if type(values) == tuple:
        if len(values[0]) == len(values[1]) == len(values[2]):
            return [[a, b, c] for a, b, c in zip(values[0], values[1], values[2])]
        else:
            raise ValueError(
                f"Length of x, y and z values must be same. Got X:{len(values[0])} Y:{len(values[1])} Z:{len(values[0])}")
