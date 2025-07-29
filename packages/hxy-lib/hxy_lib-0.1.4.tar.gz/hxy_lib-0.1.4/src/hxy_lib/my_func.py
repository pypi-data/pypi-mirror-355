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

def thesis_plot(figwidth=1):
    # Define colormap
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