# -*- coding: utf-8 -*-
"""
Last modified on Oct 18, 2024

@author: Hermann Zeyen <hermann.zeyen@universite-paris-saclay.fr>
         Université Paris-Saclay, France

Contains the following classes for plotting purposes of program PyMaGra:

    - plot
    - newWindow

"""

import os
import numpy as np
from PyQt5.uic import loadUiType
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QVBoxLayout, QWidget
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar,
)
from matplotlib.figure import Figure
from matplotlib.ticker import AutoMinorLocator
from matplotlib.path import Path as P
from matplotlib.gridspec import GridSpec
from matplotlib import tri
from ..inversion import mag_grav_utilities as utils

Ui_MainWindow, QMainWindow = loadUiType(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "Magnetics.ui")
)


class plot(QMainWindow, Ui_MainWindow):
    """
    Class for plotting in PyMaGra

    Depends on the following packages:

        - numpy
        - PyQt5
        - matplotlib

    Needed private files:

        - Magnetics.ui (user interface, produced with QtDesigner)

    Contains the following methods:

        - __init__
        - setClipPath
        - set_geography_flag
        - toggle_geography_flag
        - plot_geography
        - plot_lineaments
        - plot_north
        - plot_triang
        - plot_image
        - addMPL
        - rmMPL
        - plotFloating
        - get_mouse_click (with method onClick);
          Wait for mouse click return position and type
        - get_event (with method onClick);
          Wait for mouse click or keyboard press
        - setHelp : Set help text written at the base of the screen
        - followLine : Follow the cursor and plot a straight line

    """

    def __init__(self, main):
        super().__init__()
# Set up main window based on file Magnetics.ui created with QT Designer
        self.setupUi(self)
# create a first figure in central widget
        self.fig = Figure()
        self.fig.tight_layout()
        self.addMPL(self.fig)
        self.main = main
        self.grid_flag = True
        self.plotLin_flag = False
        self.geography_flag = False
        self.legend = []
        self.grad_data = []
        self.unit = "nT"
        self.bar_or = "vertical"
        self.nticks = 10
        self.axfont = 16
        self.cidmotion = None
        self.cidrelease = None

    def setClipPath(self, x, y):
        """
        define clip path

        Parameters
        ----------
        x : numpy float array
            contains all x-coordinates of data points.
        y : numpy float array
            contains all y-coordinates of data points.

        Returns
        -------
        PATH matplotlib.path

        """
        clip_x = []
        clip_y = []
        if self.main.direction == 0:
            for xx in np.unique(x):
                yy = np.round(np.nanmax(y[x == xx]), 2)
                if len(clip_x) == 0:
                    yy0 = yy
                else:
                    if yy > yy0:
                        # clip_x.append(xx - 0.01)
                        xc = (xx + clip_x[-1]) * 0.5
                        clip_x.append(xc)
                        clip_y.append(yy0)
                        clip_x.append(xc)
                        clip_y.append(yy)
                    elif yy < yy0:
                        # clip_x.append(clip_x[-1] + 0.01)
                        # clip_y.append(yy0)
                        xc = (xx + clip_x[-1]) * 0.5
                        clip_x.append(xc)
                        clip_y.append(yy0)
                        clip_x.append(xc)
                        clip_y.append(yy)
                clip_x.append(xx)
                clip_y.append(yy)
                yy0 = yy
            il = 0
            for xx in np.unique(x)[::-1]:
                yy = np.round(np.nanmin(y[x == xx]), 2)
                if il == 0:
                    yy0 = yy
                    il = 1
                else:
                    if yy < yy0:
                        # clip_x.append(xx + 0.01)
                        # clip_y.append(yy0)
                        xc = (xx + clip_x[-1]) * 0.5
                        clip_x.append(xc)
                        clip_y.append(yy0)
                        clip_x.append(xc)
                        clip_y.append(yy)
                    elif yy > yy0:
                        # clip_x.append(clip_x[-1] - 0.01)
                        # clip_y.append(yy)
                        xc = (xx + clip_x[-1]) * 0.5
                        clip_x.append(xc)
                        clip_y.append(yy0)
                        clip_x.append(xc)
                        clip_y.append(yy)
                clip_x.append(xx)
                clip_y.append(yy)
                yy0 = yy
        else:
            for yy in np.unique(y):
                xx = np.round(np.nanmax(x[y == yy]), 2)
                if len(clip_x) == 0:
                    xx0 = xx
                else:
                    if xx > xx0:
                        # clip_y.append(yy - 0.01)
                        # clip_x.append(xx0)
                        yc = (yy + clip_y[-1]) * 0.5
                        clip_y.append(yc)
                        clip_x.append(xx0)
                        clip_y.append(yc)
                        clip_x.append(xx)
                    elif xx < xx0:
                        # clip_y.append(clip_y[-1] + 0.01)
                        # clip_x.append(xx)
                        yc = (yy + clip_y[-1]) * 0.5
                        clip_y.append(yc)
                        clip_x.append(xx0)
                        clip_y.append(yc)
                        clip_x.append(xx)
                clip_y.append(yy)
                clip_x.append(xx)
                xx0 = xx
            il = 0
            for yy in np.unique(y)[::-1]:
                xx = np.round(np.nanmin(x[y == yy]), 2)
                if il == 0:
                    xx0 = xx
                    il = 1
                else:
                    if xx < xx0:
                        # clip_y.append(yy + 0.01)
                        # clip_x.append(xx0)
                        yc = (yy + clip_y[-1]) * 0.5
                        clip_y.append(yc)
                        clip_x.append(xx0)
                        clip_y.append(yc)
                        clip_x.append(xx)
                    elif xx > xx0:
                        # clip_y.append(clip_y[-1] - 0.01)
                        # clip_x.append(xx)
                        yc = (yy + clip_y[-1]) * 0.5
                        clip_y.append(yc)
                        clip_x.append(xx0)
                        clip_y.append(yc)
                        clip_x.append(xx)
                clip_y.append(yy)
                clip_x.append(xx)
                xx0 = xx
        clip_x.append(clip_x[0])
        clip_y.append(clip_y[0])
        clip = np.zeros((len(clip_x), 2))
        clip[:, 0] = np.array(clip_x)
        clip[:, 1] = np.array(clip_y)
# Clip contains the coordinates of the clipping path.
# Codes will contain the way to connect clipping points (move to the first
# point of the path, draw lines to all other points and finally close the path)
        codes = []
        Path = P
        codes += [Path.MOVETO]
        codes += [Path.LINETO] * (len(clip_x) - 2)
        codes += [Path.CLOSEPOLY]
# set clipping
        return Path(clip, codes)

    def set_geography_flag(self, option):
        """
        Set flag to plot geography information or not to value "option".

        Parameters
        ----------
        option : bool
            If True, geography information is plotted.

        """
        self.geography_flag = option

    def toggle_geography_flag(self):
        """
        Inverse value of flag to plot geography information or not.

        No input or output parameters

        """
        self.geography_flag = not self.geography_flag

    def plot_geography(self, ax):
        """
        Plot geography information into axis "ax".

        Parameters
        ----------
        ax : Matplotlib.Axis object

        Geography information is stored in class Main as dictionary with
        entries

        - "type" : may be "point" or "line"
        - "x" : x coordinate(s) of point or line
        - "y" : y coordinate(s) of point or line

        """
        xmin, xmax = ax.get_xlim()
        ymin, ymax = ax.get_ylim()
# Plot a point
        for key in self.main.geography.keys():
            if self.main.geography[key]["type"] == "POINT":
                x = self.main.geography[key]["x"]
                y = self.main.geography[key]["y"]
