#
# This is a generated file. Manual edits may be lost!
#
from energyPATHWAYS.data_object import DataObject

class BlendNodeBlendMeasures(DataObject):
    def __init__(self, id=None, name=None, blend_node_id=None, supply_node_id=None, geography_id=None,
                 other_index_1_id=None, interpolation_method_id=None, extrapolation_method_id=None,
                 extrapolation_growth=None):
        DataObject.__init__(self)

        self.id = id
        self.name = name
        self.blend_node_id = blend_node_id
        self.supply_node_id = supply_node_id
        self.geography_id = geography_id
        self.other_index_1_id = other_index_1_id
        self.interpolation_method_id = interpolation_method_id
        self.extrapolation_method_id = extrapolation_method_id
        self.extrapolation_growth = extrapolation_growth

    @classmethod
    def from_tuple(cls, tup):    
        (id, name, blend_node_id, supply_node_id, geography_id, other_index_1_id,
         interpolation_method_id, extrapolation_method_id, extrapolation_growth) = tup
        
        obj = cls(id=id, name=name, blend_node_id=blend_node_id, supply_node_id=supply_node_id,
                  geography_id=geography_id, other_index_1_id=other_index_1_id,
                  interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth)
        
        return obj

class BlendNodeBlendMeasuresData(DataObject):
    def __init__(self, parent_id=None, gau_id=None, year=None, value=None, id=None, demand_sector_id=None):
        DataObject.__init__(self)

        self.parent_id = parent_id
        self.gau_id = gau_id
        self.year = year
        self.value = value
        self.id = id
        self.demand_sector_id = demand_sector_id

    @classmethod
    def from_tuple(cls, tup):    
        (parent_id, gau_id, year, value, id, demand_sector_id) = tup
        
        obj = cls(parent_id=parent_id, gau_id=gau_id, year=year, value=value, id=id,
                  demand_sector_id=demand_sector_id)
        
        return obj

class BlendNodeInputsData(DataObject):
    def __init__(self, blend_node_id=None, supply_node_id=None, id=None):
        DataObject.__init__(self)

        self.blend_node_id = blend_node_id
        self.supply_node_id = supply_node_id
        self.id = id

    @classmethod
    def from_tuple(cls, tup):    
        (blend_node_id, supply_node_id, id) = tup
        
        obj = cls(blend_node_id=blend_node_id, supply_node_id=supply_node_id, id=id)
        
        return obj

class CO2PriceMeasures(DataObject):
    def __init__(self, id=None, name=None, geography_id=None, interpolation_method_id=None,
                 extrapolation_method_id=None, extrapolation_growth=None, geography_map_key_id=None,
                 supply_node_id=None):
        DataObject.__init__(self)

        self.id = id
        self.name = name
        self.geography_id = geography_id
        self.interpolation_method_id = interpolation_method_id
        self.extrapolation_method_id = extrapolation_method_id
        self.extrapolation_growth = extrapolation_growth
        self.geography_map_key_id = geography_map_key_id
        self.supply_node_id = supply_node_id

    @classmethod
    def from_tuple(cls, tup):    
        (id, name, geography_id, interpolation_method_id, extrapolation_method_id,
         extrapolation_growth, geography_map_key_id, supply_node_id) = tup
        
        obj = cls(id=id, name=name, geography_id=geography_id,
                  interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth, geography_map_key_id=geography_map_key_id,
                  supply_node_id=supply_node_id)
        
        return obj

class CO2PriceMeasuresData(DataObject):
    def __init__(self, parent_id=None, gau_id=None, year=None, value=None, id=None, sensitivity=None):
        DataObject.__init__(self)

        self.parent_id = parent_id
        self.gau_id = gau_id
        self.year = year
        self.value = value
        self.id = id
        self.sensitivity = sensitivity

    @classmethod
    def from_tuple(cls, tup):    
        (parent_id, gau_id, year, value, id, sensitivity) = tup
        
        obj = cls(parent_id=parent_id, gau_id=gau_id, year=year, value=value, id=id, sensitivity=sensitivity)
        
        return obj

class DemandCO2CaptureMeasures(DataObject):
    def __init__(self, id=None, name=None, subsector_id=None, input_type_id=None, unit=None, geography_id=None,
                 other_index_1_id=None, other_index_2_id=None, interpolation_method_id=None,
                 extrapolation_method_id=None, extrapolation_growth=None, stock_decay_function_id=None,
                 min_lifetime=None, max_lifetime=None, mean_lifetime=None, lifetime_variance=None):
        DataObject.__init__(self)

        self.id = id
        self.name = name
        self.subsector_id = subsector_id
        self.input_type_id = input_type_id
        self.unit = unit
        self.geography_id = geography_id
        self.other_index_1_id = other_index_1_id
        self.other_index_2_id = other_index_2_id
        self.interpolation_method_id = interpolation_method_id
        self.extrapolation_method_id = extrapolation_method_id
        self.extrapolation_growth = extrapolation_growth
        self.stock_decay_function_id = stock_decay_function_id
        self.min_lifetime = min_lifetime
        self.max_lifetime = max_lifetime
        self.mean_lifetime = mean_lifetime
        self.lifetime_variance = lifetime_variance

    @classmethod
    def from_tuple(cls, tup):    
        (id, name, subsector_id, input_type_id, unit, geography_id, other_index_1_id,
         other_index_2_id, interpolation_method_id, extrapolation_method_id, extrapolation_growth,
         stock_decay_function_id, min_lifetime, max_lifetime, mean_lifetime, lifetime_variance) = tup
        
        obj = cls(id=id, name=name, subsector_id=subsector_id, input_type_id=input_type_id, unit=unit,
                  geography_id=geography_id, other_index_1_id=other_index_1_id,
                  other_index_2_id=other_index_2_id, interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth,
                  stock_decay_function_id=stock_decay_function_id, min_lifetime=min_lifetime,
                  max_lifetime=max_lifetime, mean_lifetime=mean_lifetime,
                  lifetime_variance=lifetime_variance)
        
        return obj

class DemandDrivers(DataObject):
    def __init__(self, id=None, name=None, base_driver_id=None, input_type_id=None, unit_prefix=None,
                 unit_base=None, geography_id=None, other_index_1_id=None, other_index_2_id=None,
                 geography_map_key_id=None, interpolation_method_id=None, extrapolation_method_id=None,
                 extrapolation_growth=None, source=None):
        DataObject.__init__(self)

        self.id = id
        self.name = name
        self.base_driver_id = base_driver_id
        self.input_type_id = input_type_id
        self.unit_prefix = unit_prefix
        self.unit_base = unit_base
        self.geography_id = geography_id
        self.other_index_1_id = other_index_1_id
        self.other_index_2_id = other_index_2_id
        self.geography_map_key_id = geography_map_key_id
        self.interpolation_method_id = interpolation_method_id
        self.extrapolation_method_id = extrapolation_method_id
        self.extrapolation_growth = extrapolation_growth
        self.source = source

    @classmethod
    def from_tuple(cls, tup):    
        (id, name, base_driver_id, input_type_id, unit_prefix, unit_base, geography_id,
         other_index_1_id, other_index_2_id, geography_map_key_id, interpolation_method_id,
         extrapolation_method_id, extrapolation_growth, source) = tup
        
        obj = cls(id=id, name=name, base_driver_id=base_driver_id, input_type_id=input_type_id,
                  unit_prefix=unit_prefix, unit_base=unit_base, geography_id=geography_id,
                  other_index_1_id=other_index_1_id, other_index_2_id=other_index_2_id,
                  geography_map_key_id=geography_map_key_id,
                  interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth, source=source)
        
        return obj

class DemandDriversData(DataObject):
    def __init__(self, parent_id=None, gau_id=None, oth_1_id=None, oth_2_id=None, year=None, value=None, id=None,
                 sensitivity=None):
        DataObject.__init__(self)

        self.parent_id = parent_id
        self.gau_id = gau_id
        self.oth_1_id = oth_1_id
        self.oth_2_id = oth_2_id
        self.year = year
        self.value = value
        self.id = id
        self.sensitivity = sensitivity

    @classmethod
    def from_tuple(cls, tup):    
        (parent_id, gau_id, oth_1_id, oth_2_id, year, value, id, sensitivity) = tup
        
        obj = cls(parent_id=parent_id, gau_id=gau_id, oth_1_id=oth_1_id, oth_2_id=oth_2_id, year=year,
                  value=value, id=id, sensitivity=sensitivity)
        
        return obj

class DemandEnergyDemands(DataObject):
    def __init__(self, subsector_id=None, is_stock_dependent=None, input_type_id=None, unit=None,
                 driver_denominator_1_id=None, driver_denominator_2_id=None, driver_1_id=None,
                 driver_2_id=None, geography_id=None, final_energy_index=None,
                 demand_technology_index=None, other_index_1_id=None, other_index_2_id=None,
                 interpolation_method_id=None, extrapolation_method_id=None, extrapolation_growth=None,
                 geography_map_key_id=None):
        DataObject.__init__(self)

        self.subsector_id = subsector_id
        self.is_stock_dependent = is_stock_dependent
        self.input_type_id = input_type_id
        self.unit = unit
        self.driver_denominator_1_id = driver_denominator_1_id
        self.driver_denominator_2_id = driver_denominator_2_id
        self.driver_1_id = driver_1_id
        self.driver_2_id = driver_2_id
        self.geography_id = geography_id
        self.final_energy_index = final_energy_index
        self.demand_technology_index = demand_technology_index
        self.other_index_1_id = other_index_1_id
        self.other_index_2_id = other_index_2_id
        self.interpolation_method_id = interpolation_method_id
        self.extrapolation_method_id = extrapolation_method_id
        self.extrapolation_growth = extrapolation_growth
        self.geography_map_key_id = geography_map_key_id

    @classmethod
    def from_tuple(cls, tup):    
        (subsector_id, is_stock_dependent, input_type_id, unit, driver_denominator_1_id,
         driver_denominator_2_id, driver_1_id, driver_2_id, geography_id, final_energy_index,
         demand_technology_index, other_index_1_id, other_index_2_id, interpolation_method_id,
         extrapolation_method_id, extrapolation_growth, geography_map_key_id) = tup
        
        obj = cls(subsector_id=subsector_id, is_stock_dependent=is_stock_dependent,
                  input_type_id=input_type_id, unit=unit, driver_denominator_1_id=driver_denominator_1_id,
                  driver_denominator_2_id=driver_denominator_2_id, driver_1_id=driver_1_id,
                  driver_2_id=driver_2_id, geography_id=geography_id,
                  final_energy_index=final_energy_index, demand_technology_index=demand_technology_index,
                  other_index_1_id=other_index_1_id, other_index_2_id=other_index_2_id,
                  interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth, geography_map_key_id=geography_map_key_id)
        
        return obj

class DemandEnergyDemandsData(DataObject):
    def __init__(self, subsector_id=None, gau_id=None, oth_1_id=None, oth_2_id=None, final_energy_id=None,
                 demand_technology_id=None, year=None, value=None, id=None, sensitivity=None):
        DataObject.__init__(self)

        self.subsector_id = subsector_id
        self.gau_id = gau_id
        self.oth_1_id = oth_1_id
        self.oth_2_id = oth_2_id
        self.final_energy_id = final_energy_id
        self.demand_technology_id = demand_technology_id
        self.year = year
        self.value = value
        self.id = id
        self.sensitivity = sensitivity

    @classmethod
    def from_tuple(cls, tup):    
        (subsector_id, gau_id, oth_1_id, oth_2_id, final_energy_id, demand_technology_id, year,
         value, id, sensitivity) = tup
        
        obj = cls(subsector_id=subsector_id, gau_id=gau_id, oth_1_id=oth_1_id, oth_2_id=oth_2_id,
                  final_energy_id=final_energy_id, demand_technology_id=demand_technology_id, year=year,
                  value=value, id=id, sensitivity=sensitivity)
        
        return obj

class DemandEnergyEfficiencyMeasures(DataObject):
    def __init__(self, id=None, name=None, subsector_id=None, input_type_id=None, unit=None, geography_id=None,
                 other_index_1_id=None, other_index_2_id=None, interpolation_method_id=None,
                 extrapolation_method_id=None, extrapolation_growth=None, stock_decay_function_id=None,
                 min_lifetime=None, max_lifetime=None, mean_lifetime=None, lifetime_variance=None):
        DataObject.__init__(self)

        self.id = id
        self.name = name
        self.subsector_id = subsector_id
        self.input_type_id = input_type_id
        self.unit = unit
        self.geography_id = geography_id
        self.other_index_1_id = other_index_1_id
        self.other_index_2_id = other_index_2_id
        self.interpolation_method_id = interpolation_method_id
        self.extrapolation_method_id = extrapolation_method_id
        self.extrapolation_growth = extrapolation_growth
        self.stock_decay_function_id = stock_decay_function_id
        self.min_lifetime = min_lifetime
        self.max_lifetime = max_lifetime
        self.mean_lifetime = mean_lifetime
        self.lifetime_variance = lifetime_variance

    @classmethod
    def from_tuple(cls, tup):    
        (id, name, subsector_id, input_type_id, unit, geography_id, other_index_1_id,
         other_index_2_id, interpolation_method_id, extrapolation_method_id, extrapolation_growth,
         stock_decay_function_id, min_lifetime, max_lifetime, mean_lifetime, lifetime_variance) = tup
        
        obj = cls(id=id, name=name, subsector_id=subsector_id, input_type_id=input_type_id, unit=unit,
                  geography_id=geography_id, other_index_1_id=other_index_1_id,
                  other_index_2_id=other_index_2_id, interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth,
                  stock_decay_function_id=stock_decay_function_id, min_lifetime=min_lifetime,
                  max_lifetime=max_lifetime, mean_lifetime=mean_lifetime,
                  lifetime_variance=lifetime_variance)
        
        return obj

class DemandEnergyEfficiencyMeasuresCost(DataObject):
    def __init__(self, parent_id=None, currency_id=None, currency_year_id=None, cost_denominator_unit=None,
                 cost_of_capital=None, is_levelized=None, geography_id=None, other_index_1_id=None,
                 other_index_2_id=None, interpolation_method_id=None, extrapolation_method_id=None,
                 extrapolation_growth=None):
        DataObject.__init__(self)

        self.parent_id = parent_id
        self.currency_id = currency_id
        self.currency_year_id = currency_year_id
        self.cost_denominator_unit = cost_denominator_unit
        self.cost_of_capital = cost_of_capital
        self.is_levelized = is_levelized
        self.geography_id = geography_id
        self.other_index_1_id = other_index_1_id
        self.other_index_2_id = other_index_2_id
        self.interpolation_method_id = interpolation_method_id
        self.extrapolation_method_id = extrapolation_method_id
        self.extrapolation_growth = extrapolation_growth

    @classmethod
    def from_tuple(cls, tup):    
        (parent_id, currency_id, currency_year_id, cost_denominator_unit, cost_of_capital,
         is_levelized, geography_id, other_index_1_id, other_index_2_id, interpolation_method_id,
         extrapolation_method_id, extrapolation_growth) = tup
        
        obj = cls(parent_id=parent_id, currency_id=currency_id, currency_year_id=currency_year_id,
                  cost_denominator_unit=cost_denominator_unit, cost_of_capital=cost_of_capital,
                  is_levelized=is_levelized, geography_id=geography_id, other_index_1_id=other_index_1_id,
                  other_index_2_id=other_index_2_id, interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth)
        
        return obj

class DemandEnergyEfficiencyMeasuresCostData(DataObject):
    def __init__(self, parent_id=None, gau_id=None, oth_1_id=None, oth_2_id=None, vintage=None, value=None,
                 id=None, final_energy_id=None):
        DataObject.__init__(self)

        self.parent_id = parent_id
        self.gau_id = gau_id
        self.oth_1_id = oth_1_id
        self.oth_2_id = oth_2_id
        self.vintage = vintage
        self.value = value
        self.id = id
        self.final_energy_id = final_energy_id

    @classmethod
    def from_tuple(cls, tup):    
        (parent_id, gau_id, oth_1_id, oth_2_id, vintage, value, id, final_energy_id) = tup
        
        obj = cls(parent_id=parent_id, gau_id=gau_id, oth_1_id=oth_1_id, oth_2_id=oth_2_id, vintage=vintage,
                  value=value, id=id, final_energy_id=final_energy_id)
        
        return obj

class DemandEnergyEfficiencyMeasuresData(DataObject):
    def __init__(self, parent_id=None, final_energy_id=None, gau_id=None, oth_1_id=None, oth_2_id=None,
                 year=None, value=None, id=None):
        DataObject.__init__(self)

        self.parent_id = parent_id
        self.final_energy_id = final_energy_id
        self.gau_id = gau_id
        self.oth_1_id = oth_1_id
        self.oth_2_id = oth_2_id
        self.year = year
        self.value = value
        self.id = id

    @classmethod
    def from_tuple(cls, tup):    
        (parent_id, final_energy_id, gau_id, oth_1_id, oth_2_id, year, value, id) = tup
        
        obj = cls(parent_id=parent_id, final_energy_id=final_energy_id, gau_id=gau_id, oth_1_id=oth_1_id,
                  oth_2_id=oth_2_id, year=year, value=value, id=id)
        
        return obj

class DemandFlexibleLoadMeasures(DataObject):
    def __init__(self, id=None, subsector_id=None, geography_id=None, other_index_1_id=None,
                 interpolation_method_id=None, extrapolation_method_id=None, extrapolation_growth=None,
                 name=None):
        DataObject.__init__(self)

        self.id = id
        self.subsector_id = subsector_id
        self.geography_id = geography_id
        self.other_index_1_id = other_index_1_id
        self.interpolation_method_id = interpolation_method_id
        self.extrapolation_method_id = extrapolation_method_id
        self.extrapolation_growth = extrapolation_growth
        self.name = name

    @classmethod
    def from_tuple(cls, tup):    
        (id, subsector_id, geography_id, other_index_1_id, interpolation_method_id,
         extrapolation_method_id, extrapolation_growth, name) = tup
        
        obj = cls(id=id, subsector_id=subsector_id, geography_id=geography_id,
                  other_index_1_id=other_index_1_id, interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth, name=name)
        
        return obj

class DemandFlexibleLoadMeasuresData(DataObject):
    def __init__(self, parent_id=None, gau_id=None, oth_1_id=None, year=None, value=None, id=None):
        DataObject.__init__(self)

        self.parent_id = parent_id
        self.gau_id = gau_id
        self.oth_1_id = oth_1_id
        self.year = year
        self.value = value
        self.id = id

    @classmethod
    def from_tuple(cls, tup):    
        (parent_id, gau_id, oth_1_id, year, value, id) = tup
        
        obj = cls(parent_id=parent_id, gau_id=gau_id, oth_1_id=oth_1_id, year=year, value=value, id=id)
        
        return obj

