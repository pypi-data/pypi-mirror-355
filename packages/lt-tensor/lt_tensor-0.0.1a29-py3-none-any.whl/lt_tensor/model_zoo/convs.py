__all__ = ["ConvNets", "Conv1dEXT"]
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


class Conv1dEXT(ConvNets):
    def __init__(
        self,
        in_channels: int,
        out_channels: Optional[int] = None,
        kernel_size: Union[int, Tuple[int, ...]] = 1,
        stride: Union[int, Tuple[int, ...]] = 1,
        padding: Union[int, Tuple[int, ...]] = 0,
        dilation: Union[int, Tuple[int, ...]] = 1,
        groups: int = 1,
        bias: bool = True,
        padding_mode: str = "zeros",
        device: Optional[Any] = None,
        dtype: Optional[Any] = None,
        apply_norm: Optional[Literal["weight", "spectral"]] = None,
        activation: nn.Module = nn.Identity(),
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        if not out_channels:
            out_channels = in_channels
        cnn_kwargs = dict(
            in_channels=in_channels,
            out_channels=out_channels,
            kernel_size=kernel_size,
            stride=stride,
            padding=padding,
            dilation=dilation,
            groups=groups,
            bias=bias,
            padding_mode=padding_mode,
            device=device,
            dtype=dtype,
        )
        if apply_norm is None:
            self.cnn = nn.Conv1d(**cnn_kwargs)
        else:
            if apply_norm == "spectral":
                self.cnn = spectral_norm(nn.Conv1d(**cnn_kwargs))
            else:
                self.cnn = weight_norm(nn.Conv1d(**cnn_kwargs))
        self.activation = activation
        self.cnn.apply(self.init_weights)

    def forward(self, input: Tensor):
        return self.cnn(self.activation(input))
