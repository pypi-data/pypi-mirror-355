__all__ = ["sampling_period", "sampling_frequency"]

import astropy.units as u
import numpy as np


def sampling_period(t):
    r"""Calculate the sampling period of a time array."""

    if not np.issubdtype(t.dtype, np.datetime64):
        raise NotImplementedError("Input must be datetime64 dtype.")

    t = t.astype("datetime64[ns]")
    return (
        np.diff(t).mean().astype("timedelta64[ns]").astype("f8") * u.ns
    ).to(u.s)


def sampling_frequency(t):
    r"""Calculate the sampling frequency of a time array."""
    return (1 / sampling_period(t)).to(u.Hz)
