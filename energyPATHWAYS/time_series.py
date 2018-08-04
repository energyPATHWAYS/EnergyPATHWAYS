__author__ = 'Ben Haley & Ryan Jones'

import pandas as pd
import numpy as np
from scipy import optimize, interpolate, stats
import util
import logging
import pylab
import pdb

pd.options.mode.chained_assignment = None

class TimeSeries:
    @staticmethod
    def decay_towards_linear_regression_fill(x, y, newindex, decay_speed=0.2):
        """Use known x, y values and assuming a linear relationship to map a new index"""
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        linear_regression = newindex * slope + intercept

        # top part
        max_x, y_at_max_x = max(x), y[np.argmax(x)]
        regressed_y_at_max_x = linear_regression[np.argmax(x)]
        regressed_y_at_max_x = max_x * slope + intercept
        extrapolated_index = np.nonzero(newindex >= max_x)[0]
        decay = (y_at_max_x - regressed_y_at_max_x) * np.exp(-decay_speed*(newindex[extrapolated_index] - max_x))
        linear_regression[extrapolated_index] += decay

        # bottom part
        min_x, y_at_min_x = min(x), y[np.argmin(x)]
        regressed_y_at_min_x = min_x * slope + intercept
        extrapolated_index = np.nonzero(newindex <= min_x)[0]
        decay = (y_at_min_x - regressed_y_at_min_x) * np.exp(-decay_speed*extrapolated_index)
        linear_regression[extrapolated_index] += decay[-1::-1]

        return linear_regression

    @staticmethod
    def linear_regression_fill(x, y, newindex):
        """Use known x, y values and assuming a linear relationship to map a new index"""
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        return newindex * slope + intercept

    @staticmethod
    def generalized_logistic(x, A, K, M, B):
        """General logistic curve
        Args:
            x (ndarray): domain values
            A (float): lower bound
            K (float): upper bound
            B (float): controls speed of transition
            M (float): domain location of transition

        returns:
            y (ndarray)
        """
        return A + ((K - A) / (1 + np.exp(-B * (x - M))))
    
    @staticmethod
    def _approx_M(A, K, B, x, y):
        return (np.log(((K - A) / (y - A)) - 1) + B * x) / B

    @staticmethod
    def _logistic_end_point_error(B, A, K, x, y, slope, t=.005):
        M = TimeSeries._approx_M(A, K, B, x[1], y[1])
        y_est = TimeSeries.generalized_logistic(np.array([x[0], x[-1]]), A, K, M, B)
        y_tar = np.array([y[0], y[-1]]) + np.array([t, -t])*slope/abs(slope)
        return sum((y_tar - y_est)**2)

    @staticmethod
    def logistic_default_param(x, y):
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        A = min(y) if slope > 0 else max(y)
        K = max(y) if slope > 0 else min(y)
        if len(x) == 3:
            if sum(y) == 0:
                # if we have all zeros, the logistic should just return all zeros
                A, K, M, B = 0, 0, 0, 0
            else:
                assert y[0] != y[1] != y[2], "x = {}, y = {}".format(x, y)
                B0 = (10 / float(max(x) - min(x)))
                B = optimize.root(TimeSeries._logistic_end_point_error, x0=B0, args=(A, K, x, y, slope))['x'][0]
                M = TimeSeries._approx_M(A, K, B, x[1], y[1])
        else:
            B = 10 / float(max(x) - min(x))
            M = min(x) + (max(x) - min(x)) / 2.
        return A, K, M, B

    @staticmethod
    def default_logistic(x, y, newindex=None):
        A, K, M, B = TimeSeries.logistic_default_param(x, y)
        return TimeSeries.generalized_logistic(x if newindex is None else newindex, A, K, M, B)

    @staticmethod
    def fit_generalized_logistic(x, y, newindex, **kwargs):
        """Function to use leastsq_curve_fit to fit a general logistic curve to data x, y
        Tries to fit 50 times (default) before raising a runtime error
        """
        if len(x) < 4:
            return TimeSeries.default_logistic(x, y, newindex)
            # TODO: print to log file here
        
        A, K, M, B = TimeSeries.logistic_default_param(x, y)
        popt = TimeSeries.leastsq_curve_fit(x, y, f=TimeSeries.generalized_logistic, p0=(A, K, M, B))
        
        if popt is None:
            # Raise an error if no fit is found
            logging.debug("leastsq_curve_fit failed to find a solution - data does not support logistic fit")
            logging.debug("Model using default logistic curve")
            # TODO: print to log file here
            return TimeSeries.default_logistic(x, y, newindex)

        return TimeSeries.generalized_logistic(newindex, *popt)

    @staticmethod
    def leastsq_curve_fit(x, y, f, p0):
        """
        Args:
            x (1d array): domain values for fitting
            y (1d array): range values
            f (function): function that maps x to y; must have x as first param
            p0 (tuple): default parameter values for function f

        returns:
            popt (tuple): best fit parameters for function f
        """
        try:
            popt, pcov = optimize.curve_fit(f, x, y, p0)
            return popt
        except RuntimeError as e:
            return None

    @staticmethod
    def spline_fill(x, y, newindex, k=3, s=0):
        """
        s gives the smoothness, k is the degree of the spline
        k=1 "linear interpolation"; k=2 "quadratic spline"; k=3 "cubic spline"
        documentation says that use cubic spline by default

        This function will work for both interpolation and extrapolation
        However, using cubic or quadratic spline for extrapolation can give values far from
        the origional range.
        """
        # First line creates the relationship
        tck = interpolate.splrep(x, y, k=k, s=s)
        # Final line passes the new index to fill
        return interpolate.splev(newindex, tck, der=0)

    @staticmethod
    def fill_with_nearest(x, y, newindex):
        """Interpolates and extrapolates using the nearest available known datapoint"""
        if len(y) == 1:  # if we only have 1 good data point
            return np.array([y[0]] * len(newindex))
        
        interp = interpolate.interp1d(x, y, kind='nearest', bounds_error=False)
        fill = interp(newindex)
        fill[newindex < min(x)] = y[np.argmin(x)]
        fill[newindex > max(x)] = y[np.argmax(x)]
        return fill

    @staticmethod
    def fill_with_exponential_regression(x, y, newindex):
        """If growth_rate is None, extrapolates with NaN"""
        if np.all(y==0):
            # edge case where we don't want to throw an error, we just want to fill with zeros
            return np.array([0] * len(newindex))

        if np.any(y<0):
            raise ValueError("fitting with exponential shouldn't be done with negative inputs: y={}, x={}".format(y, x))

        if np.sum(y>0)<2:
            raise ValueError("more than two non-zero points are needed for fitting with exponential: y={}, x={}".format(y, x))

        slope, intercept = np.polyfit(x[y>0], np.log(y[y>0]), 1, w=np.sqrt(y[y>0]))

        # y = c * exp(k*x)
        fill = np.exp(intercept) * np.exp(slope*newindex)
        if any(np.isinf(fill)):
            # sometimes if the data is too steep, it can return inf, try to get an exponential fit just using the beginning and ending points
            # note, this can be dangerous
            fill_dict = dict(zip(x, y))
            firstx, lastx = min(x), max(x)
            firsty, lasty = fill_dict[firstx], fill_dict[lastx]
            growth_rate = (lasty / firsty) ** (1. / (lastx - firstx))
            fill = firsty * (growth_rate) ** (newindex - firstx)
        return fill

    @staticmethod
    def fill_with_exponential_interpolation(x, y, newindex, growth_rate=None):
        """If growth_rate is None, extrapolates with NaN"""
        fill_dict = dict(zip(x, y))
        fill = np.array(map(lambda p: fill_dict.get(p, np.NaN), newindex))

        if growth_rate is None:
            firstx, lastx = min(x), max(x)
            firsty, lasty = fill_dict[firstx], fill_dict[lastx]
            growth_rate = (lasty / firsty) ** (1. / (lastx - firstx))
        else:
            # the growth rates in the DB come in as 0.05, for example, and we need to add 1 before we use it
            growth_rate += 1

        gapindex = np.nonzero(~np.isfinite(fill))[0]
        gapgroups = np.array_split(gapindex, np.where(np.diff(gapindex) != 1)[0] + 1)
        for group in gapgroups:
            if group[0] == 0:
                firstx = newindex[group[-1] + 1]
                firsty = fill_dict[firstx]
                fill[group] = firsty * (growth_rate) ** (newindex[group] - firstx)
            elif group[-1] == len(fill) - 1:
                lastx = newindex[group[0] - 1]
                lasty = fill_dict[lastx]
                fill[group] = lasty * (growth_rate) ** (newindex[group] - lastx)
            else:
                firstx, lastx = newindex[group[0] - 1], newindex[group[-1] + 1]
                firsty, lasty = fill_dict[firstx], fill_dict[lastx]
                rate = (lasty / firsty) ** (1. / (lastx - firstx))
                fill[group] = lasty * (rate) ** (newindex[group] - lastx)
        return fill

    @staticmethod
    def fill_with_average(x, y, newindex):
        fill = np.ones_like(newindex) * np.mean(y)
        return fill

    @staticmethod
    def _run_cleaning_method(x, y, newindex, method, **kwargs):
        if method == 'linear_interpolation':
            return TimeSeries.spline_fill(x, y, newindex, k=1, s=0)
        elif method == 'linear_regression':
            return TimeSeries.linear_regression_fill(x, y, newindex)
        elif method == 'logistic':
            return TimeSeries.fit_generalized_logistic(x, y, newindex, **kwargs)
        elif method == 'cubic':
            return TimeSeries.spline_fill(x, y, newindex, k=3, s=0)
        elif method == 'quadratic':
            return TimeSeries.spline_fill(x, y, newindex, k=2, s=0)
        elif method == 'nearest':
            return TimeSeries.fill_with_nearest(x, y, newindex)
        elif method == 'exponential_interpolation':
            return TimeSeries.fill_with_exponential_interpolation(x, y, newindex, kwargs.get('exp_growth_rate'))
        elif method == 'exponential_regression':
            return TimeSeries.fill_with_exponential_regression(x, y, newindex)
        elif method == 'average' or method == 'mean':
            return TimeSeries.fill_with_average(x, y, newindex)
        elif method == 'decay_towards_linear_regression':
            return TimeSeries.decay_towards_linear_regression_fill(x, y, newindex)
        else:
            raise ValueError("{} is not a known cleaning method type".format(method))

    @staticmethod
    def _clean_method_checks(x, interpolation_method, extrapolation_method, **kwargs):
        if len(x)==1:
            if interpolation_method=='exponential_interpolation' and kwargs.get('exp_growth_rate') is None:
                interpolation_method = 'nearest'
            elif interpolation_method=='exponential_regression':
                interpolation_method = 'nearest'
            elif interpolation_method=='logistic':
                interpolation_method = 'nearest'
                logging.debug('More than one x, y pair is needed for logistic regression, changed to nearest')
            elif interpolation_method is not None and interpolation_method != 'none':
                interpolation_method = 'nearest'

            if extrapolation_method=='exponential_interpolation' and kwargs.get('exp_growth_rate', None) is None:
                extrapolation_method = 'nearest'
            elif extrapolation_method=='exponential_regression':
                extrapolation_method = 'nearest'
            elif extrapolation_method=='logistic':
                extrapolation_method = 'nearest'
                logging.debug('More than one x, y pair is needed for logistic regression, changed to nearest')
            elif extrapolation_method is not None and extrapolation_method != 'none':
                extrapolation_method = 'nearest'

        if interpolation_method == 'quadratic':
            if len(x) < 3:
                # TODO: print to log file here
                interpolation_method = 'linear_interpolation'                
        if extrapolation_method == 'quadratic':
            if len(x) < 3:
                # TODO: print to log file here
                extrapolation_method = 'linear_interpolation'

        if interpolation_method == 'cubic':
            if len(x) < 4:
                # TODO: print to log file here
                interpolation_method = 'linear_interpolation'
        if extrapolation_method == 'cubic':
            if len(x) < 4:
                # TODO: print to log file here
                extrapolation_method = 'linear_interpolation'

        if interpolation_method == 'decay_towards_linear_regression':
            raise ValueError('decay_towards_linear_regression is only supported for extrapolation, not interpolation')

        return interpolation_method, extrapolation_method, kwargs

    @staticmethod
    def clean(data, newindex=None, interpolation_method=None, extrapolation_method=None, time_index_name=None, **kwargs):
        """
        Return cleaned timeseries data reindexed to time_index, interpolated for missing data points,
        and extrapolated using selected method.

        Each column in the dataframe is cleaned and the returned data maintains column names

        Cleaning methods:
            linear_interpolation - linear interpolation between points (default)
            linear_regression - linear regression for a set of x, y values and fill
            logistic - fit logistic regression and fill
            nearest - fill missing value with nearest y value
            quadratic - quadratic spline fill (no smoothing)
            cubic - cubic spline fill (no smoothing)
            exponential - annual growth rate for extrapolating data
            average - takes an average of all given values to fill in missing values

        Args:
            data (dataframe): dataframe with missing values
            interpolation_method (string): method to use between max(y) and min(y), defaults to linear_interpolation
            extrapolation_method (string): method to use beyond the range of max(y) and min(y), defaults to linear_interpolation
            newindex (array): new dataframe index to fill, defaults to range(min(x), max(x)+1)

        Returns:
            returndata (dataframe): reindexed and with values filled
        """
        if not len(data):
            raise IndexError('Empty data passed to TimeSeries.clean')

        if not isinstance(data, pd.core.frame.DataFrame):
            raise ValueError('cleaning requires a pandas dataframe as an input')
        
        if np.all(data.isnull()):
            raise ValueError('cleaning requires at least one finite data point')

        if data.index.nlevels > 1:
            return TimeSeries._clean_multindex(data[:], time_index_name, interpolation_method, extrapolation_method, newindex, **kwargs)
        else:
            return TimeSeries._singleindex_clean(data[:], newindex, interpolation_method, extrapolation_method, **kwargs)

    @staticmethod
    def _clean_multindex(data, time_index_name, interpolation_method=None, extrapolation_method=None, newindex=None, **kwargs):
        if time_index_name not in data.index.names:
            raise ValueError('Time_index_name must match one of the index level names if cleaning a multi-index dataframe')

        if newindex is None:
            exist_index = data.index.get_level_values(time_index_name)
            newindex = np.array(sorted(set(exist_index)), dtype=int)
            # newindex = np.arange(min(exist_index), max(exist_index) + 1, dtype=int)
        elif not isinstance(newindex, np.ndarray):
            # We use newindex to calculate extrap_index using a method that takes an array
            newindex = np.array(newindex, dtype=int)
        
        # this is done so that we can take use data that falls outside of the newindex
        wholeindex = np.array(sorted(list(set(newindex) | set(data.index.get_level_values(time_index_name)))), dtype=int)

        # Add new levels to data for missing time indices
        data = util.reindex_df_level_with_new_elements(data, time_index_name, wholeindex)
        

        group_levels = tuple([n for n in data.index.names if n != time_index_name])
        data = data.groupby(level=group_levels).apply(TimeSeries._clean_multindex_helper,
                                                      time_index_name=time_index_name,
                                                      newindex=wholeindex,
                                                      interpolation_method=interpolation_method,
                                                      extrapolation_method=extrapolation_method,
                                                      **kwargs)
        
        data = util.reindex_df_level_with_new_elements(data, time_index_name, newindex)

        return data

    @staticmethod
    def _clean_multindex_helper(data, time_index_name, newindex, interpolation_method=None, extrapolation_method=None, **kwargs):
        
        x = np.array(data.index.get_level_values(time_index_name), dtype=int)

        for colname in data.columns:
            y = np.array(data[colname])
            if not np.any(np.isfinite(y)):
                continue
            data[colname] = TimeSeries.cleanxy(x, y, newindex, interpolation_method, extrapolation_method, **kwargs)
        
        return data

    @staticmethod
    def _singleindex_clean(data, newindex=None, interpolation_method=None, extrapolation_method=None, **kwargs):
        
        # TODO: duplicate values should raise an error when doing data validation
        # drop duplicates
        data.groupby(data.index).first()

        data = data.sort_index()

        if newindex is None:
            newindex = np.arange(min(data.index), max(data.index) + 1, dtype=int)
        elif not isinstance(newindex, np.ndarray):
            # We use newindex to calculate extrap_index using a method that takes an array
            newindex = np.array(newindex, dtype=int)
        
        # this is done so that we can take use data that falls outside of the newindex
        wholeindex = np.array(sorted(list(set(newindex) | set(data.index))), dtype=int)

        data = data.reindex(wholeindex)
        x = np.array(data.index)

        for colname in data.columns:
            y = np.array(data[colname])
            data[colname] = TimeSeries.cleanxy(x, y, wholeindex, interpolation_method, extrapolation_method, **kwargs)
        
        data = data.reindex(newindex)
        
        return data

    @staticmethod
    def cleanxy(x, y, newindex, interpolation_method=None, extrapolation_method=None, replace_training_data=True, **kwargs):
        #if you have no interpolation method, start with the current y (with nans)
        if interpolation_method is None or interpolation_method == 'none':
            yhat = y.copy()
            
        goody = np.nonzero(np.isfinite(y))[0]  # Used to isolate only good data (not NaN)
        x = np.array(x)[goody]
        y = np.array(y)[goody]

        interpolation_method, extrapolation_method, kwargs = TimeSeries._clean_method_checks(x, interpolation_method, extrapolation_method, **kwargs)

        ##################
        # interpolation
        ##################
        # basic process is to use interpolation method on ALL points and then replace points with
        # extrapolation method if it is specified. Objective is to cut down on if statements and make
        # interpolation and extrapolation consistant in the case of curve fitting
        if interpolation_method is not None and interpolation_method != 'none':
            yhat = TimeSeries._run_cleaning_method(x, y, newindex, interpolation_method, **kwargs)

        ##################
        # extrapolation
        ##################
        # if given an extrapolation method and there are points to extrapolate to
        extrap_index = np.nonzero(np.any([newindex < min(x), newindex > max(x)], axis=0))[0]
        if extrapolation_method is None or extrapolation_method == 'none':
            yhat[extrap_index] = np.NaN
        elif len(extrap_index) and extrapolation_method != interpolation_method:
            yhat[extrap_index] = TimeSeries._run_cleaning_method(x, y, newindex, extrapolation_method, **kwargs)[extrap_index]
        
        # fill back in the "training" data, meaning good data kept and not replaced
        if not replace_training_data:
            yhat[goody] = y
        
        return yhat