# If fpoint outside map don't plot
                if x < xmin or x > xmax or y < ymin or y > ymax:
                    continue
# Check whether a point has already been plotted. If not, add label to legend
                if "town" in self.legend:
                    ax.plot(x, y, "o", color="black")
                else:
                    self.legend.append("town")
                    ax.plot(x, y, "o", color="black", label="town/place")
                ax.text(x, y, "  " + self.main.geography[key]["name"],
                        ha="left", va="center")
# Plot a line and check whether a line has already been plotted.
            else:
                if "geology" in self.legend:
                    ax.plot(self.main.geography[key]["x"],
                            self.main.geography[key]["y"], "k")
                else:
                    self.legend.append("geology")
                    ax.plot(self.main.geography[key]["x"],
                            self.main.geography[key]["y"], "k",
                            label="geology")

    def plot_lineaments(self, ax):
        """
        Plot lineaments picked from tilt maps into axis "ax".

        Parameters
        ----------
        ax : Matplotlib.Axis object

        Lineament information is stored as dictionary with entries

        - "type" : may be "gravity" or "magnetic"
        - "x" : x coordinate(s) of point or line
        - "y" : y coordinate(s) of point or line

        """
        col = "k"
        for key in self.lineaments.keys():
            if "gravity" in self.lineaments[key]["type"]:
                col = "w"
            elif "magnetic" in self.lineaments[key]["type"]:
                col = "k"
            if self.lineaments[key]["type"] in self.legend:
                ax.plot(self.lineaments[key]["x"], self.lineaments[key]["y"],
                        col, ls="--", linewidth=4)
            else:
                self.legend.append(self.lineaments[key]["type"])
                ax.plot(self.lineaments[key]["x"], self.lineaments[key]["y"],
                        col, label=self.lineaments[key]["type"], ls="--",
                        linewidth=4)

    def plot_north(self, ax, angle, pos):
        """
        Plot North arrow into map
        It is supposed that the map is drawn with set_aspect="equal"

        Parameters
        ----------
        ax : matplotlib axes object
            axis where to plot the North arrow.
        angle : float
            Angle in degrees from N to E (geological sense, not mathematical).
        pos : str
            string of two characters indicationg the position of the arrow.
            One character may be "t" or "b" for top or bottom of the plot
            The other letter may be "l" or "r" for left or right
            The order of the two characters as well as capitalization has no
            importance.

        Returns
        -------
        None.

        """
        xmin, xmax = ax.get_xlim()
        ymin, ymax = ax.get_ylim()
        dx = (xmax - xmin) * 0.02
        dy = (ymax - ymin) * 0.05
        alpha = 90.0 - angle
        if alpha < -180:
            alpha += 360.0
        if alpha > 180:
            alpha -= 360.0
        c = np.cos(np.deg2rad(alpha))
        s = np.sin(np.deg2rad(alpha))
        dxa = dy * c
        dya = dy * s
        radius = np.sqrt(dxa**2 + dya**2)

        if "t" in pos.lower():
            y0 = ymax - (1.5 + s) * dy
        else:
            y0 = ymin + (1.5 - s) * dy
        if "r" in pos.lower():
            x0 = xmax - (2.5 + 2 * c) * dx
        else:
            x0 = xmin + (2.5 - 2 * c) * dx

        ax.arrow(x0, y0, dxa, dya, width=dya/5.0, length_includes_head=True,
                 head_length=radius, head_width=radius/1.5, shape="left",
                 color="k", edgecolor=None)
        ax.arrow(x0, y0, dxa, dya, width=dya/5.0, length_includes_head=True,
                 head_length=radius, head_width=radius / 1.5, shape="right",
                 facecolor="w", edgecolor="k")
        ax.text(x0+dxa*0.5, y0+dya*0.5, "N", fontsize=20, c="r",
                horizontalalignment="center",
                verticalalignment="center_baseline",
                rotation=alpha-90.0, rotation_mode="anchor")
        # ax.text(x0 + dxa * 1.6, y0 + dya * 1.75, "N",
        #         horizontalalignment="center",
        #         verticalalignment="center_baseline",
        #         rotation=alpha - 90.0, rotation_mode="anchor")

    def plot_sensor_triang(self, ax, x, y, s, vmin, vmax, percent, cmap,
                           xlabel, ylabel, title, cbar_title, dec=0.0):
        """
        Plot map of one sensor by triangulation

        Parameters
        ----------
        ax : Matplotlib axis
            Axis where to plot the map
        x : Numpy 1D float array
            X-coordinates of data
        y : Numpy 1D float array
            Y-coordinates of data
        s : Numpy 1D float array
            Values [nT or mGal]
        vmin : float
            Value for lower end of color scale [nT or mGal]
            If vmin==vmax, the color scale is calculated automatically based on
            quantiles (see "percent")
        vmax : float
            Value for upper end of color scale [nT or mGal]
        percent : float
            Scaling of color scale. Maximum value is percentile (1-percent),
            minimum value for percentile percent. This is only used if
            mincol==maxcol.
        cmap : Matplotlib color map
            Color map to be used
        xlabel : str
            Label for x-axis
        ylabel : str
            Label for y-axis
        title : str
            Title of map
        cbar_title : str
            Text for color bar
        dec : float (optional, default : 0.)
            Direction of the measurement lines with respect to magnetic North
            in degrees, measured from N to E

        Returns
        -------
        None.

        """
        self.legend = []
# Define clip paths for both sensors, searching for every line maximum and
#    minimum coordinates
        xmin = x.min()
        xmax = x.max()
        ymin = y.min()
        ymax = y.max()
        clip_path = self.setClipPath(x, y)
        rd = (int(np.ceil(-np.log10(np.nanquantile(s, 0.999)
                                    - np.nanquantile(s, 0.001))))+2)
    # Define collor bar limits and levels
        if vmin == vmax:
            if percent > 0:
                max_col = np.round(np.nanquantile(s, 1 - percent), rd)
                min_col = np.round(np.nanquantile(s, percent), rd)
            else:
                max_col = np.round(np.nanmax(s), rd)
                min_col = np.round(np.nanmin(s), rd)
        else:
            max_col = np.round(vmax, rd)
            min_col = np.round(vmin, rd)
        if cmap == "special mag":
            cmap, norm = utils.mag_color_map(min_col, max_col, cif=2)
        else:
            norm = "linear"
        rd = int(np.ceil(-np.log10(max_col - min_col))) + 2
        nlev = 51
        ds = np.round((max_col - min_col) / nlev, rd)
        levels = np.arange(min_col, max_col + ds / 2, ds)
# Calculate triangulation
        triang = tri.Triangulation(x, y)
# Do triangulation plot
        gci = ax.tricontourf(triang, s, extend="both", vmin=min_col,
                             vmax=max_col, levels=levels, cmap=cmap,
                             norm=norm)
        ax.set_clip_on(True)
        for collection in gci.collections:
            collection.set_clip_path(clip_path, transform=ax.transData)
        ax.set_title(title, fontsize=self.axfont + 2)
        ax.set_xlabel(xlabel, fontsize=self.axfont)
        ax.set_ylabel(ylabel, fontsize=self.axfont)
        ax.tick_params(labelsize=self.axfont)
        if self.grid_flag:
            ax.grid(visible=True, which="both")
        if self.plotLin_flag:
            self.plot_lineaments(ax)
        ax.set_xlim([xmin, xmax])
        ax.set_ylim([ymin, ymax])
        ax.xaxis.set_minor_locator(AutoMinorLocator())
        ax.yaxis.set_minor_locator(AutoMinorLocator())
        if self.bar_or == "vertical":
            cax = ax.inset_axes([1.05, 0.05, 0.02, 0.9],
                                transform=ax.transAxes)
        else:
            cax = ax.inset_axes([0.05, -0.2, 0.9, 0.05],
                                transform=ax.transAxes)
        smin = np.round(np.nanmin(s), rd)
        smax = np.round(np.nanmax(s), rd)
        ssmin = levels[0]
        ssmax = levels[-1]
        ds = (ssmax - ssmin) / (self.nticks - 1)
        ticks = np.round(np.arange(ssmin, ssmax + ds / 2, ds), rd)
        ticks = list(ticks)
