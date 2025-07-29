import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.axes import Axes  # 基础类型
import scienceplots


def thesis_plot(figwidth: float=1):
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

def linear_fit_plt(ax_handle: Axes, x_array :list[float], y_array: list[float], gain: float, legend_list: list[float], lable_tuple: tuple[str], unit_str: str):
    """
        绘制输入x和y数据的去中心散点图，并且进行线性拟合，绘制拟合曲线，打印拟合斜率。(主要用于温漂拟合和数据绘图）

        Args:
            ax_handle (Axes): 绘图轴句柄
            x_array (array): x坐标数据
            y_array (array): y坐标数据
            gain(float): y坐标增益，绘图和计算斜率时除以此增益
            legend_list(list[str]):数据和拟合的图例名称字符串列表
            lable_tuple(truple(str)):x和y坐标的标签字符串元组
            unit_str(str):拟合斜率单位字符串



        Returns:
            None

        Example:

        """
    voltage_mean = np.mean(y_array)
    y_array = [(x-voltage_mean)/gain for x in y_array]
    slope, intercept = np.polyfit(x_array, y_array, 1)
    slope_uV = slope*1e6
    fitted_temp = np.linspace(np.min(x_array), np.max(x_array), 1000)
    fitted_digital = slope*fitted_temp + intercept



    ax_handle.plot(x_array, y_array, marker='o', ls='None', label= legend_list[0])
    ax_handle.plot(fitted_temp, fitted_digital, lw = 2, label = legend_list[1])
    # 获取当前坐标轴范围
    xmin, xmax = ax_handle.get_xlim()
    ymin, ymax = ax_handle.get_ylim()
    if slope_uV < 0:
        # 动态计算文本位置（例如右上角）
        text_x = xmax - 0.1 * (xmax - xmin)  # 向右偏移10%
        text_y = ymax - 0.1 * (ymax - ymin)  # 向下偏移10%
    else:
        # 动态计算文本位置（例如右下角）
        text_x = xmax - 0.1 * (xmax - xmin)  # 向右偏移10%
        text_y = ymax - 0.8 * (ymax - ymin)  # 向下偏移10%
    # plt.text(text_xy[0], text_xy[1], 'slope: %.3f uV/K' % slope_uV)
    plt.text(text_x, text_y, ('slope: %.3e ' + unit_str) % slope_uV,
             ha='right', va='top',
             bbox=dict(facecolor='white', alpha=0.8))

    #plt.xlabel('Temperature')
    #plt.ylabel('Input Voltage (V)')
    ax_handle.set_xlabel(lable_tuple[0])
    ax_handle.set_ylabel(lable_tuple[1])
    #ax_handle.set_ylabel('Voltage(V)')
    plt.legend()
    plt.grid()