class DemandFuelSwitchingMeasures(DataObject):
    def __init__(self, id=None, name=None, subsector_id=None, final_energy_from_id=None, final_energy_to_id=None,
                 stock_decay_function_id=None, max_lifetime=None, min_lifetime=None, mean_lifetime=None,
                 lifetime_variance=None):
        DataObject.__init__(self)

        self.id = id
        self.name = name
        self.subsector_id = subsector_id
        self.final_energy_from_id = final_energy_from_id
        self.final_energy_to_id = final_energy_to_id
        self.stock_decay_function_id = stock_decay_function_id
        self.max_lifetime = max_lifetime
        self.min_lifetime = min_lifetime
        self.mean_lifetime = mean_lifetime
        self.lifetime_variance = lifetime_variance

    @classmethod
    def from_tuple(cls, tup):    
        (id, name, subsector_id, final_energy_from_id, final_energy_to_id, stock_decay_function_id,
         max_lifetime, min_lifetime, mean_lifetime, lifetime_variance) = tup
        
        obj = cls(id=id, name=name, subsector_id=subsector_id, final_energy_from_id=final_energy_from_id,
                  final_energy_to_id=final_energy_to_id, stock_decay_function_id=stock_decay_function_id,
                  max_lifetime=max_lifetime, min_lifetime=min_lifetime, mean_lifetime=mean_lifetime,
                  lifetime_variance=lifetime_variance)
        
        return obj

class DemandFuelSwitchingMeasuresCost(DataObject):
    def __init__(self, parent_id=None, currency_id=None, currency_year_id=None, cost_denominator_unit=None,
                 cost_of_capital=None, is_levelized=None, geography_id=None, other_index_1_id=None,
                 other_index_2_id=None, interpolation_method_id=None, extrapolation_method_id=None,
                 extrapolation_growth=None):
        DataObject.__init__(self)

        self.parent_id = parent_id
        self.currency_id = currency_id
        self.currency_year_id = currency_year_id
        self.cost_denominator_unit = cost_denominator_unit
        self.cost_of_capital = cost_of_capital
        self.is_levelized = is_levelized
        self.geography_id = geography_id
        self.other_index_1_id = other_index_1_id
        self.other_index_2_id = other_index_2_id
        self.interpolation_method_id = interpolation_method_id
        self.extrapolation_method_id = extrapolation_method_id
        self.extrapolation_growth = extrapolation_growth

    @classmethod
    def from_tuple(cls, tup):    
        (parent_id, currency_id, currency_year_id, cost_denominator_unit, cost_of_capital,
         is_levelized, geography_id, other_index_1_id, other_index_2_id, interpolation_method_id,
         extrapolation_method_id, extrapolation_growth) = tup
        
        obj = cls(parent_id=parent_id, currency_id=currency_id, currency_year_id=currency_year_id,
                  cost_denominator_unit=cost_denominator_unit, cost_of_capital=cost_of_capital,
                  is_levelized=is_levelized, geography_id=geography_id, other_index_1_id=other_index_1_id,
                  other_index_2_id=other_index_2_id, interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth)
        
        return obj

class DemandFuelSwitchingMeasuresCostData(DataObject):
    def __init__(self, parent_id=None, gau_id=None, oth_1_id=None, oth_2_id=None, vintage=None, value=None,
                 id=None):
        DataObject.__init__(self)

        self.parent_id = parent_id
        self.gau_id = gau_id
        self.oth_1_id = oth_1_id
        self.oth_2_id = oth_2_id
        self.vintage = vintage
        self.value = value
        self.id = id

    @classmethod
    def from_tuple(cls, tup):    
        (parent_id, gau_id, oth_1_id, oth_2_id, vintage, value, id) = tup
        
        obj = cls(parent_id=parent_id, gau_id=gau_id, oth_1_id=oth_1_id, oth_2_id=oth_2_id, vintage=vintage,
                  value=value, id=id)
        
        return obj

class DemandFuelSwitchingMeasuresEnergyIntensity(DataObject):
    def __init__(self, parent_id=None, geography_id=None, other_index_1_id=None, other_index_2_id=None,
                 interpolation_method_id=None, extrapolation_method_id=None, extrapolation_growth=None):
        DataObject.__init__(self)

        self.parent_id = parent_id
        self.geography_id = geography_id
        self.other_index_1_id = other_index_1_id
        self.other_index_2_id = other_index_2_id
        self.interpolation_method_id = interpolation_method_id
        self.extrapolation_method_id = extrapolation_method_id
        self.extrapolation_growth = extrapolation_growth

    @classmethod
    def from_tuple(cls, tup):    
        (parent_id, geography_id, other_index_1_id, other_index_2_id, interpolation_method_id,
         extrapolation_method_id, extrapolation_growth) = tup
        
        obj = cls(parent_id=parent_id, geography_id=geography_id, other_index_1_id=other_index_1_id,
                  other_index_2_id=other_index_2_id, interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth)
        
        return obj

class DemandFuelSwitchingMeasuresEnergyIntensityData(DataObject):
    def __init__(self, parent_id=None, gau_id=None, oth_1_id=None, oth_2_id=None, year=None, value=None, id=None):
        DataObject.__init__(self)

        self.parent_id = parent_id
        self.gau_id = gau_id
        self.oth_1_id = oth_1_id
        self.oth_2_id = oth_2_id
        self.year = year
        self.value = value
        self.id = id

    @classmethod
    def from_tuple(cls, tup):    
        (parent_id, gau_id, oth_1_id, oth_2_id, year, value, id) = tup
        
        obj = cls(parent_id=parent_id, gau_id=gau_id, oth_1_id=oth_1_id, oth_2_id=oth_2_id, year=year,
                  value=value, id=id)
        
        return obj

class DemandFuelSwitchingMeasuresImpact(DataObject):
    def __init__(self, parent_id=None, input_type_id=None, unit=None, geography_id=None, other_index_1_id=None,
                 other_index_2_id=None, interpolation_method_id=None, extrapolation_method_id=None,
                 extrapolation_growth=None):
        DataObject.__init__(self)

        self.parent_id = parent_id
        self.input_type_id = input_type_id
        self.unit = unit
        self.geography_id = geography_id
        self.other_index_1_id = other_index_1_id
        self.other_index_2_id = other_index_2_id
        self.interpolation_method_id = interpolation_method_id
        self.extrapolation_method_id = extrapolation_method_id
        self.extrapolation_growth = extrapolation_growth

    @classmethod
    def from_tuple(cls, tup):    
        (parent_id, input_type_id, unit, geography_id, other_index_1_id, other_index_2_id,
         interpolation_method_id, extrapolation_method_id, extrapolation_growth) = tup
        
        obj = cls(parent_id=parent_id, input_type_id=input_type_id, unit=unit, geography_id=geography_id,
                  other_index_1_id=other_index_1_id, other_index_2_id=other_index_2_id,
                  interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth)
        
        return obj

class DemandFuelSwitchingMeasuresImpactData(DataObject):
    def __init__(self, parent_id=None, gau_id=None, oth_1_id=None, oth_2_id=None, year=None, value=None, id=None):
        DataObject.__init__(self)

        self.parent_id = parent_id
        self.gau_id = gau_id
        self.oth_1_id = oth_1_id
        self.oth_2_id = oth_2_id
        self.year = year
        self.value = value
        self.id = id

    @classmethod
    def from_tuple(cls, tup):    
        (parent_id, gau_id, oth_1_id, oth_2_id, year, value, id) = tup
        
        obj = cls(parent_id=parent_id, gau_id=gau_id, oth_1_id=oth_1_id, oth_2_id=oth_2_id, year=year,
                  value=value, id=id)
        
        return obj

class DemandSales(DataObject):
    def __init__(self, subsector_id=None, geography_id=None, other_index_1_id=None, other_index_2_id=None,
                 input_type_id=None, interpolation_method_id=None, extrapolation_method_id=None,
                 extrapolation_growth=None):
        DataObject.__init__(self)

        self.subsector_id = subsector_id
        self.geography_id = geography_id
        self.other_index_1_id = other_index_1_id
        self.other_index_2_id = other_index_2_id
        self.input_type_id = input_type_id
        self.interpolation_method_id = interpolation_method_id
        self.extrapolation_method_id = extrapolation_method_id
        self.extrapolation_growth = extrapolation_growth

    @classmethod
    def from_tuple(cls, tup):    
        (subsector_id, geography_id, other_index_1_id, other_index_2_id, input_type_id,
         interpolation_method_id, extrapolation_method_id, extrapolation_growth) = tup
        
        obj = cls(subsector_id=subsector_id, geography_id=geography_id, other_index_1_id=other_index_1_id,
                  other_index_2_id=other_index_2_id, input_type_id=input_type_id,
                  interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth)
        
        return obj

class DemandSalesData(DataObject):
    def __init__(self, subsector_id=None, gau_id=None, oth_1_id=None, oth_2_id=None, demand_technology_id=None,
                 vintage=None, value=None, id=None):
        DataObject.__init__(self)

        self.subsector_id = subsector_id
        self.gau_id = gau_id
        self.oth_1_id = oth_1_id
        self.oth_2_id = oth_2_id
        self.demand_technology_id = demand_technology_id
        self.vintage = vintage
        self.value = value
        self.id = id

    @classmethod
    def from_tuple(cls, tup):    
        (subsector_id, gau_id, oth_1_id, oth_2_id, demand_technology_id, vintage, value, id) = tup
        
        obj = cls(subsector_id=subsector_id, gau_id=gau_id, oth_1_id=oth_1_id, oth_2_id=oth_2_id,
                  demand_technology_id=demand_technology_id, vintage=vintage, value=value, id=id)
        
        return obj

class DemandSalesShareMeasures(DataObject):
    def __init__(self, id=None, subsector_id=None, geography_id=None, other_index_1_id=None,
                 demand_technology_id=None, replaced_demand_tech_id=None, input_type_id=None,
                 interpolation_method_id=None, extrapolation_method_id=None, extrapolation_growth=None,
                 name=None):
        DataObject.__init__(self)

        self.id = id
        self.subsector_id = subsector_id
        self.geography_id = geography_id
        self.other_index_1_id = other_index_1_id
        self.demand_technology_id = demand_technology_id
        self.replaced_demand_tech_id = replaced_demand_tech_id
        self.input_type_id = input_type_id
        self.interpolation_method_id = interpolation_method_id
        self.extrapolation_method_id = extrapolation_method_id
        self.extrapolation_growth = extrapolation_growth
        self.name = name

    @classmethod
    def from_tuple(cls, tup):    
        (id, subsector_id, geography_id, other_index_1_id, demand_technology_id,
         replaced_demand_tech_id, input_type_id, interpolation_method_id, extrapolation_method_id,
         extrapolation_growth, name) = tup
        
        obj = cls(id=id, subsector_id=subsector_id, geography_id=geography_id,
                  other_index_1_id=other_index_1_id, demand_technology_id=demand_technology_id,
                  replaced_demand_tech_id=replaced_demand_tech_id, input_type_id=input_type_id,
                  interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth, name=name)
        
        return obj

class DemandSalesShareMeasuresData(DataObject):
    def __init__(self, parent_id=None, gau_id=None, oth_1_id=None, vintage=None, value=None, id=None):
        DataObject.__init__(self)

        self.parent_id = parent_id
        self.gau_id = gau_id
        self.oth_1_id = oth_1_id
        self.vintage = vintage
        self.value = value
        self.id = id

    @classmethod
    def from_tuple(cls, tup):    
        (parent_id, gau_id, oth_1_id, vintage, value, id) = tup
        
        obj = cls(parent_id=parent_id, gau_id=gau_id, oth_1_id=oth_1_id, vintage=vintage, value=value, id=id)
        
        return obj

class DemandSectors(DataObject):
    def __init__(self, id=None, name=None, shape_id=None, max_lead_hours=None, max_lag_hours=None):
        DataObject.__init__(self)

        self.id = id
        self.name = name
        self.shape_id = shape_id
        self.max_lead_hours = max_lead_hours
        self.max_lag_hours = max_lag_hours

    @classmethod
    def from_tuple(cls, tup):    
        (id, name, shape_id, max_lead_hours, max_lag_hours) = tup
        
        obj = cls(id=id, name=name, shape_id=shape_id, max_lead_hours=max_lead_hours,
                  max_lag_hours=max_lag_hours)
        
        return obj

class DemandServiceDemandMeasures(DataObject):
    def __init__(self, id=None, name=None, subsector_id=None, input_type_id=None, unit=None, geography_id=None,
                 other_index_1_id=None, other_index_2_id=None, interpolation_method_id=None,
                 extrapolation_method_id=None, extrapolation_growth=None, stock_decay_function_id=None,
                 min_lifetime=None, max_lifetime=None, mean_lifetime=None, lifetime_variance=None):
        DataObject.__init__(self)

        self.id = id
        self.name = name
        self.subsector_id = subsector_id
        self.input_type_id = input_type_id
        self.unit = unit
        self.geography_id = geography_id
        self.other_index_1_id = other_index_1_id
        self.other_index_2_id = other_index_2_id
        self.interpolation_method_id = interpolation_method_id
        self.extrapolation_method_id = extrapolation_method_id
        self.extrapolation_growth = extrapolation_growth
        self.stock_decay_function_id = stock_decay_function_id
        self.min_lifetime = min_lifetime
        self.max_lifetime = max_lifetime
        self.mean_lifetime = mean_lifetime
        self.lifetime_variance = lifetime_variance

    @classmethod
    def from_tuple(cls, tup):    
        (id, name, subsector_id, input_type_id, unit, geography_id, other_index_1_id,
         other_index_2_id, interpolation_method_id, extrapolation_method_id, extrapolation_growth,
         stock_decay_function_id, min_lifetime, max_lifetime, mean_lifetime, lifetime_variance) = tup
        
        obj = cls(id=id, name=name, subsector_id=subsector_id, input_type_id=input_type_id, unit=unit,
                  geography_id=geography_id, other_index_1_id=other_index_1_id,
                  other_index_2_id=other_index_2_id, interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth,
                  stock_decay_function_id=stock_decay_function_id, min_lifetime=min_lifetime,
                  max_lifetime=max_lifetime, mean_lifetime=mean_lifetime,
                  lifetime_variance=lifetime_variance)
        
        return obj

class DemandServiceDemandMeasuresCost(DataObject):
    def __init__(self, parent_id=None, currency_id=None, currency_year_id=None, cost_denominator_unit=None,
                 cost_of_capital=None, is_levelized=None, geography_id=None, other_index_1_id=None,
                 other_index_2_id=None, interpolation_method_id=None, extrapolation_method_id=None,
                 extrapolation_growth=None):
        DataObject.__init__(self)

        self.parent_id = parent_id
        self.currency_id = currency_id
        self.currency_year_id = currency_year_id
        self.cost_denominator_unit = cost_denominator_unit
        self.cost_of_capital = cost_of_capital
        self.is_levelized = is_levelized
        self.geography_id = geography_id
        self.other_index_1_id = other_index_1_id
        self.other_index_2_id = other_index_2_id
        self.interpolation_method_id = interpolation_method_id
        self.extrapolation_method_id = extrapolation_method_id
        self.extrapolation_growth = extrapolation_growth

    @classmethod
    def from_tuple(cls, tup):    
        (parent_id, currency_id, currency_year_id, cost_denominator_unit, cost_of_capital,
         is_levelized, geography_id, other_index_1_id, other_index_2_id, interpolation_method_id,
         extrapolation_method_id, extrapolation_growth) = tup
        
        obj = cls(parent_id=parent_id, currency_id=currency_id, currency_year_id=currency_year_id,
                  cost_denominator_unit=cost_denominator_unit, cost_of_capital=cost_of_capital,
                  is_levelized=is_levelized, geography_id=geography_id, other_index_1_id=other_index_1_id,
                  other_index_2_id=other_index_2_id, interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth)
        
        return obj

class DemandServiceDemandMeasuresCostData(DataObject):
    def __init__(self, id=None, gau_id=None, oth_1_id=None, oth_2_id=None, vintage=None, value=None,
                 parent_id=None):
        DataObject.__init__(self)

        self.id = id
        self.gau_id = gau_id
        self.oth_1_id = oth_1_id
        self.oth_2_id = oth_2_id
        self.vintage = vintage
        self.value = value
        self.parent_id = parent_id

    @classmethod
    def from_tuple(cls, tup):    
        (id, gau_id, oth_1_id, oth_2_id, vintage, value, parent_id) = tup
        
        obj = cls(id=id, gau_id=gau_id, oth_1_id=oth_1_id, oth_2_id=oth_2_id, vintage=vintage, value=value,
                  parent_id=parent_id)
        
        return obj

class DemandServiceDemandMeasuresData(DataObject):
    def __init__(self, parent_id=None, gau_id=None, oth_1_id=None, oth_2_id=None, year=None, value=None, id=None):
        DataObject.__init__(self)

        self.parent_id = parent_id
        self.gau_id = gau_id
        self.oth_1_id = oth_1_id
        self.oth_2_id = oth_2_id
        self.year = year
        self.value = value
        self.id = id

    @classmethod
    def from_tuple(cls, tup):    
        (parent_id, gau_id, oth_1_id, oth_2_id, year, value, id) = tup
        
        obj = cls(parent_id=parent_id, gau_id=gau_id, oth_1_id=oth_1_id, oth_2_id=oth_2_id, year=year,
                  value=value, id=id)
        
        return obj

class DemandServiceDemands(DataObject):
    def __init__(self, subsector_id=None, is_stock_dependent=None, input_type_id=None, unit=None,
                 driver_denominator_1_id=None, driver_denominator_2_id=None, driver_1_id=None,
                 driver_2_id=None, geography_id=None, final_energy_index=None,
                 demand_technology_index=None, other_index_1_id=None, other_index_2_id=None,
                 interpolation_method_id=None, extrapolation_method_id=None, extrapolation_growth=None,
                 geography_map_key_id=None):
        DataObject.__init__(self)

        self.subsector_id = subsector_id
        self.is_stock_dependent = is_stock_dependent
        self.input_type_id = input_type_id
        self.unit = unit
        self.driver_denominator_1_id = driver_denominator_1_id
        self.driver_denominator_2_id = driver_denominator_2_id
        self.driver_1_id = driver_1_id
        self.driver_2_id = driver_2_id
        self.geography_id = geography_id
        self.final_energy_index = final_energy_index
        self.demand_technology_index = demand_technology_index
        self.other_index_1_id = other_index_1_id
        self.other_index_2_id = other_index_2_id
        self.interpolation_method_id = interpolation_method_id
        self.extrapolation_method_id = extrapolation_method_id
        self.extrapolation_growth = extrapolation_growth
        self.geography_map_key_id = geography_map_key_id

    @classmethod
    def from_tuple(cls, tup):    
        (subsector_id, is_stock_dependent, input_type_id, unit, driver_denominator_1_id,
         driver_denominator_2_id, driver_1_id, driver_2_id, geography_id, final_energy_index,
         demand_technology_index, other_index_1_id, other_index_2_id, interpolation_method_id,
         extrapolation_method_id, extrapolation_growth, geography_map_key_id) = tup
        
        obj = cls(subsector_id=subsector_id, is_stock_dependent=is_stock_dependent,
                  input_type_id=input_type_id, unit=unit, driver_denominator_1_id=driver_denominator_1_id,
                  driver_denominator_2_id=driver_denominator_2_id, driver_1_id=driver_1_id,
                  driver_2_id=driver_2_id, geography_id=geography_id,
                  final_energy_index=final_energy_index, demand_technology_index=demand_technology_index,
                  other_index_1_id=other_index_1_id, other_index_2_id=other_index_2_id,
                  interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth, geography_map_key_id=geography_map_key_id)
        
        return obj