# Plot color bar
        cbar = plt.colorbar(gci, orientation=self.bar_or, cax=cax,
                            fraction=0.1, ticks=ticks, extend="both")
        if self.bar_or == "vertical":
            cbar.ax.set_ylabel(cbar_title, size=10)
            cbar.ax.text(0.0, -0.06, f"{smin}", verticalalignment="top",
                         horizontalalignment="left",
                         transform=cbar.ax.transAxes, fontsize=10)
            cbar.ax.text(0.0, 1.06, f"{smax}", verticalalignment="bottom",
                         horizontalalignment="left",
                         transform=cbar.ax.transAxes, fontsize=10)
        else:
            cbar.ax.set_xlabel(cbar_title, size=10)
            cbar.ax.text(0.0, 1.0, f"{smin}", verticalalignment="bottom",
                         horizontalalignment="right",
                         transform=cbar.ax.transAxes, fontsize=10)
            cbar.ax.text(1.0, 1.0, f"{smax}", verticalalignment="bottom",
                         horizontalalignment="left",
                         transform=cbar.ax.transAxes, fontsize=10)
        ticklabs = cbar.ax.get_yticklabels()
        cbar.ax.set_yticklabels(ticklabs, fontsize=10)
        ticklabs = cbar.ax.get_xticklabels()
        cbar.ax.set_xticklabels(ticklabs, fontsize=10)
        ax.set_aspect("equal", adjustable="box")
        if self.geography_flag:
            self.plot_geography(ax)
        if self.plotLin_flag:
            ax.legend(bbox_to_anchor=(1, 1), loc="upper right", fontsize=10)
        self.plot_north(ax, -dec, "tl")

    def plot_triang(self, data, title="Measured magnetic data",
                    xlabel="Easting", ylabel="Northing", percent=0.01,
                    c="rainbow", mincol1=0.0, maxcol1=0.0, mincol2=0.0,
                    maxcol2=0.0, mincolg=0.0, maxcolg=0.0, grad_flag=False):
        """
        Plot maps of not interpolated data (stn format) of both sensors using
        tricontourf

        Parameters
        ----------
        data: dictionary with one entry per line, key = number of line.
              Each entry is itself a dictionary containing the following
              entries:

              - "s1": Numpy float array with data of sensor 1
              - "s2": Numpy float array with data of sensor 2
                If only data of one single sensor were measured, "s2" contains
                only one zero.
              - "x":  Numpy float array with E-W coordinates of data points
              - "y":  Numpy float array with N-S coordinates of data points
              - "grad_flag" bool. True if 2 sensors were used, False if only
                one sensor
              - "mask": bool, True if line should be plotted, False if excluded
                from plotting
        title : str, optional. Default is "Measured magnetic data"
            Plot title for both sensor polts (the text "sensor n" is
            automatically added, n being sensor numnber).
        xlabel : str, optional
            Text for x-axis. The default is "Easting".
        ylabel : str, optional
            Text for y-axis. The default is "Northing".
        percent : float, optional
            Scaling of color scale. Maximum value is percentile (1-percent),
            minimum value for percentile percent. The default is 0.01.
            This is only used if mincol==maxcol.
        mincol1 : float, optional
            value for lower end of color scale for sensor 1 [nT]
        maxcol1 : float, optional
            value for upper end of color scale for sensor 1 [nT]
            If mincol1==maxcol1, the color scale is calculated automatically
            based on quantiles (see "percent")
        mincol2 : float, optional
            value for lower end of color scale for sensor 2 [nT]
        maxcol2 : float, optional
            value for upper end of color scale for sensor 2 [nT]
            If mincol2==maxcol2, the color scale is calculated automatically
            based on quantiles (see "percent")
        mincolg : float, optional
            value for lower end of color scale for vertical gradient [nT/m]
        maxcolg : float, optional
            value for upper end of color scale for vertical gradient [nT/m]
            If mincolg==maxcolg, the color scale is calculated automatically
            based on quantiles (see "percent")
        c : str, optional
            Color map to be used. The default is "rainbow".
        grad_flag: bool, optional, default: False
            If True, 3 plots are shown on the screen: Sensor1, sensor2 and
            gradient. If False only the two sensors are plotted

        Returns
        -------
        fig : matplotlib.figure
            Figure used for plot.
        ax : matplotlib.axis
            List of axes used for plots. ax has two entrances, one for each
            sensor

        """
        x = []
        y = []
        v1 = []
        v2 = []
        self.grad_data = data["grad_data"]
        if data["type"] == "magnetic":
            self.unit = "nT"
        else:
            self.unit = "mGal"
        for key, val in data.items():
            try:
                _ = int(key)
                if not val["mask"]:
                    continue
                x += list(val["x"])
                y += list(val["y"])
                v1 += list(val["s1"])
                if self.grad_data:
                    v2 += list(val["s2"])
            except ValueError:
                break
        x = np.array(x)
        y = np.array(y)
        v1 = np.array(v1)
        v2 = np.array(v2)
        ddx = x.max() - x.min()
        ddy = y.max() - y.min()

        ax = []
# Gradient is plotted
        if self.grad_data:
            if grad_flag:
                facx = 10 / (3 * ddx)
                facy = 8 / (3 * ddy)
# Vertical layout
                if facx < facy:
                    self.bar_or = "vertical"
                    self.nticks = 10
                    fig = plt.figure(figsize=(14, 12), layout="constrained")
                    self.gs = GridSpec(26, 10, fig)
                    ax.append(fig.add_subplot(self.gs[1:9, 1:]))
                    ax.append(fig.add_subplot(self.gs[9:17, 1:]))
                    ax.append(fig.add_subplot(self.gs[17:25, 1:]))
# Horizontal layout
                else:
                    fig = plt.figure(figsize=(26, 12), layout="constrained")
                    self.gs = GridSpec(10, 26, fig)
                    ax.append(fig.add_subplot(self.gs[1:, 1:9]))
                    ax.append(fig.add_subplot(self.gs[1:, 9:17]))
                    ax.append(fig.add_subplot(self.gs[1:, 17:25]))
                    self.bar_or = "horizontal"
                    self.nticks = 4
# Gradient is not plotted
            else:
                facx = 10 / (3 * ddx)
                facy = 8 / (3 * ddy)
# Vertical layout
                if facx < facy:
                    fig = plt.figure(figsize=(14, 12), layout="constrained")
                    self.gs = GridSpec(18, 10, fig)
                    ax.append(fig.add_subplot(self.gs[1:9, 1:]))
                    ax.append(fig.add_subplot(self.gs[9:17, 1:]))
                    self.bar_or = "vertical"
                    self.nticks = 10
# Horizontal layout
                else:
                    fig = plt.figure(figsize=(18, 12), layout="constrained")
                    self.gs = GridSpec(10, 18, fig)
                    ax.append(fig.add_subplot(self.gs[1:, 1:9]))
                    ax.append(fig.add_subplot(self.gs[1:, 9:17]))
                    self.bar_or = "horizontal"
                    self.nticks = 5
