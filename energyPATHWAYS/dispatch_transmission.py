
import util
import numpy as np
import copy
import pandas as pd
import math
import config as cfg
from geomapper import GeoMapper
from unit_converter import UnitConverter
from energyPATHWAYS.generated import schema
from data_object import DataObject
import pdb

class TransmissionSuper(DataObject):
    """loads and cleans the data that allocates demand sectors to dispatch feeders"""
    def __init__(self):
        self._setup_and_validate()


    def _setup_and_validate(self):
        if self.raw_values is None:
            self._setup_zero_constraints()
            return""
       # self._validate_gaus()
        self.values = self.clean_timeseries(attr='raw_values', inplace=False, time_index=cfg.supply_years, time_index_name='year', interpolation_method=self.interpolation_method, extrapolation_method=self.extrapolation_method)
        # fill in any missing combinations of geographies
        self.values = util.reindex_df_level_with_new_elements(self.values, 'gau_from', GeoMapper.dispatch_geographies)
        self.values = util.reindex_df_level_with_new_elements(self.values, 'gau_to', GeoMapper.dispatch_geographies)
        self.values = self.values.fillna(0)
        self.values = self.values.sort_index()

    def _setup_zero_constraints(self):
        index = pd.MultiIndex.from_product([cfg.supply_years,GeoMapper.dispatch_geographies, GeoMapper.dispatch_geographies], names=['year', 'gau_from', 'gau_to'])
        self.values = pd.DataFrame(0, index=index, columns=['value'])

    def _validate_gaus(self):
        dispatch_geographies = set(GeoMapper.dispatch_geographies)
        geography_from_names = self.raw_values.index.get_level_values('gau_from')
        if len(set(geography_from_names) - dispatch_geographies):
            raise ValueError("gau_from_names {} are found in transmission constraint name {} "
                             "but not found in the dispatch_geographies {}".format(list(set(geography_from_names) - dispatch_geographies), self.name, GeoMapper.dispatch_geographies))
        geography_to_names = self.raw_values.index.get_level_values('gau_to')
        if len(set(geography_to_names) - dispatch_geographies):
            raise ValueError("gau_to_names {} are found in transmission constraint name {} "
                             "but not found in the dispatch_geographies {}".format(list(set(geography_to_names) - dispatch_geographies), self.name, GeoMapper.dispatch_geographies))

        if any([name in self.raw_values.index.names for name in ('month', 'hour', 'day_type_name')]):
            print 'Time slices for transmission constraints are not implemented yet, average of all combinations will be used'
            self.raw_values = util.remove_df_levels(self.raw_values,[name for name in ('month', 'hour', 'day_type_name')],agg_function='mean')

    def get_values_as_dict(self, year):
        capacity = util.df_slice(self.values,year,'year').squeeze().to_dict()
        for key in capacity.keys():
            if key[0]==key[1]:
                del capacity[key]
        # tuple needs to be a string in the optimization
        capacity = dict(zip([str((key[0], key[1])) for key in capacity.keys()], capacity.values()))
        return capacity

    def get_values(self, year):
        return util.df_slice(self.values,year,'year')

class DispatchTransmissionConstraint(schema.DispatchTransmissionConstraint, TransmissionSuper):
    """loads and cleans the data that allocates demand sectors to dispatch feeders"""
    def __init__(self, name, scenario):
        schema.DispatchTransmissionConstraint.__init__(self, name, scenario=scenario)
        if self.name is not None:
           self.init_from_db(name, scenario)
        TransmissionSuper.__init__(self)
        self.scenario = scenario
        self.name = name
        if self.name is None:
            self._setup_zero_constraints()
        else:
            self._setup_and_validate()
        self.convert_units()

    def convert_units(self):
        if self.name is not None:
            unit_factor = UnitConverter.unit_convert(1, unit_from_den=self.energy_unit, unit_to_den=cfg.calculation_energy_unit)
            self.values /= unit_factor


class DispatchTransmissionHurdleRate(schema.DispatchTransmissionHurdleRate, TransmissionSuper):
    """loads and cleans the data that allocates demand sectors to dispatch feeders"""
    def __init__(self, name, scenario):
        schema.DispatchTransmissionHurdleRate.__init__(self, name, scenario=scenario)
        if self.name is not None:
           self.init_from_db(name, scenario)
        self.name = name
        TransmissionSuper.__init__(self)
        self.scenario = scenario
        self.convert_units()


    def convert_units(self):
        if self.name is not None:
            unit_factor = UnitConverter.unit_convert(1, unit_from_den=self.energy_unit, unit_to_den=cfg.calculation_energy_unit)
            self.values *= unit_factor

class DispatchTransmissionLosses(schema.DispatchTransmissionLosses, TransmissionSuper):
    """loads and cleans the data that allocates demand sectors to dispatch feeders"""
    def __init__(self, name, scenario):
        schema.DispatchTransmissionLosses.__init__(self, name, scenario=scenario)
        self.name = name
        if self.name is not None:
           self.init_from_db(name, scenario)
        TransmissionSuper.__init__(self)
        self.scenario = scenario

class DispatchTransmissionCost(schema.DispatchTransmissionCost, TransmissionSuper):
    """loads and cleans the data that allocates demand sectors to dispatch feeders"""
    def __init__(self, name, scenario):
        schema.DispatchTransmissionCost.__init__(self, name, scenario=scenario)
        self.name = name
        if self.name is not None:
           self.init_from_db(name, scenario)
        TransmissionSuper.__init__(self)
        self.scenario = scenario

        if self.values.sum().sum()>0:
            self.convert()
            self.levelize_costs()

    def convert(self):
        """
        convert raw_values to model currency and capacity (energy_unit/time_step)
        """
        self.values = UnitConverter.currency_convert(self.values, self.currency, self.currency_year)
        model_energy_unit = cfg.calculation_energy_unit
        model_time_step = cfg.getParam('time_step', section='TIME')
        if self.time_unit is not None:
            # if a cost has a time_unit, then the unit is energy and must be converted to capacity
            self.values = UnitConverter.unit_convert(self.values,
                                            unit_from_den=self.self.capacity_or_energy_unit,
                                            unit_from_num=self.time_unit, unit_to_den=model_energy_unit,
                                            unit_to_num=model_time_step)
        else:
            self.values = UnitConverter.unit_convert(self.values, unit_from_den=self.capacity_or_energy_unit+"_"+model_time_step,
                                                unit_to_den=model_energy_unit)

    def levelize_costs(self):
        inflation = cfg.getParamAsFloat('inflation_rate', section='UNITS')
        rate = self.cost_of_capital - inflation
        self.values_level = - np.pmt(rate, self.lifetime, 1, 0, 'end') * self.values


class DispatchTransmission():
    def __init__(self, name, scenario):
        self.name = name
        self.constraints = DispatchTransmissionConstraint(name, scenario)
        self.hurdles = DispatchTransmissionHurdleRate(name, scenario)
        self.losses = DispatchTransmissionLosses(name, scenario)
        self.cost = DispatchTransmissionCost(name,scenario)
        self.list_transmission_lines = self.get_transmission_lines()

    def get_transmission_lines(self):
        transmission_lines = []
        for t_from in GeoMapper.dispatch_geographies:
            for t_to in GeoMapper.dispatch_geographies:
                if t_from==t_to:
                    continue
                transmission_lines.append(str((t_from, t_to)))
        return transmission_lines