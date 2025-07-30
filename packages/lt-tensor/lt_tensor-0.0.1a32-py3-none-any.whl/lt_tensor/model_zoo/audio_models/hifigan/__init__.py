__all__ = ["HifiganGenerator", "HifiganConfig"]
from lt_utils.common import *
from lt_tensor.torch_commons import *
from lt_tensor.model_zoo.convs import ConvNets
from torch.nn import functional as F
from lt_utils.file_ops import load_json, is_file, is_dir, is_path_valid
from lt_tensor.misc_utils import get_config, get_weights


def get_padding(kernel_size, dilation=1):
    return int((kernel_size * dilation - dilation) / 2)


from lt_tensor.config_templates import ModelConfig


class HifiganConfig(ModelConfig):
    # Training params
    in_channels: int = 80
    upsample_rates: List[Union[int, List[int]]] = [8, 8]
    upsample_kernel_sizes: List[Union[int, List[int]]] = [16, 16]
    upsample_initial_channel: int = 512
    resblock_kernel_sizes: List[Union[int, List[int]]] = [3, 7, 11]
    resblock_dilation_sizes: List[Union[int, List[int]]] = [
        [1, 3, 5],
        [1, 3, 5],
        [1, 3, 5],
    ]

    activation: nn.Module = nn.LeakyReLU(0.1)
    resblock: int = 0

    def __init__(
        self,
        in_channels: int = 80,
        upsample_rates: List[Union[int, List[int]]] = [8, 8],
        upsample_kernel_sizes: List[Union[int, List[int]]] = [16, 16],
        upsample_initial_channel: int = 512,
        resblock_kernel_sizes: List[Union[int, List[int]]] = [3, 7, 11],
        resblock_dilation_sizes: List[Union[int, List[int]]] = [
            [1, 3, 5],
            [1, 3, 5],
            [1, 3, 5],
        ],
        activation: nn.Module = nn.LeakyReLU(0.1),
        resblock: Union[int, str] = "1",
        *args,
        **kwargs,
    ):
        settings = {
            "in_channels": in_channels,
            "upsample_rates": upsample_rates,
            "upsample_kernel_sizes": upsample_kernel_sizes,
            "upsample_initial_channel": upsample_initial_channel,
            "resblock_kernel_sizes": resblock_kernel_sizes,
            "resblock_dilation_sizes": resblock_dilation_sizes,
            "activation": activation,
            "resblock": resblock,
        }
        super().__init__(**settings)

    def post_process(self):
        if isinstance(self.resblock, str):
            self.resblock = 0 if self.resblock == "1" else 1


class ResBlock1(ConvNets):
    def __init__(self, channels, kernel_size=3, dilation=(1, 3, 5)):
        super().__init__()

        self.convs1 = nn.ModuleList(
            [
                weight_norm(
                    nn.Conv1d(
                        channels,
                        channels,
                        kernel_size,
                        1,
                        dilation=dilation[0],
                        padding=get_padding(kernel_size, dilation[0]),
                    )
                ),
                weight_norm(
                    nn.Conv1d(
                        channels,
                        channels,
                        kernel_size,
                        1,
                        dilation=dilation[1],
                        padding=get_padding(kernel_size, dilation[1]),
                    )
                ),
                weight_norm(
                    nn.Conv1d(
                        channels,
                        channels,
                        kernel_size,
                        1,
                        dilation=dilation[2],
                        padding=get_padding(kernel_size, dilation[2]),
                    )
                ),
            ]
        )
        self.convs1.apply(self.init_weights)

        self.convs2 = nn.ModuleList(
            [
                weight_norm(
                    nn.Conv1d(
                        channels,
                        channels,
                        kernel_size,
                        1,
                        dilation=1,
                        padding=get_padding(kernel_size, 1),
                    )
                ),
                weight_norm(
                    nn.Conv1d(
                        channels,
                        channels,
                        kernel_size,
                        1,
                        dilation=1,
                        padding=get_padding(kernel_size, 1),
                    )
                ),
                weight_norm(
                    nn.Conv1d(
                        channels,
                        channels,
                        kernel_size,
                        1,
                        dilation=1,
                        padding=get_padding(kernel_size, 1),
                    )
                ),
            ]
        )
        self.convs2.apply(self.init_weights)
        self.activation = nn.LeakyReLU(0.1)

    def forward(self, x):
        for c1, c2 in zip(self.convs1, self.convs2):
            xt = c1(self.activation(x))
            xt = c2(self.activation(xt))
            x = xt + x
        return x


