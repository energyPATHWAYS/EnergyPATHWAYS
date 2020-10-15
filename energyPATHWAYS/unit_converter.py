__author__ = 'ryan'

import pandas as pd
import numpy as np
import os
import logging
import pdb
import pint

import config as cfg
from csvdb.data_object import get_database

class UnitConverter:
    _instance = None
    _unit_defs = ['US_gge = 120,500 * BTU',
                 'US_gde = 138,490 * BTU',
                 'US_gee = 80337.35 * BTU',
                 'lng_gallon = 82,644 * BTU',
                 'mmBtu = 1,000,000 * BTU',
                 'mmbtu = 1,000,000 * BTU',
                 'lumen = candela * steradian',
                 'lumen_hour = candela * steradian * hour',
                 'lumen_year = candela * steradian * year',
                 'quad = 1,000,000,000,000,000 * BTU',
                 'cubic_foot = 28316.8 * cubic_centimeter',
                 'cubic_meter = 1000000 * cubic_centimeter',
                 'cubic_foot_hour = cubic_foot * hour',
                 'cubic_foot_year = cubic_foot * year',
                 'cubic_feet_year = cubic_foot * year',
                 'TBtu  = 1,000,000,000,000 * BTU',
                 'ton_mile = ton * mile',
                 'h2_kilogram = 39.5 * kilowatt_hour',
                 'jet_fuel_gallon = 125800 * Btu',
                 'pipeline_gas_cubic_meter = 9000 * kilocalorie',
                 'boe = 5,800,000 * Btu',
                 'bee = 3,559,000 * Btu',
                 'TW_hour = terawatt_hour',
                 'MW_hour = megawatt_hour',
                 'kW_hour = kilowatt_hour']

    @classmethod
    def get_instance(cls, database_path=None):
        if cls._instance is None:
            cls._instance = UnitConverter(database_path)
        return cls._instance

    def __init__(self, database_path):
        # Initiate pint for unit conversions
        self.ureg = pint.UnitRegistry()
        self.cfg_energy_unit = cfg.getParam('calculation_energy_unit')
        self.cfg_currency = cfg.getParam('currency_name')
        self.cfg_currency_year = cfg.getParamAsInt('currency_year')

        db = get_database(database_path)
        self.currency_table = db.get_table("CurrenciesConversion").data
        self.currency_table = self.currency_table.set_index(['currency', 'year']).sort_index()
        self.inflation_table = db.get_table("InflationConversion").data
        self.inflation_table = self.inflation_table.set_index(['currency', 'year']).sort_index()

        for unit_def in UnitConverter._unit_defs:
            unit_name = unit_def.split(' = ')[0]
            if hasattr(self.ureg, unit_name):
                logging.debug('pint already has unit {}, unit is not being redefined'.format(unit_name))
                continue
            self.ureg.define(unit_def)

    @classmethod
    def unit_convert(cls, data=1, unit_from_num=None, unit_from_den=None, unit_to_num=None, unit_to_den=None):
        uc = cls.get_instance()
        """return data converted from unit_from to unit_to"""
        # This is used to cancel out units that are the same but may not be recognized by the ureg
        if unit_from_num == unit_to_num:
            unit_from_num = unit_to_num = None
        if unit_from_den == unit_to_den:
            unit_from_den = unit_to_den = None
        if unit_from_num == unit_to_den:
            unit_from_num = unit_to_den = None
        if unit_from_den == unit_to_num:
            unit_from_den = unit_to_num = None

        input_unit = uc.ureg.parse_expression(unit_from_num) / uc.ureg.parse_expression(unit_from_den)
        output_unit = uc.ureg.parse_expression(unit_to_num) / uc.ureg.parse_expression(unit_to_den)
        try:
            factor = input_unit.to(output_unit).magnitude
            return data * factor
        except pint.DimensionalityError:
            try:
                factor = (1. / input_unit).to(output_unit).magnitude
            except:
                pdb.set_trace()
            return (1. / data) * factor

    def exchange_rate(self, year, currency_from, currency_to=None):
        """calculate exchange rate between two specified currencies"""
        currency_to = currency_to or self.cfg_currency
        if (currency_from, year) not in self.currency_table.index:
            raise ValueError("Unable to find currency '{}' for year '{}' in available currencies: {}".format(currency_from, year, self.currency_table.index.levels))
        return self.currency_table.loc[(currency_to, year),] / self.currency_table.loc[(currency_from, year),]

    def inflation_rate(self, currency, year_from, year_to=None):
        """calculate inflation rate between two years in a specified currency"""
        year_to = year_to or self.cfg_currency_year
        return self.inflation_table.loc[(currency, year_to),] / self.inflation_table.loc[(currency, year_from),]

    @classmethod
    def currency_convert(cls, data, currency_from, year_from, currency_to=None, year_to=None, currency_multiple=1):
        """converts cost data in original currency specifications (currency,year) to model currency and year"""
        uc = cls.get_instance()
        currency_to = currency_to or uc.cfg_currency
        year_to = year_to or uc.cfg_currency_year

        # exchange rate factor
        exc_rate = uc.exchange_rate(year_to, currency_from, currency_to)

        # inflation factor
        available_currencies = uc.inflation_table.index.get_level_values('currency').unique()
        if currency_from in available_currencies:
            # best if we are able to use inflation in the starting currency
            inf_rate = uc.inflation_rate(currency_from, year_from, year_to)
        elif currency_to in available_currencies:
            # second best if we are able to use inflation in the ending currency
            inf_rate = uc.inflation_rate(currency_to, year_from, year_to)
        else:
            # last resort is to use USD as a proxy for inflation
            exc_rate = uc.exchange_rate(year_from, currency_from=currency_from, currency_to='USD')
            inf_rate = uc.inflation_rate('USD', year_from, year_to)
            exc_rate *= uc.exchange_rate(year_to, currency_from='USD', currency_to=currency_to)
        df =  data * exc_rate.values * inf_rate.values
        if type(df) is pd.core.frame.DataFrame and np.any(np.isnan(df.values)):
            pdb.set_trace()
        else:
            return df

    @classmethod
    def is_energy_unit(cls, unit):
        uc = cls.get_instance()
        if uc.ureg.Quantity(unit).dimensionality == uc.ureg.Quantity('kilowatt_hour').dimensionality:
            return True
        else:
            return False


