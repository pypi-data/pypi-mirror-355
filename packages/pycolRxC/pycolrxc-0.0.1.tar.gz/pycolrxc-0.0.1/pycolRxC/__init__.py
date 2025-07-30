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


import numpy as np
import numba as nb

from pycolRxC._stat import qnorm, pnorm2d

def compute_net_voters(x0, y0, scenario):
    x = x0
    y = y0
    return {'x': x, 'y': y}

@nb.njit(parallel = False, error_model = "numpy", cache = True)
def constraints_zeros_local(
    pjk_crude_local,
    pjk_crude_l_local,
    pjk_crude_u_local,
    scenario, 
    J0, 
    K0, 
    x, 
    y
):
    J = pjk_crude_local.shape[2]
    K = pjk_crude_local.shape[1]

    zeros_row = np.nonzero(x == 0)[0]
    zeros_col = np.nonzero(y == 0)[0]

    for i in zeros_row:
        j_arr = np.nonzero(x[i,:] == 0)[0]
        for j in j_arr.flat:
            pjk_crude_local[i,j,:] = 0
            pjk_crude_l_local[i,j,:] = 0
            pjk_crude_u_local[i,j,:] = 0

    for i in zeros_col:
        k_arr = np.nonzero(y[i,:] == 0)[0]
        for k in k_arr.flat:
            pjk_crude_local[i,:,k] = 0
            pjk_crude_l_local[i,:,k] = 0
            pjk_crude_u_local[i,:,k] = 0

    return pjk_crude_local, pjk_crude_l_local, pjk_crude_u_local

