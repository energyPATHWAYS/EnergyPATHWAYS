"""
Input classes for allocation optimization and dispatch optimization.
"""


import csv
import os


class AllocationInputs(object):
    """
    Inputs to the allocation optimization. Currently defined relative to an inputs directory, but this will have to
    change.

    The following elements will be needed:
    self.periods
    self.regions
    self.alloc_resources
    self.alloc_region
    self.alloc_power_capacity
    self.alloc_energy_capacity
    self.average_net_load
    self.period_net_load
    self.upward_imbalance_penalty
    self.downward_imbalance_penalty

    """
    def __init__(self, inputs_directory):

        # List of "periods" for allocation of large pumped storage across year and for each dispatch optimization
        self.periods = list()
        with open(os.path.join(inputs_directory, "periods.csv"), "Ur") as periods_file:
            periods_reader = csv.reader(periods_file)
            periods_reader.next()
            for row in periods_reader:
                self.periods.append(int(row[0]))

        # List of regions
        self.regions = list()
        with open(os.path.join(inputs_directory, "regions.csv"), "Ur") as regions_file:
            regions_reader = csv.reader(regions_file)
            regions_reader.next()
            for row in regions_reader:
                self.regions.append(str(row[0]))

        # ### Inputs for year to period allocation ### #

        # Average load across all periods
        # Data structure: dictionary with regions as keys
        self.average_net_load = dict()
        with open(os.path.join(inputs_directory, "alloc_average_net_load.csv"), "Ur") as avg_net_load_file:
            average_net_load_reader = csv.reader(avg_net_load_file)
            average_net_load_reader.next()
            for row in average_net_load_reader:
                self.average_net_load[str(row[0])] = float(row[1])

        # Total load in each period
        # Dictionary with two indices: period and region
        self.period_net_load = dict()
        with open(os.path.join(inputs_directory, "alloc_period_net_load.csv"), "Ur") as period_net_load_file:
            period_total_net_load_reader = csv.reader(period_net_load_file)
            period_total_net_load_reader.next()
            for row in period_total_net_load_reader:
                self.period_net_load[str(row[0]), int(row[1])] = float(row[2])

        # List of resources
        self.alloc_resources = list()

        # Resource params: region, technology, power capacity, energy capacity
        # Data structrue: dictionaries with the resource names as keys
        self.alloc_region = dict()
        self.alloc_technology = dict()
        self.alloc_power_capacity = dict()
        self.alloc_energy_capacity = dict()
        with open(os.path.join(inputs_directory, "alloc_resources.csv"), "Ur") as alloc_resources_file:
            alloc_resources_reader = csv.reader(alloc_resources_file)
            alloc_resources_reader.next()
            for row in alloc_resources_reader:
                self.alloc_resources.append(str(row[0]))
                self.alloc_region[str(row[0])] = str(row[1])
                self.alloc_technology[str(row[0])] = str(row[2])
                self.alloc_power_capacity[str(row[0])] = float(row[3])
                self.alloc_energy_capacity[str(row[0])] = float(row[4])

        # Penalties; these are all single values
        # TODO: define outside of class
        self.upward_imbalance_penalty = 1000.0
        self.downward_imbalance_penalty = 100.0