class DemandServiceDemandsData(DataObject):
    def __init__(self, subsector_id=None, gau_id=None, final_energy_id=None, demand_technology_id=None,
                 oth_1_id=None, oth_2_id=None, year=None, value=None, id=None, sensitivity=None):
        DataObject.__init__(self)

        self.subsector_id = subsector_id
        self.gau_id = gau_id
        self.final_energy_id = final_energy_id
        self.demand_technology_id = demand_technology_id
        self.oth_1_id = oth_1_id
        self.oth_2_id = oth_2_id
        self.year = year
        self.value = value
        self.id = id
        self.sensitivity = sensitivity

    @classmethod
    def from_tuple(cls, tup):    
        (subsector_id, gau_id, final_energy_id, demand_technology_id, oth_1_id, oth_2_id, year,
         value, id, sensitivity) = tup
        
        obj = cls(subsector_id=subsector_id, gau_id=gau_id, final_energy_id=final_energy_id,
                  demand_technology_id=demand_technology_id, oth_1_id=oth_1_id, oth_2_id=oth_2_id,
                  year=year, value=value, id=id, sensitivity=sensitivity)
        
        return obj

class DemandServiceEfficiency(DataObject):
    def __init__(self, subsector_id=None, energy_unit=None, denominator_unit=None, geography_id=None,
                 other_index_1_id=None, other_index_2_id=None, interpolation_method_id=None,
                 extrapolation_method_id=None, extrapolation_growth=None, geography_map_key_id=None):
        DataObject.__init__(self)

        self.subsector_id = subsector_id
        self.energy_unit = energy_unit
        self.denominator_unit = denominator_unit
        self.geography_id = geography_id
        self.other_index_1_id = other_index_1_id
        self.other_index_2_id = other_index_2_id
        self.interpolation_method_id = interpolation_method_id
        self.extrapolation_method_id = extrapolation_method_id
        self.extrapolation_growth = extrapolation_growth
        self.geography_map_key_id = geography_map_key_id

    @classmethod
    def from_tuple(cls, tup):    
        (subsector_id, energy_unit, denominator_unit, geography_id, other_index_1_id,
         other_index_2_id, interpolation_method_id, extrapolation_method_id, extrapolation_growth,
         geography_map_key_id) = tup
        
        obj = cls(subsector_id=subsector_id, energy_unit=energy_unit, denominator_unit=denominator_unit,
                  geography_id=geography_id, other_index_1_id=other_index_1_id,
                  other_index_2_id=other_index_2_id, interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth, geography_map_key_id=geography_map_key_id)
        
        return obj

class DemandServiceEfficiencyData(DataObject):
    def __init__(self, subsector_id=None, final_energy_id=None, gau_id=None, oth_1_id=None, oth_2_id=None,
                 year=None, value=None, id=None):
        DataObject.__init__(self)

        self.subsector_id = subsector_id
        self.final_energy_id = final_energy_id
        self.gau_id = gau_id
        self.oth_1_id = oth_1_id
        self.oth_2_id = oth_2_id
        self.year = year
        self.value = value
        self.id = id

    @classmethod
    def from_tuple(cls, tup):    
        (subsector_id, final_energy_id, gau_id, oth_1_id, oth_2_id, year, value, id) = tup
        
        obj = cls(subsector_id=subsector_id, final_energy_id=final_energy_id, gau_id=gau_id,
                  oth_1_id=oth_1_id, oth_2_id=oth_2_id, year=year, value=value, id=id)
        
        return obj

class DemandServiceLink(DataObject):
    def __init__(self, id=None, subsector_id=None, linked_subsector_id=None, service_demand_share=None, year=None):
        DataObject.__init__(self)

        self.id = id
        self.subsector_id = subsector_id
        self.linked_subsector_id = linked_subsector_id
        self.service_demand_share = service_demand_share
        self.year = year

    @classmethod
    def from_tuple(cls, tup):    
        (id, subsector_id, linked_subsector_id, service_demand_share, year) = tup
        
        obj = cls(id=id, subsector_id=subsector_id, linked_subsector_id=linked_subsector_id,
                  service_demand_share=service_demand_share, year=year)
        
        return obj

class DemandStock(DataObject):
    def __init__(self, subsector_id=None, is_service_demand_dependent=None, driver_denominator_1_id=None,
                 driver_denominator_2_id=None, driver_1_id=None, driver_2_id=None, geography_id=None,
                 other_index_1_id=None, other_index_2_id=None, geography_map_key_id=None,
                 input_type_id=None, demand_stock_unit_type_id=None, unit=None, time_unit=None,
                 interpolation_method_id=None, extrapolation_method_id=None, extrapolation_growth=None):
        DataObject.__init__(self)

        self.subsector_id = subsector_id
        self.is_service_demand_dependent = is_service_demand_dependent
        self.driver_denominator_1_id = driver_denominator_1_id
        self.driver_denominator_2_id = driver_denominator_2_id
        self.driver_1_id = driver_1_id
        self.driver_2_id = driver_2_id
        self.geography_id = geography_id
        self.other_index_1_id = other_index_1_id
        self.other_index_2_id = other_index_2_id
        self.geography_map_key_id = geography_map_key_id
        self.input_type_id = input_type_id
        self.demand_stock_unit_type_id = demand_stock_unit_type_id
        self.unit = unit
        self.time_unit = time_unit
        self.interpolation_method_id = interpolation_method_id
        self.extrapolation_method_id = extrapolation_method_id
        self.extrapolation_growth = extrapolation_growth

    @classmethod
    def from_tuple(cls, tup):    
        (subsector_id, is_service_demand_dependent, driver_denominator_1_id,
         driver_denominator_2_id, driver_1_id, driver_2_id, geography_id, other_index_1_id,
         other_index_2_id, geography_map_key_id, input_type_id, demand_stock_unit_type_id, unit,
         time_unit, interpolation_method_id, extrapolation_method_id, extrapolation_growth) = tup
        
        obj = cls(subsector_id=subsector_id, is_service_demand_dependent=is_service_demand_dependent,
                  driver_denominator_1_id=driver_denominator_1_id,
                  driver_denominator_2_id=driver_denominator_2_id, driver_1_id=driver_1_id,
                  driver_2_id=driver_2_id, geography_id=geography_id, other_index_1_id=other_index_1_id,
                  other_index_2_id=other_index_2_id, geography_map_key_id=geography_map_key_id,
                  input_type_id=input_type_id, demand_stock_unit_type_id=demand_stock_unit_type_id,
                  unit=unit, time_unit=time_unit, interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth)
        
        return obj

class DemandStockData(DataObject):
    def __init__(self, subsector_id=None, gau_id=None, oth_1_id=None, oth_2_id=None, demand_technology_id=None,
                 year=None, value=None, id=None):
        DataObject.__init__(self)

        self.subsector_id = subsector_id
        self.gau_id = gau_id
        self.oth_1_id = oth_1_id
        self.oth_2_id = oth_2_id
        self.demand_technology_id = demand_technology_id
        self.year = year
        self.value = value
        self.id = id

    @classmethod
    def from_tuple(cls, tup):    
        (subsector_id, gau_id, oth_1_id, oth_2_id, demand_technology_id, year, value, id) = tup
        
        obj = cls(subsector_id=subsector_id, gau_id=gau_id, oth_1_id=oth_1_id, oth_2_id=oth_2_id,
                  demand_technology_id=demand_technology_id, year=year, value=value, id=id)
        
        return obj

class DemandStockMeasures(DataObject):
    def __init__(self, id=None, subsector_id=None, geography_id=None, other_index_1_id=None,
                 demand_technology_id=None, interpolation_method_id=None, extrapolation_method_id=None,
                 extrapolation_growth=None, name=None):
        DataObject.__init__(self)

        self.id = id
        self.subsector_id = subsector_id
        self.geography_id = geography_id
        self.other_index_1_id = other_index_1_id
        self.demand_technology_id = demand_technology_id
        self.interpolation_method_id = interpolation_method_id
        self.extrapolation_method_id = extrapolation_method_id
        self.extrapolation_growth = extrapolation_growth
        self.name = name

    @classmethod
    def from_tuple(cls, tup):    
        (id, subsector_id, geography_id, other_index_1_id, demand_technology_id,
         interpolation_method_id, extrapolation_method_id, extrapolation_growth, name) = tup
        
        obj = cls(id=id, subsector_id=subsector_id, geography_id=geography_id,
                  other_index_1_id=other_index_1_id, demand_technology_id=demand_technology_id,
                  interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth, name=name)
        
        return obj

class DemandStockMeasuresData(DataObject):
    def __init__(self, parent_id=None, gau_id=None, oth_1_id=None, year=None, value=None, id=None):
        DataObject.__init__(self)

        self.parent_id = parent_id
        self.gau_id = gau_id
        self.oth_1_id = oth_1_id
        self.year = year
        self.value = value
        self.id = id

    @classmethod
    def from_tuple(cls, tup):    
        (parent_id, gau_id, oth_1_id, year, value, id) = tup
        
        obj = cls(parent_id=parent_id, gau_id=gau_id, oth_1_id=oth_1_id, year=year, value=value, id=id)
        
        return obj

class DemandSubsectors(DataObject):
    def __init__(self, id=None, sector_id=None, name=None, cost_of_capital=None, is_active=None, shape_id=None,
                 max_lead_hours=None, max_lag_hours=None):
        DataObject.__init__(self)

        self.id = id
        self.sector_id = sector_id
        self.name = name
        self.cost_of_capital = cost_of_capital
        self.is_active = is_active
        self.shape_id = shape_id
        self.max_lead_hours = max_lead_hours
        self.max_lag_hours = max_lag_hours

    @classmethod
    def from_tuple(cls, tup):    
        (id, sector_id, name, cost_of_capital, is_active, shape_id, max_lead_hours, max_lag_hours) = tup
        
        obj = cls(id=id, sector_id=sector_id, name=name, cost_of_capital=cost_of_capital,
                  is_active=is_active, shape_id=shape_id, max_lead_hours=max_lead_hours,
                  max_lag_hours=max_lag_hours)
        
        return obj

class DemandTechs(DataObject):
    def __init__(self, id=None, linked_id=None, stock_link_ratio=None, subsector_id=None, name=None,
                 min_lifetime=None, max_lifetime=None, source=None, additional_description=None,
                 demand_tech_unit_type_id=None, unit=None, time_unit=None, cost_of_capital=None,
                 stock_decay_function_id=None, mean_lifetime=None, lifetime_variance=None, shape_id=None,
                 max_lead_hours=None, max_lag_hours=None):
        DataObject.__init__(self)

        self.id = id
        self.linked_id = linked_id
        self.stock_link_ratio = stock_link_ratio
        self.subsector_id = subsector_id
        self.name = name
        self.min_lifetime = min_lifetime
        self.max_lifetime = max_lifetime
        self.source = source
        self.additional_description = additional_description
        self.demand_tech_unit_type_id = demand_tech_unit_type_id
        self.unit = unit
        self.time_unit = time_unit
        self.cost_of_capital = cost_of_capital
        self.stock_decay_function_id = stock_decay_function_id
        self.mean_lifetime = mean_lifetime
        self.lifetime_variance = lifetime_variance
        self.shape_id = shape_id
        self.max_lead_hours = max_lead_hours
        self.max_lag_hours = max_lag_hours

    @classmethod
    def from_tuple(cls, tup):    
        (id, linked_id, stock_link_ratio, subsector_id, name, min_lifetime, max_lifetime, source,
         additional_description, demand_tech_unit_type_id, unit, time_unit, cost_of_capital,
         stock_decay_function_id, mean_lifetime, lifetime_variance, shape_id, max_lead_hours,
         max_lag_hours) = tup
        
        obj = cls(id=id, linked_id=linked_id, stock_link_ratio=stock_link_ratio, subsector_id=subsector_id,
                  name=name, min_lifetime=min_lifetime, max_lifetime=max_lifetime, source=source,
                  additional_description=additional_description,
                  demand_tech_unit_type_id=demand_tech_unit_type_id, unit=unit, time_unit=time_unit,
                  cost_of_capital=cost_of_capital, stock_decay_function_id=stock_decay_function_id,
                  mean_lifetime=mean_lifetime, lifetime_variance=lifetime_variance, shape_id=shape_id,
                  max_lead_hours=max_lead_hours, max_lag_hours=max_lag_hours)
        
        return obj

class DemandTechsAuxEfficiency(DataObject):
    def __init__(self, demand_technology_id=None, definition_id=None, reference_tech_id=None, geography_id=None,
                 other_index_1_id=None, other_index_2_id=None, final_energy_id=None,
                 demand_tech_efficiency_types_id=None, is_numerator_service=None, numerator_unit=None,
                 denominator_unit=None, interpolation_method_id=None, extrapolation_method_id=None,
                 extrapolation_growth=None, age_growth_or_decay_type_id=None, age_growth_or_decay=None,
                 shape_id=None):
        DataObject.__init__(self)

        self.demand_technology_id = demand_technology_id
        self.definition_id = definition_id
        self.reference_tech_id = reference_tech_id
        self.geography_id = geography_id
        self.other_index_1_id = other_index_1_id
        self.other_index_2_id = other_index_2_id
        self.final_energy_id = final_energy_id
        self.demand_tech_efficiency_types_id = demand_tech_efficiency_types_id
        self.is_numerator_service = is_numerator_service
        self.numerator_unit = numerator_unit
        self.denominator_unit = denominator_unit
        self.interpolation_method_id = interpolation_method_id
        self.extrapolation_method_id = extrapolation_method_id
        self.extrapolation_growth = extrapolation_growth
        self.age_growth_or_decay_type_id = age_growth_or_decay_type_id
        self.age_growth_or_decay = age_growth_or_decay
        self.shape_id = shape_id

    @classmethod
    def from_tuple(cls, tup):    
        (demand_technology_id, definition_id, reference_tech_id, geography_id, other_index_1_id,
         other_index_2_id, final_energy_id, demand_tech_efficiency_types_id, is_numerator_service,
         numerator_unit, denominator_unit, interpolation_method_id, extrapolation_method_id,
         extrapolation_growth, age_growth_or_decay_type_id, age_growth_or_decay, shape_id) = tup
        
        obj = cls(demand_technology_id=demand_technology_id, definition_id=definition_id,
                  reference_tech_id=reference_tech_id, geography_id=geography_id,
                  other_index_1_id=other_index_1_id, other_index_2_id=other_index_2_id,
                  final_energy_id=final_energy_id,
                  demand_tech_efficiency_types_id=demand_tech_efficiency_types_id,
                  is_numerator_service=is_numerator_service, numerator_unit=numerator_unit,
                  denominator_unit=denominator_unit, interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth,
                  age_growth_or_decay_type_id=age_growth_or_decay_type_id,
                  age_growth_or_decay=age_growth_or_decay, shape_id=shape_id)
        
        return obj

class DemandTechsAuxEfficiencyData(DataObject):
    def __init__(self, demand_technology_id=None, gau_id=None, oth_1_id=None, oth_2_id=None, vintage=None,
                 value=None, id=None, sensitivity=None):
        DataObject.__init__(self)

        self.demand_technology_id = demand_technology_id
        self.gau_id = gau_id
        self.oth_1_id = oth_1_id
        self.oth_2_id = oth_2_id
        self.vintage = vintage
        self.value = value
        self.id = id
        self.sensitivity = sensitivity

    @classmethod
    def from_tuple(cls, tup):    
        (demand_technology_id, gau_id, oth_1_id, oth_2_id, vintage, value, id, sensitivity) = tup
        
        obj = cls(demand_technology_id=demand_technology_id, gau_id=gau_id, oth_1_id=oth_1_id,
                  oth_2_id=oth_2_id, vintage=vintage, value=value, id=id, sensitivity=sensitivity)
        
        return obj

class DemandTechsCapitalCost(DataObject):
    def __init__(self, demand_technology_id=None, definition_id=None, reference_tech_id=None, geography_id=None,
                 other_index_1_id=None, other_index_2_id=None, currency_id=None, currency_year_id=None,
                 is_levelized=None, interpolation_method_id=None, extrapolation_method_id=None,
                 extrapolation_growth=None):
        DataObject.__init__(self)

        self.demand_technology_id = demand_technology_id
        self.definition_id = definition_id
        self.reference_tech_id = reference_tech_id
        self.geography_id = geography_id
        self.other_index_1_id = other_index_1_id
        self.other_index_2_id = other_index_2_id
        self.currency_id = currency_id
        self.currency_year_id = currency_year_id
        self.is_levelized = is_levelized
        self.interpolation_method_id = interpolation_method_id
        self.extrapolation_method_id = extrapolation_method_id
        self.extrapolation_growth = extrapolation_growth

    @classmethod
    def from_tuple(cls, tup):    
        (demand_technology_id, definition_id, reference_tech_id, geography_id, other_index_1_id,
         other_index_2_id, currency_id, currency_year_id, is_levelized, interpolation_method_id,
         extrapolation_method_id, extrapolation_growth) = tup
        
        obj = cls(demand_technology_id=demand_technology_id, definition_id=definition_id,
                  reference_tech_id=reference_tech_id, geography_id=geography_id,
                  other_index_1_id=other_index_1_id, other_index_2_id=other_index_2_id,
                  currency_id=currency_id, currency_year_id=currency_year_id, is_levelized=is_levelized,
                  interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth)
        
        return obj

