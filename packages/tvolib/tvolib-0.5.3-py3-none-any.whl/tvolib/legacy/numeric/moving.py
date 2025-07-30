__all__ = ["move_avg", "move_rms", "move_std"]

from functools import reduce

import numpy as np
from astropy.convolution import (
    Box1DKernel,
    CustomKernel,
    Gaussian1DKernel,
    Gaussian2DKernel,
    convolve,
)


def move_avg(x, w, window="box"):
    r"""
    Calculate the moving average of a signal

    Parameters
    ----------
    x: array_like, shape (N, ...)
        Input signal. Currently only works up to 2 dimensions
    w: tuple
        Shape of averaging window
    window: "box", "gauss"
        Type of window to apply average on

    Return
    ------
    xout: array_like
        Processed signal
    """

    if not isinstance(w, (tuple, list)):
        raise NotImplementedError("w must be a tuple or list.")
    if (ndim := x.ndim) != len(w := np.array(w)):
        raise NotImplementedError(
            "Length of w-tuple must be the same as x dimensions."
        )

    if ndim == 1:
        if window == "gauss":
            kernel = Gaussian1DKernel(*(w / 6))
        else:
            kernel = Box1DKernel(*w)
    elif ndim == 2:
        if window == "gauss":
            kernel = Gaussian2DKernel(*(w / 6), theta=np.pi / 2)
        else:
            kernel = CustomKernel(
                reduce(np.outer, (Box1DKernel(_w) for _w in w)).reshape(w)
            )
    else:
        raise NotImplementedError("Dimensionality is constrained to 2.")

    return convolve(x, kernel, fill_value=np.nan, boundary="fill")


def move_rms(x, w, window="box"):
    r"""
    Calculate the moving root-mean-square of a signal

    Parameters
    ----------
    x: array_like, shape (N, ...)
        Input signal. Currently only works up to 2 dimensions
    w: tuple
        Shape of averaging window
    window: "box", "gauss"
        Type of window to apply average on

    Return
    ------
    xout: array_like
        Processed signal
    """
    return np.sqrt(move_avg(x**2, w, window=window))


def move_std(x, w, window="box"):
    r"""
    Calculate the moving standard deviation of a signal

    Parameters
    ----------
    x: array_like, shape (N, ...)
        Input signal. Currently only works up to 2 dimensions
    w: tuple
        Shape of averaging window
    window: "box", "gauss"
        Type of window to apply average on

    Return
    ------
    xout: array_like
        Processed signal
    """
    return np.sqrt(
        move_avg(x**2, w, window=window) - move_avg(x, w, window=window) ** 2
    )