class ResBlock2(ConvNets):
    def __init__(self, channels, kernel_size=3, dilation=(1, 3)):
        super().__init__()
        self.convs = nn.ModuleList(
            [
                weight_norm(
                    nn.Conv1d(
                        channels,
                        channels,
                        kernel_size,
                        1,
                        dilation=dilation[0],
                        padding=get_padding(kernel_size, dilation[0]),
                    )
                ),
                weight_norm(
                    nn.Conv1d(
                        channels,
                        channels,
                        kernel_size,
                        1,
                        dilation=dilation[1],
                        padding=get_padding(kernel_size, dilation[1]),
                    )
                ),
            ]
        )
        self.convs.apply(self.init_weights)
        self.activation = nn.LeakyReLU(0.1)

    def forward(self, x):
        for c in self.convs:
            xt = c(self.activation(x))
            x = xt + x
        return x


class HifiganGenerator(ConvNets):
    def __init__(self, cfg: HifiganConfig = HifiganConfig()):
        super().__init__()
        self.cfg = cfg
        self.num_kernels = len(cfg.resblock_kernel_sizes)
        self.num_upsamples = len(cfg.upsample_rates)
        self.conv_pre = weight_norm(
            nn.Conv1d(cfg.in_channels, cfg.upsample_initial_channel, 7, 1, padding=3)
        )
        if isinstance(cfg.resblock, str):
            cfg.resblock = 0 if cfg.resblock == "1" else 1
        resblock = ResBlock1 if cfg.resblock == 0 else ResBlock2
        self.activation = cfg.activation
        self.ups = nn.ModuleList()
        for i, (u, k) in enumerate(zip(cfg.upsample_rates, cfg.upsample_kernel_sizes)):
            self.ups.append(
                weight_norm(
                    nn.ConvTranspose1d(
                        cfg.upsample_initial_channel // (2**i),
                        cfg.upsample_initial_channel // (2 ** (i + 1)),
                        k,
                        u,
                        padding=(k - u) // 2,
                    )
                )
            )

        self.resblocks = nn.ModuleList()
        for i in range(len(self.ups)):
            ch = cfg.upsample_initial_channel // (2 ** (i + 1))
            for j, (k, d) in enumerate(
                zip(cfg.resblock_kernel_sizes, cfg.resblock_dilation_sizes)
            ):
                self.resblocks.append(resblock(ch, k, d))

        self.conv_post = weight_norm(nn.Conv1d(ch, 1, 7, 1, padding=3))
        self.ups.apply(self.init_weights)
        self.conv_post.apply(self.init_weights)

    def forward(self, x: Tensor):
        x = self.conv_pre(x)
        for i in range(self.num_upsamples):
            x = self.ups[i](self.activation(x))
            xs = None
            for j in range(self.num_kernels):
                if xs is None:
                    xs = self.resblocks[i * self.num_kernels + j](x)
                else:
                    xs += self.resblocks[i * self.num_kernels + j](x)
            x = xs / self.num_kernels
        x = self.conv_post(self.activation(x))
        x = torch.tanh(x)

        return x

    def load_weights(
        self,
        path,
        strict=False,
        assign=False,
        weights_only=False,
        mmap=None,
        raise_if_not_exists=False,
        **pickle_load_args,
    ):
        try:
            incompatible_keys = super().load_weights(
                path,
                raise_if_not_exists,
                strict,
                assign,
                weights_only,
                mmap,
                **pickle_load_args,
            )
            if incompatible_keys:
                self.remove_norms()
                incompatible_keys = super().load_weights(
                    path,
                    raise_if_not_exists,
                    strict,
                    assign,
                    weights_only,
                    mmap,
                    **pickle_load_args,
                )
            return incompatible_keys
        except RuntimeError:
            self.remove_norms()
            return super().load_weights(
                path,
                raise_if_not_exists,
                strict,
                assign,
                weights_only,
                mmap,
                **pickle_load_args,
            )

    @classmethod
    def from_pretrained(
        cls,
        model_file: PathLike,
        model_config: Union[HifiganConfig, Dict[str, Any]],
        *,
        strict: bool = False,
        map_location: str = "cpu",
        weights_only: bool = False,
        **kwargs,
    ):

        is_file(model_file, validate=True)
        model_state_dict = torch.load(
            model_file, weights_only=weights_only, map_location=map_location
        )

        if isinstance(model_config, HifiganConfig):
            h = model_config
        else:
            h = HifiganConfig(**model_config)

        model = cls(h)
        try:
            incompatible_keys = model.load_state_dict(model_state_dict, strict=strict)
            if incompatible_keys:
                model.remove_norms()
                model.load_state_dict(model_state_dict, strict=strict)
        except RuntimeError:
            print(
                f"[INFO] the pretrained checkpoint does not contain weight norm. Loading the checkpoint after removing weight norm!"
            )
            model.remove_norms()
            model.load_state_dict(model_state_dict, strict=strict)
        return model


