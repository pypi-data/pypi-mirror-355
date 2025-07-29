__all__ = ["Model", "LossTracker"]

import gc
import json
import math
import warnings
from lt_tensor.torch_commons import *
from lt_utils.common import *
from lt_tensor.misc_utils import plot_view, get_weights, get_config, updateDict
from lt_utils.misc_utils import log_traceback, get_current_time
from lt_utils.file_ops import load_json, save_json

T = TypeVar("T")

ROOT_DEVICE = torch.zeros(1).device

POSSIBLE_OUTPUT_TYPES: TypeAlias = Union[
    Tensor,
    Sequence[Tensor],
    Dict[Union[str, Tensor, Any], Union[Sequence[Tensor], Tensor, Any]],
]


class LossTracker:
    last_file = f"logs/history_{get_current_time()}.json"

    def __init__(self, max_len=50_000):
        self.max_len = max_len
        self.history = {
            "train": [],
            "eval": [],
        }

    def append(
        self, loss: float, mode: Union[Literal["train", "eval"], "str"] = "train"
    ):
        self.history[mode].append(float(loss))
        if len(self.history[mode]) > self.max_len:
            self.history[mode] = self.history[mode][-self.max_len :]

    def get(self, mode: Union[Literal["train", "eval"], "str"] = "train"):
        return self.history.get(mode, [])

    def save(self, path: Optional[PathLike] = None):
        if path is None:
            path = f"logs/history_{get_current_time()}.json"
        save_json(path, self.history, indent=2)
        self.last_file = path

    def load(self, path: Optional[PathLike] = None):
        if path is None:
            path = self.last_file
        self.history = load_json(path, [])
        self.last_file = path

    def plot(
        self,
        history_keys: Union[str, List[str]],
        max_amount: int = 0,
        title: str = "Loss",
    ):
        if isinstance(history_keys, str):
            history_keys = [history_keys]
        return plot_view(
            {k: v for k, v in self.history.items() if k in history_keys},
            title,
            max_amount,
        )


class _Devices_Base(nn.Module):
    _device: torch.device = ROOT_DEVICE

    @property
    def device(self):
        return self._device

    @device.setter
    def device(self, device: Union[torch.device, str]):
        assert isinstance(device, (str, torch.device))
        self._device = torch.device(device) if isinstance(device, str) else device

    def _apply_device(self):
        """Add here components that are needed to have device applied to them,
        that usually the '.to()' function fails to apply

        example:
        ```
        def _apply_device_to(self):
            self.my_tensor = self.my_tensor.to(device=self.device)
        ```
        """
        pass

    def _to_dvc(
        self, device_name: str, device_id: Optional[Union[int, torch.device]] = None
    ):
        device = device_name
        if device_id is not None:
            if isinstance(device_id, Number):
                device += ":" + str(int(device_id))
            elif hasattr(device_id, "index"):
                device += ":" + str(device_id.index)
        self.device = device
        self._apply_device()

    def to(self, *args, **kwargs):
        device, dtype, non_blocking, convert_to_format = torch._C._nn._parse_to(
            *args, **kwargs
        )

        if dtype is not None:
            if not (dtype.is_floating_point or dtype.is_complex):
                raise TypeError(
                    "nn.Module.to only accepts floating point or complex "
                    f"dtypes, but got desired dtype={dtype}"
                )
            if dtype.is_complex:
                warnings.warn(
                    "Complex modules are a new feature under active development whose design may change, "
                    "and some modules might not work as expected when using complex tensors as parameters or buffers. "
                    "Please file an issue at https://github.com/pytorch/pytorch/issues/new?template=bug-report.yml "
                    "if a complex module does not work as expected."
                )

        def convert(t: Tensor):
            try:
                if convert_to_format is not None and t.dim() in (4, 5):
                    return t.to(
                        device,
                        dtype if t.is_floating_point() or t.is_complex() else None,
                        non_blocking,
                        memory_format=convert_to_format,
                    )
                return t.to(
                    device,
                    dtype if t.is_floating_point() or t.is_complex() else None,
                    non_blocking,
                )
            except NotImplementedError as e:
                if str(e) == "Cannot copy out of meta tensor; no data!":
                    raise NotImplementedError(
                        f"{e} Please use torch.nn.Module.to_empty() instead of torch.nn.Module.to() "
                        f"when moving module from meta to a different device."
                    ) from None
                else:
                    raise

        self._apply(convert)
        self._to_dvc(device)
        return self

    def ipu(self, device: Optional[Union[int, torch.device]] = None) -> T:
        super().ipu(device)
        self._to_dvc("ipu", device)
        return self

    def xpu(self, device: Optional[Union[int, torch.device]] = None) -> T:
        super().xpu(device)
        self._to_dvc("xpu", device)
        return self

    def cuda(self, device: Optional[Union[int, torch.device]] = None) -> T:
        super().cuda(device)
        self._to_dvc("cuda", device)
        return self

    def mtia(self, device: Optional[Union[int, torch.device]] = None) -> T:
        super().mtia(device)
        self._to_dvc("mtia", device)
        return self

    def cpu(self) -> T:
        super().cpu()
        self._to_dvc("cpu", None)
        return self