if __name__ == "__main__":
    path = r'C:\github\EP_US_db\180728_US.db'
    os.chdir(path)
    cfg.initialize_config(r'C:\github\EP_runs\csv_migration', 'config.INI', None)
    uc = self = UnitConverter.get_instance(path)

    currency_from, year_from, currency_to, year_to = 'EUR', 2001, 'USD', 2015
    factor = UnitConverter.currency_convert(1, currency_from, year_from, currency_to, year_to)
    print currency_from, year_from, currency_to, year_to, factor

    currency_from, year_from, currency_to, year_to = 'EUR', 2015, 'USD', 2001
    factor = UnitConverter.currency_convert(1, currency_from, year_from, currency_to, year_to)
    print currency_from, year_from, currency_to, year_to, factor

    currency_from, year_from, currency_to, year_to = 'USD', 2015, 'EUR', 2001
    factor = UnitConverter.currency_convert(1, currency_from, year_from, currency_to, year_to)
    print currency_from, year_from, currency_to, year_to, factor

    currency_from, year_from, currency_to, year_to = 'USD', 2001, 'USD', 2015
    factor = UnitConverter.currency_convert(1, currency_from, year_from, currency_to, year_to)
    print currency_from, year_from, currency_to, year_to, factor

    currency_from, year_from, currency_to, year_to = 'AUD', 2001, 'CAD', 2015
    factor = UnitConverter.currency_convert(1, currency_from, year_from, currency_to, year_to)
    print currency_from, year_from, currency_to, year_to, factor

    unit_from_num, unit_from_den = 'kilowatt_hour', 'year'
    unit_to_num, unit_to_den = 'megawatt_hour', 'month'
    factor = UnitConverter.unit_convert(1, unit_from_num, unit_from_den, unit_to_num, unit_to_den)
    print unit_from_num, unit_from_den, unit_to_num, unit_to_den, factor

    unit_from_num, unit_from_den = 'gallons', 'kilometer'
    unit_to_num, unit_to_den = 'mile', 'gallons'
    factor = UnitConverter.unit_convert(10, unit_from_num, unit_from_den, unit_to_num, unit_to_den)
    print unit_from_num, unit_from_den, unit_to_num, unit_to_den, factor

    unit_from_num, unit_from_den = 'kilometer', 'gallons'
    unit_to_num, unit_to_den = 'mile', 'gallons'
    factor = UnitConverter.unit_convert(10, unit_from_num, unit_from_den, unit_to_num, unit_to_den)
    print unit_from_num, unit_from_den, unit_to_num, unit_to_den, factor

    unit_from_num, unit_from_den = 'miles', 'gallons'
    unit_to_num, unit_to_den = 'liters', 'miles'
    factor = UnitConverter.unit_convert(10, unit_from_num, unit_from_den, unit_to_num, unit_to_den)
    print unit_from_num, unit_from_den, unit_to_num, unit_to_den, factor

    unit_from_num, unit_from_den = 'miles', 'gallons'
    unit_to_num, unit_to_den = 'miles', 'liters'
    factor = UnitConverter.unit_convert(10, unit_from_num, unit_from_den, unit_to_num, unit_to_den)
    print unit_from_num, unit_from_den, unit_to_num, unit_to_den, factor

    unit_from_num, unit_from_den = 'test_non_unit', 'gallons'
    unit_to_num, unit_to_den = 'test_non_unit', 'liters'
    factor = UnitConverter.unit_convert(10, unit_from_num, unit_from_den, unit_to_num, unit_to_den)
    print unit_from_num, unit_from_den, unit_to_num, unit_to_den, factor

    unit_from_num, unit_from_den = 'gallons', 'test_non_unit'
    unit_to_num, unit_to_den = 'test_non_unit', 'liters'
    factor = UnitConverter.unit_convert(10, unit_from_num, unit_from_den, unit_to_num, unit_to_den)
    print unit_from_num, unit_from_den, unit_to_num, unit_to_den, factor