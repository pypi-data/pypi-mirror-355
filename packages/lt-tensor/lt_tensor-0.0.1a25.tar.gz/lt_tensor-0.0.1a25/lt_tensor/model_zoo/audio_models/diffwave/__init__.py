__all__ = ["DiffWave", "DiffWaveConfig", "SpectrogramUpsample", "DiffusionEmbedding"]

import numpy as np
from lt_tensor.torch_commons import *
from torch.nn import functional as F
from lt_tensor.config_templates import ModelConfig
from lt_tensor.torch_commons import *
from lt_tensor.model_base import Model
from math import sqrt
from lt_utils.common import *


class DiffWaveConfig(ModelConfig):
    # Model params
    n_mels = 80
    hop_samples = 256
    residual_layers = 30
    residual_channels = 64
    dilation_cycle_length = 10
    unconditional = False
    noise_schedule: list[int] = np.linspace(1e-4, 0.05, 50).tolist()
    # settings for auto-fixes
    interpolate = False
    interpolation_mode: Literal[
        "nearest", "linear", "bilinear", "bicubic", "trilinear", "area", "nearest-exact"
    ] = "nearest"

    def __init__(
        self,
        n_mels=80,
        hop_samples=256,
        residual_layers=30,
        residual_channels=64,
        dilation_cycle_length=10,
        unconditional=False,
        noise_schedule: list[int] = np.linspace(1e-4, 0.05, 50).tolist(),
        interpolate_cond=False,
        interpolation_mode: Literal[
            "nearest",
            "linear",
            "bilinear",
            "bicubic",
            "trilinear",
            "area",
            "nearest-exact",
        ] = "nearest",
    ):
        settings = {
            "n_mels": n_mels,
            "hop_samples": hop_samples,
            "residual_layers": residual_layers,
            "dilation_cycle_length": dilation_cycle_length,
            "residual_channels": residual_channels,
            "unconditional": unconditional,
            "noise_schedule": noise_schedule,
            "interpolate": interpolate_cond,
            "interpolation_mode": interpolation_mode,
        }
        super().__init__(**settings)


def Conv1d(*args, **kwargs):
    layer = nn.Conv1d(*args, **kwargs)
    nn.init.kaiming_normal_(layer.weight)
    return layer


class DiffusionEmbedding(Model):
    def __init__(self, max_steps: int):
        super().__init__()
        self.register_buffer(
            "embedding", self._build_embedding(max_steps), persistent=False
        )
        self.projection1 = nn.Linear(128, 512)
        self.projection2 = nn.Linear(512, 512)
        self.activation = nn.SiLU()

    def forward(self, diffusion_step):
        if diffusion_step.dtype in [torch.int32, torch.int64]:
            x = self.embedding[diffusion_step]
        else:
            x = self._lerp_embedding(diffusion_step)
        x = self.projection1(x)
        x = self.activation(x)
        x = self.projection2(x)
        x = self.activation(x)
        return x

    def _lerp_embedding(self, t):
        low_idx = torch.floor(t).long()
        high_idx = torch.ceil(t).long()
        low = self.embedding[low_idx]
        high = self.embedding[high_idx]
        return low + (high - low) * (t - low_idx)

    def _build_embedding(self, max_steps):
        steps = torch.arange(max_steps).unsqueeze(1)  # [T,1]
        dims = torch.arange(64).unsqueeze(0)  # [1,64]
        table = steps * 10.0 ** (dims * 4.0 / 63.0)  # [T,64]
        table = torch.cat([torch.sin(table), torch.cos(table)], dim=1)
        return table


class SpectrogramUpsample(Model):
    def __init__(self):
        super().__init__()
        self.conv1 = nn.ConvTranspose2d(1, 1, [3, 32], stride=[1, 16], padding=[1, 8])
        self.conv2 = nn.ConvTranspose2d(1, 1, [3, 32], stride=[1, 16], padding=[1, 8])
        self.activation = nn.LeakyReLU(0.4)

    def forward(self, x):
        x = torch.unsqueeze(x, 1)
        x = self.activation(self.conv1(x))
        x = self.activation(self.conv2(x))
        x = torch.squeeze(x, 1)
        return x


