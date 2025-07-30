__all__ = ["curlometer"]

import numpy as np


def curlometer(Q1, Q2, Q3, Q4, R1, R2, R3, R4):
    r"""
    Calculate the divergence and curl of a vector field from 4-point
    measurements using the curlometer technique. For reference see
    Chapter 14 of Paschmann & Daly (2000), "Analysis Methods for
    Multi-Spacecraft Data", ISSI Scientific Report, SR-001.

    Parameters
    ----------
    Q1, Q2, Q3, Q4: array_like, shape (..., 3)
        Values of vector field at 4 spatial positions. The last axis is
        vector components
    R1, R2, R3, R4: array_like, shape (..., 3)
        Position of the 4 measurements. The last axis is vector
        components

    Return
    ------
    curlometer: dict
        Contains div_Q, curl_Q
    """

    dR_12 = R2 - R1
    dR_13 = R3 - R1
    dR_14 = R4 - R1

    k2 = (tmp := np.cross(dR_13, dR_14, axis=-1)) / np.einsum(
        "...i,...i", dR_12, tmp
    )[:, np.newaxis]
    k3 = (tmp := np.cross(dR_12, dR_14, axis=-1)) / np.einsum(
        "...i,...i", dR_13, tmp
    )[:, np.newaxis]
    k4 = (tmp := np.cross(dR_12, dR_13, axis=-1)) / np.einsum(
        "...i,...i", dR_14, tmp
    )[:, np.newaxis]
    k1 = -k2 - k3 - k4

    div_Q = np.sum(k1 * Q1 + k2 * Q2 + k3 * Q3 + k4 * Q4, axis=-1)
    curl_Q = (
        np.cross(k1, Q1, axis=-1)
        + np.cross(k2, Q2, axis=-1)
        + np.cross(k3, Q3, axis=-1)
        + np.cross(k4, Q4, axis=-1)
    )

    return dict(div_Q=div_Q, curl_Q=curl_Q)
