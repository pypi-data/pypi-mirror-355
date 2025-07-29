import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import mpl_toolkits.axisartist as axisartist
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from matplotlib.ticker import AutoMinorLocator
import pandas as pd
#from pdf2image import convert_from_path
import scipy.linalg as linalg
import scienceplots
import csv
from cProfile import label
#import allantools as alt
import sympy as sp
from scipy import optimize,signal
from datetime import datetime, date, timedelta
from pathlib import Path
from scipy import special
import matplotlib.path as mpath
from scipy.fftpack import fft
from matplotlib.ticker import (MultipleLocator, AutoMinorLocator)
import matplotlib.ticker as ticker
import time
import allantools
from scipy.optimize import curve_fit
from matplotlib.figure import Figure
from matplotlib.axes import Axes  # 基础类型
from typing import Tuple

def thesis_plot(figwidth: float=1) -> Tuple[Figure, Axes]:
    # Define colormap
    """
    规定论文绘图格式

    :parameter
    -----------
    figwidth: int/float
              图像宽度，默认1，表示A4的单栏宽度

    Returns
    -------
    handle
        fig, ax的句柄

    Examples
    --------
    fig, ax = thesis_plot(figwidth=1)
    """
    upper = mpl.cm.Blues(np.arange(256))
    lower = np.ones((int(256/4),4))
    for i in range(3):
        lower[:,i] = np.linspace(1, upper[0,i], lower.shape[0])
    cmap0 = np.vstack(( lower, upper ))
    cmap0 = mpl.colors.ListedColormap(cmap0, name='myColorMap0', N=cmap0.shape[0])

    plt.style.use(['science'])

    plt.rcParams.update({
        "text.usetex": False,
        "font.family": "serif",
        "font.serif": "times new roman",
        "mathtext.fontset":"stix",
        "font.size":10,
        "savefig.bbox": "standard"})
    plt.rcParams['figure.figsize'] = (6.0, 4.0) # 设置figure_size尺寸
    plt.rcParams['image.interpolation'] = 'nearest' # 设置 interpolation style
    plt.rcParams['image.cmap'] = 'gray' # 设置 颜色 style
    plt.rcParams['savefig.dpi'] = 300 #图片像素
    plt.rcParams['figure.dpi'] = 300 #分辨率

    col_width = 3.375  # inch(半个A4宽度)
    fontsize = np.array([10,9,6.7])*2

    fig = plt.figure(figsize=[col_width*1.05*figwidth,col_width*0.75*figwidth],facecolor='w')
    #ax1 = fig.add_axes([0.22, 0.15, 0.75, 0.75])
    ax1 = fig.add_axes([0.15, 0.15, 0.75, 0.75])
    bwidth = 0.75
    ax1.spines['top'].set_linewidth(bwidth)
    ax1.spines['bottom'].set_linewidth(bwidth)
    ax1.spines['left'].set_linewidth(bwidth)
    ax1.spines['right'].set_linewidth(bwidth)
    ax1.xaxis.set_tick_params(which='minor', bottom=True, top=True)
    ax1.yaxis.set_tick_params(which='minor', left=True, right=True)

    ax1.tick_params(axis='both', which='major', length=3, width=0.75, labelsize=6)
    ax1.tick_params(axis='both', which='minor', length=1.5, width=0.75, labelsize=6)

    ax1.grid(which='both',linestyle='--',zorder=0,alpha=0.5)
    return fig, ax1

def time_str_to_seconds(time_str:str)-> int:
    """
        DAQ970的yy:mm:dd:hh:mm:ss字符串数据转为起点为0的秒

        parameter
        -----------
        time_str: str
                  DAQ970的yy:mm:dd:hh:mm:ss时间戳字符串

        Returns
        -------
        int
            以其实时间为0时刻的秒

        Examples
        --------
        second = time_str_to_seconds(time_str)
        """
    dt = datetime.strptime(time_str, "%Y/%m/%d %H:%M:%S")

    # 计算与UNIX纪元(1970-01-01)的时间差
    seconds = (dt - datetime(1970,1,1)).total_seconds()
    return seconds


def calculate_sum(a: int, b: int) -> int:
    """
    计算两个整数的和

    Args:
        a (int): 第一个参数
        b (int): 第二个参数

    Returns:
        int: 两数之和

    Example:
        >>> calculate_sum(2, 3)
        5
    """
    return a + b


def KK_data_read_single(path: str, name: str, begin: int=0, end: int=-1, channel: float='CH2'):
    t = []
    t_data = []
    f_1 = []
    with open(path + name, 'r') as file:
        userlines = file.readlines()
        file.close()
    for line in userlines[begin:end]:
        datetime_obj = datetime.strptime('20' + line.split()[0] + line.split()[1], "%Y%m%d%H%M%S.%f")
        t.append(time.mktime(datetime_obj.timetuple()) + datetime_obj.microsecond / 1E6)
        t_data.append(datetime_obj)
        if channel == 'CH1':
            f_1.append(float(line.split()[3]))
        elif channel == 'CH2':
            f_1.append(float(line.split()[4]))
        elif channel == 'CH3':
            f_1.append(float(line.split()[5]))
        elif channel == 'CH4':
            f_1.append(float(line.split()[6]))

    return t, t_data, f_1