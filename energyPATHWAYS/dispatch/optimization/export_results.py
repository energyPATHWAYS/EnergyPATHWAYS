"""
Currently exports basic results to CSVs.
"""

import os
import csv


def export_allocation_results(instance, results_directory):

    periods_set = getattr(instance, "PERIODS")
    regions_set = getattr(instance, "REGIONS")
    resources_set = getattr(instance, "RESOURCES")

    load_writer = csv.writer(open(os.path.join(results_directory, "alloc_loads.csv"), "wb"))
    load_writer.writerow(["region", "period", "avg_net_load", "period_net_load"])

    for r in regions_set:
        for p in periods_set:
            load_writer.writerow([r, p, instance.average_net_load[r], instance.period_net_load[r, p]])

    net_charge_writer = csv.writer(open(os.path.join(results_directory, "alloc_results_state_of_charge.csv"), "wb"))
    net_charge_writer.writerow(["resource", "period", "region", "discharge", "charge", "net_power", "start_state_of_charge",
                                "end_state_of_charge"])
    start_soc = dict()
    end_soc = dict()

    for r in resources_set:
        for p in periods_set:
            net_charge_writer.writerow([r, p, instance.region[r],
                                        instance.Discharge[r, p].value, instance.Charge[r, p].value,
                                        (instance.Discharge[r, p].value-instance.Charge[r, p].value),
                                        instance.Energy_in_Storage[r, p].value,
                                        (instance.Energy_in_Storage[r, p].value -
                                         (instance.Discharge[r, p].value-instance.Charge[r, p].value)
                                         )]
                                       )

            nested_dict(start_soc, [p, r], instance.Energy_in_Storage[r, p].value)
            nested_dict(end_soc, [p, r], instance.Energy_in_Storage[r, p].value - (instance.Discharge[r, p].value-instance.Charge[r, p].value))

    state_of_charge = [start_soc, end_soc]
    return state_of_charge


def export_dispatch_results(instance, results_directory, period):
    """

    :param instance:
    :param results_directory:
    :param period:
    :return:
    """
    timepoints_set = getattr(instance, "TIMEPOINTS")
    regions_set = getattr(instance, "REGIONS")
    resources_set = getattr(instance, "RESOURCES")
    storage_resources_set = getattr(instance, "STORAGE_RESOURCES")
    large_storage_resources_set = getattr(instance, "VERY_LARGE_STORAGE_RESOURCES")
    transmission_lines_set = getattr(instance, "TRANSMISSION_LINES")

    operations_writer = csv.writer(open(os.path.join(results_directory, str(period)+"_dispatch_results.csv"), "wb"))
    operations_writer.writerow(["timepoint", "resource", "technology", "region", "power", "charging", "state_of_charge",
                                "goal_state_of_charge_start", "goal_state_of_charge_end"])

    for t in timepoints_set:
        for r in resources_set:
            power = instance.Provide_Power[r, t].value
            if r in storage_resources_set:
                charge = instance.Charge[r, t].value
                state_of_charge = instance.Energy_in_Storage[r, t].value

                if r in large_storage_resources_set:
                    state_of_charge_start = instance.start_state_of_charge[r]
                    state_of_charge_end = instance.end_state_of_charge[r]
                else:
                    state_of_charge_start = None
                    state_of_charge_end = None
            else:
                charge = None
                state_of_charge = None
                state_of_charge_start = None
                state_of_charge_end = None
            operations_writer.writerow([t, r, instance.technology[r], instance.region[r], power, charge, state_of_charge,
                                        state_of_charge_start, state_of_charge_end])

    load_writer = csv.writer(open(os.path.join(results_directory, str(period)+"_load_results.csv"), "wb"))
    load_writer.writerow(["timepoint", "region", "net_static_load", "flex_load", "ev_load", "bulk_renewables",
                          "curtailment", "unserved_energy", "cumulative_flex_load_min", "cumulative_flex_load_max",
                          "cumulative_ev_load_min", "cumulative_ev_load_max"])

    for t in timepoints_set:
        for r in regions_set:
            load_writer.writerow([t, r, instance.net_distributed_load[r, t],
                                  instance.Flexible_Load[r, t].value, instance.EV_Load[r, t].value,
                                  instance.bulk_renewables[r, t],
                                  instance.Curtailment[r, t].value, instance.Unserved_Energy[r, t].value,
                                  instance.min_cumulative_flex_load[r, t], instance.max_cumulative_flex_load[r, t],
                                  instance.min_cumulative_ev_load[r, t], instance.max_cumulative_ev_load[r, t]])

    transmission_writer = csv.writer(open(os.path.join(results_directory, str(period)+"_transmission_results.csv"), "wb"))
    transmission_writer.writerow(["timepoint", "line", "from", "to", "flow"])
    for tmp in timepoints_set:
        for tl in transmission_lines_set:
            transmission_writer.writerow([tmp, tl, instance.transmission_from[tl], instance.transmission_to[tl],
                                          instance.Transmit_Power[tl, tmp].value])


def nested_dict(dic, keys, value):
    """
    Create a nested dictionary.
    :param dic:
    :param keys:
    :param value:
    :return:
    """
    for key in keys[:-1]:
        dic = dic.setdefault(key, {})
    dic[keys[-1]] = value