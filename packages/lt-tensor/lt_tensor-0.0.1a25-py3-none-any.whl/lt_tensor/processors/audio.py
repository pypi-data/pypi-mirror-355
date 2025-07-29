__all__ = ["AudioProcessor"]
from lt_tensor.torch_commons import *
from lt_utils.common import *
import librosa
import torchaudio
import numpy as np
from lt_tensor.model_base import Model
from lt_utils.type_utils import is_file, is_array
from lt_utils.file_ops import FileScan, get_file_name, path_to_str
from torchaudio.functional import detect_pitch_frequency
import torch.nn.functional as F

DEFAULT_DEVICE = torch.tensor([0]).device


class AudioProcessor(Model):
    def __init__(
        self,
        sample_rate: int = 24000,
        n_mels: int = 80,
        n_fft: int = 1024,
        win_length: Optional[int] = None,
        hop_length: Optional[int] = None,
        f_min: float = 0,
        f_max: float = 12000.0,
        center: bool = True,
        mel_scale: Literal["htk", "slaney"] = "htk",
        std: int = 4,
        mean: int = -4,
        n_iter: int = 32,
        window: Optional[Tensor] = None,
        normalized: bool = False,
        onesided: Optional[bool] = None,
    ):
        super().__init__()
        self.mean = mean
        self.std = std
        self.n_mels = n_mels
        self.n_fft = n_fft
        self.n_stft = n_fft // 2 + 1
        self.f_min = f_min
        self.f_max = max(min(f_max, 12000), self.f_min + 1)
        self.n_iter = n_iter
        self.hop_length = hop_length or n_fft // 4
        self.win_length = win_length or n_fft
        self.sample_rate = sample_rate
        self.center = center
        self._mel_spec = torchaudio.transforms.MelSpectrogram(
            sample_rate=sample_rate,
            n_mels=n_mels,
            n_fft=n_fft,
            win_length=win_length,
            hop_length=hop_length,
            center=center,
            f_min=f_min,
            f_max=f_max,
            mel_scale=mel_scale,
            onesided=onesided,
            normalized=normalized,
        )
        self.mel_rscale = torchaudio.transforms.InverseMelScale(
            n_stft=self.n_stft,
            n_mels=n_mels,
            sample_rate=sample_rate,
            f_min=f_min,
            f_max=f_max,
            mel_scale=mel_scale,
        )
        self.giffin_lim = torchaudio.transforms.GriffinLim(
            n_fft=n_fft,
            n_iter=n_iter,
            win_length=win_length,
            hop_length=hop_length,
        )
        self.normalized = normalized
        self.onesided = onesided

        self.register_buffer(
            "window",
            (torch.hann_window(self.win_length) if window is None else window),
        )

    def from_numpy(
        self,
        array: np.ndarray,
        device: Optional[torch.device] = None,
        dtype: Optional[torch.dtype] = None,
    ):
        converted = torch.from_numpy(array)
        if not any([device is not None, dtype is not None]):
            return converted
        return converted.to(device=device, dtype=dtype)

    def from_numpy_batch(
        self,
        arrays: List[np.ndarray],
        device: Optional[torch.device] = None,
        dtype: Optional[torch.dtype] = None,
    ):
        stacked = torch.stack([torch.from_numpy(x) for x in arrays])
        if not any([device is not None, dtype is not None]):
            return stacked
        return stacked.to(device=device, dtype=dtype)

    def to_numpy_safe(self, tensor: Tensor):
        return tensor.detach().to(DEFAULT_DEVICE).numpy(force=True)

    def compute_rms(
        self,
        audio: Union[Tensor, np.ndarray],
        mel: Optional[Tensor] = None,
    ):
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
            gt_mel = lambda idx: mel[idx, :, :]

        else:
            gt_mel = lambda idx: None
        audio = self.to_numpy_safe(audio)
        if B == 1:
            _r = librosa.feature.rms(
                y=audio, frame_length=self.n_fft, hop_length=self.hop_length
            )[0]
            rms = self.from_numpy(_r, default_device, default_dtype)

        else:
            rms_ = []
            for i in range(B):
                _r = librosa.feature.rms(
                    y=audio[i, :],
                    S=gt_mel(i),
                    frame_length=self.n_fft,
                    hop_length=self.hop_length,
                )[0]
                rms_.append(_r)
            rms = self.from_numpy_batch(rms_, default_device, default_dtype)

        return rms

    def compute_pitch(
        self,
        audio: Tensor,
    ):
        default_dtype = audio.dtype
        default_device = audio.device
        if audio.ndim > 1:
            B = audio.shape[0]
        else:
            B = 1
        fmin = max(self.f_min, 80)
        if B == 1:
            f0 = self.from_numpy(
                librosa.yin(
                    self.to_numpy_safe(audio),
                    fmin=fmin,
                    fmax=min(self.f_max, self.sample_rate // 2 - 1),
                    frame_length=self.n_fft,
                    sr=self.sample_rate,
                    hop_length=self.hop_length,
                    center=self.center,
                ),
                default_device,
                default_dtype,
            )

        else:
            f0_ = []
            for i in range(B):
                r = librosa.yin(
                    self.to_numpy_safe(audio[i, :]),
                    fmin=fmin,
                    fmax=self.f_max,
                    frame_length=self.n_fft,
                    sr=self.sample_rate,
                    hop_length=self.hop_length,
                    center=self.center,
                )
                f0_.append(r)
            f0 = self.from_numpy_batch(f0_, default_device, default_dtype)

        # librosa.pyin(self.f_min, self.f_max)
        return f0  # dict(f0=f0, attention_mask=f0 != f_max)

    def compute_pitch_torch(self, audio: Tensor):
        return detect_pitch_frequency(
            audio,
            sample_rate=self.sample_rate,
            frame_time=self.n_fft,
            win_length=self.win_length,
            freq_low=max(self.f_min, 1),
            freq_high=self.f_max,
        )

    def interpolate_tensor(
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
        try:
            return torch.istft(
                spec * torch.exp(phase * 1j),
                n_fft=n_fft or self.n_fft,
                hop_length=hop_length or self.hop_length,
                win_length=win_length or self.win_length,
                window=torch.hann_window(
                    win_length or self.win_length, device=spec.device
                ),
                center=self.center,
                normalized=self.normalized,
                onesided=self.onesided,
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
                n_fft=self.n_fft,
                hop_length=self.hop_length,
                win_length=self.win_length,
                window=self.window,
                center=self.center,
                pad_mode="reflect",
                normalized=self.normalized,
                onesided=self.onesided,
                return_complex=True,  # needed for the istft
            )
            return torch.istft(
                spectrogram
                * torch.full(
                    spectrogram.size(),
                    fill_value=1,
                    device=spectrogram.device,
                ),
                n_fft=self.n_fft,
                hop_length=self.hop_length,
                win_length=self.win_length,
                window=self.window,
                length=length,
                center=self.center,
                normalized=self.normalized,
                onesided=self.onesided,
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
        base: float = 1e-5,
        add_base: bool = True,
    ) -> Tensor:
        """Returns: [B, M, ML]"""
        mel_tensor = self._mel_spec(wave.to(self.device))  # [M, ML]
        if not add_base:
            return (mel_tensor - self.mean) / self.std
        return (
            (torch.log(base + mel_tensor.unsqueeze(0)) - self.mean) / self.std
        ).squeeze()

    def inverse_mel_spectogram(self, mel: Tensor, n_iter: Optional[int] = None):
        if isinstance(n_iter, int) and n_iter != self.n_iter:
            self.giffin_lim.n_iter = n_iter
            self.n_iter = n_iter
        return self.giffin_lim.forward(
            self.mel_rscale(mel),
        )

    def load_audio(
        self,
        path: PathLike,
        top_db: float = 30,
        normalize: bool = False,
        alpha: float = 1.0,
    ) -> Tensor:
        is_file(path, True)
        wave, sr = librosa.load(str(path), sr=self.sample_rate)
        wave, _ = librosa.effects.trim(wave, top_db=top_db)
        if sr != self.sample_rate:
            wave = librosa.resample(wave, orig_sr=sr, target_sr=self.sample_rate)
        if normalize:
            wave = librosa.util.normalize(wave)
        if alpha not in [0.0, 1.0]:
            wave = wave * alpha
        return torch.from_numpy(wave).float().unsqueeze(0)

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

    def find_audio_text_pairs(
        self,
        path,
        additional_extensions: List[str] = [],
        text_file_patterns: List[str] = [".normalized.txt", ".original.txt"],
    ):
        is_array(text_file_patterns, True, validate=True)  # Rases if empty or not valid
        additional_extensions = [
            x
            for x in additional_extensions
            if isinstance(x, str)
            and "*" in x
            and not any(list(map(lambda y: y in x), text_file_patterns))
        ]
        audio_files = self.find_audios(path, additional_extensions)
        results = []
        for audio in audio_files:
            base_audio_dir = Path(audio).parent
            audio_name = get_file_name(audio, False)
            for pattern in text_file_patterns:
                possible_txt_file = Path(base_audio_dir, audio_name + pattern)
                if is_file(possible_txt_file):
                    results.append((audio, path_to_str(possible_txt_file)))
                    break
        return results

    def stft_loss(
        self,
        signal: Tensor,
        ground: Tensor,
    ):
        ground = F.interpolate(ground, signal.shape[-1]).to(signal.device)
        if ground.ndim != signal.ndim:
            assert ground.ndim in [1, 2, 3]
            assert signal.ndim in [1, 2, 3]
            if ground.ndim == 3:
                ground = ground.squeeze(1)
            elif ground.ndim == 1:
                ground = ground.unsqueeze(0)
            if signal.ndim == 3:
                signal = signal.squeeze(1)
            elif signal.ndim == 1:
                signal = signal.unsqueeze(0)
        return F.l1_loss(signal, ground)

    @staticmethod
    def plot_spectrogram(spectrogram, ax_):
        import matplotlib.pylab as plt

        fig, ax = plt.subplots(figsize=(10, 2))
        im = ax.imshow(spectrogram, aspect="auto", origin="lower", interpolation="none")
        plt.colorbar(im, ax=ax)

        fig.canvas.draw()
        plt.close()

        return fig

    def forward(
        self,
        *inputs: Union[Tensor, float],
        ap_task: Literal[
            "get_mel", "get_loss", "inv_transform", "revert_mel"
        ] = "get_mel",
        **inputs_kwargs,
    ):
        if ap_task == "get_mel":
            return self.compute_mel(*inputs, **inputs_kwargs)
        elif ap_task == "get_loss":
            return self.stft_loss(*inputs, **inputs_kwargs)
        elif ap_task == "inv_transform":
            return self.inverse_transform(*inputs, **inputs_kwargs)
        elif ap_task == "revert_mel":
            return self.inverse_mel_spectogram(*inputs, **inputs_kwargs)
        else:
            raise ValueError(f"Invalid task '{ap_task}'")
