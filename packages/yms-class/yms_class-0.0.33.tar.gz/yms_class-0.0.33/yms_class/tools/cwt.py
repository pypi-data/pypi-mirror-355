import sys

import matplotlib.pyplot as plt
import numpy as np
import pywt
from tqdm import tqdm
import os
from scipy.io import loadmat
'''
num: 图片保存时防止名字重复，通过末尾数字区分
total: 保存的图片总量
start_num: 从csv表格的第几行开始读取（一般从第二行读取，0代表第二行）
space: 读取间隔（我这里是每1024个采样点作为一个样本）
sampling_period: 采样率（根据数据集实际情况设置，比如数据集采样率为12kHz，则sampling_period = 1.0 / 12000）
totalscal: 小波变换尺度（我这里是256）
wavename: 小波基函数（morl用的比较多，还有很多如：cagu8，cmor1-1等等）
'''


def img_time_freq(data, total, start_num, end_num, space, sampling_period, totalscal, wavename, class_name, save_path):
    bar_format = '{percentage:.1f}%| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}{postfix}]'
    for i in tqdm(range(0, total), bar_format=bar_format, file=sys.stdout, colour='green'):
        # 加载数据集
        signal = data[start_num:end_num]
        start_num += space
        end_num += space

        # 计算小波基函数的中心频率fc,然后根据totalscal 计算参数cparam
        # 通过除以np.arange(totalscal, 0, -1) 来生成一系列尺度值，并存储在scales中
        fc = pywt.central_frequency(wavename)
        cparam = 2 * fc * totalscal
        scales = cparam / np.arange(totalscal, 0, -1)

        # 连续小波变换函数
        coefficients, frequencies = pywt.cwt(signal, scales, wavename, sampling_period)

        # 计算变换系数的幅度
        amp = abs(coefficients)

        # 根据采样周期生成时间轴
        t = np.linspace(1, sampling_period, (end_num-start_num), endpoint=False)

        # 绘制时频图
        image_path = os.path.join(save_path, (class_name + '_' + str(i)+'.jpg'))
        plt.figure(figsize=(42 / 100, 42 / 100))
        plt.contourf(t, frequencies, amp, cmap='jet')
        plt.axis('off')  # 去坐标轴
        plt.xticks([])  # 去x轴刻度
        plt.yticks([])  # 去y轴刻度
        # 去白边
        plt.savefig(image_path, bbox_inches='tight', pad_inches=0)
        plt.close()


# def img_time_freq(data, start_num, end_num, space, sampling_period, totalscal, wavename, save_dir):
#     n = data.shape[1]
#     # for i in range(0, n):
#     bar_format = '{percentage:.1f}%| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}{postfix}]'
#     for i in tqdm(range(0, n), bar_format=bar_format):
#         signals = data[:, i]
#         total = int(signals.shape[0] / space)
#         start = start_num
#         end = end_num
#         for j in range(0, total):
#             signal = signals[start:end]
#             start += space
#             end += space
#             # 计算小波基函数的中心频率fc,然后根据totalscal 计算参数cparam
#             # 通过除以np.arange(totalscal, 0, -1) 来生成一系列尺度值，并存储在scales中
#             fc = pywt.central_frequency(wavename)
#             cparam = 2 * fc * totalscal
#             scales = cparam / np.arange(totalscal, 0, -1)
#             # 连续小波变换函数
#             coefficients, frequencies = pywt.cwt(signal, scales, wavename, sampling_period)
#             # 计算变换系数的幅度
#             amp = abs(coefficients)
#             # frequencies.max()
#             # 根据采样周期生成时间轴
#             t = np.linspace(1, sampling_period, 1024, endpoint=False)
#             # 绘制时频图
#             plt.figure(figsize=(42 / 100, 42 / 100))
#             plt.contourf(t, frequencies, amp, cmap='jet')
#             plt.axis('off')  # 去坐标轴
#             plt.xticks([])  # 去x轴刻度
#             plt.yticks([])  # 去y轴刻度
#             # image_name = r"D:\Code\0-data\2-滚刀磨损数据集\工况2(2db)"
#             image_name = os.path.join(save_dir, str(i) + '_' + str(j))
#             plt.savefig("{}_resized.jpg".format(image_name.split(".jpg")[0]), bbox_inches='tight', pad_inches=0)
#             plt.close()