# Only sensor 1 is plotted
        else:
            fig = plt.figure(figsize=(12, 12), layout="constrained")
            self.gs = GridSpec(10, 10, fig)
            ax.append(fig.add_subplot(self.gs[1:, 1:9]))
            self.bar_or = "vertical"
            self.nticks = 10
        matplotlib.rcParams.update({"font.size": 14})
        self.axfont = 12
        plt.rc("xtick", labelsize=self.axfont)
        plt.rc("ytick", labelsize=self.axfont)

# Eliminate possible nans (coming from function clean_data) for both sensors
        x1 = np.copy(x)
        y1 = np.copy(y)
        s1 = np.copy(v1)
        if self.grad_data:
            x2 = np.copy(x)
            y2 = np.copy(y)
            s2 = np.copy(v2)
            x3 = np.copy(x)
            y3 = np.copy(y)
            s3 = s2 - s1

            index = np.isfinite(s1) & np.isfinite(s2)
            x3 = x3[index]
            y3 = y3[index]
            s3 = s3[index]
            x2 = np.delete(x2, np.isnan(s2))
            y2 = np.delete(y2, np.isnan(s2))
            s2 = np.delete(s2, np.isnan(s2))
        x1 = np.delete(x1, np.isnan(s1))
        y1 = np.delete(y1, np.isnan(s1))
        s1 = np.delete(s1, np.isnan(s1))

# Do plot for sensor 1
        if self.grad_data:
            if ";" in title[:-1]:
                t = title.split(";")
                txt = t[0] + " Sensor 1;" + t[1]
            else:
                txt = title + " Sensor 1"
        else:
            txt = title
        self.plot_sensor_triang(ax[0], x1, y1, s1, mincol1, maxcol1, percent,
                                c, xlabel, ylabel, txt,
                                f"Field strength [{self.unit}]",
                                dec=data["line_declination"])
# Do plot for sensor 2
        if self.grad_data:
            if ";" in title[:-1]:
                t = title.split(";")
                txt = t[0] + " Sensor 2;" + t[1]
            else:
                txt = title + " Sensor 2"
            self.plot_sensor_triang(ax[1], x2, y2, s2, mincol2, maxcol2,
                                    percent, c, xlabel, ylabel, txt,
                                    f"Field strength [{self.unit}]",
                                    dec=data["line_declination"])
# plot vertical gradient
            if grad_flag:
                if ";" in title[:-1]:
                    t = title.split(";")
                    txt = t[0] + " Gradient;" + t[1]
                else:
                    txt = title + " Gradient"
                self.plot_sensor_triang(ax[2], x3, y3, s3, mincolg, maxcolg,
                                        percent, c, xlabel, ylabel, txt,
                                        f"Field gradient [{self.unit}/m]",
                                        dec=data["line_declination"])
# Erase actual plot in central widget and plot the new one
        self.rmMPL()
        self.addMPL(fig)
        return fig, ax

    def plot_sensor_image(self, ax, x, y, s, vmin, vmax, percent, cmap,
                          xlabel, ylabel, title, cbar_title, dec=0.0):
        """
        Plot map of one sensor by triangulation

        Parameters
        ----------
        ax : Matplotlib axis
            Axis where to plot the map
        x : Numpy 1D float array
            X-coordinates of data columns
        y : Numpy 1D float array
            Y-coordinates of data rows
        s : Numpy 2D float array
            Values [nT or mGal] on a regular grid
        vmin : float
            Value for lower end of color scale [nT or mGal]
            If vmin==vmax, the color scale is calculated automatically based on
            quantiles (see "percent")
        vmax : float
            Value for upper end of color scale [nT or mGal]
        percent : float
            Scaling of color scale. Maximum value is percentile (1-percent),
            minimum value for percentile percent. This is only used if
            mincol==maxcol.
        cmap : Matplotlib color map
            Color map to be used
        xlabel : str
            Label for x-axis
        ylabel : str
            Label for y-axis
        title : str
            Title of map
        cbar_title : str
            Text for color bar
        dec : float (optional, default : 0.)
            Direction of the measurement lines with respect to magnetic North
            in degrees, measured from N to E

        Returns
        -------
        None.

        """
        self.legend = []
        matplotlib.rcParams.update({"font.size": 16})
        axfont = 12
        matplotlib.rcParams.update({"font.size": 16})
        plt.rc("xtick", labelsize=axfont)
        plt.rc("ytick", labelsize=axfont)
# Calculate color scale
        if vmin == vmax:
            if percent > 0:
                max_col = np.nanquantile(s, 1 - percent)
                min_col = np.nanquantile(s, percent)
            else:
                max_col = np.nanmax(s)
                min_col = np.nanmin(s)
        else:
            max_col = vmax
            min_col = vmin
        rd = int(np.ceil(-np.log10(max_col - min_col))) + 2
        xmin = np.nanmin(x)
        xmax = np.nanmax(x)
        ymin = np.nanmin(y)
        ymax = np.nanmax(y)
        dx2 = (x[1] - x[0]) / 2
        dy2 = (y[1] - y[0]) / 2
        im1 = ax.imshow(np.flip(s, axis=0), cmap=cmap, aspect="equal",
                        extent=[xmin-dx2, xmax+dx2, ymin-dy2, ymax+dy2],
                        vmin=min_col, vmax=max_col)
        if self.grad_data:
            ax.set_title(title, fontsize=14)
        else:
            ax.set_title(title, fontsize=14)
        ax.set_xlabel(xlabel, fontsize=axfont)
        ax.set_ylabel(ylabel, fontsize=axfont)
        ax.tick_params(labelsize=axfont)
        if self.grid_flag:
            ax.grid(visible=True, which="both")
        if self.plotLin_flag:
            self.plot_lineaments(ax)
        ax.set_xlim([xmin, xmax])
        ax.set_ylim([ymin, ymax])
        ax.xaxis.set_minor_locator(AutoMinorLocator())
        ax.yaxis.set_minor_locator(AutoMinorLocator())
        if self.bar_or == "vertical":
            cax = ax.inset_axes([1.05, 0.05, 0.02, 0.9],
                                transform=ax.transAxes)
        else:
            cax = ax.inset_axes([0.05, -0.2, 0.9, 0.05],
                                transform=ax.transAxes)
        smin = np.round(np.nanmin(s), rd)
        smax = np.round(np.nanmax(s), rd)
        ssmin = min_col
        ssmax = max_col
        ds = (ssmax - ssmin) / self.nticks
        ticks = np.round(np.arange(ssmin, ssmax + ds / 2, ds), rd)
        ticks = list(ticks)
        labels = []
        for t in ticks:
            labels.append(f"{t}")
        cbar = plt.colorbar(im1, orientation=self.bar_or, cax=cax,
                            fraction=0.1, ticks=ticks, extend="both")
        if self.bar_or == "vertical":
            cbar.ax.set_ylabel(cbar_title, size=10)
            cbar.ax.text(0.0, -0.06, f"{smin}", verticalalignment="top",
                         horizontalalignment="left",
                         transform=cbar.ax.transAxes, fontsize=10)
            cbar.ax.text(0.0, 1.06, f"{smax}", verticalalignment="bottom",
                         horizontalalignment="left",
                         transform=cbar.ax.transAxes, fontsize=10)
        else:
            cbar.ax.set_xlabel(cbar_title, size=10)
            cbar.ax.text(0.0, 1.0, f"{smin}", verticalalignment="bottom",
                         horizontalalignment="right",
                         transform=cbar.ax.transAxes, fontsize=10)
            cbar.ax.text(1.0, 1.0, f"{smax}", verticalalignment="bottom",
                         horizontalalignment="left",
                         transform=cbar.ax.transAxes, fontsize=10)
        ticklabs = cbar.ax.get_yticklabels()
        cbar.ax.set_yticklabels(ticklabs, fontsize=10)
        ticklabs = cbar.ax.get_xticklabels()
        cbar.ax.set_xticklabels(ticklabs, fontsize=10)
        if self.geography_flag:
            self.plot_geography(ax)
        # ax[0].set_aspect('equal', adjustable='box', anchor=anchor)
        ax.set_aspect("equal", adjustable="box")
        if self.plotLin_flag:
            ax.legend(bbox_to_anchor=(1, 1), loc="upper right", fontsize=10)
        self.plot_north(ax, -dec, "tl")

    def plot_image(self, title="Measured magnetic data", xlabel="Easting",
                   ylabel="Northing", percent=0.01, c="rainbow", mincol1=0,
                   maxcol1=0, mincol2=0.0, maxcol2=0.0, mincolg=0.0,
                   maxcolg=0.0, grad_flag=False, dec=0.0):
        """
        Plot maps of interpolated data of both sensors using imshow

        Parameters
        ----------
        title : str, optional. Default is "Measured magnetic data"
            Plot title for both sensor polts (the text "sensor n" is
            automatically added, n being sensor numnber).
        xlabel : str, optional
            Text for x-axis. The default is "Easting".
        ylabel : str, optional
            Text for y-axis. The default is "Northing".
        percent : float, optional
            Scaling of color scale. Maximum value is percentile (1-percent),
            minimum value for percentile percent. The default is 0.01.
        mincol1 : float, optional
            value for lower end of color scale for sensor 1 [nT]
        maxcol1 : float, optional
            value for upper end of color scale for sensor 1 [nT]
            If mincol1==maxcol1, the color scale is calculated automatically
            based on quantiles (see "percent")
        mincol2 : float, optional
            value for lower end of color scale for sensor 2 [nT]
        maxcol2 : float, optional
            value for upper end of color scale for sensor 2 [nT]
            If mincol2==maxcol2, the color scale is calculated automatically
            based on quantiles (see "percent")
        mincolg : float, optional
            value for lower end of color scale for vertical gradient [nT/m]
        maxcolg : float, optional
            value for upper end of color scale for vertical gradient [nT/m]
            If mincolg==maxcolg, the color scale is calculated automatically
            based on quantiles (see "percent")
        c : str, optional
            Color map to be used. The default is "rainbow".
        grad_flag: bool, optional, default: False
            If True, 3 plots are shown on the screen: Sensor1, sensor2 and
            gradient. If False only the two sensors are plotted.
        dec : float
            Y direction with respect to geographic north (measured from N to E)

        Returns
        -------
        fig : matplotlib.figure
            Figure used for plot.
        ax : matplotlib.axis
            List of axes used for plots. ax has two entrances, one for each
            sensor

        """
        self.legend = []
        ax = []
        ddx = self.main.x_inter.max() - self.main.x_inter.min()
        ddy = self.main.y_inter.max() - self.main.y_inter.min()
