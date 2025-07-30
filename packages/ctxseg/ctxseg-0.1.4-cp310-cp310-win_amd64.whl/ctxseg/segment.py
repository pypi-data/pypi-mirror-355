import numpy as np
from scipy import stats
from scipy import signal
import mne
import math
from typing import Union, Literal, Tuple, List


def segment_signal(
    x: np.ndarray,
    w: int,
    s: int = 1,
    alpha: float = 0.05,
    win_fn: Union[str, np.ndarray] = "hamming",
    engine: Literal["c", "npy"] = "c"
) -> np.ndarray:
    """Performs adaptive segmentation using CTX-SEG on a signal.
        C is number of channels. N is length of signal.

    Args:
        x (np.ndarray): Signal, shape (C, N).
        w (int): Window size.
        s (int, optional): Stride. Defaults to 1.
        alpha (float, optional): Significance threshold. Defaults to 0.05.
        win_fn (Union[str, np.ndarray], optional): Window function to apply
            before performing FFT. Defaults to "hamming".
        engine (["c" | "npy"], optional): Backend implementation to use.
            Defaults to "c".

    Raises:
        NotImplementedError: If an unsupported engine is specified.

    Returns:
        np.ndarray: Segment boundaries, shape (C, N).
    """
    assert len(x.shape) == 2, "[ctxseg] signal x must have shape (C, N)"

    print(
        f"[ctxseg] segmenting with w={w}, s={s}, α={alpha}"
    )

    # Getting p-values on every iteration is very slow
    # instead, check the t_stat directly, assuming a symmetrical distribution
    dof = w // 2
    t_thresh = stats.t.ppf(1 - (alpha / 2), dof)

    # Handle window function
    if isinstance(win_fn, str):
        win_fn = signal.windows.get_window(window=win_fn, Nx=w)
    assert isinstance(win_fn, np.ndarray), "[ctxseg] window fn must be an array"
    assert win_fn.shape == (w,), "[ctxseg] window fn must have shape (w,)"

    # Perform segmentation
    if engine == "c":
        from ctxseg.c import seg_ttest

    elif engine == "npy":
        from ctxseg.seg_ttest import seg_ttest

    else:
        raise NotImplementedError(f"[ctxseg] {engine} is not a valid engine")

    z = seg_ttest(x=x, win=win_fn, w=w, s=s, t_thresh=t_thresh)

    return z


def segment_signal_varri(
    x: np.ndarray,
    w: int,
    thr_win: float,
    det_win: float,
    s: int = 1,
    kF: float = 7,
    kA: float = 1,
):
    """Performs adaptive segmentation using the modified Varri method from
        Krajča et al., 1991 (DOI: 10.1016/0020-7101(91)90028-D).

    Args:
        x (np.ndarray): Signal, shape (C, N).
        w (int): Window size.
        thr_win (float, optional): Window size for calculation of adaptive
            threshold in seconds.
        det_win (float, optional): Window size for calculation of local maxima.
        s (int, optional): Stride. Defaults to 1.
        kF (float, optional): Frequency coefficient. Defaults to 7.
        kA (float, optional): Amplitude coefficient. Defaults to 1.
    """
    from ctxseg.c import seg_modified_varri
    z, G = seg_modified_varri(
        x=x, w=w, s=s, kF=kF, kA=kA,
        det_win=det_win, thr_win=thr_win
    )
    return z, G


def segment_signal_nleo(
    x: np.ndarray,
    w: int,
    det_win: float,
    s: int = 1,
):
    """Performs adaptive segmentation using the non-linear energy operator
        (NLEO) from Agarwal & Gotman, 1999 (DOI: 10.1109/ISCAS.1999.779976).

    Args:
        x (np.ndarray): Signal, shape (C, N).
        w (int): Window size.
        det_win (float, optional): Window size for calculation of local maxima.
        s (int, optional): Stride. Defaults to 1.
    """
    from ctxseg.c import seg_nleo
    z, G = seg_nleo(x=x, w=w, s=s, det_win=det_win)
    return z, G


def segment_signal_sps(
    x: np.ndarray,
    w: int,
    alpha: float,
    sfreq: float,
    freq_bins: List[Tuple[float, float]] = [
        (0, 0.5), (0.5, 4),
        (4, 6), (6, 8),
        (8, 10), (10, 12),
        (12, 15), (15, 20), (20, 30)
    ],
    s: int = 1,
):
    """Performs adaptive segmentation using the Spectral Power Statistics
        (SPS) from Jakaite et al., 2011 (DOI: 10.1109/CBMS.2011.5999109).
        Default 9 frequency bands in Hz:
        1. Subdelta [0 - 0.5)
        2. Delta [0.5, 4)
        3. Theta1 [4, 6)
        4. Theta2 [6, 8)
        5. Alpha1 [8, 10)
        6. Alpha2 [10, 12)
        7. Beta1 [12, 15)
        8. Beta2 [15, 20)
        9. Beta3 [20, 30)

    Args:
        x (np.ndarray): Signal, shape (C, N).
        w (int): Window size.
        alpha (float, optional): Significance threshold. Defaults to 0.05.
        freq_bins (List[Tuple[float, float]], optional): Frequency bins used
            for statistical comparison.
        s (int, optional): Stride. Defaults to 1.
    """
    from ctxseg.c import seg_sps

    # Convert freq_bins to 2d np array of shape (F, 2)
    # Calculate the starting and ending indices for each frequency bin
    freq_bins = np.array(freq_bins)
    freqs = np.fft.rfftfreq(n=w, d=(1 / sfreq))
    start_indices = np.searchsorted(freqs, freq_bins[:, 0])
    end_indices = np.searchsorted(freqs, freq_bins[:, 1])
    freq_bins = np.column_stack((start_indices, end_indices))

    # Get critical value threshold
    # The b_i values are the interpolation coefficients from Table 2
    # of Scholz and Stephens 1987
    # https://github.com/scipy/scipy/blob/v1.15.2/scipy/stats/_morestats.py#L2379
    m = 2 - 1 # (k - 1)
    b0 = np.array([0.675, 1.281, 1.645, 1.96, 2.326, 2.573, 3.085])
    b1 = np.array([-0.245, 0.25, 0.678, 1.149, 1.822, 2.364, 3.615])
    b2 = np.array([-0.105, -0.305, -0.362, -0.391, -0.396, -0.345, -0.154])
    crits = b0 + b1 / math.sqrt(m) + b2 / m
    sigs = np.array([0.25, 0.1, 0.05, 0.025, 0.01, 0.005, 0.001])
    threshold = {sig : crit for sig, crit in zip(sigs, crits)}[alpha]

    z, G = seg_sps(x=x, w=w, s=s, freq_bins=freq_bins, crit=threshold)
    return z, G


def segment_raw(
    raw: mne.io.Raw,
    w: int,
    s: int = 1,
    alpha: float = 0.05,
    win_fn: Union[str, np.ndarray] = "hamming",
    engine: Literal["c", "npy"] = "c",
    picks: Union[str, list, np.ndarray] = None
) -> mne.io.Raw:

    x = raw.get_data(picks=picks)
    z = segment_signal(x=x, w=w, s=s, alpha=alpha, win_fn=win_fn, engine=engine)
    # TODO add z as annotation
    raise NotImplementedError("[ctxseg] not implemented")

    return