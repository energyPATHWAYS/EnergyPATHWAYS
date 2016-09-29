# -*- coding: utf-8 -*-
"""
Created on Sat Dec 12 10:33:41 2015

@author: ryan
"""

import numpy as np
import scipy.sparse
import scipy.sparse.linalg
import e3
import time

#https://pypi.python.org/pypi/InverseProblem/1.0
#http://pysparse.sourceforge.net/itsolvers.html
#http://austingwalters.com/gauss-seidel-method/
#http://georgioudakis.com/blog/categories/python/cg.html

def solve_IO(IO_matrix, d=None):
    """ Given, the IO_matrix and intermediate demand, solve for final demand
        -> Inputs and Outputs are numpy arrays
        if no demand (d) is passed, the inverse is returned
    """
    identity_matrix = np.eye(len(IO_matrix), len(IO_matrix))
    energy_supply = np.linalg.solve(identity_matrix - IO_matrix, identity_matrix if d is None else d)
    return energy_supply

def inv_IO(IO_matrix):
    identity_matrix = np.eye(len(IO_matrix))
    return np.linalg.inv(identity_matrix - IO_matrix)

def inv_ID_sparse(IO_matrix):
    size = len(IO_matrix)
    identity_matrix = np.eye(size)
    a_sps = scipy.sparse.csc_matrix(identity_matrix - IO_matrix)
    lu_obj = scipy.sparse.linalg.splu(a_sps)
    return lu_obj.solve(identity_matrix)



#def inv_ID_sparse(IO_matrix):
#    identity_matrix = np.eye(len(IO_matrix))
#    return scipy.sparse.linalg.inv(scipy.sparse.csc_matrix(identity_matrix - IO_matrix))

#size = 5000
size = 5000
density = .1

b = np.random.rand(size)

a = scipy.sparse.rand(size,size,density)
IO_matrix = a.toarray()
identity_matrix = np.eye(len(IO_matrix))

A = identity_matrix - IO_matrix

t = time.time()
inv = inv_IO(IO_matrix)
t = e3.utils.time_stamp(t)

#inv2 = inv_ID_sparse(IO_matrix)
t = e3.utils.time_stamp(t)
for i in range(10):
    inv3 = np.linalg.solve(A, identity_matrix)

t = e3.utils.time_stamp(t)
sol2 = np.linalg.solve(A, b)
t = e3.utils.time_stamp(t)

#print 'Use BIConjugate Gradient iteration to solve A x = b'
#temp = scipy.sparse.linalg.bicg(A, b, x0=b)
#print sum((temp[0] - sol2)**2)
#t = e3.utils.time_stamp(t)
#
#print 'Use BIConjugate Gradient STABilized iteration to solve A x = b'
#temp = scipy.sparse.linalg.bicgstab(A, b, x0=b)
#print sum((temp[0] - sol2)**2)
#t = e3.utils.time_stamp(t)
#
#print 'Use Conjugate Gradient iteration to solve A x = b'
#temp = scipy.sparse.linalg.cg(A, b, x0=b)
#print sum((temp[0] - sol2)**2)
#t = e3.utils.time_stamp(t)
#
#print 'Use Conjugate Gradient Squared iteration to solve A x = b'
#temp = scipy.sparse.linalg.cgs(A, b, x0=b)
#print sum((b - sol2)**2)
#print sum((temp[0] - sol2)**2)
#t = e3.utils.time_stamp(t)
#
#print 'Use Generalized Minimal RESidual iteration to solve A x = b.'
#temp = scipy.sparse.linalg.gmres(A, b, x0=b)
#print sum((temp[0] - sol2)**2)
#t = e3.utils.time_stamp(t)
#
#print 'Solve a matrix equation using the LGMRES algorithm.'
#temp = scipy.sparse.linalg.lgmres(A, b, x0=b)
#print sum((b - sol2)**2)
#print sum((temp[0] - sol2)**2)
#t = e3.utils.time_stamp(t)
#
#print 'Use MINimum RESidual iteration to solve Ax=b'
#temp = scipy.sparse.linalg.minres(A, b, x0=b)
#print sum((temp[0] - sol2)**2)
#t = e3.utils.time_stamp(t)
#
#print 'Use Quasi-Minimal Residual iteration to solve A x = b'
#temp = scipy.sparse.linalg.qmr(A, b, x0=b)
#print sum((temp[0] - sol2)**2)
#t = e3.utils.time_stamp(t)






