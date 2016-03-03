"""
Formulation of the dispatch optimization.
"""

from pyomo.environ import *


def dispatch_problem_formulation(_inputs, start_state_of_charge, end_state_of_charge, period,dispatch):
    """
    Formulation of dispatch problem.
    If _inputs contains data, the data are initialized with the formulation of the model (concrete model).
    Model is defined as "abstract," however, so data can also be loaded when create_instance() is called instead.

    :param _inputs:
    :param start_state_of_charge:
    :param end_state_of_charge:
    :param period:
    :return:
    """

    dispatch_model = AbstractModel()

    ###########################
    # ### Sets and params ### #
    ###########################

    # ### Temporal structure ### #
    dispatch_model.TIMEPOINTS = Set(within=NonNegativeIntegers, ordered=True,initialize=_inputs.period_timepoints[period])

    dispatch_model.flex_load_timepoint = Param(dispatch_model.TIMEPOINTS, within=PositiveIntegers, initialize=_inputs.period_flex_load_timepoints[period])


    def first_timepoint_init(model):
        """
        Assumes timepoints are ordered
        :param model:
        :return:
        """
        return min(model.TIMEPOINTS)

    dispatch_model.first_timepoint = Param(initialize=first_timepoint_init)

    def last_timepoint_init(model):
        """
        Assumes timepoints are ordered
        :param model:
        :return:
        """
        return max(model.TIMEPOINTS)

    dispatch_model.last_timepoint = Param(initialize=last_timepoint_init)

    def previous_timepoint_init(model):
        """
        Define a "previous timepoint" for periodic boundary constraints
        The previous timepoint for the first timepoint is the last timepoint
        :param model:
        :return:
        """
        previous_timepoints = dict()
        for timepoint in model.TIMEPOINTS:
            if timepoint == model.first_timepoint:
                previous_timepoints[timepoint] = model.last_timepoint
            else:
                previous_timepoints[timepoint] = timepoint - 1
        return previous_timepoints

    dispatch_model.previous_timepoint = Param(dispatch_model.TIMEPOINTS, initialize=previous_timepoint_init)

    # ### Geographic structure ### #
    dispatch_model.REGIONS = Set(initialize=dispatch.regions)
    dispatch_model.FEEDERS = Set(initialize=dispatch.feeders)

    # ### Technologies ### #
    dispatch_model.STORAGE_TECHNOLOGIES = Set(initialize=dispatch.storage_technologies)
    dispatch_model.GENERATION_TECHNOLOGIES = Set(initialize=_inputs.generation_technologies)
    dispatch_model.TECHNOLOGIES = dispatch_model.STORAGE_TECHNOLOGIES | dispatch_model.GENERATION_TECHNOLOGIES

    dispatch_model.large_storage = Param(dispatch_model.STORAGE_TECHNOLOGIES, initialize=dispatch.large_storage,
                                         within=Binary)
    dispatch_model.charging_efficiency = Param(dispatch_model.STORAGE_TECHNOLOGIES,
                                               initialize=dispatch.charging_efficiency)
    dispatch_model.discharging_efficiency = Param(dispatch_model.STORAGE_TECHNOLOGIES,
                                                  initialize=dispatch.discharging_efficiency)

    # Current, only "generation" technologys have variable costs; storage does not
    dispatch_model.variable_cost = Param(dispatch_model.GENERATION_TECHNOLOGIES, initialize=_inputs.variable_cost)

    def large_storage_tech_init(model):
        large_storage_techs = list()
        for t in model.STORAGE_TECHNOLOGIES:
            if model.large_storage[t]:
                large_storage_techs.append(t)
            else:
                pass
        return large_storage_techs

    dispatch_model.VERY_LARGE_STORAGE_TECHNOLOGIES = SET(dispatch_model.STORAGE_TECHNOLOGIES, initialize=dispatch.large_storage,within=Binary)

#    # ### Resources ### #
#    dispatch_model.RESOURCES = Set(initialize=_inputs.period_resources[period])
#    dispatch_model.technology = Param(dispatch_model.RESOURCES, within=dispatch_model.TECHNOLOGIES,
#                                      initialize=_inputs.period_technology[period])
#    dispatch_model.region = Param(dispatch_model.RESOURCES, within=dispatch_model.REGIONS,
#                                  initialize=
#                                  _inputs.period_region[period])
##    dispatch_model.distributed = Param(dispatch_model.RESOURCES, within=Binary,
##                                       initialize=_inputs.period_distributed[period])