class DemandTechsCapitalCostNewData(DataObject):
    def __init__(self, demand_technology_id=None, gau_id=None, oth_1_id=None, oth_2_id=None, vintage=None,
                 value=None, id=None, sensitivity=None):
        DataObject.__init__(self)

        self.demand_technology_id = demand_technology_id
        self.gau_id = gau_id
        self.oth_1_id = oth_1_id
        self.oth_2_id = oth_2_id
        self.vintage = vintage
        self.value = value
        self.id = id
        self.sensitivity = sensitivity

    @classmethod
    def from_tuple(cls, tup):    
        (demand_technology_id, gau_id, oth_1_id, oth_2_id, vintage, value, id, sensitivity) = tup
        
        obj = cls(demand_technology_id=demand_technology_id, gau_id=gau_id, oth_1_id=oth_1_id,
                  oth_2_id=oth_2_id, vintage=vintage, value=value, id=id, sensitivity=sensitivity)
        
        return obj

class DemandTechsCapitalCostReplacementData(DataObject):
    def __init__(self, demand_technology_id=None, gau_id=None, oth_1_id=None, oth_2_id=None, vintage=None,
                 value=None, id=None, sensitivity=None):
        DataObject.__init__(self)

        self.demand_technology_id = demand_technology_id
        self.gau_id = gau_id
        self.oth_1_id = oth_1_id
        self.oth_2_id = oth_2_id
        self.vintage = vintage
        self.value = value
        self.id = id
        self.sensitivity = sensitivity

    @classmethod
    def from_tuple(cls, tup):    
        (demand_technology_id, gau_id, oth_1_id, oth_2_id, vintage, value, id, sensitivity) = tup
        
        obj = cls(demand_technology_id=demand_technology_id, gau_id=gau_id, oth_1_id=oth_1_id,
                  oth_2_id=oth_2_id, vintage=vintage, value=value, id=id, sensitivity=sensitivity)
        
        return obj

class DemandTechsFixedMaintenanceCost(DataObject):
    def __init__(self, demand_technology_id=None, definition_id=None, reference_tech_id=None, geography_id=None,
                 other_index_1_id=None, other_index_2_id=None, currency_id=None, currency_year_id=None,
                 interpolation_method_id=None, extrapolation_method_id=None, extrapolation_growth=None,
                 age_growth_or_decay_type_id=None, age_growth_or_decay=None, additional_description=None):
        DataObject.__init__(self)

        self.demand_technology_id = demand_technology_id
        self.definition_id = definition_id
        self.reference_tech_id = reference_tech_id
        self.geography_id = geography_id
        self.other_index_1_id = other_index_1_id
        self.other_index_2_id = other_index_2_id
        self.currency_id = currency_id
        self.currency_year_id = currency_year_id
        self.interpolation_method_id = interpolation_method_id
        self.extrapolation_method_id = extrapolation_method_id
        self.extrapolation_growth = extrapolation_growth
        self.age_growth_or_decay_type_id = age_growth_or_decay_type_id
        self.age_growth_or_decay = age_growth_or_decay
        self.additional_description = additional_description

    @classmethod
    def from_tuple(cls, tup):    
        (demand_technology_id, definition_id, reference_tech_id, geography_id, other_index_1_id,
         other_index_2_id, currency_id, currency_year_id, interpolation_method_id,
         extrapolation_method_id, extrapolation_growth, age_growth_or_decay_type_id,
         age_growth_or_decay, additional_description) = tup
        
        obj = cls(demand_technology_id=demand_technology_id, definition_id=definition_id,
                  reference_tech_id=reference_tech_id, geography_id=geography_id,
                  other_index_1_id=other_index_1_id, other_index_2_id=other_index_2_id,
                  currency_id=currency_id, currency_year_id=currency_year_id,
                  interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth,
                  age_growth_or_decay_type_id=age_growth_or_decay_type_id,
                  age_growth_or_decay=age_growth_or_decay, additional_description=additional_description)
        
        return obj

class DemandTechsFixedMaintenanceCostData(DataObject):
    def __init__(self, demand_technology_id=None, gau_id=None, oth_1_id=None, oth_2_id=None, vintage=None,
                 value=None, id=None, sensitivity=None):
        DataObject.__init__(self)

        self.demand_technology_id = demand_technology_id
        self.gau_id = gau_id
        self.oth_1_id = oth_1_id
        self.oth_2_id = oth_2_id
        self.vintage = vintage
        self.value = value
        self.id = id
        self.sensitivity = sensitivity

    @classmethod
    def from_tuple(cls, tup):    
        (demand_technology_id, gau_id, oth_1_id, oth_2_id, vintage, value, id, sensitivity) = tup
        
        obj = cls(demand_technology_id=demand_technology_id, gau_id=gau_id, oth_1_id=oth_1_id,
                  oth_2_id=oth_2_id, vintage=vintage, value=value, id=id, sensitivity=sensitivity)
        
        return obj

class DemandTechsFuelSwitchCost(DataObject):
    def __init__(self, demand_technology_id=None, definition_id=None, reference_tech_id=None, geography_id=None,
                 other_index_1_id=None, other_index_2_id=None, currency_id=None, currency_year_id=None,
                 is_levelized=None, interpolation_method_id=None, extrapolation_method_id=None,
                 extrapolation_growth=None):
        DataObject.__init__(self)

        self.demand_technology_id = demand_technology_id
        self.definition_id = definition_id
        self.reference_tech_id = reference_tech_id
        self.geography_id = geography_id
        self.other_index_1_id = other_index_1_id
        self.other_index_2_id = other_index_2_id
        self.currency_id = currency_id
        self.currency_year_id = currency_year_id
        self.is_levelized = is_levelized
        self.interpolation_method_id = interpolation_method_id
        self.extrapolation_method_id = extrapolation_method_id
        self.extrapolation_growth = extrapolation_growth

    @classmethod
    def from_tuple(cls, tup):    
        (demand_technology_id, definition_id, reference_tech_id, geography_id, other_index_1_id,
         other_index_2_id, currency_id, currency_year_id, is_levelized, interpolation_method_id,
         extrapolation_method_id, extrapolation_growth) = tup
        
        obj = cls(demand_technology_id=demand_technology_id, definition_id=definition_id,
                  reference_tech_id=reference_tech_id, geography_id=geography_id,
                  other_index_1_id=other_index_1_id, other_index_2_id=other_index_2_id,
                  currency_id=currency_id, currency_year_id=currency_year_id, is_levelized=is_levelized,
                  interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth)
        
        return obj

class DemandTechsFuelSwitchCostData(DataObject):
    def __init__(self, demand_technology_id=None, gau_id=None, oth_1_id=None, oth_2_id=None, vintage=None,
                 value=None, id=None, sensitivity=None):
        DataObject.__init__(self)

        self.demand_technology_id = demand_technology_id
        self.gau_id = gau_id
        self.oth_1_id = oth_1_id
        self.oth_2_id = oth_2_id
        self.vintage = vintage
        self.value = value
        self.id = id
        self.sensitivity = sensitivity

    @classmethod
    def from_tuple(cls, tup):    
        (demand_technology_id, gau_id, oth_1_id, oth_2_id, vintage, value, id, sensitivity) = tup
        
        obj = cls(demand_technology_id=demand_technology_id, gau_id=gau_id, oth_1_id=oth_1_id,
                  oth_2_id=oth_2_id, vintage=vintage, value=value, id=id, sensitivity=sensitivity)
        
        return obj

class DemandTechsInstallationCost(DataObject):
    def __init__(self, demand_technology_id=None, definition_id=None, reference_tech_id=None, geography_id=None,
                 other_index_1_id=None, other_index_2_id=None, currency_id=None, currency_year_id=None,
                 is_levelized=None, interpolation_method_id=None, extrapolation_method_id=None,
                 extrapolation_growth=None):
        DataObject.__init__(self)

        self.demand_technology_id = demand_technology_id
        self.definition_id = definition_id
        self.reference_tech_id = reference_tech_id
        self.geography_id = geography_id
        self.other_index_1_id = other_index_1_id
        self.other_index_2_id = other_index_2_id
        self.currency_id = currency_id
        self.currency_year_id = currency_year_id
        self.is_levelized = is_levelized
        self.interpolation_method_id = interpolation_method_id
        self.extrapolation_method_id = extrapolation_method_id
        self.extrapolation_growth = extrapolation_growth

    @classmethod
    def from_tuple(cls, tup):    
        (demand_technology_id, definition_id, reference_tech_id, geography_id, other_index_1_id,
         other_index_2_id, currency_id, currency_year_id, is_levelized, interpolation_method_id,
         extrapolation_method_id, extrapolation_growth) = tup
        
        obj = cls(demand_technology_id=demand_technology_id, definition_id=definition_id,
                  reference_tech_id=reference_tech_id, geography_id=geography_id,
                  other_index_1_id=other_index_1_id, other_index_2_id=other_index_2_id,
                  currency_id=currency_id, currency_year_id=currency_year_id, is_levelized=is_levelized,
                  interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth)
        
        return obj

class DemandTechsInstallationCostNewData(DataObject):
    def __init__(self, demand_technology_id=None, gau_id=None, oth_1_id=None, oth_2_id=None, vintage=None,
                 value=None, id=None, sensitivity=None):
        DataObject.__init__(self)

        self.demand_technology_id = demand_technology_id
        self.gau_id = gau_id
        self.oth_1_id = oth_1_id
        self.oth_2_id = oth_2_id
        self.vintage = vintage
        self.value = value
        self.id = id
        self.sensitivity = sensitivity

    @classmethod
    def from_tuple(cls, tup):    
        (demand_technology_id, gau_id, oth_1_id, oth_2_id, vintage, value, id, sensitivity) = tup
        
        obj = cls(demand_technology_id=demand_technology_id, gau_id=gau_id, oth_1_id=oth_1_id,
                  oth_2_id=oth_2_id, vintage=vintage, value=value, id=id, sensitivity=sensitivity)
        
        return obj

class DemandTechsInstallationCostReplacementData(DataObject):
    def __init__(self, demand_technology_id=None, gau_id=None, oth_1_id=None, oth_2_id=None, vintage=None,
                 value=None, id=None, sensitivity=None):
        DataObject.__init__(self)

        self.demand_technology_id = demand_technology_id
        self.gau_id = gau_id
        self.oth_1_id = oth_1_id
        self.oth_2_id = oth_2_id
        self.vintage = vintage
        self.value = value
        self.id = id
        self.sensitivity = sensitivity

    @classmethod
    def from_tuple(cls, tup):    
        (demand_technology_id, gau_id, oth_1_id, oth_2_id, vintage, value, id, sensitivity) = tup
        
        obj = cls(demand_technology_id=demand_technology_id, gau_id=gau_id, oth_1_id=oth_1_id,
                  oth_2_id=oth_2_id, vintage=vintage, value=value, id=id, sensitivity=sensitivity)
        
        return obj

class DemandTechsMainEfficiency(DataObject):
    def __init__(self, demand_technology_id=None, definition_id=None, reference_tech_id=None, geography_id=None,
                 other_index_1_id=None, other_index_2_id=None, final_energy_id=None, utility_factor=None,
                 demand_tech_efficiency_types=None, is_numerator_service=None, numerator_unit=None,
                 denominator_unit=None, interpolation_method_id=None, extrapolation_method_id=None,
                 extrapolation_growth=None, age_growth_or_decay_type_id=None, age_growth_or_decay=None,
                 shape_id=None):
        DataObject.__init__(self)

        self.demand_technology_id = demand_technology_id
        self.definition_id = definition_id
        self.reference_tech_id = reference_tech_id
        self.geography_id = geography_id
        self.other_index_1_id = other_index_1_id
        self.other_index_2_id = other_index_2_id
        self.final_energy_id = final_energy_id
        self.utility_factor = utility_factor
        self.demand_tech_efficiency_types = demand_tech_efficiency_types
        self.is_numerator_service = is_numerator_service
        self.numerator_unit = numerator_unit
        self.denominator_unit = denominator_unit
        self.interpolation_method_id = interpolation_method_id
        self.extrapolation_method_id = extrapolation_method_id
        self.extrapolation_growth = extrapolation_growth
        self.age_growth_or_decay_type_id = age_growth_or_decay_type_id
        self.age_growth_or_decay = age_growth_or_decay
        self.shape_id = shape_id

    @classmethod
    def from_tuple(cls, tup):    
        (demand_technology_id, definition_id, reference_tech_id, geography_id, other_index_1_id,
         other_index_2_id, final_energy_id, utility_factor, demand_tech_efficiency_types,
         is_numerator_service, numerator_unit, denominator_unit, interpolation_method_id,
         extrapolation_method_id, extrapolation_growth, age_growth_or_decay_type_id,
         age_growth_or_decay, shape_id) = tup
        
        obj = cls(demand_technology_id=demand_technology_id, definition_id=definition_id,
                  reference_tech_id=reference_tech_id, geography_id=geography_id,
                  other_index_1_id=other_index_1_id, other_index_2_id=other_index_2_id,
                  final_energy_id=final_energy_id, utility_factor=utility_factor,
                  demand_tech_efficiency_types=demand_tech_efficiency_types,
                  is_numerator_service=is_numerator_service, numerator_unit=numerator_unit,
                  denominator_unit=denominator_unit, interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth,
                  age_growth_or_decay_type_id=age_growth_or_decay_type_id,
                  age_growth_or_decay=age_growth_or_decay, shape_id=shape_id)
        
        return obj

class DemandTechsMainEfficiencyData(DataObject):
    def __init__(self, demand_technology_id=None, gau_id=None, oth_1_id=None, oth_2_id=None, vintage=None,
                 value=None, id=None, sensitivity=None):
        DataObject.__init__(self)

        self.demand_technology_id = demand_technology_id
        self.gau_id = gau_id
        self.oth_1_id = oth_1_id
        self.oth_2_id = oth_2_id
        self.vintage = vintage
        self.value = value
        self.id = id
        self.sensitivity = sensitivity

    @classmethod
    def from_tuple(cls, tup):    
        (demand_technology_id, gau_id, oth_1_id, oth_2_id, vintage, value, id, sensitivity) = tup
        
        obj = cls(demand_technology_id=demand_technology_id, gau_id=gau_id, oth_1_id=oth_1_id,
                  oth_2_id=oth_2_id, vintage=vintage, value=value, id=id, sensitivity=sensitivity)
        
        return obj

class DemandTechsParasiticEnergy(DataObject):
    def __init__(self, demand_technology_id=None, definition_id=None, reference_tech_id=None, geography_id=None,
                 other_index_1_id=None, other_index_2_id=None, energy_unit=None, time_unit=None,
                 interpolation_method_id=None, extrapolation_method_id=None, extrapolation_growth=None,
                 age_growth_or_decay_type_id=None, age_growth_or_decay=None):
        DataObject.__init__(self)

        self.demand_technology_id = demand_technology_id
        self.definition_id = definition_id
        self.reference_tech_id = reference_tech_id
        self.geography_id = geography_id
        self.other_index_1_id = other_index_1_id
        self.other_index_2_id = other_index_2_id
        self.energy_unit = energy_unit
        self.time_unit = time_unit
        self.interpolation_method_id = interpolation_method_id
        self.extrapolation_method_id = extrapolation_method_id
        self.extrapolation_growth = extrapolation_growth
        self.age_growth_or_decay_type_id = age_growth_or_decay_type_id
        self.age_growth_or_decay = age_growth_or_decay

    @classmethod
    def from_tuple(cls, tup):    
        (demand_technology_id, definition_id, reference_tech_id, geography_id, other_index_1_id,
         other_index_2_id, energy_unit, time_unit, interpolation_method_id,
         extrapolation_method_id, extrapolation_growth, age_growth_or_decay_type_id,
         age_growth_or_decay) = tup
        
        obj = cls(demand_technology_id=demand_technology_id, definition_id=definition_id,
                  reference_tech_id=reference_tech_id, geography_id=geography_id,
                  other_index_1_id=other_index_1_id, other_index_2_id=other_index_2_id,
                  energy_unit=energy_unit, time_unit=time_unit,
                  interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth,
                  age_growth_or_decay_type_id=age_growth_or_decay_type_id,
                  age_growth_or_decay=age_growth_or_decay)
        
        return obj

class DemandTechsParasiticEnergyData(DataObject):
    def __init__(self, demand_technology_id=None, gau_id=None, oth_1_id=None, oth_2_id=None,
                 final_energy_id=None, vintage=None, value=None, id=None, sensitivity=None):
        DataObject.__init__(self)

        self.demand_technology_id = demand_technology_id
        self.gau_id = gau_id
        self.oth_1_id = oth_1_id
        self.oth_2_id = oth_2_id
        self.final_energy_id = final_energy_id
        self.vintage = vintage
        self.value = value
        self.id = id
        self.sensitivity = sensitivity

    @classmethod
    def from_tuple(cls, tup):    
        (demand_technology_id, gau_id, oth_1_id, oth_2_id, final_energy_id, vintage, value, id,
         sensitivity) = tup
        
        obj = cls(demand_technology_id=demand_technology_id, gau_id=gau_id, oth_1_id=oth_1_id,
                  oth_2_id=oth_2_id, final_energy_id=final_energy_id, vintage=vintage, value=value, id=id,
                  sensitivity=sensitivity)
        
        return obj

class DemandTechsServiceDemandModifier(DataObject):
    def __init__(self, demand_technology_id=None, geography_id=None, other_index_1_id=None,
                 other_index_2_id=None, interpolation_method_id=None, extrapolation_method_id=None,
                 extrapolation_growth=None, age_growth_or_decay_type_id=None, age_growth_or_decay=None):
        DataObject.__init__(self)

        self.demand_technology_id = demand_technology_id
        self.geography_id = geography_id
        self.other_index_1_id = other_index_1_id
        self.other_index_2_id = other_index_2_id
        self.interpolation_method_id = interpolation_method_id
        self.extrapolation_method_id = extrapolation_method_id
        self.extrapolation_growth = extrapolation_growth
        self.age_growth_or_decay_type_id = age_growth_or_decay_type_id
        self.age_growth_or_decay = age_growth_or_decay

    @classmethod
    def from_tuple(cls, tup):    
        (demand_technology_id, geography_id, other_index_1_id, other_index_2_id,
         interpolation_method_id, extrapolation_method_id, extrapolation_growth,
         age_growth_or_decay_type_id, age_growth_or_decay) = tup
        
        obj = cls(demand_technology_id=demand_technology_id, geography_id=geography_id,
                  other_index_1_id=other_index_1_id, other_index_2_id=other_index_2_id,
                  interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth,
                  age_growth_or_decay_type_id=age_growth_or_decay_type_id,
                  age_growth_or_decay=age_growth_or_decay)
        
        return obj

