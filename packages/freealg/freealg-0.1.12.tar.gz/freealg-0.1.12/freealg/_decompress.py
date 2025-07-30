# SPDX-License-Identifier: BSD-3-Clause
# SPDX-FileType: SOURCE
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the license found in the LICENSE.txt file in the root directory
# of this source tree.


# =======
# Imports
# =======

import numpy
# from scipy.integrate import solve_ivp

__all__ = ['decompress', 'reverse_characteristics']


# ==========
# decompress
# ==========

def decompress(freeform, size, x=None, delta=1e-6, iterations=500,
               step_size=0.1, tolerance=1e-9):
    """
    Free decompression of spectral density.

    Parameters
    ----------

    freeform : FreeForm
        The initial freeform object of matrix to be decompressed

    size : int
        Size of the decompressed matrix.

    x : numpy.array, default=None
        Positions where density to be evaluated at. If `None`, an interval
        slightly larger than the support interval will be used.

    delta: float, default=1e-4
        Size of the perturbation into the upper half plane for Plemelj's
        formula.

    iterations: int, default=500
        Maximum number of Newton iterations.

    step_size: float, default=0.1
        Step size for Newton iterations.

    tolerance: float, default=1e-4
        Tolerance for the solution obtained by the Newton solver. Also
        used for the finite difference approximation to the derivative.

    Returns
    -------

    rho : numpy.array
        Spectral density

    See Also
    --------

    density
    stieltjes

    Notes
    -----

    Work in progress.

    References
    ----------

    .. [1] tbd

    Examples
    --------

    .. code-block:: python

        >>> from freealg import FreeForm
    """

    alpha = size / freeform.n
    m = freeform._eval_stieltjes
    # Lower and upper bound on new support
    hilb_lb = (1 / m(freeform.lam_m + delta * 1j)[1]).real
    hilb_ub = (1 / m(freeform.lam_p + delta * 1j)[1]).real
    lb = freeform.lam_m - (alpha - 1) * hilb_lb
    ub = freeform.lam_p - (alpha - 1) * hilb_ub

    # Create x if not given
    if x is None:
        radius = 0.5 * (ub - lb)
        center = 0.5 * (ub + lb)
        scale = 1.25
        x_min = numpy.floor(center - radius * scale)
        x_max = numpy.ceil(center + radius * scale)
        x = numpy.linspace(x_min, x_max, 500)

    def _char_z(z):
        return z + (1 / m(z)[1]) * (1 - alpha)

    # Ensure that input is an array
    x = numpy.asarray(x)

    target = x + delta * 1j

    z = numpy.full(target.shape, numpy.mean(freeform.support) - .1j,
                   dtype=numpy.complex128)

    # Broken Newton steps can produce a lot of warnings. Removing them
    # for now.
    with numpy.errstate(all='ignore'):
        for _ in range(iterations):
            objective = _char_z(z) - target
            mask = numpy.abs(objective) >= tolerance
            if not numpy.any(mask):
                break
            z_m = z[mask]

            # Perform finite difference approximation
            dfdz = _char_z(z_m+tolerance) - _char_z(z_m-tolerance)
            dfdz /= 2*tolerance
            dfdz[dfdz == 0] = 1.0

            # Perform Newton step
            z[mask] = z_m - step_size * objective[mask] / dfdz

    # Plemelj's formula
    char_s = m(z)[1] / alpha
    rho = numpy.maximum(0, char_s.imag / numpy.pi)
    rho[numpy.isnan(rho) | numpy.isinf(rho)] = 0
    rho = rho.reshape(*x.shape)

    return rho, x, (lb, ub)


# =======================
# reverse characteristics
# =======================

def reverse_characteristics(freeform, z_inits, T, iterations=500,
                            step_size=0.1, tolerance=1e-8):
    """
    """

    t_span = (0, T)
    t_eval = numpy.linspace(t_span[0], t_span[1], 50)

    m = freeform._eval_stieltjes

    def _char_z(z, t):
        return z + (1 / m(z)[1]) * (1 - numpy.exp(t))

    target_z, target_t = numpy.meshgrid(z_inits, t_eval)

    z = numpy.full(target_z.shape, numpy.mean(freeform.support) - .1j,
                   dtype=numpy.complex128)

    # Broken Newton steps can produce a lot of warnings. Removing them for now.
    with numpy.errstate(all='ignore'):
        for _ in range(iterations):
            objective = _char_z(z, target_t) - target_z
            mask = numpy.abs(objective) >= tolerance
            if not numpy.any(mask):
                break
            z_m = z[mask]
            t_m = target_t[mask]

            # Perform finite difference approximation
            dfdz = _char_z(z_m+tolerance, t_m) - _char_z(z_m-tolerance, t_m)
            dfdz /= 2*tolerance
            dfdz[dfdz == 0] = 1.0

            # Perform Newton step
            z[mask] = z_m - step_size * objective[mask] / dfdz

    return z
