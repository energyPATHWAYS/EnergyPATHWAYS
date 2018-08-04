"""
Formulation of the dispatch optimization.
"""

from pyomo.environ import *
import pdb

def large_storage_tech_init(model):
    large_storage_techs = list()
    for t in model.STORAGE_TECHNOLOGIES:
        if model.large_storage[t]:
            large_storage_techs.append(t)
        else:
            pass
    return large_storage_techs

def feeder_charge(model, geography, timepoint, feeder):
    return sum(model.Charge[t, timepoint] for t in model.STORAGE_TECHNOLOGIES if (model.geography[t]==geography) and (model.feeder[t]==feeder))

def feeder_provide_power(model, geography, timepoint, feeder):
    return sum(model.Provide_Power[t, timepoint] for t in model.TECHNOLOGIES if (model.geography[t]==geography) and (model.feeder[t]==feeder))

def meet_load_rule(model, geography, timepoint):
    """
    In each geography and timepoint, net bulk power plus curtailment must equal the bulk load,
    i.e. the distribution load plus an adjustment for T&D losses.

    The distribution load is equal to the static load plus flex/EV load plus any other distribution loads (e.g.
    distribution storage charging) minus any power available at the distribution level.

    Bulk power is equal to bulk generation plus net bulk storage plus imports/exports.

    This assumes we won't be charging bulk storage with distribution power -- in that situation this constraint will
    break, as the direction of losses would need to be reversed.
    """
    return (feeder_provide_power(model, geography, timepoint, feeder=0) +
            model.Net_Transmit_Power_by_Geo[geography, timepoint] +
            model.bulk_gen[geography, timepoint] -
            model.bulk_load[geography, timepoint] * model.t_and_d_losses[geography,0] -
            feeder_charge(model, geography, timepoint, feeder=0) * model.t_and_d_losses[geography,0] -
            model.Curtailment[geography, timepoint]) \
            == \
            sum(model.t_and_d_losses[geography,feeder] * 
            (model.distribution_load[geography, timepoint,feeder] -
            model.distribution_gen[geography, timepoint,feeder] -
            feeder_provide_power(model, geography, timepoint, feeder) +
            feeder_charge(model, geography, timepoint, feeder) +
            model.Flexible_Load[geography, timepoint,feeder])
            for feeder in model.FEEDERS if feeder!=0) - \
            model.Unserved_Energy[geography, timepoint]

def power_rule(model, technology, timepoint):
    """
    Storage cannot discharge at a higher rate than implied by its total installed power capacity.
    Charge and discharge rate limits are currently the same.
    """
    return model.min_capacity[technology]<= model.Provide_Power[technology, timepoint] <= model.capacity[technology]


def ld_energy_rule(model, technology):
    return sum(model.Provide_Power[technology,t] for t in model.TIMEPOINTS) == model.ld_energy[technology]


def storage_charge_rule(model, technology, timepoint):
    """
    Storage cannot charge at a higher rate than implied by its total installed power capacity.
    Charge and discharge rate limits are currently the same.
    """
    return model.Charge[technology, timepoint] + model.Provide_Power[technology, timepoint] <= model.capacity[technology]

def storage_energy_rule(model, technology, timepoint):
    """
    No more total energy can be stored at any point that the total storage energy capacity.
    """
    return 0 <= model.Energy_in_Storage[technology, timepoint] <= model.capacity[technology] * model.duration[technology]
    
    
#def storage_simultaneous_rule(model,technology,timepoint):
    # return model.Charge[technology, timepoint] * model.Provide_Power[technology, timepoint] <= 0

def storage_energy_tracking_rule(model, technology, timepoint):
    """
    The total energy in storage at the start of the current timepoint must equal
    the energy in storage at the start of the previous timepoint
    plus charging that happened in the last timepoint, adjusted for the charging efficiency,
    minus discharging in the last timepoint, adjusted for the discharging efficiency.
    The starting and ending state of charge are determined outside this optimization for large storage technologies.
    """
    if technology in model.VERY_LARGE_STORAGE_TECHNOLOGIES and timepoint == model.first_timepoint.value:
        return model.Energy_in_Storage[technology, timepoint] == \
               model.start_state_of_charge[technology]
    else:
        return model.Energy_in_Storage[technology, timepoint] \
            == model.Energy_in_Storage[technology, model.previous[timepoint]] \
            + model.Charge[technology, model.previous[timepoint]] \
            * model.charging_efficiency[technology] \
            - model.Provide_Power[technology, model.previous[timepoint]] \
            / model.discharging_efficiency[technology]