# Gradientplotted
# Vertical layout
        if self.grad_data:
            if grad_flag:
                if ddx > 2.0 * ddy:
                    fig = plt.figure(figsize=(14, 12), layout="constrained")
                    self.gs = GridSpec(26, 10, fig)
                    ax.append(fig.add_subplot(self.gs[1:9, 1:]))
                    ax.append(fig.add_subplot(self.gs[9:17, 1:]))
                    ax.append(fig.add_subplot(self.gs[17:25, 1:]))
                    self.bar_or = "vertical"
                    # anchor = 'E'
                    self.nticks = 10
# Horizontal layout
                else:
                    fig = plt.figure(figsize=(26, 12), layout="constrained")
                    self.gs = GridSpec(10, 26, fig)
                    ax.append(fig.add_subplot(self.gs[1:, 1:9]))
                    ax.append(fig.add_subplot(self.gs[1:, 9:17]))
                    ax.append(fig.add_subplot(self.gs[1:, 17:25]))
                    self.bar_or = "horizontal"
                    # anchor = 'S'
                    self.nticks = 4
# Gradient not plotted
# Vertical layout
            else:
                if ddx > 1.5 * ddy:
                    fig = plt.figure(figsize=(14, 12), layout="constrained")
                    self.gs = GridSpec(18, 10, fig)
                    ax.append(fig.add_subplot(self.gs[1:9, 1:]))
                    ax.append(fig.add_subplot(self.gs[9:17, 1:]))
                    self.bar_or = "vertical"
                    # anchor = 'E'
                    self.nticks = 10
# Horizontal layout
                else:
                    fig = plt.figure(figsize=(18, 12), layout="constrained")
                    self.gs = GridSpec(10, 18, fig)
                    ax.append(fig.add_subplot(self.gs[1:, 1:9]))
                    ax.append(fig.add_subplot(self.gs[1:, 9:17]))
                    self.bar_or = "horizontal"
                    # anchor = 'S'
                    self.nticks = 5
        else:
            fig = plt.figure(figsize=(12, 12), layout="constrained")
            self.gs = GridSpec(10, 10, fig)
            ax.append(fig.add_subplot(self.gs[1:, 1:9]))
            self.bar_or = "vertical"
            # anchor = 'E'
            self.nticks = 10

# Do plot for sensor 1
        if self.grad_data:
            if ";" in title[:-1]:
                t = title.split(";")
                txt = t[0] + " Sensor 1;" + t[1]
            else:
                txt = title + " Sensor 1"
        else:
            txt = title
        self.plot_sensor_image(ax[0], self.main.x_inter, self.main.y_inter,
                               self.main.sensor1_inter, mincol1, maxcol1,
                               percent, c, xlabel, ylabel, txt,
                               f"Field strength [{self.unit}]", dec=dec)

# Do plot for sensor 2
        if self.grad_data:
            if ";" in title[:-1]:
                t = title.split(";")
                txt = t[0] + " Sensor 2;" + t[1]
            else:
                txt = title + " Sensor 2"
            self.plot_sensor_image(ax[1], self.main.x_inter, self.main.y_inter,
                                   self.main.sensor2_inter, mincol2, maxcol2,
                                   percent, c, xlabel, ylabel, txt,
                                   f"Field strength [{self.unit}]", dec=dec)
# Do plot for gradient
            if grad_flag:
                if ";" in title[:-1]:
                    t = title.split(";")
                    txt = t[0] + " Gradient;" + t[1]
                else:
                    txt = title + " Gradient"
                self.plot_sensor_image(ax[2], self.main.x_inter,
                                       self.main.y_inter, self.main.grad_inter,
                                       mincolg, maxcolg, percent, c, xlabel,
                                       ylabel, txt,
                                       f"Gradient [{self.unit}/m]", dec=dec)