class DiscriminatorP(ConvNets):
    def __init__(self, period, kernel_size=5, stride=3, use_spectral_norm=False):
        super(DiscriminatorP, self).__init__()
        self.period = period
        norm_f = weight_norm if use_spectral_norm == False else spectral_norm
        self.convs = nn.ModuleList(
            [
                norm_f(
                    nn.Conv2d(
                        1,
                        32,
                        (kernel_size, 1),
                        (stride, 1),
                        padding=(get_padding(5, 1), 0),
                    )
                ),
                norm_f(
                    nn.Conv2d(
                        32,
                        128,
                        (kernel_size, 1),
                        (stride, 1),
                        padding=(get_padding(5, 1), 0),
                    )
                ),
                norm_f(
                    nn.Conv2d(
                        128,
                        512,
                        (kernel_size, 1),
                        (stride, 1),
                        padding=(get_padding(5, 1), 0),
                    )
                ),
                norm_f(
                    nn.Conv2d(
                        512,
                        1024,
                        (kernel_size, 1),
                        (stride, 1),
                        padding=(get_padding(5, 1), 0),
                    )
                ),
                norm_f(nn.Conv2d(1024, 1024, (kernel_size, 1), 1, padding=(2, 0))),
            ]
        )
        self.conv_post = norm_f(nn.Conv2d(1024, 1, (3, 1), 1, padding=(1, 0)))
        self.activation = nn.LeakyReLU(0.1)

    def forward(self, x):
        fmap = []

        # 1d to 2d
        b, c, t = x.shape
        if t % self.period != 0:  # pad first
            n_pad = self.period - (t % self.period)
            x = F.pad(x, (0, n_pad), "reflect")
            t = t + n_pad
        x = x.view(b, c, t // self.period, self.period)

        for l in self.convs:
            x = l(x)
            x = self.activation(x)
            fmap.append(x)
        x = self.conv_post(x)
        fmap.append(x)
        x = torch.flatten(x, 1, -1)

        return x, fmap


class MultiPeriodDiscriminator(ConvNets):
    def __init__(self):
        super(MultiPeriodDiscriminator, self).__init__()
        self.discriminators = nn.ModuleList(
            [
                DiscriminatorP(2),
                DiscriminatorP(3),
                DiscriminatorP(5),
                DiscriminatorP(7),
                DiscriminatorP(11),
            ]
        )

    def forward(self, y, y_hat):
        y_d_rs = []
        y_d_gs = []
        fmap_rs = []
        fmap_gs = []
        for i, d in enumerate(self.discriminators):
            y_d_r, fmap_r = d(y)
            y_d_g, fmap_g = d(y_hat)
            y_d_rs.append(y_d_r)
            fmap_rs.append(fmap_r)
            y_d_gs.append(y_d_g)
            fmap_gs.append(fmap_g)

        return y_d_rs, y_d_gs, fmap_rs, fmap_gs


class DiscriminatorS(ConvNets):
    def __init__(self, use_spectral_norm=False):
        super(DiscriminatorS, self).__init__()
        norm_f = weight_norm if use_spectral_norm == False else spectral_norm
        self.convs = nn.ModuleList(
            [
                norm_f(nn.Conv1d(1, 128, 15, 1, padding=7)),
                norm_f(nn.Conv1d(128, 128, 41, 2, groups=4, padding=20)),
                norm_f(nn.Conv1d(128, 256, 41, 2, groups=16, padding=20)),
                norm_f(nn.Conv1d(256, 512, 41, 4, groups=16, padding=20)),
                norm_f(nn.Conv1d(512, 1024, 41, 4, groups=16, padding=20)),
                norm_f(nn.Conv1d(1024, 1024, 41, 1, groups=16, padding=20)),
                norm_f(nn.Conv1d(1024, 1024, 5, 1, padding=2)),
            ]
        )
        self.conv_post = norm_f(nn.Conv1d(1024, 1, 3, 1, padding=1))
        self.activation = nn.LeakyReLU(0.1)

    def forward(self, x):
        fmap = []
        for l in self.convs:
            x = l(x)
            x = self.activation(x)
            fmap.append(x)
        x = self.conv_post(x)
        fmap.append(x)
        x = torch.flatten(x, 1, -1)

        return x, fmap


class MultiScaleDiscriminator(ConvNets):
    def __init__(self):
        super(MultiScaleDiscriminator, self).__init__()
        self.discriminators = nn.ModuleList(
            [
                DiscriminatorS(use_spectral_norm=True),
                DiscriminatorS(),
                DiscriminatorS(),
            ]
        )
        self.meanpools = nn.ModuleList(
            [nn.AvgPool1d(4, 2, padding=2), nn.AvgPool1d(4, 2, padding=2)]
        )

    def forward(self, y, y_hat):
        y_d_rs = []
        y_d_gs = []
        fmap_rs = []
        fmap_gs = []
        for i, d in enumerate(self.discriminators):
            if i != 0:
                y = self.meanpools[i - 1](y)
                y_hat = self.meanpools[i - 1](y_hat)
            y_d_r, fmap_r = d(y)
            y_d_g, fmap_g = d(y_hat)
            y_d_rs.append(y_d_r)
            fmap_rs.append(fmap_r)
            y_d_gs.append(y_d_g)
            fmap_gs.append(fmap_g)

        return y_d_rs, y_d_gs, fmap_rs, fmap_gs


def feature_loss(fmap_r, fmap_g):
    loss = 0
    for dr, dg in zip(fmap_r, fmap_g):
        for rl, gl in zip(dr, dg):
            loss += torch.mean(torch.abs(rl - gl))

    return loss * 2


def discriminator_loss(disc_real_outputs, disc_generated_outputs):
    loss = 0
    r_losses = []
    g_losses = []
    for dr, dg in zip(disc_real_outputs, disc_generated_outputs):
        r_loss = torch.mean((1 - dr) ** 2)
        g_loss = torch.mean(dg**2)
        loss += r_loss + g_loss
        r_losses.append(r_loss.item())
        g_losses.append(g_loss.item())

    return loss, r_losses, g_losses


def generator_loss(disc_outputs):
    loss = 0
    gen_losses = []
    for dg in disc_outputs:
        l = torch.mean((1 - dg) ** 2)
        gen_losses.append(l)
        loss += l

    return loss, gen_losses