#@nb.njit(parallel = False, error_model = "numpy", cache = True)
#def Thomsen_local_logit_2x2(
#    votes1,
#    total1,
#    votes2,
#    total2,
#    confidence = 0.95,
#    Yule_aprox = False 
#):
#    I = votes2.size
#    weight = total2 / np.sum(total2)
#    t1 = np.sum(votes1) / np.sum(total1)
#    t2 = np.sum(votes2) / np.sum(total2)
#    # To avoid taking logs from zero values
#    votes1[votes1 == 0] += 0.5
#    votes2[votes2 == 0] += 0.5
#    #total1[total1 == votes1] += 0.5
#    #total2[total2 == votes2] += 0.5
#
#    # To avoid taking logs from zero values
#    lv1 = np.log(votes1 / (total1 - votes1))
#    lv2 = np.log(votes2 / (total2 - votes2))
#    meanlv1 = np.sum(weight * lv1)
#    meanlv2 = np.sum(weight * lv2)
#    varlv1 = np.sum(I * weight * (lv1 - meanlv1) ** 2) / (I - 1)
#    varlv2 = np.sum(I * weight * (lv2 - meanlv2) ** 2) / (I - 1)
#    # To avoid taking logs from zero values
#    r = np.sum(weight * (lv1 - meanlv1) * (lv2 - meanlv2)) / np.sqrt(varlv1 * varlv2)
#
#    # Whole space votes
#    # Integration binormal
#    core = pnorm2d(qnorm(t1), qnorm(t2))
#    p2p = core / t1
#    t2p = (t2 - core) / (1 - t1)
#    trans_matrix = np.array([
#        [p2p, t2p],
#        [1 - p2p, 1 - t2p]
#    ])
#    trans_matrix_low = np.full((2, 2), np.nan)
#    trans_matrix_high = np.full((2, 2), np.nan)
#    
#    trans_matrix_local = np.full((2, 2, I), np.nan)
#    trans_matrix_low_local = np.full((2, 2, I), np.nan)
#    trans_matrix_high_local = np.full((2, 2, I), np.nan)
#    pjk = np.full((2, 2, I), np.nan)
#    pjk_low = np.full((2, 2, I), np.nan)
#    pjk_high = np.full((2, 2, I), np.nan)
#
#    for i in range(I):
#        t1 = votes1[i] / total1[i]
#        t2 = votes2[i] / total2[i]
#        core = pnorm2d(qnorm(t1), qnorm(t2))
#        p2p = core / t1 # Estimate of proportion transfer from party 1 to party 2
#        t2p = (t2 - core) / (1 - t1) # Estimate of proportion transfer from total(rest) 1 to party 2
#        trans_matrix_local[0, 0, i] = p2p
#        trans_matrix_local[0, 1, i] = t2p
#        trans_matrix_local[1, 0, i] = 1 - p2p
#        trans_matrix_local[1, 1, i] = 1 - t2p
#
#    if confidence != None:
#        z = qnorm(1 - (1 - confidence) / 2)
#        r_hi = np.tanh(np.log((1 + r) / (1 - r)) / 2 + z / np.sqrt(I - 3))
#        r_low = np.tanh(np.log((1 + r) / (1 - r)) / 2 - z / np.sqrt(I - 3))
#        p2p_hi = pnorm2d(qnorm(t1), qnorm(t2), rho = r_hi) / t1
#        p2p_low = pnorm2d(qnorm(t1), qnorm(t2), rho = r_low) / t1
#        t2p_hi = (t2 - p2p_low * t1) / (1 - t1)
#        t2p_low = (t2 - p2p_hi * t1) / (1 - t1)
#        trans_matrix_low = np.array([
#            [p2p_low, t2p_low],
#            [1 - p2p_hi, 1 - t2p_hi]
#        ])
#        trans_matrix_high = np.array([
#            [p2p_hi, t2p_hi],
#            [1 - p2p_low, 1 - t2p_low]
#        ])
#        for i in range(I):
#            t1 = votes1[i] / total1[i]
#            t2 = votes2[i] / total2[i]
#            p2p_hi = pnorm2d(qnorm(t1), qnorm(t2), rho = r_hi) / t1
#            p2p_low = pnorm2d(qnorm(t1), qnorm(t2), rho = r_low) / t1
#            t2p_hi = (t2 - p2p_low * t1) / (1 - t1)
#            t2p_low = (t2 - p2p_hi * t1) / (1 - t1)
#            
#            trans_matrix_low_local[0, 0, i] = p2p_low
#            trans_matrix_low_local[0, 1, i] = t2p_low
#            trans_matrix_low_local[1, 0, i] = 1 - p2p_hi
#            trans_matrix_low_local[1, 1, i] = 1 - t2p_hi
#
#            trans_matrix_high_local[0, 0, i] = p2p_hi
#            trans_matrix_high_local[0, 1, i] = t2p_hi
#            trans_matrix_high_local[1, 0, i] = 1 - p2p_low
#            trans_matrix_high_local[1, 1, i] = 1 - t2p_low
#
#    #total_rows = np.full((2, 2, I), np.nan)
#    #kron = np.kron([1, 1], [votes1 / total1, 1 - votes1 / total1])
#    #print(kron)
#    #for i in range(I):
#    #    total_rows[0, 0, i] = kron[0]
#    #    total_rows[0, 1, i] = kron[0]
#    #    total_rows[1, 0, i] = kron[1]
#    #    total_rows[1, 1, i] = kron[1]
#    total_rows = np.reshape(np.kron([1.0, 1.0], [votes1 / total1, 1 - votes1 / total1]), (2, 2, I))
#    pjk = trans_matrix_local * total_rows
#    pjk_low = trans_matrix_low_local * total_rows
#    pjk_high = trans_matrix_high_local * total_rows
#
#    return {
#        'PTM': trans_matrix,
#        'PTM_low': trans_matrix_low,
#        'PTM_high': trans_matrix_high,
#        'PTM_local': trans_matrix_local,
#        'PTM_low_local': trans_matrix_low_local,
#        'PTM_high_local': trans_matrix_high_local,
#        'pjk': pjk,
#        'pjk_low': pjk_low,
#        'pjk_high': pjk_high,
#        'cor': r
#    }

