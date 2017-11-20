
from pyomo.environ import *
import pdb

def ld_energy_formulation(dispatch):
    """
    Formulation of dispatch problem.
    If _inputs contains data, the data are initialized with the formulation of the model (concrete model).
    Model is defined as "abstract," however, so data can also be loaded when create_instance() is called instead.
    """

    def power_rule(model, technology, timepoint):
        """
        Storage cannot discharge at a higher rate than implied by its total installed power capacity.
        Charge and discharge rate limits are currently the same.
        """
        return model.min_capacity[technology,timepoint] <= model.Provide_Power[technology, timepoint] <= model.capacity[technology,timepoint]

    def ld_energy_rule(model, technology):
        return sum(model.Provide_Power[technology, t] for t in model.TIMEPOINTS) == model.annual_ld_energy[technology]

    def transmission_rule(model, line, timepoint):
        """
        Transmission line flow is limited by transmission capacity.
        """
        # if we make transmission capacity vary by hour, we just need to add timepoint to transmission capacity
        return model.Transmit_Power[line, timepoint] <= model.transmission_capacity[line]

    def net_transmit_power_by_geo_rule(model, geography, timepoint):
        # line is constructed as (from, to)
        # net transmit power = sum of all imports minus the sum of all exports
        return model.Net_Transmit_Power_by_Geo[geography, timepoint] == sum([model.Transmit_Power[str((g, geography)), timepoint] for g in model.GEOGRAPHIES if g!=geography]) - \
                                                                        sum([model.Transmit_Power[str((geography, g)), timepoint] / (1 - model.transmission_losses[str((geography, g))]) for g in model.GEOGRAPHIES if g!=geography])

    def upward_imbalance_penalty_rule(model, geography, timepoint):
        ld_dispatch = sum(model.Provide_Power[technology, timepoint] for technology in model.LD_TECHNOLOGIES if model.geography[technology]==geography)
        return model.Upward_Imbalance[geography, timepoint] >= model.bulk_net_load[geography, timepoint] - ld_dispatch - model.Net_Transmit_Power_by_Geo[geography, timepoint]

    def downward_imbalance_penalty_rule(model, geography, timepoint):
        ld_dispatch = sum(model.Provide_Power[technology, timepoint] for technology in model.LD_TECHNOLOGIES if model.geography[technology]==geography)
        return model.Downward_Imbalance[geography, timepoint] >= ld_dispatch + model.Net_Transmit_Power_by_Geo[geography, timepoint]  -model.bulk_net_load[geography, timepoint]

    def total_imbalance_penalty_rule(model):
        transmission_hurdles = sum(model.Transmit_Power[str((from_geo, to_geo)), t] * model.transmission_hurdle[str((from_geo, to_geo))]
                                                                                    for from_geo in model.GEOGRAPHIES
                                                                                    for to_geo in model.GEOGRAPHIES
                                                                                    for t in model.TIMEPOINTS if from_geo!=to_geo)
        return sum((model.Upward_Imbalance[g, t] * model.ld_imbalance_penalty +
                    model.Downward_Imbalance[g, t] * model.downward_imbalance_penalty
                    for g in model.GEOGRAPHIES for t in model.TIMEPOINTS)) + transmission_hurdles

    model = AbstractModel()

    ###########################
    # ### Sets and params ### #
    ###########################
    # ### Temporal structure ### #
    model.TIMEPOINTS = Set(within=NonNegativeIntegers, ordered=True, initialize=dispatch.hours)
    # ### Geographic structure ### #
    model.GEOGRAPHIES = Set(initialize=dispatch.dispatch_geographies)

    # ### Technologies ### #
    model.LD_TECHNOLOGIES = Set(initialize=dispatch.ld_technologies)
    # Only "generation" technologys have variable costs; storage does not
    model.geography = Param(model.LD_TECHNOLOGIES, within=model.GEOGRAPHIES, initialize=dispatch.ld_geography)
    model.min_capacity = Param(model.LD_TECHNOLOGIES, model.TIMEPOINTS, initialize=dispatch.ld_min_capacity)
    model.capacity = Param(model.LD_TECHNOLOGIES,model.TIMEPOINTS, initialize=dispatch.ld_capacity)
    model.annual_ld_energy = Param(model.LD_TECHNOLOGIES, initialize = dispatch.annual_ld_energy)

    # ### System ### #
    # Load - this should contain the impact of must run generation
    model.bulk_net_load = Param(model.GEOGRAPHIES, model.TIMEPOINTS, within=Reals, initialize=dispatch.ld_bulk_net_load)

    model.TRANSMISSION_LINES = Set(initialize=dispatch.transmission.list_transmission_lines)
    model.transmission_capacity = Param(model.TRANSMISSION_LINES, initialize=dispatch.transmission.constraints.get_values_as_dict(dispatch.year))
    model.transmission_hurdle = Param(model.TRANSMISSION_LINES, initialize=dispatch.transmission.hurdles.get_values_as_dict(dispatch.year))
    model.transmission_losses = Param(model.TRANSMISSION_LINES, initialize=dispatch.transmission.losses.get_values_as_dict(dispatch.year))

    model.ld_imbalance_penalty = Param(initialize=dispatch.ld_imbalance_penalty, within=NonNegativeReals)
    model.downward_imbalance_penalty = Param(initialize=dispatch.downward_imbalance_penalty, within=NonNegativeReals)

    # System variables
    #####################
    # ### Variables ### #
    #####################
    # Projects
    model.Provide_Power = Var(model.LD_TECHNOLOGIES, model.TIMEPOINTS, within=Reals)
    model.Upward_Imbalance = Var(model.GEOGRAPHIES, model.TIMEPOINTS, within=NonNegativeReals)
    model.Downward_Imbalance = Var(model.GEOGRAPHIES, model.TIMEPOINTS, within=NonNegativeReals)

    # Transmission
    model.Transmit_Power = Var(model.TRANSMISSION_LINES, model.TIMEPOINTS, within=NonNegativeReals)
    model.Net_Transmit_Power_by_Geo = Var(model.GEOGRAPHIES, model.TIMEPOINTS, within=Reals)

    ##############################
    # ### Objective function ### #
    ##############################
    model.Total_Imbalance = Objective(rule=total_imbalance_penalty_rule, sense=minimize)

    #######################
    # ### Constraints ### #
    #######################

    # ### Project constraints ### #
    model.Power_Constraint = Constraint(model.LD_TECHNOLOGIES, model.TIMEPOINTS, rule=power_rule)
    model.Upward_Imbalance_Constraint = Constraint(model.GEOGRAPHIES, model.TIMEPOINTS, rule=upward_imbalance_penalty_rule)
    model.Downward_Imbalance_Constraint = Constraint(model.GEOGRAPHIES, model.TIMEPOINTS, rule=downward_imbalance_penalty_rule)
    #ld_energy
    model.LD_Energy_Constraint = Constraint(model.LD_TECHNOLOGIES, rule=ld_energy_rule)
    # Transmission
    model.Transmission_Constraint = Constraint(model.TRANSMISSION_LINES, model.TIMEPOINTS, rule=transmission_rule)
    model.Net_Transmit_Power_by_Geo_Constraint = Constraint(model.GEOGRAPHIES, model.TIMEPOINTS, rule=net_transmit_power_by_geo_rule)

    return model




