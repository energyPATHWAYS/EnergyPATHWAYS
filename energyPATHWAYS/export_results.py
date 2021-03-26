"""
Currently exports basic results to CSVs.
"""

import os
import csv
from energyPATHWAYS import util
from ast import literal_eval
import numpy as np

def export_allocation_results(instance, results_directory, write_to_file=False):

    periods_set = getattr(instance, "PERIODS")
    geographies_set = getattr(instance, "GEOGRAPHIES")
    tech_set = getattr(instance, "VERY_LARGE_STORAGE_TECHNOLOGIES")

    if write_to_file:
        load_writer = csv.writer(open(os.path.join(results_directory, "alloc_loads.csv"), "wb"))
        load_writer.writerow(["geography", "period", "avg_net_load", "period_net_load"])

        for g in geographies_set:
            for p in periods_set:
                load_writer.writerow([g, p, instance.average_net_load[g], instance.period_net_load[g, p]])

        net_charge_writer = csv.writer(open(os.path.join(results_directory, "alloc_results_state_of_charge.csv"), "wb"))
        net_charge_writer.writerow(["technology", "period", "geography", "discharge", "charge", "net_power", "start_state_of_charge",
                                "end_state_of_charge"])
    start_soc = dict()
    end_soc = dict()

    for t in tech_set:
        for p in periods_set:
            if write_to_file:
                net_charge_writer.writerow([t, p, instance.region[t],
                                        instance.Discharge[t, p].value, instance.Charge[t, p].value,
                                        (instance.Discharge[t, p].value-instance.Charge[t, p].value),
                                        instance.Energy_in_Storage[t, p].value,
                                        (instance.Energy_in_Storage[t, p].value -
                                         (instance.Discharge[t, p].value-instance.Charge[t, p].value)
                                         )]
                                       )

            nested_dict(start_soc, [p, t], instance.Energy_in_Storage[t, p].value)
            nested_dict(end_soc, [p, t], instance.Energy_in_Storage[t, p].value - (instance.Discharge[t, p].value-instance.Charge[t, p].value))

    state_of_charge = [start_soc, end_soc]
    return state_of_charge


#def export_storage_results(instance,period, dist_storage_df, bulk_storage_charge_df):
#    timepoints_set = getattr(instance, "TIMEPOINTS")
#    storage_tech_set = getattr(instance, "STORAGE_TECHNOLOGIES")
#    geographies_set = getattr(instance, "GEOGRAPHIES")
#    feeder_set = getattr(instance,"FEEDERS")
#    for geography in geographies_set:
#        for tech in storage_tech_set:
#            if instance.feeder[tech] == 0:
#                charge_indexer = util.level_specific_indexer(bulk_storage_df, [self.dispatch_geography, 'storage_technology', 'charge_discharge'], [geography, tech, 'charge'])
#                discharge_indexer = util.level_specific_indexer(bulk_storage_df, [self.dispatch_geography, 'storage_technology','charge_discharge'], [geography, tech, 'discharge']) 
#                for timepoint in self.period_timepoints[period]:                
#                    time_index = (period * self.opt_hours) + timepoint - 1 
#                    bulk_storage_df.loc[charge_indexer,:].iloc[time_index] = instance.Charge[t, timepoint] 
#                    bulk_storage_df.loc[discharge_indexer,:].iloc[time_index] = instance.Provide_Power[t, timepoint] 
#            else:
#                charge_indexer = util.level_specific_indexer(dist_storage_df, [self.dispatch_geography, 'storage_technology', 'charge_discharge','feeder'], [geography, tech, 'charge', feeder])
#                discharge_indexer = util.level_specific_indexer(dist_storage_df, [self.dispatch_geography, 'storage_technology','charge_discharge','feeder'], [geography, tech, 'discharge', feeder]) 
#                for timepoint in self.period_timepoints[period]:                
#                    time_index = (period * self.opt_hours) + timepoint - 1 
#                    dist_storage_df.loc[charge_indexer,:].iloc[time_index] = instance.Charge[t, timepoint] 
#                    dist_storage_df.loc[discharge_indexer,:].iloc[time_index] = instance.Provide_Power[t, timepoint] 
            
    

 


def export_dispatch_results(instance, results_directory, period):
    """

    :param instance:
    :param results_directory:
    :param period:
    :return:
    """
    timepoints_set = getattr(instance, "TIMEPOINTS")
    geographies_set = getattr(instance, "GEOGRAPHIES")
    tech_set = getattr(instance, "TECHNOLOGIES")
    storage_tech_set = getattr(instance, "STORAGE_TECHNOLOGIES")
    large_storage_tech_set = getattr(instance, "VERY_LARGE_STORAGE_TECHNOLOGIES")
    feeder_set = getattr(instance, "FEEDERS")
#    transmission_lines_set = getattr(instance, "TRANSMISSION_LINES")
    
    operations_writer = csv.writer(open(os.path.join(results_directory, str(period)+"_dispatch_results.csv"), "wb"))
    operations_writer.writerow(["timepoint",  "technology", "region", "power", "charging", "state_of_charge",
                            "goal_state_of_charge_start", "goal_state_of_charge_end"])

    for x in timepoints_set:
        for t in tech_set:
            power = instance.Provide_Power[t, x].value
            if t in storage_tech_set:
                charge = instance.Charge[t, x].value
                state_of_charge = instance.Energy_in_Storage[t, x].value
                if t in large_storage_tech_set:
                    state_of_charge_start = instance.start_state_of_charge[t]
                    state_of_charge_end = instance.end_state_of_charge[t]
                else:
                    state_of_charge_start = None
                    state_of_charge_end = None
            else:
                charge = None
                state_of_charge = None
                state_of_charge_start = None
                state_of_charge_end = None
            operations_writer.writerow([x, t, instance.geography[t], power, charge, state_of_charge,
                                    state_of_charge_start, state_of_charge_end])

    load_writer = csv.writer(open(os.path.join(results_directory, str(period)+"_load_results.csv"), "wb"))
    load_writer.writerow(["timepoint", "geography",  "feeder", "distribution_load", "flex_load"])

    for x in timepoints_set:
        for g in geographies_set:
            for f in feeder_set:
                    load_writer.writerow([x, g, f, instance.distribution_load[g, x, f],
                                      instance.Flexible_Load[g, x, f].value])

#    transmission_writer = csv.writer(open(os.path.join(results_directory, str(period)+"_transmission_results.csv"), "wb"))
#    transmission_writer.writerow(["timepoint", "line", "from", "to", "flow"])
#    for tmp in timepoints_set:
#        for tl in transmission_lines_set:
#            transmission_writer.writerow([tmp, tl, instance.transmission_from[tl], instance.transmission_to[tl],
#                                          instance.Transmit_Power[tl, tmp].value])
#
#