def large_storage_end_state_of_charge_rule(model, technology, timepoint):
    """
    In addition to tracking energy from timepoint to timepoint, the ending state of charge of large storage
    must equal a predetermined value.
    :param model:
    :param technology:
    :param timepoint:
    :return:
    """
    if technology in model.VERY_LARGE_STORAGE_TECHNOLOGIES and timepoint == model.last_timepoint.value:
        return model.Energy_in_Storage[technology, timepoint] \
               + model.Charge[technology, timepoint]* model.charging_efficiency[technology]\
               - model.Provide_Power[technology, timepoint]/model.discharging_efficiency[technology] >= \
               model.end_state_of_charge[technology]
    else:
        return Constraint.Skip

def cumulative_flex_load_tracking_rule(model, geography, timepoint, feeder):
    if feeder == 0:
        return Constraint.Skip
    
    return model.Cumulative_Flexible_Load[geography, timepoint, feeder] == model.Cumulative_Flexible_Load[geography, model.previous[timepoint], feeder] + model.Flexible_Load[geography, timepoint, feeder]

def cumulative_flexible_load_rule(model, geography, timepoint, feeder):
    """
    The cumulative flexible load through each timepoint must be between the minimum and maximum cumulative flexible
    load for that timepoint.
    """
    if feeder == 0:
        return Constraint.Skip
    
    if timepoint == model.last_timepoint.value:
        return model.Cumulative_Flexible_Load[geography, timepoint, feeder] == 0
    else:
        return model.min_cumulative_flex_load[geography, timepoint, feeder] \
        <= model.cumulative_distribution_load[geography, timepoint, feeder] + model.Cumulative_Flexible_Load[geography, timepoint, feeder] \
        <= model.max_cumulative_flex_load[geography, timepoint, feeder]

def flex_load_capacity_rule(model, geography, timepoint, feeder):
    """
    Maximum flexible load that can be shifted to a given timepoint.
    """
    if feeder == 0:
        return model.Flexible_Load[geography, timepoint, feeder] == 0
    else:
        return model.min_flex_load[geography, feeder] <= model.Flexible_Load[geography, timepoint, feeder] + model.distribution_load[geography, timepoint, feeder] <= model.max_flex_load[geography, feeder]

def zero_flexible_load(model, geography, timepoint, feeder):
    return model.Flexible_Load[geography, timepoint, feeder] == 0
    
def storage_power_rule(model, technology, timepoint):
    return model.Provide_Power[technology, timepoint] == model.Storage_Provide_Power[technology, timepoint]
    
def generation_power_rule(model, technology, timepoint):
    return model.Provide_Power[technology, timepoint] == model.Generation_Provide_Power[technology, timepoint]
    
def ld_power_rule(model, technology, timepoint):   
    return model.Provide_Power[technology, timepoint] == model.LD_Provide_Power[technology, timepoint]

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

def dist_system_capacity_need_rule(model, geography, timepoint, feeder):
    """
    Apply a penalty whenever distribution net load exceeds a pre-specified threshold
    """    
    if feeder ==0:
        return Constraint.Skip
    else:
        return (model.DistSysCapacityNeed[geography, feeder] +
           model.dist_net_load_threshold[geography, feeder]) \
           >= \
           (model.distribution_load[geography, timepoint, feeder] -
           model.distribution_gen[geography, timepoint, feeder] + 
           model.Flexible_Load[geography, timepoint, feeder] +
           feeder_charge(model, geography, timepoint, feeder) -
           feeder_provide_power(model, geography, timepoint, feeder))

def flex_load_use_rule(model, geography, timepoint, feeder):
    """
    Apply a penalty whenever distribution net load exceeds a pre-specified threshold
    """
    return model.FlexLoadUse[geography, timepoint, feeder]>= model.Flexible_Load[geography, timepoint, feeder]