#    def storage_resources_init(model):
#        storage_resources = list()
#        for r in model.RESOURCES:
#            if model.technology[r] in model.STORAGE_TECHNOLOGIES:
#                storage_resources.append(r)
#            else:
#                pass
#        return storage_resources
#
#    def generation_resources_init(model):
#        generation_resources = list()
#        for r in model.RESOURCES:
#            if model.technology[r] in model.GENERATION_TECHNOLOGIES:
#                generation_resources.append(r)
#            else:
#                pass
#        return generation_resources
#
#    dispatch_model.GENERATION_RESOURCES = Set(within=dispatch_model.RESOURCES, initialize=generation_resources_init)

    dispatch_model.capacity = Param(dispatch_model.TECHNOLOGIES, initialize= dispatch.period_capacity[period])
    dispatch_model.duration = Param(dispatch_model.STORAGE_TECHNOLOGIES, initialize= dispatch.period_duration[period])

#    def very_large_storage_resources_init(model):
#        very_large_storage_resources = list()
#        for r in model.STORAGE_RESOURCES:
#            if model.technology[r] in model.VERY_LARGE_STORAGE_TECHNOLOGIES:
#                very_large_storage_resources.append(r)
#            else:
#                pass
#        return very_large_storage_resources
#
#    dispatch_model.VERY_LARGE_STORAGE_RESOURCES = Set(within=dispatch_model.STORAGE_TECHNOLOGIES,within=Binary,
#                                                      initialize=dispatch.large_storage)
    dispatch_model.start_state_of_charge = Param(dispatch_model.VERY_LARGE_STORAGE_TECHNOLOGIES,
                                                 initialize=start_state_of_charge[period])
    dispatch_model.end_state_of_charge = Param(dispatch_model.VERY_LARGE_STORAGE_TECHNOLOGIES,
                                               initialize=end_state_of_charge[period])

    # ### System ### #

    # Load
    dispatch_model.net_distributed_load = Param(dispatch_model.REGIONS, dispatch_model.TIMEPOINTS, dispatch_model.FEEDERS,
                                                initialize=_inputs.net_distributed_load[period], within=Reals)
    # Flex and EV loads
    dispatch_model.min_cumulative_flex_load = Param(dispatch_model.REGIONS, dispatch_model.TIMEPOINTS,dispatch_model.FEEDERS,
                                                    within=NonNegativeReals,
                                                    initialize=_inputs.min_cumulative_flex_load[period])
    dispatch_model.max_cumulative_flex_load = Param(dispatch_model.REGIONS, dispatch_model.TIMEPOINTS,dispatch_model.FEEDERS,
                                                    within=NonNegativeReals,
                                                    initialize=_inputs.max_cumulative_flex_load[period])

    # Renewables
    dispatch_model.bulk_renewables = Param(dispatch_model.REGIONS, dispatch_model.TIMEPOINTS,
                                           within=NonNegativeReals,
                                           initialize=_inputs.bulk_renewables[period])

    # TODO: should this also vary by timepoint
    dispatch_model.max_flex_load = Param(dispatch_model.REGIONS,dispatch_model.FEEDERS,
                                         within=NonNegativeReals, initialize=_inputs.period_max_flex_load[period])

    # T&D

    dispatch_model.TRANSMISSION_LINES = Set(initialize=_inputs.transmission_lines)
    dispatch_model.transmission_from = Param(dispatch_model.TRANSMISSION_LINES, initialize=_inputs.transmission_from)
    dispatch_model.transmission_to = Param(dispatch_model.TRANSMISSION_LINES, initialize=_inputs.transmission_to)

    dispatch_model.transmission_capacity = Param(dispatch_model.TRANSMISSION_LINES,
                                                 initialize=_inputs.transmission_capacity)

    dispatch_model.dist_net_load_threshold = Param(dispatch_model.REGIONS, dispatch_model.FEEDERS, within=NonNegativeReals,
                                                   initialize=_inputs.dist_net_load_threshold)
    dispatch_model.bulk_net_load_threshold = Param(dispatch_model.REGIONS, within=NonNegativeReals,
                                                   initialize=_inputs.bulk_net_load_threshold)

    dispatch_model.t_and_d_losses = Param(within=PercentFraction, initialize=_inputs.t_and_d_losses)

    # Imbalance penalties
    # Not regionalized, as we don't want arbitrage across regions
    dispatch_model.curtailment_cost = Param(within=NonNegativeReals, initialize=_inputs.curtailment_cost)
    dispatch_model.unserved_energy_cost = Param(within=NonNegativeReals, initialize=_inputs.unserved_energy_cost)
    dispatch_model.dist_penalty = Param(within=NonNegativeReals, initialize=_inputs.dist_net_load_penalty)
    dispatch_model.bulk_penalty = Param(within=NonNegativeReals, initialize=_inputs.bulk_net_load_penalty)


    #####################
    # ### Variables ### #
    #####################

    # Projects
    dispatch_model.Provide_Power = Var(dispatch_model.GENERATION_TECHNOLOGIES,
                                       dispatch_model.TIMEPOINTS, within=NonNegativeReals)
    dispatch_model.Charge = Var(dispatch_model.STORAGE_TECHNOLOGIES,
                                dispatch_model.TIMEPOINTS, within=NonNegativeReals)
    dispatch_model.Energy_in_Storage = Var(dispatch_model.STORAGE_TECHNOLOGIES,
                                           dispatch_model.TIMEPOINTS, within=NonNegativeReals)

    # Transmission
    dispatch_model.Transmit_Power = Var(dispatch_model.TRANSMISSION_LINES, dispatch_model.TIMEPOINTS,
                                        within=Reals)

    # System
    dispatch_model.Flexible_Load = Var(dispatch_model.REGIONS, dispatch_model.TIMEPOINTS, dispatch_model.FEEDERS, within=NonNegativeReals)
