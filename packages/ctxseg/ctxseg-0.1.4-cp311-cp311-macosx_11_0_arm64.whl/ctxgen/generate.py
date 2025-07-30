import numpy as np
from numpy import ndarray
import scipy.stats as stats
import math
import mne
from typing import List, Tuple, Union, Dict
from pathlib import Path

from ctxgen.c import calc_membrane_potential


class CtxGen:
    """Context Generator (CTX-GEN).
    Generate a synthetic signal based on user-defined context states using
    multiple integrate-and-fire (LIF) models.

    Args:
        n_neurons (int, optional): Number of neurons. Defaults to 500.
        sfreq (int, optional): Sampling frequency for output. Defaults to 256.
        sfreq_gen (int, optional): Sampling frequency for
            calculating membrane potentials. Defaults to 2048.
        v_thresh (int, optional): Threshold potential. Defaults to 24.
        tau (float, optional): Time constant. Defaults to 0.02.
        verbose (bool, optional): Defaults to True.
    """

    def __init__(
        self,
        n_neurons: int = 500,
        sfreq: int = 256,
        sfreq_gen: int = 2048,
        v_thresh: int = 24,
        tau: float = 0.02,
        verbose: bool = True
    ) -> None:
        self.M = n_neurons
        self.v_thresh = v_thresh
        self.tau = tau
        self.sfreq = sfreq
        if not sfreq_gen:
            sfreq_gen = sfreq
        assert sfreq_gen >= sfreq, "[ctxgen] sfreq_gen must be >= sfreq"
        assert (sfreq_gen / sfreq) % 1 == 0., \
            "[ctxgen] sfreq_gen must be an int multiple of sfreq"
        self.delta_t = 1 / sfreq_gen
        self.verbose = verbose

        if verbose:
            print("[ctxgen] number of neurons:", n_neurons)
            print("[ctxgen] output sample frequency (Hz)", self.sfreq)
            print("[ctxgen] generation sample frequency (Hz):", sfreq_gen)
            print("[ctxgen] Δt:", self.delta_t)
        return

    def generate_signal(
        self,
        states: List[Tuple[int, int]],
        pad: int = 8,
        seed: int = 42,
        as_raw: bool = True,
    ) -> Union[Tuple[np.ndarray, np.ndarray], mne.io.Raw]:
        """Generate the signal by supplying context states.

        Args:
            states (List[Tuple[int, int]]): Context states as a list of
                tuple(firing rate, duration in secs).
            pad (int, optional): Padding in secs. Defaults to 8.
            seed (int, optional): Random seed. Defaults to 42.
            as_raw (bool, optional): Output as mne.io.Raw. Defaults to True.

        Returns:
            mne.io.Raw: if as_raw is True.
            Tuple[np.ndarray, np.ndarray]: as tuple of (signal, firing_rates)
                if as_raw is False.
        """
        # Convert context states to firing rates "fr"
        # we use a mask and keep track of indices to assembly later
        pad = int(pad / self.delta_t)
        fr, mask, state_idx = [], [], []
        N, i, j = 0, 0, 0
        for _fr, t in states:
            # Create a mask to indicate if padding is used
            _mask = np.repeat(True, repeats=int(t / self.delta_t))
            if pad > 0:
                pad_mask = np.repeat(False, repeats=pad)
                _mask = np.hstack([pad_mask, _mask, pad_mask])
            mask.append(_mask)
            n = _mask.shape[0]

            # Specify the firing rate for each time step
            fr.append(np.repeat(_fr, repeats=n))

            # Save indices of this state
            j = i + n
            state_idx.append((i, j))
            i = j

            # Increment total size
            N += n

            if self.verbose:
                print(f"[ctxgen] state:\t{_fr} Hz\tt={t}")

            continue

        fr = np.hstack(fr)
        mask = np.hstack(mask)
        assert fr.shape == (N,)
        assert mask.shape == (N,)

        # Calculate membrane potentials
        V = calc_membrane_potential(
            fr=fr,
            M=self.M,
            delta_t=self.delta_t,
            tau=self.tau,
            v_thresh=self.v_thresh,
            seed=seed
        )

        # Construct signal
        W = np.abs(stats.norm.rvs(
            loc=0,
            scale=1,
            size=self.M,
            random_state=seed
        ))
        x = np.dot(W, V)

        # Correct DC shift by removing the mean in each state
        # this is preferred over filtering low frequencies for reliability
        for i, j in state_idx:
            x[i : j] = x[i : j] - np.mean(x[i : j])
            continue

        # Remove padding
        x = x[mask]
        fr = fr[mask]
        N = np.sum(mask)
        assert x.shape == (N,)
        assert fr.shape == (N,)

        # Downsample to output frequency
        resample_step = int(1 / (self.sfreq * self.delta_t))
        N = math.ceil(N / resample_step)
        x = x[:: resample_step]
        fr = fr[:: resample_step]
        assert x.shape == (N,)
        assert fr.shape == (N,)

        if self.verbose:
            print(
                "[ctxgen] generated signal:"
                f" T={N / self.sfreq:.2f}s, N={N}, {self.sfreq} Hz"
            )

        if not as_raw:
            return x, fr

        # Convert to mne.io.Raw
        raw = mne.io.RawArray(
            data=np.vstack([x, fr]),
            info=mne.create_info(
                ch_names=["x", "fr"],
                ch_types=["misc", "misc"],
                sfreq=self.sfreq
            ),
            verbose=self.verbose
        )
        events = mne.find_events(
            raw=raw,
            stim_channel="fr",
            initial_event=True,
            consecutive=True,
            verbose=self.verbose
        )[1:]
        if len(events) > 0:
            raw.set_annotations(mne.annotations_from_events(
                events=events,
                sfreq=self.sfreq,
                event_desc={e[2] : "y" for e in events}
            ))

        return raw


