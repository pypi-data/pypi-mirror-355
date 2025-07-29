__all__ = ["AudioProcessor", "AudioProcessorConfig"]
from lt_tensor.torch_commons import *
from lt_utils.common import *
import librosa
import torchaudio
import numpy as np
from lt_tensor.model_base import Model
from lt_utils.misc_utils import default
from lt_utils.type_utils import is_file, is_array
from lt_utils.file_ops import FileScan, get_file_name, path_to_str
from torchaudio.functional import detect_pitch_frequency
import torch.nn.functional as F

DEFAULT_DEVICE = torch.tensor([0]).device

from lt_tensor.config_templates import ModelConfig


class AudioProcessorConfig(ModelConfig):
    sample_rate: int = 24000
    n_mels: int = 80
    n_fft: int = 1024
    win_length: int = 1024
    hop_length: int = 256
    f_min: float = 0
    f_max: float = 8000.0
    center: bool = True
    mel_scale: Literal["htk" "slaney"] = "htk"
    std: int = 4
    mean: int = -4
    n_iter: int = 32
    window: Optional[Tensor] = None
    normalized: bool = False
    onesided: Optional[bool] = None
    n_stft: int = None

    def __init__(
        self,
        sample_rate: int = 24000,
        n_mels: int = 80,
        n_fft: int = 1024,
        win_length: Optional[int] = None,
        hop_length: Optional[int] = None,
        f_min: float = 1,
        f_max: float = 12000.0,
        center: bool = True,
        mel_scale: Literal["htk", "slaney"] = "htk",
        std: int = 4,
        mean: int = -4,
        normalized: bool = False,
        onesided: Optional[bool] = None,
        *args,
        **kwargs,
    ):
        settings = {
            "sample_rate": sample_rate,
            "n_mels": n_mels,
            "n_fft": n_fft,
            "win_length": win_length,
            "hop_length": hop_length,
            "f_min": f_min,
            "f_max": f_max,
            "center": center,
            "mel_scale": mel_scale,
            "std": std,
            "mean": mean,
            "normalized": normalized,
            "onesided": onesided,
        }
        super().__init__(**settings)
        self.post_process()

    def post_process(self):
        self.f_min = max(self.f_min, 1)
        self.f_max = max(min(self.f_max, self.n_fft // 2), self.f_min + 1)
        self.n_stft = self.n_fft // 2 + 1
        self.hop_length = default(self.hop_length, self.n_fft // 4)
        self.win_length = default(self.win_length, self.n_fft)


def _comp_rms_helper(i: int, audio: Tensor, mel: Optional[Tensor]):
    if mel is None:
        return {"y": audio[i, :]}
    return {"y": audio[i, :], "S": mel[i, :, :]}


class AudioProcessor(Model):
    def __init__(
        self,
        config: AudioProcessorConfig = AudioProcessorConfig(),
        window: Optional[Tensor] = None,
    ):
        super().__init__()
        self.cfg = config
        self._mel_spec = torchaudio.transforms.MelSpectrogram(
            sample_rate=self.cfg.sample_rate,
            n_mels=self.cfg.n_mels,
            n_fft=self.cfg.n_fft,
            win_length=self.cfg.win_length,
            hop_length=self.cfg.hop_length,
            center=self.cfg.center,
            f_min=self.cfg.f_min,
            f_max=self.cfg.f_max,
            mel_scale=self.cfg.mel_scale,
            onesided=self.cfg.onesided,
            normalized=self.cfg.normalized,
        )
        self.griffin_lm_iters = 32
        self.mel_rscale = torchaudio.transforms.InverseMelScale(
            n_stft=self.cfg.n_stft,
            n_mels=self.cfg.n_mels,
            sample_rate=self.cfg.sample_rate,
            f_min=self.cfg.f_min,
            f_max=self.cfg.f_max,
            mel_scale=self.cfg.mel_scale,
        )
        self.giffin_lim = torchaudio.transforms.GriffinLim(
            n_fft=self.cfg.n_fft,
            win_length=self.cfg.win_length,
            hop_length=self.cfg.hop_length,
        )
        self.register_buffer(
            "window",
            (torch.hann_window(self.cfg.win_length) if window is None else window),
        )

    def _apply_device(self):
        print(f"Audio Processor Device: {self.device.type}")
        self.giffin_lim.to(device=self.device)
        self._mel_spec.to(device=self.device)
        self.mel_rscale.to(device=self.device)

    def from_numpy(
        self,
        array: np.ndarray,
        device: Optional[torch.device] = None,
        dtype: Optional[torch.dtype] = None,
    ):
        converted = torch.from_numpy(array)
        if device is None:
            device = self.device
        return converted.to(device=device, dtype=dtype)

    def from_numpy_batch(
        self,
        arrays: List[np.ndarray],
        device: Optional[torch.device] = None,
        dtype: Optional[torch.dtype] = None,
    ):
        stacked = torch.stack([torch.from_numpy(x) for x in arrays])
        if device is None:
            device = self.device
        return stacked.to(device=device, dtype=dtype)

    def to_numpy_safe(self, tensor: Union[Tensor, np.ndarray]):
        if isinstance(tensor, np.ndarray):
            return tensor
        return tensor.detach().to(DEFAULT_DEVICE).numpy(force=True)

    def compute_rms(
        self,
        audio: Optional[Union[Tensor, np.ndarray]] = None,
        mel: Optional[Tensor] = None,
        frame_length: Optional[int] = None,
        hop_length: Optional[int] = None,
        center: Optional[int] = None,
    ):
        assert any([audio is not None, mel is not None])
        rms_kwargs = dict(
            frame_length=default(frame_length, self.cfg.n_fft),
            hop_length=default(hop_length, self.cfg.hop_length),
            center=default(center, self.cfg.center),
        )

        if audio is None and mel is not None:
            return self.from_numpy(librosa.feature.rms(S=mel, **rms_kwargs)[0])
        default_dtype = audio.dtype
        default_device = audio.device
        if audio.ndim > 1:
            B = audio.shape[0]
        else:
            B = 1
            audio = audio.unsqueeze(0)

        if mel is not None:
            if mel.ndim == 2:
                assert B == 1, "Batch from mel and audio must be the same!"
                mel = mel.unsqueeze(0)
            else:
                assert B == mel.shape[0], "Batch from mel and audio must be the same!"
            mel = self.to_numpy_safe(mel)
        audio = self.to_numpy_safe(audio)
        if B == 1:
            if mel is None:
                return self.from_numpy(librosa.feature.rms(y=audio, **rms_kwargs)[0])
            return self.from_numpy(librosa.feature.rms(y=audio, S=mel, **rms_kwargs)[0])
        else:
            rms_ = []
            for i in range(B):
                _r = librosa.feature.rms(_comp_rms_helper(i, audio, mel), **rms_kwargs)[
                    0
                ]
                rms_.append(_r)
            return self.from_numpy_batch(rms_, default_device, default_dtype)

    def compute_pitch(
        self,
        audio: Tensor,
        *,
        pad_mode: str = "constant",
        trough_threshold: float = 0.1,
        fmin: Optional[float] = None,
        fmax: Optional[float] = None,
        sr: Optional[float] = None,
        frame_length: Optional[int] = None,
        hop_length: Optional[int] = None,
        center: Optional[bool] = None,
    ):
        default_dtype = audio.dtype
        default_device = audio.device
        if audio.ndim > 1:
            B = audio.shape[0]
        else:
            B = 1
        sr = default(sr, self.cfg.sample_rate)
        fmin = max(default(fmin, self.cfg.f_min), 65)
        fmax = min(default(fmax, self.cfg.f_max), sr // 2)
        frame_length = default(frame_length, self.cfg.n_fft)
        hop_length = default(hop_length, self.cfg.hop_length)
        center = default(center, self.cfg.center)
        yn_kwargs = dict(
            fmin=fmin,
            fmax=fmax,
            frame_length=frame_length,
            sr=sr,
            hop_length=hop_length,
            center=center,
            trough_threshold=trough_threshold,
            pad_mode=pad_mode,
        )
        if B == 1:
            f0 = self.from_numpy(
                librosa.yin(self.to_numpy_safe(audio), **yn_kwargs),
                default_device,
                default_dtype,
            )

        else:
            f0_ = []
            for i in range(B):
                f0_.append(librosa.yin(self.to_numpy_safe(audio[i, :]), **yn_kwargs))
            f0 = self.from_numpy_batch(f0_, default_device, default_dtype)
        return f0.squeeze()

    def compute_pitch_torch(
        self,
        audio: Tensor,
        fmin: Optional[float] = None,
        fmax: Optional[float] = None,
        sr: Optional[float] = None,
        win_length: Optional[Number] = None,
        frame_length: Optional[Number] = None,
    ):
        sr = default(sr, self.sample_rate)
        fmin = max(default(fmin, self.f_min), 1)
        fmax = min(default(fmax, self.f_max), sr // 2)
        win_length = default(win_length, self.win_length)
        frame_length = default(frame_length, self.n_fft)
        return detect_pitch_frequency(
            audio,
            sample_rate=sr,
            frame_time=frame_length,
            win_length=win_length,
            freq_low=fmin,
            freq_high=fmax,
        )

    def interpolate(
        self,
        tensor: Tensor,
        target_len: int,
        mode: Literal[
            "nearest",
            "linear",
            "bilinear",
            "bicubic",
            "trilinear",
            "area",
            "nearest-exact",
        ] = "nearest",
        align_corners: Optional[bool] = None,
        scale_factor: Optional[list[float]] = None,
        recompute_scale_factor: Optional[bool] = None,
        antialias: bool = False,
    ):
        """
        The modes available for upsampling are: `nearest`, `linear` (3D-only),
        `bilinear`, `bicubic` (4D-only), `trilinear` (5D-only)
        """

        if tensor.ndim == 2:  # [1, T]
            tensor = tensor.unsqueeze(1)  # [1, 1, T]
        elif tensor.ndim == 1:
            tensor = tensor.unsqueeze(0).unsqueeze(0)  # [1, 1, T]
        return F.interpolate(
            tensor,
            size=target_len,
            mode=mode,
            align_corners=align_corners,
            scale_factor=scale_factor,
            recompute_scale_factor=recompute_scale_factor,
            antialias=antialias,
        )

    def inverse_transform(
        self,
        spec: Tensor,
        phase: Tensor,
        n_fft: Optional[int] = None,
        hop_length: Optional[int] = None,
        win_length: Optional[int] = None,
        length: Optional[int] = None,
        *,
        _recall: bool = False,
    ):
        if win_length is not None and win_length != self.cfg.win_length:
            window = torch.hann_window(win_length, device=spec.device)
        else:
            window = self.window

        try:
            return torch.istft(
                spec * torch.exp(phase * 1j),
                n_fft=n_fft or self.cfg.n_fft,
                hop_length=hop_length or self.cfg.hop_length,
                win_length=win_length or self.cfg.win_length,
                window=window,
                center=self.cfg.center,
                normalized=self.cfg.normalized,
                onesided=self.cfg.onesided,
                length=length,
                return_complex=False,
            )
        except RuntimeError as e:
            if not _recall and spec.device != self.window.device:
                self.window = self.window.to(spec.device)
                return self.inverse_transform(
                    spec, phase, n_fft, hop_length, win_length, length, _recall=True
                )
            raise e

    def normalize_audio(
        self,
        wave: Tensor,
        length: Optional[int] = None,
        *,
        _recall: bool = False,
    ):
        try:
            spectrogram = torch.stft(
                input=wave,
                n_fft=self.cfg.n_fft,
                hop_length=self.cfg.hop_length,
                win_length=self.cfg.win_length,
                window=self.window,
                center=self.cfg.center,
                pad_mode="reflect",
                normalized=self.cfg.normalized,
                onesided=self.cfg.onesided,
                return_complex=True,
            )
            return torch.istft(
                spectrogram
                * torch.full(
                    spectrogram.size(),
                    fill_value=1,
                    device=spectrogram.device,
                ),
                n_fft=self.cfg.n_fft,
                hop_length=self.cfg.hop_length,
                win_length=self.cfg.win_length,
                window=self.window,
                length=length,
                center=self.cfg.center,
                normalized=self.cfg.normalized,
                onesided=self.cfg.onesided,
                return_complex=False,
            )
        except RuntimeError as e:
            if not _recall and wave.device != self.window.device:
                self.window = self.window.to(wave.device)
                return self.normalize_audio(wave, length, _recall=True)
            raise e

    def compute_mel(
        self,
        wave: Tensor,
        raw_mel_only: bool = False,
        eps: float = 1e-5,
        *,
        _recall: bool = False,
    ) -> Tensor:
        """Returns: [B, M, T]"""
        try:
            mel_tensor = self._mel_spec(wave.to(self.device))  # [M, T]
            if not raw_mel_only:
                mel_tensor = (
                    torch.log(eps + mel_tensor.unsqueeze(0)) - self.cfg.mean
                ) / self.cfg.std
            return mel_tensor.squeeze()

        except RuntimeError as e:
            if not _recall:
                self._mel_spec.to(self.device)
                return self.compute_mel(wave, raw_mel_only, eps, _recall=True)
            raise e

    def inverse_mel_spectogram(self, mel: Tensor, n_iter: Optional[int] = None):
        if isinstance(n_iter, int) and n_iter != self.griffin_lm_iters:
            self.giffin_lim.n_iter = n_iter
            self.griffin_lm_iters = n_iter
        return self.giffin_lim.forward(
            self.mel_rscale(mel),
        )

    def load_audio(
        self,
        path: PathLike,
        top_db: float = 30,
        normalize: bool = False,
        *,
        ref: float | Callable[[np.ndarray], Any] = np.max,
        frame_length: int = 2048,
        hop_length: int = 512,
        mono: bool = True,
        offset: float = 0.0,
        duration: Optional[float] = None,
        dtype: Any = np.float32,
        res_type: str = "soxr_hq",
        fix: bool = True,
        scale: bool = False,
        axis: int = -1,
        norm: Optional[float] = np.inf,
        norm_axis: int = 0,
        norm_threshold: Optional[float] = None,
        norm_fill: Optional[bool] = None,
    ) -> Tensor:
        is_file(path, True)
        wave, sr = librosa.load(
            str(path),
            sr=self.cfg.sample_rate,
            mono=mono,
            offset=offset,
            duration=duration,
            dtype=dtype,
            res_type=res_type,
        )
        wave, _ = librosa.effects.trim(
            wave,
            top_db=top_db,
            ref=ref,
            frame_length=frame_length,
            hop_length=hop_length,
        )
        if sr != self.cfg.sample_rate:
            wave = librosa.resample(
                wave,
                orig_sr=sr,
                target_sr=self.cfg.sample_rate,
                res_type=res_type,
                fix=fix,
                scale=scale,
                axis=axis,
            )
        if normalize:
            wave = librosa.util.normalize(
                wave,
                norm=norm,
                axis=norm_axis,
                threshold=norm_threshold,
                fill=norm_fill,
            )
        return torch.from_numpy(wave).float().unsqueeze(0).to(self.device)

    def find_audios(
        self,
        path: PathLike,
        additional_extensions: List[str] = [],
        maximum: int | None = None,
    ):
        extensions = [
            "*.wav",
            "*.aac",
            "*.m4a",
            "*.mp3",
            "*.ogg",
            "*.opus",
            "*.flac",
        ]
        extensions.extend(
            [x for x in additional_extensions if isinstance(x, str) and "*" in x]
        )
        return FileScan.files(
            path,
            extensions,
            maximum,
        )

    def stft_loss(
        self,
        signal: Tensor,
        ground: Tensor,
    ):
        with torch.no_grad():
            ground = F.interpolate(ground, signal.shape[-1]).to(signal.device)
        return F.l1_loss(signal, ground)

    def forward(
        self,
        *inputs: Union[Tensor, float],
        **inputs_kwargs,
    ):
        return self.compute_mel(*inputs, **inputs_kwargs)