# newindex = np.arange(2000, 2051)
# x = np.array([2015, 2045, 2070])
# y = np.array([.2, .8, 1])
# start = pd.DataFrame(y, index=x)
# interpolation_method = 'logistic'
# extrapolation_method = 'logistic'
# filled = TimeSeries.clean(start, newindex, interpolation_method, extrapolation_method)
#
# pylab.plot(newindex, filled.values.flatten(), '.')
# pylab.plot(x, y, '*')

# newindex = np.arange(2000, 2051)
# x = np.array([2015, 2020, 2025, 2030, 2040])
# y = np.array([.2, -0.03, .1, 6, 4])
# start = pd.DataFrame(y, index=x)
# interpolation_method = 'linear_regression'
# extrapolation_method = 'decay_towards_linear_regression'
# filled = TimeSeries.clean(start, newindex, interpolation_method, extrapolation_method)
#
# pylab.plot(newindex, filled.values.flatten(), '.')
# pylab.plot(x, y, '*')

# decay_towards_linear_regression

# newindex = np.arange(2000, 2051)
# x = np.array([2015, 2020, 2025, 2030, 2040, 2050])
# y = np.array([0.01, 0.03, .1, 1, .8, .4])
# # x = np.array([2020])
# # y = np.array([0.716194956])
# start = pd.DataFrame(y, index=x)
# interpolation_method = 'exponential'
# extrapolation_method = 'exponential'
# filled = TimeSeries.clean(start, newindex, interpolation_method, extrapolation_method)
#
# pylab.plot(newindex, filled.values.flatten(), '.')
# pylab.plot(x, y, '*')

