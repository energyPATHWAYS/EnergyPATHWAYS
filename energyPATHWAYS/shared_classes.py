# -*- coding: utf-8 -*-
"""
Created on Tue Nov 17 08:46:24 2015

@author: Ben
"""
import util 
import numpy as np
import pandas as pd
from datamapfunctions import Abstract
import config as cfg
import pdb
import logging
from .generated import schema
from .geomapper import GeoMapper

class StockItem(object):
    def __init__(self):
        self.spy = 1. #stock rollover steps per year

    def calculate_sales_shares(self, sales_shares,reference_run=False):
        sales_shares = getattr(self, sales_shares)
        for sales_share in sales_shares.values():
            sales_share.calculate(vintages=self.vintages[1:], years=self.years)
                
    def calculate_sales(self, sales):
        sales= getattr(self, sales)
        for sales in sales.values():
            sales.calculate(vintages=self.vintages[1:], years=self.years)       
            
    def calculate_specified_stocks(self):
        stock_measures = getattr(self, 'specified_stocks')
        for stock_measure in stock_measures.values():
            stock_measure.calculate(vintages=self.vintages, years=self.years)
    
    def reconcile_sales_shares(self, sales_shares, needed_sales_share_levels, needed_sales_share_names):
        sales_shares = getattr(self, sales_shares)
        for sales_share in sales_shares.values():
            sales_share.reconcile_with_stock_levels(needed_sales_share_levels, needed_sales_share_names)
            
    def reconcile_sales(self, sales, needed_sales_levels, needed_sales_names):
        sales = getattr(self, sales)
        for sales in sales.values():
            sales.reconcile_with_stock_levels(needed_sales_levels, needed_sales_names)

    def set_survival_parameters(self):
        if self.mean_lifetime is None and self.min_lifetime is not None and self.max_lifetime is not None:
            self.mean_lifetime = self.min_lifetime + (self.max_lifetime - self.min_lifetime) / 2.
        if self.lifetime_variance is None and self.min_lifetime is not None and self.max_lifetime is not None:
            self.lifetime_variance = ((self.max_lifetime - self.min_lifetime) / 2. * .5) ** 2  # approximate
        if self.stock_decay_function == 'weibull':
            self.weibull_beta_parameter = util.find_weibul_beta(self.mean_lifetime*self.spy, self.lifetime_variance*self.spy**2)
            self.weibull_alpha_parameter = self.mean_lifetime*self.spy / util.mean_weibul_factor(self.weibull_beta_parameter)
            self.max_survival_periods = max((self.mean_lifetime + np.sqrt(self.lifetime_variance)*10), len(self.years))*self.spy + 1
        elif self.stock_decay_function == 'linear':
            if self.min_lifetime is None and self.mean_lifetime is not None and self.lifetime_variance is not None:
                self.min_lifetime = self.mean_lifetime - 2 * self.lifetime_variance ** .5  # approximate
            if self.max_lifetime is None and self.mean_lifetime is not None and self.lifetime_variance is not None:
                self.max_lifetime = self.mean_lifetime + 2 * self.lifetime_variance ** .5  # approximate
            self.max_survival_periods = max(self.max_lifetime, len(self.years))*self.spy + 1
        elif self.stock_decay_function == 'exponential':
            self.max_survival_periods = max((self.mean_lifetime + np.sqrt(self.lifetime_variance)*10), len(self.years))*self.spy + 1

    def calc_survival_vintaged(self, periods):
        if self.stock_decay_function == 'weibull':
            return np.exp(-(np.arange(periods) / self.weibull_alpha_parameter) ** self.weibull_beta_parameter)
        elif self.stock_decay_function == 'linear':
            start = [1] * int(round((self.min_lifetime - 1)*self.spy))
            middle = np.linspace(1, 0, int(round((self.max_lifetime - self.min_lifetime)*self.spy)) + 1)
            end = [0] * int(max(periods - (len(start) + len(middle)), 0))
            return np.concatenate((start, middle, end))[:int(periods)]
        elif self.stock_decay_function == 'exponential':
            rate = 1. / (self.mean_lifetime*self.spy)
            return np.exp(-rate * np.arange(periods))
        else:
            raise ValueError('Unsupported stock decay function for stock id %s' % self.id)

    def set_survival_vintaged(self):
        periods = len(self.years)*self.spy + 1
        self.survival_vintaged = self.calc_survival_vintaged(periods)

    def set_decay_vintaged(self):
        if not hasattr(self, 'survival_vintaged'):
            self.set_survival_vintaged()
        self.decay_vintaged = np.append([0.], np.diff(-self.survival_vintaged))

    def set_survival_initial_stock(self):
        long_survival_vintaged = self.calc_survival_vintaged(self.max_survival_periods)
        self.survival_initial_stock = np.array([np.sum(long_survival_vintaged[i:]) for i in range(int(len(self.years)*self.spy + 1))])
        self.survival_initial_stock /= self.survival_initial_stock[0]

    def set_decay_initial_stock(self):
        if not hasattr(self, 'survival_initial_stock'):
            self.set_survival_initial_stock()
        self.decay_initial_stock = np.append([0.], np.diff(-self.survival_initial_stock))
        
        
