# -*- coding: utf-8 -*-
"""
Created on Mon Mar 07 14:33:35 2016

@author: Ben
"""

# -*- coding: utf-8 -*-
"""
Created on Fri Mar 04 10:23:57 2016

@author: Ben
"""
import types
import copy
import numpy as np
from collections import defaultdict
from energyPATHWAYS import util
import pandas as pd
import os 
import pickle
from energyPATHWAYS import config




directory = os.getcwd()

def year_to_period_allocation_formulation(dispatch):
    """
    Formulation of year to period allocation problem.
    If dispatch contains data, the data are initialized with the formulation of the model (concrete model).
    Model is defined as "abstract," however, so data can also be loaded when create_instance() is called instead.
    :param dispatch:
    :return:
    """

    allocation_model = AbstractModel()

    allocation_model.PERIODS = Set(within=NonNegativeIntegers, ordered=True, initialize=dispatch.periods)

    def first_period_init(model):
        """
        Assumes periods are ordered
        :param model:
        :return:
        """
        return min(model.PERIODS)

    allocation_model.first_period = Param(initialize=first_period_init)

    def last_period_init(model):
        """
        Assumes periods are ordered
        :param model:
        :return:
        """
        return max(model.PERIODS)

    allocation_model.last_period = Param(initialize=last_period_init)

    def previous_period_init(model):
        """
        Define a "previous period" for periodic boundary constraints
        The previous timepoint for the first timepoint is the last timepoint
        :param model:
        :return:
        """
        previous_periods = dict()
        for period in model.PERIODS:
            if period == model.first_period:
                previous_periods[period] = model.last_period
            else:
                previous_periods[period] = period - 1
        return previous_periods

    allocation_model.previous_period = Param(allocation_model.PERIODS, initialize=previous_period_init)

    allocation_model.REGIONS = Set(initialize=dispatch.regions)
    
    dispatch_model.STORAGE_TECHNOLOGIES =  Set(initialize=dispatch.storage_technologies)

    dispatch_model.VERY_LARGE_STORAGE_TECHNOLOGIES = SET(dispatch_model.STORAGE_TECHNOLOGIES, initialize=dispatch.large_storage,within=Binary)

    allocation_model.region = Param(allocation_model.VERY_LARGE_STORAGE_TECHNOLOGIES, initialize=dispatch.region)
    # TODO: careful with capacity means in the context of, say, a week instead of an hour
    allocation_model.power_capacity = Param(allocation_model.VERY_LARGE_STORAGE_TECHNOLOGIES,
                                            initialize=dispatch.capacity)
    allocation_model.energy_capacity = Param(allocation_model.VERY_LARGE_STORAGE_TECHNOLOGIES,
                                             initialize=dispatch.energy)

    allocation_model.average_net_load = Param(allocation_model.REGIONS, initialize=dispatch.average_net_load)
    allocation_model.period_net_load = Param(allocation_model.REGIONS, allocation_model.PERIODS,
                                             initialize=dispatch.period_net_load)

    allocation_model.upward_imbalance_penalty = Param(initialize=dispatch.upward_imbalance_penalty)
    allocation_model.downward_imbalance_penalty = Param(initialize=dispatch.downward_imbalance_penalty)

    # Resource variables
    allocation_model.Charge = Var(allocation_model.VERY_LARGE_STORAGE_TECHNOLOGIES, allocation_model.PERIODS,
                                  within=NonNegativeReals)
    allocation_model.Discharge = Var(allocation_model.VERY_LARGE_STORAGE_TECHNOLOGIES, allocation_model.PERIODS,
                                     within=NonNegativeReals)
    allocation_model.Energy_in_Storage = Var(allocation_model.VERY_LARGE_STORAGE_TECHNOLOGIES, allocation_model.PERIODS,
                                             within=NonNegativeReals)

    # System variables
    allocation_model.Upward_Imbalance = Var(allocation_model.REGIONS, allocation_model.PERIODS,
                                            within=NonNegativeReals)
    allocation_model.Downward_Imbalance = Var(allocation_model.REGIONS, allocation_model.PERIODS,
                                              within=NonNegativeReals)

    # Objective function
    def total_imbalance_penalty_rule(model):
        return sum((model.Upward_Imbalance[r, p] * model.upward_imbalance_penalty +
                    model.Downward_Imbalance[r, p] * model.downward_imbalance_penalty)
                   for r in model.REGIONS
                   for p in model.PERIODS)
    allocation_model.Total_Imbalance = Objective(rule=total_imbalance_penalty_rule, sense=minimize)

    # Constraints
    def power_balance_rule(model, region, period):

        discharge = sum(model.Discharge[technology, period] for technology in model.VERY_LARGE_STORAGE_TECHNOLOGIES
                        if model.region[resource] == region)
        charge = sum(model.Charge[technology, period] for technology in model.VERY_LARGE_STORAGE_TECHNOLOGIES
                     if model.region[resource] == region)

        return discharge + model.Upward_Imbalance[region, period] \
            == model.period_net_load[region, period] - model.average_net_load[region] \
            + charge + model.Downward_Imbalance[region, period]

    allocation_model.Power_Balance_Constraint = Constraint(allocation_model.REGIONS,
                                                           allocation_model.PERIODS,
                                                           rule=power_balance_rule)

    def storage_energy_tracking_rule(model, technology, period):
        """
        Set starting state of charge for each period.
        :param model:
        :param resource:
        :param period:
        :return:
        """
        return model.Energy_in_Storage[technology, period] \
            == model.Energy_in_Storage[technology, model.previous_period[period]] \
            - model.Discharge[technology, model.previous_period[period]] \
            + model.Charge[technology, model.previous_period[period]]

    allocation_model.Storage_Energy_Tracking_Constraint = Constraint(allocation_model.VERY_LARGE_STORAGE_TECHNOLOGIES,
                                                                     allocation_model.PERIODS,
                                                                     rule=storage_energy_tracking_rule)

    def storage_discharge_rule(model, technology, period):
        return model.Discharge[technology, period] <= model.power_capacity[technology]

    allocation_model.Storage_Discharge_Constraint = Constraint(allocation_model.VERY_LARGE_STORAGE_TECHNOLOGIES,
                                                               allocation_model.PERIODS,
                                                               rule=storage_discharge_rule)

    def storage_charge_rule(model, technology, period):
        return model.Charge[technology, period] <= model.power_capacity[technology]

    allocation_model.Storage_Charge_Constraint = Constraint(allocation_model.VERY_LARGE_STORAGE_TECHNOLOGIES,
                                                            allocation_model.PERIODS,
                                                            rule=storage_charge_rule)

    def storage_energy_rule(model, technology, period):
        return model.Energy_in_Storage[technology, period] <= model.energy_capacity[technology]

    allocation_model.Storage_Energy_Constraint = Constraint(allocation_model.VERY_LARGE_STORAGE_TECHNOLOGIES,
                                                            allocation_model.PERIODS,
                                                            rule=storage_energy_rule)

    # TODO: add charge and discharge efficiencies?

    return allocation_model