@nb.njit(parallel = False, error_model = "numpy", cache = True)
def Thomsen_local_probit_2x2(votes1, total1, votes2, total2, confidence = 0.95, Yule_aprox = False):
    I = votes2.size
    weight = total2 / np.sum(total2)
    t1 = np.sum(votes1) / np.sum(total1)
    t2 = np.sum(votes2) / np.sum(total2)
    # To avoid taking probits from zero values
    votes1[votes1 == 0] = 0.5
    votes2[votes2 == 0] = 0.5
    total1[total1 == votes1] += 0.5
    total2[total2 == votes2] += 0.5

    # To avoid taking logs from zero values
    pv1 = qnorm(votes1 / total1)
    pv2 = qnorm(votes2 / total2)
    meanpv1 = np.sum(weight * pv1)
    meanpv2 = np.sum(weight * pv2)
    varpv1 = np.sum(I * weight * (pv1 - meanpv1) ** 2) / (I - 1)
    varpv2 = np.sum(I * weight * (pv2 - meanpv2) ** 2) / (I - 1)
    # To avoid taking logs from zero values
    r = np.sum(weight * (pv1 - meanpv1) * (pv2 - meanpv2)) / np.sqrt(varpv1 * varpv2)

    # Whole space votes
    # Integration binormal
    core = pnorm2d(qnorm(t1), qnorm(t2), rho = r)
    p2p = core / t1
    t2p = (t2 - core) / (1 - t1)
    trans_matrix = np.array([
        [p2p, 1 - p2p],
        [t2p, 1 - t2p]
    ])
    trans_matrix_low = np.full((2, 2), np.nan)
    trans_matrix_high = np.full((2, 2), np.nan)
    
    trans_matrix_local = np.full((I, 2, 2), np.nan)
    trans_matrix_low_local = np.full((I, 2, 2), np.nan)
    trans_matrix_high_local = np.full((I, 2, 2), np.nan)
    pjk = np.full((I, 2, 2), np.nan)
    pjk_low = np.full((I, 2, 2), np.nan)
    pjk_high = np.full((I, 2, 2), np.nan)

    for i in range(I):
        t1 = votes1[i] / total1[i]
        t2 = votes2[i] / total2[i]
        core = pnorm2d(qnorm(t1), qnorm(t2), rho = r)
        p2p = core / t1 # Estimate of proportion transfer from party 1 to party 2
        t2p = (t2 - core) / (1 - t1) # Estimate of proportion transfer from total(rest) 1 to party 2
        trans_matrix_local[i, 0, 0] = p2p
        trans_matrix_local[i, 0, 1] = 1 - p2p
        trans_matrix_local[i, 1, 0] = t2p
        trans_matrix_local[i, 1, 1] = 1 - t2p

    if confidence != None:
        z = qnorm(1 - (1 - confidence) / 2)
        r_hi = np.tanh(np.log((1 + r) / (1 - r)) / 2 + z / np.sqrt(I - 3))
        r_low = np.tanh(np.log((1 + r) / (1 - r)) / 2 - z / np.sqrt(I - 3))
        p2p_hi = core = pnorm2d(qnorm(t1), qnorm(t2), rho = r_hi) / t1
        p2p_low = core = pnorm2d(qnorm(t1), qnorm(t2), rho = r_low) / t1
        t2p_hi = (t2 - p2p_low * t1) / (1 - t1)
        t2p_low = (t2 - p2p_hi * t1) / (1 - t1)
        trans_matrix_low = np.array([
            [p2p_low, t2p_low],
            [1 - p2p_hi, 1 - t2p_hi]
        ])
        trans_matrix_high = np.array([
            [p2p_hi, t2p_hi],
            [1 - p2p_low, 1 - t2p_low]
        ])
        for i in range(I):
            t1 = votes1[i] / total1[i]
            t2 = votes2[i] / total2[i]
            p2p_hi = core = pnorm2d(qnorm(t1), qnorm(t2), rho = r_hi) / t1
            p2p_low = core = pnorm2d(qnorm(t1), qnorm(t2), rho = r_low) / t1
            t2p_hi = (t2 - p2p_low * t1) / (1 - t1)
            t2p_low = (t2 - p2p_hi * t1) / (1 - t1)
            
            trans_matrix_low_local[i, 0, 0] = p2p_low
            trans_matrix_low_local[i, 1, 0] = t2p_low
            trans_matrix_low_local[i, 0, 1] = 1 - p2p_hi
            trans_matrix_low_local[i, 1, 1] = 1 - t2p_hi

            trans_matrix_high_local[i, 0, 0] = p2p_hi
            trans_matrix_high_local[i, 1, 0] = t2p_hi
            trans_matrix_high_local[i, 0, 1] = 1 - p2p_low
            trans_matrix_high_local[i, 1, 1] = 1 - t2p_low

    total_rows = np.full((I, 2, 2), np.nan)
    for i in range(I):
        kron = np.kron(np.array([1.0, 1.0], dtype = np.float64), np.array([votes1[i] / total1[i], 1 - votes1[i] / total1[i]], dtype = np.float64))
        total_rows[i, 0, 0] = kron[0]
        total_rows[i, 0, 1] = kron[0]
        total_rows[i, 1, 0] = kron[1]
        total_rows[i, 1, 1] = kron[1]
    pjk = trans_matrix_local * total_rows
    pjk_low = trans_matrix_low_local * total_rows
    pjk_high = trans_matrix_high_local * total_rows

    return trans_matrix, trans_matrix_low, trans_matrix_high, trans_matrix_local, trans_matrix_low_local, trans_matrix_high_local, pjk, pjk_low, pjk_high, r