class AggregateStock(object):
    def __init__(self):
        pass

    def calc_annual_stock_changes(self):
        # stock is steady before the first year, thus fill the first NaN with 0
        self.annual_stock_changes = self.total.groupby(level=self.rollover_group_names).transform(pd.Series.diff).fillna(0)

    def set_rollover_groups(self):
        # separate stock rollover except for year and technology
        self.rollover_group_levels = []
        self.rollover_group_names = []
        for name, level in zip(self.total.index.names, self.total.index.levels):
            if (name == 'year') or (name == 'technology'):
                continue
            self.rollover_group_levels.append(list(level))
            self.rollover_group_names.append(name)



class Stock(object):
    def __init__(self):
        pass

    def in_use_drivers(self):
        """reduces the stock driver dictionary to in-use drivers"""
        driver_ids = [getattr(self, col) for col in cfg.drivr_col_names if getattr(self, col) is not None]
        denominator_driver_ids = [getattr(self, col) for col in cfg.dnmtr_col_names if getattr(self, col) is not None]

        drivers = driver_ids + denominator_driver_ids
        self.drivers = {k: v for k, v in self.drivers.iteritems() if k in drivers}


    def calc_annual_stock_changes(self):
        # stock is steady before the first year, thus fill the first NaN with 0
        self.annual_stock_changes = self.total.groupby(level=self.rollover_group_names).transform(pd.Series.diff).fillna(0)

    def set_rollover_groups(self):
        # separate stock rollover except for year and technology
        self.rollover_group_levels = []
        self.rollover_group_names = []
        for name, level in zip(self.total.index.names, self.total.index.levels):
            if (name == 'year') or (name == 'technology'):
                continue
            self.rollover_group_levels.append(list(level))
            self.rollover_group_names.append(name)

    @staticmethod
    def calc_initial_shares(initial_total, transition_matrix, num_years=100):
        """ Use a transition matrix to calculate the initial stock share
        transition matrix: when technology in the column retires it is replace with technology in the row
        All columns must sum to 1
        Method works by raising the transition matrix to some large number then multiplying by the initial stock total
        """
        return np.mean(np.linalg.matrix_power(transition_matrix, num_years), axis=1) * initial_total

    def return_stock_slice(self, elements, levels, stock_name='technology'):
        group = util.df_slice(getattr(self,stock_name), elements, levels)
        return group


class SpecifiedStock(object):
    def __init__(self):
        pass

    def calculate(self, vintages, years):
        self.vintages = vintages
        self.years = years
        if self.raw_values is not None:
            try:
                self.remap(fill_value=np.nan, converted_geography=self.primary_geography)
            except:
                print self.raw_values
                raise
        else:
            self.values = None

    def set_geography_map_key(self, geography_map_key):
        self.geography_map_key = geography_map_key

class DemandStockMeasure(schema.DemandStockMeasures, SpecifiedStock):
    def __init__(self, name, subsector, scenario=None):
        schema.DemandStockMeasures.__init__(self, name=name, scenario=scenario)
        self.init_from_db(name, scenario, subsector=subsector)
        self.primary_geography = GeoMapper.demand_primary_geography
        self.scenario = scenario
        self.mapped = False
        self.input_type='total'