def bulk_system_capacity_need_rule(model, geography, timepoint):
    """
    Apply a penalty whenever bulk net load (distribution load + T&D losses) exceeds a pre-specified threshold.
    """
    return (model.BulkSysCapacityNeed[geography] +
           model.bulk_net_load_threshold[geography]) \
           >= \
           sum((model.t_and_d_losses[geography,feeder]) *
           (model.distribution_load[geography, timepoint,feeder] -
           model.distribution_gen[geography, timepoint,feeder] -
           feeder_provide_power(model, geography, timepoint, feeder) +
           feeder_charge(model, geography, timepoint, feeder) +
           model.Flexible_Load[geography, timepoint,feeder]) \
           for feeder in model.FEEDERS if feeder!=0) - \
           model.Unserved_Energy[geography, timepoint] + \
           model.bulk_load[geography, timepoint] - \
           model.dispatched_bulk_load[geography, timepoint] * .5

def unserved_capacity_rule(model, geography, timepoint):
    """
    Apply a penalty whenever bulk net load (distribution load + T&D losses) exceeds a pre-specified threshold.
    """
    return model.Unserved_Capacity[geography] >= model.Unserved_Energy[geography, timepoint]

def unserved_energy_rule(model, geography, timepoint):
    """
    Apply a penalty whenever bulk net load (distribution load + T&D losses) exceeds a pre-specified threshold.
    """
    return 0 <= model.Unserved_Energy[geography, timepoint]



def total_cost_rule(model):
    gen_cost = sum(model.Provide_Power[gt, t] * model.variable_cost[gt] for gt in model.GENERATION_TECHNOLOGIES
                                                                        for t in model.TIMEPOINTS)
    curtailment_cost = sum(model.Curtailment[r, t] * model.curtailment_cost for r in model.GEOGRAPHIES 
                                                                            for t in model.TIMEPOINTS)
    unserved_capacity_cost = sum(model.Unserved_Capacity[r] * model.unserved_capacity_cost for r in model.GEOGRAPHIES)
    unserved_energy_cost = sum(model.Unserved_Energy[r, t] * model.unserved_energy_cost for r in model.GEOGRAPHIES for t in model.TIMEPOINTS)
    dist_sys_penalty_cost = sum(model.DistSysCapacityNeed[r, f] * model.dist_penalty for r in model.GEOGRAPHIES
                                                                                        for f in model.FEEDERS)
    bulk_sys_penalty_cost = sum(model.BulkSysCapacityNeed[r] * model.bulk_penalty for r in model.GEOGRAPHIES)
    flex_load_use_cost = sum(model.FlexLoadUse[r, t, f] * model.flex_penalty for r in model.GEOGRAPHIES
                                                                             for t in model.TIMEPOINTS
                                                                             for f in model.FEEDERS)
    transmission_hurdles = sum(model.Transmit_Power[str((from_geo, to_geo)), t] * model.transmission_hurdle[str((from_geo, to_geo))]
                                                                                for from_geo in model.GEOGRAPHIES
                                                                                for to_geo in model.GEOGRAPHIES
                                                                                for t in model.TIMEPOINTS if from_geo!=to_geo)
    total_cost = gen_cost + curtailment_cost + unserved_capacity_cost + unserved_energy_cost + dist_sys_penalty_cost + bulk_sys_penalty_cost + flex_load_use_cost + transmission_hurdles
    return total_cost

def min_timepoints(model):
    return model.TIMEPOINTS.value[0]

def max_timepoints(model):
    return model.TIMEPOINTS.value[-1]
    return total_cost