@nb.njit(parallel = False, error_model = "numpy", cache = True)
def IPF(matriz, vector_columna, vector_fila, precision = 0.000001):
    nc = len(vector_columna)
    nf = len(vector_fila)
    vector_fila1 = matriz.sum(axis = 1)
    R1 = np.diag(vector_fila) @ np.diag(1 / vector_fila1)
    # numba doesn't support >1d arrays as indices
    #R1[np.isnan(R1)] = 0
    R1_shape = R1.shape
    R1_flat = R1.flatten()
    R1_flat[np.isnan(R1_flat)] = 0
    R1 = R1_flat.reshape(R1_shape)
    #R1[np.isinf(R1)] = 1
    R1_shape = R1.shape
    R1_flat = R1.flatten()
    R1_flat[np.isinf(R1_flat)] = 1
    R1 = R1_flat.reshape(R1_shape)
    X1 = R1 @ matriz
    vecor_columna1 = X1.sum(axis = 0)
    S1 = np.diag(vector_columna) @ np.diag(1 / vecor_columna1)
    #S1[np.isnan(S1)] = 0
    S1_shape = S1.shape
    S1_flat = S1.flatten()
    S1_flat[np.isnan(S1_flat)] = 0
    S1 = S1_flat.reshape(S1_shape)
    #S1[np.isinf(S1)] = 1
    S1_shape = S1.shape
    S1_flat = S1.flatten()
    S1_flat[np.isinf(S1_flat)] = 1
    S1 = S1_flat.reshape(S1_shape)
    X2 = X1 @ S1
    dif = np.max(np.abs(X2 - matriz))

    while dif > precision:
        matriz = X2
        vector_fila1 = matriz.sum(axis = 1)
        R1 = np.diag(vector_fila) @ np.diag(1 / vector_fila1)
        #R1[np.isnan(R1)] = 0
        R1_shape = R1.shape
        R1_flat = R1.flatten()
        R1_flat[np.isnan(R1_flat)] = 0
        R1 = R1_flat.reshape(R1_shape)
        #R1[np.isinf(R1)] = 1
        R1_shape = R1.shape
        R1_flat = R1.flatten()
        R1_flat[np.isinf(R1_flat)] = 1
        R1 = R1_flat.reshape(R1_shape)
        X1 = R1 @ matriz
        vecor_columna1 = X1.sum(axis = 0)
        S1 = np.diag(vector_columna) @ np.diag(1 / vecor_columna1)
        #S1[np.isnan(S1)] = 0
        S1_shape = S1.shape
        S1_flat = S1.flatten()
        S1_flat[np.isnan(S1_flat)] = 0
        S1 = S1_flat.reshape(S1_shape)
        #S1[np.isinf(S1)] = 1
        S1_shape = S1.shape
        S1_flat = S1.flatten()
        S1_flat[np.isinf(S1_flat)] = 1
        S1 = S1_flat.reshape(S1_shape)
        X2 = X1 @ S1
        dif = np.max(np.abs(X2 - matriz))

    X2 = X2 * (vector_fila / X2.sum(axis = 1))[:, np.newaxis]
    #X2[np.isnan(X2)] = 0
    X2_shape = X2.shape
    X2_flat = X2.flatten()
    X2_flat[np.isnan(X2_flat)] = 0
    X2 = X2_flat.reshape(X2_shape)
    #X2[np.isinf(X2)] = 1
    X2_shape = X2.shape
    X2_flat = X2.flatten()
    X2_flat[np.isinf(X2_flat)] = 1
    X2 = X2_flat.reshape(X2_shape)
    X2 = (X2.transpose() * (vector_columna / X2.sum(axis = 0))[:, np.newaxis]).transpose()
    #X2[np.isnan(X2)] = 0
    X2_shape = X2.shape
    X2_flat = X2.flatten()
    X2_flat[np.isnan(X2_flat)] = 0
    X2 = X2_flat.reshape(X2_shape)
    #X2[np.isinf(X2)] = 1
    X2_shape = X2.shape
    X2_flat = X2.flatten()
    X2_flat[np.isinf(X2_flat)] = 1
    X2 = X2_flat.reshape(X2_shape)

    return X2

