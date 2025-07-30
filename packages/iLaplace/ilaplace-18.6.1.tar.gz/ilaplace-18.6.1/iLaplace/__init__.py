"""
inverse_laplace - Numerical Inverse Laplace Transform using Talbot's Method.

This module provides efficient computation of the inverse Laplace transform using Talbot’s method,
suitable for engineering, physics, and mathematical applications.

Dependencies:
    - numpy
    - sympy
    - mpmath
"""

import numpy as np
import sympy as sp
import mpmath
from functools import lru_cache
from multiprocessing import Pool, cpu_count

# Symbol definitions
t, s = sp.symbols('t s')

# Cached symbolic-to-numeric conversion
@lru_cache(maxsize=None)
def get_lambdified_func(F):
    return sp.lambdify(s, F, 'mpmath')

@lru_cache(maxsize=None)
def function(F):
    return sp.lambdify(s, F, 'mpmath')

# Core single-point inverse Laplace using Talbot
def inverse_laplace(F, t_val):
    if t_val <= 0:
        return 0.0
    F_func = get_lambdified_func(F)
    return float(mpmath.invertlaplace(F_func, t_val, method='talbot'))

# Internal helper for multiprocessing
def _compute_at_t(args):
    F, t_val = args
    return inverse_laplace(F, t_val)

# Parallel version for multiple time points
def inverse_laplace_vectorized(F, t_list, processes=None):
    """
    Computes the inverse Laplace transform at multiple time points in parallel.

    Parameters:
        F (sympy.Expr): The Laplace-domain expression.
        t_list (Iterable[float]): List of time values.
        processes (int or None): Number of processes (defaults to CPU count).

    Returns:
        List[float]: Inverse Laplace transform evaluated at each time point.
    """
    with Pool(processes=processes or cpu_count()) as pool:
        results = pool.map(_compute_at_t, [(F, t_val) for t_val in t_list])
    return results

# Public API
__all__ = ['inverse_laplace', 'inverse_laplace_vectorized', 'function']