#    dispatch_model.EV_Load = Var(dispatch_model.REGIONS, dispatch_model.TIMEPOINTS,dispatch_model.FEEDERS, within=NonNegativeReals)

    dispatch_model.DistSysCapacityNeed = Var(dispatch_model.REGIONS, dispatch_model.TIMEPOINTS, dispatch_model.FEEDERS, within=NonNegativeReals)
    dispatch_model.BulkSysCapacityNeed = Var(dispatch_model.REGIONS, dispatch_model.TIMEPOINTS, within=NonNegativeReals)

    dispatch_model.Curtailment = Var(dispatch_model.REGIONS, dispatch_model.TIMEPOINTS, within=NonNegativeReals)
    dispatch_model.Unserved_Energy = Var(dispatch_model.REGIONS, dispatch_model.TIMEPOINTS,within=NonNegativeReals)

    ##############################
    # ### Objective function ### #
    ##############################

    def total_cost_rule(model):

        gen_cost = sum(model.Provide_Power[gt, t] * model.variable_cost[model.technology[gt]]
                       for gt in model.GENERATION_TECHNOLOGIES
                       for t in model.TIMEPOINTS)

        curtailment_cost = sum(model.Curtailment[r, t] * model.curtailment_cost for r in model.REGIONS
                               for t in model.TIMEPOINTS)
        unserved_energy_cost = sum(model.Unserved_Energy[r, t] * model.unserved_energy_cost
                                   for r in model.REGIONS
                                   for t in model.TIMEPOINTS)
        dist_sys_penalty_cost = sum(model.DistSysCapacityNeed[r, t, f] * model.dist_penalty for r in model.REGIONS
                                    for t in model.TIMEPOINTS
                                    for f in model.FEEDERS)
        bulk_sys_penalty_cost = sum(model.BulkSysCapacityNeed[r, t] * model.bulk_penalty for r in model.REGIONS
                                    for t in model.TIMEPOINTS)

        total_cost = gen_cost + curtailment_cost + unserved_energy_cost + dist_sys_penalty_cost + bulk_sys_penalty_cost

        return total_cost

    dispatch_model.Total_Cost = Objective(rule=total_cost_rule, sense=minimize)

    #######################
    # ### Constraints ### #
    #######################

    # ### Meet load constraint ### #
    def meet_load_rule(model, region, timepoint):
        """
        In each region and timepoint, net bulk power plus curtailment must equal the bulk load,
        i.e. the distributed load plus an adjustment for T&D losses.

        The distributed load is equal to the static load plus flex/EV load plus any other distributed loads (e.g.
        distributed storage charging) minus any power available at the distribution level.

        Bulk power is equal to bulk generation plus net bulk storage plus imports/exports.

        This assumes we won't be charging bulk storage with distributed power -- in that situation this constraint will
        break, as the direction of losses would need to be reversed.


        :param model:
        :param region:
        :param timepoint:
        :return:
        """

        bulk_power = float()
        for t in model.TECHNOLOGIES:
            if model.region[t] == region and model.feeder[t] == 0:
                bulk_power += model.Provide_Power[t, timepoint]
            else:
                pass

        bulk_charging = float()
        for st in model.STORAGE_TECHNOLOGIES:
            if model.region[st] == region and model.feeder[st] == 0:
                bulk_charging += model.Charge[st, timepoint]
            else:
                pass

        distributed_power = float()
        for t in model.TECHNOLOGIES:
            for feeder in model.FEEDERS:
                if model.region[t] == region and model.feeder[t] == feeder and feeder!=0:
                    distributed_power += model.Provide_Power[t, timepoint]
            else:
                pass

        distributed_charging = float()
        for st in model.STORAGE_TECHNOLOGIES:
            for feeder in model.FEEDERS:
                if model.region[st] == region and model.feeder[st] == feeder and feeder!=0:
                    distributed_charging += model.Charge[st, timepoint]
            else:
                pass

        imports_exports = float()
        for tl in model.TRANSMISSION_LINES:
            if model.transmission_to[tl] == region:
                imports_exports += model.Transmit_Power[tl, timepoint]
            if model.transmission_from[tl] == region:
                imports_exports -= model.Transmit_Power[tl, timepoint]
            else:
                pass

        return bulk_power + model.bulk_renewables[region, timepoint] - bulk_charging \
            + imports_exports \
            - model.Curtailment[region, timepoint] \
            == (sum(model.net_distributed_load[region, timepoint,feeder] for feeder in model.FEEDERS) - distributed_power + distributed_charging +
                sum(model.Flexible_Load[region, timepoint,feeder] for feeder in model.FEEDERS)  -
                model.Unserved_Energy[region, timepoint]) \
            * (1 + model.t_and_d_losses)

    dispatch_model.Meet_Load_Constraint = Constraint(dispatch_model.REGIONS, dispatch_model.TIMEPOINTS,
                                                     rule=meet_load_rule)

    # ### Project constraints ### #

    # "Gas"
    def gas_and_storage_power_rule(model, technology, timepoint):
        """
        Storage cannot discharge at a higher rate than implied by its total installed power capacity.
        Charge and discharge rate limits are currently the same.
        :param model:
        :param technology:
        :param timepoint:
        :return:
        """

        return model.Provide_Power[technology, timepoint] \
            <= model.capacity[technology]

    dispatch_model.Power_Constraint = Constraint(dispatch_model.TECHNOLOGIES,
                                                 dispatch_model.TIMEPOINTS,
                                                 rule=gas_and_storage_power_rule)

    # Storage
    def storage_charge_rule(model, technology, timepoint):
        """
        Storage cannot charge at a higher rate than implied by its total installed power capacity.
        Charge and discharge rate limits are currently the same.
        :param model:
        :param technology:
        :param timepoint:
        :return:
        """

        return model.Charge[technology, timepoint] \
            <= model.capacity[technology]

    dispatch_model.Storage_Charge_Constraint = Constraint(dispatch_model.STORAGE_TECHNOLOGIES, dispatch_model.TIMEPOINTS,
                                                          rule=storage_charge_rule)

    def storage_energy_rule(model, technology, timepoint):
        """
        No more total energy can be stored at any point that the total storage energy capacity.
        :param model:
        :param technology:
        :param timepoint:
        :return:
        """

        return model.Energy_in_Storage[technology, timepoint] \
            <= model.capacity[technology] * model.duration[technology]

    dispatch_model.Storage_Energy_Constraint = Constraint(dispatch_model.STORAGE_RESOURCES, dispatch_model.TIMEPOINTS,
                                                          rule=storage_energy_rule)

    def storage_energy_tracking_rule(model, technology, timepoint):
        """
        The total energy in storage at the start of the current timepoint must equal
        the energy in storage at the start of the previous timepoint
        plus charging that happened in the last timepoint, adjusted for the charging efficiency,
        minus discharging in the last timepoint, adjusted for the discharging efficiency.
        The starting and ending state of charge are determined outside this optimization for large storage technologies.
        :param model:
        :param technology:
        :param timepoint:
        :return:
        """
        if technology in model.VERY_LARGE_STORAGE_TECHNOLOGIES and timepoint == model.first_timepoint:
            return model.Energy_in_Storage[technology, timepoint] == \
                   model.start_state_of_charge[technology]
        else:
            return model.Energy_in_Storage[technology, timepoint] \
                == model.Energy_in_Storage[technology, model.previous_timepoint[timepoint]] \
                + model.Charge[technology, model.previous_timepoint[timepoint]] \
                * model.charging_efficiency[technology] \
                - model.Provide_Power[technology, model.previous_timepoint[timepoint]] \
                / model.discharging_efficiency[technology]

    dispatch_model.Storage_Energy_Tracking_Constraint = Constraint(dispatch_model.STORAGE_TECHNOLOGIES,
                                                                   dispatch_model.TIMEPOINTS,
                                                                   rule=storage_energy_tracking_rule)

    def large_storage_end_state_of_charge_rule(model, technology, timepoint):
        """
        In addition to tracking energy from timepoint to timepoint, the ending state of charge of large storage
        must equal a predetermined value.
        :param model:
        :param technology:
        :param timepoint:
        :return:
        """
        if timepoint == model.last_timepoint:
            return model.Energy_in_Storage[technology, timepoint] \
                   + model.Charge[technology, timepoint] - model.Provide_Power[technology, timepoint] == \
                   model.end_state_of_charge[technology]
        else:
            return Constraint.Skip

    dispatch_model.Large_Storage_End_State_of_Charge_Constraint = Constraint(dispatch_model.VERY_LARGE_STORAGE_TECHNOLOGIES,
                                                                             dispatch_model.TIMEPOINTS,
                                                                             rule=large_storage_end_state_of_charge_rule)

    # Flex loads
    def cumulative_flexible_load_rule(model, region, timepoint, feeder):
        """
        The cumulative flexible load through each timepoint must be between the minimum and maximum cumulative flexible
        load for that timepoint.
        :param model:
        :param region:
        :param timepoint:
        :param feeder
        :return:
        """
        previous_timepoints = list()
        for tmp in model.TIMEPOINTS:
            if model.flex_load_timepoint[tmp] <= model.flex_load_timepoint[timepoint]:
                previous_timepoints.append(tmp)
            else:
                pass
        return model.min_cumulative_flex_load[region, timepoint, feeder] \
            <= sum(model.Flexible_Load[region, prev_timepoint, feeder] for prev_timepoint in previous_timepoints) \
            <= model.max_cumulative_flex_load[region, timepoint, feeder]

    dispatch_model.Cumulative_Flexible_Load_Constraint = Constraint(dispatch_model.REGIONS, dispatch_model.TIMEPOINTS, dispatch_model.FEEDERS,
                                                                    rule=cumulative_flexible_load_rule)

    def max_flex_load_rule(model, region, timepoint, feeder):
        """
        Maximum flexible load that can be shifted to a given timepoint.
        :param model:
        :param region:
        :param timepoint:
        :return:
        """
        return model.Flexible_Load[region, timepoint, feeder] <= model.max_flex_load[region, feeder]

    dispatch_model.Max_Flex_Load_Constraint = Constraint(dispatch_model.REGIONS, dispatch_model.TIMEPOINTS,dispatch_model.FEEDERS,
                                                         rule=max_flex_load_rule)