# newindex = np.arange(2000, 2051)
# # x = np.array([2015, 2020, 2025, 2030, 2040, 2050])
# # y = np.array([0.01, 0.03, .1, 1, .8, .4])
# x = np.array([2000, 2010, 2015])
# y = np.array([0.6, 0.716194956, .725])
# start = pd.DataFrame(y, index=x)
# interpolation_method = 'linear_interpolation'
# extrapolation_method = 'exponential_regression'
# filled = TimeSeries.clean(start, newindex, interpolation_method, extrapolation_method)
#
# pylab.plot(newindex, filled.values.flatten(), '-.')
# pylab.plot(x, y, '*')
#
#'linear_interpolation'
#'linear_regression'
#'logistic'
#'nearest'
#'quadratic'
#'cubic'
#'exponential'

#B = .5

#M2 = approx_M(A, K, B, x[1], y[1])
#B2 = approx_B(A, K, M2, x[0], .01)
#M2 = approx_M(A, K, B2, x[1], y[1])

#y = A + ((K - A) / (1 + e^(-B * (x - M))))

#newindex = np.arange(2015, 2051)
#
#y_hat = TimeSeries.fit_generalized_logistic(x, y, newindex)
#


#x = np.array([2016, 2023, 2030, 2040, 2050])
#y = np.array([0, .16, .48, .7, .72])