@nb.njit(parallel = False, error_model = "numpy", cache = True)
def IPF2(matriz, vector_columna, vector_fila, precision = 0.01):
    nc = len(vector_columna)
    nf = len(vector_fila)
    vector_fila1 = matriz.sum(axis = 1)
    R1 = np.diag(vector_fila) @ np.diag(1 / vector_fila1)
    #R1[np.isnan(R1)] = 0
    R1_shape = R1.shape
    R1_flat = R1.flatten()
    R1_flat[np.isnan(R1_flat)] = 0
    R1 = R1_flat.reshape(R1_shape)
    #R1[np.isinf(R1)] = 1
    R1_shape = R1.shape
    R1_flat = R1.flatten()
    R1_flat[np.isinf(R1_flat)] = 1
    R1 = R1_flat.reshape(R1_shape)
    X1 = R1 @ matriz
    vecor_columna1 = X1.sum(axis = 0)
    S1 = np.diag(vector_columna) @ np.diag(1 / vecor_columna1)
    #S1[np.isnan(S1)] = 0
    S1_shape = S1.shape
    S1_flat = S1.flatten()
    S1_flat[np.isnan(S1_flat)] = 0
    S1 = S1_flat.reshape(S1_shape)
    #S1[np.isinf(S1)] = 1
    S1_shape = S1.shape
    S1_flat = S1.flatten()
    S1_flat[np.isinf(S1_flat)] = 1
    S1 = S1_flat.reshape(S1_shape)
    X2 = X1 @ S1
    dif_r = np.sum(np.abs(vector_fila - X2.sum(axis = 1)))
    dif_c = np.sum(np.abs(vector_columna - X2.sum(axis = 0)))
    dif = np.max(np.array([dif_r, dif_c]))
    iter_n = 0
    while dif > precision and iter_n < 1000:
        matriz = X2
        vector_fila1 = matriz.sum(axis = 1)
        R1 = np.diag(vector_fila) @ np.diag(1 / vector_fila1)
        #R1[np.isnan(R1)] = 0
        R1_shape = R1.shape
        R1_flat = R1.flatten()
        R1_flat[np.isnan(R1_flat)] = 0
        R1 = R1_flat.reshape(R1_shape)
        #R1[np.isinf(R1)] = 1
        R1_shape = R1.shape
        R1_flat = R1.flatten()
        R1_flat[np.isinf(R1_flat)] = 1
        R1 = R1_flat.reshape(R1_shape)
        X1 = R1 @ matriz
        vecor_columna1 = X1.sum(axis = 0)
        S1 = np.diag(vector_columna) @ np.diag(1 / vecor_columna1)
        #S1[np.isnan(S1)] = 0
        S1_shape = S1.shape
        S1_flat = S1.flatten()
        S1_flat[np.isnan(S1_flat)] = 0
        S1 = S1_flat.reshape(S1_shape)
        #S1[np.isinf(S1)] = 1
        S1_shape = S1.shape
        S1_flat = S1.flatten()
        S1_flat[np.isinf(S1_flat)] = 1
        S1 = S1_flat.reshape(S1_shape)
        X2 = X1 @ S1
        dif_r = np.sum(np.abs(vector_fila - X2.sum(axis = 1)))
        dif_c = np.sum(np.abs(vector_columna - X2.sum(axis = 0)))
        dif = np.max(np.array([dif_r, dif_c]))
        iter_n += 1

    return X2

