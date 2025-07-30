__all__ = [
    "spectral_norm_select",
    "get_weight_norm",
    "ResBlock1D",
    "ResBlock1DShuffled",
    "AdaResBlock1D",
    "ResBlocks1D",
    "ResBlock1D2",
]
import math
from lt_utils.common import *
import torch.nn.functional as F
from lt_tensor.torch_commons import *
from lt_tensor.model_base import Model
from lt_tensor.misc_utils import log_tensor
from lt_tensor.model_zoo.fusion import AdaFusion1D, AdaIN1D
from lt_tensor.model_zoo.convs import ConvNets


def get_padding(ks, d):
    return int((ks * d - d) / 2)


class ResBlock1D(ConvNets):
    def __init__(
        self,
        channels,
        kernel_size=3,
        dilation=(1, 3, 5),
        activation: nn.Module = nn.LeakyReLU(0.1),
    ):
        super().__init__()

        self.conv_nets = nn.ModuleList(
            [
                self._get_conv_layer(i, channels, kernel_size, 1, dilation, activation)
                for i in range(len(dilation))
            ]
        )
        self.conv_nets.apply(self.init_weights)
        self.last_index = len(self.conv_nets) - 1

    def _get_conv_layer(self, id, ch, k, stride, d, actv):
        return nn.Sequential(
            actv,  # 1
            weight_norm(
                nn.Conv1d(
                    ch, ch, k, stride, dilation=d[id], padding=get_padding(k, d[id])
                )
            ),  # 2
            actv,  # 3
            weight_norm(
                nn.Conv1d(ch, ch, k, stride, dilation=1, padding=get_padding(k, 1))
            ),  # 4
        )

    def forward(self, x: Tensor):
        for cnn in self.conv_nets:
            x = cnn(x) + x
        return x


class ResBlock1DShuffled(ConvNets):
    def __init__(
        self,
        channels,
        kernel_size=3,
        dilation=(1, 3, 5),
        activation: nn.Module = nn.LeakyReLU(0.1),
        channel_shuffle_groups=1,
    ):
        super().__init__()

        self.channel_shuffle = nn.ChannelShuffle(channel_shuffle_groups)

        self.conv_nets = nn.ModuleList(
            [
                self._get_conv_layer(i, channels, kernel_size, 1, dilation, activation)
                for i in range(3)
            ]
        )
        self.conv_nets.apply(self.init_weights)
        self.last_index = len(self.conv_nets) - 1

    def _get_conv_layer(self, id, ch, k, stride, d, actv):
        return nn.Sequential(
            actv,  # 1
            weight_norm(
                nn.Conv1d(
                    ch, ch, k, stride, dilation=d[id], padding=get_padding(k, d[id])
                )
            ),  # 2
            actv,  # 3
            weight_norm(
                nn.Conv1d(ch, ch, k, stride, dilation=1, padding=get_padding(k, 1))
            ),  # 4
        )

    def forward(self, x: Tensor):
        b = x.clone() * 0.5
        for cnn in self.conv_nets:
            x = cnn(self.channel_shuffle(x)) + b
        return x


class AdaResBlock1D(ConvNets):
    def __init__(
        self,
        res_block_channels: int,
        ada_channel_in: int,
        kernel_size=3,
        dilation=(1, 3, 5),
        activation: nn.Module = nn.LeakyReLU(0.1),
    ):
        super().__init__()

        self.alpha1 = nn.ModuleList()
        self.alpha2 = nn.ModuleList()
        self.conv_nets = nn.ModuleList(
            [
                self._get_conv_layer(
                    d,
                    res_block_channels,
                    ada_channel_in,
                    kernel_size,
                )
                for d in dilation
            ]
        )
        self.conv_nets.apply(self.init_weights)
        self.last_index = len(self.conv_nets) - 1
        self.activation = activation

    def _get_conv_layer(self, d, ch, ada_ch, k):
        self.alpha1.append(nn.Parameter(torch.ones(1, ada_ch, 1)))
        self.alpha2.append(nn.Parameter(torch.ones(1, ada_ch, 1)))
        return nn.ModuleDict(
            dict(
                norm1=AdaFusion1D(ada_ch, ch),
                norm2=AdaFusion1D(ada_ch, ch),
                conv1=weight_norm(
                    nn.Conv1d(ch, ch, k, 1, dilation=d, padding=get_padding(k, d))
                ),  # 2
                conv2=weight_norm(
                    nn.Conv1d(ch, ch, k, 1, dilation=1, padding=get_padding(k, 1))
                ),  # 4
            )
        )

    def forward(self, x: torch.Tensor, y: torch.Tensor):
        for i, cnn in enumerate(self.conv_nets):
            xt = self.activation(cnn["norm1"](x, y, self.alpha1[i]))
            xt = cnn["conv1"](xt)
            xt = self.activation(cnn["norm2"](xt, y, self.alpha2[i]))
            x = cnn["conv2"](xt) + x
        return x


class ResBlock1D2(ConvNets):
    def __init__(
        self,
        channels,
        kernel_size=3,
        dilation=(1, 3, 5),
        activation: nn.Module = nn.LeakyReLU(0.1),
    ):
        super().__init__()
        self.convs = nn.ModuleList(
            [
                weight_norm(
                    nn.Conv1d(
                        channels,
                        channels,
                        kernel_size,
                        dilation=d,
                        padding=get_padding(kernel_size, d),
                    )
                )
                for d in range(dilation)
            ]
        )
        self.convs.apply(self.init_weights)
        self.activation = activation

    def forward(self, x):
        for c in self.convs:
            xt = c(self.activation(x))
            x = xt + x
        return x


class ResBlocks1D(ConvNets):
    def __init__(
        self,
        channels: int,
        resblock_kernel_sizes: List[Union[int, List[int]]] = [3, 7, 11],
        resblock_dilation_sizes: List[Union[int, List[int]]] = [
            [1, 3, 5],
            [1, 3, 5],
            [1, 3, 5],
        ],
        activation: nn.Module = nn.LeakyReLU(0.1),
        block: Union[ResBlock1D, ResBlock1D2] = ResBlock1D,
    ):
        super().__init__()
        self.num_kernels = len(resblock_kernel_sizes)
        self.rb = nn.ModuleList()
        self.activation = activation

        for k, j in zip(resblock_kernel_sizes, resblock_dilation_sizes):
            self.rb.append(block(channels, k, j, activation))

        self.rb.apply(self.init_weights)

    def forward(self, x: torch.Tensor):
        xs = None
        for i, block in enumerate(self.rb):
            if i == 0:
                xs = block(x)
            else:
                xs += block(x)
        return xs / self.num_kernels