#x = np.array([2015, 2030, 2033, 2050])
#y = np.array([0, .48, .6, .72])



# groups.apply(TimeSeries.clean, args=(time_index_name, interpolation_method, extrapolation_method, newindex, lbound, ubound))
# @staticmethod
# def generate_data_to_clean(data, time_index_name):
#
# if data.index.nlevels>1:
# if time_index_name is None or time_index_name not in data.index.names:
# raise ValueError('time_index_name must match one of the index level names')
# group_levels = [n for n in data.index.names if n!=time_index_name]
# groups = data.groupby(level=group_levels)
# for key, value in groups:
# print data.loc[key]
# print value
# break
# else:
# if time_index_name is not None and time_index_name not in data.index.names:
# raise ValueError('time_index_name must match one of the index level names')
# else:
# time_index_name = data.index.names[0]


# frames = []
# for group in data.groupby(level=group_levels).groups.keys():
# if isinstance(group, basestring):
# group = (group,)
#
# data_slice = data.xs(group, level=group_levels)
# clean_data = TimeSeries.clean(data_slice, time_index_name, interpolation_method, extrapolation_method, newindex, lbound, ubound).reset_index()
#
# for level, ele in zip(group_levels, group):
# clean_data[level] = ele
#    
#    frames.append(clean_data)


#from collections import defaultdict
#

#x = np.array([2010, 2018, 2025, 2040, 2050])
#y = np.array([.8, .7, .4, .35, .34])
#
#example_data = pd.DataFrame(y, index=x)

#
#data = defaultdict(dict)
#data['a']['a'] = pd.DataFrame(y, index=x)
#data['a']['b'] = pd.DataFrame(y, index=x)
#data['b'] = pd.DataFrame(y, index=x)
#
#newdata = TimeSeries.clean_dict(data, newindex=newindex)