def generate_with_harmonics(
    states: List[Tuple[List[Tuple[float, float]], float]] = None,
    sfreq: int|float = 256,
    as_raw: bool = True,
    verbose: bool = True,
) -> Union[Tuple[np.ndarray, np.ndarray], mne.io.Raw]:
    """Generate the signal using harmonics states, where each state
        is calculated by `A \cos(k \pi t)`
        Note: this is a legacy method.

    Args:
        states (List[Tuple[List[Tuple[float, float]], float]]): Harmonics
            as a list of Tuple(components, t). t is the duration in seconds.
            components is a list of tuple (A, k), amplitude and frequency
            factors respectively.
        sfreq (int|float, optional): Sampling frequency. Defaults to 256 Hz.
        as_raw (bool, optional): Output as mne.io.Raw. Defaults to True.
        verbose (bool, optional): Display output. Defaults to True.

    Returns:
        mne.io.Raw: if as_raw is True.
        Tuple[np.ndarray, np.ndarray]: as tuple of (signal, state_id)
            if as_raw is False.
    """
    print("[ctxgen] warning, using harmonics generator")

    # Default states from (Azami et al., 2014)
    # DOI: 10.1007/978-3-319-10849-0_18
    if states is None:
        t = 50 / 7
        states = [
            ([(0.5, 1), (1.5, 4), (4, 5)], t),
            ([(0.7, 1), (2.1, 4), (5.6, 5)], t),
            ([(1.5, 2), (4, 8)], t),
            ([(1.5, 1), (4, 4)], t),
            ([(0.5, 1), (1.7, 2), (3.7, 5)], t),
            ([(2.3, 3), (7.8, 8)], t),
            ([(0.8, 1), (1, 3), (3, 5)], t),
        ]
    x, state_id, i = [], [], 0
    for _i, (component, _t) in enumerate(states):
        _t = (np.arange(int(_t * sfreq)) + i) / sfreq
        _n = len(_t)

        _x = np.zeros((_n))
        for _A, _k in component:
            _x += _A * np.cos(_k * np.pi * _t)

        x.append(_x)
        state_id.append(np.repeat(_i + 1, _n))
        i += _n
        continue

    x = np.hstack(x)
    N = x.shape[0]
    state_id = np.hstack(state_id)
    assert state_id.shape[0] == N

    if verbose:
        print(
            "[harmonics] generated signal:"
            f" T={N / sfreq:.2f}s, N={N}, {sfreq} Hz"
        )

    if not as_raw:
        return x, state_id

    # Convert to mne.io.Raw
    raw = mne.io.RawArray(
        data=np.vstack([x, state_id]),
        info=mne.create_info(
            ch_names=["x", "state_id"],
            ch_types=["misc", "misc"],
            sfreq=sfreq
        ),
        verbose=verbose
    )

    # Create events based on A and k
    events = mne.find_events(
        raw=raw,
        stim_channel=["state_id"],
        initial_event=True,
        consecutive=True,
        verbose=verbose
    )[1:]
    if len(events) > 0:
        raw.set_annotations(mne.annotations_from_events(
            events=events,
            sfreq=sfreq,
            event_desc={e[2] : "y" for e in events}
        ))

    return raw


