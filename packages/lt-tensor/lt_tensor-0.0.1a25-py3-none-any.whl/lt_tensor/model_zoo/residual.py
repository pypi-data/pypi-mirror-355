__all__ = [
    "spectral_norm_select",
    "get_weight_norm",
    "ResBlock1D",
    "ResBlock2D",
    "ResBlock1DShuffled",
    "AdaResBlock1D",
    "ResBlocks1D",
    "ResBlock1D2",
    "ShuffleBlock2D",
]
import math
from lt_utils.common import *
import torch.nn.functional as F
from lt_tensor.torch_commons import *
from lt_tensor.model_base import Model
from lt_tensor.misc_utils import log_tensor
from lt_tensor.model_zoo.fusion import AdaFusion1D, AdaIN1D


def spectral_norm_select(module: nn.Module, enabled: bool):
    if enabled:
        return spectral_norm(module)
    return module


def get_weight_norm(norm_type: Optional[Literal["weight", "spectral"]] = None):
    if not norm_type:
        return lambda x: x
    if norm_type == "weight":
        return lambda x: weight_norm(x)
    return lambda x: spectral_norm(x)


def remove_norm(module, name: str = "weight"):
    try:
        try:
            remove_parametrizations(module, name, leave_parametrized=False)
        except:
            # many times will fail with 'leave_parametrized'
            remove_parametrizations(module, name)
    except ValueError:
        pass  # not parametrized


class ConvNets(Model):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def remove_norms(self, name: str = "weight"):
        for module in self.modules():
            if "Conv" in module.__class__.__name__:
                remove_norm(module, name)

    @staticmethod
    def init_weights(
        m: nn.Module,
        norm: Optional[Literal["spectral", "weight"]] = None,
        mean=0.0,
        std=0.02,
        name: str = "weight",
        n_power_iterations: int = 1,
        eps: float = 1e-9,
        dim_sn: Optional[int] = None,
        dim_wn: int = 0,
    ):
        if "Conv" in m.__class__.__name__:
            if norm is not None:
                try:
                    if norm == "spectral":
                        m.apply(
                            lambda m: spectral_norm(
                                m,
                                n_power_iterations=n_power_iterations,
                                eps=eps,
                                name=name,
                                dim=dim_sn,
                            )
                        )
                    else:
                        m.apply(lambda m: weight_norm(m, name=name, dim=dim_wn))
                except ValueError:
                    pass
            m.weight.data.normal_(mean, std)


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
        get_padding = lambda ks, d: int((ks * d - d) / 2)
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


class ResBlock2D(Model):
    def __init__(
        self,
        in_channels: int,
        out_channels: Optional[int] = None,
        hidden_dim: int = 32,
        downscale: bool = False,
        activation: nn.Module = nn.LeakyReLU(0.2),
    ):
        super().__init__()
        stride = 2 if downscale else 1
        if out_channels is None:
            out_channels = in_channels

        self.block = nn.Sequential(
            nn.Conv2d(in_channels, hidden_dim, 3, stride, 1),
            activation,
            nn.Conv2d(hidden_dim, hidden_dim, 7, 1, 3),
            activation,
            nn.Conv2d(hidden_dim, out_channels, 3, 1, 1),
        )

        self.skip = nn.Identity()
        if downscale or in_channels != out_channels:
            self.skip = spectral_norm_select(
                nn.Conv2d(in_channels, out_channels, 1, stride)
            )
        # on less to be handled every cycle
        self.sqrt_2 = math.sqrt(2)

    def forward(self, x: Tensor):
        return x + ((self.block(x) + self.skip(x)) / self.sqrt_2)


class ShuffleBlock2D(ConvNets):
    def __init__(
        self,
        channels: int,
        out_channels: Optional[int] = None,
        hidden_dim: int = 32,
        downscale: bool = False,
        activation: nn.Module = nn.LeakyReLU(0.1),
    ):
        super().__init__()
        if out_channels is None:
            out_channels = channels
        self.shuffle = nn.ChannelShuffle(groups=2)
        self.ch_split = lambda tensor: torch.split(tensor, 1, dim=1)
        self.activation = activation
        self.resblock_2d = ResBlock2D(
            channels, out_channels, hidden_dim, downscale, activation
        )

    def shuffle_channels(self, tensor: torch.Tensor):
        with torch.no_grad():
            x = F.channel_shuffle(tensor.transpose(1, -1), tensor.shape[1]).transpose(
                -1, 1
            )
        return self.ch_split(x)

    def forward(self, x: torch.Tensor):
        ch1, ch2 = self.shuffle_channels(x)
        ch2 = self.resblock_2d(ch2)
        return torch.cat((ch1, ch2), dim=1)


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