# Erase actual plot in central widget and plot the new one
        self.rmMPL()
        self.addMPL(fig)
        return fig, ax

    def addMPL(self, fig):
        """
        Add widget to actual Figure

        Parameters
        ----------
        fig : matplotlib.figure.Figure object
            Actually used Figure

        """
        self.canvas = FigureCanvas(fig)
        self.mplvl.addWidget(self.canvas)
        self.canvas.draw()
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.mplvl.addWidget(self.toolbar)

    def rmMPL(self):
        """
        Remove widget from actual Figure
        """
        self.mplvl.removeWidget(self.canvas)
        self.canvas.close()
        self.mplvl.removeWidget(self.toolbar)
        self.toolbar.close()

    def plotFloating(self, data, x, y, wtitle="", sizeh=800, sizev=500,
                     mincol=0, maxcol=0, percent=0, c="rainbow", ptitle="",
                     xlabel="", ylabel="", clabel=""):
        """
        Plot one or several 2D arrays into floating window

        Parameters
        ----------
        data : numpy array
            Data to be plotted.
            The array my be 2D or 3D. If 3D, it is supposed that several
            figures should be plotted into the same window in different frames.
            If more than one plot is to be done, the thrid dimension contains
            the different data sets. Every data set must be 2D. Several data
            sets may be concatenated into data with the following commands:

            - data = data1.reshape(nr,nc,1)
            - data = np.concatenate((data,data2.reshape(nr,nc,1)),axis=2)

            data1 and data2 are arrays with shape (nr,nc) defined on regular
            grids.

        x : numpy 1D float array
            Positions of the columns
        y : numpy 1D float array
            Positions of the rows
        wtitle : str optional, default: empty string
            Title of floating window
        sizeh : float optional,default: 800
            horizontal size of floating window.
        sizev : float optional, default: 500
            vertical size of floating window
        mincol : float optional, default: 0
            Minimum value of color scale
        maxcol : float optional,  default: 0
            Maximum value of color scale.
            If mincol == maxcol,  and percent == 0, the limits of the color
            scale are minimum and maximum values of the data.
        percent : float optional:
            If >0, mincol and maxcol are calculated as quantiles
            (percent, 1-percent).
        c: str optional, default: "rainbow"
            color scale to be used.
        ptitle : str, optional, default: empty string
            May be a single string or a list of strings, where the length of
            the list must correspond to the length of the third dimension of
            data.
        xlabel : str, optional
            Similar as ptitle for lables of horizontal axis
        ylabel : str, optional
            Similar as ptitle for lables of vertical axis
        clabel : str, optional
            Similar as ptitle for lables of color bars

        Returns
        -------
        fig_float,ax_float: Matplot values of figure and axes

        """
# Only 2D arrays may be plotted, test if 1D data are passed to the routine
        if data.ndim < 2:
            _ = QtWidgets.QMessageBox.warning(
                None, "Warning",
                "Function plotFloating is not prepared for 1D plots",
                QtWidgets.QMessageBox.Close, QtWidgets.QMessageBox.Close)
            return False
# Create figure
        fig_float = newWindow(wtitle, sizeh, sizev)
        fig_float.fig.tight_layout()
# If 2D array is passed create single axis
        if data.ndim == 2:
            ax_float = fig_float.fig.subplots(1, 1)
            data1 = np.copy(data)
            bar_or = "vertical"
            # anchor = 'E'
            nticks = 10
# If 3D array is passed create 2 or 3 axis depending on the shape of data
        else:
            ddx = x.max() - x.min()
            ddy = y.max() - y.min()
            data1 = data[:, :, 0]
# If horizontal extension is > 1.5x vertical one, plot axes vertically one
#    above the next. If not plot axis in horizontal direction
            if data.shape[2] == 3:
                facx = sizeh / (3 * ddx)
                facy = sizev / (3 * ddy)
                if facx < facy:
                    ax_float = fig_float.fig.subplots(3, 1)
                    bar_or = "vertical"
                    # anchor = 'E'
                    nticks = 10
                else:
                    ax_float = fig_float.fig.subplots(1, 3)
                    bar_or = "horizontal"
                    # anchor = 'S'
                    nticks = 6
            else:
                facx = sizeh / (2 * ddx)
                facy = sizev / (2 * ddy)
                if facx < facy:
                    ax_float = fig_float.fig.subplots(2, 1)
                    bar_or = "vertical"
                    # anchor = 'E'
                    nticks = 10
                else:
                    ax_float = fig_float.fig.subplots(1, 2)
                    bar_or = "horizontal"
                    # anchor = 'S'
                    nticks = 6
# Calculate color scale for both sensors independently
        rd = int(np.ceil(-np.log10(np.nanmax(abs(data1))))) + 2
        if mincol == maxcol:
            if percent > 0:
                max_col = np.round(np.nanquantile(data1, 1 - percent), rd)
                min_col = np.round(np.nanquantile(data1, percent), rd)
            else:
                max_col = np.nanmax(data1)
                min_col = np.nanmin(data1)
        else:
            max_col = maxcol
            min_col = mincol
# Plot first into axis ax_float[0]
        try:
            ax = ax_float[0]
            pt = ptitle[0]
            xl = xlabel[0]
            yl = ylabel[0]
            cl = clabel[0]
# If only one subplot has been created
        except TypeError:
            ax = ax_float
            pt = ptitle
            xl = xlabel
            yl = ylabel
            cl = clabel
        dx2 = (x[1] - x[0]) / 2
        dy2 = (y[1] - y[0]) / 2
        im1 = ax.imshow(
            np.flip(data1, axis=0),
            cmap=c,
            aspect="equal",
            extent=[np.min(x)-dx2, np.max(x)+dx2,
                    np.min(y)-dy2, np.max(y)+dy2],
            vmin=min_col, vmax=max_col)
        ax.set_title(pt)
        ax.set_xlabel(xl)
        ax.set_ylabel(yl)
        if bar_or == "vertical":
            cax = ax.inset_axes([1.015, 0.05, 0.015, 0.9],
                                transform=ax.transAxes)
        else:
            cax = ax.inset_axes([0.05, -0.15, 0.9, 0.05],
                                transform=ax.transAxes)
        smin = np.round(np.nanmin(data1), rd)
        smax = np.round(np.nanmax(data1), rd)
        ssmin = min_col
        ssmax = max_col
        ds = (ssmax - ssmin) / nticks
        ticks = np.round(np.arange(ssmin, ssmax + ds / 2, ds), rd)
        ticks = list(ticks)
        # cbar = plt.colorbar(
        cbar = fig_float.fig.colorbar(im1, orientation=bar_or, ax=ax, cax=cax,
                                      fraction=0.1, extend="both", ticks=ticks)
        if bar_or == "vertical":
            cbar.ax.set_ylabel(cl)
            cbar.ax.text(0.0, -0.075, f"{smin}", verticalalignment="top",
                         horizontalalignment="left",
                         transform=cbar.ax.transAxes)
            cbar.ax.text(0.0, 1.075, f"{smax}", verticalalignment="bottom",
                         horizontalalignment="left",
                         transform=cbar.ax.transAxes)
        else:
            cbar.ax.set_xlabel(cl)
            cbar.ax.text(0.0, 1.0, f"{smin}", verticalalignment="bottom",
                         horizontalalignment="right",
                         transform=cbar.ax.transAxes)
            cbar.ax.text(1.0, 1.0, f"{smax}", verticalalignment="bottom",
                         horizontalalignment="left",
                         transform=cbar.ax.transAxes)
        if self.grid_flag:
            ax.grid(visible=True)
        # ax.set_aspect('equal', adjustable='box', anchor=anchor)
        ax.set_aspect("equal", adjustable="box")