def time_freq(data, num, total, start_num, end_num, space, sampling_period, totalscal, wavename, image_path):
    for i in tqdm(range(0, total)):
        # for i in range(0, total):
        # data = data.loc[start_num:end_num, 'data']
        signals = data[start_num:end_num]
        # 计算小波基函数的中心频率fc,然后根据totalscal 计算参数 cparam
        # 通过除以np.arange(totalscal, 0, -1) 来生成一系列尺度值，并存储在scales中
        fc = pywt.central_frequency(wavename)
        cparam = 2 * fc * totalscal
        scales = cparam / np.arange(totalscal, 0, -1)

        # 连续小波变换函数
        coefficients, frequencies = pywt.cwt(signals, scales, wavename, sampling_period)

        # 计算变换系数的幅度
        amp = abs(coefficients)
        # frequencies.max()

        # 根据采样周期生成时间轴
        t = np.linspace(1, sampling_period, 1024, endpoint=False)

        # 绘制时频图
        image_name = os.path.join(image_path, str(num) + '.jpg')
        plt.figure(figsize=(224 / 100, 224 / 100))
        plt.contourf(t, frequencies, amp, cmap='jet')
        plt.axis('off')  # 去坐标轴
        plt.xticks([])  # 去x轴刻度
        plt.yticks([])  # 去y轴刻度
        # 去白边
        plt.savefig(image_name, bbox_inches='tight', pad_inches=0)
        plt.close()
        start_num += space
        end_num += space
        num += 1


def calculate_parameter(folder_path, L=None, M=None, N=None):
    """
    根据已知的两个参数（L, M, N中的两个）计算第三个参数的最大可行值。

    参数:
    folder_path (str): .mat文件目录
    L (int, optional): 窗口长度
    M (int, optional): 数据块数
    N (int, optional): 步长

    返回:
    int: 第三个参数的最大可行值，若无法满足返回-1

    异常:
    ValueError: 参数错误或文件错误时抛出
    """
    # 参数校验
    known_params = [p for p in [L, M, N] if p is not None]
    if len(known_params) != 2:
        raise ValueError("必须且只能提供两个参数")
    if L is not None and L < 0:
        raise ValueError("L必须≥0")
    if M is not None and M < 1:
        raise ValueError("M必须≥1")
    if N is not None and N < 0:
        raise ValueError("N必须≥0")

    # 确定目标参数
    target = None
    if L is None:
        target = 'L'
        M_val, N_val = M, N
    elif M is None:
        target = 'M'
        L_val, N_val = L, N
    else:
        target = 'N'
        L_val, M_val = L, M

    min_value = float('inf')
    valid = True

    for filename in os.listdir(folder_path):
        if not filename.endswith('.mat'):
            continue

        filepath = os.path.join(folder_path, filename)
        try:
            mat = loadmat(filepath)
            signal = mat['DE'].flatten()
            S = len(signal)
        except KeyError:
            raise ValueError(f"文件 {filename} 缺少DE信号")
        except Exception as e:
            raise IOError(f"读取文件 {filename} 失败: {str(e)}")

        try:
            if target == 'N':
                # 已知L和M求N
                if M_val == 1:
                    if S < L_val:
                        valid = False
                        break
                    current = 0
                else:
                    if S < L_val:
                        valid = False
                        break
                    max_step = (S - L_val) // (M_val - 1)
                    current = min(max_step, L_val)
                    if L_val + (M_val - 1) * current > S:
                        valid = False
                        break

            elif target == 'M':
                # 已知L和N求M
                if N_val == 0:
                    if S < L_val:
                        valid = False
                        break
                    current = 1
                else:
                    if L_val < N_val:
                        valid = False
                        break
                    if S < L_val:
                        valid = False
                        break
                    max_m = (S - L_val) // N_val + 1
                    if (max_m - 1) * N_val > S - L_val:
                        max_m -= 1
                    current = max_m if max_m >= 1 else 0

            elif target == 'L':
                # 已知M和N求L
                required_min_signal = M_val * N_val
                if S < required_min_signal:
                    valid = False
                    break
                current = S - (M_val - 1) * N_val
                if current < N_val:
                    valid = False
                    break

            min_value = min(min_value, current)

        except Exception as e:
            valid = False
            break

    if not valid or min_value == float('inf'):
        return -1

    # 最终校验
    if target == 'L' and min_value < N_val:
        return -1
    if target == 'M' and min_value < 1:
        return -1

    return min_value


if __name__ == '__main__':
    data_dir = r'D:\Code\0-data\8-工业大竞赛数据集\mat'
    mat_names = os.listdir(data_dir)
    for mat_name in mat_names:
        class_name = mat_name.split('.')[0]
        mat_path = os.path.join(data_dir, mat_name)
        data = loadmat(mat_path)['DE'].reshape(-1)
        img_time_freq(data, 1000, 0, 1024, 256, 1.0/120000,
                      256, 'morl', class_name, r'D:\Code\0-data\8-工业大竞赛数据集\images')

    # data = loadmat(r'D:\Code\0-data\7-HOB\HOB\1-H1.mat')['DE'].reshape(-1)
    # img_time_freq(data, 1000, 0, 2048, 2048, 1.0/10000,
    #               256, 'morl', '1-H1', r'D:\Code\0-data\0-故障诊断结果输出\HOB\1-H1')
    # M = calculate_parameter(r'D:\Code\0-data\8-工业大竞赛数据集\mat', L=1024, N=256)
    # print(M)