class Model(_Devices_Base, ABC):
    """
    This makes it easier to assign a device and retrieves it later
    """

    _autocast: bool = False
    _is_unfrozen: bool = False
    # list with modules that can be frozen or unfrozen
    registered_freezable_modules: List[str] = []
    is_frozen: bool = False
    _can_be_frozen: bool = (
        False  # to control if the module can or cannot be freezed by other modules from 'Model' class
    )
    # this is to be used on the case of they module requires low-rank adapters
    _low_rank_lambda: Optional[Callable[[], nn.Module]] = (
        None  # Example: lambda: nn.Linear(32, 32, True)
    )
    low_rank_adapter: Union[nn.Identity, nn.Module, nn.Sequential] = nn.Identity()
    # never freeze:
    _never_freeze_modules: List[str] = ["low_rank_adapter"]

    # dont save list:
    _dont_save_items: List[str] = []

    @property
    def autocast(self):
        return self._autocast

    @autocast.setter
    def autocast(self, value: bool):
        self._autocast = value

    def freeze_all(self, exclude: Optional[List[str]] = None, force: bool = False):
        no_exclusions = not exclude
        no_exclusions = not exclude
        results = []
        for name, module in self.named_modules():
            if (
                name in self._never_freeze_modules
                or not force
                and name not in self.registered_freezable_modules
            ):
                results.append(
                    (
                        name,
                        "Unregistered module, to freeze/unfreeze it add its name into 'registered_freezable_modules'.",
                    )
                )
                continue
            if no_exclusions:
                self.change_frozen_state(True, module)
            elif not any(exclusion in name for exclusion in exclude):
                results.append((name, self.change_frozen_state(True, module)))
            else:
                results.append((name, "excluded"))
        return results

    def unfreeze_all(self, exclude: Optional[list[str]] = None, force: bool = False):
        """Unfreezes all model parameters except specified layers."""
        no_exclusions = not exclude
        results = []
        for name, module in self.named_modules():
            if (
                name in self._never_freeze_modules
                or not force
                and name not in self.registered_freezable_modules
            ):

                results.append(
                    (
                        name,
                        "Unregistered module, to freeze/unfreeze it add it into 'registered_freezable_modules'.",
                    )
                )
                continue
            if no_exclusions:
                self.change_frozen_state(False, module)
            elif not any(exclusion in name for exclusion in exclude):
                results.append((name, self.change_frozen_state(False, module)))
            else:
                results.append((name, "excluded"))
        return results

    def change_frozen_state(self, freeze: bool, module: nn.Module):
        assert isinstance(module, nn.Module)
        if module.__class__.__name__ in self._never_freeze_modules:
            return "Not Allowed"
        try:
            if isinstance(module, Model):
                if module._can_be_frozen:
                    if freeze:
                        return module.freeze_all()
                    return module.unfreeze_all()
                else:
                    return "Not Allowed"
            else:
                module.requires_grad_(not freeze)
                return not freeze
        except Exception as e:
            return e

    def trainable_parameters(self, module_name: Optional[str] = None):
        """Gets the number of trainable parameters from either the entire model or from a specific module."""
        if module_name is not None:
            assert hasattr(self, module_name), f"Module '{module_name}' not found."
            module = getattr(self, module_name)
            return sum(
                [
                    x.numel()
                    for x in module.parameters()
                    if hasattr(x, "requires_grad") and x.requires_grad
                ]
            )
        return sum(
            [
                x.numel()
                for x in self.parameters()
                if hasattr(x, "requires_grad") and x.requires_grad
            ]
        )

    def non_trainable_parameters(self, module_name: Optional[str] = None):
        """Gets the number of non-trainable parameters from either the entire model or from a specific module."""
        if module_name is not None:
            assert hasattr(self, module_name), f"Module '{module_name}' not found."
            module = getattr(self, module_name)
            return sum(
                [
                    x.numel()
                    for x in module.parameters()
                    if not hasattr(x, "requires_grad") or not x.requires_grad
                ]
            )
        return sum(
            [
                x.numel()
                for x in self.parameters()
                if not hasattr(x, "requires_grad") or not x.requires_grad
            ]
        )

    def extract_weights(self, module_name: Optional[str] = None) -> List[Tensor]:
        """Returns the weights of the model entry model or from a specified module"""
        if module_name is not None:
            assert hasattr(self, module_name), f"Module '{module_name}' not found."
            module = getattr(self, module_name)
            params = []
            if isinstance(module, nn.Module):
                return [x.data.detach() for x in module.parameters()]
            elif isinstance(module, (Tensor, nn.Parameter)):
                return [module.data.detach()]
            raise (f"{module_name} is has no weights")
        return [x.data.detach() for x in self.parameters()]

    def format_trainable_parameters(self, module_name: Optional[str] = None) -> str:
        params = format(self.trainable_parameters(module_name), ",").replace(",", ".")
        return params

    def format_non_trainable_parameters(self, module_name: Optional[str] = None) -> str:
        params = format(self.non_trainable_parameters(module_name), ",").replace(
            ",", "."
        )
        return params

    def print_trainable_parameters(self, module_name: Optional[str] = None) -> str:
        fmt = self.format_trainable_parameters(module_name)
        if module_name is not None:
            print(f"Trainable parameter(s) for module '{module_name}': {fmt}")
        else:
            print(f"Trainable parameter(s): {fmt}")

    def print_non_trainable_parameters(self, module_name: Optional[str] = None) -> str:
        fmt = self.format_non_trainable_parameters(module_name)
        if module_name is not None:
            print(f"Non-Trainable parameter(s) for module '{module_name}': {fmt}")
        else:
            print(f"Non-Trainable parameter(s): {fmt}")

    @classmethod
    def from_pretrained(
        cls,
        model_path: Union[str, PathLike],
        model_config: Optional[Union[str, PathLike]] = None,
        model_config_dict: Optional[Dict[str, Any]] = None,
    ):
        """TODO: Finish this implementation or leave it as an optional function."""
        assert isinstance(model_path, (str, PathLike, bytes))
        model_path = get_weights(model_path)
        model_config = get_config(model_config, model_config_dict)
        return model_path, model_config

    def save_weights(
        self,
        path: Union[Path, str],
        replace: bool = False,
        save_with_adapters: bool = False,
    ):
        path = Path(path)
        model_dir = path
        if path.exists():
            if path.is_dir():
                model_dir = Path(path, f"model_{get_current_time()}.pt")
            elif path.is_file():
                if replace:
                    path.unlink()
                else:
                    model_dir = Path(path.parent, f"model_{get_current_time()}.pt")
        else:
            if not "." in str(path):
                model_dir = Path(path, f"model_{get_current_time()}.pt")
        path.parent.mkdir(exist_ok=True, parents=True)

        state_dict = self.state_dict()
        if not save_with_adapters or isinstance(self.low_rank_adapter, nn.Identity):
            state_dict.pop("low_rank_adapter", None)
        torch.save(obj=state_dict, f=str(model_dir))

    def save_lora(
        self,
        path: Union[Path, str],
        replace: bool = False,
    ):
        assert not isinstance(
            self.low_rank_adapter, nn.Identity
        ), "The adapter is empty!"
        path = Path(path)
        model_dir = path
        if path.exists():
            if path.is_dir():
                model_dir = Path(path, f"adapter_{get_current_time()}.pt")
            elif path.is_file():
                if replace:
                    path.unlink()
                else:
                    model_dir = Path(path.parent, f"adapter_{get_current_time()}.pt")
        else:
            if not "." in str(path):
                model_dir = Path(path, f"adapter_{get_current_time()}.pt")

        state_dict = self.low_rank_adapter.state_dict()
        torch.save(obj=state_dict, f=str(model_dir))

    def load_lora(
        self,
        path: Union[Path, str],
        raise_if_not_exists: bool = False,
        strict: bool = False,
        assign: bool = False,
        weights_only: bool = True,
        mmap: Optional[bool] = None,
        **pickle_load_args,
    ):
        assert (
            self._low_rank_lambda is not None
        ), "Lora not implemented! '_low_rank_lambda' must be setup to deploy a proper module"
        path = Path(path)
        if not path.exists():
            assert not raise_if_not_exists, "Path does not exists!"
            return None

        if path.is_dir():
            possible_files = list(Path(path).rglob("adapter_*.pt"))
            assert (
                possible_files or not raise_if_not_exists
            ), "No model could be found in the given path!"
            if not possible_files:
                return None
            path = sorted(possible_files)[-1]

        state_dict = torch.load(
            str(path), weights_only=weights_only, mmap=mmap, **pickle_load_args
        )
        self.low_rank_adapter = None
        gc.collect()
        self.low_rank_adapter = self._low_rank_lambda()
        incompatible_keys = self.low_rank_adapter.load_state_dict(
            state_dict,
            strict=strict,
            assign=assign,
        )
        return incompatible_keys

    def load_weights(
        self,
        path: Union[Path, str],
        raise_if_not_exists: bool = False,
        strict: bool = False,
        assign: bool = False,
        weights_only: bool = False,
        mmap: Optional[bool] = None,
        **pickle_load_args,
    ):
        path = Path(path)
        if not path.exists():
            assert not raise_if_not_exists, "Path does not exists!"
            return None
        if path.is_dir():
            possible_files = list(Path(path).rglob("*.pt"))
            assert (
                possible_files or not raise_if_not_exists
            ), "No model could be found in the given path!"
            if not possible_files:
                return None
            path = sorted(possible_files)[-1]
        state_dict = torch.load(
            str(path), weights_only=weights_only, mmap=mmap, **pickle_load_args
        )
        incompatible_keys = self.load_state_dict(
            state_dict,
            strict=strict,
            assign=assign,
        )
        return incompatible_keys

    def lora_step(self, *arg, **kwargs):
        raise NotImplementedError("Not implemented for this model")

    @torch.no_grad()
    def inference(self, *args, **kwargs):
        if self.training:
            self.eval()
        return self(*args, **kwargs)

    def train_step(
        self,
        *inputs,
        **kwargs,
    ):
        """Train Step"""
        if not self.training:
            self.train()
        return self(*inputs, **kwargs)

    def __call__(self, *args, **kwds) -> POSSIBLE_OUTPUT_TYPES:
        with torch.autocast(device_type=self.device.type, enabled=self.autocast):
            return super().__call__(*args, **kwds)

    @abstractmethod
    def forward(
        self, *args, **kwargs
    ) -> Union[Tensor, Sequence[Tensor], Dict[Any, Union[Any, Tensor]]]:
        pass
