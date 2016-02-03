# -*- coding: utf-8 -*-
"""
Created on Wed Sep 02 11:19:36 2015

@author: Ben
"""
import numpy as np
from config import cfgfile
import pandas as pd

vintage_start, vintage_stop, vintage_step = 1950, 2050, 1
vintages = np.arange(vintage_start, vintage_stop + 1, vintage_step)

year_start, year_stop, year_step = 1950, 2050, 1
years = np.asarray(cfgfile.get('case', 'years'))
vintages = np.asarray(cfgfile.get('case', 'vintages'))


# vintage_age creates an array of numbers for each vintage v that represents age in year y.
def vintage_age(years, vintages):
    ages = np.zeros((len(years), len(vintages)))


# vintage_exist creates a binary array that is 1 if year is greater than vintage (i.e. vintage v exists in year y)
def vintage_exist(years, vintages):
    # Built in function to create a lower triangular distribution, k gives the shift from the diagonal
    age = vintage_age(years, vintages)
    return np.triu(age, k=(min(years) - min(vintages)))


test = np.triu(len(years), len(vintages), k=min(years) - min(vintages))


def decay_growth_df(growth_type, growth_rate):
    vintages, years = np.asarray(cfgfile.get('case', 'vintages')), np.asarray(cfgfile.get('case', 'years'))
    ages = np.zeros((len(years), len(vintages)))
    for i, year in enumerate(years):
        ages[i] = vintages - year
    if growth_type == 'linear':
        fill = 1 + (growth_rate * ages)
        fill = np.triu(fill, k=(min(years) - min(vintages)))
    elif growth_type == 'exponential':
        fill = (1 + growth_rate) ** ages
        fill = np.triu(fill, k=(min(years) - min(vintages)))
    return pd.DataFrame(fill, index=vintages, columns=years)


if is_stock_dependent == False and is_service_dependent == False:
    if stock == 'equipment':
        if service == 'service':
            "project stock and service demand"
        elif service == 'energy':
            "project stock and divide service demand by stock efficiency"
    elif stock == 'capacity factor':
        if service == service:
            "project service demand and divide by time unit and then by capacity_factor"
        if service == energy:
            """
            project stock with a unit of 1 in order to get normalized efficiency, use the efficiency value to remove efficiency from service demand,
            project service demand, project stock
            """
    elif stock == 'service demand':
        if service == service:
            "project service, use service demand as total stock"
        if service == energy:
            """
              project stock with original service demand (energy terms), use the efficiency value to remove efficiency from service demand,
              project service demand, use service demand as stock
            """
if is_stock_dependent == True and is_service_dependent == False:
    if stock == 'equipment':
        if service == 'service':
            "project stock, use stock as a driver for service demand"
        elif service == 'energy':
            "project stock and divide service demand by stock efficiency, use stock as a driver for service demand"
    elif stock == 'capacity factor':
        if service == service:
            False
        if service == energy:
            False
    elif stock == 'service demand':
        if service == service:
            False
        if service == energy:
            False

if is_stock_dependent == False and is_service_dependent == True:
    if stock == 'equipment':
        if service == 'service':
            "project service demand and use it as a driver to project stock"
        elif service == 'energy':
            """project stock without using service demand as a driver. Demand service demand by efficiency. 
            Project service demand. Project stock using new service demand. 
            """
    elif stock == 'capacity factor':
        if service == service:
            "project service demand and divide by time unit and then by capacity_factor"
        if service == energy:
            """
            project stock with original service demand (energy terms), use the efficiency value to remove efficiency from service demand,
                  project service demand, stock = service demand divided by time unit and then capacity factor
            """
    elif stock == 'service demand':
        if service == service:
            "project service, use service demand as total stock"
        if service == energy:
            """
              project stock with a unit of 1 in order to get normalized efficiency, use the efficiency value to remove efficiency from service demand,
              project service demand, use service demand as stock
            """
    