class DispatchInputs(object):
    """
    Inputs to the dispatch optimization. Currently defined relative to an inputs directory, but this will have to
    change. Most inputs can vary by period, so this class defines a number of dictionaries with periods as keys
    (these usually start with 'period_'), which in turn contain the correct input data structure for each period
    optimization. Don't pay too much attention to how the data are currently loaded; you can just use the main function
    at the end to print any of the elements of this class to see what the data inputs will need to look like.

    These are the elements of this class that will be needed at the end:

    self.period_timepoints
    self.period_flex_load_timepoints
    self.period_ev_load_timepoints
    self.regions
    self.storage_technologies
    self.generation_technologies
    self.large_storage
    self.charging_efficiency
    self.discharging_efficiency
    self.variable_cost
    self.period_resources
    self.period_technology
    self.period_region
    self.period_distributed
    self.period_capacity
    self.period_duration
    self.net_distributed_load
    self.min_cumulative_flex_load
    self.max_cumulative_flex_load
    self.min_cumulative_ev_load
    self.max_cumulative_ev_load
    self.bulk_renewables
    self.period_max_flex_load
    self.period_max_ev_load
    self.transmission_lines
    self.transmission_from
    self.transmission_to
    self.transmission_capacity
    self.dist_net_load_threshold
    self.bulk_net_load_threshold
    self.t_and_d_losses
    self.curtailment_cost
    self.unserved_energy_cost
    self.dist_net_load_penalty
    self.bulk_net_load_penalty

    """

    def __init__(self, inputs_directory):

        # List of "periods" to optimize (can be optimized in parallel)
        self.periods = list()
        with open(os.path.join(inputs_directory, "periods.csv"), "Ur") as periods_file:
            periods_reader = csv.reader(periods_file)
            periods_reader.next()
            for row in periods_reader:
                self.periods.append(int(row[0]))

        # List of regions
        # Also importing the penalty thresholds for the distribution and bulk systems
        self.regions = list()
        self.dist_net_load_threshold = dict()
        self.bulk_net_load_threshold = dict()
        with open(os.path.join(inputs_directory, "regions.csv"), "Ur") as regions_file:
            regions_reader = csv.reader(regions_file)
            regions_reader.next()
            for row in regions_reader:
                self.regions.append(str(row[0]))
                self.dist_net_load_threshold[str(row[0])] = float(row[1])
                self.bulk_net_load_threshold[str(row[0])] = float(row[2])

        # Dictionary with period as key and the list of timepoints for each period as values
        self.period_timepoints = dict()
        # List of timepoints in each period (e.g. 1-24 for days, 1-168 for weeks, etc.)
        self.timepoints = list()
        # Dictionary with the order in which the cumulative flexible load constraint is enforced,
        # e.g. if starting it on timepoint 7, flex_load_timepoint 1 is assigned to timepoint 7
        # {7: 1, 8: 2, 9: 3 ...}
        self.flex_load_timepoints = dict()
        self.ev_load_timepoints = dict()
        self.period_flex_load_timepoints = dict()
        self.period_ev_load_timepoints = dict()
        with open(os.path.join(inputs_directory, "timepoints.csv"), "Ur") as timepoints_file:
            timepoints_reader = csv.reader(timepoints_file)
            timepoints_reader.next()
            for row in timepoints_reader:
                self.timepoints.append(int(row[1]))
                self.flex_load_timepoints[int(row[1])] = int(row[2])
                self.ev_load_timepoints[int(row[1])] = int(row[3])
                if int(row[1]) == 168:
                    self.period_timepoints[int(row[0])] = self.timepoints
                    self.timepoints = list()
                    self.period_flex_load_timepoints[int(row[0])] = self.flex_load_timepoints
                    self.flex_load_timepoints = dict()
                    self.period_ev_load_timepoints[int(row[0])] = self.ev_load_timepoints
                    self.ev_load_timepoints = dict()

        # List of storage technologies
        self.storage_technologies = list()
        # Dictionaries with technology params (storage technologies as keys): large-storage boolean flag,
        # charging efficiency, discharging efficiency
        self.large_storage = dict()
        self.charging_efficiency = dict()
        self.discharging_efficiency = dict()
        with open(os.path.join(inputs_directory, "storage_technologies.csv"), "Ur") as storage_technologies_file:
            storage_technologies_reader = csv.reader(storage_technologies_file)
            storage_technologies_reader.next()
            for row in storage_technologies_reader:
                self.storage_technologies.append(str(row[0]))
                self.large_storage[str(row[0])] = int(row[1])
                self.charging_efficiency[str(row[0])] = float(row[2])
                self.discharging_efficiency[str(row[0])] = float(row[3])

        # List of generation technologies; this doesn't vary by period, so no period dictionary needed
        self.generation_technologies = list()
        # Dictionary of variable cost by generation technologies (generation technologies as keys)
        self.variable_cost = dict()
        with open(os.path.join(inputs_directory, "generation_technologies.csv"), "Ur") as generation_technologies_file:
            generation_technologies_reader = csv.reader(generation_technologies_file)
            generation_technologies_reader.next()
            for row in generation_technologies_reader:
                self.generation_technologies.append(str(row[0]))
                self.variable_cost[str(row[0])] = float(row[1])

        # Dictionary with periods as keys, list of resources in each period as values
        self.period_resources = dict()
        # List of resources to populate values in period_resources dictionary
        self.resources = list()

        # Dictionaries by period, which in turn contain dictionaries by resource with the following parameters:
        # region, technology, a boolean for distributed resources, and capacity
        self.period_region = dict()
        self.region = dict()
        self.period_technology = dict()
        self.technology = dict()
        self.period_distributed = dict()
        self.distributed = dict()
        self.period_capacity = dict()
        self.capacity = dict()

        # Dictionary with duration for storage resources only
        self.period_duration = dict()
        self.duration = dict()
        with open(os.path.join(inputs_directory, "resources.csv"), "Ur") as resources_file:
            resources_reader = csv.reader(resources_file)
            resources_reader.next()
            last_period = 1
            for row in resources_reader:
                if int(row[0]) == last_period:
                    self.resources.append(str(row[1]))
                    self.region[str(row[1])] = str(row[2])
                    self.technology[str(row[1])] = str(row[3])
                    self.distributed[str(row[1])] = int(row[4])
                    if row[5] == "":
                        pass
                    else:
                        self.capacity[str(row[1])] = float(row[5])
                    if row[6] == "":
                        pass
                    else:
                        self.duration[str(row[1])] = float(row[6])
                else:
                    # Assign to period dictionary
                    self.period_resources[last_period] = self.resources
                    self.period_region[last_period] = self.region
                    self.period_technology[last_period] = self.technology
                    self.period_distributed[last_period] = self.distributed
                    self.period_capacity[last_period] = self.capacity
                    self.period_duration[last_period] = self.duration

                    # Clean up
                    self.resources = list()
                    self.region = dict()
                    self.technology = dict()
                    self.distributed = dict()
                    self.capacity = dict()
                    self.duration = dict()

                    # Correct last row
                    last_period = int(row[0])

                    # Start over
                    self.resources.append(str(row[1]))
                    self.region[str(row[1])] = str(row[2])
                    self.technology[str(row[1])] = str(row[3])
                    self.distributed[str(row[1])] = int(row[4])
                    if row[5] == "":
                        pass
                    else:
                        self.capacity[str(row[1])] = float(row[5])
                    if row[6] == "":
                        pass
                    else:
                        self.duration[str(row[1])] = float(row[6])

        # List of transmission lines
        self.transmission_lines = list()
        # Dictionaries with transmission lines as keys; values are:
        # Region where transmission line starts
        self.transmission_from = dict()
        # Region where transmission line ends
        self.transmission_to = dict()
        # Transmission capacity
        self.transmission_capacity = dict()
        with open(os.path.join(inputs_directory, "transmission.csv"), "Ur") as transmission_file:
            transmission_reader = csv.reader(transmission_file)
            transmission_reader.next()
            for row in transmission_reader:
                self.transmission_lines.append(str(row[0]))
                self.transmission_from[str(row[0])] = str(row[1])
                self.transmission_to[str(row[0])] = str(row[2])
                self.transmission_capacity[str(row[0])] = int(row[3])

        # Loads
        # Dictionary with period as keys, containing dictionary with timepoints as keys and load as values
        self.period_net_distributed_load = dict()
        self.net_distributed_load = dict()
        # Same as above but for minimum cumulative flexible load,
        self.period_min_cum_flex_load = dict()
        self.min_cumulative_flex_load = dict()
        # maximum cumulative net load,
        self.period_max_cum_flex_load = dict()
        self.max_cumulative_flex_load = dict()
        # minimum cumulative EV load,
        self.period_min_cum_ev_load = dict()
        self.min_cumulative_ev_load = dict()
        # maximum cumulative EV load,
        self.period_max_cum_ev_load = dict()
        self.max_cumulative_ev_load = dict()
        # renewable output.
        self.period_bulk_renewables = dict()
        self.bulk_renewables = dict()

        with open(os.path.join(inputs_directory, "net_load.csv"), "Ur") as net_load_file:
            net_load_reader = csv.reader(net_load_file)
            net_load_reader.next()
            region_num = 0
            for row in net_load_reader:
                self.period_net_distributed_load[row[1], int(row[2])] = float(row[3])
                self.period_min_cum_flex_load[row[1], int(row[2])] = float(row[4])
                self.period_max_cum_flex_load[row[1], int(row[2])] = float(row[5])
                self.period_min_cum_ev_load[row[1], int(row[2])] = float(row[6])
                self.period_max_cum_ev_load[row[1], int(row[2])] = float(row[7])
                self.period_bulk_renewables[row[1], int(row[2])] = float(row[8])
                if int(row[2]) == 168:  # TODO: remove hardcoding; this is super ugly, but works for testing purposes
                    region_num += 1
                    if region_num == 3:
                        self.net_distributed_load[int(row[0])] = self.period_net_distributed_load
                        self.period_net_distributed_load = dict()
                        self.min_cumulative_flex_load[int(row[0])] = self.period_min_cum_flex_load
                        self.period_min_cum_flex_load = dict()
                        self.max_cumulative_flex_load[int(row[0])] = self.period_max_cum_flex_load
                        self.period_max_cum_flex_load = dict()
                        self.min_cumulative_ev_load[int(row[0])] = self.period_min_cum_ev_load
                        self.period_min_cum_ev_load = dict()
                        self.max_cumulative_ev_load[int(row[0])] = self.period_max_cum_ev_load
                        self.period_max_cum_ev_load = dict()
                        self.bulk_renewables[int(row[0])] = self.period_bulk_renewables
                        self.period_bulk_renewables = dict()
                        region_num = 0
                    else:
                        pass
                else:
                    pass

        # Dictionary with period as key containing a dictionary with regions as keys and maximum flexible load as values
        self.period_max_flex_load = dict()
        self.max_flex_load = dict()
        with open(os.path.join(inputs_directory, "max_flex_load.csv"), "Ur") as max_flex_load_file:
            max_flex_load_reader = csv.reader(max_flex_load_file)
            max_flex_load_reader.next()
            last_period = 1
            for row in max_flex_load_reader:
                if int(row[0]) == last_period:
                    self.max_flex_load[str(row[1])] = float(row[2])
                else:
                    self.period_max_flex_load[int(last_period)] = self.max_flex_load
                    self.max_flex_load = dict()
                    last_period = int(row[0])
                    self.max_flex_load[str(row[1])] = float(row[2])

        # Dictionary with period as key containing a dictionary with regions as keys and maximum EV load as values
        self.max_ev_load = dict()
        self.period_max_ev_load = dict()
        with open(os.path.join(inputs_directory, "max_ev_load.csv"), "Ur") as max_ev_load_file:
            max_ev_load_reader = csv.reader(max_ev_load_file)
            max_ev_load_reader.next()
            last_period = 1
            for row in max_ev_load_reader:
                if int(row[0]) == last_period:
                    self.max_ev_load[str(row[1])] = float(row[2])
                else:
                    self.period_max_ev_load[int(last_period)] = self.max_ev_load
                    self.max_ev_load = dict()
                    last_period = int(row[0])
                    self.max_ev_load[str(row[1])] = float(row[2])

        # These are all single values and inelegantly instantiated inside the class here because it was easy
        # TODO: define outside of this class
        self.t_and_d_losses = 0
        self.curtailment_cost = 10**2
        self.unserved_energy_cost = 10**5
        self.dist_net_load_penalty = 1.0
        self.bulk_net_load_penalty = 1.0


def dispatch_inputs_init(inputs_directory):
    dispatch_inputs = DispatchInputs(inputs_directory)
    return dispatch_inputs


def alloc_inputs_init(inputs_directory):
    alloc_inputs = AllocationInputs(inputs_directory)
    return alloc_inputs


if __name__ == "__main__":
    _dispatch_inputs = dispatch_inputs_init(os.path.join(os.getcwd(), "inputs_weeks"))
    # print _dispatch_inputs.timepoints
    # print _dispatch_inputs.technologies
    # print _dispatch_inputs.storage
    # print _dispatch_inputs.net_load
    # print _dispatch_inputs.period_net_load[52]
    # print _dispatch_inputs.regions
    # with open("test.csv", "wb") as f:
    #     w = csv.DictWriter(f, _dispatch_inputs.net_load.keys())
    #     w.writeheader()
    #     w.writerow(_dispatch_inputs.net_load)
    # print _dispatch_inputs.storage_technologies
    # print _dispatch_inputs.generation_technologies
    # print _dispatch_inputs.start_state_of_charge
    # print _dispatch_inputs.period_max_flex_load
