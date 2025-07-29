import collections
import math
import time
from itertools import repeat
from typing import Union, Tuple, TypeVar

import torch
from torch import nn
from torch.nn.parameter import Parameter

from yms_class.convolution.KANLayer import KANLayer

T = TypeVar('T')


def _tuple(n, name="parse"):
    def parse(x):
        if isinstance(x, collections.abc.Iterable):
            return tuple(x)
        return tuple(repeat(x, n))

    parse.__name__ = name
    return parse


_scalar_or_tuple_2_t = Union[T, Tuple[T, T]]
_size_2_t = _scalar_or_tuple_2_t[int]
_pair = _tuple(2, "_pair")

def convolution2d(
        in_channels: int,
        out_channels: int,
        matrix,
        kernels,
        kernel_size,
        stride,
        padding,
        dilation,
        bias,
        unfold
):
    batch_size, in_ch, height, width = matrix.shape
    if in_channels != in_ch:
        raise ValueError(f"Input channel mismatch: parameter in_channels={in_channels}, but input matrix has {in_ch} channels")
    out_height = (height + 2 * padding[0] - dilation[0] * (kernel_size[0] - 1) - 1) // stride[0] + 1
    out_width = (width + 2 * padding[1] - dilation[1] * (kernel_size[1] - 1) - 1) // stride[1] + 1
    # out_height, out_width = calc_out_dims(matrix, kernel_size, stride, padding, dilation)
    matrix_out = matrix.new_zeros((batch_size, out_channels, out_height, out_width))
    # matrix_out = torch.zeros(batch_size, out_channels, out_height, out_width).to(device)
    # unfold = torch.nn.Unfold(kernel_size=kernel_size, dilation=dilation, stride=stride, padding=padding)
    conv_groups = unfold(matrix).view(batch_size, in_channels, kernel_size[0] * kernel_size[1],
                                      out_height * out_width).transpose(2, 3)

    for out_channel in range(out_channels):
        for in_channel in range(in_channels):
            matrix_out[:, out_channel, :, :] += kernels[out_channel][in_channel].forward(
                conv_groups[:, in_channel, :, :].flatten(0, 1)).reshape((batch_size, out_height, out_width))

    # 添加偏置操作：为每个输出通道添加对应的偏置值
    if bias is not None:
        # 将偏置重塑为(1, out_channels, 1, 1)以便广播
        matrix_out += bias.view(1, -1, 1, 1)

    return matrix_out


class KANConvolution(torch.nn.Module):
    def __init__(self,
                 in_channels: int,
                 out_channels: int,
                 kernel_size: _size_2_t = 3,
                 stride: _size_2_t = 1,
                 padding: _size_2_t = 0,
                 dilation: _size_2_t = 1,
                 num=5, k=3, noise_scale=0.5, scale_base_mu=0.0, scale_base_sigma=1.0,
                 scale_sp=1.0, base_fun=torch.nn.SiLU(), grid_eps=0.02, grid_range=None, sp_trainable=True,
                 sb_trainable=True, sparse_init=False, bias=True
                 ):
        super(KANConvolution, self).__init__()

        if grid_range is None:
            grid_range = [-1, 1]
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.kernel_size = _pair(kernel_size)
        self.stride = _pair(stride)
        self.padding = _pair(padding)
        self.dilation = _pair(dilation)
        self.conv = torch.nn.ModuleList()
        self.unfold = torch.nn.Unfold(kernel_size=kernel_size, dilation=dilation, stride=stride, padding=padding)
        # 根据bias标志创建或忽略偏置参数
        if bias:
            self.bias = Parameter(torch.zeros(self.out_channels))  # 初始化为零
        else:
            self.register_parameter('bias', None)  # 无偏置

        for i in range(self.out_channels):
            self.conv.append(torch.nn.ModuleList())
            for j in range(self.in_channels):
                self.conv[i].append(
                    KANLayer(
                        in_dim=math.prod(self.kernel_size),
                        out_dim=1,
                        num=num,
                        k=k,
                        noise_scale=noise_scale,
                        scale_base_mu=scale_base_mu,
                        scale_base_sigma=scale_base_sigma,
                        scale_sp=scale_sp,
                        base_fun=base_fun,
                        grid_eps=grid_eps,
                        grid_range=grid_range,
                        sp_trainable=sp_trainable,
                        sb_trainable=sb_trainable,
                        sparse_init=sparse_init
                    )
                )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return convolution2d(in_channels=self.in_channels,out_channels=self.out_channels, matrix=x, kernels=self.conv,
                             kernel_size=self.kernel_size, stride=self.stride, padding=self.padding,
                             dilation=self.dilation, bias=self.bias, unfold=self.unfold)

if __name__ == '__main__':
    import torch.nn.functional as F

    device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
    input_size = [1, 3, 32, 32]
    input_map = torch.randn(input_size)
    # kernel_size = [3, 3, 3, 3]
    # kernels = torch.randn(kernel_size)
    # bias = torch.randn(3)
    model = KANConvolution(in_channels=3, out_channels=4, kernel_size=3, stride=1, padding=0, dilation=1)
    t1 = time.time()
    # # for param in model.parameters():
    # #     print(param.device)
    output = model(input_map)
    t2 = time.time()
    # output2 = F.conv2d(input=input_map, weight=kernels, stride=[1, 1], padding=0, bias=bias)
    # # t3 = time.time()
    # print(output.shape)
    # print(output2)
    print(output.shape)
    # print(output2.shape)
    print(f'kan卷积时间：{t2 - t1}')
    # print(f'官方卷积时间：{t3 - t2}')
    # print(f'倍数{(t2 - t1)/(t3 - t2)}')

