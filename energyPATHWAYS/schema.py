## Start of boilerplate.py ##

import sys
from energyPATHWAYS.error import UnknownDataClass
from energyPATHWAYS.data_object import DataObject
from energyPATHWAYS.database import get_database

_Module = sys.modules[__name__]  # get ref to our own module object

def class_for_table(tbl_name):
    try:
        cls = getattr(_Module, tbl_name)
    except AttributeError:
        raise UnknownDataClass(tbl_name)

    return cls

def load_data_objects(scenario, load_children=True):

    db = get_database()

    table_names = db.tables_with_classes()
    table_objs  = [db.get_table(name) for name in table_names]

    for tbl in table_objs:
        name = tbl.name
        cls = class_for_table(name)
        tbl.load_data_object(cls, scenario)

    if load_children:
        missing = {}
        for tbl in table_objs:
            tbl.link_children(missing)

    print("Done loading data objects")

## End of boilerplate.py ##

class AgeGrowthOrDecayType(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, id=None, name=None):
        DataObject.__init__(self, scenario)
        AgeGrowthOrDecayType._instances_by_id[id] = self

        self.id = id
        self.name = name

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (id, name) = tup

        obj = cls(scenario, id=id, name=name)

        return obj

class BlendNodeBlendMeasures(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, id=None, name=None, blend_node_id=None, supply_node_id=None, geography_id=None,
                 other_index_1_id=None, interpolation_method_id=None, extrapolation_method_id=None,
                 extrapolation_growth=None):
        DataObject.__init__(self, scenario)
        BlendNodeBlendMeasures._instances_by_id[id] = self

        self.id = id
        self.name = name
        self.blend_node_id = blend_node_id
        self.supply_node_id = supply_node_id
        self.geography_id = geography_id
        self.other_index_1_id = other_index_1_id
        self.interpolation_method_id = interpolation_method_id
        self.extrapolation_method_id = extrapolation_method_id
        self.extrapolation_growth = extrapolation_growth

        # ints mapped to strings
        self._extrapolation_method = None
        self._geography = None
        self._interpolation_method = None
        self._other_index_1 = None

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (id, name, blend_node_id, supply_node_id, geography_id, other_index_1_id,
         interpolation_method_id, extrapolation_method_id, extrapolation_growth) = tup

        obj = cls(scenario, id=id, name=name, blend_node_id=blend_node_id, supply_node_id=supply_node_id,
                  geography_id=geography_id, other_index_1_id=other_index_1_id,
                  interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth)

        return obj

class BlendNodeBlendMeasuresData(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, parent_id=None, gau_id=None, year=None, value=None, id=None, demand_sector_id=None):
        DataObject.__init__(self, scenario)
        BlendNodeBlendMeasuresData._instances_by_id[id] = self

        self.parent_id = parent_id
        self.gau_id = gau_id
        self.year = year
        self.value = value
        self.id = id
        self.demand_sector_id = demand_sector_id

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (parent_id, gau_id, year, value, id, demand_sector_id) = tup

        obj = cls(scenario, parent_id=parent_id, gau_id=gau_id, year=year, value=value, id=id,
                  demand_sector_id=demand_sector_id)

        return obj

class BlendNodeInputsData(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, blend_node_id=None, supply_node_id=None, id=None):
        DataObject.__init__(self, scenario)
        BlendNodeInputsData._instances_by_id[id] = self

        self.blend_node_id = blend_node_id
        self.supply_node_id = supply_node_id
        self.id = id

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (blend_node_id, supply_node_id, id) = tup

        obj = cls(scenario, blend_node_id=blend_node_id, supply_node_id=supply_node_id, id=id)

        return obj

class CO2PriceMeasures(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, id=None, name=None, geography_id=None, interpolation_method_id=None,
                 extrapolation_method_id=None, extrapolation_growth=None, geography_map_key_id=None,
                 supply_node_id=None):
        DataObject.__init__(self, scenario)
        CO2PriceMeasures._instances_by_id[id] = self

        self.id = id
        self.name = name
        self.geography_id = geography_id
        self.interpolation_method_id = interpolation_method_id
        self.extrapolation_method_id = extrapolation_method_id
        self.extrapolation_growth = extrapolation_growth
        self.geography_map_key_id = geography_map_key_id
        self.supply_node_id = supply_node_id

        # ints mapped to strings
        self._extrapolation_method = None
        self._geography = None
        self._geography_map_key = None
        self._interpolation_method = None

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (id, name, geography_id, interpolation_method_id, extrapolation_method_id,
         extrapolation_growth, geography_map_key_id, supply_node_id) = tup

        obj = cls(scenario, id=id, name=name, geography_id=geography_id,
                  interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth, geography_map_key_id=geography_map_key_id,
                  supply_node_id=supply_node_id)

        return obj

class CO2PriceMeasuresData(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, parent_id=None, gau_id=None, year=None, value=None, id=None, sensitivity=None):
        DataObject.__init__(self, scenario)
        CO2PriceMeasuresData._instances_by_id[id] = self

        self.parent_id = parent_id
        self.gau_id = gau_id
        self.year = year
        self.value = value
        self.id = id
        self.sensitivity = sensitivity

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (parent_id, gau_id, year, value, id, sensitivity) = tup

        obj = cls(scenario, parent_id=parent_id, gau_id=gau_id, year=year, value=value, id=id, sensitivity=sensitivity)

        return obj

class CleaningMethods(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, id=None, name=None):
        DataObject.__init__(self, scenario)
        CleaningMethods._instances_by_id[id] = self

        self.id = id
        self.name = name

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (id, name) = tup

        obj = cls(scenario, id=id, name=name)

        return obj

class Currencies(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, id=None, name=None):
        DataObject.__init__(self, scenario)
        Currencies._instances_by_id[id] = self

        self.id = id
        self.name = name

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (id, name) = tup

        obj = cls(scenario, id=id, name=name)

        return obj

class DayType(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, id=None, name=None):
        DataObject.__init__(self, scenario)
        DayType._instances_by_id[id] = self

        self.id = id
        self.name = name

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (id, name) = tup

        obj = cls(scenario, id=id, name=name)

        return obj

class Definitions(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, id=None, name=None):
        DataObject.__init__(self, scenario)
        Definitions._instances_by_id[id] = self

        self.id = id
        self.name = name

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (id, name) = tup

        obj = cls(scenario, id=id, name=name)

        return obj

class DemandCO2CaptureMeasures(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, id=None, name=None, subsector_id=None, input_type_id=None, unit=None, geography_id=None,
                 other_index_1_id=None, other_index_2_id=None, interpolation_method_id=None,
                 extrapolation_method_id=None, extrapolation_growth=None, stock_decay_function_id=None,
                 min_lifetime=None, max_lifetime=None, mean_lifetime=None, lifetime_variance=None):
        DataObject.__init__(self, scenario)
        DemandCO2CaptureMeasures._instances_by_id[id] = self

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

        # ints mapped to strings
        self._extrapolation_method = None
        self._geography = None
        self._input_type = None
        self._interpolation_method = None
        self._other_index_1 = None
        self._other_index_2 = None
        self._stock_decay_function = None

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (id, name, subsector_id, input_type_id, unit, geography_id, other_index_1_id,
         other_index_2_id, interpolation_method_id, extrapolation_method_id, extrapolation_growth,
         stock_decay_function_id, min_lifetime, max_lifetime, mean_lifetime, lifetime_variance) = tup

        obj = cls(scenario, id=id, name=name, subsector_id=subsector_id, input_type_id=input_type_id, unit=unit,
                  geography_id=geography_id, other_index_1_id=other_index_1_id,
                  other_index_2_id=other_index_2_id, interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth,
                  stock_decay_function_id=stock_decay_function_id, min_lifetime=min_lifetime,
                  max_lifetime=max_lifetime, mean_lifetime=mean_lifetime,
                  lifetime_variance=lifetime_variance)

        return obj

class DemandDrivers(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, id=None, name=None, base_driver_id=None, input_type_id=None, unit_prefix=None,
                 unit_base=None, geography_id=None, other_index_1_id=None, other_index_2_id=None,
                 geography_map_key_id=None, interpolation_method_id=None, extrapolation_method_id=None,
                 extrapolation_growth=None, source=None):
        DataObject.__init__(self, scenario)
        DemandDrivers._instances_by_id[id] = self

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

        # ints mapped to strings
        self._extrapolation_method = None
        self._geography = None
        self._geography_map_key = None
        self._input_type = None
        self._interpolation_method = None
        self._other_index_1 = None
        self._other_index_2 = None

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (id, name, base_driver_id, input_type_id, unit_prefix, unit_base, geography_id,
         other_index_1_id, other_index_2_id, geography_map_key_id, interpolation_method_id,
         extrapolation_method_id, extrapolation_growth, source) = tup

        obj = cls(scenario, id=id, name=name, base_driver_id=base_driver_id, input_type_id=input_type_id,
                  unit_prefix=unit_prefix, unit_base=unit_base, geography_id=geography_id,
                  other_index_1_id=other_index_1_id, other_index_2_id=other_index_2_id,
                  geography_map_key_id=geography_map_key_id,
                  interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth, source=source)

        return obj

class DemandDriversData(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, parent_id=None, gau_id=None, oth_1_id=None, oth_2_id=None, year=None, value=None, id=None,
                 sensitivity=None):
        DataObject.__init__(self, scenario)
        DemandDriversData._instances_by_id[id] = self

        self.parent_id = parent_id
        self.gau_id = gau_id
        self.oth_1_id = oth_1_id
        self.oth_2_id = oth_2_id
        self.year = year
        self.value = value
        self.id = id
        self.sensitivity = sensitivity

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (parent_id, gau_id, oth_1_id, oth_2_id, year, value, id, sensitivity) = tup

        obj = cls(scenario, parent_id=parent_id, gau_id=gau_id, oth_1_id=oth_1_id, oth_2_id=oth_2_id, year=year,
                  value=value, id=id, sensitivity=sensitivity)

        return obj