def create_dispatch_model(dispatch, period, model_type='abstract'):
    """
    Formulation of dispatch problem.
    If _inputs contains data, the data are initialized with the formulation of the model (concrete model).
    Model is defined as "abstract," however, so data can also be loaded when create_instance() is called instead.
    """
    model = AbstractModel() if model_type == 'abstract' else ConcreteModel()

    ###########################
    # ### Sets and params ### #
    ###########################
    # ### Temporal structure ### #
    model.TIMEPOINTS = Set(within=NonNegativeIntegers, ordered=True, initialize=dispatch.period_timepoints[period])
    model.previous = Param(model.TIMEPOINTS, within=NonNegativeIntegers, initialize=dispatch.period_previous_timepoints[period])
    model.first_timepoint = Param(initialize=min_timepoints)
    model.last_timepoint = Param(initialize=max_timepoints)

    # ### Geographic structure ### #
    model.GEOGRAPHIES = Set(initialize=dispatch.dispatch_geographies)
    model.FEEDERS = Set(initialize=dispatch.feeders)

    # ### Technologies ### #
    model.STORAGE_TECHNOLOGIES = Set(initialize=dispatch.storage_technologies)
    model.GENERATION_TECHNOLOGIES = Set(initialize=dispatch.generation_technologies)
    model.LD_TECHNOLOGIES = Set(initialize=dispatch.ld_technologies)
    model.TECHNOLOGIES = model.STORAGE_TECHNOLOGIES | model.GENERATION_TECHNOLOGIES | model.LD_TECHNOLOGIES
    model.large_storage = Param(model.STORAGE_TECHNOLOGIES, initialize=dispatch.large_storage, within=Binary)
    model.VERY_LARGE_STORAGE_TECHNOLOGIES = Set(within=model.STORAGE_TECHNOLOGIES, initialize=large_storage_tech_init)
    model.start_state_of_charge = Param(model.VERY_LARGE_STORAGE_TECHNOLOGIES, initialize=(dispatch.start_soc_large_storage[period] if len(dispatch.start_soc_large_storage) else dispatch.start_soc_large_storage))
    model.end_state_of_charge = Param(model.VERY_LARGE_STORAGE_TECHNOLOGIES, initialize=(dispatch.end_soc_large_storage[period] if len(dispatch.end_soc_large_storage) else dispatch.end_soc_large_storage))
    model.charging_efficiency = Param(model.STORAGE_TECHNOLOGIES, initialize=dispatch.charging_efficiency)
    model.discharging_efficiency = Param(model.STORAGE_TECHNOLOGIES, initialize=dispatch.discharging_efficiency)

    # Only "generation" technologys have variable costs; storage does not
    model.variable_cost = Param(model.GENERATION_TECHNOLOGIES, initialize=dispatch.variable_costs)
    model.geography = Param(model.TECHNOLOGIES, within=model.GEOGRAPHIES, initialize=dispatch.geography[period])
    model.feeder = Param(model.TECHNOLOGIES, within=model.FEEDERS, initialize=dispatch.feeder[period])
    model.min_capacity = Param(model.TECHNOLOGIES, initialize=dispatch.min_capacity[period])    
    model.capacity = Param(model.TECHNOLOGIES, initialize=dispatch.capacity[period])
    model.duration = Param(model.STORAGE_TECHNOLOGIES, initialize= dispatch.duration[period])
    model.ld_energy = Param(model.LD_TECHNOLOGIES, initialize = (dispatch.ld_energy_budgets[period] if len(dispatch.ld_energy_budgets) else dispatch.ld_energy_budgets))
    
    # ### System ### #
    # Load
    model.distribution_load = Param(model.GEOGRAPHIES, model.TIMEPOINTS, model.FEEDERS, initialize=dispatch.distribution_load[period], within=Reals)
    model.bulk_load = Param(model.GEOGRAPHIES, model.TIMEPOINTS, within=Reals, initialize=dispatch.bulk_load[period]) 
    model.dispatched_bulk_load = Param(model.GEOGRAPHIES, model.TIMEPOINTS, within=Reals, initialize=dispatch.dispatched_bulk_load[period])     
    model.distribution_gen = Param(model.GEOGRAPHIES, model.TIMEPOINTS, model.FEEDERS, initialize=dispatch.distribution_gen[period], within=Reals)
    model.bulk_gen = Param(model.GEOGRAPHIES, model.TIMEPOINTS, within=NonNegativeReals, initialize=dispatch.bulk_gen[period])                                        
                                           
    # Flex  loads
    model.min_cumulative_flex_load = Param(model.GEOGRAPHIES, model.TIMEPOINTS, model.FEEDERS, within=Reals, initialize=dispatch.min_cumulative_flex_load[period])
    model.max_cumulative_flex_load = Param(model.GEOGRAPHIES, model.TIMEPOINTS, model.FEEDERS, within=Reals, initialize=dispatch.max_cumulative_flex_load[period])
    model.cumulative_distribution_load = Param(model.GEOGRAPHIES, model.TIMEPOINTS, model.FEEDERS, within=Reals, initialize=dispatch.cumulative_distribution_load[period])
    model.max_flex_load = Param(model.GEOGRAPHIES,model.FEEDERS, within=Reals, initialize=dispatch.max_flex_load[period])
    model.min_flex_load = Param(model.GEOGRAPHIES,model.FEEDERS, within=Reals, initialize=dispatch.min_flex_load[period])
    
    model.TRANSMISSION_LINES = Set(initialize=dispatch.transmission.list_transmission_lines)
    model.transmission_capacity = Param(model.TRANSMISSION_LINES, initialize=dispatch.transmission.constraints.get_values_as_dict(dispatch.year))
    model.transmission_hurdle = Param(model.TRANSMISSION_LINES, initialize=dispatch.transmission.hurdles.get_values_as_dict(dispatch.year))
    model.transmission_losses = Param(model.TRANSMISSION_LINES, initialize=dispatch.transmission.losses.get_values_as_dict(dispatch.year))

    model.dist_net_load_threshold = Param(model.GEOGRAPHIES, model.FEEDERS, within=NonNegativeReals, initialize=dispatch.dist_net_load_thresholds)
    model.bulk_net_load_threshold = Param(model.GEOGRAPHIES, within=NonNegativeReals, initialize=dispatch.bulk_net_load_thresholds)
    model.t_and_d_losses = Param(model.GEOGRAPHIES, model.FEEDERS,within=NonNegativeReals, initialize=dispatch.t_and_d_losses)

    # Imbalance penalties
    # Not geographyalized, as we don't want arbitrage across geographies
    model.curtailment_cost = Param(within=NonNegativeReals, initialize= dispatch.curtailment_cost)
    model.unserved_capacity_cost = Param(within=NonNegativeReals, initialize= dispatch.unserved_capacity_cost)
    model.unserved_energy_cost = Param(within=NonNegativeReals, initialize= max(dispatch.variable_costs.values())*1.05)
    model.dist_penalty = Param(within=NonNegativeReals, initialize= dispatch.dist_net_load_penalty)
    model.bulk_penalty = Param(within=NonNegativeReals, initialize= dispatch.bulk_net_load_penalty)
    model.flex_penalty = Param(within=NonNegativeReals, initialize= dispatch.flex_load_penalty)
    #####################
    # ### Variables ### #
    #####################
    # Projects
    model.Provide_Power = Var(model.TECHNOLOGIES, model.TIMEPOINTS, within=Reals)
    model.LD_Provide_Power = Var(model.LD_TECHNOLOGIES, model.TIMEPOINTS, within=Reals)
    model.Storage_Provide_Power = Var(model.STORAGE_TECHNOLOGIES, model.TIMEPOINTS, within=Reals)
    model.Generation_Provide_Power = Var(model.GENERATION_TECHNOLOGIES, model.TIMEPOINTS, within=Reals)
    model.Charge = Var(model.STORAGE_TECHNOLOGIES, model.TIMEPOINTS, within=NonNegativeReals)
    model.Energy_in_Storage = Var(model.STORAGE_TECHNOLOGIES, model.TIMEPOINTS, within=NonNegativeReals)

    # Transmission
    model.Transmit_Power = Var(model.TRANSMISSION_LINES, model.TIMEPOINTS, within=NonNegativeReals)
    model.Net_Transmit_Power_by_Geo = Var(model.GEOGRAPHIES, model.TIMEPOINTS, within=Reals)

    # System
    model.Flexible_Load = Var(model.GEOGRAPHIES, model.TIMEPOINTS, model.FEEDERS, within=Reals)
    model.Cumulative_Flexible_Load = Var(model.GEOGRAPHIES, model.TIMEPOINTS, model.FEEDERS, within=Reals)
    model.DistSysCapacityNeed = Var(model.GEOGRAPHIES, model.FEEDERS, within=NonNegativeReals)
    model.BulkSysCapacityNeed = Var(model.GEOGRAPHIES, within=NonNegativeReals)
    model.FlexLoadUse = Var(model.GEOGRAPHIES, model.TIMEPOINTS, model.FEEDERS, within=NonNegativeReals)
    model.Curtailment = Var(model.GEOGRAPHIES, model.TIMEPOINTS, within=NonNegativeReals)
    model.Unserved_Energy = Var(model.GEOGRAPHIES, model.TIMEPOINTS, within=NonNegativeReals)
    model.Unserved_Capacity = Var(model.GEOGRAPHIES, within=NonNegativeReals)
    ##############################
    # ### Objective function ### #
    ##############################
    model.Total_Cost = Objective(rule=total_cost_rule, sense=minimize)

    #######################
    # ### Constraints ### #
    #######################
    # ### Meet load constraint ### #
    model.Meet_Load_Constraint = Constraint(model.GEOGRAPHIES, model.TIMEPOINTS, rule=meet_load_rule)

    # ### Project constraints ### #
    # "Gas"
    model.Power_Constraint = Constraint(model.TECHNOLOGIES, model.TIMEPOINTS, rule=power_rule)
    model.Storage_Power_Constraint = Constraint(model.STORAGE_TECHNOLOGIES, model.TIMEPOINTS, rule=storage_power_rule)
    model.Generation_Power_Constraint = Constraint(model.GENERATION_TECHNOLOGIES, model.TIMEPOINTS, rule=generation_power_rule)
    model.LD_Power_Constraint = Constraint(model.LD_TECHNOLOGIES, model.TIMEPOINTS, rule=ld_power_rule)

    # Storage
    model.Storage_Charge_Constraint = Constraint(model.STORAGE_TECHNOLOGIES, model.TIMEPOINTS, rule=storage_charge_rule)
    model.Storage_Energy_Constraint = Constraint(model.STORAGE_TECHNOLOGIES, model.TIMEPOINTS, rule=storage_energy_rule)