#    # EV loads; currently same implementation as flex load
#    def cumulative_ev_load_rule(model, region, timepoint):
#        """
#
#        :param model:
#        :param region:
#        :param timepoint:
#        :return:
#        """
#        previous_timepoints = list()
#        for tmp in model.TIMEPOINTS:
#            if model.ev_load_timepoint[tmp] <= model.ev_load_timepoint[timepoint]:
#                previous_timepoints.append(tmp)
#            else:
#                pass
#        return model.min_cumulative_ev_load[region, timepoint] \
#            <= sum(model.EV_Load[region, prev_timepoint] for prev_timepoint in previous_timepoints) \
#            <= model.max_cumulative_ev_load[region, timepoint]
#
#    dispatch_model.Cumulative_EV_Load_Constraint = Constraint(dispatch_model.REGIONS, dispatch_model.TIMEPOINTS,
#                                                              rule=cumulative_ev_load_rule)
#
#    def max_ev_load_rule(model, region, timepoint):
#        """
#        Maximum EV load that can be shifted to a given timepoint.
#        :param model:
#        :param region:
#        :param timepoint:
#        :return:
#        """
#        return model.EV_Load[region, timepoint] <= model.max_ev_load[region]
#
#    dispatch_model.Max_EV_Load_Constraint = Constraint(dispatch_model.REGIONS, dispatch_model.TIMEPOINTS,
#                                                       rule=max_ev_load_rule)

    # Transmission
    def transmission_rule(model, line, timepoint):
        """
        Transmission line flow is limited by transmission capacity.
        :param model:
        :param line:
        :param timepoint:
        :return:
        """

        return -model.transmission_capacity[line] \
            <= model.Transmit_Power[line, timepoint] \
            <= model.transmission_capacity[line]

    dispatch_model.Transmission_Constraint = Constraint(dispatch_model.TRANSMISSION_LINES,
                                                                       dispatch_model.TIMEPOINTS,
                                                                       rule=transmission_rule)

    # Distribution system penalty
    def dist_system_capacity_need_rule(model, region, timepoint, feeder):
        """
        Apply a penalty whenever distributed net load exceeds a pre-specified threshold
        :param model:
        :param region:
        :param timepoint:
        :return:
        """
        distributed_power = sum(model.Provide_Power[technology, timepoint]
                                for technology in model.TECHNOLOGIES
                                if model.region[technology] == region and model.feeder[technology]==feeder)

        distributed_charging = sum(model.Charge[technology, timepoint]
                                   for storage_technology in model.STORAGE_TECHNOLOGIES
                                   if model.region[storage_technology] == region and model.feeder[storage_technology]==feeder)

        return model.DistSysCapacityNeed[region, timepoint, feeder] \
            >= (model.net_distributed_load[region, timepoint,feeder] +
                model.Flexible_Load[region, timepoint, feeder] +
                distributed_charging - distributed_power
                ) - model.dist_net_load_threshold[region,feeder]

    dispatch_model.Distribution_System_Penalty_Constraint = Constraint(dispatch_model.REGIONS,
                                                                       dispatch_model.TIMEPOINTS, model.FEEDERS,
                                                                       rule=dist_system_capacity_need_rule)

    # Bulk system capacity penalty
    def bulk_system_capacity_need_rule(model, region, timepoint):
        """
        Apply a penalty whenever bulk net load (distributed load + T&D losses) exceeds a pre-specified threshold.
        :param model:
        :param region:
        :param timepoint:
        :return:
        """
        distributed_power = sum(model.Provide_Power[technology, timepoint]
                                for technology in model.TECHNOLOGIES
                                if model.region[technology] == region and model.feeder[technology]!=0)

        distributed_charging = sum(model.Charge[technology, timepoint]
                                   for technology in model.STORAGE_TECHNOLOGIES
                                   if model.region[technology] == region and model.feeder[technology]!=0)

        return model.BulkSysCapacityNeed[region, timepoint] \
            >= (sum(model.net_distributed_load[region, timepoint] for f in model.FEEDERS) +
                sum(model.Flexible_Load[region, timepoint] for f in model.FEEDERS) +
                distributed_charging - distributed_power
                ) * (1 + model.t_and_d_losses) - model.bulk_net_load_threshold[region]

    dispatch_model.Bulk_System_Penalty_Constraint = Constraint(dispatch_model.REGIONS,
                                                               dispatch_model.TIMEPOINTS,
                                                               rule=bulk_system_capacity_need_rule)

    return dispatch_model
