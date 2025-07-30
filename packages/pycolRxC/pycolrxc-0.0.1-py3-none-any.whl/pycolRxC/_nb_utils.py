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


# https://github.com/numba/numba/issues/7818#issue-1127113927

import ctypes as ct
import numba as nb

def capsule_name(capsule):
    ct.pythonapi.PyCapsule_GetName.restype = ct.c_char_p
    ct.pythonapi.PyCapsule_GetName.argtypes = [ct.py_object]
    return ct.pythonapi.PyCapsule_GetName(capsule)

def get_f2py_function_address(capsule):
    name = capsule_name(capsule)
    ct.pythonapi.PyCapsule_GetPointer.restype = ct.c_void_p
    ct.pythonapi.PyCapsule_GetPointer.argtypes = [ct.py_object, ct.c_char_p]
    return ct.pythonapi.PyCapsule_GetPointer(capsule, name)

from numba import types
from numba.extending import intrinsic
from numba.core import cgutils

#########Intrinsics to efficiently to pass scalars by ref#############
#Workaround using stack-allocated arrays, faster than heap-allocated arrays.
#This could be relevant on functions with short runtimes.
@intrinsic
def val_to_ptr(typingctx, data):
    def impl(context, builder, signature, args):
        ptr = cgutils.alloca_once_value(builder,args[0])
        return ptr
    sig = types.CPointer(nb.typeof(data).instance_type)(nb.typeof(data).instance_type)
    return sig, impl

@intrinsic
def ptr_to_val(typingctx, data):
    def impl(context, builder, signature, args):
        val = builder.load(args[0])
        return val
    sig = data.dtype(types.CPointer(data.dtype))
    return sig, impl
	