class DemandEnergyDemands(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, subsector_id=None, is_stock_dependent=None, input_type_id=None, unit=None,
                 driver_denominator_1_id=None, driver_denominator_2_id=None, driver_1_id=None,
                 driver_2_id=None, geography_id=None, final_energy_index=None,
                 demand_technology_index=None, other_index_1_id=None, other_index_2_id=None,
                 interpolation_method_id=None, extrapolation_method_id=None, extrapolation_growth=None,
                 geography_map_key_id=None):
        DataObject.__init__(self, scenario)
        DemandEnergyDemands._instances_by_id[id] = self

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

        # ints mapped to strings
        self._extrapolation_method = None
        self._geography = None
        self._geography_map_key = None
        self._input_type = None
        self._interpolation_method = None
        self._other_index_1 = None
        self._other_index_2 = None

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (subsector_id, is_stock_dependent, input_type_id, unit, driver_denominator_1_id,
         driver_denominator_2_id, driver_1_id, driver_2_id, geography_id, final_energy_index,
         demand_technology_index, other_index_1_id, other_index_2_id, interpolation_method_id,
         extrapolation_method_id, extrapolation_growth, geography_map_key_id) = tup

        obj = cls(scenario, subsector_id=subsector_id, is_stock_dependent=is_stock_dependent,
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
    _instances_by_id = {}

    __slots__ = ['subsector_id', 'gau_id', 'oth_1_id', 'oth_2_id', 'final_energy_id',
                 'demand_technology_id', 'year', 'value', 'id', 'sensitivity']

    def __init__(self, scenario, subsector_id=None, gau_id=None, oth_1_id=None, oth_2_id=None, final_energy_id=None,
                 demand_technology_id=None, year=None, value=None, id=None, sensitivity=None):
        DataObject.__init__(self, scenario)
        DemandEnergyDemandsData._instances_by_id[id] = self

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

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (subsector_id, gau_id, oth_1_id, oth_2_id, final_energy_id, demand_technology_id, year,
         value, id, sensitivity) = tup

        obj = cls(scenario, subsector_id=subsector_id, gau_id=gau_id, oth_1_id=oth_1_id, oth_2_id=oth_2_id,
                  final_energy_id=final_energy_id, demand_technology_id=demand_technology_id, year=year,
                  value=value, id=id, sensitivity=sensitivity)

        return obj

class DemandEnergyEfficiencyMeasures(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, id=None, name=None, subsector_id=None, input_type_id=None, unit=None, geography_id=None,
                 other_index_1_id=None, other_index_2_id=None, interpolation_method_id=None,
                 extrapolation_method_id=None, extrapolation_growth=None, stock_decay_function_id=None,
                 min_lifetime=None, max_lifetime=None, mean_lifetime=None, lifetime_variance=None):
        DataObject.__init__(self, scenario)
        DemandEnergyEfficiencyMeasures._instances_by_id[id] = self

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

        # ints mapped to strings
        self._extrapolation_method = None
        self._geography = None
        self._input_type = None
        self._interpolation_method = None
        self._other_index_1 = None
        self._other_index_2 = None
        self._stock_decay_function = None

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (id, name, subsector_id, input_type_id, unit, geography_id, other_index_1_id,
         other_index_2_id, interpolation_method_id, extrapolation_method_id, extrapolation_growth,
         stock_decay_function_id, min_lifetime, max_lifetime, mean_lifetime, lifetime_variance) = tup

        obj = cls(scenario, id=id, name=name, subsector_id=subsector_id, input_type_id=input_type_id, unit=unit,
                  geography_id=geography_id, other_index_1_id=other_index_1_id,
                  other_index_2_id=other_index_2_id, interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth,
                  stock_decay_function_id=stock_decay_function_id, min_lifetime=min_lifetime,
                  max_lifetime=max_lifetime, mean_lifetime=mean_lifetime,
                  lifetime_variance=lifetime_variance)

        return obj

class DemandEnergyEfficiencyMeasuresCost(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, parent_id=None, currency_id=None, currency_year_id=None, cost_denominator_unit=None,
                 cost_of_capital=None, is_levelized=None, geography_id=None, other_index_1_id=None,
                 other_index_2_id=None, interpolation_method_id=None, extrapolation_method_id=None,
                 extrapolation_growth=None):
        DataObject.__init__(self, scenario)
        DemandEnergyEfficiencyMeasuresCost._instances_by_id[id] = self

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

        # ints mapped to strings
        self._currency = None
        self._extrapolation_method = None
        self._geography = None
        self._interpolation_method = None
        self._other_index_1 = None
        self._other_index_2 = None

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (parent_id, currency_id, currency_year_id, cost_denominator_unit, cost_of_capital,
         is_levelized, geography_id, other_index_1_id, other_index_2_id, interpolation_method_id,
         extrapolation_method_id, extrapolation_growth) = tup

        obj = cls(scenario, parent_id=parent_id, currency_id=currency_id, currency_year_id=currency_year_id,
                  cost_denominator_unit=cost_denominator_unit, cost_of_capital=cost_of_capital,
                  is_levelized=is_levelized, geography_id=geography_id, other_index_1_id=other_index_1_id,
                  other_index_2_id=other_index_2_id, interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth)

        return obj

class DemandEnergyEfficiencyMeasuresCostData(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, parent_id=None, gau_id=None, oth_1_id=None, oth_2_id=None, vintage=None, value=None,
                 id=None, final_energy_id=None):
        DataObject.__init__(self, scenario)
        DemandEnergyEfficiencyMeasuresCostData._instances_by_id[id] = self

        self.parent_id = parent_id
        self.gau_id = gau_id
        self.oth_1_id = oth_1_id
        self.oth_2_id = oth_2_id
        self.vintage = vintage
        self.value = value
        self.id = id
        self.final_energy_id = final_energy_id

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (parent_id, gau_id, oth_1_id, oth_2_id, vintage, value, id, final_energy_id) = tup

        obj = cls(scenario, parent_id=parent_id, gau_id=gau_id, oth_1_id=oth_1_id, oth_2_id=oth_2_id, vintage=vintage,
                  value=value, id=id, final_energy_id=final_energy_id)

        return obj

class DemandEnergyEfficiencyMeasuresData(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, parent_id=None, final_energy_id=None, gau_id=None, oth_1_id=None, oth_2_id=None,
                 year=None, value=None, id=None):
        DataObject.__init__(self, scenario)
        DemandEnergyEfficiencyMeasuresData._instances_by_id[id] = self

        self.parent_id = parent_id
        self.final_energy_id = final_energy_id
        self.gau_id = gau_id
        self.oth_1_id = oth_1_id
        self.oth_2_id = oth_2_id
        self.year = year
        self.value = value
        self.id = id

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (parent_id, final_energy_id, gau_id, oth_1_id, oth_2_id, year, value, id) = tup

        obj = cls(scenario, parent_id=parent_id, final_energy_id=final_energy_id, gau_id=gau_id, oth_1_id=oth_1_id,
                  oth_2_id=oth_2_id, year=year, value=value, id=id)

        return obj

class DemandFlexibleLoadMeasures(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, id=None, subsector_id=None, geography_id=None, other_index_1_id=None,
                 interpolation_method_id=None, extrapolation_method_id=None, extrapolation_growth=None,
                 name=None):
        DataObject.__init__(self, scenario)
        DemandFlexibleLoadMeasures._instances_by_id[id] = self

        self.id = id
        self.subsector_id = subsector_id
        self.geography_id = geography_id
        self.other_index_1_id = other_index_1_id
        self.interpolation_method_id = interpolation_method_id
        self.extrapolation_method_id = extrapolation_method_id
        self.extrapolation_growth = extrapolation_growth
        self.name = name

        # ints mapped to strings
        self._extrapolation_method = None
        self._geography = None
        self._interpolation_method = None
        self._other_index_1 = None

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (id, subsector_id, geography_id, other_index_1_id, interpolation_method_id,
         extrapolation_method_id, extrapolation_growth, name) = tup

        obj = cls(scenario, id=id, subsector_id=subsector_id, geography_id=geography_id,
                  other_index_1_id=other_index_1_id, interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth, name=name)

        return obj

class DemandFlexibleLoadMeasuresData(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, parent_id=None, gau_id=None, oth_1_id=None, year=None, value=None, id=None):
        DataObject.__init__(self, scenario)
        DemandFlexibleLoadMeasuresData._instances_by_id[id] = self

        self.parent_id = parent_id
        self.gau_id = gau_id
        self.oth_1_id = oth_1_id
        self.year = year
        self.value = value
        self.id = id

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (parent_id, gau_id, oth_1_id, year, value, id) = tup

        obj = cls(scenario, parent_id=parent_id, gau_id=gau_id, oth_1_id=oth_1_id, year=year, value=value, id=id)

        return obj

class DemandFuelSwitchingMeasures(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, id=None, name=None, subsector_id=None, final_energy_from_id=None, final_energy_to_id=None,
                 stock_decay_function_id=None, max_lifetime=None, min_lifetime=None, mean_lifetime=None,
                 lifetime_variance=None):
        DataObject.__init__(self, scenario)
        DemandFuelSwitchingMeasures._instances_by_id[id] = self

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

        # ints mapped to strings
        self._stock_decay_function = None

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (id, name, subsector_id, final_energy_from_id, final_energy_to_id, stock_decay_function_id,
         max_lifetime, min_lifetime, mean_lifetime, lifetime_variance) = tup

        obj = cls(scenario, id=id, name=name, subsector_id=subsector_id, final_energy_from_id=final_energy_from_id,
                  final_energy_to_id=final_energy_to_id, stock_decay_function_id=stock_decay_function_id,
                  max_lifetime=max_lifetime, min_lifetime=min_lifetime, mean_lifetime=mean_lifetime,
                  lifetime_variance=lifetime_variance)

        return obj

class DemandFuelSwitchingMeasuresCost(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, parent_id=None, currency_id=None, currency_year_id=None, cost_denominator_unit=None,
                 cost_of_capital=None, is_levelized=None, geography_id=None, other_index_1_id=None,
                 other_index_2_id=None, interpolation_method_id=None, extrapolation_method_id=None,
                 extrapolation_growth=None):
        DataObject.__init__(self, scenario)
        DemandFuelSwitchingMeasuresCost._instances_by_id[id] = self

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

        # ints mapped to strings
        self._currency = None
        self._extrapolation_method = None
        self._geography = None
        self._interpolation_method = None
        self._other_index_1 = None
        self._other_index_2 = None

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (parent_id, currency_id, currency_year_id, cost_denominator_unit, cost_of_capital,
         is_levelized, geography_id, other_index_1_id, other_index_2_id, interpolation_method_id,
         extrapolation_method_id, extrapolation_growth) = tup

        obj = cls(scenario, parent_id=parent_id, currency_id=currency_id, currency_year_id=currency_year_id,
                  cost_denominator_unit=cost_denominator_unit, cost_of_capital=cost_of_capital,
                  is_levelized=is_levelized, geography_id=geography_id, other_index_1_id=other_index_1_id,
                  other_index_2_id=other_index_2_id, interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth)

        return obj

class DemandFuelSwitchingMeasuresCostData(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, parent_id=None, gau_id=None, oth_1_id=None, oth_2_id=None, vintage=None, value=None,
                 id=None):
        DataObject.__init__(self, scenario)
        DemandFuelSwitchingMeasuresCostData._instances_by_id[id] = self

        self.parent_id = parent_id
        self.gau_id = gau_id
        self.oth_1_id = oth_1_id
        self.oth_2_id = oth_2_id
        self.vintage = vintage
        self.value = value
        self.id = id

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (parent_id, gau_id, oth_1_id, oth_2_id, vintage, value, id) = tup

        obj = cls(scenario, parent_id=parent_id, gau_id=gau_id, oth_1_id=oth_1_id, oth_2_id=oth_2_id, vintage=vintage,
                  value=value, id=id)

        return obj

class DemandFuelSwitchingMeasuresEnergyIntensity(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, parent_id=None, geography_id=None, other_index_1_id=None, other_index_2_id=None,
                 interpolation_method_id=None, extrapolation_method_id=None, extrapolation_growth=None):
        DataObject.__init__(self, scenario)
        DemandFuelSwitchingMeasuresEnergyIntensity._instances_by_id[id] = self

        self.parent_id = parent_id
        self.geography_id = geography_id
        self.other_index_1_id = other_index_1_id
        self.other_index_2_id = other_index_2_id
        self.interpolation_method_id = interpolation_method_id
        self.extrapolation_method_id = extrapolation_method_id
        self.extrapolation_growth = extrapolation_growth

        # ints mapped to strings
        self._extrapolation_method = None
        self._interpolation_method = None
        self._other_index_1 = None
        self._other_index_2 = None
        self._geography = None

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (parent_id, geography_id, other_index_1_id, other_index_2_id, interpolation_method_id,
         extrapolation_method_id, extrapolation_growth) = tup

        obj = cls(scenario, parent_id=parent_id, geography_id=geography_id, other_index_1_id=other_index_1_id,
                  other_index_2_id=other_index_2_id, interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth)

        return obj

class DemandFuelSwitchingMeasuresEnergyIntensityData(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, parent_id=None, gau_id=None, oth_1_id=None, oth_2_id=None, year=None, value=None, id=None):
        DataObject.__init__(self, scenario)
        DemandFuelSwitchingMeasuresEnergyIntensityData._instances_by_id[id] = self

        self.parent_id = parent_id
        self.gau_id = gau_id
        self.oth_1_id = oth_1_id
        self.oth_2_id = oth_2_id
        self.year = year
        self.value = value
        self.id = id

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (parent_id, gau_id, oth_1_id, oth_2_id, year, value, id) = tup

        obj = cls(scenario, parent_id=parent_id, gau_id=gau_id, oth_1_id=oth_1_id, oth_2_id=oth_2_id, year=year,
                  value=value, id=id)

        return obj

class DemandFuelSwitchingMeasuresImpact(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, parent_id=None, input_type_id=None, unit=None, geography_id=None, other_index_1_id=None,
                 other_index_2_id=None, interpolation_method_id=None, extrapolation_method_id=None,
                 extrapolation_growth=None):
        DataObject.__init__(self, scenario)
        DemandFuelSwitchingMeasuresImpact._instances_by_id[id] = self

        self.parent_id = parent_id
        self.input_type_id = input_type_id
        self.unit = unit
        self.geography_id = geography_id
        self.other_index_1_id = other_index_1_id
        self.other_index_2_id = other_index_2_id
        self.interpolation_method_id = interpolation_method_id
        self.extrapolation_method_id = extrapolation_method_id
        self.extrapolation_growth = extrapolation_growth

        # ints mapped to strings
        self._extrapolation_method = None
        self._geography = None
        self._input_type = None
        self._interpolation_method = None
        self._other_index_1 = None
        self._other_index_2 = None

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (parent_id, input_type_id, unit, geography_id, other_index_1_id, other_index_2_id,
         interpolation_method_id, extrapolation_method_id, extrapolation_growth) = tup

        obj = cls(scenario, parent_id=parent_id, input_type_id=input_type_id, unit=unit, geography_id=geography_id,
                  other_index_1_id=other_index_1_id, other_index_2_id=other_index_2_id,
                  interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth)

        return obj

class DemandFuelSwitchingMeasuresImpactData(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, parent_id=None, gau_id=None, oth_1_id=None, oth_2_id=None, year=None, value=None, id=None):
        DataObject.__init__(self, scenario)
        DemandFuelSwitchingMeasuresImpactData._instances_by_id[id] = self

        self.parent_id = parent_id
        self.gau_id = gau_id
        self.oth_1_id = oth_1_id
        self.oth_2_id = oth_2_id
        self.year = year
        self.value = value
        self.id = id

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (parent_id, gau_id, oth_1_id, oth_2_id, year, value, id) = tup

        obj = cls(scenario, parent_id=parent_id, gau_id=gau_id, oth_1_id=oth_1_id, oth_2_id=oth_2_id, year=year,
                  value=value, id=id)

        return obj

class DemandSales(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, subsector_id=None, geography_id=None, other_index_1_id=None, other_index_2_id=None,
                 input_type_id=None, interpolation_method_id=None, extrapolation_method_id=None,
                 extrapolation_growth=None):
        DataObject.__init__(self, scenario)
        DemandSales._instances_by_id[id] = self

        self.subsector_id = subsector_id
        self.geography_id = geography_id
        self.other_index_1_id = other_index_1_id
        self.other_index_2_id = other_index_2_id
        self.input_type_id = input_type_id
        self.interpolation_method_id = interpolation_method_id
        self.extrapolation_method_id = extrapolation_method_id
        self.extrapolation_growth = extrapolation_growth

        # ints mapped to strings
        self._extrapolation_method = None
        self._geography = None
        self._input_type = None
        self._interpolation_method = None
        self._other_index_1 = None
        self._other_index_2 = None

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (subsector_id, geography_id, other_index_1_id, other_index_2_id, input_type_id,
         interpolation_method_id, extrapolation_method_id, extrapolation_growth) = tup

        obj = cls(scenario, subsector_id=subsector_id, geography_id=geography_id, other_index_1_id=other_index_1_id,
                  other_index_2_id=other_index_2_id, input_type_id=input_type_id,
                  interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth)

        return obj

class DemandSalesData(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, subsector_id=None, gau_id=None, oth_1_id=None, oth_2_id=None, demand_technology_id=None,
                 vintage=None, value=None, id=None):
        DataObject.__init__(self, scenario)
        DemandSalesData._instances_by_id[id] = self

        self.subsector_id = subsector_id
        self.gau_id = gau_id
        self.oth_1_id = oth_1_id
        self.oth_2_id = oth_2_id
        self.demand_technology_id = demand_technology_id
        self.vintage = vintage
        self.value = value
        self.id = id

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (subsector_id, gau_id, oth_1_id, oth_2_id, demand_technology_id, vintage, value, id) = tup

        obj = cls(scenario, subsector_id=subsector_id, gau_id=gau_id, oth_1_id=oth_1_id, oth_2_id=oth_2_id,
                  demand_technology_id=demand_technology_id, vintage=vintage, value=value, id=id)

        return obj

class DemandSalesShareMeasures(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, id=None, subsector_id=None, geography_id=None, other_index_1_id=None,
                 demand_technology_id=None, replaced_demand_tech_id=None, input_type_id=None,
                 interpolation_method_id=None, extrapolation_method_id=None, extrapolation_growth=None,
                 name=None):
        DataObject.__init__(self, scenario)
        DemandSalesShareMeasures._instances_by_id[id] = self

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

        # ints mapped to strings
        self._extrapolation_method = None
        self._geography = None
        self._input_type = None
        self._interpolation_method = None
        self._other_index_1 = None

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (id, subsector_id, geography_id, other_index_1_id, demand_technology_id,
         replaced_demand_tech_id, input_type_id, interpolation_method_id, extrapolation_method_id,
         extrapolation_growth, name) = tup

        obj = cls(scenario, id=id, subsector_id=subsector_id, geography_id=geography_id,
                  other_index_1_id=other_index_1_id, demand_technology_id=demand_technology_id,
                  replaced_demand_tech_id=replaced_demand_tech_id, input_type_id=input_type_id,
                  interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth, name=name)

        return obj

class DemandSalesShareMeasuresData(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, parent_id=None, gau_id=None, oth_1_id=None, vintage=None, value=None, id=None):
        DataObject.__init__(self, scenario)
        DemandSalesShareMeasuresData._instances_by_id[id] = self

        self.parent_id = parent_id
        self.gau_id = gau_id
        self.oth_1_id = oth_1_id
        self.vintage = vintage
        self.value = value
        self.id = id

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (parent_id, gau_id, oth_1_id, vintage, value, id) = tup

        obj = cls(scenario, parent_id=parent_id, gau_id=gau_id, oth_1_id=oth_1_id, vintage=vintage, value=value, id=id)

        return obj

class DemandSectors(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, id=None, name=None, shape_id=None, max_lead_hours=None, max_lag_hours=None):
        DataObject.__init__(self, scenario)
        DemandSectors._instances_by_id[id] = self

        self.id = id
        self.name = name
        self.shape_id = shape_id
        self.max_lead_hours = max_lead_hours
        self.max_lag_hours = max_lag_hours

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (id, name, shape_id, max_lead_hours, max_lag_hours) = tup

        obj = cls(scenario, id=id, name=name, shape_id=shape_id, max_lead_hours=max_lead_hours,
                  max_lag_hours=max_lag_hours)

        return obj

class DemandServiceDemandMeasures(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, id=None, name=None, subsector_id=None, input_type_id=None, unit=None, geography_id=None,
                 other_index_1_id=None, other_index_2_id=None, interpolation_method_id=None,
                 extrapolation_method_id=None, extrapolation_growth=None, stock_decay_function_id=None,
                 min_lifetime=None, max_lifetime=None, mean_lifetime=None, lifetime_variance=None):
        DataObject.__init__(self, scenario)
        DemandServiceDemandMeasures._instances_by_id[id] = self

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

        # ints mapped to strings
        self._extrapolation_method = None
        self._geography = None
        self._input_type = None
        self._interpolation_method = None
        self._other_index_1 = None
        self._other_index_2 = None
        self._stock_decay_function = None

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (id, name, subsector_id, input_type_id, unit, geography_id, other_index_1_id,
         other_index_2_id, interpolation_method_id, extrapolation_method_id, extrapolation_growth,
         stock_decay_function_id, min_lifetime, max_lifetime, mean_lifetime, lifetime_variance) = tup

        obj = cls(scenario, id=id, name=name, subsector_id=subsector_id, input_type_id=input_type_id, unit=unit,
                  geography_id=geography_id, other_index_1_id=other_index_1_id,
                  other_index_2_id=other_index_2_id, interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth,
                  stock_decay_function_id=stock_decay_function_id, min_lifetime=min_lifetime,
                  max_lifetime=max_lifetime, mean_lifetime=mean_lifetime,
                  lifetime_variance=lifetime_variance)

        return obj

class DemandServiceDemandMeasuresCost(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, parent_id=None, currency_id=None, currency_year_id=None, cost_denominator_unit=None,
                 cost_of_capital=None, is_levelized=None, geography_id=None, other_index_1_id=None,
                 other_index_2_id=None, interpolation_method_id=None, extrapolation_method_id=None,
                 extrapolation_growth=None):
        DataObject.__init__(self, scenario)
        DemandServiceDemandMeasuresCost._instances_by_id[id] = self

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

        # ints mapped to strings
        self._currency = None
        self._extrapolation_method = None
        self._geography = None
        self._interpolation_method = None
        self._other_index_1 = None
        self._other_index_2 = None

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (parent_id, currency_id, currency_year_id, cost_denominator_unit, cost_of_capital,
         is_levelized, geography_id, other_index_1_id, other_index_2_id, interpolation_method_id,
         extrapolation_method_id, extrapolation_growth) = tup

        obj = cls(scenario, parent_id=parent_id, currency_id=currency_id, currency_year_id=currency_year_id,
                  cost_denominator_unit=cost_denominator_unit, cost_of_capital=cost_of_capital,
                  is_levelized=is_levelized, geography_id=geography_id, other_index_1_id=other_index_1_id,
                  other_index_2_id=other_index_2_id, interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth)

        return obj

class DemandServiceDemandMeasuresCostData(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, id=None, gau_id=None, oth_1_id=None, oth_2_id=None, vintage=None, value=None,
                 parent_id=None):
        DataObject.__init__(self, scenario)
        DemandServiceDemandMeasuresCostData._instances_by_id[id] = self

        self.id = id
        self.gau_id = gau_id
        self.oth_1_id = oth_1_id
        self.oth_2_id = oth_2_id
        self.vintage = vintage
        self.value = value
        self.parent_id = parent_id

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (id, gau_id, oth_1_id, oth_2_id, vintage, value, parent_id) = tup

        obj = cls(scenario, id=id, gau_id=gau_id, oth_1_id=oth_1_id, oth_2_id=oth_2_id, vintage=vintage, value=value,
                  parent_id=parent_id)

        return obj

class DemandServiceDemandMeasuresData(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, parent_id=None, gau_id=None, oth_1_id=None, oth_2_id=None, year=None, value=None, id=None):
        DataObject.__init__(self, scenario)
        DemandServiceDemandMeasuresData._instances_by_id[id] = self

        self.parent_id = parent_id
        self.gau_id = gau_id
        self.oth_1_id = oth_1_id
        self.oth_2_id = oth_2_id
        self.year = year
        self.value = value
        self.id = id

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (parent_id, gau_id, oth_1_id, oth_2_id, year, value, id) = tup

        obj = cls(scenario, parent_id=parent_id, gau_id=gau_id, oth_1_id=oth_1_id, oth_2_id=oth_2_id, year=year,
                  value=value, id=id)

        return obj

class DemandServiceDemands(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, subsector_id=None, is_stock_dependent=None, input_type_id=None, unit=None,
                 driver_denominator_1_id=None, driver_denominator_2_id=None, driver_1_id=None,
                 driver_2_id=None, geography_id=None, final_energy_index=None,
                 demand_technology_index=None, other_index_1_id=None, other_index_2_id=None,
                 interpolation_method_id=None, extrapolation_method_id=None, extrapolation_growth=None,
                 geography_map_key_id=None):
        DataObject.__init__(self, scenario)
        DemandServiceDemands._instances_by_id[id] = self

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

        # ints mapped to strings
        self._extrapolation_method = None
        self._geography = None
        self._geography_map_key = None
        self._input_type = None
        self._interpolation_method = None
        self._other_index_1 = None
        self._other_index_2 = None

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (subsector_id, is_stock_dependent, input_type_id, unit, driver_denominator_1_id,
         driver_denominator_2_id, driver_1_id, driver_2_id, geography_id, final_energy_index,
         demand_technology_index, other_index_1_id, other_index_2_id, interpolation_method_id,
         extrapolation_method_id, extrapolation_growth, geography_map_key_id) = tup

        obj = cls(scenario, subsector_id=subsector_id, is_stock_dependent=is_stock_dependent,
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
    _instances_by_id = {}

    def __init__(self, scenario, subsector_id=None, gau_id=None, final_energy_id=None, demand_technology_id=None,
                 oth_1_id=None, oth_2_id=None, year=None, value=None, id=None, sensitivity=None):
        DataObject.__init__(self, scenario)
        DemandServiceDemandsData._instances_by_id[id] = self

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

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (subsector_id, gau_id, final_energy_id, demand_technology_id, oth_1_id, oth_2_id, year,
         value, id, sensitivity) = tup

        obj = cls(scenario, subsector_id=subsector_id, gau_id=gau_id, final_energy_id=final_energy_id,
                  demand_technology_id=demand_technology_id, oth_1_id=oth_1_id, oth_2_id=oth_2_id,
                  year=year, value=value, id=id, sensitivity=sensitivity)

        return obj

class DemandServiceEfficiency(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, subsector_id=None, energy_unit=None, denominator_unit=None, geography_id=None,
                 other_index_1_id=None, other_index_2_id=None, interpolation_method_id=None,
                 extrapolation_method_id=None, extrapolation_growth=None, geography_map_key_id=None):
        DataObject.__init__(self, scenario)
        DemandServiceEfficiency._instances_by_id[id] = self

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

        # ints mapped to strings
        self._extrapolation_method = None
        self._geography = None
        self._geography_map_key = None
        self._interpolation_method = None
        self._other_index_1 = None
        self._other_index_2 = None

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (subsector_id, energy_unit, denominator_unit, geography_id, other_index_1_id,
         other_index_2_id, interpolation_method_id, extrapolation_method_id, extrapolation_growth,
         geography_map_key_id) = tup

        obj = cls(scenario, subsector_id=subsector_id, energy_unit=energy_unit, denominator_unit=denominator_unit,
                  geography_id=geography_id, other_index_1_id=other_index_1_id,
                  other_index_2_id=other_index_2_id, interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth, geography_map_key_id=geography_map_key_id)

        return obj

class DemandServiceEfficiencyData(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, subsector_id=None, final_energy_id=None, gau_id=None, oth_1_id=None, oth_2_id=None,
                 year=None, value=None, id=None):
        DataObject.__init__(self, scenario)
        DemandServiceEfficiencyData._instances_by_id[id] = self

        self.subsector_id = subsector_id
        self.final_energy_id = final_energy_id
        self.gau_id = gau_id
        self.oth_1_id = oth_1_id
        self.oth_2_id = oth_2_id
        self.year = year
        self.value = value
        self.id = id

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (subsector_id, final_energy_id, gau_id, oth_1_id, oth_2_id, year, value, id) = tup

        obj = cls(scenario, subsector_id=subsector_id, final_energy_id=final_energy_id, gau_id=gau_id,
                  oth_1_id=oth_1_id, oth_2_id=oth_2_id, year=year, value=value, id=id)

        return obj

class DemandServiceLink(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, id=None, subsector_id=None, linked_subsector_id=None, service_demand_share=None, year=None):
        DataObject.__init__(self, scenario)
        DemandServiceLink._instances_by_id[id] = self

        self.id = id
        self.subsector_id = subsector_id
        self.linked_subsector_id = linked_subsector_id
        self.service_demand_share = service_demand_share
        self.year = year

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (id, subsector_id, linked_subsector_id, service_demand_share, year) = tup

        obj = cls(scenario, id=id, subsector_id=subsector_id, linked_subsector_id=linked_subsector_id,
                  service_demand_share=service_demand_share, year=year)

        return obj

class DemandStock(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, subsector_id=None, is_service_demand_dependent=None, driver_denominator_1_id=None,
                 driver_denominator_2_id=None, driver_1_id=None, driver_2_id=None, geography_id=None,
                 other_index_1_id=None, other_index_2_id=None, geography_map_key_id=None,
                 input_type_id=None, demand_stock_unit_type_id=None, unit=None, time_unit=None,
                 interpolation_method_id=None, extrapolation_method_id=None, extrapolation_growth=None):
        DataObject.__init__(self, scenario)
        DemandStock._instances_by_id[id] = self

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

        # ints mapped to strings
        self._demand_stock_unit_type = None
        self._extrapolation_method = None
        self._geography = None
        self._geography_map_key = None
        self._input_type = None
        self._interpolation_method = None
        self._other_index_1 = None
        self._other_index_2 = None

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (subsector_id, is_service_demand_dependent, driver_denominator_1_id,
         driver_denominator_2_id, driver_1_id, driver_2_id, geography_id, other_index_1_id,
         other_index_2_id, geography_map_key_id, input_type_id, demand_stock_unit_type_id, unit,
         time_unit, interpolation_method_id, extrapolation_method_id, extrapolation_growth) = tup

        obj = cls(scenario, subsector_id=subsector_id, is_service_demand_dependent=is_service_demand_dependent,
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
    _instances_by_id = {}

    def __init__(self, scenario, subsector_id=None, gau_id=None, oth_1_id=None, oth_2_id=None, demand_technology_id=None,
                 year=None, value=None, id=None):
        DataObject.__init__(self, scenario)
        DemandStockData._instances_by_id[id] = self

        self.subsector_id = subsector_id
        self.gau_id = gau_id
        self.oth_1_id = oth_1_id
        self.oth_2_id = oth_2_id
        self.demand_technology_id = demand_technology_id
        self.year = year
        self.value = value
        self.id = id

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (subsector_id, gau_id, oth_1_id, oth_2_id, demand_technology_id, year, value, id) = tup

        obj = cls(scenario, subsector_id=subsector_id, gau_id=gau_id, oth_1_id=oth_1_id, oth_2_id=oth_2_id,
                  demand_technology_id=demand_technology_id, year=year, value=value, id=id)

        return obj

class DemandStockMeasures(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, id=None, subsector_id=None, geography_id=None, other_index_1_id=None,
                 demand_technology_id=None, interpolation_method_id=None, extrapolation_method_id=None,
                 extrapolation_growth=None, name=None):
        DataObject.__init__(self, scenario)
        DemandStockMeasures._instances_by_id[id] = self

        self.id = id
        self.subsector_id = subsector_id
        self.geography_id = geography_id
        self.other_index_1_id = other_index_1_id
        self.demand_technology_id = demand_technology_id
        self.interpolation_method_id = interpolation_method_id
        self.extrapolation_method_id = extrapolation_method_id
        self.extrapolation_growth = extrapolation_growth
        self.name = name

        # ints mapped to strings
        self._extrapolation_method = None
        self._geography = None
        self._interpolation_method = None
        self._other_index_1 = None

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (id, subsector_id, geography_id, other_index_1_id, demand_technology_id,
         interpolation_method_id, extrapolation_method_id, extrapolation_growth, name) = tup

        obj = cls(scenario, id=id, subsector_id=subsector_id, geography_id=geography_id,
                  other_index_1_id=other_index_1_id, demand_technology_id=demand_technology_id,
                  interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth, name=name)

        return obj

class DemandStockMeasuresData(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, parent_id=None, gau_id=None, oth_1_id=None, year=None, value=None, id=None):
        DataObject.__init__(self, scenario)
        DemandStockMeasuresData._instances_by_id[id] = self

        self.parent_id = parent_id
        self.gau_id = gau_id
        self.oth_1_id = oth_1_id
        self.year = year
        self.value = value
        self.id = id

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (parent_id, gau_id, oth_1_id, year, value, id) = tup

        obj = cls(scenario, parent_id=parent_id, gau_id=gau_id, oth_1_id=oth_1_id, year=year, value=value, id=id)

        return obj

class DemandStockUnitTypes(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, id=None, name=None):
        DataObject.__init__(self, scenario)
        DemandStockUnitTypes._instances_by_id[id] = self

        self.id = id
        self.name = name

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (id, name) = tup

        obj = cls(scenario, id=id, name=name)

        return obj

class DemandSubsectors(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, id=None, sector_id=None, name=None, cost_of_capital=None, is_active=None, shape_id=None,
                 max_lead_hours=None, max_lag_hours=None):
        DataObject.__init__(self, scenario)
        DemandSubsectors._instances_by_id[id] = self

        self.id = id
        self.sector_id = sector_id
        self.name = name
        self.cost_of_capital = cost_of_capital
        self.is_active = is_active
        self.shape_id = shape_id
        self.max_lead_hours = max_lead_hours
        self.max_lag_hours = max_lag_hours

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (id, sector_id, name, cost_of_capital, is_active, shape_id, max_lead_hours, max_lag_hours) = tup

        obj = cls(scenario, id=id, sector_id=sector_id, name=name, cost_of_capital=cost_of_capital,
                  is_active=is_active, shape_id=shape_id, max_lead_hours=max_lead_hours,
                  max_lag_hours=max_lag_hours)

        return obj

class DemandTechEfficiencyTypes(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, id=None, name=None):
        DataObject.__init__(self, scenario)
        DemandTechEfficiencyTypes._instances_by_id[id] = self

        self.id = id
        self.name = name

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (id, name) = tup

        obj = cls(scenario, id=id, name=name)

        return obj

class DemandTechUnitTypes(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, id=None, name=None):
        DataObject.__init__(self, scenario)
        DemandTechUnitTypes._instances_by_id[id] = self

        self.id = id
        self.name = name

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (id, name) = tup

        obj = cls(scenario, id=id, name=name)

        return obj

class DemandTechs(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, id=None, linked_id=None, stock_link_ratio=None, subsector_id=None, name=None,
                 min_lifetime=None, max_lifetime=None, source=None, additional_description=None,
                 demand_tech_unit_type_id=None, unit=None, time_unit=None, cost_of_capital=None,
                 stock_decay_function_id=None, mean_lifetime=None, lifetime_variance=None, shape_id=None,
                 max_lead_hours=None, max_lag_hours=None):
        DataObject.__init__(self, scenario)
        DemandTechs._instances_by_id[id] = self

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

        # ints mapped to strings
        self._demand_tech_unit_type = None
        self._stock_decay_function = None

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (id, linked_id, stock_link_ratio, subsector_id, name, min_lifetime, max_lifetime, source,
         additional_description, demand_tech_unit_type_id, unit, time_unit, cost_of_capital,
         stock_decay_function_id, mean_lifetime, lifetime_variance, shape_id, max_lead_hours,
         max_lag_hours) = tup

        obj = cls(scenario, id=id, linked_id=linked_id, stock_link_ratio=stock_link_ratio, subsector_id=subsector_id,
                  name=name, min_lifetime=min_lifetime, max_lifetime=max_lifetime, source=source,
                  additional_description=additional_description,
                  demand_tech_unit_type_id=demand_tech_unit_type_id, unit=unit, time_unit=time_unit,
                  cost_of_capital=cost_of_capital, stock_decay_function_id=stock_decay_function_id,
                  mean_lifetime=mean_lifetime, lifetime_variance=lifetime_variance, shape_id=shape_id,
                  max_lead_hours=max_lead_hours, max_lag_hours=max_lag_hours)

        return obj

class DemandTechsAuxEfficiency(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, demand_technology_id=None, definition_id=None, reference_tech_id=None, geography_id=None,
                 other_index_1_id=None, other_index_2_id=None, final_energy_id=None,
                 demand_tech_efficiency_types_id=None, is_numerator_service=None, numerator_unit=None,
                 denominator_unit=None, interpolation_method_id=None, extrapolation_method_id=None,
                 extrapolation_growth=None, age_growth_or_decay_type_id=None, age_growth_or_decay=None,
                 shape_id=None):
        DataObject.__init__(self, scenario)
        DemandTechsAuxEfficiency._instances_by_id[id] = self

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

        # ints mapped to strings
        self._age_growth_or_decay_type = None
        self._definition = None
        self._demand_tech_efficiency_types = None
        self._extrapolation_method = None
        self._geography = None
        self._interpolation_method = None
        self._other_index_1 = None
        self._other_index_2 = None

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (demand_technology_id, definition_id, reference_tech_id, geography_id, other_index_1_id,
         other_index_2_id, final_energy_id, demand_tech_efficiency_types_id, is_numerator_service,
         numerator_unit, denominator_unit, interpolation_method_id, extrapolation_method_id,
         extrapolation_growth, age_growth_or_decay_type_id, age_growth_or_decay, shape_id) = tup

        obj = cls(scenario, demand_technology_id=demand_technology_id, definition_id=definition_id,
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
    _instances_by_id = {}

    def __init__(self, scenario, demand_technology_id=None, gau_id=None, oth_1_id=None, oth_2_id=None, vintage=None,
                 value=None, id=None, sensitivity=None):
        DataObject.__init__(self, scenario)
        DemandTechsAuxEfficiencyData._instances_by_id[id] = self

        self.demand_technology_id = demand_technology_id
        self.gau_id = gau_id
        self.oth_1_id = oth_1_id
        self.oth_2_id = oth_2_id
        self.vintage = vintage
        self.value = value
        self.id = id
        self.sensitivity = sensitivity

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (demand_technology_id, gau_id, oth_1_id, oth_2_id, vintage, value, id, sensitivity) = tup

        obj = cls(scenario, demand_technology_id=demand_technology_id, gau_id=gau_id, oth_1_id=oth_1_id,
                  oth_2_id=oth_2_id, vintage=vintage, value=value, id=id, sensitivity=sensitivity)

        return obj

class DemandTechsCapitalCost(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, demand_technology_id=None, definition_id=None, reference_tech_id=None, geography_id=None,
                 other_index_1_id=None, other_index_2_id=None, currency_id=None, currency_year_id=None,
                 is_levelized=None, interpolation_method_id=None, extrapolation_method_id=None,
                 extrapolation_growth=None):
        DataObject.__init__(self, scenario)
        DemandTechsCapitalCost._instances_by_id[id] = self

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

        # ints mapped to strings
        self._currency = None
        self._definition = None
        self._extrapolation_method = None
        self._geography = None
        self._interpolation_method = None
        self._other_index_1 = None
        self._other_index_2 = None

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (demand_technology_id, definition_id, reference_tech_id, geography_id, other_index_1_id,
         other_index_2_id, currency_id, currency_year_id, is_levelized, interpolation_method_id,
         extrapolation_method_id, extrapolation_growth) = tup

        obj = cls(scenario, demand_technology_id=demand_technology_id, definition_id=definition_id,
                  reference_tech_id=reference_tech_id, geography_id=geography_id,
                  other_index_1_id=other_index_1_id, other_index_2_id=other_index_2_id,
                  currency_id=currency_id, currency_year_id=currency_year_id, is_levelized=is_levelized,
                  interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth)

        return obj

class DemandTechsCapitalCostNewData(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, demand_technology_id=None, gau_id=None, oth_1_id=None, oth_2_id=None, vintage=None,
                 value=None, id=None, sensitivity=None):
        DataObject.__init__(self, scenario)
        DemandTechsCapitalCostNewData._instances_by_id[id] = self

        self.demand_technology_id = demand_technology_id
        self.gau_id = gau_id
        self.oth_1_id = oth_1_id
        self.oth_2_id = oth_2_id
        self.vintage = vintage
        self.value = value
        self.id = id
        self.sensitivity = sensitivity

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (demand_technology_id, gau_id, oth_1_id, oth_2_id, vintage, value, id, sensitivity) = tup

        obj = cls(scenario, demand_technology_id=demand_technology_id, gau_id=gau_id, oth_1_id=oth_1_id,
                  oth_2_id=oth_2_id, vintage=vintage, value=value, id=id, sensitivity=sensitivity)

        return obj

class DemandTechsCapitalCostReplacementData(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, demand_technology_id=None, gau_id=None, oth_1_id=None, oth_2_id=None, vintage=None,
                 value=None, id=None, sensitivity=None):
        DataObject.__init__(self, scenario)
        DemandTechsCapitalCostReplacementData._instances_by_id[id] = self

        self.demand_technology_id = demand_technology_id
        self.gau_id = gau_id
        self.oth_1_id = oth_1_id
        self.oth_2_id = oth_2_id
        self.vintage = vintage
        self.value = value
        self.id = id
        self.sensitivity = sensitivity

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (demand_technology_id, gau_id, oth_1_id, oth_2_id, vintage, value, id, sensitivity) = tup

        obj = cls(scenario, demand_technology_id=demand_technology_id, gau_id=gau_id, oth_1_id=oth_1_id,
                  oth_2_id=oth_2_id, vintage=vintage, value=value, id=id, sensitivity=sensitivity)

        return obj

class DemandTechsFixedMaintenanceCost(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, demand_technology_id=None, definition_id=None, reference_tech_id=None, geography_id=None,
                 other_index_1_id=None, other_index_2_id=None, currency_id=None, currency_year_id=None,
                 interpolation_method_id=None, extrapolation_method_id=None, extrapolation_growth=None,
                 age_growth_or_decay_type_id=None, age_growth_or_decay=None, additional_description=None):
        DataObject.__init__(self, scenario)
        DemandTechsFixedMaintenanceCost._instances_by_id[id] = self

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

        # ints mapped to strings
        self._age_growth_or_decay_type = None
        self._currency = None
        self._definition = None
        self._extrapolation_method = None
        self._geography = None
        self._interpolation_method = None
        self._other_index_1 = None
        self._other_index_2 = None

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (demand_technology_id, definition_id, reference_tech_id, geography_id, other_index_1_id,
         other_index_2_id, currency_id, currency_year_id, interpolation_method_id,
         extrapolation_method_id, extrapolation_growth, age_growth_or_decay_type_id,
         age_growth_or_decay, additional_description) = tup

        obj = cls(scenario, demand_technology_id=demand_technology_id, definition_id=definition_id,
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
    _instances_by_id = {}

    def __init__(self, scenario, demand_technology_id=None, gau_id=None, oth_1_id=None, oth_2_id=None, vintage=None,
                 value=None, id=None, sensitivity=None):
        DataObject.__init__(self, scenario)
        DemandTechsFixedMaintenanceCostData._instances_by_id[id] = self

        self.demand_technology_id = demand_technology_id
        self.gau_id = gau_id
        self.oth_1_id = oth_1_id
        self.oth_2_id = oth_2_id
        self.vintage = vintage
        self.value = value
        self.id = id
        self.sensitivity = sensitivity

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (demand_technology_id, gau_id, oth_1_id, oth_2_id, vintage, value, id, sensitivity) = tup

        obj = cls(scenario, demand_technology_id=demand_technology_id, gau_id=gau_id, oth_1_id=oth_1_id,
                  oth_2_id=oth_2_id, vintage=vintage, value=value, id=id, sensitivity=sensitivity)

        return obj

class DemandTechsFuelSwitchCost(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, demand_technology_id=None, definition_id=None, reference_tech_id=None, geography_id=None,
                 other_index_1_id=None, other_index_2_id=None, currency_id=None, currency_year_id=None,
                 is_levelized=None, interpolation_method_id=None, extrapolation_method_id=None,
                 extrapolation_growth=None):
        DataObject.__init__(self, scenario)
        DemandTechsFuelSwitchCost._instances_by_id[id] = self

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

        # ints mapped to strings
        self._currency = None
        self._definition = None
        self._extrapolation_method = None
        self._geography = None
        self._interpolation_method = None
        self._other_index_1 = None
        self._other_index_2 = None

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (demand_technology_id, definition_id, reference_tech_id, geography_id, other_index_1_id,
         other_index_2_id, currency_id, currency_year_id, is_levelized, interpolation_method_id,
         extrapolation_method_id, extrapolation_growth) = tup

        obj = cls(scenario, demand_technology_id=demand_technology_id, definition_id=definition_id,
                  reference_tech_id=reference_tech_id, geography_id=geography_id,
                  other_index_1_id=other_index_1_id, other_index_2_id=other_index_2_id,
                  currency_id=currency_id, currency_year_id=currency_year_id, is_levelized=is_levelized,
                  interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth)

        return obj

class DemandTechsFuelSwitchCostData(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, demand_technology_id=None, gau_id=None, oth_1_id=None, oth_2_id=None, vintage=None,
                 value=None, id=None, sensitivity=None):
        DataObject.__init__(self, scenario)
        DemandTechsFuelSwitchCostData._instances_by_id[id] = self

        self.demand_technology_id = demand_technology_id
        self.gau_id = gau_id
        self.oth_1_id = oth_1_id
        self.oth_2_id = oth_2_id
        self.vintage = vintage
        self.value = value
        self.id = id
        self.sensitivity = sensitivity

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (demand_technology_id, gau_id, oth_1_id, oth_2_id, vintage, value, id, sensitivity) = tup

        obj = cls(scenario, demand_technology_id=demand_technology_id, gau_id=gau_id, oth_1_id=oth_1_id,
                  oth_2_id=oth_2_id, vintage=vintage, value=value, id=id, sensitivity=sensitivity)

        return obj

class DemandTechsInstallationCost(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, demand_technology_id=None, definition_id=None, reference_tech_id=None, geography_id=None,
                 other_index_1_id=None, other_index_2_id=None, currency_id=None, currency_year_id=None,
                 is_levelized=None, interpolation_method_id=None, extrapolation_method_id=None,
                 extrapolation_growth=None):
        DataObject.__init__(self, scenario)
        DemandTechsInstallationCost._instances_by_id[id] = self

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

        # ints mapped to strings
        self._currency = None
        self._definition = None
        self._extrapolation_method = None
        self._geography = None
        self._interpolation_method = None
        self._other_index_1 = None
        self._other_index_2 = None

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (demand_technology_id, definition_id, reference_tech_id, geography_id, other_index_1_id,
         other_index_2_id, currency_id, currency_year_id, is_levelized, interpolation_method_id,
         extrapolation_method_id, extrapolation_growth) = tup

        obj = cls(scenario, demand_technology_id=demand_technology_id, definition_id=definition_id,
                  reference_tech_id=reference_tech_id, geography_id=geography_id,
                  other_index_1_id=other_index_1_id, other_index_2_id=other_index_2_id,
                  currency_id=currency_id, currency_year_id=currency_year_id, is_levelized=is_levelized,
                  interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth)

        return obj

class DemandTechsInstallationCostNewData(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, demand_technology_id=None, gau_id=None, oth_1_id=None, oth_2_id=None, vintage=None,
                 value=None, id=None, sensitivity=None):
        DataObject.__init__(self, scenario)
        DemandTechsInstallationCostNewData._instances_by_id[id] = self

        self.demand_technology_id = demand_technology_id
        self.gau_id = gau_id
        self.oth_1_id = oth_1_id
        self.oth_2_id = oth_2_id
        self.vintage = vintage
        self.value = value
        self.id = id
        self.sensitivity = sensitivity

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (demand_technology_id, gau_id, oth_1_id, oth_2_id, vintage, value, id, sensitivity) = tup

        obj = cls(scenario, demand_technology_id=demand_technology_id, gau_id=gau_id, oth_1_id=oth_1_id,
                  oth_2_id=oth_2_id, vintage=vintage, value=value, id=id, sensitivity=sensitivity)

        return obj

class DemandTechsInstallationCostReplacementData(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, demand_technology_id=None, gau_id=None, oth_1_id=None, oth_2_id=None, vintage=None,
                 value=None, id=None, sensitivity=None):
        DataObject.__init__(self, scenario)
        DemandTechsInstallationCostReplacementData._instances_by_id[id] = self

        self.demand_technology_id = demand_technology_id
        self.gau_id = gau_id
        self.oth_1_id = oth_1_id
        self.oth_2_id = oth_2_id
        self.vintage = vintage
        self.value = value
        self.id = id
        self.sensitivity = sensitivity

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (demand_technology_id, gau_id, oth_1_id, oth_2_id, vintage, value, id, sensitivity) = tup

        obj = cls(scenario, demand_technology_id=demand_technology_id, gau_id=gau_id, oth_1_id=oth_1_id,
                  oth_2_id=oth_2_id, vintage=vintage, value=value, id=id, sensitivity=sensitivity)

        return obj

class DemandTechsMainEfficiency(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, demand_technology_id=None, definition_id=None, reference_tech_id=None, geography_id=None,
                 other_index_1_id=None, other_index_2_id=None, final_energy_id=None, utility_factor=None,
                 demand_tech_efficiency_types=None, is_numerator_service=None, numerator_unit=None,
                 denominator_unit=None, interpolation_method_id=None, extrapolation_method_id=None,
                 extrapolation_growth=None, age_growth_or_decay_type_id=None, age_growth_or_decay=None,
                 shape_id=None):
        DataObject.__init__(self, scenario)
        DemandTechsMainEfficiency._instances_by_id[id] = self

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

        # ints mapped to strings
        self._age_growth_or_decay_type = None
        self._definition = None
        self._demand_tech_efficiency_types = None
        self._extrapolation_method = None
        self._geography = None
        self._interpolation_method = None
        self._other_index_1 = None
        self._other_index_2 = None

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (demand_technology_id, definition_id, reference_tech_id, geography_id, other_index_1_id,
         other_index_2_id, final_energy_id, utility_factor, demand_tech_efficiency_types,
         is_numerator_service, numerator_unit, denominator_unit, interpolation_method_id,
         extrapolation_method_id, extrapolation_growth, age_growth_or_decay_type_id,
         age_growth_or_decay, shape_id) = tup

        obj = cls(scenario, demand_technology_id=demand_technology_id, definition_id=definition_id,
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
    _instances_by_id = {}

    def __init__(self, scenario, demand_technology_id=None, gau_id=None, oth_1_id=None, oth_2_id=None, vintage=None,
                 value=None, id=None, sensitivity=None):
        DataObject.__init__(self, scenario)
        DemandTechsMainEfficiencyData._instances_by_id[id] = self

        self.demand_technology_id = demand_technology_id
        self.gau_id = gau_id
        self.oth_1_id = oth_1_id
        self.oth_2_id = oth_2_id
        self.vintage = vintage
        self.value = value
        self.id = id
        self.sensitivity = sensitivity

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (demand_technology_id, gau_id, oth_1_id, oth_2_id, vintage, value, id, sensitivity) = tup

        obj = cls(scenario, demand_technology_id=demand_technology_id, gau_id=gau_id, oth_1_id=oth_1_id,
                  oth_2_id=oth_2_id, vintage=vintage, value=value, id=id, sensitivity=sensitivity)

        return obj

class DemandTechsParasiticEnergy(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, demand_technology_id=None, definition_id=None, reference_tech_id=None, geography_id=None,
                 other_index_1_id=None, other_index_2_id=None, energy_unit=None, time_unit=None,
                 interpolation_method_id=None, extrapolation_method_id=None, extrapolation_growth=None,
                 age_growth_or_decay_type_id=None, age_growth_or_decay=None):
        DataObject.__init__(self, scenario)
        DemandTechsParasiticEnergy._instances_by_id[id] = self

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

        # ints mapped to strings
        self._age_growth_or_decay_type = None
        self._definition = None
        self._extrapolation_method = None
        self._geography = None
        self._interpolation_method = None
        self._other_index_1 = None
        self._other_index_2 = None

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (demand_technology_id, definition_id, reference_tech_id, geography_id, other_index_1_id,
         other_index_2_id, energy_unit, time_unit, interpolation_method_id,
         extrapolation_method_id, extrapolation_growth, age_growth_or_decay_type_id,
         age_growth_or_decay) = tup

        obj = cls(scenario, demand_technology_id=demand_technology_id, definition_id=definition_id,
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
    _instances_by_id = {}

    def __init__(self, scenario, demand_technology_id=None, gau_id=None, oth_1_id=None, oth_2_id=None,
                 final_energy_id=None, vintage=None, value=None, id=None, sensitivity=None):
        DataObject.__init__(self, scenario)
        DemandTechsParasiticEnergyData._instances_by_id[id] = self

        self.demand_technology_id = demand_technology_id
        self.gau_id = gau_id
        self.oth_1_id = oth_1_id
        self.oth_2_id = oth_2_id
        self.final_energy_id = final_energy_id
        self.vintage = vintage
        self.value = value
        self.id = id
        self.sensitivity = sensitivity

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (demand_technology_id, gau_id, oth_1_id, oth_2_id, final_energy_id, vintage, value, id,
         sensitivity) = tup

        obj = cls(scenario, demand_technology_id=demand_technology_id, gau_id=gau_id, oth_1_id=oth_1_id,
                  oth_2_id=oth_2_id, final_energy_id=final_energy_id, vintage=vintage, value=value, id=id,
                  sensitivity=sensitivity)

        return obj

class DemandTechsServiceDemandModifier(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, demand_technology_id=None, geography_id=None, other_index_1_id=None,
                 other_index_2_id=None, interpolation_method_id=None, extrapolation_method_id=None,
                 extrapolation_growth=None, age_growth_or_decay_type_id=None, age_growth_or_decay=None):
        DataObject.__init__(self, scenario)
        DemandTechsServiceDemandModifier._instances_by_id[id] = self

        self.demand_technology_id = demand_technology_id
        self.geography_id = geography_id
        self.other_index_1_id = other_index_1_id
        self.other_index_2_id = other_index_2_id
        self.interpolation_method_id = interpolation_method_id
        self.extrapolation_method_id = extrapolation_method_id
        self.extrapolation_growth = extrapolation_growth
        self.age_growth_or_decay_type_id = age_growth_or_decay_type_id
        self.age_growth_or_decay = age_growth_or_decay

        # ints mapped to strings
        self._age_growth_or_decay_type = None
        self._extrapolation_method = None
        self._geography = None
        self._interpolation_method = None
        self._other_index_1 = None
        self._other_index_2 = None

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (demand_technology_id, geography_id, other_index_1_id, other_index_2_id,
         interpolation_method_id, extrapolation_method_id, extrapolation_growth,
         age_growth_or_decay_type_id, age_growth_or_decay) = tup

        obj = cls(scenario, demand_technology_id=demand_technology_id, geography_id=geography_id,
                  other_index_1_id=other_index_1_id, other_index_2_id=other_index_2_id,
                  interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth,
                  age_growth_or_decay_type_id=age_growth_or_decay_type_id,
                  age_growth_or_decay=age_growth_or_decay)

        return obj

class DemandTechsServiceDemandModifierData(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, demand_technology_id=None, gau_id=None, oth_1_id=None, oth_2_id=None, vintage=None,
                 value=None, id=None, sensitivity=None):
        DataObject.__init__(self, scenario)
        DemandTechsServiceDemandModifierData._instances_by_id[id] = self

        self.demand_technology_id = demand_technology_id
        self.gau_id = gau_id
        self.oth_1_id = oth_1_id
        self.oth_2_id = oth_2_id
        self.vintage = vintage
        self.value = value
        self.id = id
        self.sensitivity = sensitivity

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (demand_technology_id, gau_id, oth_1_id, oth_2_id, vintage, value, id, sensitivity) = tup

        obj = cls(scenario, demand_technology_id=demand_technology_id, gau_id=gau_id, oth_1_id=oth_1_id,
                  oth_2_id=oth_2_id, vintage=vintage, value=value, id=id, sensitivity=sensitivity)

        return obj

class DemandTechsServiceLink(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, id=None, service_link_id=None, demand_technology_id=None, definition_id=None,
                 reference_id=None, geography_id=None, other_index_1_id=None, other_index_2_id=None,
                 interpolation_method_id=None, extrapolation_method_id=None, extrapolation_growth=None,
                 age_growth_or_decay_type_id=None, age_growth_or_decay=None):
        DataObject.__init__(self, scenario)
        DemandTechsServiceLink._instances_by_id[id] = self

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

        # ints mapped to strings
        self._age_growth_or_decay_type = None
        self._definition = None
        self._extrapolation_method = None
        self._geography = None
        self._interpolation_method = None
        self._other_index_1 = None
        self._other_index_2 = None

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (id, service_link_id, demand_technology_id, definition_id, reference_id, geography_id,
         other_index_1_id, other_index_2_id, interpolation_method_id, extrapolation_method_id,
         extrapolation_growth, age_growth_or_decay_type_id, age_growth_or_decay) = tup

        obj = cls(scenario, id=id, service_link_id=service_link_id, demand_technology_id=demand_technology_id,
                  definition_id=definition_id, reference_id=reference_id, geography_id=geography_id,
                  other_index_1_id=other_index_1_id, other_index_2_id=other_index_2_id,
                  interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth,
                  age_growth_or_decay_type_id=age_growth_or_decay_type_id,
                  age_growth_or_decay=age_growth_or_decay)

        return obj

class DemandTechsServiceLinkData(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, parent_id=None, gau_id=None, oth_1_id=None, oth_2_id=None, vintage=None, value=None,
                 id=None):
        DataObject.__init__(self, scenario)
        DemandTechsServiceLinkData._instances_by_id[id] = self

        self.parent_id = parent_id
        self.gau_id = gau_id
        self.oth_1_id = oth_1_id
        self.oth_2_id = oth_2_id
        self.vintage = vintage
        self.value = value
        self.id = id

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (parent_id, gau_id, oth_1_id, oth_2_id, vintage, value, id) = tup

        obj = cls(scenario, parent_id=parent_id, gau_id=gau_id, oth_1_id=oth_1_id, oth_2_id=oth_2_id, vintage=vintage,
                  value=value, id=id)

        return obj

class DispatchConfig(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, id=None, geography_id=None, flex_load_constraints_offset=None,
                 large_storage_duration=None, thermal_dispatch_node_id=None, distribution_node_id=None,
                 transmission_node_id=None, distribution_grid_node_id=None):
        DataObject.__init__(self, scenario)
        DispatchConfig._instances_by_id[id] = self

        self.id = id
        self.geography_id = geography_id
        self.flex_load_constraints_offset = flex_load_constraints_offset
        self.large_storage_duration = large_storage_duration
        self.thermal_dispatch_node_id = thermal_dispatch_node_id
        self.distribution_node_id = distribution_node_id
        self.transmission_node_id = transmission_node_id
        self.distribution_grid_node_id = distribution_grid_node_id

        # ints mapped to strings
        self._geography = None

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (id, geography_id, flex_load_constraints_offset, large_storage_duration,
         thermal_dispatch_node_id, distribution_node_id, transmission_node_id,
         distribution_grid_node_id) = tup

        obj = cls(scenario, id=id, geography_id=geography_id,
                  flex_load_constraints_offset=flex_load_constraints_offset,
                  large_storage_duration=large_storage_duration,
                  thermal_dispatch_node_id=thermal_dispatch_node_id,
                  distribution_node_id=distribution_node_id, transmission_node_id=transmission_node_id,
                  distribution_grid_node_id=distribution_grid_node_id)

        return obj

class DispatchConstraintTypes(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, id=None, name=None):
        DataObject.__init__(self, scenario)
        DispatchConstraintTypes._instances_by_id[id] = self

        self.id = id
        self.name = name

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (id, name) = tup

        obj = cls(scenario, id=id, name=name)

        return obj

class DispatchFeeders(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, id=None, name=None):
        DataObject.__init__(self, scenario)
        DispatchFeeders._instances_by_id[id] = self

        self.id = id
        self.name = name

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (id, name) = tup

        obj = cls(scenario, id=id, name=name)

        return obj

class DispatchFeedersAllocation(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, id=None, geography_id=None, geography_map_key_id=None, input_type_id=None,
                 interpolation_method_id=None, extrapolation_method_id=None):
        DataObject.__init__(self, scenario)
        DispatchFeedersAllocation._instances_by_id[id] = self

        self.id = id
        self.geography_id = geography_id
        self.geography_map_key_id = geography_map_key_id
        self.input_type_id = input_type_id
        self.interpolation_method_id = interpolation_method_id
        self.extrapolation_method_id = extrapolation_method_id

        # ints mapped to strings
        self._extrapolation_method = None
        self._geography = None
        self._geography_map_key = None
        self._input_type = None
        self._interpolation_method = None

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (id, geography_id, geography_map_key_id, input_type_id, interpolation_method_id,
         extrapolation_method_id) = tup

        obj = cls(scenario, id=id, geography_id=geography_id, geography_map_key_id=geography_map_key_id,
                  input_type_id=input_type_id, interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id)

        return obj

class DispatchFeedersAllocationData(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, parent_id=None, gau_id=None, dispatch_feeder_id=None, demand_sector_id=None, year=None,
                 value=None, id=None):
        DataObject.__init__(self, scenario)
        DispatchFeedersAllocationData._instances_by_id[id] = self

        self.parent_id = parent_id
        self.gau_id = gau_id
        self.dispatch_feeder_id = dispatch_feeder_id
        self.demand_sector_id = demand_sector_id
        self.year = year
        self.value = value
        self.id = id

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (parent_id, gau_id, dispatch_feeder_id, demand_sector_id, year, value, id) = tup

        obj = cls(scenario, parent_id=parent_id, gau_id=gau_id, dispatch_feeder_id=dispatch_feeder_id,
                  demand_sector_id=demand_sector_id, year=year, value=value, id=id)

        return obj

class DispatchWindows(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, id=None, name=None):
        DataObject.__init__(self, scenario)
        DispatchWindows._instances_by_id[id] = self

        self.id = id
        self.name = name

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (id, name) = tup

        obj = cls(scenario, id=id, name=name)

        return obj

class EfficiencyTypes(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, id=None, name=None):
        DataObject.__init__(self, scenario)
        EfficiencyTypes._instances_by_id[id] = self

        self.id = id
        self.name = name

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (id, name) = tup

        obj = cls(scenario, id=id, name=name)

        return obj

class FinalEnergy(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, id=None, name=None, shape_id=None):
        DataObject.__init__(self, scenario)
        FinalEnergy._instances_by_id[id] = self

        self.id = id
        self.name = name
        self.shape_id = shape_id

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (id, name, shape_id) = tup

        obj = cls(scenario, id=id, name=name, shape_id=shape_id)

        return obj

class FlexibleLoadShiftTypes(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, id=None, name=None):
        DataObject.__init__(self, scenario)
        FlexibleLoadShiftTypes._instances_by_id[id] = self

        self.id = id
        self.name = name

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (id, name) = tup

        obj = cls(scenario, id=id, name=name)

        return obj

class Geographies(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, id=None, name=None):
        DataObject.__init__(self, scenario)
        Geographies._instances_by_id[id] = self

        self.id = id
        self.name = name

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (id, name) = tup

        obj = cls(scenario, id=id, name=name)

        return obj

class GeographiesData(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, id=None, name=None, geography_id=None):
        DataObject.__init__(self, scenario)
        GeographiesData._instances_by_id[id] = self

        self.id = id
        self.name = name
        self.geography_id = geography_id

        # ints mapped to strings
        self._geography = None

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (id, name, geography_id) = tup

        obj = cls(scenario, id=id, name=name, geography_id=geography_id)

        return obj

class GeographyMapKeys(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, id=None, name=None):
        DataObject.__init__(self, scenario)
        GeographyMapKeys._instances_by_id[id] = self

        self.id = id
        self.name = name

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (id, name) = tup

        obj = cls(scenario, id=id, name=name)

        return obj

class GreenhouseGasEmissionsType(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, id=None, name=None):
        DataObject.__init__(self, scenario)
        GreenhouseGasEmissionsType._instances_by_id[id] = self

        self.id = id
        self.name = name

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (id, name) = tup

        obj = cls(scenario, id=id, name=name)

        return obj

class GreenhouseGases(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, id=None, name=None, long_name=None):
        DataObject.__init__(self, scenario)
        GreenhouseGases._instances_by_id[id] = self

        self.id = id
        self.name = name
        self.long_name = long_name

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (id, name, long_name) = tup

        obj = cls(scenario, id=id, name=name, long_name=long_name)

        return obj

class ImportCost(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, import_node_id=None, source=None, notes=None, geography_id=None, currency_id=None,
                 currency_year_id=None, denominator_unit=None, interpolation_method_id=None,
                 extrapolation_method_id=None, extrapolation_growth=None):
        DataObject.__init__(self, scenario)
        ImportCost._instances_by_id[id] = self

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

        # ints mapped to strings
        self._currency = None
        self._extrapolation_method = None
        self._geography = None
        self._interpolation_method = None

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (import_node_id, source, notes, geography_id, currency_id, currency_year_id,
         denominator_unit, interpolation_method_id, extrapolation_method_id, extrapolation_growth) = tup

        obj = cls(scenario, import_node_id=import_node_id, source=source, notes=notes, geography_id=geography_id,
                  currency_id=currency_id, currency_year_id=currency_year_id,
                  denominator_unit=denominator_unit, interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth)

        return obj

class ImportCostData(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, import_node_id=None, gau_id=None, demand_sector_id=None, year=None, value=None, id=None,
                 sensitivity=None, resource_bin=None):
        DataObject.__init__(self, scenario)
        ImportCostData._instances_by_id[id] = self

        self.import_node_id = import_node_id
        self.gau_id = gau_id
        self.demand_sector_id = demand_sector_id
        self.year = year
        self.value = value
        self.id = id
        self.sensitivity = sensitivity
        self.resource_bin = resource_bin

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (import_node_id, gau_id, demand_sector_id, year, value, id, sensitivity, resource_bin) = tup

        obj = cls(scenario, import_node_id=import_node_id, gau_id=gau_id, demand_sector_id=demand_sector_id,
                  year=year, value=value, id=id, sensitivity=sensitivity, resource_bin=resource_bin)

        return obj

class InputTypes(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, id=None, name=None):
        DataObject.__init__(self, scenario)
        InputTypes._instances_by_id[id] = self

        self.id = id
        self.name = name

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (id, name) = tup

        obj = cls(scenario, id=id, name=name)

        return obj

class OtherIndexes(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, id=None, name=None):
        DataObject.__init__(self, scenario)
        OtherIndexes._instances_by_id[id] = self

        self.id = id
        self.name = name

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (id, name) = tup

        obj = cls(scenario, id=id, name=name)

        return obj

class OtherIndexesData(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, id=None, name=None, other_index_id=None):
        DataObject.__init__(self, scenario)
        OtherIndexesData._instances_by_id[id] = self

        self.id = id
        self.name = name
        self.other_index_id = other_index_id

        # ints mapped to strings
        self._other_index = None

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (id, name, other_index_id) = tup

        obj = cls(scenario, id=id, name=name, other_index_id=other_index_id)

        return obj

class OtherIndexesData_copy(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, id=None, name=None, other_index_id=None):
        DataObject.__init__(self, scenario)
        OtherIndexesData_copy._instances_by_id[id] = self

        self.id = id
        self.name = name
        self.other_index_id = other_index_id

        # ints mapped to strings
        self._other_index = None

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (id, name, other_index_id) = tup

        obj = cls(scenario, id=id, name=name, other_index_id=other_index_id)

        return obj

class PrimaryCost(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, primary_node_id=None, geography_id=None, other_index_1_id=None, currency_id=None,
                 currency_year_id=None, denominator_unit=None, interpolation_method_id=None,
                 extrapolation_method_id=None, extrapolation_growth=None):
        DataObject.__init__(self, scenario)
        PrimaryCost._instances_by_id[id] = self

        self.primary_node_id = primary_node_id
        self.geography_id = geography_id
        self.other_index_1_id = other_index_1_id
        self.currency_id = currency_id
        self.currency_year_id = currency_year_id
        self.denominator_unit = denominator_unit
        self.interpolation_method_id = interpolation_method_id
        self.extrapolation_method_id = extrapolation_method_id
        self.extrapolation_growth = extrapolation_growth

        # ints mapped to strings
        self._currency = None
        self._extrapolation_method = None
        self._geography = None
        self._interpolation_method = None
        self._other_index_1 = None

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (primary_node_id, geography_id, other_index_1_id, currency_id, currency_year_id,
         denominator_unit, interpolation_method_id, extrapolation_method_id, extrapolation_growth) = tup

        obj = cls(scenario, primary_node_id=primary_node_id, geography_id=geography_id,
                  other_index_1_id=other_index_1_id, currency_id=currency_id,
                  currency_year_id=currency_year_id, denominator_unit=denominator_unit,
                  interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth)

        return obj

class PrimaryCostData(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, primary_node_id=None, gau_id=None, demand_sector_id=None, oth_1_id=None,
                 resource_bin=None, year=None, value=None, id=None, sensitivity=None):
        DataObject.__init__(self, scenario)
        PrimaryCostData._instances_by_id[id] = self

        self.primary_node_id = primary_node_id
        self.gau_id = gau_id
        self.demand_sector_id = demand_sector_id
        self.oth_1_id = oth_1_id
        self.resource_bin = resource_bin
        self.year = year
        self.value = value
        self.id = id
        self.sensitivity = sensitivity

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (primary_node_id, gau_id, demand_sector_id, oth_1_id, resource_bin, year, value, id,
         sensitivity) = tup

        obj = cls(scenario, primary_node_id=primary_node_id, gau_id=gau_id, demand_sector_id=demand_sector_id,
                  oth_1_id=oth_1_id, resource_bin=resource_bin, year=year, value=value, id=id,
                  sensitivity=sensitivity)

        return obj

class Shapes(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, id=None, name=None, shape_type_id=None, shape_unit_type_id=None, time_zone_id=None,
                 geography_id=None, other_index_1_id=None, other_index_2_id=None,
                 geography_map_key_id=None, interpolation_method_id=None, extrapolation_method_id=None,
                 input_type_id=None):
        DataObject.__init__(self, scenario)
        Shapes._instances_by_id[id] = self

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

        # ints mapped to strings
        self._extrapolation_method = None
        self._geography = None
        self._geography_map_key = None
        self._input_type = None
        self._interpolation_method = None
        self._other_index_1 = None
        self._other_index_2 = None
        self._shape_type = None
        self._shape_unit_type = None

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (id, name, shape_type_id, shape_unit_type_id, time_zone_id, geography_id, other_index_1_id,
         other_index_2_id, geography_map_key_id, interpolation_method_id, extrapolation_method_id,
         input_type_id) = tup

        obj = cls(scenario, id=id, name=name, shape_type_id=shape_type_id, shape_unit_type_id=shape_unit_type_id,
                  time_zone_id=time_zone_id, geography_id=geography_id, other_index_1_id=other_index_1_id,
                  other_index_2_id=other_index_2_id, geography_map_key_id=geography_map_key_id,
                  interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id, input_type_id=input_type_id)

        return obj

class ShapesData(DataObject):
    _instances_by_id = {}

    __slots__ = ['parent_id', 'gau_id', 'dispatch_feeder_id', 'timeshift_type_id', 'resource_bin',
                 'dispatch_constraint_id', 'year', 'month', 'week', 'hour', 'day_type_id',
                 'weather_datetime', 'value', 'id', '_day_type', '_dispatch_constraint',
                 '_dispatch_feeder', '_timeshift_type']

    def __init__(self, scenario, parent_id=None, gau_id=None, dispatch_feeder_id=None, timeshift_type_id=None,
                 resource_bin=None, dispatch_constraint_id=None, year=None, month=None, week=None,
                 hour=None, day_type_id=None, weather_datetime=None, value=None, id=None):
        DataObject.__init__(self, scenario)
        ShapesData._instances_by_id[id] = self

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

        # ints mapped to strings
        self._day_type = None
        self._dispatch_constraint = None
        self._dispatch_feeder = None
        self._timeshift_type = None

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (parent_id, gau_id, dispatch_feeder_id, timeshift_type_id, resource_bin,
         dispatch_constraint_id, year, month, week, hour, day_type_id, weather_datetime, value, id) = tup

        obj = cls(scenario, parent_id=parent_id, gau_id=gau_id, dispatch_feeder_id=dispatch_feeder_id,
                  timeshift_type_id=timeshift_type_id, resource_bin=resource_bin,
                  dispatch_constraint_id=dispatch_constraint_id, year=year, month=month, week=week,
                  hour=hour, day_type_id=day_type_id, weather_datetime=weather_datetime, value=value, id=id)

        return obj

class ShapesTypes(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, id=None, name=None):
        DataObject.__init__(self, scenario)
        ShapesTypes._instances_by_id[id] = self

        self.id = id
        self.name = name

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (id, name) = tup

        obj = cls(scenario, id=id, name=name)

        return obj

class ShapesUnits(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, id=None, name=None):
        DataObject.__init__(self, scenario)
        ShapesUnits._instances_by_id[id] = self

        self.id = id
        self.name = name

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (id, name) = tup

        obj = cls(scenario, id=id, name=name)

        return obj

class StockDecayFunctions(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, id=None, name=None):
        DataObject.__init__(self, scenario)
        StockDecayFunctions._instances_by_id[id] = self

        self.id = id
        self.name = name

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (id, name) = tup

        obj = cls(scenario, id=id, name=name)

        return obj

class StorageTechsCapacityCapitalCost(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, supply_tech_id=None, definition_id=None, reference_tech_id=None, currency_id=None,
                 geography_id=None, currency_year_id=None, capacity_or_energy_unit=None,
                 is_levelized=None, cost_of_capital=None, interpolation_method_id=None,
                 extrapolation_method_id=None, time_unit=None):
        DataObject.__init__(self, scenario)
        StorageTechsCapacityCapitalCost._instances_by_id[id] = self

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

        # ints mapped to strings
        self._currency = None
        self._definition = None
        self._extrapolation_method = None
        self._geography = None
        self._interpolation_method = None

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (supply_tech_id, definition_id, reference_tech_id, currency_id, geography_id,
         currency_year_id, capacity_or_energy_unit, is_levelized, cost_of_capital,
         interpolation_method_id, extrapolation_method_id, time_unit) = tup

        obj = cls(scenario, supply_tech_id=supply_tech_id, definition_id=definition_id,
                  reference_tech_id=reference_tech_id, currency_id=currency_id, geography_id=geography_id,
                  currency_year_id=currency_year_id, capacity_or_energy_unit=capacity_or_energy_unit,
                  is_levelized=is_levelized, cost_of_capital=cost_of_capital,
                  interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id, time_unit=time_unit)

        return obj

class StorageTechsCapacityCapitalCostNewData(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, supply_tech_id=None, gau_id=None, oth_1_id=None, oth_2_id=None, vintage=None, value=None,
                 id=None, sensitivity=None):
        DataObject.__init__(self, scenario)
        StorageTechsCapacityCapitalCostNewData._instances_by_id[id] = self

        self.supply_tech_id = supply_tech_id
        self.gau_id = gau_id
        self.oth_1_id = oth_1_id
        self.oth_2_id = oth_2_id
        self.vintage = vintage
        self.value = value
        self.id = id
        self.sensitivity = sensitivity

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (supply_tech_id, gau_id, oth_1_id, oth_2_id, vintage, value, id, sensitivity) = tup

        obj = cls(scenario, supply_tech_id=supply_tech_id, gau_id=gau_id, oth_1_id=oth_1_id, oth_2_id=oth_2_id,
                  vintage=vintage, value=value, id=id, sensitivity=sensitivity)

        return obj

class StorageTechsCapacityCapitalCostReplacementData(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, supply_tech_id=None, gau_id=None, oth_1_id=None, oth_2_id=None, vintage=None, value=None,
                 id=None, sensitivity=None):
        DataObject.__init__(self, scenario)
        StorageTechsCapacityCapitalCostReplacementData._instances_by_id[id] = self

        self.supply_tech_id = supply_tech_id
        self.gau_id = gau_id
        self.oth_1_id = oth_1_id
        self.oth_2_id = oth_2_id
        self.vintage = vintage
        self.value = value
        self.id = id
        self.sensitivity = sensitivity

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (supply_tech_id, gau_id, oth_1_id, oth_2_id, vintage, value, id, sensitivity) = tup

        obj = cls(scenario, supply_tech_id=supply_tech_id, gau_id=gau_id, oth_1_id=oth_1_id, oth_2_id=oth_2_id,
                  vintage=vintage, value=value, id=id, sensitivity=sensitivity)

        return obj

class StorageTechsEnergyCapitalCost(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, supply_tech_id=None, definition_id=None, reference_tech_id=None, currency_id=None,
                 geography_id=None, currency_year_id=None, energy_unit=None, is_levelized=None,
                 cost_of_capital=None, interpolation_method_id=None, extrapolation_method_id=None):
        DataObject.__init__(self, scenario)
        StorageTechsEnergyCapitalCost._instances_by_id[id] = self

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

        # ints mapped to strings
        self._currency = None
        self._definition = None
        self._extrapolation_method = None
        self._geography = None
        self._interpolation_method = None

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (supply_tech_id, definition_id, reference_tech_id, currency_id, geography_id,
         currency_year_id, energy_unit, is_levelized, cost_of_capital, interpolation_method_id,
         extrapolation_method_id) = tup

        obj = cls(scenario, supply_tech_id=supply_tech_id, definition_id=definition_id,
                  reference_tech_id=reference_tech_id, currency_id=currency_id, geography_id=geography_id,
                  currency_year_id=currency_year_id, energy_unit=energy_unit, is_levelized=is_levelized,
                  cost_of_capital=cost_of_capital, interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id)

        return obj

class StorageTechsEnergyCapitalCostNewData(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, supply_tech_id=None, gau_id=None, oth_1_id=None, oth_2_id=None, vintage=None, value=None,
                 id=None, sensitivity=None):
        DataObject.__init__(self, scenario)
        StorageTechsEnergyCapitalCostNewData._instances_by_id[id] = self

        self.supply_tech_id = supply_tech_id
        self.gau_id = gau_id
        self.oth_1_id = oth_1_id
        self.oth_2_id = oth_2_id
        self.vintage = vintage
        self.value = value
        self.id = id
        self.sensitivity = sensitivity

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (supply_tech_id, gau_id, oth_1_id, oth_2_id, vintage, value, id, sensitivity) = tup

        obj = cls(scenario, supply_tech_id=supply_tech_id, gau_id=gau_id, oth_1_id=oth_1_id, oth_2_id=oth_2_id,
                  vintage=vintage, value=value, id=id, sensitivity=sensitivity)

        return obj

class StorageTechsEnergyCapitalCostReplacementData(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, supply_tech_id=None, gau_id=None, oth_1_id=None, oth_2_id=None, vintage=None, value=None,
                 id=None, sensitivity=None):
        DataObject.__init__(self, scenario)
        StorageTechsEnergyCapitalCostReplacementData._instances_by_id[id] = self

        self.supply_tech_id = supply_tech_id
        self.gau_id = gau_id
        self.oth_1_id = oth_1_id
        self.oth_2_id = oth_2_id
        self.vintage = vintage
        self.value = value
        self.id = id
        self.sensitivity = sensitivity

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (supply_tech_id, gau_id, oth_1_id, oth_2_id, vintage, value, id, sensitivity) = tup

        obj = cls(scenario, supply_tech_id=supply_tech_id, gau_id=gau_id, oth_1_id=oth_1_id, oth_2_id=oth_2_id,
                  vintage=vintage, value=value, id=id, sensitivity=sensitivity)

        return obj

class SupplyCapacityFactor(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, supply_node_id=None, geography_id=None, unit=None, interpolation_method_id=None,
                 extrapolation_method_id=None, extrapolation_growth=None,
                 age_growth_or_decay_type_id=None, age_growth_or_decay=None):
        DataObject.__init__(self, scenario)
        SupplyCapacityFactor._instances_by_id[id] = self

        self.supply_node_id = supply_node_id
        self.geography_id = geography_id
        self.unit = unit
        self.interpolation_method_id = interpolation_method_id
        self.extrapolation_method_id = extrapolation_method_id
        self.extrapolation_growth = extrapolation_growth
        self.age_growth_or_decay_type_id = age_growth_or_decay_type_id
        self.age_growth_or_decay = age_growth_or_decay

        # ints mapped to strings
        self._age_growth_or_decay_type = None
        self._extrapolation_method = None
        self._geography = None
        self._interpolation_method = None

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (supply_node_id, geography_id, unit, interpolation_method_id, extrapolation_method_id,
         extrapolation_growth, age_growth_or_decay_type_id, age_growth_or_decay) = tup

        obj = cls(scenario, supply_node_id=supply_node_id, geography_id=geography_id, unit=unit,
                  interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth,
                  age_growth_or_decay_type_id=age_growth_or_decay_type_id,
                  age_growth_or_decay=age_growth_or_decay)

        return obj

class SupplyCapacityFactorData(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, supply_node_id=None, gau_id=None, demand_sector_id=None, resource_bin=None, year=None,
                 value=None, id=None):
        DataObject.__init__(self, scenario)
        SupplyCapacityFactorData._instances_by_id[id] = self

        self.supply_node_id = supply_node_id
        self.gau_id = gau_id
        self.demand_sector_id = demand_sector_id
        self.resource_bin = resource_bin
        self.year = year
        self.value = value
        self.id = id

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (supply_node_id, gau_id, demand_sector_id, resource_bin, year, value, id) = tup

        obj = cls(scenario, supply_node_id=supply_node_id, gau_id=gau_id, demand_sector_id=demand_sector_id,
                  resource_bin=resource_bin, year=year, value=value, id=id)

        return obj

class SupplyCost(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, id=None, name=None, source=None, additional_notes=None, supply_node_id=None,
                 geography_id=None, supply_cost_type_id=None, currency_id=None, currency_year_id=None,
                 energy_or_capacity_unit=None, time_unit=None, is_capital_cost=None, cost_of_capital=None,
                 book_life=None, throughput_correlation=None, interpolation_method_id=None,
                 extrapolation_method_id=None, extrapolation_growth=None):
        DataObject.__init__(self, scenario)
        SupplyCost._instances_by_id[id] = self

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

        # ints mapped to strings
        self._currency = None
        self._extrapolation_method = None
        self._geography = None
        self._interpolation_method = None

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (id, name, source, additional_notes, supply_node_id, geography_id, supply_cost_type_id,
         currency_id, currency_year_id, energy_or_capacity_unit, time_unit, is_capital_cost,
         cost_of_capital, book_life, throughput_correlation, interpolation_method_id,
         extrapolation_method_id, extrapolation_growth) = tup

        obj = cls(scenario, id=id, name=name, source=source, additional_notes=additional_notes,
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
    _instances_by_id = {}

    def __init__(self, scenario, parent_id=None, gau_id=None, demand_sector_id=None, resource_bin=None, year=None,
                 value=None, id=None):
        DataObject.__init__(self, scenario)
        SupplyCostData._instances_by_id[id] = self

        self.parent_id = parent_id
        self.gau_id = gau_id
        self.demand_sector_id = demand_sector_id
        self.resource_bin = resource_bin
        self.year = year
        self.value = value
        self.id = id

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (parent_id, gau_id, demand_sector_id, resource_bin, year, value, id) = tup

        obj = cls(scenario, parent_id=parent_id, gau_id=gau_id, demand_sector_id=demand_sector_id,
                  resource_bin=resource_bin, year=year, value=value, id=id)

        return obj

class SupplyCostTypes(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, id=None, name=None):
        DataObject.__init__(self, scenario)
        SupplyCostTypes._instances_by_id[id] = self

        self.id = id
        self.name = name

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (id, name) = tup

        obj = cls(scenario, id=id, name=name)

        return obj

class SupplyEfficiency(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, id=None, geography_id=None, source=None, notes=None, input_unit=None, output_unit=None,
                 interpolation_method_id=None, extrapolation_method_id=None, extrapolation_growth=None):
        DataObject.__init__(self, scenario)
        SupplyEfficiency._instances_by_id[id] = self

        self.id = id
        self.geography_id = geography_id
        self.source = source
        self.notes = notes
        self.input_unit = input_unit
        self.output_unit = output_unit
        self.interpolation_method_id = interpolation_method_id
        self.extrapolation_method_id = extrapolation_method_id
        self.extrapolation_growth = extrapolation_growth

        # ints mapped to strings
        self._extrapolation_method = None
        self._geography = None
        self._interpolation_method = None

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (id, geography_id, source, notes, input_unit, output_unit, interpolation_method_id,
         extrapolation_method_id, extrapolation_growth) = tup

        obj = cls(scenario, id=id, geography_id=geography_id, source=source, notes=notes, input_unit=input_unit,
                  output_unit=output_unit, interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth)

        return obj

class SupplyEfficiencyData(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, parent_id=None, gau_id=None, efficiency_type_id=None, demand_sector_id=None,
                 supply_node_id=None, resource_bin=None, year=None, value=None, id=None):
        DataObject.__init__(self, scenario)
        SupplyEfficiencyData._instances_by_id[id] = self

        self.parent_id = parent_id
        self.gau_id = gau_id
        self.efficiency_type_id = efficiency_type_id
        self.demand_sector_id = demand_sector_id
        self.supply_node_id = supply_node_id
        self.resource_bin = resource_bin
        self.year = year
        self.value = value
        self.id = id

        # ints mapped to strings
        self._efficiency_type = None

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (parent_id, gau_id, efficiency_type_id, demand_sector_id, supply_node_id, resource_bin,
         year, value, id) = tup

        obj = cls(scenario, parent_id=parent_id, gau_id=gau_id, efficiency_type_id=efficiency_type_id,
                  demand_sector_id=demand_sector_id, supply_node_id=supply_node_id,
                  resource_bin=resource_bin, year=year, value=value, id=id)

        return obj

class SupplyEmissions(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, supply_node_id=None, geography_id=None, other_index_1_id=None, mass_unit=None,
                 denominator_unit=None, interpolation_method_id=None, extrapolation_method_id=None,
                 extrapolation_growth=None, source=None, notes=None):
        DataObject.__init__(self, scenario)
        SupplyEmissions._instances_by_id[id] = self

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

        # ints mapped to strings
        self._extrapolation_method = None
        self._geography = None
        self._interpolation_method = None
        self._other_index_1 = None

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (supply_node_id, geography_id, other_index_1_id, mass_unit, denominator_unit,
         interpolation_method_id, extrapolation_method_id, extrapolation_growth, source, notes) = tup

        obj = cls(scenario, supply_node_id=supply_node_id, geography_id=geography_id,
                  other_index_1_id=other_index_1_id, mass_unit=mass_unit,
                  denominator_unit=denominator_unit, interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth, source=source, notes=notes)

        return obj

class SupplyEmissionsData(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, supply_node_id=None, gau_id=None, demand_sector_id=None, oth_1_id=None, ghg_type_id=None,
                 ghg_id=None, year=None, value=None, id=None, sensitivity=None):
        DataObject.__init__(self, scenario)
        SupplyEmissionsData._instances_by_id[id] = self

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

        # ints mapped to strings
        self._ghg_type = None

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (supply_node_id, gau_id, demand_sector_id, oth_1_id, ghg_type_id, ghg_id, year, value, id,
         sensitivity) = tup

        obj = cls(scenario, supply_node_id=supply_node_id, gau_id=gau_id, demand_sector_id=demand_sector_id,
                  oth_1_id=oth_1_id, ghg_type_id=ghg_type_id, ghg_id=ghg_id, year=year, value=value, id=id,
                  sensitivity=sensitivity)

        return obj

class SupplyExport(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, supply_node_id=None, geography_id=None, other_index_1_id=None, unit=None,
                 interpolation_method_id=None, extrapolation_method_id=None, extrapolation_growth=None):
        DataObject.__init__(self, scenario)
        SupplyExport._instances_by_id[id] = self

        self.supply_node_id = supply_node_id
        self.geography_id = geography_id
        self.other_index_1_id = other_index_1_id
        self.unit = unit
        self.interpolation_method_id = interpolation_method_id
        self.extrapolation_method_id = extrapolation_method_id
        self.extrapolation_growth = extrapolation_growth

        # ints mapped to strings
        self._extrapolation_method = None
        self._geography = None
        self._interpolation_method = None
        self._other_index_1 = None

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (supply_node_id, geography_id, other_index_1_id, unit, interpolation_method_id,
         extrapolation_method_id, extrapolation_growth) = tup

        obj = cls(scenario, supply_node_id=supply_node_id, geography_id=geography_id,
                  other_index_1_id=other_index_1_id, unit=unit,
                  interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth)

        return obj

class SupplyExportData(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, supply_node_id=None, gau_id=None, oth_1_id=None, resource_bin=None, year=None, value=None,
                 id=None):
        DataObject.__init__(self, scenario)
        SupplyExportData._instances_by_id[id] = self

        self.supply_node_id = supply_node_id
        self.gau_id = gau_id
        self.oth_1_id = oth_1_id
        self.resource_bin = resource_bin
        self.year = year
        self.value = value
        self.id = id

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (supply_node_id, gau_id, oth_1_id, resource_bin, year, value, id) = tup

        obj = cls(scenario, supply_node_id=supply_node_id, gau_id=gau_id, oth_1_id=oth_1_id,
                  resource_bin=resource_bin, year=year, value=value, id=id)

        return obj

class SupplyExportMeasures(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, id=None, supply_node_id=None, name=None, geography_id=None, other_index_1_id=None,
                 interpolation_method_id=None, extrapolation_method_id=None, unit=None):
        DataObject.__init__(self, scenario)
        SupplyExportMeasures._instances_by_id[id] = self

        self.id = id
        self.supply_node_id = supply_node_id
        self.name = name
        self.geography_id = geography_id
        self.other_index_1_id = other_index_1_id
        self.interpolation_method_id = interpolation_method_id
        self.extrapolation_method_id = extrapolation_method_id
        self.unit = unit

        # ints mapped to strings
        self._extrapolation_method = None
        self._geography = None
        self._interpolation_method = None
        self._other_index_1 = None

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (id, supply_node_id, name, geography_id, other_index_1_id, interpolation_method_id,
         extrapolation_method_id, unit) = tup

        obj = cls(scenario, id=id, supply_node_id=supply_node_id, name=name, geography_id=geography_id,
                  other_index_1_id=other_index_1_id, interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id, unit=unit)

        return obj

class SupplyExportMeasuresData(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, parent_id=None, gau_id=None, oth_1_id=None, year=None, value=None, id=None):
        DataObject.__init__(self, scenario)
        SupplyExportMeasuresData._instances_by_id[id] = self

        self.parent_id = parent_id
        self.gau_id = gau_id
        self.oth_1_id = oth_1_id
        self.year = year
        self.value = value
        self.id = id

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (parent_id, gau_id, oth_1_id, year, value, id) = tup

        obj = cls(scenario, parent_id=parent_id, gau_id=gau_id, oth_1_id=oth_1_id, year=year, value=value, id=id)

        return obj

class SupplyNodes(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, id=None, name=None, supply_type_id=None, tradable_geography_id=None, is_active=None,
                 final_energy_link=None, is_curtailable=None, is_exportable=None, is_flexible=None,
                 residual_supply_node_id=None, mean_lifetime=None, lifetime_variance=None,
                 max_lifetime=None, min_lifetime=None, stock_decay_function_id=None, cost_of_capital=None,
                 book_life=None, geography_map_key_id=None, shape_id=None, max_lag_hours=None,
                 max_lead_hours=None, enforce_potential_constraint=None):
        DataObject.__init__(self, scenario)
        SupplyNodes._instances_by_id[id] = self

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

        # ints mapped to strings
        self._geography_map_key = None
        self._stock_decay_function = None
        self._supply_type = None
        self._tradable_geography = None

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (id, name, supply_type_id, tradable_geography_id, is_active, final_energy_link,
         is_curtailable, is_exportable, is_flexible, residual_supply_node_id, mean_lifetime,
         lifetime_variance, max_lifetime, min_lifetime, stock_decay_function_id, cost_of_capital,
         book_life, geography_map_key_id, shape_id, max_lag_hours, max_lead_hours,
         enforce_potential_constraint) = tup

        obj = cls(scenario, id=id, name=name, supply_type_id=supply_type_id,
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
    _instances_by_id = {}

    def __init__(self, scenario, enforce=False, supply_node_id=None, geography_id=None, other_index_1_id=None, unit=None,
                 time_unit=None, interpolation_method_id=None, extrapolation_growth=None,
                 extrapolation_method_id=None, geography_map_key_id=None):
        DataObject.__init__(self, scenario)
        SupplyPotential._instances_by_id[id] = self

        self.enforce = enforce
        self.supply_node_id = supply_node_id
        self.geography_id = geography_id
        self.other_index_1_id = other_index_1_id
        self.unit = unit
        self.time_unit = time_unit
        self.interpolation_method_id = interpolation_method_id
        self.extrapolation_growth = extrapolation_growth
        self.extrapolation_method_id = extrapolation_method_id
        self.geography_map_key_id = geography_map_key_id

        # ints mapped to strings
        self._extrapolation_method = None
        self._geography = None
        self._geography_map_key = None
        self._interpolation_method = None
        self._other_index_1 = None

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (supply_node_id, geography_id, other_index_1_id, unit, time_unit, interpolation_method_id,
         extrapolation_growth, extrapolation_method_id, geography_map_key_id) = tup

        obj = cls(scenario, kwargs.get("enforce", False), supply_node_id=supply_node_id, geography_id=geography_id,
                  other_index_1_id=other_index_1_id, unit=unit, time_unit=time_unit,
                  interpolation_method_id=interpolation_method_id,
                  extrapolation_growth=extrapolation_growth,
                  extrapolation_method_id=extrapolation_method_id,
                  geography_map_key_id=geography_map_key_id)

        return obj

class SupplyPotentialConversion(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, supply_node_id=None, geography_id=None, other_index_1_id=None, energy_unit_numerator=None,
                 resource_unit_denominator=None, interpolation_method_id=None,
                 extrapolation_method_id=None, extrapolation_growth=None):
        DataObject.__init__(self, scenario)
        SupplyPotentialConversion._instances_by_id[id] = self

        self.supply_node_id = supply_node_id
        self.geography_id = geography_id
        self.other_index_1_id = other_index_1_id
        self.energy_unit_numerator = energy_unit_numerator
        self.resource_unit_denominator = resource_unit_denominator
        self.interpolation_method_id = interpolation_method_id
        self.extrapolation_method_id = extrapolation_method_id
        self.extrapolation_growth = extrapolation_growth

        # ints mapped to strings
        self._extrapolation_method = None
        self._geography = None
        self._interpolation_method = None
        self._other_index_1 = None

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (supply_node_id, geography_id, other_index_1_id, energy_unit_numerator,
         resource_unit_denominator, interpolation_method_id, extrapolation_method_id,
         extrapolation_growth) = tup

        obj = cls(scenario, supply_node_id=supply_node_id, geography_id=geography_id,
                  other_index_1_id=other_index_1_id, energy_unit_numerator=energy_unit_numerator,
                  resource_unit_denominator=resource_unit_denominator,
                  interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth)

        return obj

class SupplyPotentialConversionData(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, supply_node_id=None, gau_id=None, oth_1_id=None, resource_bin=None, year=None, value=None,
                 id=None):
        DataObject.__init__(self, scenario)
        SupplyPotentialConversionData._instances_by_id[id] = self

        self.supply_node_id = supply_node_id
        self.gau_id = gau_id
        self.oth_1_id = oth_1_id
        self.resource_bin = resource_bin
        self.year = year
        self.value = value
        self.id = id

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (supply_node_id, gau_id, oth_1_id, resource_bin, year, value, id) = tup

        obj = cls(scenario, supply_node_id=supply_node_id, gau_id=gau_id, oth_1_id=oth_1_id,
                  resource_bin=resource_bin, year=year, value=value, id=id)

        return obj

class SupplyPotentialData(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, supply_node_id=None, gau_id=None, demand_sector_id=None, oth_1_id=None, resource_bin=None,
                 year=None, value=None, id=None, sensitivity=None):
        DataObject.__init__(self, scenario)
        SupplyPotentialData._instances_by_id[id] = self

        self.supply_node_id = supply_node_id
        self.gau_id = gau_id
        self.demand_sector_id = demand_sector_id
        self.oth_1_id = oth_1_id
        self.resource_bin = resource_bin
        self.year = year
        self.value = value
        self.id = id
        self.sensitivity = sensitivity

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (supply_node_id, gau_id, demand_sector_id, oth_1_id, resource_bin, year, value, id,
         sensitivity) = tup

        obj = cls(scenario, supply_node_id=supply_node_id, gau_id=gau_id, demand_sector_id=demand_sector_id,
                  oth_1_id=oth_1_id, resource_bin=resource_bin, year=year, value=value, id=id,
                  sensitivity=sensitivity)

        return obj

class SupplySales(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, supply_node_id=None, geography_id=None, capacity_or_energy_unit=None, time_unit=None,
                 interpolation_method_id=None, extrapolation_method_id=None, extrapolation_growth=None,
                 geography_map_key_id=None):
        DataObject.__init__(self, scenario)
        SupplySales._instances_by_id[id] = self

        self.supply_node_id = supply_node_id
        self.geography_id = geography_id
        self.capacity_or_energy_unit = capacity_or_energy_unit
        self.time_unit = time_unit
        self.interpolation_method_id = interpolation_method_id
        self.extrapolation_method_id = extrapolation_method_id
        self.extrapolation_growth = extrapolation_growth
        self.geography_map_key_id = geography_map_key_id

        # ints mapped to strings
        self._extrapolation_method = None
        self._geography = None
        self._geography_map_key = None
        self._interpolation_method = None

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (supply_node_id, geography_id, capacity_or_energy_unit, time_unit, interpolation_method_id,
         extrapolation_method_id, extrapolation_growth, geography_map_key_id) = tup

        obj = cls(scenario, supply_node_id=supply_node_id, geography_id=geography_id,
                  capacity_or_energy_unit=capacity_or_energy_unit, time_unit=time_unit,
                  interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth, geography_map_key_id=geography_map_key_id)

        return obj

class SupplySalesData(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, supply_node_id=None, gau_id=None, demand_sector_id=None, supply_technology_id=None,
                 vintage=None, value=None, id=None, resource_bin=None):
        DataObject.__init__(self, scenario)
        SupplySalesData._instances_by_id[id] = self

        self.supply_node_id = supply_node_id
        self.gau_id = gau_id
        self.demand_sector_id = demand_sector_id
        self.supply_technology_id = supply_technology_id
        self.vintage = vintage
        self.value = value
        self.id = id
        self.resource_bin = resource_bin

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (supply_node_id, gau_id, demand_sector_id, supply_technology_id, vintage, value, id,
         resource_bin) = tup

        obj = cls(scenario, supply_node_id=supply_node_id, gau_id=gau_id, demand_sector_id=demand_sector_id,
                  supply_technology_id=supply_technology_id, vintage=vintage, value=value, id=id,
                  resource_bin=resource_bin)

        return obj

class SupplySalesMeasures(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, id=None, name=None, supply_technology_id=None, supply_node_id=None, geography_id=None,
                 other_index_1_id=None, interpolation_method_id=None, extrapolation_method_id=None,
                 extrapolation_growth=None, geography_map_key_id=None):
        DataObject.__init__(self, scenario)
        SupplySalesMeasures._instances_by_id[id] = self

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

        # ints mapped to strings
        self._extrapolation_method = None
        self._geography = None
        self._geography_map_key = None
        self._interpolation_method = None
        self._other_index_1 = None

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (id, name, supply_technology_id, supply_node_id, geography_id, other_index_1_id,
         interpolation_method_id, extrapolation_method_id, extrapolation_growth,
         geography_map_key_id) = tup

        obj = cls(scenario, id=id, name=name, supply_technology_id=supply_technology_id,
                  supply_node_id=supply_node_id, geography_id=geography_id,
                  other_index_1_id=other_index_1_id, interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth, geography_map_key_id=geography_map_key_id)

        return obj

class SupplySalesMeasuresData(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, parent_id=None, gau_id=None, oth_1_id=None, demand_sector_id=None, resource_bin=None,
                 vintage=None, value=None, id=None):
        DataObject.__init__(self, scenario)
        SupplySalesMeasuresData._instances_by_id[id] = self

        self.parent_id = parent_id
        self.gau_id = gau_id
        self.oth_1_id = oth_1_id
        self.demand_sector_id = demand_sector_id
        self.resource_bin = resource_bin
        self.vintage = vintage
        self.value = value
        self.id = id

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (parent_id, gau_id, oth_1_id, demand_sector_id, resource_bin, vintage, value, id) = tup

        obj = cls(scenario, parent_id=parent_id, gau_id=gau_id, oth_1_id=oth_1_id, demand_sector_id=demand_sector_id,
                  resource_bin=resource_bin, vintage=vintage, value=value, id=id)

        return obj

class SupplySalesShare(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, supply_node_id=None, geography_id=None, interpolation_method_id=None,
                 extrapolation_method_id=None, extrapolation_growth=None):
        DataObject.__init__(self, scenario)
        SupplySalesShare._instances_by_id[id] = self

        self.supply_node_id = supply_node_id
        self.geography_id = geography_id
        self.interpolation_method_id = interpolation_method_id
        self.extrapolation_method_id = extrapolation_method_id
        self.extrapolation_growth = extrapolation_growth

        # ints mapped to strings
        self._extrapolation_method = None
        self._geography = None
        self._interpolation_method = None

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (supply_node_id, geography_id, interpolation_method_id, extrapolation_method_id,
         extrapolation_growth) = tup

        obj = cls(scenario, supply_node_id=supply_node_id, geography_id=geography_id,
                  interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth)

        return obj

class SupplySalesShareData(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, supply_node_id=None, gau_id=None, demand_sector_id=None, supply_technology_id=None,
                 vintage=None, value=None, id=None):
        DataObject.__init__(self, scenario)
        SupplySalesShareData._instances_by_id[id] = self

        self.supply_node_id = supply_node_id
        self.gau_id = gau_id
        self.demand_sector_id = demand_sector_id
        self.supply_technology_id = supply_technology_id
        self.vintage = vintage
        self.value = value
        self.id = id

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (supply_node_id, gau_id, demand_sector_id, supply_technology_id, vintage, value, id) = tup

        obj = cls(scenario, supply_node_id=supply_node_id, gau_id=gau_id, demand_sector_id=demand_sector_id,
                  supply_technology_id=supply_technology_id, vintage=vintage, value=value, id=id)

        return obj

class SupplySalesShareMeasures(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, id=None, name=None, supply_node_id=None, supply_technology_id=None,
                 replaced_supply_technology_id=None, geography_id=None, capacity_or_energy_unit=None,
                 time_unit=None, interpolation_method_id=None, extrapolation_method_id=None,
                 extrapolation_growth=None, other_index_1_id=None):
        DataObject.__init__(self, scenario)
        SupplySalesShareMeasures._instances_by_id[id] = self

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

        # ints mapped to strings
        self._extrapolation_method = None
        self._geography = None
        self._interpolation_method = None
        self._other_index_1 = None

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (id, name, supply_node_id, supply_technology_id, replaced_supply_technology_id,
         geography_id, capacity_or_energy_unit, time_unit, interpolation_method_id,
         extrapolation_method_id, extrapolation_growth, other_index_1_id) = tup

        obj = cls(scenario, id=id, name=name, supply_node_id=supply_node_id,
                  supply_technology_id=supply_technology_id,
                  replaced_supply_technology_id=replaced_supply_technology_id, geography_id=geography_id,
                  capacity_or_energy_unit=capacity_or_energy_unit, time_unit=time_unit,
                  interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth, other_index_1_id=other_index_1_id)

        return obj

class SupplySalesShareMeasuresData(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, parent_id=None, gau_id=None, demand_sector_id=None, vintage=None, value=None, id=None,
                 resource_bin=None, oth_1_id=None):
        DataObject.__init__(self, scenario)
        SupplySalesShareMeasuresData._instances_by_id[id] = self

        self.parent_id = parent_id
        self.gau_id = gau_id
        self.demand_sector_id = demand_sector_id
        self.vintage = vintage
        self.value = value
        self.id = id
        self.resource_bin = resource_bin
        self.oth_1_id = oth_1_id

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (parent_id, gau_id, demand_sector_id, vintage, value, id, resource_bin, oth_1_id) = tup

        obj = cls(scenario, parent_id=parent_id, gau_id=gau_id, demand_sector_id=demand_sector_id, vintage=vintage,
                  value=value, id=id, resource_bin=resource_bin, oth_1_id=oth_1_id)

        return obj

class SupplyStock(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, supply_node_id=None, geography_id=None, capacity_or_energy_unit=None, time_unit=None,
                 interpolation_method_id=None, extrapolation_method_id=None, extrapolation_growth=None,
                 geography_map_key_id=None):
        DataObject.__init__(self, scenario)
        SupplyStock._instances_by_id[id] = self

        self.supply_node_id = supply_node_id
        self.geography_id = geography_id
        self.capacity_or_energy_unit = capacity_or_energy_unit
        self.time_unit = time_unit
        self.interpolation_method_id = interpolation_method_id
        self.extrapolation_method_id = extrapolation_method_id
        self.extrapolation_growth = extrapolation_growth
        self.geography_map_key_id = geography_map_key_id

        # ints mapped to strings
        self._extrapolation_method = None
        self._geography = None
        self._geography_map_key = None
        self._interpolation_method = None

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (supply_node_id, geography_id, capacity_or_energy_unit, time_unit, interpolation_method_id,
         extrapolation_method_id, extrapolation_growth, geography_map_key_id) = tup

        obj = cls(scenario, supply_node_id=supply_node_id, geography_id=geography_id,
                  capacity_or_energy_unit=capacity_or_energy_unit, time_unit=time_unit,
                  interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth, geography_map_key_id=geography_map_key_id)

        return obj

class SupplyStockData(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, supply_node_id=None, gau_id=None, demand_sector_id=None, supply_technology_id=None,
                 resource_bin=None, year=None, value=None, id=None, sensitivity=None):
        DataObject.__init__(self, scenario)
        SupplyStockData._instances_by_id[id] = self

        self.supply_node_id = supply_node_id
        self.gau_id = gau_id
        self.demand_sector_id = demand_sector_id
        self.supply_technology_id = supply_technology_id
        self.resource_bin = resource_bin
        self.year = year
        self.value = value
        self.id = id
        self.sensitivity = sensitivity

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (supply_node_id, gau_id, demand_sector_id, supply_technology_id, resource_bin, year, value,
         id, sensitivity) = tup

        obj = cls(scenario, supply_node_id=supply_node_id, gau_id=gau_id, demand_sector_id=demand_sector_id,
                  supply_technology_id=supply_technology_id, resource_bin=resource_bin, year=year,
                  value=value, id=id, sensitivity=sensitivity)

        return obj

class SupplyStockMeasures(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, id=None, name=None, supply_technology_id=None, supply_node_id=None, geography_id=None,
                 other_index_1_id=None, capacity_or_energy_unit=None, time_unit=None,
                 interpolation_method_id=None, extrapolation_method_id=None, extrapolation_growth=None,
                 geography_map_key_id=None):
        DataObject.__init__(self, scenario)
        SupplyStockMeasures._instances_by_id[id] = self

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

        # ints mapped to strings
        self._extrapolation_method = None
        self._geography = None
        self._geography_map_key = None
        self._interpolation_method = None
        self._other_index_1 = None

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (id, name, supply_technology_id, supply_node_id, geography_id, other_index_1_id,
         capacity_or_energy_unit, time_unit, interpolation_method_id, extrapolation_method_id,
         extrapolation_growth, geography_map_key_id) = tup

        obj = cls(scenario, id=id, name=name, supply_technology_id=supply_technology_id,
                  supply_node_id=supply_node_id, geography_id=geography_id,
                  other_index_1_id=other_index_1_id, capacity_or_energy_unit=capacity_or_energy_unit,
                  time_unit=time_unit, interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth, geography_map_key_id=geography_map_key_id)

        return obj

class SupplyStockMeasuresData(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, parent_id=None, gau_id=None, oth_1_id=None, demand_sector_id=None, year=None, value=None,
                 id=None, resource_bin=None):
        DataObject.__init__(self, scenario)
        SupplyStockMeasuresData._instances_by_id[id] = self

        self.parent_id = parent_id
        self.gau_id = gau_id
        self.oth_1_id = oth_1_id
        self.demand_sector_id = demand_sector_id
        self.year = year
        self.value = value
        self.id = id
        self.resource_bin = resource_bin

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (parent_id, gau_id, oth_1_id, demand_sector_id, year, value, id, resource_bin) = tup

        obj = cls(scenario, parent_id=parent_id, gau_id=gau_id, oth_1_id=oth_1_id, demand_sector_id=demand_sector_id,
                  year=year, value=value, id=id, resource_bin=resource_bin)

        return obj

class SupplyTechs(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, id=None, name=None, supply_node_id=None, source=None, additional_description=None,
                 stock_decay_function_id=None, book_life=None, mean_lifetime=None, lifetime_variance=None,
                 min_lifetime=None, max_lifetime=None, discharge_duration=None, cost_of_capital=None,
                 shape_id=None, max_lag_hours=None, max_lead_hours=None, thermal_capacity_multiplier=None):
        DataObject.__init__(self, scenario)
        SupplyTechs._instances_by_id[id] = self

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

        # ints mapped to strings
        self._stock_decay_function = None

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (id, name, supply_node_id, source, additional_description, stock_decay_function_id,
         book_life, mean_lifetime, lifetime_variance, min_lifetime, max_lifetime,
         discharge_duration, cost_of_capital, shape_id, max_lag_hours, max_lead_hours,
         thermal_capacity_multiplier) = tup

        obj = cls(scenario, id=id, name=name, supply_node_id=supply_node_id, source=source,
                  additional_description=additional_description,
                  stock_decay_function_id=stock_decay_function_id, book_life=book_life,
                  mean_lifetime=mean_lifetime, lifetime_variance=lifetime_variance,
                  min_lifetime=min_lifetime, max_lifetime=max_lifetime,
                  discharge_duration=discharge_duration, cost_of_capital=cost_of_capital,
                  shape_id=shape_id, max_lag_hours=max_lag_hours, max_lead_hours=max_lead_hours,
                  thermal_capacity_multiplier=thermal_capacity_multiplier)

        return obj

class SupplyTechsCO2Capture(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, supply_tech_id=None, definition_id=None, geography_id=None, reference_tech_id=None,
                 interpolation_method_id=None, extrapolation_method_id=None, extrapolation_growth=None,
                 age_growth_or_decay_type_id=None, age_growth_or_decay=None):
        DataObject.__init__(self, scenario)
        SupplyTechsCO2Capture._instances_by_id[id] = self

        self.supply_tech_id = supply_tech_id
        self.definition_id = definition_id
        self.geography_id = geography_id
        self.reference_tech_id = reference_tech_id
        self.interpolation_method_id = interpolation_method_id
        self.extrapolation_method_id = extrapolation_method_id
        self.extrapolation_growth = extrapolation_growth
        self.age_growth_or_decay_type_id = age_growth_or_decay_type_id
        self.age_growth_or_decay = age_growth_or_decay

        # ints mapped to strings
        self._age_growth_or_decay_type = None
        self._definition = None
        self._extrapolation_method = None
        self._geography = None
        self._interpolation_method = None

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (supply_tech_id, definition_id, geography_id, reference_tech_id, interpolation_method_id,
         extrapolation_method_id, extrapolation_growth, age_growth_or_decay_type_id,
         age_growth_or_decay) = tup

        obj = cls(scenario, supply_tech_id=supply_tech_id, definition_id=definition_id, geography_id=geography_id,
                  reference_tech_id=reference_tech_id, interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth,
                  age_growth_or_decay_type_id=age_growth_or_decay_type_id,
                  age_growth_or_decay=age_growth_or_decay)

        return obj

class SupplyTechsCO2CaptureData(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, supply_tech_id=None, gau_id=None, resource_bin=None, vintage=None, value=None, id=None):
        DataObject.__init__(self, scenario)
        SupplyTechsCO2CaptureData._instances_by_id[id] = self

        self.supply_tech_id = supply_tech_id
        self.gau_id = gau_id
        self.resource_bin = resource_bin
        self.vintage = vintage
        self.value = value
        self.id = id

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (supply_tech_id, gau_id, resource_bin, vintage, value, id) = tup

        obj = cls(scenario, supply_tech_id=supply_tech_id, gau_id=gau_id, resource_bin=resource_bin, vintage=vintage,
                  value=value, id=id)

        return obj

class SupplyTechsCapacityFactor(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, supply_tech_id=None, geography_id=None, reference_tech_id=None, definition_id=None,
                 interpolation_method_id=None, extrapolation_method_id=None, extrapolation_growth=None,
                 age_growth_or_decay_type_id=None, age_growth_or_decay=None):
        DataObject.__init__(self, scenario)
        SupplyTechsCapacityFactor._instances_by_id[id] = self

        self.supply_tech_id = supply_tech_id
        self.geography_id = geography_id
        self.reference_tech_id = reference_tech_id
        self.definition_id = definition_id
        self.interpolation_method_id = interpolation_method_id
        self.extrapolation_method_id = extrapolation_method_id
        self.extrapolation_growth = extrapolation_growth
        self.age_growth_or_decay_type_id = age_growth_or_decay_type_id
        self.age_growth_or_decay = age_growth_or_decay

        # ints mapped to strings
        self._age_growth_or_decay_type = None
        self._definition = None
        self._extrapolation_method = None
        self._geography = None
        self._interpolation_method = None

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (supply_tech_id, geography_id, reference_tech_id, definition_id, interpolation_method_id,
         extrapolation_method_id, extrapolation_growth, age_growth_or_decay_type_id,
         age_growth_or_decay) = tup

        obj = cls(scenario, supply_tech_id=supply_tech_id, geography_id=geography_id,
                  reference_tech_id=reference_tech_id, definition_id=definition_id,
                  interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth,
                  age_growth_or_decay_type_id=age_growth_or_decay_type_id,
                  age_growth_or_decay=age_growth_or_decay)

        return obj

class SupplyTechsCapacityFactorData(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, supply_tech_id=None, gau_id=None, oth_1_id=None, resource_bin=None, vintage=None,
                 value=None, id=None):
        DataObject.__init__(self, scenario)
        SupplyTechsCapacityFactorData._instances_by_id[id] = self

        self.supply_tech_id = supply_tech_id
        self.gau_id = gau_id
        self.oth_1_id = oth_1_id
        self.resource_bin = resource_bin
        self.vintage = vintage
        self.value = value
        self.id = id

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (supply_tech_id, gau_id, oth_1_id, resource_bin, vintage, value, id) = tup

        obj = cls(scenario, supply_tech_id=supply_tech_id, gau_id=gau_id, oth_1_id=oth_1_id,
                  resource_bin=resource_bin, vintage=vintage, value=value, id=id)

        return obj

class SupplyTechsCapitalCost(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, supply_tech_id=None, definition_id=None, reference_tech_id=None, geography_id=None,
                 currency_id=None, currency_year_id=None, capacity_or_energy_unit=None, time_unit=None,
                 is_levelized=None, interpolation_method_id=None, extrapolation_method_id=None,
                 extrapolation_growth=None, source=None, notes=None, geography_map_key_id=None):
        DataObject.__init__(self, scenario)
        SupplyTechsCapitalCost._instances_by_id[id] = self

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

        # ints mapped to strings
        self._currency = None
        self._definition = None
        self._extrapolation_method = None
        self._geography = None
        self._geography_map_key = None
        self._interpolation_method = None

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (supply_tech_id, definition_id, reference_tech_id, geography_id, currency_id,
         currency_year_id, capacity_or_energy_unit, time_unit, is_levelized,
         interpolation_method_id, extrapolation_method_id, extrapolation_growth, source, notes,
         geography_map_key_id) = tup

        obj = cls(scenario, supply_tech_id=supply_tech_id, definition_id=definition_id,
                  reference_tech_id=reference_tech_id, geography_id=geography_id, currency_id=currency_id,
                  currency_year_id=currency_year_id, capacity_or_energy_unit=capacity_or_energy_unit,
                  time_unit=time_unit, is_levelized=is_levelized,
                  interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth, source=source, notes=notes,
                  geography_map_key_id=geography_map_key_id)

        return obj

class SupplyTechsCapitalCostNewData(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, supply_tech_id=None, gau_id=None, demand_sector_id=None, resource_bin=None, vintage=None,
                 value=None, id=None, sensitivity=None):
        DataObject.__init__(self, scenario)
        SupplyTechsCapitalCostNewData._instances_by_id[id] = self

        self.supply_tech_id = supply_tech_id
        self.gau_id = gau_id
        self.demand_sector_id = demand_sector_id
        self.resource_bin = resource_bin
        self.vintage = vintage
        self.value = value
        self.id = id
        self.sensitivity = sensitivity

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (supply_tech_id, gau_id, demand_sector_id, resource_bin, vintage, value, id, sensitivity) = tup

        obj = cls(scenario, supply_tech_id=supply_tech_id, gau_id=gau_id, demand_sector_id=demand_sector_id,
                  resource_bin=resource_bin, vintage=vintage, value=value, id=id, sensitivity=sensitivity)

        return obj

class SupplyTechsCapitalCostReplacementData(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, supply_tech_id=None, gau_id=None, demand_sector_id=None, resource_bin=None, vintage=None,
                 value=None, id=None, sensitivity=None):
        DataObject.__init__(self, scenario)
        SupplyTechsCapitalCostReplacementData._instances_by_id[id] = self

        self.supply_tech_id = supply_tech_id
        self.gau_id = gau_id
        self.demand_sector_id = demand_sector_id
        self.resource_bin = resource_bin
        self.vintage = vintage
        self.value = value
        self.id = id
        self.sensitivity = sensitivity

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (supply_tech_id, gau_id, demand_sector_id, resource_bin, vintage, value, id, sensitivity) = tup

        obj = cls(scenario, supply_tech_id=supply_tech_id, gau_id=gau_id, demand_sector_id=demand_sector_id,
                  resource_bin=resource_bin, vintage=vintage, value=value, id=id, sensitivity=sensitivity)

        return obj

class SupplyTechsEfficiency(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, supply_tech_id=None, geography_id=None, definition_id=None, reference_tech_id=None,
                 input_unit=None, output_unit=None, interpolation_method_id=None,
                 extrapolation_method_id=None, extrapolation_growth=None,
                 age_growth_or_decay_type_id=None, age_growth_or_decay=None, source=None, notes=None):
        DataObject.__init__(self, scenario)
        SupplyTechsEfficiency._instances_by_id[id] = self

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

        # ints mapped to strings
        self._age_growth_or_decay_type = None
        self._definition = None
        self._extrapolation_method = None
        self._geography = None
        self._interpolation_method = None

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (supply_tech_id, geography_id, definition_id, reference_tech_id, input_unit, output_unit,
         interpolation_method_id, extrapolation_method_id, extrapolation_growth,
         age_growth_or_decay_type_id, age_growth_or_decay, source, notes) = tup

        obj = cls(scenario, supply_tech_id=supply_tech_id, geography_id=geography_id, definition_id=definition_id,
                  reference_tech_id=reference_tech_id, input_unit=input_unit, output_unit=output_unit,
                  interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth,
                  age_growth_or_decay_type_id=age_growth_or_decay_type_id,
                  age_growth_or_decay=age_growth_or_decay, source=source, notes=notes)

        return obj

class SupplyTechsEfficiencyData(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, supply_tech_id=None, supply_node_id=None, efficiency_type_id=None, gau_id=None,
                 demand_sector_id=None, resource_bin=None, vintage=None, value=None, id=None,
                 sensitivity=None):
        DataObject.__init__(self, scenario)
        SupplyTechsEfficiencyData._instances_by_id[id] = self

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

        # ints mapped to strings
        self._efficiency_type = None

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (supply_tech_id, supply_node_id, efficiency_type_id, gau_id, demand_sector_id,
         resource_bin, vintage, value, id, sensitivity) = tup

        obj = cls(scenario, supply_tech_id=supply_tech_id, supply_node_id=supply_node_id,
                  efficiency_type_id=efficiency_type_id, gau_id=gau_id, demand_sector_id=demand_sector_id,
                  resource_bin=resource_bin, vintage=vintage, value=value, id=id, sensitivity=sensitivity)

        return obj

class SupplyTechsFixedMaintenanceCost(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, supply_tech_id=None, definition_id=None, reference_tech_id=None, geography_id=None,
                 currency_id=None, currency_year_id=None, capacity_or_energy_unit=None, time_unit=None,
                 interpolation_method_id=None, extrapolation_method_id=None, extrapolation_growth=None,
                 age_growth_or_decay_type_id=None, age_growth_or_decay=None, source=None, notes=None):
        DataObject.__init__(self, scenario)
        SupplyTechsFixedMaintenanceCost._instances_by_id[id] = self

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

        # ints mapped to strings
        self._age_growth_or_decay_type = None
        self._currency = None
        self._definition = None
        self._extrapolation_method = None
        self._geography = None
        self._interpolation_method = None

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (supply_tech_id, definition_id, reference_tech_id, geography_id, currency_id,
         currency_year_id, capacity_or_energy_unit, time_unit, interpolation_method_id,
         extrapolation_method_id, extrapolation_growth, age_growth_or_decay_type_id,
         age_growth_or_decay, source, notes) = tup

        obj = cls(scenario, supply_tech_id=supply_tech_id, definition_id=definition_id,
                  reference_tech_id=reference_tech_id, geography_id=geography_id, currency_id=currency_id,
                  currency_year_id=currency_year_id, capacity_or_energy_unit=capacity_or_energy_unit,
                  time_unit=time_unit, interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth,
                  age_growth_or_decay_type_id=age_growth_or_decay_type_id,
                  age_growth_or_decay=age_growth_or_decay, source=source, notes=notes)

        return obj

class SupplyTechsFixedMaintenanceCostData(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, supply_tech_id=None, gau_id=None, demand_sector_id=None, resource_bin=None, vintage=None,
                 value=None, id=None, sensitivity=None):
        DataObject.__init__(self, scenario)
        SupplyTechsFixedMaintenanceCostData._instances_by_id[id] = self

        self.supply_tech_id = supply_tech_id
        self.gau_id = gau_id
        self.demand_sector_id = demand_sector_id
        self.resource_bin = resource_bin
        self.vintage = vintage
        self.value = value
        self.id = id
        self.sensitivity = sensitivity

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (supply_tech_id, gau_id, demand_sector_id, resource_bin, vintage, value, id, sensitivity) = tup

        obj = cls(scenario, supply_tech_id=supply_tech_id, gau_id=gau_id, demand_sector_id=demand_sector_id,
                  resource_bin=resource_bin, vintage=vintage, value=value, id=id, sensitivity=sensitivity)

        return obj

class SupplyTechsInstallationCost(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, supply_tech_id=None, definition_id=None, geography_id=None, reference_tech_id=None,
                 currency_id=None, currency_year_id=None, capacity_or_energy_unit=None, time_unit=None,
                 is_levelized=None, interpolation_method_id=None, extrapolation_method_id=None,
                 extrapolation_growth=None, source=None, notes=None):
        DataObject.__init__(self, scenario)
        SupplyTechsInstallationCost._instances_by_id[id] = self

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

        # ints mapped to strings
        self._currency = None
        self._definition = None
        self._extrapolation_method = None
        self._geography = None
        self._interpolation_method = None

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (supply_tech_id, definition_id, geography_id, reference_tech_id, currency_id,
         currency_year_id, capacity_or_energy_unit, time_unit, is_levelized,
         interpolation_method_id, extrapolation_method_id, extrapolation_growth, source, notes) = tup

        obj = cls(scenario, supply_tech_id=supply_tech_id, definition_id=definition_id, geography_id=geography_id,
                  reference_tech_id=reference_tech_id, currency_id=currency_id,
                  currency_year_id=currency_year_id, capacity_or_energy_unit=capacity_or_energy_unit,
                  time_unit=time_unit, is_levelized=is_levelized,
                  interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth, source=source, notes=notes)

        return obj

class SupplyTechsInstallationCostNewData(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, supply_tech_id=None, gau_id=None, demand_sector_id=None, resource_bin=None, vintage=None,
                 value=None, id=None, sensitivity=None):
        DataObject.__init__(self, scenario)
        SupplyTechsInstallationCostNewData._instances_by_id[id] = self

        self.supply_tech_id = supply_tech_id
        self.gau_id = gau_id
        self.demand_sector_id = demand_sector_id
        self.resource_bin = resource_bin
        self.vintage = vintage
        self.value = value
        self.id = id
        self.sensitivity = sensitivity

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (supply_tech_id, gau_id, demand_sector_id, resource_bin, vintage, value, id, sensitivity) = tup

        obj = cls(scenario, supply_tech_id=supply_tech_id, gau_id=gau_id, demand_sector_id=demand_sector_id,
                  resource_bin=resource_bin, vintage=vintage, value=value, id=id, sensitivity=sensitivity)

        return obj

class SupplyTechsInstallationCostReplacementData(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, supply_tech_id=None, gau_id=None, demand_sector_id=None, resource_bin=None, vintage=None,
                 value=None, id=None, sensitivity=None):
        DataObject.__init__(self, scenario)
        SupplyTechsInstallationCostReplacementData._instances_by_id[id] = self

        self.supply_tech_id = supply_tech_id
        self.gau_id = gau_id
        self.demand_sector_id = demand_sector_id
        self.resource_bin = resource_bin
        self.vintage = vintage
        self.value = value
        self.id = id
        self.sensitivity = sensitivity

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (supply_tech_id, gau_id, demand_sector_id, resource_bin, vintage, value, id, sensitivity) = tup

        obj = cls(scenario, supply_tech_id=supply_tech_id, gau_id=gau_id, demand_sector_id=demand_sector_id,
                  resource_bin=resource_bin, vintage=vintage, value=value, id=id, sensitivity=sensitivity)

        return obj

class SupplyTechsVariableMaintenanceCost(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, supply_tech_id=None, definition_id=None, reference_tech_id=None, currency_id=None,
                 geography_id=None, currency_year_id=None, energy_unit=None, interpolation_method_id=None,
                 extrapolation_method_id=None, extrapolation_growth=None,
                 age_growth_or_decay_type_id=None, age_growth_or_decay=None, source=None, notes=None):
        DataObject.__init__(self, scenario)
        SupplyTechsVariableMaintenanceCost._instances_by_id[id] = self

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

        # ints mapped to strings
        self._currency = None
        self._definition = None
        self._extrapolation_method = None
        self._geography = None
        self._interpolation_method = None
        self._age_growth_or_decay_type = None

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (supply_tech_id, definition_id, reference_tech_id, currency_id, geography_id,
         currency_year_id, energy_unit, interpolation_method_id, extrapolation_method_id,
         extrapolation_growth, age_growth_or_decay_type_id, age_growth_or_decay, source, notes) = tup

        obj = cls(scenario, supply_tech_id=supply_tech_id, definition_id=definition_id,
                  reference_tech_id=reference_tech_id, currency_id=currency_id, geography_id=geography_id,
                  currency_year_id=currency_year_id, energy_unit=energy_unit,
                  interpolation_method_id=interpolation_method_id,
                  extrapolation_method_id=extrapolation_method_id,
                  extrapolation_growth=extrapolation_growth,
                  age_growth_or_decay_type_id=age_growth_or_decay_type_id,
                  age_growth_or_decay=age_growth_or_decay, source=source, notes=notes)

        return obj

class SupplyTechsVariableMaintenanceCostData(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, supply_tech_id=None, gau_id=None, demand_sector_id=None, resource_bin=None, vintage=None,
                 value=None, id=None, sensitivity=None):
        DataObject.__init__(self, scenario)
        SupplyTechsVariableMaintenanceCostData._instances_by_id[id] = self

        self.supply_tech_id = supply_tech_id
        self.gau_id = gau_id
        self.demand_sector_id = demand_sector_id
        self.resource_bin = resource_bin
        self.vintage = vintage
        self.value = value
        self.id = id
        self.sensitivity = sensitivity

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (supply_tech_id, gau_id, demand_sector_id, resource_bin, vintage, value, id, sensitivity) = tup

        obj = cls(scenario, supply_tech_id=supply_tech_id, gau_id=gau_id, demand_sector_id=demand_sector_id,
                  resource_bin=resource_bin, vintage=vintage, value=value, id=id, sensitivity=sensitivity)

        return obj

class SupplyTypes(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, id=None, name=None):
        DataObject.__init__(self, scenario)
        SupplyTypes._instances_by_id[id] = self

        self.id = id
        self.name = name

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (id, name) = tup

        obj = cls(scenario, id=id, name=name)

        return obj

class TimeZones(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, id=None, name=None, utc_shift=None):
        DataObject.__init__(self, scenario)
        TimeZones._instances_by_id[id] = self

        self.id = id
        self.name = name
        self.utc_shift = utc_shift

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (id, name, utc_shift) = tup

        obj = cls(scenario, id=id, name=name, utc_shift=utc_shift)

        return obj

class Version(DataObject):
    _instances_by_id = {}

    def __init__(self, scenario, version_number=None, date=None, author=None):
        DataObject.__init__(self, scenario)
        Version._instances_by_id[id] = self

        self.version_number = version_number
        self.date = date
        self.author = author

        # ints mapped to strings

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (version_number, date, author) = tup

        obj = cls(scenario, version_number=version_number, date=date, author=author)

        return obj

