__all__ = ["Lin10MagnetopauseModel"]

import numpy as np
from scipy.interpolate import UnivariateSpline


class Lin10MagnetopauseModel:
    r"""
    3D asymmetric magnetopause model. For references consult
    Lin+ (2010), "A three-dimensional asymmetric magnetopause model",
    JGR-Space Physics, doi:10.1029/2009JA014235
    """

    # Fit coefficients (see Table 9 in reference)
    a = np.zeros(22, dtype=np.float32)
    a[0] = 12.544
    a[1] = -0.194
    a[2] = 0.305
    a[3] = 0.0573
    a[4] = 2.178
    a[5] = 0.0571
    a[6] = -0.999
    a[7] = 16.473
    a[8] = 0.00152
    a[9] = 0.382
    a[10] = 0.0431
    a[11] = -0.00763
    a[12] = -0.210
    a[13] = 0.0405
    a[14] = -4.430
    a[15] = -0.636
    a[16] = -2.600
    a[17] = 0.832
    a[18] = -5.328
    a[19] = 1.103
    a[20] = -0.907
    a[21] = 1.450

    def __init__(self, pressure, bfield, tilt_angle):
        r"""

        Parameters
        ----------
        pressure: nPa
            Total (dynamic and magnetic) solar wind pressure
        bfield: nT
            z coordinate of the interplanetary magnetic field
        tilt_angle: rad
            Dipole tilt angle
        """

        # Save
        self._P = pressure
        self._Bz = bfield
        self._phi = tilt_angle

        # Calculate other coefficients
        self.construct_model()

    def construct_model(self):
        r"""
        Calculate the coefficients in eq. (20) and r(theta, varphi)
        in eq. (19)
        """
        # Unpack
        a = self.a
        P = self._P
        Bz = self._Bz
        phi = self._phi

        # Auxilliary coefficients
        r0 = (
            a[0]
            * (P ** a[1])
            * (1 + a[2] * (np.exp(a[3] * Bz) - 1) / (np.exp(a[4] * Bz) + 1))
        )
        b0 = a[6] + a[7] * (np.exp(a[8] * Bz) - 1) / (np.exp(a[9] * Bz) + 1)
        b1 = a[10]
        b2 = a[11] + a[12] * phi
        b3 = a[13]
        cn = cs = a[14] * (P ** a[15])
        dn = a[16] + a[17] * phi + a[18] * (phi**2)
        ds = a[16] - a[17] * phi + a[18] * (phi**2)
        en = es = a[21]
        tn = a[19] + a[20] * phi
        ts = a[19] - a[20] * phi

        # Auxilliary functions
        def psi_n(varphi, theta):
            return np.arccos(
                np.cos(theta) * np.cos(tn)
                + np.sin(theta) * np.sin(tn) * np.cos(varphi - np.pi / 2)
            )

        def psi_s(varphi, theta):
            return np.arccos(
                np.cos(theta) * np.cos(ts)
                + np.sin(theta) * np.sin(ts) * np.cos(varphi - 3 * np.pi / 2)
            )

        def f(varphi, theta):
            return (
                np.cos(theta / 2)
                + a[5] * np.sin(theta * 2) * (1 - np.exp(-theta))
            ) ** (
                b0
                + b1 * np.cos(varphi)
                + b2 * np.sin(varphi)
                + b3 * (np.sin(varphi) ** 2)
            )

        # Radial function
        def r(varphi, theta):
            return (
                r0 * f(varphi, theta)
                + cn * np.exp(dn * (psi_n(varphi, theta) ** en))
                + cs * np.exp(ds * (psi_s(varphi, theta) ** es))
            )

        self.radial_distance = r

    def shape_N(self, which="XY", N=1000, rotation_angle=0):
        theta = np.linspace(0, np.pi, N // 2)
        if which == "XY":
            # Get negative side of Y_gsm
            Rm = self.radial_distance(np.pi, theta[::-1])
            Xm = Rm * np.cos(theta[::-1])
            Ym = -Rm * np.sin(theta[::-1])
            # Get positive side of Y_gsm
            Rp = self.radial_distance(0, theta[1:])
            Xp = Rp * np.cos(theta[1:])
            Yp = Rp * np.sin(theta[1:])
            # Combine
            X = np.append(Xm, Xp)
            Y = np.append(Ym, Yp)
            # Rotate
            R = np.sqrt(X**2 + Y**2)
            T = np.arctan2(Y, X) + rotation_angle
            X = R * np.cos(T)
            Y = R * np.sin(T)
            return X, Y
        elif which == "XZ":
            # Get negative side of Z_gsm
            Rm = self.radial_distance(-np.pi / 2, theta[::-1])
            Xm = Rm * np.cos(theta[::-1])
            Zm = -Rm * np.sin(theta[::-1])
            # Get positive side of Z_gsm
            Rp = self.radial_distance(np.pi / 2, theta[1:])
            Xp = Rp * np.cos(theta[1:])
            Zp = Rp * np.sin(theta[1:])
            # Combine
            X = np.append(Xm, Xp)
            Z = np.append(Zm, Zp)
            # Rotate
            R = np.sqrt(X**2 + Z**2)
            T = np.arctan2(-Z, X) + rotation_angle
            X = R * np.cos(T)
            Z = R * np.sin(T)
            return X, Z
        else:
            raise NotImplementedError

    def shape_F(self, which="XY", N=1000000, rotation_angle=0):
        if which == "XY":
            X, Y = self.shape_N(which, N, rotation_angle=rotation_angle)
            R = np.sqrt(X**2 + Y**2)
            T = np.arctan2(Y, X)
        elif which == "XZ":
            X, Z = self.shape_N(which, N, rotation_angle=rotation_angle)
            R = np.sqrt(X**2 + Z**2)
            T = np.arctan2(-Z, X)
        else:
            raise NotImplementedError

        idx = np.argsort(T)
        return UnivariateSpline(T[idx], R[idx], s=0)

    def add_mpause_model(self, ax, which="XY", rotation_angle=0, **kw):
        ax.plot(
            *self.shape_N(which=which, rotation_angle=rotation_angle), **kw
        )

    @property
    def pressure(self):
        return self._P

    @property
    def bfield(self):
        return self._Bz

    @property
    def tilt_angle(self):
        return self._phi

    @pressure.setter
    def pressure(self, new_pressure):
        self._P = new_pressure

    @bfield.setter
    def bfield(self, new_bfield):
        self._Bz = new_bfield

    @tilt_angle.setter
    def tilt_angle(self, new_tilt_angle):
        self._phi = new_tilt_angle


if __name__ == "__main__":
    from tvolib import mpl_utils as mu

    model = Lin10MagnetopauseModel(pressure=1, bfield=0, tilt_angle=0)
    X_gsm, Y_gsm = model.shape_N(which="XY")
    T = np.linspace(-np.pi, np.pi, 1000)
    f = model.shape_F(which="XY", rotation_angle=np.radians(0))
    R = f(T)

    fig, ax = mu.plt.subplots(1, 1)

    mu.draw_earth(ax)
    ax.plot(X_gsm, Y_gsm, "-k")
    ax.plot(R * np.cos(T), R * np.sin(T), "--r")
    ax.set_xlim(-40, 20)
    ax.set_ylim(-35, 35)
    ax.set_aspect("equal")

    mu.plt.show()