class DemandTechsServiceDemandModifierData(DataObject):
    def __init__(self, demand_technology_id=None, gau_id=None, oth_1_id=None, oth_2_id=None, vintage=None,
                 value=None, id=None, sensitivity=None):
        DataObject.__init__(self)

        self.demand_technology_id = demand_technology_id
        self.gau_id = gau_id
        self.oth_1_id = oth_1_id
        self.oth_2_id = oth_2_id
        self.vintage = vintage
        self.value = value
        self.id = id
        self.sensitivity = sensitivity

    @classmethod
    def from_tuple(cls, tup):    
        (demand_technology_id, gau_id, oth_1_id, oth_2_id, vintage, value, id, sensitivity) = tup
        
        obj = cls(demand_technology_id=demand_technology_id, gau_id=gau_id, oth_1_id=oth_1_id,
                  oth_2_id=oth_2_id, vintage=vintage, value=value, id=id, sensitivity=sensitivity)
        
        return obj

class DemandTechsServiceLink(DataObject):
    def __init__(self, id=None, service_link_id=None, demand_technology_id=None, definition_id=None,
                 reference_id=None, geography_id=None, other_index_1_id=None, other_index_2_id=None,
                 interpolation_method_id=None, extrapolation_method_id=None, extrapolation_growth=None,
                 age_growth_or_decay_type_id=None, age_growth_or_decay=None):
        DataObject.__init__(self)

        self.id = id
        self.service_link_id = service_link_id
        self.demand_technology_id = demand_technology_id
        self.definition_id = definition_id
        self.reference_id = reference_id
        self.geography_id = geography_id
        self.other_index_1_id = other_index_1_id
        self.other_index_2_id = other_index_2_id
        self.interpolation_method_id = interpolation_method_id
        self.extrapolation_method_id = extrapolation_method_id
        self.extrapolation_growth = extrapolation_growth
        self.age_growth_or_decay_type_id = age_growth_or_decay_type_id
        self.age_growth_or_decay = age_growth_or_decay

    @classmethod
    def from_tuple(cls, tup):    
        (id, service_link_id, demand_technology_id, definition_id, reference_id, geography_id,
         other_index_1_id, other_index_2_id, interpolation_method_id, extrapolation_method_id,
         extrapolation_growth, age_growth_or_decay_type_id, age_growth_or_decay) = tup
        
        obj = cls(id=id, service_link_id=service_link_id, demand_technology_id=demand_technology_id,
                  definition_id=definition_id, reference_id=reference_id, geography_id=geography_id,
                  other_index_1_id=other_index_1_id, other_index_2_id=other_index_2_id,
                  interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth,
                  age_growth_or_decay_type_id=age_growth_or_decay_type_id,
                  age_growth_or_decay=age_growth_or_decay)
        
        return obj

class DemandTechsServiceLinkData(DataObject):
    def __init__(self, parent_id=None, gau_id=None, oth_1_id=None, oth_2_id=None, vintage=None, value=None,
                 id=None):
        DataObject.__init__(self)

        self.parent_id = parent_id
        self.gau_id = gau_id
        self.oth_1_id = oth_1_id
        self.oth_2_id = oth_2_id
        self.vintage = vintage
        self.value = value
        self.id = id

    @classmethod
    def from_tuple(cls, tup):    
        (parent_id, gau_id, oth_1_id, oth_2_id, vintage, value, id) = tup
        
        obj = cls(parent_id=parent_id, gau_id=gau_id, oth_1_id=oth_1_id, oth_2_id=oth_2_id, vintage=vintage,
                  value=value, id=id)
        
        return obj

class FinalEnergy(DataObject):
    def __init__(self, id=None, name=None, shape_id=None):
        DataObject.__init__(self)

        self.id = id
        self.name = name
        self.shape_id = shape_id

    @classmethod
    def from_tuple(cls, tup):    
        (id, name, shape_id) = tup
        
        obj = cls(id=id, name=name, shape_id=shape_id)
        
        return obj

class GeographiesData(DataObject):
    def __init__(self, id=None, name=None, geography_id=None):
        DataObject.__init__(self)

        self.id = id
        self.name = name
        self.geography_id = geography_id

    @classmethod
    def from_tuple(cls, tup):    
        (id, name, geography_id) = tup
        
        obj = cls(id=id, name=name, geography_id=geography_id)
        
        return obj

class GeographyIntersectionData(DataObject):
    def __init__(self, intersection_id=None, gau_id=None, id=None):
        DataObject.__init__(self)

        self.intersection_id = intersection_id
        self.gau_id = gau_id
        self.id = id

    @classmethod
    def from_tuple(cls, tup):    
        (intersection_id, gau_id, id) = tup
        
        obj = cls(intersection_id=intersection_id, gau_id=gau_id, id=id)
        
        return obj

class GeographyMap(DataObject):
    def __init__(self, intersection_id=None, geography_map_key_id=None, value=None, id=None):
        DataObject.__init__(self)

        self.intersection_id = intersection_id
        self.geography_map_key_id = geography_map_key_id
        self.value = value
        self.id = id

    @classmethod
    def from_tuple(cls, tup):    
        (intersection_id, geography_map_key_id, value, id) = tup
        
        obj = cls(intersection_id=intersection_id, geography_map_key_id=geography_map_key_id, value=value,
                  id=id)
        
        return obj

class ImportCost(DataObject):
    def __init__(self, import_node_id=None, source=None, notes=None, geography_id=None, currency_id=None,
                 currency_year_id=None, denominator_unit=None, interpolation_method_id=None,
                 extrapolation_method_id=None, extrapolation_growth=None):
        DataObject.__init__(self)

        self.import_node_id = import_node_id
        self.source = source
        self.notes = notes
        self.geography_id = geography_id
        self.currency_id = currency_id
        self.currency_year_id = currency_year_id
        self.denominator_unit = denominator_unit
        self.interpolation_method_id = interpolation_method_id
        self.extrapolation_method_id = extrapolation_method_id
        self.extrapolation_growth = extrapolation_growth

    @classmethod
    def from_tuple(cls, tup):    
        (import_node_id, source, notes, geography_id, currency_id, currency_year_id,
         denominator_unit, interpolation_method_id, extrapolation_method_id, extrapolation_growth) = tup
        
        obj = cls(import_node_id=import_node_id, source=source, notes=notes, geography_id=geography_id,
                  currency_id=currency_id, currency_year_id=currency_year_id,
                  denominator_unit=denominator_unit, interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth)
        
        return obj

class ImportCostData(DataObject):
    def __init__(self, import_node_id=None, gau_id=None, demand_sector_id=None, year=None, value=None, id=None,
                 sensitivity=None, resource_bin=None):
        DataObject.__init__(self)

        self.import_node_id = import_node_id
        self.gau_id = gau_id
        self.demand_sector_id = demand_sector_id
        self.year = year
        self.value = value
        self.id = id
        self.sensitivity = sensitivity
        self.resource_bin = resource_bin

    @classmethod
    def from_tuple(cls, tup):    
        (import_node_id, gau_id, demand_sector_id, year, value, id, sensitivity, resource_bin) = tup
        
        obj = cls(import_node_id=import_node_id, gau_id=gau_id, demand_sector_id=demand_sector_id,
                  year=year, value=value, id=id, sensitivity=sensitivity, resource_bin=resource_bin)
        
        return obj

class OtherIndexesData(DataObject):
    def __init__(self, id=None, name=None, other_index_id=None):
        DataObject.__init__(self)

        self.id = id
        self.name = name
        self.other_index_id = other_index_id

    @classmethod
    def from_tuple(cls, tup):    
        (id, name, other_index_id) = tup
        
        obj = cls(id=id, name=name, other_index_id=other_index_id)
        
        return obj

class OtherIndexesData_copy(DataObject):
    def __init__(self, id=None, name=None, other_index_id=None):
        DataObject.__init__(self)

        self.id = id
        self.name = name
        self.other_index_id = other_index_id

    @classmethod
    def from_tuple(cls, tup):    
        (id, name, other_index_id) = tup
        
        obj = cls(id=id, name=name, other_index_id=other_index_id)
        
        return obj

class PrimaryCost(DataObject):
    def __init__(self, primary_node_id=None, geography_id=None, other_index_1_id=None, currency_id=None,
                 currency_year_id=None, denominator_unit=None, interpolation_method_id=None,
                 extrapolation_method_id=None, extrapolation_growth=None):
        DataObject.__init__(self)

        self.primary_node_id = primary_node_id
        self.geography_id = geography_id
        self.other_index_1_id = other_index_1_id
        self.currency_id = currency_id
        self.currency_year_id = currency_year_id
        self.denominator_unit = denominator_unit
        self.interpolation_method_id = interpolation_method_id
        self.extrapolation_method_id = extrapolation_method_id
        self.extrapolation_growth = extrapolation_growth

    @classmethod
    def from_tuple(cls, tup):    
        (primary_node_id, geography_id, other_index_1_id, currency_id, currency_year_id,
         denominator_unit, interpolation_method_id, extrapolation_method_id, extrapolation_growth) = tup
        
        obj = cls(primary_node_id=primary_node_id, geography_id=geography_id,
                  other_index_1_id=other_index_1_id, currency_id=currency_id,
                  currency_year_id=currency_year_id, denominator_unit=denominator_unit,
                  interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth)
        
        return obj

class PrimaryCostData(DataObject):
    def __init__(self, primary_node_id=None, gau_id=None, demand_sector_id=None, oth_1_id=None,
                 resource_bin=None, year=None, value=None, id=None, sensitivity=None):
        DataObject.__init__(self)

        self.primary_node_id = primary_node_id
        self.gau_id = gau_id
        self.demand_sector_id = demand_sector_id
        self.oth_1_id = oth_1_id
        self.resource_bin = resource_bin
        self.year = year
        self.value = value
        self.id = id
        self.sensitivity = sensitivity

    @classmethod
    def from_tuple(cls, tup):    
        (primary_node_id, gau_id, demand_sector_id, oth_1_id, resource_bin, year, value, id,
         sensitivity) = tup
        
        obj = cls(primary_node_id=primary_node_id, gau_id=gau_id, demand_sector_id=demand_sector_id,
                  oth_1_id=oth_1_id, resource_bin=resource_bin, year=year, value=value, id=id,
                  sensitivity=sensitivity)
        
        return obj

class Shapes(DataObject):
    def __init__(self, id=None, name=None, shape_type_id=None, shape_unit_type_id=None, time_zone_id=None,
                 geography_id=None, other_index_1_id=None, other_index_2_id=None,
                 geography_map_key_id=None, interpolation_method_id=None, extrapolation_method_id=None,
                 input_type_id=None):
        DataObject.__init__(self)

        self.id = id
        self.name = name
        self.shape_type_id = shape_type_id
        self.shape_unit_type_id = shape_unit_type_id
        self.time_zone_id = time_zone_id
        self.geography_id = geography_id
        self.other_index_1_id = other_index_1_id
        self.other_index_2_id = other_index_2_id
        self.geography_map_key_id = geography_map_key_id
        self.interpolation_method_id = interpolation_method_id
        self.extrapolation_method_id = extrapolation_method_id
        self.input_type_id = input_type_id

    @classmethod
    def from_tuple(cls, tup):    
        (id, name, shape_type_id, shape_unit_type_id, time_zone_id, geography_id, other_index_1_id,
         other_index_2_id, geography_map_key_id, interpolation_method_id, extrapolation_method_id,
         input_type_id) = tup
        
        obj = cls(id=id, name=name, shape_type_id=shape_type_id, shape_unit_type_id=shape_unit_type_id,
                  time_zone_id=time_zone_id, geography_id=geography_id, other_index_1_id=other_index_1_id,
                  other_index_2_id=other_index_2_id, geography_map_key_id=geography_map_key_id,
                  interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id, input_type_id=input_type_id)
        
        return obj

class ShapesData(DataObject):
    def __init__(self, parent_id=None, gau_id=None, dispatch_feeder_id=None, timeshift_type_id=None,
                 resource_bin=None, dispatch_constraint_id=None, year=None, month=None, week=None,
                 hour=None, day_type_id=None, weather_datetime=None, value=None, id=None):
        DataObject.__init__(self)

        self.parent_id = parent_id
        self.gau_id = gau_id
        self.dispatch_feeder_id = dispatch_feeder_id
        self.timeshift_type_id = timeshift_type_id
        self.resource_bin = resource_bin
        self.dispatch_constraint_id = dispatch_constraint_id
        self.year = year
        self.month = month
        self.week = week
        self.hour = hour
        self.day_type_id = day_type_id
        self.weather_datetime = weather_datetime
        self.value = value
        self.id = id

    @classmethod
    def from_tuple(cls, tup):    
        (parent_id, gau_id, dispatch_feeder_id, timeshift_type_id, resource_bin,
         dispatch_constraint_id, year, month, week, hour, day_type_id, weather_datetime, value, id) = tup
        
        obj = cls(parent_id=parent_id, gau_id=gau_id, dispatch_feeder_id=dispatch_feeder_id,
                  timeshift_type_id=timeshift_type_id, resource_bin=resource_bin,
                  dispatch_constraint_id=dispatch_constraint_id, year=year, month=month, week=week,
                  hour=hour, day_type_id=day_type_id, weather_datetime=weather_datetime, value=value, id=id)
        
        return obj

class StorageTechsCapacityCapitalCost(DataObject):
    def __init__(self, supply_tech_id=None, definition_id=None, reference_tech_id=None, currency_id=None,
                 geography_id=None, currency_year_id=None, capacity_or_energy_unit=None,
                 is_levelized=None, cost_of_capital=None, interpolation_method_id=None,
                 extrapolation_method_id=None, time_unit=None):
        DataObject.__init__(self)

        self.supply_tech_id = supply_tech_id
        self.definition_id = definition_id
        self.reference_tech_id = reference_tech_id
        self.currency_id = currency_id
        self.geography_id = geography_id
        self.currency_year_id = currency_year_id
        self.capacity_or_energy_unit = capacity_or_energy_unit
        self.is_levelized = is_levelized
        self.cost_of_capital = cost_of_capital
        self.interpolation_method_id = interpolation_method_id
        self.extrapolation_method_id = extrapolation_method_id
        self.time_unit = time_unit

    @classmethod
    def from_tuple(cls, tup):    
        (supply_tech_id, definition_id, reference_tech_id, currency_id, geography_id,
         currency_year_id, capacity_or_energy_unit, is_levelized, cost_of_capital,
         interpolation_method_id, extrapolation_method_id, time_unit) = tup
        
        obj = cls(supply_tech_id=supply_tech_id, definition_id=definition_id,
                  reference_tech_id=reference_tech_id, currency_id=currency_id, geography_id=geography_id,
                  currency_year_id=currency_year_id, capacity_or_energy_unit=capacity_or_energy_unit,
                  is_levelized=is_levelized, cost_of_capital=cost_of_capital,
                  interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id, time_unit=time_unit)
        
        return obj

class StorageTechsCapacityCapitalCostNewData(DataObject):
    def __init__(self, supply_tech_id=None, gau_id=None, oth_1_id=None, oth_2_id=None, vintage=None, value=None,
                 id=None, sensitivity=None):
        DataObject.__init__(self)

        self.supply_tech_id = supply_tech_id
        self.gau_id = gau_id
        self.oth_1_id = oth_1_id
        self.oth_2_id = oth_2_id
        self.vintage = vintage
        self.value = value
        self.id = id
        self.sensitivity = sensitivity

    @classmethod
    def from_tuple(cls, tup):    
        (supply_tech_id, gau_id, oth_1_id, oth_2_id, vintage, value, id, sensitivity) = tup
        
        obj = cls(supply_tech_id=supply_tech_id, gau_id=gau_id, oth_1_id=oth_1_id, oth_2_id=oth_2_id,
                  vintage=vintage, value=value, id=id, sensitivity=sensitivity)
        
        return obj

class StorageTechsCapacityCapitalCostReplacementData(DataObject):
    def __init__(self, supply_tech_id=None, gau_id=None, oth_1_id=None, oth_2_id=None, vintage=None, value=None,
                 id=None, sensitivity=None):
        DataObject.__init__(self)

        self.supply_tech_id = supply_tech_id
        self.gau_id = gau_id
        self.oth_1_id = oth_1_id
        self.oth_2_id = oth_2_id
        self.vintage = vintage
        self.value = value
        self.id = id
        self.sensitivity = sensitivity

    @classmethod
    def from_tuple(cls, tup):    
        (supply_tech_id, gau_id, oth_1_id, oth_2_id, vintage, value, id, sensitivity) = tup
        
        obj = cls(supply_tech_id=supply_tech_id, gau_id=gau_id, oth_1_id=oth_1_id, oth_2_id=oth_2_id,
                  vintage=vintage, value=value, id=id, sensitivity=sensitivity)
        
        return obj

class StorageTechsEnergyCapitalCost(DataObject):
    def __init__(self, supply_tech_id=None, definition_id=None, reference_tech_id=None, currency_id=None,
                 geography_id=None, currency_year_id=None, energy_unit=None, is_levelized=None,
                 cost_of_capital=None, interpolation_method_id=None, extrapolation_method_id=None):
        DataObject.__init__(self)

        self.supply_tech_id = supply_tech_id
        self.definition_id = definition_id
        self.reference_tech_id = reference_tech_id
        self.currency_id = currency_id
        self.geography_id = geography_id
        self.currency_year_id = currency_year_id
        self.energy_unit = energy_unit
        self.is_levelized = is_levelized
        self.cost_of_capital = cost_of_capital
        self.interpolation_method_id = interpolation_method_id
        self.extrapolation_method_id = extrapolation_method_id

    @classmethod
    def from_tuple(cls, tup):    
        (supply_tech_id, definition_id, reference_tech_id, currency_id, geography_id,
         currency_year_id, energy_unit, is_levelized, cost_of_capital, interpolation_method_id,
         extrapolation_method_id) = tup
        
        obj = cls(supply_tech_id=supply_tech_id, definition_id=definition_id,
                  reference_tech_id=reference_tech_id, currency_id=currency_id, geography_id=geography_id,
                  currency_year_id=currency_year_id, energy_unit=energy_unit, is_levelized=is_levelized,
                  cost_of_capital=cost_of_capital, interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id)
        
        return obj

class StorageTechsEnergyCapitalCostNewData(DataObject):
    def __init__(self, supply_tech_id=None, gau_id=None, oth_1_id=None, oth_2_id=None, vintage=None, value=None,
                 id=None, sensitivity=None):
        DataObject.__init__(self)

        self.supply_tech_id = supply_tech_id
        self.gau_id = gau_id
        self.oth_1_id = oth_1_id
        self.oth_2_id = oth_2_id
        self.vintage = vintage
        self.value = value
        self.id = id
        self.sensitivity = sensitivity

    @classmethod
    def from_tuple(cls, tup):    
        (supply_tech_id, gau_id, oth_1_id, oth_2_id, vintage, value, id, sensitivity) = tup
        
        obj = cls(supply_tech_id=supply_tech_id, gau_id=gau_id, oth_1_id=oth_1_id, oth_2_id=oth_2_id,
                  vintage=vintage, value=value, id=id, sensitivity=sensitivity)
        
        return obj