@nb.njit(parallel = False, error_model = "numpy", cache = True)
def reweighting_pjk(pjk_array, ref1, ref2, scale, x, y, tol = 10**-6):
    I = pjk_array.shape[0]
    J = pjk_array.shape[1]
    K = pjk_array.shape[2]
    parties1 = [i for i in range(J) if i != ref1]
    parties2 = [i for i in range(K) if i != ref2]

    p_obs_rows = x / x.sum(axis = 1)[:,np.newaxis]
    p_obs_cols = y / y.sum(axis = 1)[:,np.newaxis]
    weight = x.sum(axis = 1) / np.sum(x)

    suma0 = 0
    suma1 = np.sum(pjk_array)
    dif = abs(suma0 - suma1)
    cont = 0

    #print("reweighting")
    while (dif > tol and cont < 10000):
        #print(dif, cont)
        if (scale == "logit"):
            for j in parties1:
                for k in parties2:
                    #print(j, k)
                    # numba doesn't support more than one array as indices
                    # pjk_temp = pjk_array[:,np.array([j, ref1]),np.array([k, ref2])]
                    pjk_temp = pjk_array[:,np.array([j, ref1]),:][:,:,np.array([k, ref2])]
                    suma_rows = pjk_temp.sum(axis = 2)
                    suma_cols = pjk_temp.sum(axis = 1)
                    ps1 = suma_rows[:,0] / suma_rows[:,1]
                    ps2 = suma_cols[:,0] / suma_cols[:,1]
                    weight = x.sum(axis = 1) * np.sum(suma_rows) #rowSums
                    weight = weight / np.sum(weight)
                    valid = np.logical_and(np.abs(ps1) != 0, np.isfinite(ps1))
                    #print(valid)
                    valid = np.logical_and(valid, np.logical_and(np.abs(ps2) != 0, np.isfinite(ps2)))
                    #valid = np.logical_and(
                    #    valid,
                    #    np.logical_and(
                    #        suma_rows[0,:] >= 1,
                    #        suma_rows[0,:] == 1
                    #    )
                    #)
                    #valid = np.logical_and(
                    #    valid,
                    #    np.logical_and(
                    #        suma_cols[0,:] >= 1,
                    #        suma_cols[0,:] == 1
                    #    )
                    #)
                    logit_rows = np.log(ps1[valid])
                    logit_cols = np.log(ps2[valid])
                    mean1 = np.sum(weight[valid] * logit_rows) / np.sum(weight[valid])
                    mean2 = np.sum(weight[valid] * logit_cols) / np.sum(weight[valid])
                    var1 = np.sum(weight[valid] * (logit_rows - mean1) ** 2) / np.sum(weight[valid])
                    var2 = np.sum(weight[valid] * (logit_cols - mean2) ** 2) / np.sum(weight[valid])
                    # Pearson correlation of logit transformation
                    cor_e = np.sum(weight[valid] * (logit_rows - mean1) * (logit_cols - mean2)) / np.sqrt(var1 * var2)
                    no_0 = np.logical_and(valid, pjk_array[:, j, k] != 0)
                    for i, val in enumerate(no_0):
                        if val == True:
                            #print(suma_rows[i, 0], qnorm(suma_rows[i, 0]))
                            #print(suma_cols[i, 0], qnorm(suma_cols[i, 0]))
                            pjk_array[i, j, k] = pnorm2d(qnorm(suma_rows[i, 0]), qnorm(suma_cols[i, 0]), rho = cor_e)
        else:
            for j in parties1:
                for k in parties2:
                    pjk_temp = pjk_array[:,np.array([j, ref1]),:][:,:,np.array([k, ref2])]
                    suma_rows = pjk_temp.sum(axis = 2).transpose()
                    suma_cols = pjk_temp.sum(axis = 1).transpose()
                    ps1 = suma_rows[0,:] / suma_rows.sum(axis = 0)
                    ps2 = suma_cols[0,:] / suma_cols.sum(axis = 0)
                    weight = x.sum(axis = 1) * suma_rows.sum(axis = 0) #rowSums
                    weight = weight / np.sum(weight)
                    valid = np.logical_and(np.abs(ps1) != 0, np.isfinite(ps1))
                    valid = np.logical_and(valid, np.logical_and(np.abs(ps2) != 0, np.isfinite(ps2)))
                    valid = np.logical_and(valid, np.logical_and(ps1 != 1, ps2 != 1))
                    valid = np.logical_and(valid, np.logical_and(suma_rows[0,:] >= 1, suma_rows[0,:] == 0))
                    valid = np.logical_and(valid, np.logical_and(suma_cols[0,:] >= 1, suma_cols[0,:] == 0))
                    probit_rows = qnorm(ps1[valid])
                    probit_cols = qnorm(ps2[valid])
                    mean1 = np.sum(weight[valid] * probit_rows) / np.sum(weight[valid])
                    mean2 = np.sum(weight[valid] * probit_cols) / np.sum(weight[valid])
                    var1 = np.sum(weight[valid] * (probit_rows - mean1) ** 2) / np.sum(weight[valid])
                    var2 = np.sum(weight[valid] * (probit_cols - mean2) ** 2) / np.sum(weight[valid])
                    # Pearson correlation of logit transformation
                    if var1 == 0 or var2 == 0:
                        cor_e = 0.0
                    else:
                        cor_e = np.sum(weight[valid] * (probit_rows - mean1) * (probit_cols - mean2)) / np.sqrt(var1 * var2)
                    no_0 = np.logical_and(valid, pjk_array[:, j, k] != 0)
                    for i, val in enumerate(no_0):
                        if val == True:
                            pjk_array[i, j, k] = pnorm2d(qnorm(suma_rows[i, 0]), qnorm(suma_cols[i, 0]), rho = cor_e)
                    #print(j, k, no_0)
        #pjk_array[pjk_array < 0] = 0
        pjk_array_shape = pjk_array.shape
        pjk_array_flat = pjk_array.flatten()
        pjk_array_flat[pjk_array_flat < 0] = 0
        pjk_array = pjk_array_flat.reshape(pjk_array_shape)
        p_est_rows = pjk_array.sum(axis = 2)
        p_est_cols = pjk_array.sum(axis = 1)

        for kk in parties2:
            no_0 = p_est_cols[:,kk] != 0
            pjk_array[no_0, ref1, kk] = pjk_array[no_0, ref1, kk] * p_obs_cols[no_0, kk] / p_est_cols[no_0, kk]

        for jj in parties1:
            no_0 = p_est_rows[:,jj] != 0
            pjk_array[no_0, jj, ref2] = pjk_array[no_0, jj, ref2] * p_obs_rows[no_0, jj] / p_est_rows[no_0, jj]

        cont += 1
        suma0 = suma1
        suma1 = np.sum(pjk_array)
        dif = np.abs(suma0 - suma1)

    for ii in range(I):
        pjk_array[ii,:,:] = IPF(pjk_array[ii,:,:] * np.sum(y[ii,:]), y[ii], x[ii], tol)
        dif_r = np.sum(np.abs(x[ii,:] - pjk_array[ii,:,:].sum(axis = 1)))
        dif_c = np.sum(np.abs(y[ii,:] - pjk_array[ii,:,:].sum(axis = 0)))
        if np.max(np.array([dif_r, dif_c])) > 0.01:
            pjk_array[ii,:,:] = IPF2(pjk_array[ii,:,:] * np.sum(y[ii,:]), y[ii], x[ii])

    return pjk_array
        

        
