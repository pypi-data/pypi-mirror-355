#  -*- coding: utf-8 -*-
"""
Author: Rafael R. L. Benevides
"""

from spacekernel.time cimport Time
from spacekernel.frames cimport Frame
from spacekernel.datamodel cimport GeodeticState


cdef class State:

    cdef:
        readonly Frame frame
        readonly Time time


# ========== ========== ========== ========== ========== ========== StateVector
cdef class StateVector(State):

    cdef:
        double[:, :] _r, _v
        double[:, :, :] _cov