# If more than one map has to be plotted, do this now
        if data.ndim > 2:
            if data.shape[2] > 1:
                data1 = data[:, :, 1]
                rd = int(np.ceil(-np.log10(np.nanmax(abs(data1))))) + 2
                if mincol == maxcol:
                    if percent > 0:
                        max_col = np.round(np.nanquantile(data1, 1-percent),
                                           rd)
                        min_col = np.round(np.nanquantile(data1, percent), rd)
                    else:
                        max_col = np.nanmax(data1)
                        min_col = np.nanmin(data1)
                else:
                    max_col = maxcol
                    min_col = mincol
                im1 = ax_float[1].imshow(np.flip(data1, axis=0), cmap=c,
                                         aspect="equal",
                                         extent=[np.min(x) - dx2,
                                                 np.max(x) + dx2,
                                                 np.min(y) - dy2,
                                                 np.max(y) + dy2],
                                         vmin=min_col, vmax=max_col)
                ax_float[1].set_title(ptitle[1])
                ax_float[1].set_xlabel(xlabel[1])
                ax_float[1].set_ylabel(ylabel[1])
                if self.grid_flag:
                    ax_float[1].grid(visible=True)
                if bar_or == "vertical":
                    cax = ax_float[1].inset_axes(
                        [1.015, 0.05, 0.015, 0.9],
                        transform=ax_float[1].transAxes)
                else:
                    cax = ax_float[1].inset_axes(
                        [0.05, -0.15, 0.9, 0.05],
                        transform=ax_float[1].transAxes)
                smin = np.round(np.nanmin(data1), rd)
                smax = np.round(np.nanmax(data1), rd)
                ssmin = min_col
                ssmax = max_col
                ds = (ssmax - ssmin) / nticks
                ticks = np.round(np.arange(ssmin, ssmax + ds / 2, ds), rd)
                ticks = list(ticks)
                # cbar = plt.colorbar(
                cbar = fig_float.fig.colorbar(im1, orientation=bar_or, ax=ax,
                                              cax=cax, fraction=0.1,
                                              extend="both", ticks=ticks)
                if bar_or == "vertical":
                    cbar.ax.set_ylabel(clabel[1])
                    cbar.ax.text(0.0, -0.075, f"{smin}",
                                 verticalalignment="top",
                                 horizontalalignment="left",
                                 transform=cbar.ax.transAxes)
                    cbar.ax.text(0.0, 1.075, f"{smax}",
                                 verticalalignment="bottom",
                                 horizontalalignment="left",
                                 transform=cbar.ax.transAxes)
                else:
                    cbar.ax.set_xlabel(clabel[1])
                    cbar.ax.text(0.0, 1.0, f"{smin}",
                                 verticalalignment="bottom",
                                 horizontalalignment="right",
                                 transform=cbar.ax.transAxes)
                    cbar.ax.text(1.0, 1.0, f"{smax}",
                                 verticalalignment="bottom",
                                 horizontalalignment="left",
                                 transform=cbar.ax.transAxes)
                # ax_float[1].set_aspect('equal', adjustable='box',
                #                        anchor=anchor)
                ax_float[1].set_aspect("equal", adjustable="box")
                if data.shape[2] > 2:
                    data1 = data[:, :, 2]
                    rd = int(np.ceil(-np.log10(np.nanmax(abs(data1))))) + 2
                    if mincol == maxcol:
                        if percent > 0:
                            max_col = np.round(np.nanquantile(
                                data1, 1-percent), rd)
                            min_col = np.round(np.nanquantile(data1, percent),
                                               rd)
                        else:
                            max_col = np.nanmax(data1)
                            min_col = np.nanmin(data1)
                    else:
                        max_col = maxcol
                        min_col = mincol
                    im1 = ax_float[2].imshow(np.flip(data1, axis=0), cmap=c,
                                             aspect="equal",
                                             extent=[np.min(x) - dx2,
                                                     np.max(x) + dx2,
                                                     np.min(y) - dy2,
                                                     np.max(y) + dy2],
                                             vmin=min_col, vmax=max_col)
                    ax_float[2].set_title(ptitle[2])
                    ax_float[2].set_xlabel(xlabel[2])
                    ax_float[2].set_ylabel(ylabel[2])
                    if self.grid_flag:
                        ax_float[2].grid(visible=True)
                    if bar_or == "vertical":
                        cax = ax_float[2].inset_axes(
                            [1.015, 0.05, 0.015, 0.9],
                            transform=ax_float[2].transAxes)
                    else:
                        cax = ax_float[2].inset_axes(
                            [0.05, -0.15, 0.9, 0.05],
                            transform=ax_float[2].transAxes)
                    smin = np.round(np.nanmin(data1), rd)
                    smax = np.round(np.nanmax(data1), rd)
                    ssmin = min_col
                    ssmax = max_col
                    ds = (ssmax - ssmin) / nticks
                    ticks = np.round(np.arange(ssmin, ssmax + ds / 2, ds), rd)
                    ticks = list(ticks)
                    # cbar = plt.colorbar(
                    cbar = fig_float.fig.colorbar(im1, orientation=bar_or,
                                                  ax=ax, cax=cax, fraction=0.1,
                                                  extend="both", ticks=ticks)
                    if bar_or == "vertical":
                        cbar.ax.set_ylabel(clabel[2])
                        cbar.ax.text(0.0, -0.075, f"{smin}",
                                     verticalalignment="top",
                                     horizontalalignment="left",
                                     transform=cbar.ax.transAxes)
                        cbar.ax.text(0.0, 1.075, f"{smax}",
                                     verticalalignment="bottom",
                                     horizontalalignment="left",
                                     transform=cbar.ax.transAxes)
                    else:
                        cbar.ax.set_xlabel(clabel[2])
                        cbar.ax.text(0.0, 1.0, f"{smin}",
                                     verticalalignment="bottom",
                                     horizontalalignment="right",
                                     transform=cbar.ax.transAxes)
                        cbar.ax.text(1.0, 1.0, f"{smax}",
                                     verticalalignment="bottom",
                                     horizontalalignment="left",
                                     transform=cbar.ax.transAxes)
                # ax_float[2].set_aspect('equal', adjustable='box',
                #                        anchor=anchor)
                    ax_float[2].set_aspect("equal", adjustable="box")
        fig_float.show()
        return fig_float, ax_float

    def get_mouse_click(self, fig):
        """
        wait for a mouse click within figure "fig".

        Parameters
        ----------
        fig : matplotlib figure
            for main window, it must be self.w.mplvl
            for floating window, it is the name that has been given to the
            window at creation time

        Returns
        -------
        event.
        Mouse position, button pressed and the general event parameters are
        accessible through event.xdata, event.ydata, event.button and
        others like event.x or event.y

        """
        self.wait = True
        self.click = False
        self.press = False

        def onClick(event):
            self.wait = False
            self.click = True
            self.event = event
            self.x_mouse = event.xdata
            self.y_mouse = event.ydata
            self.mouse = event.button
            self.xwin = event.x
            self.ywin = event.y

        fig.canvas.mpl_connect("button_press_event", onClick)
        while self.wait:
            QtCore.QCoreApplication.processEvents()
        return self.event

    def get_event(self, fig):
        """
        wait for a mouse click of keyboard press within figure "fig".

        Parameters
        ----------
        fig : matplotlib figure
            for main window, it must be self.w.mplvl
            for floating window, it is the name that has been given to the
            window at creation time

        Returns
        -------
        event.
        Mouse position, button pressed and the general event parameters are
        accessible through event.xdata, event.ydata, event.button and
        others like event.x or event.y

        """
        self.wait = True

        def onClick(event):
            self.wait = False
            self.event = event

        fig.canvas.mpl_connect("button_press_event", onClick)
        fig.canvas.mpl_connect("key_press_event", onClick)
        while self.wait:
            QtCore.QCoreApplication.processEvents()
        return self.event

    def setHelp(self, text, fig):
        """
        Set help text at bottom of screen.

        Parameters
        ----------
        text : str
            Text to be printed (defined in __init__)
            Text is written in QLabel widget. In order to keep the widget at
            the bottom of the screen, the existing one is first erased and
            then reopened. This call has to be done after any modification of
            the graphics window.

        fig : Matplotlib Figure
            Figure where to write the help text.

        Returns
        -------
        None
        """
        try:
            self.help.close()
        except (AttributeError, RuntimeError):
            pass
        self.help = QtWidgets.QLabel(self)
        self.help.setMaximumHeight(15)
        if fig == self.mplvl:
            fig.addWidget(self.help)
        else:
            fig.layout.addWidget(self.help)
        self.help.show()
        self.help.setText(text)

    def followLine(self, fig, ax, release_flag=False, nleft=1, nright=1):
        """
        Pull line across plot
        Parameters
        ----------
        fig, ax : names of figures and axis where to follow the line
        release_flag (boolean): If True, end of line when left button released\
                                if False, end of line triggered by pressing
                                right button
        nleft (int): if 0 start line for negative direction at origin \
                     if not, start line at the position of first click
        nright (int): if 0 start line for positive direction at origin \
                     if not, start line at the position of first click

        Returns
        -------
        event : QT mouse event
            Information concerning the last mouse event.
            Mainly useful are event.button (mouse button pressed/released);
            event.xdata and event.ydata: coordinates of last mouse position in
            axis coordinate system (e.g. meters);
            event.x and event.y: coordinates of last mouse position in
            window coordinates (pixels)

        coor_x and coor_y: list of floats
            coordinates (axis coordinate system) of line segment(s)

        Mouse button pressed to exit sunction (may be 2 for wheel ar 3
        for right button)

        Left button adds new point. right button finishes. Wheel erases last
        clicked point or, if no points are available, returns
        """
        global figure

        def onPress(event):
            global figure
            self.event = event
            self.line_click = False
