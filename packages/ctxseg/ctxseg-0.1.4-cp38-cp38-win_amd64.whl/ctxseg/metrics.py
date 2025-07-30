import numpy as np
from numpy import ndarray
from typing import Tuple


def boundaries_from_time(
    times: ndarray,
    size: int,
    sfreq: float
) -> Tuple[str, int]:
    """
    Converts an array of boundaries times to NLTK formatted segmentation
    sequence. (See: https://www.nltk.org/api/nltk.metrics.segmentation.html)

    Args:
        times (ndarray): Array of boundary times in seconds.
        size (int): Size of the sequence.
        sfreq (float): Sample frequency.

    Returns:
        str: Segmentation sequence, where 1 is the position of a boundary.
            Eg. "00100001"
        int: Number of boundaries contained in the sequence.
    """
    boundaries = ["0"] * size
    n_boundaries = len(times)
    for onset_time in times:
        boundaries[int(onset_time * sfreq)] = "1"
    assert np.array(boundaries, dtype=int).sum() == n_boundaries
    boundaries = "".join(boundaries)
    return boundaries, n_boundaries


def boundaries_from_detections(z: ndarray) -> Tuple[str, int]:
    """
    Converts a boolean boundary sequence to NLTK formatted segmentation
    sequence. (See: https://www.nltk.org/api/nltk.metrics.segmentation.html)

    Args:
        z (ndarray): A Boolean array with the same length as the number of
        samples in the signal, where each element represents a sample and a
        value of True indicates a boundary position.

    Returns:
        str: Segmentation sequence, where 1 is the position of a boundary.
            Eg. "00100001"
        int: Number of boundaries contained in the sequence.
    """
    size = len(z)
    boundaries = ["0"] * size
    boundary_idx = np.where(z)[0]
    n_boundaries = len(boundary_idx)
    for idx in boundary_idx:
        boundaries[idx] = "1"
    assert np.array(boundaries, dtype=int).sum() == n_boundaries
    boundaries = "".join(boundaries)
    return boundaries, n_boundaries


def times_from_boundaries(s: str, sfreq: float) -> ndarray:
    s = np.array(list(s))
    times = np.where(s == "1")[0] / sfreq
    return times


def detection_delay(
    ref: str,
    hyp: str,
    sfreq: float
) -> float:
    """
    Calculates the detection delay, being the time difference, in seconds,
    between a reference boundary and a hypothesis boundary that occurs at
    or after the reference. If no hypothesis boundary exists after the
    reference, the time difference between the end of sequence and the reference boundary is taken to be the detection delay.

    Args:
        ref (str): Reference segment sequence in NLTK format, Eg. "00100010000"
            would have boundaries at position 2 and 6.
        hyp (str): Hypothesis segment sequence in NLTK format.
        sfreq (float): Sampling frequency.

    Returns:
        float: average detection delay in seconds.
    """
    n_samples = len(ref)
    assert len(hyp) == n_samples, "[delay] ref and hyp have same len"

    # Get the boundary times
    ref_times = times_from_boundaries(ref, sfreq)
    hyp_times = times_from_boundaries(hyp, sfreq)
    max_time = n_samples / sfreq
    assert ref_times.max() < max_time, "[delay] ref times must be < max_time"

    # Add the maximum time to the hypothesis for the case where no hyp exists
    hyp_times = np.hstack([hyp_times, np.array([max_time])])

    # Match hyp to ref, where ref occurs before hyp, then calculate the delay
    hyp_idx = np.searchsorted(a=hyp_times, v=ref_times, side="left")
    delays = hyp_times[hyp_idx] - ref_times
    return delays.mean()


def detection_sensitivity(
    ref: str,
    hyp: str,
    sfreq: float
) -> float:
    """
    Calculates the detection sensitivity, being the proportion of reference
    boundaries are discovered at or after the reference but before the following
    reference.

    Args:
        ref (str): Reference segment sequence in NLTK format. Eg. "00100010000"
            would have boundaries at position 2 and 6.
        hyp (str): Hypothesis segment sequence in NLTK format.
        sfreq (float): Sampling frequency.

    Returns:
        float: detection sensitivity between [0.0, 1.0].
    """
    n_samples = len(ref)
    assert len(hyp) == n_samples, "[delay] ref and hyp have same len"

    # Get the boundary times
    ref_times = times_from_boundaries(ref, sfreq)
    hyp_times = times_from_boundaries(hyp, sfreq)
    max_time = n_samples / sfreq
    assert ref_times.max() < max_time, "[delay] ref times must be < max_time"

    # Match hyp to ref, where ref occurs before hyp
    # then calculate the proportion of ref that has a hyp
    ref_with_hyp = np.searchsorted(a=ref_times, v=hyp_times, side="left") - 1
    ref_with_hyp = np.unique(ref_with_hyp[ref_with_hyp >= 0])
    sensitivity = len(ref_with_hyp) / len(ref_times)
    return sensitivity