@nb.njit(parallel = False, error_model = "numpy", cache = True)
def Thomsen_iter_algorithm(pjk_crude_local, Yule_aprox, reference, scale, x,  y, J0, K0, tol):
    #if Yule_aprox:
    #    reweighting = reweighting_pjk_Yule
    #else:
    #    reweighting = reweighting_pjk
    reweighting = reweighting_pjk
    
    vjk_units_multi = np.full((J0 * K0,) + pjk_crude_local.shape, np.nan)
    iter_count = np.nan
    
    for j in range(J0):
        for k in range(K0):
            #print(j, k)
            vjk_temp =  reweighting(pjk_crude_local.copy(), ref1 = j , ref2 = k, scale = scale, x = x, y = y, tol = tol)
            #print(vjk_temp)
            vjk_units_multi[j * K0 + k,:,:,:] = vjk_temp
    # https://github.com/numba/numba/issues/1269
    # numba doesn't support reduction functions over axis
    # vjk_units = np.mean(vjk_units_multi, axis = 0)
    #print(vjk_units_multi)
    #vjk_units = nb_mean_along_axis(vjk_units_multi, axis = 0)
    vjk_units = vjk_units_multi.sum(axis = 0) / vjk_units_multi.shape[0]
    #print(vjk_units)

    return vjk_units, vjk_units_multi