def ld_storage_formulation(dispatch):
    """
    Formulation of year to period allocation problem.
    If dispatch contains data, the data are initialized with the formulation of the model (concrete model).
    Model is defined as "abstract," however, so data can also be loaded when create_instance() is called instead.
    :param dispatch:
    :return:
    """

    def first_period_init(model):
        """
        Assumes periods are ordered
        :param model:
        :return:
        """
        return min(model.PERIODS)

    def last_period_init(model):
        """
        Assumes periods are ordered
        :param model:
        :return:
        """
        return max(model.PERIODS)

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

    def transmission_rule_alloc(model, line, period):
        """
        Transmission line flow is limited by transmission capacity.
        """
        # if we make transmission capacity vary by hour, we just need to add timepoint to transmission capacity
        return model.Transmit_Energy[line,period] <= model.transmission_energy[line,period]

    def net_transmit_energy_by_geo_rule(model, geography, timepoint):
        # line is constructed as (from, to)
        # net transmit power = sum of all imports minus the sum of all exports
        return model.Net_Transmit_Energy_by_Geo[geography, timepoint] == sum([model.Transmit_Energy[str((g, geography)), timepoint] for g in model.GEOGRAPHIES if g!=geography]) - \
                                                                        sum([model.Transmit_Energy[str((geography, g)), timepoint] / (1 - model.transmission_losses[str((geography, g))]) for g in model.GEOGRAPHIES if g!=geography])

    # Objective function
    def total_imbalance_penalty_rule(model):
        return sum((model.Upward_Imbalance[g, p] * model.upward_imbalance_penalty +
                    model.Downward_Imbalance[g, p] * model.downward_imbalance_penalty
                    for g in model.GEOGRAPHIES
                   for p in model.PERIODS))

    def upward_imbalance_penalty_rule(model, geography, period):
        discharge = sum(model.Discharge[technology, period] for technology in model.VERY_LARGE_STORAGE_TECHNOLOGIES
                        if model.geography[technology] == geography)
        charge = sum(model.Charge[technology, period] for technology in model.VERY_LARGE_STORAGE_TECHNOLOGIES
                     if model.geography[technology] == geography)
        return model.Upward_Imbalance[geography, period]>= model.period_net_load[geography, period] - discharge - model.Net_Transmit_Energy_by_Geo[geography, period] + charge

    def downward_imbalance_penalty_rule(model, geography, period):
        discharge = sum(model.Discharge[technology, period] for technology in model.VERY_LARGE_STORAGE_TECHNOLOGIES
                        if model.geography[technology] == geography)
        charge = sum(model.Charge[technology, period] for technology in model.VERY_LARGE_STORAGE_TECHNOLOGIES
                     if model.geography[technology] == geography)

        return model.Downward_Imbalance[geography, period]>= discharge + model.Net_Transmit_Energy_by_Geo[geography, period] - charge -model.period_net_load[geography, period]


    def storage_energy_tracking_rule(model, technology, period):
        """
        Set starting state of charge for each period.
        """
        return model.Energy_in_Storage[technology, period] \
            == model.Energy_in_Storage[technology, model.previous_period[period]] \
            - model.Discharge[technology, model.previous_period[period]] \
            + model.Charge[technology, model.previous_period[period]]

    def storage_discharge_rule(model, technology, period):
        return model.Discharge[technology, period] <= model.power_capacity[technology]/model.discharging_efficiency[technology]

    def storage_charge_rule(model, technology, period):
        return model.Charge[technology, period] <= model.power_capacity[technology] * model.charging_efficiency[technology]

    def storage_energy_rule(model, technology, period):
        return model.Energy_in_Storage[technology, period] <= model.energy_capacity[technology]

    model = AbstractModel()

    model.PERIODS = Set(within=NonNegativeIntegers, ordered=True, initialize=dispatch.periods)
    model.last_period = Param(initialize=last_period_init)
    model.first_period = Param(initialize=first_period_init)
    model.previous_period = Param(model.PERIODS, initialize=previous_period_init)
    model.GEOGRAPHIES = Set(initialize=dispatch.dispatch_geographies)
    model.TRANSMISSION_LINES = Set(initialize=dispatch.transmission.list_transmission_lines)
    model.VERY_LARGE_STORAGE_TECHNOLOGIES = Set(initialize =dispatch.alloc_technologies)
    model.geography = Param(model.VERY_LARGE_STORAGE_TECHNOLOGIES , initialize=dispatch.alloc_geography) # why do we need this???

    # TODO: careful with capacity means in the context of, say, a week instead of an hour
    model.power_capacity = Param(model.VERY_LARGE_STORAGE_TECHNOLOGIES, initialize=dispatch.alloc_capacity)
    model.energy_capacity = Param(model.VERY_LARGE_STORAGE_TECHNOLOGIES, initialize=dispatch.alloc_energy)
    model.charging_efficiency = Param(model.VERY_LARGE_STORAGE_TECHNOLOGIES, initialize=dispatch.alloc_charging_efficiency)
    model.discharging_efficiency = Param(model.VERY_LARGE_STORAGE_TECHNOLOGIES, initialize=dispatch.alloc_discharging_efficiency)

    model.average_net_load = Param(model.GEOGRAPHIES, initialize=dispatch.average_net_load)
    model.period_net_load = Param(model.GEOGRAPHIES, model.PERIODS, initialize=dispatch.period_net_load)

    model.transmission_energy = Param(model.TRANSMISSION_LINES, model.PERIODS, initialize=dispatch.tx_energy_dict)
    model.transmission_losses = Param(model.TRANSMISSION_LINES, initialize=dispatch.transmission.losses.get_values_as_dict(dispatch.year))

    model.upward_imbalance_penalty = Param(initialize=dispatch.upward_imbalance_penalty,within=NonNegativeReals)
    model.downward_imbalance_penalty = Param(initialize=dispatch.downward_imbalance_penalty, within=NonNegativeReals)

    # Resource variables

    model.Charge = Var(model.VERY_LARGE_STORAGE_TECHNOLOGIES, model.PERIODS, within=NonNegativeReals)
    model.Discharge = Var(model.VERY_LARGE_STORAGE_TECHNOLOGIES, model.PERIODS, within=NonNegativeReals)
    model.Energy_in_Storage = Var(model.VERY_LARGE_STORAGE_TECHNOLOGIES, model.PERIODS, within=NonNegativeReals)
    model.Transmit_Energy = Var(model.TRANSMISSION_LINES, model.PERIODS,within=NonNegativeReals)
    model.Net_Transmit_Energy_by_Geo = Var(model.GEOGRAPHIES, model.PERIODS, within=Reals)

    # System variables
    model.Upward_Imbalance = Var(model.GEOGRAPHIES, model.PERIODS, within=NonNegativeReals)
    model.Downward_Imbalance = Var(model.GEOGRAPHIES, model.PERIODS, within=NonNegativeReals)

    #constraints
    model.Transmission_Constraint = Constraint(model.TRANSMISSION_LINES, model.PERIODS, rule=transmission_rule_alloc)
    model.Net_Transmit_Energy_by_Geo_Constraint = Constraint(model.GEOGRAPHIES, model.PERIODS, rule=net_transmit_energy_by_geo_rule)

    model.Upward_Imbalance_Constraint = Constraint(model.GEOGRAPHIES, model.PERIODS, rule=upward_imbalance_penalty_rule)
    model.Downward_Imbalance_Constraint = Constraint(model.GEOGRAPHIES, model.PERIODS, rule=downward_imbalance_penalty_rule)
    model.Storage_Energy_Tracking_Constraint = Constraint(model.VERY_LARGE_STORAGE_TECHNOLOGIES, model.PERIODS, rule=storage_energy_tracking_rule)
    model.Storage_Discharge_Constraint = Constraint(model.VERY_LARGE_STORAGE_TECHNOLOGIES, model.PERIODS, rule=storage_discharge_rule)
    model.Storage_Charge_Constraint = Constraint(model.VERY_LARGE_STORAGE_TECHNOLOGIES, model.PERIODS, rule=storage_charge_rule)
    model.Storage_Energy_Constraint = Constraint(model.VERY_LARGE_STORAGE_TECHNOLOGIES, model.PERIODS, rule=storage_energy_rule)

    # TODO: add charge and discharge efficiencies?

    model.Total_Imbalance = Objective(rule=total_imbalance_penalty_rule, sense=minimize)

    return model
