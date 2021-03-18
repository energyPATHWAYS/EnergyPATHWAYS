# -*- coding: utf-8 -*-
"""
Created on Thu Aug 06 14:28:23 2015

@author: Ryan Jones
"""

import numpy as np
import copy
from random import randint


def completeA(A, x, b):
    """ Use completed x, and b to solve for missing elements in A
    A*x = b
    Each row in A can be missing no more than 1 element.
    Missing elements should be indicated with np.NaN    
    """
    repaired = copy.copy(A)
    for i in range(len(A)):
        isnan = np.isnan(A[i])
        nan_loc = np.nonzero(isnan)[0]

        if len(nan_loc) == 0:
            continue
        elif len(nan_loc) > 1:
            raise ValueError('Only one NaN value is permitted per row of A matrix')

        good_loc = np.nonzero(~isnan)[0]
        incomplete_sum = sum(A[i, good_loc] * x[good_loc])

        repaired[i, nan_loc] = (b[i] - incomplete_sum) / x[nan_loc]

    return repaired

# set up data example
size = 5

A = np.random.rand(size, size)
x = np.random.rand(size)
b = np.dot(A, x)

A_incomplete = copy.copy(A)
for row in range(size):
    A_incomplete[row, randint(0, size - 1)] = np.nan

# call method

repaired = completeA(A_incomplete, x, b)

# varify

print(np.sum(A))
print(np.sum(A) - np.sum(repaired))