#    model.Storage_Simultaenous_Constraint = Constraint(model.STORAGE_TECHNOLOGIES, model.TIMEPOINTS, rule=storage_simultaneous_rule)
    model.Storage_Energy_Tracking_Constraint = Constraint(model.STORAGE_TECHNOLOGIES, model.TIMEPOINTS, rule=storage_energy_tracking_rule)
    model.Large_Storage_End_State_of_Charge_Constraint = Constraint(model.STORAGE_TECHNOLOGIES, model.TIMEPOINTS, rule=large_storage_end_state_of_charge_rule)
    
    # Flex loads
    model.Cumulative_Flex_Load_Tracking_Constraint = Constraint(model.GEOGRAPHIES, model.TIMEPOINTS, model.FEEDERS, rule=cumulative_flex_load_tracking_rule)
    model.Cumulative_Flexible_Load_Constraint = Constraint(model.GEOGRAPHIES, model.TIMEPOINTS, model.FEEDERS, rule=cumulative_flexible_load_rule)
    if dispatch.has_flexible_load:
        model.Flex_Load_Capacity_Constraint = Constraint(model.GEOGRAPHIES, model.TIMEPOINTS, model.FEEDERS, rule=flex_load_capacity_rule)
    else:
        model.Flex_Load_Capacity_Constraint = Constraint(model.GEOGRAPHIES, model.TIMEPOINTS, model.FEEDERS, rule=zero_flexible_load)
    
    #ld_energy
    model.LD_Energy_Constraint = Constraint(model.LD_TECHNOLOGIES, rule=ld_energy_rule)
    # Transmission
    model.Transmission_Constraint = Constraint(model.TRANSMISSION_LINES, model.TIMEPOINTS, rule=transmission_rule)
    model.Net_Transmit_Power_by_Geo_Constraint = Constraint(model.GEOGRAPHIES, model.TIMEPOINTS, rule=net_transmit_power_by_geo_rule)

    # Distribution system penalty
    model.Distribution_System_Penalty_Constraint = Constraint(model.GEOGRAPHIES, model.TIMEPOINTS, model.FEEDERS, rule=dist_system_capacity_need_rule)
    
    # flexible load usage penalty
    model.Flex_Load_Penalty_Constraint = Constraint(model.GEOGRAPHIES, model.TIMEPOINTS, model.FEEDERS, rule=flex_load_use_rule)

    # Bulk system capacity penalty
    model.Bulk_System_Penalty_Constraint = Constraint(model.GEOGRAPHIES, model.TIMEPOINTS, rule=bulk_system_capacity_need_rule)
    model.Unserved_Capacity_Penalty_Constraint = Constraint(model.GEOGRAPHIES, model.TIMEPOINTS, rule=unserved_capacity_rule)
#    model.Unserved_Energy_Constraint = Constraint(model.GEOGRAPHIES, model.TIMEPOINTS, rule=unserved_energy_rule)
    return model