class StorageTechsEnergyCapitalCostReplacementData(DataObject):
    def __init__(self, supply_tech_id=None, gau_id=None, oth_1_id=None, oth_2_id=None, vintage=None, value=None,
                 id=None, sensitivity=None):
        DataObject.__init__(self)

        self.supply_tech_id = supply_tech_id
        self.gau_id = gau_id
        self.oth_1_id = oth_1_id
        self.oth_2_id = oth_2_id
        self.vintage = vintage
        self.value = value
        self.id = id
        self.sensitivity = sensitivity

    @classmethod
    def from_tuple(cls, tup):    
        (supply_tech_id, gau_id, oth_1_id, oth_2_id, vintage, value, id, sensitivity) = tup
        
        obj = cls(supply_tech_id=supply_tech_id, gau_id=gau_id, oth_1_id=oth_1_id, oth_2_id=oth_2_id,
                  vintage=vintage, value=value, id=id, sensitivity=sensitivity)
        
        return obj

class SupplyCapacityFactor(DataObject):
    def __init__(self, supply_node_id=None, geography_id=None, unit=None, interpolation_method_id=None,
                 extrapolation_method_id=None, extrapolation_growth=None,
                 age_growth_or_decay_type_id=None, age_growth_or_decay=None):
        DataObject.__init__(self)

        self.supply_node_id = supply_node_id
        self.geography_id = geography_id
        self.unit = unit
        self.interpolation_method_id = interpolation_method_id
        self.extrapolation_method_id = extrapolation_method_id
        self.extrapolation_growth = extrapolation_growth
        self.age_growth_or_decay_type_id = age_growth_or_decay_type_id
        self.age_growth_or_decay = age_growth_or_decay

    @classmethod
    def from_tuple(cls, tup):    
        (supply_node_id, geography_id, unit, interpolation_method_id, extrapolation_method_id,
         extrapolation_growth, age_growth_or_decay_type_id, age_growth_or_decay) = tup
        
        obj = cls(supply_node_id=supply_node_id, geography_id=geography_id, unit=unit,
                  interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth,
                  age_growth_or_decay_type_id=age_growth_or_decay_type_id,
                  age_growth_or_decay=age_growth_or_decay)
        
        return obj

class SupplyCapacityFactorData(DataObject):
    def __init__(self, supply_node_id=None, gau_id=None, demand_sector_id=None, resource_bin=None, year=None,
                 value=None, id=None):
        DataObject.__init__(self)

        self.supply_node_id = supply_node_id
        self.gau_id = gau_id
        self.demand_sector_id = demand_sector_id
        self.resource_bin = resource_bin
        self.year = year
        self.value = value
        self.id = id

    @classmethod
    def from_tuple(cls, tup):    
        (supply_node_id, gau_id, demand_sector_id, resource_bin, year, value, id) = tup
        
        obj = cls(supply_node_id=supply_node_id, gau_id=gau_id, demand_sector_id=demand_sector_id,
                  resource_bin=resource_bin, year=year, value=value, id=id)
        
        return obj

class SupplyCost(DataObject):
    def __init__(self, id=None, name=None, source=None, additional_notes=None, supply_node_id=None,
                 geography_id=None, supply_cost_type_id=None, currency_id=None, currency_year_id=None,
                 energy_or_capacity_unit=None, time_unit=None, is_capital_cost=None, cost_of_capital=None,
                 book_life=None, throughput_correlation=None, interpolation_method_id=None,
                 extrapolation_method_id=None, extrapolation_growth=None):
        DataObject.__init__(self)

        self.id = id
        self.name = name
        self.source = source
        self.additional_notes = additional_notes
        self.supply_node_id = supply_node_id
        self.geography_id = geography_id
        self.supply_cost_type_id = supply_cost_type_id
        self.currency_id = currency_id
        self.currency_year_id = currency_year_id
        self.energy_or_capacity_unit = energy_or_capacity_unit
        self.time_unit = time_unit
        self.is_capital_cost = is_capital_cost
        self.cost_of_capital = cost_of_capital
        self.book_life = book_life
        self.throughput_correlation = throughput_correlation
        self.interpolation_method_id = interpolation_method_id
        self.extrapolation_method_id = extrapolation_method_id
        self.extrapolation_growth = extrapolation_growth

    @classmethod
    def from_tuple(cls, tup):    
        (id, name, source, additional_notes, supply_node_id, geography_id, supply_cost_type_id,
         currency_id, currency_year_id, energy_or_capacity_unit, time_unit, is_capital_cost,
         cost_of_capital, book_life, throughput_correlation, interpolation_method_id,
         extrapolation_method_id, extrapolation_growth) = tup
        
        obj = cls(id=id, name=name, source=source, additional_notes=additional_notes,
                  supply_node_id=supply_node_id, geography_id=geography_id,
                  supply_cost_type_id=supply_cost_type_id, currency_id=currency_id,
                  currency_year_id=currency_year_id, energy_or_capacity_unit=energy_or_capacity_unit,
                  time_unit=time_unit, is_capital_cost=is_capital_cost, cost_of_capital=cost_of_capital,
                  book_life=book_life, throughput_correlation=throughput_correlation,
                  interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth)
        
        return obj

class SupplyCostData(DataObject):
    def __init__(self, parent_id=None, gau_id=None, demand_sector_id=None, resource_bin=None, year=None,
                 value=None, id=None):
        DataObject.__init__(self)

        self.parent_id = parent_id
        self.gau_id = gau_id
        self.demand_sector_id = demand_sector_id
        self.resource_bin = resource_bin
        self.year = year
        self.value = value
        self.id = id

    @classmethod
    def from_tuple(cls, tup):    
        (parent_id, gau_id, demand_sector_id, resource_bin, year, value, id) = tup
        
        obj = cls(parent_id=parent_id, gau_id=gau_id, demand_sector_id=demand_sector_id,
                  resource_bin=resource_bin, year=year, value=value, id=id)
        
        return obj

class SupplyEfficiency(DataObject):
    def __init__(self, id=None, geography_id=None, source=None, notes=None, input_unit=None, output_unit=None,
                 interpolation_method_id=None, extrapolation_method_id=None, extrapolation_growth=None):
        DataObject.__init__(self)

        self.id = id
        self.geography_id = geography_id
        self.source = source
        self.notes = notes
        self.input_unit = input_unit
        self.output_unit = output_unit
        self.interpolation_method_id = interpolation_method_id
        self.extrapolation_method_id = extrapolation_method_id
        self.extrapolation_growth = extrapolation_growth

    @classmethod
    def from_tuple(cls, tup):    
        (id, geography_id, source, notes, input_unit, output_unit, interpolation_method_id,
         extrapolation_method_id, extrapolation_growth) = tup
        
        obj = cls(id=id, geography_id=geography_id, source=source, notes=notes, input_unit=input_unit,
                  output_unit=output_unit, interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth)
        
        return obj

class SupplyEfficiencyData(DataObject):
    def __init__(self, parent_id=None, gau_id=None, efficiency_type_id=None, demand_sector_id=None,
                 supply_node_id=None, resource_bin=None, year=None, value=None, id=None):
        DataObject.__init__(self)

        self.parent_id = parent_id
        self.gau_id = gau_id
        self.efficiency_type_id = efficiency_type_id
        self.demand_sector_id = demand_sector_id
        self.supply_node_id = supply_node_id
        self.resource_bin = resource_bin
        self.year = year
        self.value = value
        self.id = id

    @classmethod
    def from_tuple(cls, tup):    
        (parent_id, gau_id, efficiency_type_id, demand_sector_id, supply_node_id, resource_bin,
         year, value, id) = tup
        
        obj = cls(parent_id=parent_id, gau_id=gau_id, efficiency_type_id=efficiency_type_id,
                  demand_sector_id=demand_sector_id, supply_node_id=supply_node_id,
                  resource_bin=resource_bin, year=year, value=value, id=id)
        
        return obj

class SupplyEmissions(DataObject):
    def __init__(self, supply_node_id=None, geography_id=None, other_index_1_id=None, mass_unit=None,
                 denominator_unit=None, interpolation_method_id=None, extrapolation_method_id=None,
                 extrapolation_growth=None, source=None, notes=None):
        DataObject.__init__(self)

        self.supply_node_id = supply_node_id
        self.geography_id = geography_id
        self.other_index_1_id = other_index_1_id
        self.mass_unit = mass_unit
        self.denominator_unit = denominator_unit
        self.interpolation_method_id = interpolation_method_id
        self.extrapolation_method_id = extrapolation_method_id
        self.extrapolation_growth = extrapolation_growth
        self.source = source
        self.notes = notes

    @classmethod
    def from_tuple(cls, tup):    
        (supply_node_id, geography_id, other_index_1_id, mass_unit, denominator_unit,
         interpolation_method_id, extrapolation_method_id, extrapolation_growth, source, notes) = tup
        
        obj = cls(supply_node_id=supply_node_id, geography_id=geography_id,
                  other_index_1_id=other_index_1_id, mass_unit=mass_unit,
                  denominator_unit=denominator_unit, interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth, source=source, notes=notes)
        
        return obj

class SupplyEmissionsData(DataObject):
    def __init__(self, supply_node_id=None, gau_id=None, demand_sector_id=None, oth_1_id=None, ghg_type_id=None,
                 ghg_id=None, year=None, value=None, id=None, sensitivity=None):
        DataObject.__init__(self)

        self.supply_node_id = supply_node_id
        self.gau_id = gau_id
        self.demand_sector_id = demand_sector_id
        self.oth_1_id = oth_1_id
        self.ghg_type_id = ghg_type_id
        self.ghg_id = ghg_id
        self.year = year
        self.value = value
        self.id = id
        self.sensitivity = sensitivity

    @classmethod
    def from_tuple(cls, tup):    
        (supply_node_id, gau_id, demand_sector_id, oth_1_id, ghg_type_id, ghg_id, year, value, id,
         sensitivity) = tup
        
        obj = cls(supply_node_id=supply_node_id, gau_id=gau_id, demand_sector_id=demand_sector_id,
                  oth_1_id=oth_1_id, ghg_type_id=ghg_type_id, ghg_id=ghg_id, year=year, value=value, id=id,
                  sensitivity=sensitivity)
        
        return obj

class SupplyExport(DataObject):
    def __init__(self, supply_node_id=None, geography_id=None, other_index_1_id=None, unit=None,
                 interpolation_method_id=None, extrapolation_method_id=None, extrapolation_growth=None):
        DataObject.__init__(self)

        self.supply_node_id = supply_node_id
        self.geography_id = geography_id
        self.other_index_1_id = other_index_1_id
        self.unit = unit
        self.interpolation_method_id = interpolation_method_id
        self.extrapolation_method_id = extrapolation_method_id
        self.extrapolation_growth = extrapolation_growth

    @classmethod
    def from_tuple(cls, tup):    
        (supply_node_id, geography_id, other_index_1_id, unit, interpolation_method_id,
         extrapolation_method_id, extrapolation_growth) = tup
        
        obj = cls(supply_node_id=supply_node_id, geography_id=geography_id,
                  other_index_1_id=other_index_1_id, unit=unit,
                  interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth)
        
        return obj

class SupplyExportData(DataObject):
    def __init__(self, supply_node_id=None, gau_id=None, oth_1_id=None, resource_bin=None, year=None, value=None,
                 id=None):
        DataObject.__init__(self)

        self.supply_node_id = supply_node_id
        self.gau_id = gau_id
        self.oth_1_id = oth_1_id
        self.resource_bin = resource_bin
        self.year = year
        self.value = value
        self.id = id

    @classmethod
    def from_tuple(cls, tup):    
        (supply_node_id, gau_id, oth_1_id, resource_bin, year, value, id) = tup
        
        obj = cls(supply_node_id=supply_node_id, gau_id=gau_id, oth_1_id=oth_1_id,
                  resource_bin=resource_bin, year=year, value=value, id=id)
        
        return obj

class SupplyExportMeasures(DataObject):
    def __init__(self, id=None, supply_node_id=None, name=None, geography_id=None, other_index_1_id=None,
                 interpolation_method_id=None, extrapolation_method_id=None, unit=None):
        DataObject.__init__(self)

        self.id = id
        self.supply_node_id = supply_node_id
        self.name = name
        self.geography_id = geography_id
        self.other_index_1_id = other_index_1_id
        self.interpolation_method_id = interpolation_method_id
        self.extrapolation_method_id = extrapolation_method_id
        self.unit = unit

    @classmethod
    def from_tuple(cls, tup):    
        (id, supply_node_id, name, geography_id, other_index_1_id, interpolation_method_id,
         extrapolation_method_id, unit) = tup
        
        obj = cls(id=id, supply_node_id=supply_node_id, name=name, geography_id=geography_id,
                  other_index_1_id=other_index_1_id, interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id, unit=unit)
        
        return obj

class SupplyExportMeasuresData(DataObject):
    def __init__(self, parent_id=None, gau_id=None, oth_1_id=None, year=None, value=None, id=None):
        DataObject.__init__(self)

        self.parent_id = parent_id
        self.gau_id = gau_id
        self.oth_1_id = oth_1_id
        self.year = year
        self.value = value
        self.id = id

    @classmethod
    def from_tuple(cls, tup):    
        (parent_id, gau_id, oth_1_id, year, value, id) = tup
        
        obj = cls(parent_id=parent_id, gau_id=gau_id, oth_1_id=oth_1_id, year=year, value=value, id=id)
        
        return obj

class SupplyNodes(DataObject):
    def __init__(self, id=None, name=None, supply_type_id=None, tradable_geography_id=None, is_active=None,
                 final_energy_link=None, is_curtailable=None, is_exportable=None, is_flexible=None,
                 residual_supply_node_id=None, mean_lifetime=None, lifetime_variance=None,
                 max_lifetime=None, min_lifetime=None, stock_decay_function_id=None, cost_of_capital=None,
                 book_life=None, geography_map_key_id=None, shape_id=None, max_lag_hours=None,
                 max_lead_hours=None, enforce_potential_constraint=None):
        DataObject.__init__(self)

        self.id = id
        self.name = name
        self.supply_type_id = supply_type_id
        self.tradable_geography_id = tradable_geography_id
        self.is_active = is_active
        self.final_energy_link = final_energy_link
        self.is_curtailable = is_curtailable
        self.is_exportable = is_exportable
        self.is_flexible = is_flexible
        self.residual_supply_node_id = residual_supply_node_id
        self.mean_lifetime = mean_lifetime
        self.lifetime_variance = lifetime_variance
        self.max_lifetime = max_lifetime
        self.min_lifetime = min_lifetime
        self.stock_decay_function_id = stock_decay_function_id
        self.cost_of_capital = cost_of_capital
        self.book_life = book_life
        self.geography_map_key_id = geography_map_key_id
        self.shape_id = shape_id
        self.max_lag_hours = max_lag_hours
        self.max_lead_hours = max_lead_hours
        self.enforce_potential_constraint = enforce_potential_constraint

    @classmethod
    def from_tuple(cls, tup):    
        (id, name, supply_type_id, tradable_geography_id, is_active, final_energy_link,
         is_curtailable, is_exportable, is_flexible, residual_supply_node_id, mean_lifetime,
         lifetime_variance, max_lifetime, min_lifetime, stock_decay_function_id, cost_of_capital,
         book_life, geography_map_key_id, shape_id, max_lag_hours, max_lead_hours,
         enforce_potential_constraint) = tup
        
        obj = cls(id=id, name=name, supply_type_id=supply_type_id,
                  tradable_geography_id=tradable_geography_id, is_active=is_active,
                  final_energy_link=final_energy_link, is_curtailable=is_curtailable,
                  is_exportable=is_exportable, is_flexible=is_flexible,
                  residual_supply_node_id=residual_supply_node_id, mean_lifetime=mean_lifetime,
                  lifetime_variance=lifetime_variance, max_lifetime=max_lifetime,
                  min_lifetime=min_lifetime, stock_decay_function_id=stock_decay_function_id,
                  cost_of_capital=cost_of_capital, book_life=book_life,
                  geography_map_key_id=geography_map_key_id, shape_id=shape_id,
                  max_lag_hours=max_lag_hours, max_lead_hours=max_lead_hours,
                  enforce_potential_constraint=enforce_potential_constraint)
        
        return obj

class SupplyPotential(DataObject):
    def __init__(self, supply_node_id=None, geography_id=None, other_index_1_id=None, unit=None, time_unit=None,
                 interpolation_method_id=None, extrapolation_growth=None, extrapolation_method_id=None,
                 geography_map_key_id=None):
        DataObject.__init__(self)

        self.supply_node_id = supply_node_id
        self.geography_id = geography_id
        self.other_index_1_id = other_index_1_id
        self.unit = unit
        self.time_unit = time_unit
        self.interpolation_method_id = interpolation_method_id
        self.extrapolation_growth = extrapolation_growth
        self.extrapolation_method_id = extrapolation_method_id
        self.geography_map_key_id = geography_map_key_id

    @classmethod
    def from_tuple(cls, tup):    
        (supply_node_id, geography_id, other_index_1_id, unit, time_unit, interpolation_method_id,
         extrapolation_growth, extrapolation_method_id, geography_map_key_id) = tup
        
        obj = cls(supply_node_id=supply_node_id, geography_id=geography_id,
                  other_index_1_id=other_index_1_id, unit=unit, time_unit=time_unit,
                  interpolation_method_id=interpolation_method_id,
                  extrapolation_growth=extrapolation_growth,
                  extrapolation_method_id=extrapolation_method_id,
                  geography_map_key_id=geography_map_key_id)
        
        return obj

class SupplyPotentialConversion(DataObject):
    def __init__(self, supply_node_id=None, geography_id=None, other_index_1_id=None, energy_unit_numerator=None,
                 resource_unit_denominator=None, interpolation_method_id=None,
                 extrapolation_method_id=None, extrapolation_growth=None):
        DataObject.__init__(self)

        self.supply_node_id = supply_node_id
        self.geography_id = geography_id
        self.other_index_1_id = other_index_1_id
        self.energy_unit_numerator = energy_unit_numerator
        self.resource_unit_denominator = resource_unit_denominator
        self.interpolation_method_id = interpolation_method_id
        self.extrapolation_method_id = extrapolation_method_id
        self.extrapolation_growth = extrapolation_growth

    @classmethod
    def from_tuple(cls, tup):    
        (supply_node_id, geography_id, other_index_1_id, energy_unit_numerator,
         resource_unit_denominator, interpolation_method_id, extrapolation_method_id,
         extrapolation_growth) = tup
        
        obj = cls(supply_node_id=supply_node_id, geography_id=geography_id,
                  other_index_1_id=other_index_1_id, energy_unit_numerator=energy_unit_numerator,
                  resource_unit_denominator=resource_unit_denominator,
                  interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth)
        
        return obj