def _ecolRxC_Thomsen(x0, y0, x, y, scale, scenario, reference, confidence, B , Yule_aprox, tol):
    vector_columna = np.sum(y, axis = 0)
    vector_fila = np.sum(x, axis = 0)
    
    I = x.shape[0]
    J = x.shape[1]
    K = y.shape[1]
    J0 = x0.shape[1]
    K0 = y0.shape[1]

    

    correlations = np.full((J, K), np.nan)
    VTM_crude = np.full((J, K), np.nan)
    VTM_crude_l = np.full((J, K), np.nan)
    VTM_crude_u = np.full((J, K), np.nan)
    
    VTM_crude_local = np.full((I, J, K), np.nan)
    pjk_crude_local = np.full((I, J, K), np.nan)
    pjk_crude_l_local = np.full((I, J, K), np.nan)
    pjk_crude_u_local = np.full((I, J, K), np.nan)
    
    for j in range(J):
        for k in range(K):
            mt = Thomsen_local_probit_2x2(x[:,j].copy(), np.sum(x, axis = 1, dtype = np.float64), y[:,k].copy(), np.sum(y, axis = 1, dtype = np.float64), confidence, Yule_aprox)
            VTM_crude[j, k] = mt[0][0, 0]
            VTM_crude_l[j, k] = mt[1][0, 0]
            VTM_crude_u[j, k] = mt[2][0, 0]
            correlations[j, k] = mt[9]
            for i in range(I):
                VTM_crude_local[i, j, k] = mt[3][i, 0, 0]
                pjk_crude_local[i, j, k] = mt[6][i, 0, 0]
                pjk_crude_l_local[i, j, k] = mt[7][i, 0, 0]
                pjk_crude_u_local[i, j, k] = mt[8][i, 0, 0]
    #TODO: constraints_scenario

    mt = constraints_zeros_local(pjk_crude_local.copy(), pjk_crude_l_local.copy(), pjk_crude_u_local.copy(), scenario, J0, K0, x.copy(), y.copy())

    pjk_crude_local = mt[0]
    pjk_crude_l_local = mt[1]
    pjk_crude_u_local = mt[2]
    
    T_adj = Thomsen_iter_algorithm(pjk_crude_local = pjk_crude_local.copy(), Yule_aprox = Yule_aprox, reference = reference, scale = scale, x = x.copy(), y = y.copy(), J0 = J0, K0 = K0, tol = tol)
    vjk_units_multi = T_adj[0]
    vjk_units = T_adj[1]

    # if reference == None:
    weights = np.abs(correlations.flatten())
    weights /= np.sum(weights)
    W = np.full((J * K, I, J, K), np.nan)
    for jk in range(J * K):
        W[jk,:,:,:] = np.full((I, J, K), weights[jk])
    vjk_units = np.sum(vjk_units_multi * W, axis = 0)
    VTM_units = vjk_units.copy()
    for i in range(I):
        VTM_units[i,:,:] = vjk_units[i,:,:] / np.sum(vjk_units[i,:,:], axis = 1)[:, np.newaxis]
        VTM_units[i,x[i,:] == 0,:] = 0

    VTM_votes = np.sum(vjk_units, axis = 0)
    VTM_votes_global = np.sum(vjk_units, axis = 0)
    VTM = VTM_votes_global / np.sum(VTM_votes_global, axis = 1)[:, np.newaxis]
    VTM_global = VTM_votes_global / np.sum(VTM_votes_global, axis = 1)[:, np.newaxis]

    # if reference == None:
    VTM_lower = np.nan
    VTM_upper = np.nan
    pjk_crude_l_local = np.nan
    pjk_crude_u_local = np.nan

    return VTM, VTM_votes, VTM_global, VTM_votes_global, VTM_lower, VTM_upper, VTM_crude, VTM_units, vjk_units, pjk_crude_l_local, pjk_crude_l_local, pjk_crude_u_local, VTM_crude_local, correlations

    #census.changes = c("adjust", "raw", "regular", "ordinary", "enriched", "simultaneous", "semifull", "full", "gold"),
def ecolRxC_Thomsen(votes_election1, votes_election2, scale = "progit", census_changes = "adjust", reference = None, confidence = 0.95, B = 500, Yule_aprox = False, tol = 0.000001):
    x0 = votes_election1.to_numpy(dtype = np.float64)
    y0 = votes_election2.to_numpy(dtype = np.float64)
    
    scenario = census_changes
    
    net = compute_net_voters(x0.copy(), y0.copy(), scenario)
    
    x = net['x']
    y = net['y']
    
    names1 = votes_election1.columns
    names2 = votes_election2.columns
    names_units = votes_election1.index
    
    res = _ecolRxC_Thomsen(x0, y0, x, y, scale, scenario, reference, confidence, B , Yule_aprox, tol)
    
    return {
        'VTM': res[0],
        'VTM_votes': res[1],
        'VTM_global': res[2],
        'VTM_votes_global': res[3],
        'VTM_lower': res[4],
        'VTM_upper': res[5],
        'VTM_crude_global': res[6],
        'VTM_units': res[7],
        'VTM_votes_units': res[8],
        'VTM_lower_units': res[9],
        'VTM_upper_units': res[10],
        'VTM_crude_units': res[11],
        'correlations': res[12]}