class ResidualBlock(Model):
    def __init__(self, n_mels, residual_channels, dilation, uncond=False):
        """
        :param n_mels: inplanes of conv1x1 for spectrogram conditional
        :param residual_channels: audio conv
        :param dilation: audio conv dilation
        :param uncond: disable spectrogram conditional
        """
        super().__init__()
        self.dilated_conv = Conv1d(
            residual_channels,
            2 * residual_channels,
            3,
            padding=dilation,
            dilation=dilation,
        )
        self.diffusion_projection = nn.Linear(512, residual_channels)
        if not uncond:  # conditional model
            self.conditioner_projection = Conv1d(n_mels, 2 * residual_channels, 1)
        else:  # unconditional model
            self.conditioner_projection = None

        self.output_projection = Conv1d(residual_channels, 2 * residual_channels, 1)

    def forward(
        self,
        x: Tensor,
        diffusion_step: Tensor,
        conditioner: Optional[Tensor] = None,
    ):

        diffusion_step = self.diffusion_projection(diffusion_step).unsqueeze(-1)
        y = x + diffusion_step
        if (
            conditioner is None or self.conditioner_projection is None
        ):  # using a unconditional model
            y = self.dilated_conv(y)
        else:
            conditioner = self.conditioner_projection(conditioner)
            y = self.dilated_conv(y) + conditioner

        gate, filter = torch.chunk(y, 2, dim=1)
        y = torch.sigmoid(gate) * torch.tanh(filter)

        y = self.output_projection(y)
        residual, skip = torch.chunk(y, 2, dim=1)
        return (x + residual) / sqrt(2.0), skip


class DiffWave(Model):
    def __init__(self, params: DiffWaveConfig = DiffWaveConfig()):
        super().__init__()
        self.params = params
        self.n_hop = self.params.hop_samples
        self.interpolate = self.params.interpolate
        self.interpolate_mode = self.params.interpolation_mode
        self.input_projection = Conv1d(1, params.residual_channels, 1)
        self.diffusion_embedding = DiffusionEmbedding(len(params.noise_schedule))
        if self.params.unconditional:  # use unconditional model
            self.spectrogram_upsample = None
        else:
            self.spectrogram_upsample = SpectrogramUpsample()

        self.residual_layers = nn.ModuleList(
            [
                ResidualBlock(
                    params.n_mels,
                    params.residual_channels,
                    2 ** (i % params.dilation_cycle_length),
                    uncond=params.unconditional,
                )
                for i in range(params.residual_layers)
            ]
        )
        self.skip_projection = Conv1d(
            params.residual_channels, params.residual_channels, 1
        )
        self.output_projection = Conv1d(params.residual_channels, 1, 1)
        self.activation = nn.LeakyReLU(0.1)
        self.r_sqrt = sqrt(len(self.residual_layers))
        nn.init.zeros_(self.output_projection.weight)

    def forward(
        self,
        audio: Tensor,
        diffusion_step: Tensor,
        spectrogram: Optional[Tensor] = None,
    ):
        T = x.shape[-1]
        if x.ndim == 2:
            x = audio.unsqueeze(1)
        x = self.activation(self.input_projection(x))

        diffusion_step = self.diffusion_embedding(diffusion_step)
        if spectrogram is not None and self.spectrogram_upsample is not None:
            if self.auto_interpolate:
                # a little heavy, but helps a lot to fix mismatched shapes,
                # not always recommended due to data loss
                spectrogram = F.interpolate(
                    input=spectrogram,
                    size=int(T * self.n_hop),
                    mode=self.interpolate_mode,
                )
            spectrogram = self.spectrogram_upsample(spectrogram)

        skip = None
        for i, layer in enumerate(self.residual_layers):
            x, skip_connection = layer(x, diffusion_step, spectrogram)
            if i == 0:
                skip = skip_connection
            else:
                skip = skip_connection + skip
        x = skip / self.r_sqrt
        x = self.activation(self.skip_projection(x))
        x = self.output_projection(x)
        return x