class SalesShare(object):
    def __init__(self):
        pass

    def calculate(self, vintages, years):
        self.vintages = vintages
        self.years = years
        self.remap(time_index_name='vintage', converted_geography=self.primary_geography)
        self.values = util.remove_df_levels(self.values, cfg.removed_demand_levels, agg_function='mean')
        
    def reconcile_with_stock_levels(self, needed_sales_share_levels, needed_sales_share_names):
        if self.input_type == 'intensity':
            if not set(self.values.index.names).issubset(needed_sales_share_names):
                # we can't have more specificity in sales share than in stock
                raise ValueError('Sales share expressed as an intensity cannot have levels not in stock')
            # pick up extra levels
            self.values = util.expand_multi(self.values, needed_sales_share_levels,
                                            needed_sales_share_names).sort_index()
            self.values.fillna(0, inplace=True)
        elif self.input_type == 'total':
            raise ValueError(
                'A sales share type of total is not currently supported. Please normalize to sales share as a percentage')
            # if not set(sales_share.values.index.names).issubset(stock.values.index.names):
            # we have extra salesshare levels and we need to do a groupby sum
            # sales_share.values = sales_share.values.groupby(level=needed_sales_share_levels).sum()
            # todo: add logic here so that if stock and service demand
            # has more specificity than sales share, we raise an exception

    @staticmethod
    def scale_reference_array_to_gap(ss_array, space_for_reference):
        num_years, num_techs, num_techs = np.shape(ss_array)

        ref_sums = np.nansum(ss_array, axis=1)

        # ignore where no reference is specified to avoid dividing by zero
        vintage_no_ref, retiring_no_ref = np.nonzero(ref_sums)

        factors = np.zeros(np.shape(ref_sums))
        factors[vintage_no_ref, retiring_no_ref] += space_for_reference[vintage_no_ref, retiring_no_ref] / ref_sums[vintage_no_ref, retiring_no_ref]
        factors = np.reshape(np.repeat(factors, num_techs, axis=0), (num_years, num_techs, num_techs))

        # gross up reference sales share with the need
        return ss_array * factors

    @staticmethod
    def normalize_array(ss_array, retiring_must_have_replacement=True):
        # Normalize to 1
        sums = np.nansum(ss_array, axis=1)

        if np.any(sums == 0) and retiring_must_have_replacement:
            raise ValueError('Every retiring technology must have a replacement specified in sales share')

        # indicies needing scaling
        vintage, retiring = np.nonzero(sums != 1)

        # normalize all to 1
        ss_array[vintage, :, retiring] = (ss_array[vintage, :, retiring].T / sums[vintage, retiring]).T
        # we either divided by zero or everything came in as zeros, this gave us NaNs that we want to return to zero
        if not retiring_must_have_replacement:
            ss_array = np.nan_to_num(ss_array)
        return ss_array

    @staticmethod
    def cap_array_at_1(ss_array):
        # Normalize down to 1
        sums = np.nansum(ss_array, axis=1)
        vintage, retiring = np.nonzero(sums > 1)
        # normalize those greater than 1
        ss_array[vintage, :, retiring] = (ss_array[vintage, :, retiring].T / sums[vintage, retiring]).T
        return ss_array

class DemandSales(schema.DemandSales, SalesShare):
    def __init__(self, demand_technology, scenario=None):
        schema.DemandSales.__init__(self, demand_technology=demand_technology, scenario=scenario)
        self.init_from_db(demand_technology, scenario)
        self.primary_geography = GeoMapper.demand_primary_geography
        self.scenario = scenario
        self.mapped = False
        self.replaced_demand_tech_id = None
        if self.raw_values is None:
            raise ValueError('error encountered in sales share measure ' + str(self.name))

class DemandSalesShareMeasure(schema.DemandSalesShareMeasures, SalesShare):
    def __init__(self, name, subsector, scenario=None):
        schema.DemandSalesShareMeasures.__init__(self, name=name, scenario=scenario)
        self.init_from_db(name, scenario, subsector=subsector)
        self.primary_geography = GeoMapper.demand_primary_geography
        self.scenario = scenario
        self.mapped = False
        if self.raw_values is None:
            raise ValueError('error encountered in sales share measure ' + str(self.name))
        self.raw_values = util.remove_df_levels(self.raw_values, 'technology')