class SupplyPotentialConversionData(DataObject):
    def __init__(self, supply_node_id=None, gau_id=None, oth_1_id=None, resource_bin=None, year=None, value=None,
                 id=None):
        DataObject.__init__(self)

        self.supply_node_id = supply_node_id
        self.gau_id = gau_id
        self.oth_1_id = oth_1_id
        self.resource_bin = resource_bin
        self.year = year
        self.value = value
        self.id = id

    @classmethod
    def from_tuple(cls, tup):    
        (supply_node_id, gau_id, oth_1_id, resource_bin, year, value, id) = tup
        
        obj = cls(supply_node_id=supply_node_id, gau_id=gau_id, oth_1_id=oth_1_id,
                  resource_bin=resource_bin, year=year, value=value, id=id)
        
        return obj

class SupplyPotentialData(DataObject):
    def __init__(self, supply_node_id=None, gau_id=None, demand_sector_id=None, oth_1_id=None, resource_bin=None,
                 year=None, value=None, id=None, sensitivity=None):
        DataObject.__init__(self)

        self.supply_node_id = supply_node_id
        self.gau_id = gau_id
        self.demand_sector_id = demand_sector_id
        self.oth_1_id = oth_1_id
        self.resource_bin = resource_bin
        self.year = year
        self.value = value
        self.id = id
        self.sensitivity = sensitivity

    @classmethod
    def from_tuple(cls, tup):    
        (supply_node_id, gau_id, demand_sector_id, oth_1_id, resource_bin, year, value, id,
         sensitivity) = tup
        
        obj = cls(supply_node_id=supply_node_id, gau_id=gau_id, demand_sector_id=demand_sector_id,
                  oth_1_id=oth_1_id, resource_bin=resource_bin, year=year, value=value, id=id,
                  sensitivity=sensitivity)
        
        return obj

class SupplySales(DataObject):
    def __init__(self, supply_node_id=None, geography_id=None, capacity_or_energy_unit=None, time_unit=None,
                 interpolation_method_id=None, extrapolation_method_id=None, extrapolation_growth=None,
                 geography_map_key_id=None):
        DataObject.__init__(self)

        self.supply_node_id = supply_node_id
        self.geography_id = geography_id
        self.capacity_or_energy_unit = capacity_or_energy_unit
        self.time_unit = time_unit
        self.interpolation_method_id = interpolation_method_id
        self.extrapolation_method_id = extrapolation_method_id
        self.extrapolation_growth = extrapolation_growth
        self.geography_map_key_id = geography_map_key_id

    @classmethod
    def from_tuple(cls, tup):    
        (supply_node_id, geography_id, capacity_or_energy_unit, time_unit, interpolation_method_id,
         extrapolation_method_id, extrapolation_growth, geography_map_key_id) = tup
        
        obj = cls(supply_node_id=supply_node_id, geography_id=geography_id,
                  capacity_or_energy_unit=capacity_or_energy_unit, time_unit=time_unit,
                  interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth, geography_map_key_id=geography_map_key_id)
        
        return obj

class SupplySalesData(DataObject):
    def __init__(self, supply_node_id=None, gau_id=None, demand_sector_id=None, supply_technology_id=None,
                 vintage=None, value=None, id=None, resource_bin=None):
        DataObject.__init__(self)

        self.supply_node_id = supply_node_id
        self.gau_id = gau_id
        self.demand_sector_id = demand_sector_id
        self.supply_technology_id = supply_technology_id
        self.vintage = vintage
        self.value = value
        self.id = id
        self.resource_bin = resource_bin

    @classmethod
    def from_tuple(cls, tup):    
        (supply_node_id, gau_id, demand_sector_id, supply_technology_id, vintage, value, id,
         resource_bin) = tup
        
        obj = cls(supply_node_id=supply_node_id, gau_id=gau_id, demand_sector_id=demand_sector_id,
                  supply_technology_id=supply_technology_id, vintage=vintage, value=value, id=id,
                  resource_bin=resource_bin)
        
        return obj

class SupplySalesMeasures(DataObject):
    def __init__(self, id=None, name=None, supply_technology_id=None, supply_node_id=None, geography_id=None,
                 other_index_1_id=None, interpolation_method_id=None, extrapolation_method_id=None,
                 extrapolation_growth=None, geography_map_key_id=None):
        DataObject.__init__(self)

        self.id = id
        self.name = name
        self.supply_technology_id = supply_technology_id
        self.supply_node_id = supply_node_id
        self.geography_id = geography_id
        self.other_index_1_id = other_index_1_id
        self.interpolation_method_id = interpolation_method_id
        self.extrapolation_method_id = extrapolation_method_id
        self.extrapolation_growth = extrapolation_growth
        self.geography_map_key_id = geography_map_key_id

    @classmethod
    def from_tuple(cls, tup):    
        (id, name, supply_technology_id, supply_node_id, geography_id, other_index_1_id,
         interpolation_method_id, extrapolation_method_id, extrapolation_growth,
         geography_map_key_id) = tup
        
        obj = cls(id=id, name=name, supply_technology_id=supply_technology_id,
                  supply_node_id=supply_node_id, geography_id=geography_id,
                  other_index_1_id=other_index_1_id, interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth, geography_map_key_id=geography_map_key_id)
        
        return obj

class SupplySalesMeasuresData(DataObject):
    def __init__(self, parent_id=None, gau_id=None, oth_1_id=None, demand_sector_id=None, resource_bin=None,
                 vintage=None, value=None, id=None):
        DataObject.__init__(self)

        self.parent_id = parent_id
        self.gau_id = gau_id
        self.oth_1_id = oth_1_id
        self.demand_sector_id = demand_sector_id
        self.resource_bin = resource_bin
        self.vintage = vintage
        self.value = value
        self.id = id

    @classmethod
    def from_tuple(cls, tup):    
        (parent_id, gau_id, oth_1_id, demand_sector_id, resource_bin, vintage, value, id) = tup
        
        obj = cls(parent_id=parent_id, gau_id=gau_id, oth_1_id=oth_1_id, demand_sector_id=demand_sector_id,
                  resource_bin=resource_bin, vintage=vintage, value=value, id=id)
        
        return obj

class SupplySalesShare(DataObject):
    def __init__(self, supply_node_id=None, geography_id=None, interpolation_method_id=None,
                 extrapolation_method_id=None, extrapolation_growth=None):
        DataObject.__init__(self)

        self.supply_node_id = supply_node_id
        self.geography_id = geography_id
        self.interpolation_method_id = interpolation_method_id
        self.extrapolation_method_id = extrapolation_method_id
        self.extrapolation_growth = extrapolation_growth

    @classmethod
    def from_tuple(cls, tup):    
        (supply_node_id, geography_id, interpolation_method_id, extrapolation_method_id,
         extrapolation_growth) = tup
        
        obj = cls(supply_node_id=supply_node_id, geography_id=geography_id,
                  interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth)
        
        return obj

class SupplySalesShareData(DataObject):
    def __init__(self, supply_node_id=None, gau_id=None, demand_sector_id=None, supply_technology_id=None,
                 vintage=None, value=None, id=None):
        DataObject.__init__(self)

        self.supply_node_id = supply_node_id
        self.gau_id = gau_id
        self.demand_sector_id = demand_sector_id
        self.supply_technology_id = supply_technology_id
        self.vintage = vintage
        self.value = value
        self.id = id

    @classmethod
    def from_tuple(cls, tup):    
        (supply_node_id, gau_id, demand_sector_id, supply_technology_id, vintage, value, id) = tup
        
        obj = cls(supply_node_id=supply_node_id, gau_id=gau_id, demand_sector_id=demand_sector_id,
                  supply_technology_id=supply_technology_id, vintage=vintage, value=value, id=id)
        
        return obj

class SupplySalesShareMeasures(DataObject):
    def __init__(self, id=None, name=None, supply_node_id=None, supply_technology_id=None,
                 replaced_supply_technology_id=None, geography_id=None, capacity_or_energy_unit=None,
                 time_unit=None, interpolation_method_id=None, extrapolation_method_id=None,
                 extrapolation_growth=None, other_index_1_id=None):
        DataObject.__init__(self)

        self.id = id
        self.name = name
        self.supply_node_id = supply_node_id
        self.supply_technology_id = supply_technology_id
        self.replaced_supply_technology_id = replaced_supply_technology_id
        self.geography_id = geography_id
        self.capacity_or_energy_unit = capacity_or_energy_unit
        self.time_unit = time_unit
        self.interpolation_method_id = interpolation_method_id
        self.extrapolation_method_id = extrapolation_method_id
        self.extrapolation_growth = extrapolation_growth
        self.other_index_1_id = other_index_1_id

    @classmethod
    def from_tuple(cls, tup):    
        (id, name, supply_node_id, supply_technology_id, replaced_supply_technology_id,
         geography_id, capacity_or_energy_unit, time_unit, interpolation_method_id,
         extrapolation_method_id, extrapolation_growth, other_index_1_id) = tup
        
        obj = cls(id=id, name=name, supply_node_id=supply_node_id,
                  supply_technology_id=supply_technology_id,
                  replaced_supply_technology_id=replaced_supply_technology_id, geography_id=geography_id,
                  capacity_or_energy_unit=capacity_or_energy_unit, time_unit=time_unit,
                  interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth, other_index_1_id=other_index_1_id)
        
        return obj

class SupplySalesShareMeasuresData(DataObject):
    def __init__(self, parent_id=None, gau_id=None, demand_sector_id=None, vintage=None, value=None, id=None,
                 resource_bin=None, oth_1_id=None):
        DataObject.__init__(self)

        self.parent_id = parent_id
        self.gau_id = gau_id
        self.demand_sector_id = demand_sector_id
        self.vintage = vintage
        self.value = value
        self.id = id
        self.resource_bin = resource_bin
        self.oth_1_id = oth_1_id

    @classmethod
    def from_tuple(cls, tup):    
        (parent_id, gau_id, demand_sector_id, vintage, value, id, resource_bin, oth_1_id) = tup
        
        obj = cls(parent_id=parent_id, gau_id=gau_id, demand_sector_id=demand_sector_id, vintage=vintage,
                  value=value, id=id, resource_bin=resource_bin, oth_1_id=oth_1_id)
        
        return obj

class SupplyStock(DataObject):
    def __init__(self, supply_node_id=None, geography_id=None, capacity_or_energy_unit=None, time_unit=None,
                 interpolation_method_id=None, extrapolation_method_id=None, extrapolation_growth=None,
                 geography_map_key_id=None):
        DataObject.__init__(self)

        self.supply_node_id = supply_node_id
        self.geography_id = geography_id
        self.capacity_or_energy_unit = capacity_or_energy_unit
        self.time_unit = time_unit
        self.interpolation_method_id = interpolation_method_id
        self.extrapolation_method_id = extrapolation_method_id
        self.extrapolation_growth = extrapolation_growth
        self.geography_map_key_id = geography_map_key_id

    @classmethod
    def from_tuple(cls, tup):    
        (supply_node_id, geography_id, capacity_or_energy_unit, time_unit, interpolation_method_id,
         extrapolation_method_id, extrapolation_growth, geography_map_key_id) = tup
        
        obj = cls(supply_node_id=supply_node_id, geography_id=geography_id,
                  capacity_or_energy_unit=capacity_or_energy_unit, time_unit=time_unit,
                  interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth, geography_map_key_id=geography_map_key_id)
        
        return obj

class SupplyStockData(DataObject):
    def __init__(self, supply_node_id=None, gau_id=None, demand_sector_id=None, supply_technology_id=None,
                 resource_bin=None, year=None, value=None, id=None, sensitivity=None):
        DataObject.__init__(self)

        self.supply_node_id = supply_node_id
        self.gau_id = gau_id
        self.demand_sector_id = demand_sector_id
        self.supply_technology_id = supply_technology_id
        self.resource_bin = resource_bin
        self.year = year
        self.value = value
        self.id = id
        self.sensitivity = sensitivity

    @classmethod
    def from_tuple(cls, tup):    
        (supply_node_id, gau_id, demand_sector_id, supply_technology_id, resource_bin, year, value,
         id, sensitivity) = tup
        
        obj = cls(supply_node_id=supply_node_id, gau_id=gau_id, demand_sector_id=demand_sector_id,
                  supply_technology_id=supply_technology_id, resource_bin=resource_bin, year=year,
                  value=value, id=id, sensitivity=sensitivity)
        
        return obj

class SupplyStockMeasures(DataObject):
    def __init__(self, id=None, name=None, supply_technology_id=None, supply_node_id=None, geography_id=None,
                 other_index_1_id=None, capacity_or_energy_unit=None, time_unit=None,
                 interpolation_method_id=None, extrapolation_method_id=None, extrapolation_growth=None,
                 geography_map_key_id=None):
        DataObject.__init__(self)

        self.id = id
        self.name = name
        self.supply_technology_id = supply_technology_id
        self.supply_node_id = supply_node_id
        self.geography_id = geography_id
        self.other_index_1_id = other_index_1_id
        self.capacity_or_energy_unit = capacity_or_energy_unit
        self.time_unit = time_unit
        self.interpolation_method_id = interpolation_method_id
        self.extrapolation_method_id = extrapolation_method_id
        self.extrapolation_growth = extrapolation_growth
        self.geography_map_key_id = geography_map_key_id

    @classmethod
    def from_tuple(cls, tup):    
        (id, name, supply_technology_id, supply_node_id, geography_id, other_index_1_id,
         capacity_or_energy_unit, time_unit, interpolation_method_id, extrapolation_method_id,
         extrapolation_growth, geography_map_key_id) = tup
        
        obj = cls(id=id, name=name, supply_technology_id=supply_technology_id,
                  supply_node_id=supply_node_id, geography_id=geography_id,
                  other_index_1_id=other_index_1_id, capacity_or_energy_unit=capacity_or_energy_unit,
                  time_unit=time_unit, interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth, geography_map_key_id=geography_map_key_id)
        
        return obj

class SupplyStockMeasuresData(DataObject):
    def __init__(self, parent_id=None, gau_id=None, oth_1_id=None, demand_sector_id=None, year=None, value=None,
                 id=None, resource_bin=None):
        DataObject.__init__(self)

        self.parent_id = parent_id
        self.gau_id = gau_id
        self.oth_1_id = oth_1_id
        self.demand_sector_id = demand_sector_id
        self.year = year
        self.value = value
        self.id = id
        self.resource_bin = resource_bin

    @classmethod
    def from_tuple(cls, tup):    
        (parent_id, gau_id, oth_1_id, demand_sector_id, year, value, id, resource_bin) = tup
        
        obj = cls(parent_id=parent_id, gau_id=gau_id, oth_1_id=oth_1_id, demand_sector_id=demand_sector_id,
                  year=year, value=value, id=id, resource_bin=resource_bin)
        
        return obj

class SupplyTechs(DataObject):
    def __init__(self, id=None, name=None, supply_node_id=None, source=None, additional_description=None,
                 stock_decay_function_id=None, book_life=None, mean_lifetime=None, lifetime_variance=None,
                 min_lifetime=None, max_lifetime=None, discharge_duration=None, cost_of_capital=None,
                 shape_id=None, max_lag_hours=None, max_lead_hours=None, thermal_capacity_multiplier=None):
        DataObject.__init__(self)

        self.id = id
        self.name = name
        self.supply_node_id = supply_node_id
        self.source = source
        self.additional_description = additional_description
        self.stock_decay_function_id = stock_decay_function_id
        self.book_life = book_life
        self.mean_lifetime = mean_lifetime
        self.lifetime_variance = lifetime_variance
        self.min_lifetime = min_lifetime
        self.max_lifetime = max_lifetime
        self.discharge_duration = discharge_duration
        self.cost_of_capital = cost_of_capital
        self.shape_id = shape_id
        self.max_lag_hours = max_lag_hours
        self.max_lead_hours = max_lead_hours
        self.thermal_capacity_multiplier = thermal_capacity_multiplier

    @classmethod
    def from_tuple(cls, tup):    
        (id, name, supply_node_id, source, additional_description, stock_decay_function_id,
         book_life, mean_lifetime, lifetime_variance, min_lifetime, max_lifetime,
         discharge_duration, cost_of_capital, shape_id, max_lag_hours, max_lead_hours,
         thermal_capacity_multiplier) = tup
        
        obj = cls(id=id, name=name, supply_node_id=supply_node_id, source=source,
                  additional_description=additional_description,
                  stock_decay_function_id=stock_decay_function_id, book_life=book_life,
                  mean_lifetime=mean_lifetime, lifetime_variance=lifetime_variance,
                  min_lifetime=min_lifetime, max_lifetime=max_lifetime,
                  discharge_duration=discharge_duration, cost_of_capital=cost_of_capital,
                  shape_id=shape_id, max_lag_hours=max_lag_hours, max_lead_hours=max_lead_hours,
                  thermal_capacity_multiplier=thermal_capacity_multiplier)
        
        return obj

class SupplyTechsCO2Capture(DataObject):
    def __init__(self, supply_tech_id=None, definition_id=None, geography_id=None, reference_tech_id=None,
                 interpolation_method_id=None, extrapolation_method_id=None, extrapolation_growth=None,
                 age_growth_or_decay_type_id=None, age_growth_or_decay=None):
        DataObject.__init__(self)

        self.supply_tech_id = supply_tech_id
        self.definition_id = definition_id
        self.geography_id = geography_id
        self.reference_tech_id = reference_tech_id
        self.interpolation_method_id = interpolation_method_id
        self.extrapolation_method_id = extrapolation_method_id
        self.extrapolation_growth = extrapolation_growth
        self.age_growth_or_decay_type_id = age_growth_or_decay_type_id
        self.age_growth_or_decay = age_growth_or_decay

    @classmethod
    def from_tuple(cls, tup):    
        (supply_tech_id, definition_id, geography_id, reference_tech_id, interpolation_method_id,
         extrapolation_method_id, extrapolation_growth, age_growth_or_decay_type_id,
         age_growth_or_decay) = tup
        
        obj = cls(supply_tech_id=supply_tech_id, definition_id=definition_id, geography_id=geography_id,
                  reference_tech_id=reference_tech_id, interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth,
                  age_growth_or_decay_type_id=age_growth_or_decay_type_id,
                  age_growth_or_decay=age_growth_or_decay)
        
        return obj

class SupplyTechsCO2CaptureData(DataObject):
    def __init__(self, supply_tech_id=None, gau_id=None, resource_bin=None, vintage=None, value=None, id=None):
        DataObject.__init__(self)

        self.supply_tech_id = supply_tech_id
        self.gau_id = gau_id
        self.resource_bin = resource_bin
        self.vintage = vintage
        self.value = value
        self.id = id

    @classmethod
    def from_tuple(cls, tup):    
        (supply_tech_id, gau_id, resource_bin, vintage, value, id) = tup
        
        obj = cls(supply_tech_id=supply_tech_id, gau_id=gau_id, resource_bin=resource_bin, vintage=vintage,
                  value=value, id=id)
        
        return obj

