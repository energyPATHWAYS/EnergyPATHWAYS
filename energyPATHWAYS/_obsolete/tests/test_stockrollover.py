__author__ = 'Ben, Ryan'
# -*- coding: utf-8 -*-

import numpy as np
import time
import math
from scipy import stats
from matplotlib import pylab as plt
import stockrollover


def time_stamp(t):
    """Prints the difference between the parameter and current time.
    This is useful for timing program execution if timestamps are periodicly saved.
    Parameters:
        a: float
        
    Returns:
        current time: float
    """
    print "%(time).4f seconds to execute \n" % {"time": time.time() - t}
    return time.time()


# Survival shape parameters for weibull decay functions. Methodology adapted from
# https://www.aceee.org/files/proceedings/2010/data/papers/1977.pdf

np.set_printoptions(precision=2)

vintage_start, vintage_stop, vintage_step = 1990, 2050, 1
vintages = np.arange(vintage_start, vintage_stop + 1, vintage_step, dtype=np.int)

year_start, year_stop, year_step = 1990, 2050, 1
years = np.arange(year_start, year_stop + 1, year_step, dtype=np.int)

starting_stock = 5000
# annual_new = np.array(100*(1+np.arange(len(vintages))*.5), dtype=np.int)
annual_new = np.array(1000 * (1 + np.arange(len(vintages)) * .5), dtype=np.float)
# annual_new = np.zeros(len(vintages))
annual_new[0] += starting_stock

weibull_shape = 2.34
weibull_meanlife = 20

t = time.time()
for n in range(10):
    stock = stockrollover.stockrollover(years, vintages, annual_new, weibull_shape, weibull_meanlife)
t = time_stamp(t)

# test = cdf[-1::-1]*stock[-1,-1]
# vs
# stock[-1]

# Add in existing stock
#