class AutoReg:
    """Autoregressive (AR) model following the general form:
        x_t = w @ x_{t-1} + c_t, where x is the signal, w is the parameter weights of shape (order,) and c_t is gaussian white noise.
    """
    def __init__(
        self,
        order: int = 2,
        sfreq: int|float = 256,
        verbose: bool = True
    ):
        self.order = order
        self.sfreq = sfreq
        self.verbose = verbose
        self.params = np.random.randn(order)
        return

    def fit(self, x: ndarray):
        """Estimate the parameters of the model based on input EEG segment.

        Args:
            x (ndarray): Input EEG segment.
        """
        n = x.shape[0]
        assert n >= self.order, "[autoreg] len(x) must be greater than order"

        X = np.column_stack([
            x[i : n - self.order + i]
            for i in range(self.order)
        ])
        y = x[self.order:]
        self.params, *_ = np.linalg.lstsq(X, y, rcond=None)

        if self.verbose:
            print(f"[autoreg] fitted parameters: {self.params}")
        return

    def generate(self, t: float, x: ndarray = None) -> ndarray:
        """Generate a signal of a given duration based on the parameters of the
        model

        Args:
            t (float): Time in seconds.
            x (ndarray, optional): Preceeding signal to generate from.
                Defaults to None.
        """
        n = int(t * self.sfreq) + self.order
        new_x = np.random.randn(n)
        if x is not None:
            new_x[: self.order] = x[-self.order :]

        for i in range(self.order, n):
            new_x[i] += self.params @ new_x[i - self.order : i]

        new_x = new_x[self.order :]
        if x is not None:
            new_x = np.hstack([x, new_x])
        return new_x


def generate_with_ar(
    states: List[Tuple[str, float]] = [
        ("Z", 0.8), ("S", 0.8), ("Z", 1.2), ("S", 0.4), ("Z", 0.8)
    ],
    data_path: Path = Path("./data/bonn"),
    sfreq: float|int = 256,
    order: int = 2,
    seed: int = None,
    as_raw: bool = True,
    verbose: bool = True
) -> Union[Tuple[np.ndarray, np.ndarray], mne.io.Raw]:
    """Generate a signal with two autoregressive models based on the method
    in Appel & Brandt, 1984 (DOI: 10.1016/0165-1684(84)90050-1). The AR
    models are fit on EEG from the Bonn University dataset.

    Args:
        states (List[Tuple[str, float]], optional): Signal states as a list of
            tuple (set_name, duration in seconds).
        data_path (Path, optional): Defaults to Path("./data/bonn").
        sfreq (float | int, optional): Sample frequency. Defaults to 256.
        order (int, optional): Order of the AR-model. Defaults to 2.
        seed (int, optional): Random seed to select record. Defaults to None.
        as_raw (bool, optional): Returns signal as Raw. Defaults to True.
        verbose (bool, optional): Defaults to True.

    Returns:
        mne.io.Raw: if as_raw is True.
        Tuple[np.ndarray, np.ndarray]: as tuple of (signal, state_id)
            if as_raw is False.
    """
    if seed is not None:
        np.random.seed(seed)

    # Check and download the Bonn University dataset
    data_path = Path(data_path)
    if not data_path.exists():
        print(f"[ar_model] downloading bonn data to {data_path}")
        import requests
        import zipfile
        import io

        DATA_URL = [
            "https://www.ukbonn.de/site/assets/files/21874/z.zip",
            "https://www.ukbonn.de/site/assets/files/21872/o.zip",
            "https://www.ukbonn.de/site/assets/files/21871/n.zip",
            "https://www.ukbonn.de/site/assets/files/21870/f.zip",
            "https://www.ukbonn.de/site/assets/files/21875/s.zip",
        ]

        for url in DATA_URL:
            response = requests.get(url)
            with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                z.extractall(path=data_path)

    # Fit AR-models
    ar_models: Dict[str, AutoReg] = {}
    for set_name, *_ in states:
        if set_name in ar_models:
            continue
        ar_model = AutoReg(order=order, sfreq=sfreq, verbose=verbose)
        set_path = data_path.joinpath(set_name)
        records = list(sorted(set_path.glob("*.txt")))
        selected_record = np.random.choice(records)
        print(f"[ar_model] set: {set_name}, record: {selected_record}")
        x = np.loadtxt(selected_record)
        ar_model.fit(x)
        ar_models[set_name] = ar_model

    # Generate
    x = None
    state_id = []
    for i, (set_name, duration) in enumerate(states):
        x = ar_models[set_name].generate(t=duration, x=x)
        state_id.append(np.repeat(i + 1, int(duration * sfreq)))

    N = x.shape[0]
    state_id = np.hstack(state_id)
    assert state_id.shape[0] == N

    if verbose:
        print(
            "[ar_model] generated signal:"
            f" T={N / sfreq:.2f}s, N={N}, {sfreq} Hz"
        )

    if not as_raw:
        return x, state_id

    # Convert to mne.io.Raw
    raw = mne.io.RawArray(
        data=np.vstack([x, state_id]),
        info=mne.create_info(
            ch_names=["x", "state_id"],
            ch_types=["misc", "misc"],
            sfreq=sfreq
        ),
        verbose=verbose
    )

    # Create events based on A and k
    events = mne.find_events(
        raw=raw,
        stim_channel=["state_id"],
        initial_event=True,
        consecutive=True,
        verbose=verbose
    )[1:]
    if len(events) > 0:
        raw.set_annotations(mne.annotations_from_events(
            events=events,
            sfreq=sfreq,
            event_desc={e[2] : "y" for e in events}
        ))

    return raw