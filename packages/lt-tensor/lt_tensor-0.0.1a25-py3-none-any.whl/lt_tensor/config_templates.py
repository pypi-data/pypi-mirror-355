from lt_utils.common import *
from lt_utils.file_ops import load_json, save_json, FileScan
from lt_utils.misc_utils import log_traceback, get_current_time
from lt_utils.type_utils import is_pathlike, is_file, is_dir, is_dict, is_str
from lt_tensor.misc_utils import updateDict


class ModelConfig(ABC, OrderedDict):
    _default_settings: Dict[str, Any] = {}
    _forbidden_list: List[str] = [
        "_default_settings",
        "_forbidden_list",
    ]

    def __init__(
        self,
        **settings,
    ):
        self._default_settings = settings
        self.set_state_dict(self._default_settings)

    def reset_settings(self):
        raise NotImplementedError("Not implemented")

    def save_config(
        self,
        path: str,
    ):
        base = {
            k: v
            for k, v in self.state_dict().items()
            if isinstance(v, (str, int, float, list, tuple, dict, set, bytes))
        }

        save_json(path, base, indent=4)

    def set_value(self, var_name: str, value: str) -> None:
        assert var_name not in self._forbidden_list, "Not allowed!"
        updateDict(self, {var_name: value})
        self.update({var_name: value})

    def get_value(self, var_name: str) -> Any:
        return self.__dict__.get(var_name)

    def set_state_dict(self, new_state: dict[str, str]):
        new_state = {
            k: y for k, y in new_state.items() if k not in self._forbidden_list
        }
        updateDict(self, new_state)
        self.update(**new_state)

    def state_dict(self):
        return {k: y for k, y in self.__dict__.items() if k not in self._forbidden_list}

    @classmethod
    def from_dict(
        cls,
        dictionary: Dict[str, Any],
    ) -> "ModelConfig":
        assert is_dict(dictionary)
        return ModelConfig(**dictionary)

    @classmethod
    def from_path(cls, path_name: PathLike) -> "ModelConfig":
        assert is_file(path_name) or is_dir(path_name)
        settings = {}

        if is_file(path_name):
            settings.update(load_json(path_name, {}, errors="ignore"))
        else:
            files = FileScan.files(
                path_name,
                [
                    "*_config.json",
                    "config_*.json",
                    "*_config.json",
                    "cfg_*.json",
                    "*_cfg.json",
                    "cfg.json",
                    "config.json",
                    "settings.json",
                    "settings_*.json",
                    "*_settings.json",
                ],
            )
            assert files, "No config file found in the provided directory!"
            settings.update(load_json(files[-1], {}, errors="ignore"))
        settings.pop("path", None)
        settings.pop("path_name", None)

        return ModelConfig(**settings)
