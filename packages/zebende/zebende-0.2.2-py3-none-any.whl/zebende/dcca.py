import ctypes

import numpy as np
from typing import Literal

from . import mat_index_comb

from .get_platform import get_platform

from .array_to_c_pointer_convert import arr_2d_to_c

from numpy.typing import NDArray
from numpy.ctypeslib import ndpointer

uint_c_type = np.uintp

ENUM_DCCA_of = Literal['all']

def dcca(input_data: NDArray[np.float64], 
           tws:  NDArray[np.int64] | NDArray[np.float64], 
           DCCA_of: np.ndarray | ENUM_DCCA_of ="all",
           axis: int = 0
        ) ->    tuple[
                NDArray[np.float64],    # DFA
                NDArray[np.float64],    # DCCA
                ]:

    """A function that calculates the 
       DCCA (Detrended Cross-correlation Analysis)
        for a group of time series

        Args:
            input_data (NDArray[np.float64]): 2D array of times series integrated data.
            tws (NDArray[np.float64] | NDArray[np.float64]): 1D array of time scales.
            DCCA_of (np.ndarray | list | None, optional): _description_. Defaults to None.
            axis (int): axis of the input_data matrix that contains the values for each time series. Defalts to 0.

        Returns:
            <span>A tuple of 2 matrices:</span>
            DFA(NDArray[np.float64]):_description_. 
            DCCA(NDArray[np.float64]):_description_.
    """
    
    assert (tws[:-1] < tws[1:]).all() == True , ("""time window scales (tws) values must be in crescent order.""")


    # setting lib path

    

    zz = ctypes.cdll.LoadLibrary(get_platform())

    # outputs types
    c_2d_any_1d_uint = ndpointer(dtype = uint_c_type, ndim=1, flags='C')
    c_1d_double = ndpointer(dtype=np.double, ndim=1, flags='C')
    # getting the module file
    _dcca = zz.dcca
    # setting outputs
    _dcca.argtypes = [ 
                    c_1d_double, ctypes.c_size_t, ctypes.c_size_t, # input data
                    c_2d_any_1d_uint, ctypes.c_size_t, # tws
                    c_1d_double, # Time steps
                    c_2d_any_1d_uint, ctypes.c_size_t, # DCCA of
                    # outputs
                    c_2d_any_1d_uint, # DFA_arr
                    c_2d_any_1d_uint, # DCCA_arr
                    ]

    # Preparing input data    

    if not tws.flags.c_contiguous:
        tws = np.ascontiguousarray(tws)
    
    # preparing DCCA_ot array

    if type(DCCA_of) == str:
        if DCCA_of == "all":
            DCCA_of =  np.ascontiguousarray(mat_index_comb(input_data, axis=axis))
    # ensuring data compatibility
    DCCA_of = DCCA_of.astype(uint_c_type)
    c_DCCA_of = arr_2d_to_c(DCCA_of)

    
    # preparing tws array
    tws = tws.astype(uint_c_type)

    # preparing output array
    F_DFA_arr = np.ascontiguousarray(np.zeros(shape=(tws.shape[0], input_data.shape[axis]), dtype=input_data.dtype))
    c_DFA_arr = arr_2d_to_c(F_DFA_arr)
    DCCA_arr = np.ascontiguousarray(np.zeros(shape=(tws.shape[0], DCCA_of.shape[0]), dtype=input_data.dtype))
    c_DCCA_arr = arr_2d_to_c(DCCA_arr)

    # preparing data
    data_shape = input_data.shape

    if axis == 0:
        x_cnt = data_shape[0]
        x_len = data_shape[1]

        input_data = np.ascontiguousarray(input_data.flatten())

    elif axis == 1:
        x_len = data_shape[0]
        x_cnt = data_shape[1]

        input_data = np.ascontiguousarray(np.asfortranarray(input_data).flatten(order="K"))

    # time steps
    time_steps = np.ascontiguousarray(np.arange(x_len, dtype=input_data.dtype))

   
    # calling functon  
    _dcca(input_data,  x_len, x_cnt, 
            tws, tws.size, 
            time_steps, 
            c_DCCA_of , DCCA_of.shape[0],
            # Outputs
            c_DFA_arr,
            c_DCCA_arr,
            )


    return [F_DFA_arr, DCCA_arr]
