import numpy as np
from tqdm import tqdm

def ttest_tstat(
    a: np.array,
    b: np.array,
    axis: int = -1
):
    assert len(a.shape) > 1, "[ctxseg] inputs must have dims > 1"
    n = a.shape[axis]

    d = (a - b)
    s = np.std(d, ddof=1, axis=axis)

    dm = np.mean(d, axis=axis)
    denom = s / np.sqrt(n)

    with np.errstate(divide="ignore", invalid="ignore"):
        tstat = np.divide(dm, denom)

    return tstat

def seg_ttest(
    x: np.ndarray,
    win: np.ndarray,
    w: int,
    s: int,
    t_thresh: float,
) -> np.ndarray:
    """
    Performs CTX-SEG operation using NumPy.

    Args:
        x (np.ndarray): Signal, shape (C, N)
        win (np.ndarray): Window function array, shape (w,)
        w (int): Window size.
        s (int): Stride.
        t_thresh (float): Threshold for t-statistic.

    Returns:
        np.ndarray: Segment boundaries.
    """
    C, N = x.shape
    z = np.full([C, N], False) # Boundaries

    def lfftm(t: np.array, eps = 1e-12) -> np.array:
        t_range = np.arange(w) + t
        w_x = x[:, t_range]
        w_x = np.multiply(w_x, win)
        w_x = np.abs(np.fft.rfft(w_x, axis=1))
        w_x = np.log(w_x + eps)
        return w_x # (C, F)

    r = np.tile(0, C) # Reference pointer (C,)
    wr = lfftm(0) # Reference window (C, F)
    for t in tqdm(np.arange(s, N - w, step=s), desc="[ctxseg] segmenting"):
        wt = lfftm(t) # Test window (C, F)
        t_stat = ttest_tstat(wr, wt, axis=1)
        is_valid = r + s <= t
        is_boundary = is_valid & (np.abs(t_stat) > t_thresh)
        b = t + w
        z[:, b] = np.where(is_boundary, True, z[:, b])
        if b >= N:
            break
        r = np.where(is_boundary, b + 1, r)
        wr = np.where(is_boundary, lfftm(r), wr)
        continue

    return z