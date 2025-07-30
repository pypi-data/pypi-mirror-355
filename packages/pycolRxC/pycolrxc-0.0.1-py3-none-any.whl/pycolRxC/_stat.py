# Copyright 2025 Guilherme Calé <guicale@posteo.net>
#
# This file is part of pycolRxC.
#
# pycolRxC is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software Foundation,
# either version 2 of the License, or (at your option) any later version.
#
# pycolRxC is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with pycolRxC.
# If not, see <https://www.gnu.org/licenses/>. 


import numba as nb
import ctypes as ct
import scipy as sp
import numpy as np

from pycolRxC._nb_utils import get_f2py_function_address, val_to_ptr, ptr_to_val

functype = ct.CFUNCTYPE(ct.c_double, ct.c_double)
addr = nb.extending.get_cython_function_address("scipy.special.cython_special", "__pyx_fuse_1ndtr")
ndtr_cython = functype(addr)

@nb.cfunc('float64(float64)')
def ndtr(a):
    return ndtr_cython(a)

@nb.vectorize
def pnorm(x):
    return ndtr(nb.types.float64(x))

functype = ct.CFUNCTYPE(ct.c_double, ct.c_double)
addr = nb.extending.get_cython_function_address("scipy.special.cython_special", "ndtri")
ndtri_cython = functype(addr)

@nb.cfunc('float64(float64)')
def ndtri(a):
    return ndtri_cython(a)

@nb.vectorize
def qnorm(x):
    return ndtri(nb.types.float64(x))
    
dble_p=ct.POINTER(ct.c_double)
int_p =ct.POINTER(ct.c_longlong)
functype = ct.CFUNCTYPE(ct.c_void_p,
                            int_p, int_p, dble_p, dble_p, dble_p, dble_p, int_p, dble_p, dble_p, dble_p, int_p)
func_ptr = get_f2py_function_address(sp.stats._mvn.mvnun._cpointer)
mvnun_f2py = functype(func_ptr)


from numba import cfunc, types, carray

c_sig = types.double(
    types.int64,
    types.int64,
    types.CPointer(types.double),
    types.CPointer(types.double),
    types.CPointer(types.double),
    types.CPointer(types.double),
    types.int64,
    types.double,
    types.double
)

@nb.cfunc(c_sig)
def mvnun_wrapped(d, n, lower, upper, means, covar, maxpts, abseps, releps):    
    d_ptr = val_to_ptr(nb.int64(d))
    n_ptr = val_to_ptr(nb.int64(n))
    maxpts_ptr = val_to_ptr(nb.int64(maxpts))

    abseps_ptr = val_to_ptr(nb.float64(abseps))
    releps_ptr = val_to_ptr(nb.float64(releps))
    
    val_ptr = val_to_ptr(nb.float64(0))
    inform_ptr = val_to_ptr(nb.int64(0))
    
    mvnun_f2py(
        d_ptr,
        n_ptr,
        lower,
        upper,
        means,
        covar,
        maxpts_ptr,
        abseps_ptr,
        releps_ptr,
        val_ptr,
        inform_ptr
    )
    
    return ptr_to_val(val_ptr)

@nb.njit('float64(float64[:],float64[:],float64[:, :],float64[:, :],int64,float64,float64)')
def mvnun(lower, upper, means, covar, maxpts, abseps, releps):
    d = means.shape[1]
    n = means.shape[0]

    return mvnun_wrapped(
        d,
        n,
        lower.ctypes,
        upper.ctypes,
        means.ctypes,
        covar.ctypes,
        maxpts,
        abseps,
        releps
    )

# The function _cdf is based on code from the SciPy library
# scipy/stats/_multivariate.py
# Copyright (c) 2001-2002 Enthought, Inc. 2003, SciPy Developers.

@nb.njit
def _cdf(x, mean, cov, maxpts = None, abseps = 1e-6, releps = 1e-6, lower_limit = None):
    """Multivariate normal cumulative distribution function.

    Parameters
    ----------
    x : ndarray
        Points at which to evaluate the cumulative distribution function.
    mean : ndarray
        Mean of the distribution
    cov : array_like
        Covariance matrix of the distribution
    maxpts : integer
        The maximum number of points to use for integration
    abseps : float
        Absolute error tolerance
    releps : float
        Relative error tolerance
    lower_limit : array_like, optional
        Lower limit of integration of the cumulative distribution function.
        Default is negative infinity. Must be broadcastable with `x`.

    Notes
    -----
    As this function does no argument checking, it should not be
    called directly; use 'cdf' instead.


    .. versionadded:: 1.0.0

    """
    if maxpts == None:
        maxpts = x.shape[0] * 1000
        
    if lower_limit == None:
        lower = np.full(x.shape, -np.inf)
    else:
        lower = lower_limit
    # In 2d, _mvn.mvnun accepts input in which `lower` bound elements
    # are greater than `x`. Not so in other dimensions. Fix this by
    # ensuring that lower bounds are indeed lower when passed, then
    # set signs of resulting CDF manually.
    b, a = np.broadcast_arrays(x, lower)
    # numba doesn't support boolean array indexing with more >1d arrays as indices
    a_orig_shape = a.shape
    a = a.flatten()
    b_orig_shape = b.shape
    b = b.flatten()
    i_swap = b < a
    a, b = a.copy(), b.copy()
    a[i_swap], b[i_swap] = b[i_swap], a[i_swap]
    #a = a.reshape(a_orig_shape)
    #b = a.reshape(b_orig_shape)
    #i_swap = b < a
    signs = (-1)**(i_swap.sum(axis=-1))  # odd # of swaps -> negative
    n = x.shape[-1]
    limits = np.concatenate((a, b), axis=-1)
    
    # mvnun expects 1-d arguments, so process points sequentially
    #def func1d(limits):
    #    return mvnun(
    #        limits[:n],
    #        limits[n:],
    #        mean,
    #        cov,
    #        np.int64(maxpts),
    #        abseps,
    #        releps
    #    )

    out = mvnun(
        limits[:n],
        limits[n:],
        mean,
        cov,
        np.int64(maxpts),
        abseps,
        releps
    )

    #out = np.apply_along_axis(func1d, -1, limits) * signs
    #axis = len(limits.shape)
    #out = np.empty(shape = limits.shape[:-1], dtype = np.float64)
    #Ni, Nk = limits.shape[:axis], limits.shape[axis+1:]
    #for ii in np.ndindex(Ni):
    #    for kk in np.ndindex(Nk):
    #        out[ii + np.s_[...,] + kk] = func1d(limits[ii + np.s_[:,] + kk]) * signs
    # return _squeeze_output(out)
    #out = out.squeeze()
    #if out.ndim == 0:
    #    out = out[()]
    return out

@nb.njit
def pnorm2d(x, y, rho = 0):
    x_arr = np.array([x, y], dtype = np.float64)
    mean = np.array([[0,0]], dtype = np.float64)
    cov = np.array([[1, rho], [rho, 1]], dtype = np.float64)
    return _cdf(x_arr, mean, cov)