# left mouse button is pressed
            if event.button == 1:
                if event.xdata is None or event.ydata is None:
                    self.mouse = 1
                    self.x_event = event.xdata
                    self.y_event = event.ydata
                    return
                if len(self.coor_x) == 0:
                    if (event.xdata < 0 and nleft == 0) or \
                            (event.xdata >= 0 and nright == 0):
                        self.start = [0, 0]
                        self.coor_x.append(0)
                        self.coor_y.append(0)
                    else:
                        self.start = [event.xdata, event.ydata]
                        self.coor_x.append(event.xdata)
                        self.coor_y.append(event.ydata)
                    if event.xdata < 0:
                        self.side = -1
                    else:
                        self.side = 1
                    self.background = figure.canvas.copy_from_bbox(figure.bbox)
# set starting point initially also as end point
                self.coor_x.append(event.xdata)
                self.coor_y.append(event.ydata)
                self.canvas_follow = self.line.figure.canvas
                self.axl = self.line.axes
                self.line.set_data(self.coor_x, self.coor_y)
                self.axl.draw_artist(self.line)
# set action on mouse motion
                self.cidmotion = self.line.figure.canvas.mpl_connect(
                    "motion_notify_event", onMotion)
# set action on mouse release
                if release_flag:
                    self.cidrelease = self.line.figure.canvas.mpl_connect(
                        "button_release_event", onRelease)
# if right button is pressed, finish
            elif event.button == 3:
                self.mouse = 3
                self.x_event = event.xdata
                self.y_event = event.ydata
                try:
                    self.line.figure.canvas.mpl_disconnect(self.cidpress)
                except NameError:
                    pass
                self.line_click = False
                try:
                    self.line.figure.canvas.mpl_disconnect(self.cidmotion)
                except NameError:
                    pass
                if len(self.coor_x) > 0:
                    self.line_click = True
                self.line.set_animated(False)
                if self.line_click:
                    figure.canvas.restore_region(self.background)
                self.background = None
                self.released = True
                return
# Wheel is pressed, erase last point
            else:
                if len(self.coor_x) > 0:
                    print(f"Erase point ({self.coor_x[-1]},{self.coor_y[-1]})")
                    del self.coor_x[-1]
                    del self.coor_y[-1]
                    self.canvas_follow = self.line.figure.canvas
                    self.axl = self.line.axes
                    self.line.set_data(self.coor_x, self.coor_y)
                    self.axl.draw_artist(self.line)
# set action on mouse motion
                    self.cidmotion = self.line.figure.canvas.mpl_connect(
                        "motion_notify_event", onMotion)
                else:
                    self.mouse = 2
                    self.x_event = event.xdata
                    self.y_event = event.ydata
                    try:
                        self.line.figure.canvas.mpl_disconnect(self.cidpress)
                    except NameError:
                        pass
                    self.line_click = False
                    try:
                        self.line.figure.canvas.mpl_disconnect(self.cidmotion)
                    except NameError:
                        pass
                    if len(self.coor_x) > 0:
                        self.line_click = True
                    self.line.set_animated(False)
                    if self.line_click:
                        figure.canvas.restore_region(self.background)
                    self.background = None
                    self.released = True
                    return

        def onRelease(event):
            """
            When mouse is released, finish line segment

            Parameters
            ----------
            event : QT mouse event
                Not really needed, but necessary for routine call

            Returns
            -------
            None.

            """
# If line finishes when button is released do this here
            global figure
            self.line.figure.canvas.mpl_disconnect(self.cidpress)
            self.line.figure.canvas.mpl_disconnect(self.cidmotion)
            self.line.figure.canvas.mpl_disconnect(self.cidrelease)
            self.line.set_animated(False)
            if len(self.coor_x) > 0:
                figure.canvas.restore_region(self.background)
            self.background = None
            self.released = True
            return False

        def onMotion(event):
            """
            When mouse is moved, redraw the line from the fixed starting point
            to the new mouse position

            Parameters
            ----------
            event : QT mouse event
                contains mainly coordinates of new mouse position

            Returns
            -------
            None.

            """
            global figure
            self.event = event
            if event.xdata is None or event.ydata is None:
                return False
# set second point of line as actual mouse position
            self.coor_x[-1] = event.xdata
            self.coor_y[-1] = event.ydata
# Draw new line
            self.line.set_data(self.coor_x, self.coor_y)
            self.line.set_color("k")
            self.canvas_follow = self.line.figure.canvas
            self.axl = self.line.axes
            figure.canvas.restore_region(self.background)
            self.axl.draw_artist(self.line)
            self.canvas_follow.blit(self.axl.bbox)
            return True

# set flags and initialize coordinates
        self.released = False
        self.start = []
        self.coor_x = []
        self.coor_y = []
        figure = fig
        (self.line,) = ax.plot(self.coor_x, self.coor_y, "k", animated=True)
        # set action on mouse motion
        # self.cidmotion = self.line.figure.canvas.mpl_connect(
        #     "motion_notify_event", onMotion)
        self.cidpress = self.line.figure.canvas.mpl_connect(
            "button_press_event", onPress)
# As long as release flag is not set listen to events
        while self.released is not True:
            QtCore.QCoreApplication.processEvents()
# Return event information and vector of line coordinates
        return self.event, self.coor_x, self.coor_y


class newWindow(QWidget):
    """
    This "window" is a QWidget. If it has no parent, it will appear as a
    free-floating window.
    """

    def __init__(self, title, xsize=1800, ysize=1200, width=15, height=9):
        """
        Initialize a floating window

        Parameters
        ----------
        title : str
            Title of figure window
        xsize, ysize : integers, optional. Defaults: 1800 and 1200
            width and height of figure window in pixels
        width, height : floats, optional. Defaults 15 and 9
            width and height of figure itself in cm
        """
        super().__init__()
        self.fig = plt.figure(figsize=(width, height))
        self.fig.tight_layout()
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.resize(xsize, ysize)
        self.setWindowTitle(title)
        self.canvas = FigureCanvas(self.fig)
        self.layout.addWidget(self.canvas)
        self.canvas.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.cid_enter = self.canvas.mpl_connect("axes_enter_event",
                                                 self.on_enter_event)
        self.canvas.draw()
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.layout.addWidget(self.toolbar)

    def on_enter_event(self, event):
        self.canvas.setFocus()