class SupplyTechsCapacityFactor(DataObject):
    def __init__(self, supply_tech_id=None, geography_id=None, reference_tech_id=None, definition_id=None,
                 interpolation_method_id=None, extrapolation_method_id=None, extrapolation_growth=None,
                 age_growth_or_decay_type_id=None, age_growth_or_decay=None):
        DataObject.__init__(self)

        self.supply_tech_id = supply_tech_id
        self.geography_id = geography_id
        self.reference_tech_id = reference_tech_id
        self.definition_id = definition_id
        self.interpolation_method_id = interpolation_method_id
        self.extrapolation_method_id = extrapolation_method_id
        self.extrapolation_growth = extrapolation_growth
        self.age_growth_or_decay_type_id = age_growth_or_decay_type_id
        self.age_growth_or_decay = age_growth_or_decay

    @classmethod
    def from_tuple(cls, tup):    
        (supply_tech_id, geography_id, reference_tech_id, definition_id, interpolation_method_id,
         extrapolation_method_id, extrapolation_growth, age_growth_or_decay_type_id,
         age_growth_or_decay) = tup
        
        obj = cls(supply_tech_id=supply_tech_id, geography_id=geography_id,
                  reference_tech_id=reference_tech_id, definition_id=definition_id,
                  interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth,
                  age_growth_or_decay_type_id=age_growth_or_decay_type_id,
                  age_growth_or_decay=age_growth_or_decay)
        
        return obj

class SupplyTechsCapacityFactorData(DataObject):
    def __init__(self, supply_tech_id=None, gau_id=None, oth_1_id=None, resource_bin=None, vintage=None,
                 value=None, id=None):
        DataObject.__init__(self)

        self.supply_tech_id = supply_tech_id
        self.gau_id = gau_id
        self.oth_1_id = oth_1_id
        self.resource_bin = resource_bin
        self.vintage = vintage
        self.value = value
        self.id = id

    @classmethod
    def from_tuple(cls, tup):    
        (supply_tech_id, gau_id, oth_1_id, resource_bin, vintage, value, id) = tup
        
        obj = cls(supply_tech_id=supply_tech_id, gau_id=gau_id, oth_1_id=oth_1_id,
                  resource_bin=resource_bin, vintage=vintage, value=value, id=id)
        
        return obj

class SupplyTechsCapitalCost(DataObject):
    def __init__(self, supply_tech_id=None, definition_id=None, reference_tech_id=None, geography_id=None,
                 currency_id=None, currency_year_id=None, capacity_or_energy_unit=None, time_unit=None,
                 is_levelized=None, interpolation_method_id=None, extrapolation_method_id=None,
                 extrapolation_growth=None, source=None, notes=None, geography_map_key_id=None):
        DataObject.__init__(self)

        self.supply_tech_id = supply_tech_id
        self.definition_id = definition_id
        self.reference_tech_id = reference_tech_id
        self.geography_id = geography_id
        self.currency_id = currency_id
        self.currency_year_id = currency_year_id
        self.capacity_or_energy_unit = capacity_or_energy_unit
        self.time_unit = time_unit
        self.is_levelized = is_levelized
        self.interpolation_method_id = interpolation_method_id
        self.extrapolation_method_id = extrapolation_method_id
        self.extrapolation_growth = extrapolation_growth
        self.source = source
        self.notes = notes
        self.geography_map_key_id = geography_map_key_id

    @classmethod
    def from_tuple(cls, tup):    
        (supply_tech_id, definition_id, reference_tech_id, geography_id, currency_id,
         currency_year_id, capacity_or_energy_unit, time_unit, is_levelized,
         interpolation_method_id, extrapolation_method_id, extrapolation_growth, source, notes,
         geography_map_key_id) = tup
        
        obj = cls(supply_tech_id=supply_tech_id, definition_id=definition_id,
                  reference_tech_id=reference_tech_id, geography_id=geography_id, currency_id=currency_id,
                  currency_year_id=currency_year_id, capacity_or_energy_unit=capacity_or_energy_unit,
                  time_unit=time_unit, is_levelized=is_levelized,
                  interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth, source=source, notes=notes,
                  geography_map_key_id=geography_map_key_id)
        
        return obj

class SupplyTechsCapitalCostNewData(DataObject):
    def __init__(self, supply_tech_id=None, gau_id=None, demand_sector_id=None, resource_bin=None, vintage=None,
                 value=None, id=None, sensitivity=None):
        DataObject.__init__(self)

        self.supply_tech_id = supply_tech_id
        self.gau_id = gau_id
        self.demand_sector_id = demand_sector_id
        self.resource_bin = resource_bin
        self.vintage = vintage
        self.value = value
        self.id = id
        self.sensitivity = sensitivity

    @classmethod
    def from_tuple(cls, tup):    
        (supply_tech_id, gau_id, demand_sector_id, resource_bin, vintage, value, id, sensitivity) = tup
        
        obj = cls(supply_tech_id=supply_tech_id, gau_id=gau_id, demand_sector_id=demand_sector_id,
                  resource_bin=resource_bin, vintage=vintage, value=value, id=id, sensitivity=sensitivity)
        
        return obj

class SupplyTechsCapitalCostReplacementData(DataObject):
    def __init__(self, supply_tech_id=None, gau_id=None, demand_sector_id=None, resource_bin=None, vintage=None,
                 value=None, id=None, sensitivity=None):
        DataObject.__init__(self)

        self.supply_tech_id = supply_tech_id
        self.gau_id = gau_id
        self.demand_sector_id = demand_sector_id
        self.resource_bin = resource_bin
        self.vintage = vintage
        self.value = value
        self.id = id
        self.sensitivity = sensitivity

    @classmethod
    def from_tuple(cls, tup):    
        (supply_tech_id, gau_id, demand_sector_id, resource_bin, vintage, value, id, sensitivity) = tup
        
        obj = cls(supply_tech_id=supply_tech_id, gau_id=gau_id, demand_sector_id=demand_sector_id,
                  resource_bin=resource_bin, vintage=vintage, value=value, id=id, sensitivity=sensitivity)
        
        return obj

class SupplyTechsEfficiency(DataObject):
    def __init__(self, supply_tech_id=None, geography_id=None, definition_id=None, reference_tech_id=None,
                 input_unit=None, output_unit=None, interpolation_method_id=None,
                 extrapolation_method_id=None, extrapolation_growth=None,
                 age_growth_or_decay_type_id=None, age_growth_or_decay=None, source=None, notes=None):
        DataObject.__init__(self)

        self.supply_tech_id = supply_tech_id
        self.geography_id = geography_id
        self.definition_id = definition_id
        self.reference_tech_id = reference_tech_id
        self.input_unit = input_unit
        self.output_unit = output_unit
        self.interpolation_method_id = interpolation_method_id
        self.extrapolation_method_id = extrapolation_method_id
        self.extrapolation_growth = extrapolation_growth
        self.age_growth_or_decay_type_id = age_growth_or_decay_type_id
        self.age_growth_or_decay = age_growth_or_decay
        self.source = source
        self.notes = notes

    @classmethod
    def from_tuple(cls, tup):    
        (supply_tech_id, geography_id, definition_id, reference_tech_id, input_unit, output_unit,
         interpolation_method_id, extrapolation_method_id, extrapolation_growth,
         age_growth_or_decay_type_id, age_growth_or_decay, source, notes) = tup
        
        obj = cls(supply_tech_id=supply_tech_id, geography_id=geography_id, definition_id=definition_id,
                  reference_tech_id=reference_tech_id, input_unit=input_unit, output_unit=output_unit,
                  interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth,
                  age_growth_or_decay_type_id=age_growth_or_decay_type_id,
                  age_growth_or_decay=age_growth_or_decay, source=source, notes=notes)
        
        return obj

class SupplyTechsEfficiencyData(DataObject):
    def __init__(self, supply_tech_id=None, supply_node_id=None, efficiency_type_id=None, gau_id=None,
                 demand_sector_id=None, resource_bin=None, vintage=None, value=None, id=None,
                 sensitivity=None):
        DataObject.__init__(self)

        self.supply_tech_id = supply_tech_id
        self.supply_node_id = supply_node_id
        self.efficiency_type_id = efficiency_type_id
        self.gau_id = gau_id
        self.demand_sector_id = demand_sector_id
        self.resource_bin = resource_bin
        self.vintage = vintage
        self.value = value
        self.id = id
        self.sensitivity = sensitivity

    @classmethod
    def from_tuple(cls, tup):    
        (supply_tech_id, supply_node_id, efficiency_type_id, gau_id, demand_sector_id,
         resource_bin, vintage, value, id, sensitivity) = tup
        
        obj = cls(supply_tech_id=supply_tech_id, supply_node_id=supply_node_id,
                  efficiency_type_id=efficiency_type_id, gau_id=gau_id, demand_sector_id=demand_sector_id,
                  resource_bin=resource_bin, vintage=vintage, value=value, id=id, sensitivity=sensitivity)
        
        return obj

class SupplyTechsFixedMaintenanceCost(DataObject):
    def __init__(self, supply_tech_id=None, definition_id=None, reference_tech_id=None, geography_id=None,
                 currency_id=None, currency_year_id=None, capacity_or_energy_unit=None, time_unit=None,
                 interpolation_method_id=None, extrapolation_method_id=None, extrapolation_growth=None,
                 age_growth_or_decay_type_id=None, age_growth_or_decay=None, source=None, notes=None):
        DataObject.__init__(self)

        self.supply_tech_id = supply_tech_id
        self.definition_id = definition_id
        self.reference_tech_id = reference_tech_id
        self.geography_id = geography_id
        self.currency_id = currency_id
        self.currency_year_id = currency_year_id
        self.capacity_or_energy_unit = capacity_or_energy_unit
        self.time_unit = time_unit
        self.interpolation_method_id = interpolation_method_id
        self.extrapolation_method_id = extrapolation_method_id
        self.extrapolation_growth = extrapolation_growth
        self.age_growth_or_decay_type_id = age_growth_or_decay_type_id
        self.age_growth_or_decay = age_growth_or_decay
        self.source = source
        self.notes = notes

    @classmethod
    def from_tuple(cls, tup):    
        (supply_tech_id, definition_id, reference_tech_id, geography_id, currency_id,
         currency_year_id, capacity_or_energy_unit, time_unit, interpolation_method_id,
         extrapolation_method_id, extrapolation_growth, age_growth_or_decay_type_id,
         age_growth_or_decay, source, notes) = tup
        
        obj = cls(supply_tech_id=supply_tech_id, definition_id=definition_id,
                  reference_tech_id=reference_tech_id, geography_id=geography_id, currency_id=currency_id,
                  currency_year_id=currency_year_id, capacity_or_energy_unit=capacity_or_energy_unit,
                  time_unit=time_unit, interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth,
                  age_growth_or_decay_type_id=age_growth_or_decay_type_id,
                  age_growth_or_decay=age_growth_or_decay, source=source, notes=notes)
        
        return obj

class SupplyTechsFixedMaintenanceCostData(DataObject):
    def __init__(self, supply_tech_id=None, gau_id=None, demand_sector_id=None, resource_bin=None, vintage=None,
                 value=None, id=None, sensitivity=None):
        DataObject.__init__(self)

        self.supply_tech_id = supply_tech_id
        self.gau_id = gau_id
        self.demand_sector_id = demand_sector_id
        self.resource_bin = resource_bin
        self.vintage = vintage
        self.value = value
        self.id = id
        self.sensitivity = sensitivity

    @classmethod
    def from_tuple(cls, tup):    
        (supply_tech_id, gau_id, demand_sector_id, resource_bin, vintage, value, id, sensitivity) = tup
        
        obj = cls(supply_tech_id=supply_tech_id, gau_id=gau_id, demand_sector_id=demand_sector_id,
                  resource_bin=resource_bin, vintage=vintage, value=value, id=id, sensitivity=sensitivity)
        
        return obj

class SupplyTechsInstallationCost(DataObject):
    def __init__(self, supply_tech_id=None, definition_id=None, geography_id=None, reference_tech_id=None,
                 currency_id=None, currency_year_id=None, capacity_or_energy_unit=None, time_unit=None,
                 is_levelized=None, interpolation_method_id=None, extrapolation_method_id=None,
                 extrapolation_growth=None, source=None, notes=None):
        DataObject.__init__(self)

        self.supply_tech_id = supply_tech_id
        self.definition_id = definition_id
        self.geography_id = geography_id
        self.reference_tech_id = reference_tech_id
        self.currency_id = currency_id
        self.currency_year_id = currency_year_id
        self.capacity_or_energy_unit = capacity_or_energy_unit
        self.time_unit = time_unit
        self.is_levelized = is_levelized
        self.interpolation_method_id = interpolation_method_id
        self.extrapolation_method_id = extrapolation_method_id
        self.extrapolation_growth = extrapolation_growth
        self.source = source
        self.notes = notes

    @classmethod
    def from_tuple(cls, tup):    
        (supply_tech_id, definition_id, geography_id, reference_tech_id, currency_id,
         currency_year_id, capacity_or_energy_unit, time_unit, is_levelized,
         interpolation_method_id, extrapolation_method_id, extrapolation_growth, source, notes) = tup
        
        obj = cls(supply_tech_id=supply_tech_id, definition_id=definition_id, geography_id=geography_id,
                  reference_tech_id=reference_tech_id, currency_id=currency_id,
                  currency_year_id=currency_year_id, capacity_or_energy_unit=capacity_or_energy_unit,
                  time_unit=time_unit, is_levelized=is_levelized,
                  interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth, source=source, notes=notes)
        
        return obj

class SupplyTechsInstallationCostNewData(DataObject):
    def __init__(self, supply_tech_id=None, gau_id=None, demand_sector_id=None, resource_bin=None, vintage=None,
                 value=None, id=None, sensitivity=None):
        DataObject.__init__(self)

        self.supply_tech_id = supply_tech_id
        self.gau_id = gau_id
        self.demand_sector_id = demand_sector_id
        self.resource_bin = resource_bin
        self.vintage = vintage
        self.value = value
        self.id = id
        self.sensitivity = sensitivity

    @classmethod
    def from_tuple(cls, tup):    
        (supply_tech_id, gau_id, demand_sector_id, resource_bin, vintage, value, id, sensitivity) = tup
        
        obj = cls(supply_tech_id=supply_tech_id, gau_id=gau_id, demand_sector_id=demand_sector_id,
                  resource_bin=resource_bin, vintage=vintage, value=value, id=id, sensitivity=sensitivity)
        
        return obj

class SupplyTechsInstallationCostReplacementData(DataObject):
    def __init__(self, supply_tech_id=None, gau_id=None, demand_sector_id=None, resource_bin=None, vintage=None,
                 value=None, id=None, sensitivity=None):
        DataObject.__init__(self)

        self.supply_tech_id = supply_tech_id
        self.gau_id = gau_id
        self.demand_sector_id = demand_sector_id
        self.resource_bin = resource_bin
        self.vintage = vintage
        self.value = value
        self.id = id
        self.sensitivity = sensitivity

    @classmethod
    def from_tuple(cls, tup):    
        (supply_tech_id, gau_id, demand_sector_id, resource_bin, vintage, value, id, sensitivity) = tup
        
        obj = cls(supply_tech_id=supply_tech_id, gau_id=gau_id, demand_sector_id=demand_sector_id,
                  resource_bin=resource_bin, vintage=vintage, value=value, id=id, sensitivity=sensitivity)
        
        return obj

class SupplyTechsVariableMaintenanceCost(DataObject):
    def __init__(self, supply_tech_id=None, definition_id=None, reference_tech_id=None, currency_id=None,
                 geography_id=None, currency_year_id=None, energy_unit=None, interpolation_method_id=None,
                 extrapolation_method_id=None, extrapolation_growth=None,
                 age_growth_or_decay_type_id=None, age_growth_or_decay=None, source=None, notes=None):
        DataObject.__init__(self)

        self.supply_tech_id = supply_tech_id
        self.definition_id = definition_id
        self.reference_tech_id = reference_tech_id
        self.currency_id = currency_id
        self.geography_id = geography_id
        self.currency_year_id = currency_year_id
        self.energy_unit = energy_unit
        self.interpolation_method_id = interpolation_method_id
        self.extrapolation_method_id = extrapolation_method_id
        self.extrapolation_growth = extrapolation_growth
        self.age_growth_or_decay_type_id = age_growth_or_decay_type_id
        self.age_growth_or_decay = age_growth_or_decay
        self.source = source
        self.notes = notes

    @classmethod
    def from_tuple(cls, tup):    
        (supply_tech_id, definition_id, reference_tech_id, currency_id, geography_id,
         currency_year_id, energy_unit, interpolation_method_id, extrapolation_method_id,
         extrapolation_growth, age_growth_or_decay_type_id, age_growth_or_decay, source, notes) = tup
        
        obj = cls(supply_tech_id=supply_tech_id, definition_id=definition_id,
                  reference_tech_id=reference_tech_id, currency_id=currency_id, geography_id=geography_id,
                  currency_year_id=currency_year_id, energy_unit=energy_unit,
                  interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth,
                  age_growth_or_decay_type_id=age_growth_or_decay_type_id,
                  age_growth_or_decay=age_growth_or_decay, source=source, notes=notes)
        
        return obj

class SupplyTechsVariableMaintenanceCostData(DataObject):
    def __init__(self, supply_tech_id=None, gau_id=None, demand_sector_id=None, resource_bin=None, vintage=None,
                 value=None, id=None, sensitivity=None):
        DataObject.__init__(self)

        self.supply_tech_id = supply_tech_id
        self.gau_id = gau_id
        self.demand_sector_id = demand_sector_id
        self.resource_bin = resource_bin
        self.vintage = vintage
        self.value = value
        self.id = id
        self.sensitivity = sensitivity

    @classmethod
    def from_tuple(cls, tup):    
        (supply_tech_id, gau_id, demand_sector_id, resource_bin, vintage, value, id, sensitivity) = tup
        
        obj = cls(supply_tech_id=supply_tech_id, gau_id=gau_id, demand_sector_id=demand_sector_id,
                  resource_bin=resource_bin, vintage=vintage, value=value, id=id, sensitivity=sensitivity)
        
        return obj

class Version(DataObject):
    def __init__(self, version_number=None, date=None, author=None):
        DataObject.__init__(self)

        self.version_number = version_number
        self.date = date
        self.author = author

    @classmethod
    def from_tuple(cls, tup):    
        (version_number, date, author) = tup
        
        obj = cls(version_number=version_number, date=date, author=author)
        
        return obj

