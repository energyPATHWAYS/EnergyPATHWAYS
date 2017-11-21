## Start of boilerplate.py ##

import sys
from energyPATHWAYS.error import UnknownDataClass
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

from energyPATHWAYS.data_object import DataObject

class BlendNodeBlendMeasures(DataObject):
    _instances_by_key = {}
    _key_col = "name"

    def __init__(self, scenario, name=None, blend_node=None, supply_node=None, geography=None, other_index_1=None,
                 interpolation_method=None, extrapolation_method=None, extrapolation_growth=None):

        DataObject.__init__(self, scenario, key=name, data_table_name="BlendNodeBlendMeasuresData")
        BlendNodeBlendMeasures._instances_by_key[self._key] = self

        self.name = name
        self.blend_node = blend_node
        self.supply_node = supply_node
        self.geography = geography
        self.other_index_1 = other_index_1
        self.interpolation_method = interpolation_method
        self.extrapolation_method = extrapolation_method
        self.extrapolation_growth = extrapolation_growth

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (name, blend_node, supply_node, geography, other_index_1, interpolation_method,
         extrapolation_method, extrapolation_growth) = tup

        obj = cls(scenario, name=name, blend_node=blend_node, supply_node=supply_node, geography=geography,
                  other_index_1=other_index_1, interpolation_method=interpolation_method,
                  extrapolation_method=extrapolation_method, extrapolation_growth=extrapolation_growth)

        return obj

class CO2PriceMeasures(DataObject):
    _instances_by_key = {}
    _key_col = "name"

    def __init__(self, scenario, name=None, geography=None, interpolation_method=None, extrapolation_method=None,
                 extrapolation_growth=None, geography_map_key=None, supply_node_id=None):

        DataObject.__init__(self, scenario, key=name, data_table_name="CO2PriceMeasuresData")
        CO2PriceMeasures._instances_by_key[self._key] = self

        self.name = name
        self.geography = geography
        self.interpolation_method = interpolation_method
        self.extrapolation_method = extrapolation_method
        self.extrapolation_growth = extrapolation_growth
        self.geography_map_key = geography_map_key
        self.supply_node_id = supply_node_id

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (name, geography, interpolation_method, extrapolation_method, extrapolation_growth,
         geography_map_key, supply_node_id) = tup

        obj = cls(scenario, name=name, geography=geography, interpolation_method=interpolation_method,
                  extrapolation_method=extrapolation_method, extrapolation_growth=extrapolation_growth,
                  geography_map_key=geography_map_key, supply_node_id=supply_node_id)

        return obj

class DemandCO2CaptureMeasures(DataObject):
    _instances_by_key = {}
    _key_col = "name"

    def __init__(self, scenario, name=None, subsector=None, input_type=None, unit=None, geography=None, other_index_1=None,
                 other_index_2=None, interpolation_method=None, extrapolation_method=None,
                 extrapolation_growth=None, stock_decay_function=None, min_lifetime=None,
                 max_lifetime=None, mean_lifetime=None, lifetime_variance=None):

        DataObject.__init__(self, scenario, key=name, data_table_name="")
        DemandCO2CaptureMeasures._instances_by_key[self._key] = self

        self.name = name
        self.subsector = subsector
        self.input_type = input_type
        self.unit = unit
        self.geography = geography
        self.other_index_1 = other_index_1
        self.other_index_2 = other_index_2
        self.interpolation_method = interpolation_method
        self.extrapolation_method = extrapolation_method
        self.extrapolation_growth = extrapolation_growth
        self.stock_decay_function = stock_decay_function
        self.min_lifetime = min_lifetime
        self.max_lifetime = max_lifetime
        self.mean_lifetime = mean_lifetime
        self.lifetime_variance = lifetime_variance

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (name, subsector, input_type, unit, geography, other_index_1, other_index_2,
         interpolation_method, extrapolation_method, extrapolation_growth, stock_decay_function,
         min_lifetime, max_lifetime, mean_lifetime, lifetime_variance) = tup

        obj = cls(scenario, name=name, subsector=subsector, input_type=input_type, unit=unit, geography=geography,
                  other_index_1=other_index_1, other_index_2=other_index_2,
                  interpolation_method=interpolation_method, extrapolation_method=extrapolation_method,
                  extrapolation_growth=extrapolation_growth, stock_decay_function=stock_decay_function,
                  min_lifetime=min_lifetime, max_lifetime=max_lifetime, mean_lifetime=mean_lifetime,
                  lifetime_variance=lifetime_variance)

        return obj

class DemandDrivers(DataObject):
    _instances_by_key = {}
    _key_col = "name"

    def __init__(self, scenario, name=None, base_driver=None, input_type=None, unit_prefix=None, unit_base=None,
                 geography=None, other_index_1=None, other_index_2=None, geography_map_key=None,
                 interpolation_method=None, extrapolation_method=None, extrapolation_growth=None,
                 source=None):

        DataObject.__init__(self, scenario, key=name, data_table_name="DemandDriversData")
        DemandDrivers._instances_by_key[self._key] = self

        self.name = name
        self.base_driver = base_driver
        self.input_type = input_type
        self.unit_prefix = unit_prefix
        self.unit_base = unit_base
        self.geography = geography
        self.other_index_1 = other_index_1
        self.other_index_2 = other_index_2
        self.geography_map_key = geography_map_key
        self.interpolation_method = interpolation_method
        self.extrapolation_method = extrapolation_method
        self.extrapolation_growth = extrapolation_growth
        self.source = source

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (name, base_driver, input_type, unit_prefix, unit_base, geography, other_index_1,
         other_index_2, geography_map_key, interpolation_method, extrapolation_method,
         extrapolation_growth, source) = tup

        obj = cls(scenario, name=name, base_driver=base_driver, input_type=input_type, unit_prefix=unit_prefix,
                  unit_base=unit_base, geography=geography, other_index_1=other_index_1,
                  other_index_2=other_index_2, geography_map_key=geography_map_key,
                  interpolation_method=interpolation_method, extrapolation_method=extrapolation_method,
                  extrapolation_growth=extrapolation_growth, source=source)

        return obj

class DemandEnergyDemands(DataObject):
    _instances_by_key = {}
    _key_col = "subsector"

    def __init__(self, scenario, subsector=None, is_stock_dependent=None, input_type=None, unit=None,
                 driver_denominator_1=None, driver_denominator_2=None, driver_1=None, driver_2=None,
                 geography=None, final_energy_index=None, demand_technology_index=None,
                 other_index_1=None, other_index_2=None, interpolation_method=None,
                 extrapolation_method=None, extrapolation_growth=None, geography_map_key=None):

        DataObject.__init__(self, scenario, key=subsector, data_table_name="DemandEnergyDemandsData")
        DemandEnergyDemands._instances_by_key[self._key] = self

        self.subsector = subsector
        self.is_stock_dependent = is_stock_dependent
        self.input_type = input_type
        self.unit = unit
        self.driver_denominator_1 = driver_denominator_1
        self.driver_denominator_2 = driver_denominator_2
        self.driver_1 = driver_1
        self.driver_2 = driver_2
        self.geography = geography
        self.final_energy_index = final_energy_index
        self.demand_technology_index = demand_technology_index
        self.other_index_1 = other_index_1
        self.other_index_2 = other_index_2
        self.interpolation_method = interpolation_method
        self.extrapolation_method = extrapolation_method
        self.extrapolation_growth = extrapolation_growth
        self.geography_map_key = geography_map_key

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (subsector, is_stock_dependent, input_type, unit, driver_denominator_1,
         driver_denominator_2, driver_1, driver_2, geography, final_energy_index,
         demand_technology_index, other_index_1, other_index_2, interpolation_method,
         extrapolation_method, extrapolation_growth, geography_map_key) = tup

        obj = cls(scenario, subsector=subsector, is_stock_dependent=is_stock_dependent, input_type=input_type,
                  unit=unit, driver_denominator_1=driver_denominator_1,
                  driver_denominator_2=driver_denominator_2, driver_1=driver_1, driver_2=driver_2,
                  geography=geography, final_energy_index=final_energy_index,
                  demand_technology_index=demand_technology_index, other_index_1=other_index_1,
                  other_index_2=other_index_2, interpolation_method=interpolation_method,
                  extrapolation_method=extrapolation_method, extrapolation_growth=extrapolation_growth,
                  geography_map_key=geography_map_key)

        return obj

class DemandEnergyEfficiencyMeasures(DataObject):
    _instances_by_key = {}
    _key_col = "name"

    def __init__(self, scenario, name=None, subsector=None, input_type=None, unit=None, geography=None, other_index_1=None,
                 other_index_2=None, interpolation_method=None, extrapolation_method=None,
                 extrapolation_growth=None, stock_decay_function=None, min_lifetime=None,
                 max_lifetime=None, mean_lifetime=None, lifetime_variance=None):

        DataObject.__init__(self, scenario, key=name, data_table_name="DemandEnergyEfficiencyMeasuresData")
        DemandEnergyEfficiencyMeasures._instances_by_key[self._key] = self

        self.name = name
        self.subsector = subsector
        self.input_type = input_type
        self.unit = unit
        self.geography = geography
        self.other_index_1 = other_index_1
        self.other_index_2 = other_index_2
        self.interpolation_method = interpolation_method
        self.extrapolation_method = extrapolation_method
        self.extrapolation_growth = extrapolation_growth
        self.stock_decay_function = stock_decay_function
        self.min_lifetime = min_lifetime
        self.max_lifetime = max_lifetime
        self.mean_lifetime = mean_lifetime
        self.lifetime_variance = lifetime_variance

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (name, subsector, input_type, unit, geography, other_index_1, other_index_2,
         interpolation_method, extrapolation_method, extrapolation_growth, stock_decay_function,
         min_lifetime, max_lifetime, mean_lifetime, lifetime_variance) = tup

        obj = cls(scenario, name=name, subsector=subsector, input_type=input_type, unit=unit, geography=geography,
                  other_index_1=other_index_1, other_index_2=other_index_2,
                  interpolation_method=interpolation_method, extrapolation_method=extrapolation_method,
                  extrapolation_growth=extrapolation_growth, stock_decay_function=stock_decay_function,
                  min_lifetime=min_lifetime, max_lifetime=max_lifetime, mean_lifetime=mean_lifetime,
                  lifetime_variance=lifetime_variance)

        return obj

class DemandEnergyEfficiencyMeasuresCost(DataObject):
    _instances_by_key = {}
    _key_col = "parent"

    def __init__(self, scenario, parent=None, currency=None, currency_year_id=None, cost_denominator_unit=None,
                 cost_of_capital=None, is_levelized=None, geography=None, other_index_1=None,
                 other_index_2=None, interpolation_method=None, extrapolation_method=None,
                 extrapolation_growth=None):

        DataObject.__init__(self, scenario, key=parent, data_table_name="DemandEnergyEfficiencyMeasuresCostData")
        DemandEnergyEfficiencyMeasuresCost._instances_by_key[self._key] = self

        self.parent = parent
        self.currency = currency
        self.currency_year_id = currency_year_id
        self.cost_denominator_unit = cost_denominator_unit
        self.cost_of_capital = cost_of_capital
        self.is_levelized = is_levelized
        self.geography = geography
        self.other_index_1 = other_index_1
        self.other_index_2 = other_index_2
        self.interpolation_method = interpolation_method
        self.extrapolation_method = extrapolation_method
        self.extrapolation_growth = extrapolation_growth

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (parent, currency, currency_year_id, cost_denominator_unit, cost_of_capital, is_levelized,
         geography, other_index_1, other_index_2, interpolation_method, extrapolation_method,
         extrapolation_growth) = tup

        obj = cls(scenario, parent=parent, currency=currency, currency_year_id=currency_year_id,
                  cost_denominator_unit=cost_denominator_unit, cost_of_capital=cost_of_capital,
                  is_levelized=is_levelized, geography=geography, other_index_1=other_index_1,
                  other_index_2=other_index_2, interpolation_method=interpolation_method,
                  extrapolation_method=extrapolation_method, extrapolation_growth=extrapolation_growth)

        return obj

class DemandFlexibleLoadMeasures(DataObject):
    _instances_by_key = {}
    _key_col = "subsector"

    def __init__(self, scenario, subsector=None, geography=None, other_index_1=None, interpolation_method=None,
                 extrapolation_method=None, extrapolation_growth=None, name=None):

        DataObject.__init__(self, scenario, key=subsector, data_table_name="DemandFlexibleLoadMeasuresData")
        DemandFlexibleLoadMeasures._instances_by_key[self._key] = self

        self.subsector = subsector
        self.geography = geography
        self.other_index_1 = other_index_1
        self.interpolation_method = interpolation_method
        self.extrapolation_method = extrapolation_method
        self.extrapolation_growth = extrapolation_growth
        self.name = name

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (subsector, geography, other_index_1, interpolation_method, extrapolation_method,
         extrapolation_growth, name) = tup

        obj = cls(scenario, subsector=subsector, geography=geography, other_index_1=other_index_1,
                  interpolation_method=interpolation_method, extrapolation_method=extrapolation_method,
                  extrapolation_growth=extrapolation_growth, name=name)

        return obj

class DemandFuelSwitchingMeasures(DataObject):
    _instances_by_key = {}
    _key_col = "name"

    def __init__(self, scenario, name=None, subsector=None, final_energy_from=None, final_energy_to=None,
                 stock_decay_function=None, max_lifetime=None, min_lifetime=None, mean_lifetime=None,
                 lifetime_variance=None):

        DataObject.__init__(self, scenario, key=name, data_table_name="")
        DemandFuelSwitchingMeasures._instances_by_key[self._key] = self

        self.name = name
        self.subsector = subsector
        self.final_energy_from = final_energy_from
        self.final_energy_to = final_energy_to
        self.stock_decay_function = stock_decay_function
        self.max_lifetime = max_lifetime
        self.min_lifetime = min_lifetime
        self.mean_lifetime = mean_lifetime
        self.lifetime_variance = lifetime_variance

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (name, subsector, final_energy_from, final_energy_to, stock_decay_function, max_lifetime,
         min_lifetime, mean_lifetime, lifetime_variance) = tup

        obj = cls(scenario, name=name, subsector=subsector, final_energy_from=final_energy_from,
                  final_energy_to=final_energy_to, stock_decay_function=stock_decay_function,
                  max_lifetime=max_lifetime, min_lifetime=min_lifetime, mean_lifetime=mean_lifetime,
                  lifetime_variance=lifetime_variance)

        return obj

class DemandFuelSwitchingMeasuresCost(DataObject):
    _instances_by_key = {}
    _key_col = "parent"

    def __init__(self, scenario, parent=None, currency=None, currency_year_id=None, cost_denominator_unit=None,
                 cost_of_capital=None, is_levelized=None, geography=None, other_index_1=None,
                 other_index_2=None, interpolation_method=None, extrapolation_method=None,
                 extrapolation_growth=None):

        DataObject.__init__(self, scenario, key=parent, data_table_name="DemandFuelSwitchingMeasuresCostData")
        DemandFuelSwitchingMeasuresCost._instances_by_key[self._key] = self

        self.parent = parent
        self.currency = currency
        self.currency_year_id = currency_year_id
        self.cost_denominator_unit = cost_denominator_unit
        self.cost_of_capital = cost_of_capital
        self.is_levelized = is_levelized
        self.geography = geography
        self.other_index_1 = other_index_1
        self.other_index_2 = other_index_2
        self.interpolation_method = interpolation_method
        self.extrapolation_method = extrapolation_method
        self.extrapolation_growth = extrapolation_growth

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (parent, currency, currency_year_id, cost_denominator_unit, cost_of_capital, is_levelized,
         geography, other_index_1, other_index_2, interpolation_method, extrapolation_method,
         extrapolation_growth) = tup

        obj = cls(scenario, parent=parent, currency=currency, currency_year_id=currency_year_id,
                  cost_denominator_unit=cost_denominator_unit, cost_of_capital=cost_of_capital,
                  is_levelized=is_levelized, geography=geography, other_index_1=other_index_1,
                  other_index_2=other_index_2, interpolation_method=interpolation_method,
                  extrapolation_method=extrapolation_method, extrapolation_growth=extrapolation_growth)

        return obj

class DemandFuelSwitchingMeasuresEnergyIntensity(DataObject):
    _instances_by_key = {}
    _key_col = "parent"

    def __init__(self, scenario, parent=None, geography=None, other_index_1=None, other_index_2=None,
                 interpolation_method=None, extrapolation_method=None, extrapolation_growth=None):

        DataObject.__init__(self, scenario, key=parent, data_table_name="DemandFuelSwitchingMeasuresEnergyIntensityData")
        DemandFuelSwitchingMeasuresEnergyIntensity._instances_by_key[self._key] = self

        self.parent = parent
        self.geography = geography
        self.other_index_1 = other_index_1
        self.other_index_2 = other_index_2
        self.interpolation_method = interpolation_method
        self.extrapolation_method = extrapolation_method
        self.extrapolation_growth = extrapolation_growth

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (parent, geography, other_index_1, other_index_2, interpolation_method,
         extrapolation_method, extrapolation_growth) = tup

        obj = cls(scenario, parent=parent, geography=geography, other_index_1=other_index_1,
                  other_index_2=other_index_2, interpolation_method=interpolation_method,
                  extrapolation_method=extrapolation_method, extrapolation_growth=extrapolation_growth)

        return obj

class DemandFuelSwitchingMeasuresImpact(DataObject):
    _instances_by_key = {}
    _key_col = "parent"

    def __init__(self, scenario, parent=None, input_type=None, unit=None, geography=None, other_index_1=None,
                 other_index_2=None, interpolation_method=None, extrapolation_method=None,
                 extrapolation_growth=None):

        DataObject.__init__(self, scenario, key=parent, data_table_name="DemandFuelSwitchingMeasuresImpactData")
        DemandFuelSwitchingMeasuresImpact._instances_by_key[self._key] = self

        self.parent = parent
        self.input_type = input_type
        self.unit = unit
        self.geography = geography
        self.other_index_1 = other_index_1
        self.other_index_2 = other_index_2
        self.interpolation_method = interpolation_method
        self.extrapolation_method = extrapolation_method
        self.extrapolation_growth = extrapolation_growth

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (parent, input_type, unit, geography, other_index_1, other_index_2, interpolation_method,
         extrapolation_method, extrapolation_growth) = tup

        obj = cls(scenario, parent=parent, input_type=input_type, unit=unit, geography=geography,
                  other_index_1=other_index_1, other_index_2=other_index_2,
                  interpolation_method=interpolation_method, extrapolation_method=extrapolation_method,
                  extrapolation_growth=extrapolation_growth)

        return obj

class DemandSales(DataObject):
    _instances_by_key = {}
    _key_col = "subsector"

    def __init__(self, scenario, subsector=None, geography=None, other_index_1=None, other_index_2=None, input_type=None,
                 interpolation_method=None, extrapolation_method=None, extrapolation_growth=None):

        DataObject.__init__(self, scenario, key=subsector, data_table_name="DemandSalesData")
        DemandSales._instances_by_key[self._key] = self

        self.subsector = subsector
        self.geography = geography
        self.other_index_1 = other_index_1
        self.other_index_2 = other_index_2
        self.input_type = input_type
        self.interpolation_method = interpolation_method
        self.extrapolation_method = extrapolation_method
        self.extrapolation_growth = extrapolation_growth

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (subsector, geography, other_index_1, other_index_2, input_type, interpolation_method,
         extrapolation_method, extrapolation_growth) = tup

        obj = cls(scenario, subsector=subsector, geography=geography, other_index_1=other_index_1,
                  other_index_2=other_index_2, input_type=input_type,
                  interpolation_method=interpolation_method, extrapolation_method=extrapolation_method,
                  extrapolation_growth=extrapolation_growth)

        return obj

class DemandSalesShareMeasures(DataObject):
    _instances_by_key = {}
    _key_col = "name"

    def __init__(self, scenario, subsector=None, geography=None, other_index_1=None, demand_technology=None,
                 replaced_demand_tech=None, input_type=None, interpolation_method=None,
                 extrapolation_method=None, extrapolation_growth=None, name=None):

        DataObject.__init__(self, scenario, key=name, data_table_name="DemandSalesShareMeasuresData")
        DemandSalesShareMeasures._instances_by_key[self._key] = self

        self.subsector = subsector
        self.geography = geography
        self.other_index_1 = other_index_1
        self.demand_technology = demand_technology
        self.replaced_demand_tech = replaced_demand_tech
        self.input_type = input_type
        self.interpolation_method = interpolation_method
        self.extrapolation_method = extrapolation_method
        self.extrapolation_growth = extrapolation_growth
        self.name = name

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (subsector, geography, other_index_1, demand_technology, replaced_demand_tech, input_type,
         interpolation_method, extrapolation_method, extrapolation_growth, name) = tup

        obj = cls(scenario, subsector=subsector, geography=geography, other_index_1=other_index_1,
                  demand_technology=demand_technology, replaced_demand_tech=replaced_demand_tech,
                  input_type=input_type, interpolation_method=interpolation_method,
                  extrapolation_method=extrapolation_method, extrapolation_growth=extrapolation_growth,
                  name=name)

        return obj

class DemandSectors(DataObject):
    _instances_by_key = {}
    _key_col = "name"

    def __init__(self, scenario, name=None, shape=None, max_lead_hours=None, max_lag_hours=None):

        DataObject.__init__(self, scenario, key=name, data_table_name="")
        DemandSectors._instances_by_key[self._key] = self

        self.name = name
        self.shape = shape
        self.max_lead_hours = max_lead_hours
        self.max_lag_hours = max_lag_hours

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (name, shape, max_lead_hours, max_lag_hours) = tup

        obj = cls(scenario, name=name, shape=shape, max_lead_hours=max_lead_hours, max_lag_hours=max_lag_hours)

        return obj

class DemandServiceDemandMeasures(DataObject):
    _instances_by_key = {}
    _key_col = "name"

    def __init__(self, scenario, name=None, subsector=None, input_type=None, unit=None, geography=None, other_index_1=None,
                 other_index_2=None, interpolation_method=None, extrapolation_method=None,
                 extrapolation_growth=None, stock_decay_function=None, min_lifetime=None,
                 max_lifetime=None, mean_lifetime=None, lifetime_variance=None):

        DataObject.__init__(self, scenario, key=name, data_table_name="DemandServiceDemandMeasuresData")
        DemandServiceDemandMeasures._instances_by_key[self._key] = self

        self.name = name
        self.subsector = subsector
        self.input_type = input_type
        self.unit = unit
        self.geography = geography
        self.other_index_1 = other_index_1
        self.other_index_2 = other_index_2
        self.interpolation_method = interpolation_method
        self.extrapolation_method = extrapolation_method
        self.extrapolation_growth = extrapolation_growth
        self.stock_decay_function = stock_decay_function
        self.min_lifetime = min_lifetime
        self.max_lifetime = max_lifetime
        self.mean_lifetime = mean_lifetime
        self.lifetime_variance = lifetime_variance

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (name, subsector, input_type, unit, geography, other_index_1, other_index_2,
         interpolation_method, extrapolation_method, extrapolation_growth, stock_decay_function,
         min_lifetime, max_lifetime, mean_lifetime, lifetime_variance) = tup

        obj = cls(scenario, name=name, subsector=subsector, input_type=input_type, unit=unit, geography=geography,
                  other_index_1=other_index_1, other_index_2=other_index_2,
                  interpolation_method=interpolation_method, extrapolation_method=extrapolation_method,
                  extrapolation_growth=extrapolation_growth, stock_decay_function=stock_decay_function,
                  min_lifetime=min_lifetime, max_lifetime=max_lifetime, mean_lifetime=mean_lifetime,
                  lifetime_variance=lifetime_variance)

        return obj

class DemandServiceDemandMeasuresCost(DataObject):
    _instances_by_key = {}
    _key_col = "parent"

    def __init__(self, scenario, parent=None, currency=None, currency_year_id=None, cost_denominator_unit=None,
                 cost_of_capital=None, is_levelized=None, geography=None, other_index_1=None,
                 other_index_2=None, interpolation_method=None, extrapolation_method=None,
                 extrapolation_growth=None):

        DataObject.__init__(self, scenario, key=parent, data_table_name="DemandServiceDemandMeasuresCostData")
        DemandServiceDemandMeasuresCost._instances_by_key[self._key] = self

        self.parent = parent
        self.currency = currency
        self.currency_year_id = currency_year_id
        self.cost_denominator_unit = cost_denominator_unit
        self.cost_of_capital = cost_of_capital
        self.is_levelized = is_levelized
        self.geography = geography
        self.other_index_1 = other_index_1
        self.other_index_2 = other_index_2
        self.interpolation_method = interpolation_method
        self.extrapolation_method = extrapolation_method
        self.extrapolation_growth = extrapolation_growth

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (parent, currency, currency_year_id, cost_denominator_unit, cost_of_capital, is_levelized,
         geography, other_index_1, other_index_2, interpolation_method, extrapolation_method,
         extrapolation_growth) = tup

        obj = cls(scenario, parent=parent, currency=currency, currency_year_id=currency_year_id,
                  cost_denominator_unit=cost_denominator_unit, cost_of_capital=cost_of_capital,
                  is_levelized=is_levelized, geography=geography, other_index_1=other_index_1,
                  other_index_2=other_index_2, interpolation_method=interpolation_method,
                  extrapolation_method=extrapolation_method, extrapolation_growth=extrapolation_growth)

        return obj

class DemandServiceDemands(DataObject):
    _instances_by_key = {}
    _key_col = "subsector"

    def __init__(self, scenario, subsector=None, is_stock_dependent=None, input_type=None, unit=None,
                 driver_denominator_1=None, driver_denominator_2=None, driver_1=None, driver_2=None,
                 geography=None, final_energy_index=None, demand_technology_index=None,
                 other_index_1=None, other_index_2=None, interpolation_method=None,
                 extrapolation_method=None, extrapolation_growth=None, geography_map_key=None):

        DataObject.__init__(self, scenario, key=subsector, data_table_name="DemandServiceDemandsData")
        DemandServiceDemands._instances_by_key[self._key] = self

        self.subsector = subsector
        self.is_stock_dependent = is_stock_dependent
        self.input_type = input_type
        self.unit = unit
        self.driver_denominator_1 = driver_denominator_1
        self.driver_denominator_2 = driver_denominator_2
        self.driver_1 = driver_1
        self.driver_2 = driver_2
        self.geography = geography
        self.final_energy_index = final_energy_index
        self.demand_technology_index = demand_technology_index
        self.other_index_1 = other_index_1
        self.other_index_2 = other_index_2
        self.interpolation_method = interpolation_method
        self.extrapolation_method = extrapolation_method
        self.extrapolation_growth = extrapolation_growth
        self.geography_map_key = geography_map_key

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (subsector, is_stock_dependent, input_type, unit, driver_denominator_1,
         driver_denominator_2, driver_1, driver_2, geography, final_energy_index,
         demand_technology_index, other_index_1, other_index_2, interpolation_method,
         extrapolation_method, extrapolation_growth, geography_map_key) = tup

        obj = cls(scenario, subsector=subsector, is_stock_dependent=is_stock_dependent, input_type=input_type,
                  unit=unit, driver_denominator_1=driver_denominator_1,
                  driver_denominator_2=driver_denominator_2, driver_1=driver_1, driver_2=driver_2,
                  geography=geography, final_energy_index=final_energy_index,
                  demand_technology_index=demand_technology_index, other_index_1=other_index_1,
                  other_index_2=other_index_2, interpolation_method=interpolation_method,
                  extrapolation_method=extrapolation_method, extrapolation_growth=extrapolation_growth,
                  geography_map_key=geography_map_key)

        return obj

class DemandServiceEfficiency(DataObject):
    _instances_by_key = {}
    _key_col = "subsector"

    def __init__(self, scenario, subsector=None, energy_unit=None, denominator_unit=None, geography=None,
                 other_index_1=None, other_index_2=None, interpolation_method=None,
                 extrapolation_method=None, extrapolation_growth=None, geography_map_key=None):

        DataObject.__init__(self, scenario, key=subsector, data_table_name="DemandServiceEfficiencyData")
        DemandServiceEfficiency._instances_by_key[self._key] = self

        self.subsector = subsector
        self.energy_unit = energy_unit
        self.denominator_unit = denominator_unit
        self.geography = geography
        self.other_index_1 = other_index_1
        self.other_index_2 = other_index_2
        self.interpolation_method = interpolation_method
        self.extrapolation_method = extrapolation_method
        self.extrapolation_growth = extrapolation_growth
        self.geography_map_key = geography_map_key

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (subsector, energy_unit, denominator_unit, geography, other_index_1, other_index_2,
         interpolation_method, extrapolation_method, extrapolation_growth, geography_map_key) = tup

        obj = cls(scenario, subsector=subsector, energy_unit=energy_unit, denominator_unit=denominator_unit,
                  geography=geography, other_index_1=other_index_1, other_index_2=other_index_2,
                  interpolation_method=interpolation_method, extrapolation_method=extrapolation_method,
                  extrapolation_growth=extrapolation_growth, geography_map_key=geography_map_key)

        return obj

class DemandServiceLink(DataObject):
    _instances_by_key = {}
    _key_col = "name"

    def __init__(self, scenario, subsector=None, linked_subsector=None, service_demand_share=None, year=None, name=None):

        DataObject.__init__(self, scenario, key=name, data_table_name="")
        DemandServiceLink._instances_by_key[self._key] = self

        self.subsector = subsector
        self.linked_subsector = linked_subsector
        self.service_demand_share = service_demand_share
        self.year = year
        self.name = name

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (subsector, linked_subsector, service_demand_share, year, name) = tup

        obj = cls(scenario, subsector=subsector, linked_subsector=linked_subsector,
                  service_demand_share=service_demand_share, year=year, name=name)

        return obj

class DemandStock(DataObject):
    _instances_by_key = {}
    _key_col = "subsector"

    def __init__(self, scenario, subsector=None, is_service_demand_dependent=None, driver_denominator_1=None,
                 driver_denominator_2=None, driver_1=None, driver_2=None, geography=None,
                 other_index_1=None, other_index_2=None, geography_map_key=None, input_type=None,
                 demand_stock_unit_type=None, unit=None, time_unit=None, interpolation_method=None,
                 extrapolation_method=None, extrapolation_growth=None):

        DataObject.__init__(self, scenario, key=subsector, data_table_name="DemandStockData")
        DemandStock._instances_by_key[self._key] = self

        self.subsector = subsector
        self.is_service_demand_dependent = is_service_demand_dependent
        self.driver_denominator_1 = driver_denominator_1
        self.driver_denominator_2 = driver_denominator_2
        self.driver_1 = driver_1
        self.driver_2 = driver_2
        self.geography = geography
        self.other_index_1 = other_index_1
        self.other_index_2 = other_index_2
        self.geography_map_key = geography_map_key
        self.input_type = input_type
        self.demand_stock_unit_type = demand_stock_unit_type
        self.unit = unit
        self.time_unit = time_unit
        self.interpolation_method = interpolation_method
        self.extrapolation_method = extrapolation_method
        self.extrapolation_growth = extrapolation_growth

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (subsector, is_service_demand_dependent, driver_denominator_1, driver_denominator_2,
         driver_1, driver_2, geography, other_index_1, other_index_2, geography_map_key,
         input_type, demand_stock_unit_type, unit, time_unit, interpolation_method,
         extrapolation_method, extrapolation_growth) = tup

        obj = cls(scenario, subsector=subsector, is_service_demand_dependent=is_service_demand_dependent,
                  driver_denominator_1=driver_denominator_1, driver_denominator_2=driver_denominator_2,
                  driver_1=driver_1, driver_2=driver_2, geography=geography, other_index_1=other_index_1,
                  other_index_2=other_index_2, geography_map_key=geography_map_key, input_type=input_type,
                  demand_stock_unit_type=demand_stock_unit_type, unit=unit, time_unit=time_unit,
                  interpolation_method=interpolation_method, extrapolation_method=extrapolation_method,
                  extrapolation_growth=extrapolation_growth)

        return obj

class DemandStockMeasures(DataObject):
    _instances_by_key = {}
    _key_col = "name"

    def __init__(self, scenario, subsector=None, geography=None, other_index_1=None, demand_technology=None,
                 interpolation_method=None, extrapolation_method=None, extrapolation_growth=None,
                 name=None):

        DataObject.__init__(self, scenario, key=name, data_table_name="DemandStockMeasuresData")
        DemandStockMeasures._instances_by_key[self._key] = self

        self.subsector = subsector
        self.geography = geography
        self.other_index_1 = other_index_1
        self.demand_technology = demand_technology
        self.interpolation_method = interpolation_method
        self.extrapolation_method = extrapolation_method
        self.extrapolation_growth = extrapolation_growth
        self.name = name

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (subsector, geography, other_index_1, demand_technology, interpolation_method,
         extrapolation_method, extrapolation_growth, name) = tup

        obj = cls(scenario, subsector=subsector, geography=geography, other_index_1=other_index_1,
                  demand_technology=demand_technology, interpolation_method=interpolation_method,
                  extrapolation_method=extrapolation_method, extrapolation_growth=extrapolation_growth,
                  name=name)

        return obj

class DemandSubsectors(DataObject):
    _instances_by_key = {}
    _key_col = "name"

    def __init__(self, scenario, sector=None, name=None, cost_of_capital=None, is_active=None, shape=None,
                 max_lead_hours=None, max_lag_hours=None):

        DataObject.__init__(self, scenario, key=name, data_table_name="")
        DemandSubsectors._instances_by_key[self._key] = self

        self.sector = sector
        self.name = name
        self.cost_of_capital = cost_of_capital
        self.is_active = is_active
        self.shape = shape
        self.max_lead_hours = max_lead_hours
        self.max_lag_hours = max_lag_hours

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (sector, name, cost_of_capital, is_active, shape, max_lead_hours, max_lag_hours) = tup

        obj = cls(scenario, sector=sector, name=name, cost_of_capital=cost_of_capital, is_active=is_active,
                  shape=shape, max_lead_hours=max_lead_hours, max_lag_hours=max_lag_hours)

        return obj

class DemandTechs(DataObject):
    _instances_by_key = {}
    _key_col = "name"

    def __init__(self, scenario, linked=None, stock_link_ratio=None, subsector=None, name=None, min_lifetime=None,
                 max_lifetime=None, source=None, additional_description=None, demand_tech_unit_type=None,
                 unit=None, time_unit=None, cost_of_capital=None, stock_decay_function=None,
                 mean_lifetime=None, lifetime_variance=None, shape=None, max_lead_hours=None,
                 max_lag_hours=None):

        DataObject.__init__(self, scenario, key=name, data_table_name="")
        DemandTechs._instances_by_key[self._key] = self

        self.linked = linked
        self.stock_link_ratio = stock_link_ratio
        self.subsector = subsector
        self.name = name
        self.min_lifetime = min_lifetime
        self.max_lifetime = max_lifetime
        self.source = source
        self.additional_description = additional_description
        self.demand_tech_unit_type = demand_tech_unit_type
        self.unit = unit
        self.time_unit = time_unit
        self.cost_of_capital = cost_of_capital
        self.stock_decay_function = stock_decay_function
        self.mean_lifetime = mean_lifetime
        self.lifetime_variance = lifetime_variance
        self.shape = shape
        self.max_lead_hours = max_lead_hours
        self.max_lag_hours = max_lag_hours

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (linked, stock_link_ratio, subsector, name, min_lifetime, max_lifetime, source,
         additional_description, demand_tech_unit_type, unit, time_unit, cost_of_capital,
         stock_decay_function, mean_lifetime, lifetime_variance, shape, max_lead_hours,
         max_lag_hours) = tup

        obj = cls(scenario, linked=linked, stock_link_ratio=stock_link_ratio, subsector=subsector, name=name,
                  min_lifetime=min_lifetime, max_lifetime=max_lifetime, source=source,
                  additional_description=additional_description,
                  demand_tech_unit_type=demand_tech_unit_type, unit=unit, time_unit=time_unit,
                  cost_of_capital=cost_of_capital, stock_decay_function=stock_decay_function,
                  mean_lifetime=mean_lifetime, lifetime_variance=lifetime_variance, shape=shape,
                  max_lead_hours=max_lead_hours, max_lag_hours=max_lag_hours)

        return obj

class DemandTechsAuxEfficiency(DataObject):
    _instances_by_key = {}
    _key_col = "demand_technology"

    def __init__(self, scenario, demand_technology=None, definition=None, reference_tech_id=None, geography=None,
                 other_index_1=None, other_index_2=None, final_energy=None,
                 demand_tech_efficiency_types=None, is_numerator_service=None, numerator_unit=None,
                 denominator_unit=None, interpolation_method=None, extrapolation_method=None,
                 extrapolation_growth=None, age_growth_or_decay_type=None, age_growth_or_decay=None,
                 shape=None):

        DataObject.__init__(self, scenario, key=demand_technology, data_table_name="DemandTechsAuxEfficiencyData")
        DemandTechsAuxEfficiency._instances_by_key[self._key] = self

        self.demand_technology = demand_technology
        self.definition = definition
        self.reference_tech_id = reference_tech_id
        self.geography = geography
        self.other_index_1 = other_index_1
        self.other_index_2 = other_index_2
        self.final_energy = final_energy
        self.demand_tech_efficiency_types = demand_tech_efficiency_types
        self.is_numerator_service = is_numerator_service
        self.numerator_unit = numerator_unit
        self.denominator_unit = denominator_unit
        self.interpolation_method = interpolation_method
        self.extrapolation_method = extrapolation_method
        self.extrapolation_growth = extrapolation_growth
        self.age_growth_or_decay_type = age_growth_or_decay_type
        self.age_growth_or_decay = age_growth_or_decay
        self.shape = shape

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (demand_technology, definition, reference_tech_id, geography, other_index_1, other_index_2,
         final_energy, demand_tech_efficiency_types, is_numerator_service, numerator_unit,
         denominator_unit, interpolation_method, extrapolation_method, extrapolation_growth,
         age_growth_or_decay_type, age_growth_or_decay, shape) = tup

        obj = cls(scenario, demand_technology=demand_technology, definition=definition,
                  reference_tech_id=reference_tech_id, geography=geography, other_index_1=other_index_1,
                  other_index_2=other_index_2, final_energy=final_energy,
                  demand_tech_efficiency_types=demand_tech_efficiency_types,
                  is_numerator_service=is_numerator_service, numerator_unit=numerator_unit,
                  denominator_unit=denominator_unit, interpolation_method=interpolation_method,
                  extrapolation_method=extrapolation_method, extrapolation_growth=extrapolation_growth,
                  age_growth_or_decay_type=age_growth_or_decay_type,
                  age_growth_or_decay=age_growth_or_decay, shape=shape)

        return obj

class DemandTechsCapitalCost(DataObject):
    _instances_by_key = {}
    _key_col = "demand_technology"

    def __init__(self, scenario, demand_technology=None, definition=None, reference_tech_id=None, geography=None,
                 other_index_1=None, other_index_2=None, currency=None, currency_year_id=None,
                 is_levelized=None, interpolation_method=None, extrapolation_method=None,
                 extrapolation_growth=None, reference_tech_operation=None):

        DataObject.__init__(self, scenario, key=demand_technology, data_table_name="")
        DemandTechsCapitalCost._instances_by_key[self._key] = self

        self.demand_technology = demand_technology
        self.definition = definition
        self.reference_tech_id = reference_tech_id
        self.geography = geography
        self.other_index_1 = other_index_1
        self.other_index_2 = other_index_2
        self.currency = currency
        self.currency_year_id = currency_year_id
        self.is_levelized = is_levelized
        self.interpolation_method = interpolation_method
        self.extrapolation_method = extrapolation_method
        self.extrapolation_growth = extrapolation_growth
        self.reference_tech_operation = reference_tech_operation

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (demand_technology, definition, reference_tech_id, geography, other_index_1, other_index_2,
         currency, currency_year_id, is_levelized, interpolation_method, extrapolation_method,
         extrapolation_growth, reference_tech_operation) = tup

        obj = cls(scenario, demand_technology=demand_technology, definition=definition,
                  reference_tech_id=reference_tech_id, geography=geography, other_index_1=other_index_1,
                  other_index_2=other_index_2, currency=currency, currency_year_id=currency_year_id,
                  is_levelized=is_levelized, interpolation_method=interpolation_method,
                  extrapolation_method=extrapolation_method, extrapolation_growth=extrapolation_growth,
                  reference_tech_operation=reference_tech_operation)

        return obj

class DemandTechsFixedMaintenanceCost(DataObject):
    _instances_by_key = {}
    _key_col = "demand_technology"

    def __init__(self, scenario, demand_technology=None, definition=None, reference_tech_id=None, geography=None,
                 other_index_1=None, other_index_2=None, currency=None, currency_year_id=None,
                 interpolation_method=None, extrapolation_method=None, extrapolation_growth=None,
                 age_growth_or_decay_type=None, age_growth_or_decay=None, additional_description=None):

        DataObject.__init__(self, scenario, key=demand_technology, data_table_name="DemandTechsFixedMaintenanceCostData")
        DemandTechsFixedMaintenanceCost._instances_by_key[self._key] = self

        self.demand_technology = demand_technology
        self.definition = definition
        self.reference_tech_id = reference_tech_id
        self.geography = geography
        self.other_index_1 = other_index_1
        self.other_index_2 = other_index_2
        self.currency = currency
        self.currency_year_id = currency_year_id
        self.interpolation_method = interpolation_method
        self.extrapolation_method = extrapolation_method
        self.extrapolation_growth = extrapolation_growth
        self.age_growth_or_decay_type = age_growth_or_decay_type
        self.age_growth_or_decay = age_growth_or_decay
        self.additional_description = additional_description

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (demand_technology, definition, reference_tech_id, geography, other_index_1, other_index_2,
         currency, currency_year_id, interpolation_method, extrapolation_method,
         extrapolation_growth, age_growth_or_decay_type, age_growth_or_decay,
         additional_description) = tup

        obj = cls(scenario, demand_technology=demand_technology, definition=definition,
                  reference_tech_id=reference_tech_id, geography=geography, other_index_1=other_index_1,
                  other_index_2=other_index_2, currency=currency, currency_year_id=currency_year_id,
                  interpolation_method=interpolation_method, extrapolation_method=extrapolation_method,
                  extrapolation_growth=extrapolation_growth,
                  age_growth_or_decay_type=age_growth_or_decay_type,
                  age_growth_or_decay=age_growth_or_decay, additional_description=additional_description)

        return obj

class DemandTechsFuelSwitchCost(DataObject):
    _instances_by_key = {}
    _key_col = "demand_technology"

    def __init__(self, scenario, demand_technology=None, definition=None, reference_tech_id=None, geography=None,
                 other_index_1=None, other_index_2=None, currency=None, currency_year_id=None,
                 is_levelized=None, interpolation_method=None, extrapolation_method=None,
                 extrapolation_growth=None):

        DataObject.__init__(self, scenario, key=demand_technology, data_table_name="DemandTechsFuelSwitchCostData")
        DemandTechsFuelSwitchCost._instances_by_key[self._key] = self

        self.demand_technology = demand_technology
        self.definition = definition
        self.reference_tech_id = reference_tech_id
        self.geography = geography
        self.other_index_1 = other_index_1
        self.other_index_2 = other_index_2
        self.currency = currency
        self.currency_year_id = currency_year_id
        self.is_levelized = is_levelized
        self.interpolation_method = interpolation_method
        self.extrapolation_method = extrapolation_method
        self.extrapolation_growth = extrapolation_growth

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (demand_technology, definition, reference_tech_id, geography, other_index_1, other_index_2,
         currency, currency_year_id, is_levelized, interpolation_method, extrapolation_method,
         extrapolation_growth) = tup

        obj = cls(scenario, demand_technology=demand_technology, definition=definition,
                  reference_tech_id=reference_tech_id, geography=geography, other_index_1=other_index_1,
                  other_index_2=other_index_2, currency=currency, currency_year_id=currency_year_id,
                  is_levelized=is_levelized, interpolation_method=interpolation_method,
                  extrapolation_method=extrapolation_method, extrapolation_growth=extrapolation_growth)

        return obj

class DemandTechsInstallationCost(DataObject):
    _instances_by_key = {}
    _key_col = "demand_technology"

    def __init__(self, scenario, demand_technology=None, definition=None, reference_tech_id=None, geography=None,
                 other_index_1=None, other_index_2=None, currency=None, currency_year_id=None,
                 is_levelized=None, interpolation_method=None, extrapolation_method=None,
                 extrapolation_growth=None):

        DataObject.__init__(self, scenario, key=demand_technology, data_table_name="")
        DemandTechsInstallationCost._instances_by_key[self._key] = self

        self.demand_technology = demand_technology
        self.definition = definition
        self.reference_tech_id = reference_tech_id
        self.geography = geography
        self.other_index_1 = other_index_1
        self.other_index_2 = other_index_2
        self.currency = currency
        self.currency_year_id = currency_year_id
        self.is_levelized = is_levelized
        self.interpolation_method = interpolation_method
        self.extrapolation_method = extrapolation_method
        self.extrapolation_growth = extrapolation_growth

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (demand_technology, definition, reference_tech_id, geography, other_index_1, other_index_2,
         currency, currency_year_id, is_levelized, interpolation_method, extrapolation_method,
         extrapolation_growth) = tup

        obj = cls(scenario, demand_technology=demand_technology, definition=definition,
                  reference_tech_id=reference_tech_id, geography=geography, other_index_1=other_index_1,
                  other_index_2=other_index_2, currency=currency, currency_year_id=currency_year_id,
                  is_levelized=is_levelized, interpolation_method=interpolation_method,
                  extrapolation_method=extrapolation_method, extrapolation_growth=extrapolation_growth)

        return obj

class DemandTechsMainEfficiency(DataObject):
    _instances_by_key = {}
    _key_col = "demand_technology"

    def __init__(self, scenario, demand_technology=None, definition=None, reference_tech_id=None, geography=None,
                 other_index_1=None, other_index_2=None, final_energy=None, utility_factor=None,
                 is_numerator_service=None, numerator_unit=None, denominator_unit=None,
                 interpolation_method=None, extrapolation_method=None, extrapolation_growth=None,
                 age_growth_or_decay_type=None, age_growth_or_decay=None, geography_map_key=None):

        DataObject.__init__(self, scenario, key=demand_technology, data_table_name="DemandTechsMainEfficiencyData")
        DemandTechsMainEfficiency._instances_by_key[self._key] = self

        self.demand_technology = demand_technology
        self.definition = definition
        self.reference_tech_id = reference_tech_id
        self.geography = geography
        self.other_index_1 = other_index_1
        self.other_index_2 = other_index_2
        self.final_energy = final_energy
        self.utility_factor = utility_factor
        self.is_numerator_service = is_numerator_service
        self.numerator_unit = numerator_unit
        self.denominator_unit = denominator_unit
        self.interpolation_method = interpolation_method
        self.extrapolation_method = extrapolation_method
        self.extrapolation_growth = extrapolation_growth
        self.age_growth_or_decay_type = age_growth_or_decay_type
        self.age_growth_or_decay = age_growth_or_decay
        self.geography_map_key = geography_map_key

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (demand_technology, definition, reference_tech_id, geography, other_index_1, other_index_2,
         final_energy, utility_factor, is_numerator_service, numerator_unit, denominator_unit,
         interpolation_method, extrapolation_method, extrapolation_growth,
         age_growth_or_decay_type, age_growth_or_decay, geography_map_key) = tup

        obj = cls(scenario, demand_technology=demand_technology, definition=definition,
                  reference_tech_id=reference_tech_id, geography=geography, other_index_1=other_index_1,
                  other_index_2=other_index_2, final_energy=final_energy, utility_factor=utility_factor,
                  is_numerator_service=is_numerator_service, numerator_unit=numerator_unit,
                  denominator_unit=denominator_unit, interpolation_method=interpolation_method,
                  extrapolation_method=extrapolation_method, extrapolation_growth=extrapolation_growth,
                  age_growth_or_decay_type=age_growth_or_decay_type,
                  age_growth_or_decay=age_growth_or_decay, geography_map_key=geography_map_key)

        return obj

class DemandTechsParasiticEnergy(DataObject):
    _instances_by_key = {}
    _key_col = "demand_technology"

    def __init__(self, scenario, demand_technology=None, definition=None, reference_tech_id=None, geography=None,
                 other_index_1=None, other_index_2=None, energy_unit=None, time_unit=None,
                 interpolation_method=None, extrapolation_method=None, extrapolation_growth=None,
                 age_growth_or_decay_type=None, age_growth_or_decay=None):

        DataObject.__init__(self, scenario, key=demand_technology, data_table_name="DemandTechsParasiticEnergyData")
        DemandTechsParasiticEnergy._instances_by_key[self._key] = self

        self.demand_technology = demand_technology
        self.definition = definition
        self.reference_tech_id = reference_tech_id
        self.geography = geography
        self.other_index_1 = other_index_1
        self.other_index_2 = other_index_2
        self.energy_unit = energy_unit
        self.time_unit = time_unit
        self.interpolation_method = interpolation_method
        self.extrapolation_method = extrapolation_method
        self.extrapolation_growth = extrapolation_growth
        self.age_growth_or_decay_type = age_growth_or_decay_type
        self.age_growth_or_decay = age_growth_or_decay

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (demand_technology, definition, reference_tech_id, geography, other_index_1, other_index_2,
         energy_unit, time_unit, interpolation_method, extrapolation_method, extrapolation_growth,
         age_growth_or_decay_type, age_growth_or_decay) = tup

        obj = cls(scenario, demand_technology=demand_technology, definition=definition,
                  reference_tech_id=reference_tech_id, geography=geography, other_index_1=other_index_1,
                  other_index_2=other_index_2, energy_unit=energy_unit, time_unit=time_unit,
                  interpolation_method=interpolation_method, extrapolation_method=extrapolation_method,
                  extrapolation_growth=extrapolation_growth,
                  age_growth_or_decay_type=age_growth_or_decay_type,
                  age_growth_or_decay=age_growth_or_decay)

        return obj

class DemandTechsServiceDemandModifier(DataObject):
    _instances_by_key = {}
    _key_col = "demand_technology"

    def __init__(self, scenario, demand_technology=None, geography=None, other_index_1=None, other_index_2=None,
                 interpolation_method=None, extrapolation_method=None, extrapolation_growth=None,
                 age_growth_or_decay_type=None, age_growth_or_decay=None):

        DataObject.__init__(self, scenario, key=demand_technology, data_table_name="DemandTechsServiceDemandModifierData")
        DemandTechsServiceDemandModifier._instances_by_key[self._key] = self

        self.demand_technology = demand_technology
        self.geography = geography
        self.other_index_1 = other_index_1
        self.other_index_2 = other_index_2
        self.interpolation_method = interpolation_method
        self.extrapolation_method = extrapolation_method
        self.extrapolation_growth = extrapolation_growth
        self.age_growth_or_decay_type = age_growth_or_decay_type
        self.age_growth_or_decay = age_growth_or_decay

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (demand_technology, geography, other_index_1, other_index_2, interpolation_method,
         extrapolation_method, extrapolation_growth, age_growth_or_decay_type, age_growth_or_decay) = tup

        obj = cls(scenario, demand_technology=demand_technology, geography=geography, other_index_1=other_index_1,
                  other_index_2=other_index_2, interpolation_method=interpolation_method,
                  extrapolation_method=extrapolation_method, extrapolation_growth=extrapolation_growth,
                  age_growth_or_decay_type=age_growth_or_decay_type,
                  age_growth_or_decay=age_growth_or_decay)

        return obj

class DemandTechsServiceLink(DataObject):
    _instances_by_key = {}
    _key_col = "demand_technology"

    def __init__(self, scenario, id=None, service_link=None, demand_technology=None, definition=None, reference_id=None,
                 geography=None, other_index_1=None, other_index_2=None, interpolation_method=None,
                 extrapolation_method=None, extrapolation_growth=None, age_growth_or_decay_type=None,
                 age_growth_or_decay=None):

        DataObject.__init__(self, scenario, key=demand_technology, data_table_name="DemandTechsServiceLinkData")
        DemandTechsServiceLink._instances_by_key[self._key] = self

        self.id = id
        self.service_link = service_link
        self.demand_technology = demand_technology
        self.definition = definition
        self.reference_id = reference_id
        self.geography = geography
        self.other_index_1 = other_index_1
        self.other_index_2 = other_index_2
        self.interpolation_method = interpolation_method
        self.extrapolation_method = extrapolation_method
        self.extrapolation_growth = extrapolation_growth
        self.age_growth_or_decay_type = age_growth_or_decay_type
        self.age_growth_or_decay = age_growth_or_decay

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (id, service_link, demand_technology, definition, reference_id, geography, other_index_1,
         other_index_2, interpolation_method, extrapolation_method, extrapolation_growth,
         age_growth_or_decay_type, age_growth_or_decay) = tup

        obj = cls(scenario, id=id, service_link=service_link, demand_technology=demand_technology,
                  definition=definition, reference_id=reference_id, geography=geography,
                  other_index_1=other_index_1, other_index_2=other_index_2,
                  interpolation_method=interpolation_method, extrapolation_method=extrapolation_method,
                  extrapolation_growth=extrapolation_growth,
                  age_growth_or_decay_type=age_growth_or_decay_type,
                  age_growth_or_decay=age_growth_or_decay)

        return obj

class DispatchFeedersAllocation(DataObject):
    _instances_by_key = {}
    _key_col = "name"

    def __init__(self, scenario, name=None, geography=None, geography_map_key=None, input_type=None,
                 interpolation_method=None, extrapolation_method=None):

        DataObject.__init__(self, scenario, key=name, data_table_name="DispatchFeedersAllocationData")
        DispatchFeedersAllocation._instances_by_key[self._key] = self

        self.name = name
        self.geography = geography
        self.geography_map_key = geography_map_key
        self.input_type = input_type
        self.interpolation_method = interpolation_method
        self.extrapolation_method = extrapolation_method

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (name, geography, geography_map_key, input_type, interpolation_method, extrapolation_method) = tup

        obj = cls(scenario, name=name, geography=geography, geography_map_key=geography_map_key,
                  input_type=input_type, interpolation_method=interpolation_method,
                  extrapolation_method=extrapolation_method)

        return obj

class DispatchNodeConfig(DataObject):
    _instances_by_key = {}
    _key_col = "supply_node"

    def __init__(self, scenario, supply_node=None, dispatch_order=None, dispatch_window=None, geography=None):

        DataObject.__init__(self, scenario, key=supply_node, data_table_name="")
        DispatchNodeConfig._instances_by_key[self._key] = self

        self.supply_node = supply_node
        self.dispatch_order = dispatch_order
        self.dispatch_window = dispatch_window
        self.geography = geography

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (supply_node, dispatch_order, dispatch_window, geography) = tup

        obj = cls(scenario, supply_node=supply_node, dispatch_order=dispatch_order, dispatch_window=dispatch_window,
                  geography=geography)

        return obj

class DispatchTransmissionConstraint(DataObject):
    _instances_by_key = {}
    _key_col = "name"

    def __init__(self, scenario, name=None, description=None, geography_description=None, time_zone_id=None,
                 interpolation_method=None, extrapolation_method=None, hurdle_currency_id=None,
                 hurdle_currency_year_id=None, energy_unit=None):

        DataObject.__init__(self, scenario, key=name, data_table_name="DispatchTransmissionConstraintData")
        DispatchTransmissionConstraint._instances_by_key[self._key] = self

        self.name = name
        self.description = description
        self.geography_description = geography_description
        self.time_zone_id = time_zone_id
        self.interpolation_method = interpolation_method
        self.extrapolation_method = extrapolation_method
        self.hurdle_currency_id = hurdle_currency_id
        self.hurdle_currency_year_id = hurdle_currency_year_id
        self.energy_unit = energy_unit

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (name, description, geography_description, time_zone_id, interpolation_method,
         extrapolation_method, hurdle_currency_id, hurdle_currency_year_id, energy_unit) = tup

        obj = cls(scenario, name=name, description=description, geography_description=geography_description,
                  time_zone_id=time_zone_id, interpolation_method=interpolation_method,
                  extrapolation_method=extrapolation_method, hurdle_currency_id=hurdle_currency_id,
                  hurdle_currency_year_id=hurdle_currency_year_id, energy_unit=energy_unit)

        return obj

class DispatchTransmissionHurdleRate(DataObject):
    _instances_by_key = {}
    _key_col = "parent"

    def __init__(self, scenario, id=None, parent=None, gau_from=None, gau_to=None, year=None, month=None, hour=None,
                 day_type=None, value=None, sensitivity=None):

        DataObject.__init__(self, scenario, key=parent, data_table_name="")
        DispatchTransmissionHurdleRate._instances_by_key[self._key] = self

        self.id = id
        self.parent = parent
        self.gau_from = gau_from
        self.gau_to = gau_to
        self.year = year
        self.month = month
        self.hour = hour
        self.day_type = day_type
        self.value = value
        self.sensitivity = sensitivity

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (id, parent, gau_from, gau_to, year, month, hour, day_type, value, sensitivity) = tup

        obj = cls(scenario, id=id, parent=parent, gau_from=gau_from, gau_to=gau_to, year=year, month=month, hour=hour,
                  day_type=day_type, value=value, sensitivity=sensitivity)

        return obj

class FinalEnergy(DataObject):
    _instances_by_key = {}
    _key_col = "name"

    def __init__(self, scenario, name=None, shape=None):

        DataObject.__init__(self, scenario, key=name, data_table_name="")
        FinalEnergy._instances_by_key[self._key] = self

        self.name = name
        self.shape = shape

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (name, shape) = tup

        obj = cls(scenario, name=name, shape=shape)

        return obj

class GreenhouseGases(DataObject):
    _instances_by_key = {}
    _key_col = "name"

    def __init__(self, scenario, name=None, long_name=None):

        DataObject.__init__(self, scenario, key=name, data_table_name="")
        GreenhouseGases._instances_by_key[self._key] = self

        self.name = name
        self.long_name = long_name

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (name, long_name) = tup

        obj = cls(scenario, name=name, long_name=long_name)

        return obj

class ImportCost(DataObject):
    _instances_by_key = {}
    _key_col = "import_node"

    def __init__(self, scenario, import_node=None, source=None, notes=None, geography=None, currency=None,
                 currency_year_id=None, denominator_unit=None, interpolation_method=None,
                 extrapolation_method=None, extrapolation_growth=None, cost_method_id=None):

        DataObject.__init__(self, scenario, key=import_node, data_table_name="ImportCostData")
        ImportCost._instances_by_key[self._key] = self

        self.import_node = import_node
        self.source = source
        self.notes = notes
        self.geography = geography
        self.currency = currency
        self.currency_year_id = currency_year_id
        self.denominator_unit = denominator_unit
        self.interpolation_method = interpolation_method
        self.extrapolation_method = extrapolation_method
        self.extrapolation_growth = extrapolation_growth
        self.cost_method_id = cost_method_id

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (import_node, source, notes, geography, currency, currency_year_id, denominator_unit,
         interpolation_method, extrapolation_method, extrapolation_growth, cost_method_id) = tup

        obj = cls(scenario, import_node=import_node, source=source, notes=notes, geography=geography,
                  currency=currency, currency_year_id=currency_year_id, denominator_unit=denominator_unit,
                  interpolation_method=interpolation_method, extrapolation_method=extrapolation_method,
                  extrapolation_growth=extrapolation_growth, cost_method_id=cost_method_id)

        return obj

class ImportPrimaryCostMethod(DataObject):
    _instances_by_key = {}
    _key_col = "name"

    def __init__(self, scenario, id=None, name=None):

        DataObject.__init__(self, scenario, key=name, data_table_name="")
        ImportPrimaryCostMethod._instances_by_key[self._key] = self

        self.id = id
        self.name = name

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (id, name) = tup

        obj = cls(scenario, id=id, name=name)

        return obj

class IndexLevels(DataObject):
    _instances_by_key = {}
    _key_col = "index_level"

    def __init__(self, scenario, id=None, index_level=None, data_column_name=None):

        DataObject.__init__(self, scenario, key=index_level, data_table_name="")
        IndexLevels._instances_by_key[self._key] = self

        self.id = id
        self.index_level = index_level
        self.data_column_name = data_column_name

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (id, index_level, data_column_name) = tup

        obj = cls(scenario, id=id, index_level=index_level, data_column_name=data_column_name)

        return obj

class OtherIndexesData_copy(DataObject):
    _instances_by_key = {}
    _key_col = "name"

    def __init__(self, scenario, id=None, name=None, other_index=None):

        DataObject.__init__(self, scenario, key=name, data_table_name="")
        OtherIndexesData_copy._instances_by_key[self._key] = self

        self.id = id
        self.name = name
        self.other_index = other_index

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (id, name, other_index) = tup

        obj = cls(scenario, id=id, name=name, other_index=other_index)

        return obj

class PrimaryCost(DataObject):
    _instances_by_key = {}
    _key_col = "primary_node"

    def __init__(self, scenario, primary_node=None, geography=None, other_index_1=None, currency=None,
                 currency_year_id=None, denominator_unit=None, interpolation_method=None,
                 extrapolation_method=None, extrapolation_growth=None, cost_method_id=None):

        DataObject.__init__(self, scenario, key=primary_node, data_table_name="PrimaryCostData")
        PrimaryCost._instances_by_key[self._key] = self

        self.primary_node = primary_node
        self.geography = geography
        self.other_index_1 = other_index_1
        self.currency = currency
        self.currency_year_id = currency_year_id
        self.denominator_unit = denominator_unit
        self.interpolation_method = interpolation_method
        self.extrapolation_method = extrapolation_method
        self.extrapolation_growth = extrapolation_growth
        self.cost_method_id = cost_method_id

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (primary_node, geography, other_index_1, currency, currency_year_id, denominator_unit,
         interpolation_method, extrapolation_method, extrapolation_growth, cost_method_id) = tup

        obj = cls(scenario, primary_node=primary_node, geography=geography, other_index_1=other_index_1,
                  currency=currency, currency_year_id=currency_year_id, denominator_unit=denominator_unit,
                  interpolation_method=interpolation_method, extrapolation_method=extrapolation_method,
                  extrapolation_growth=extrapolation_growth, cost_method_id=cost_method_id)

        return obj

class Shapes(DataObject):
    _instances_by_key = {}
    _key_col = "name"

    def __init__(self, scenario, name=None, shape_type=None, shape_unit_type=None, time_zone_id=None, geography=None,
                 other_index_1=None, other_index_2=None, geography_map_key=None,
                 interpolation_method=None, extrapolation_method=None, input_type=None):

        DataObject.__init__(self, scenario, key=name, data_table_name="")
        Shapes._instances_by_key[self._key] = self

        self.name = name
        self.shape_type = shape_type
        self.shape_unit_type = shape_unit_type
        self.time_zone_id = time_zone_id
        self.geography = geography
        self.other_index_1 = other_index_1
        self.other_index_2 = other_index_2
        self.geography_map_key = geography_map_key
        self.interpolation_method = interpolation_method
        self.extrapolation_method = extrapolation_method
        self.input_type = input_type

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (name, shape_type, shape_unit_type, time_zone_id, geography, other_index_1, other_index_2,
         geography_map_key, interpolation_method, extrapolation_method, input_type) = tup

        obj = cls(scenario, name=name, shape_type=shape_type, shape_unit_type=shape_unit_type,
                  time_zone_id=time_zone_id, geography=geography, other_index_1=other_index_1,
                  other_index_2=other_index_2, geography_map_key=geography_map_key,
                  interpolation_method=interpolation_method, extrapolation_method=extrapolation_method,
                  input_type=input_type)

        return obj

class StorageTechsCapacityCapitalCost(DataObject):
    _instances_by_key = {}
    _key_col = "supply_tech"

    def __init__(self, scenario, supply_tech=None, definition=None, reference_tech=None, currency=None, geography=None,
                 currency_year_id=None, capacity_or_energy_unit=None, is_levelized=None,
                 cost_of_capital=None, interpolation_method=None, extrapolation_method=None,
                 time_unit=None):

        DataObject.__init__(self, scenario, key=supply_tech, data_table_name="")
        StorageTechsCapacityCapitalCost._instances_by_key[self._key] = self

        self.supply_tech = supply_tech
        self.definition = definition
        self.reference_tech = reference_tech
        self.currency = currency
        self.geography = geography
        self.currency_year_id = currency_year_id
        self.capacity_or_energy_unit = capacity_or_energy_unit
        self.is_levelized = is_levelized
        self.cost_of_capital = cost_of_capital
        self.interpolation_method = interpolation_method
        self.extrapolation_method = extrapolation_method
        self.time_unit = time_unit

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (supply_tech, definition, reference_tech, currency, geography, currency_year_id,
         capacity_or_energy_unit, is_levelized, cost_of_capital, interpolation_method,
         extrapolation_method, time_unit) = tup

        obj = cls(scenario, supply_tech=supply_tech, definition=definition, reference_tech=reference_tech,
                  currency=currency, geography=geography, currency_year_id=currency_year_id,
                  capacity_or_energy_unit=capacity_or_energy_unit, is_levelized=is_levelized,
                  cost_of_capital=cost_of_capital, interpolation_method=interpolation_method,
                  extrapolation_method=extrapolation_method, time_unit=time_unit)

        return obj

class StorageTechsEnergyCapitalCost(DataObject):
    _instances_by_key = {}
    _key_col = "supply_tech"

    def __init__(self, scenario, supply_tech=None, definition=None, reference_tech=None, currency=None, geography=None,
                 currency_year_id=None, energy_unit=None, is_levelized=None, cost_of_capital=None,
                 interpolation_method=None, extrapolation_method=None):

        DataObject.__init__(self, scenario, key=supply_tech, data_table_name="")
        StorageTechsEnergyCapitalCost._instances_by_key[self._key] = self

        self.supply_tech = supply_tech
        self.definition = definition
        self.reference_tech = reference_tech
        self.currency = currency
        self.geography = geography
        self.currency_year_id = currency_year_id
        self.energy_unit = energy_unit
        self.is_levelized = is_levelized
        self.cost_of_capital = cost_of_capital
        self.interpolation_method = interpolation_method
        self.extrapolation_method = extrapolation_method

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (supply_tech, definition, reference_tech, currency, geography, currency_year_id,
         energy_unit, is_levelized, cost_of_capital, interpolation_method, extrapolation_method) = tup

        obj = cls(scenario, supply_tech=supply_tech, definition=definition, reference_tech=reference_tech,
                  currency=currency, geography=geography, currency_year_id=currency_year_id,
                  energy_unit=energy_unit, is_levelized=is_levelized, cost_of_capital=cost_of_capital,
                  interpolation_method=interpolation_method, extrapolation_method=extrapolation_method)

        return obj

class SupplyCapacityFactor(DataObject):
    _instances_by_key = {}
    _key_col = "supply_node"

    def __init__(self, scenario, supply_node=None, geography=None, unit=None, interpolation_method=None,
                 extrapolation_method=None, extrapolation_growth=None, age_growth_or_decay_type=None,
                 age_growth_or_decay=None):

        DataObject.__init__(self, scenario, key=supply_node, data_table_name="SupplyCapacityFactorData")
        SupplyCapacityFactor._instances_by_key[self._key] = self

        self.supply_node = supply_node
        self.geography = geography
        self.unit = unit
        self.interpolation_method = interpolation_method
        self.extrapolation_method = extrapolation_method
        self.extrapolation_growth = extrapolation_growth
        self.age_growth_or_decay_type = age_growth_or_decay_type
        self.age_growth_or_decay = age_growth_or_decay

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (supply_node, geography, unit, interpolation_method, extrapolation_method,
         extrapolation_growth, age_growth_or_decay_type, age_growth_or_decay) = tup

        obj = cls(scenario, supply_node=supply_node, geography=geography, unit=unit,
                  interpolation_method=interpolation_method, extrapolation_method=extrapolation_method,
                  extrapolation_growth=extrapolation_growth,
                  age_growth_or_decay_type=age_growth_or_decay_type,
                  age_growth_or_decay=age_growth_or_decay)

        return obj

class SupplyCost(DataObject):
    _instances_by_key = {}
    _key_col = "name"

    def __init__(self, scenario, name=None, source=None, additional_notes=None, supply_node=None, geography=None,
                 supply_cost_type_id=None, currency=None, currency_year_id=None,
                 energy_or_capacity_unit=None, time_unit=None, is_capital_cost=None, cost_of_capital=None,
                 book_life=None, throughput_correlation=None, interpolation_method=None,
                 extrapolation_method=None, extrapolation_growth=None):

        DataObject.__init__(self, scenario, key=name, data_table_name="SupplyCostData")
        SupplyCost._instances_by_key[self._key] = self

        self.name = name
        self.source = source
        self.additional_notes = additional_notes
        self.supply_node = supply_node
        self.geography = geography
        self.supply_cost_type_id = supply_cost_type_id
        self.currency = currency
        self.currency_year_id = currency_year_id
        self.energy_or_capacity_unit = energy_or_capacity_unit
        self.time_unit = time_unit
        self.is_capital_cost = is_capital_cost
        self.cost_of_capital = cost_of_capital
        self.book_life = book_life
        self.throughput_correlation = throughput_correlation
        self.interpolation_method = interpolation_method
        self.extrapolation_method = extrapolation_method
        self.extrapolation_growth = extrapolation_growth

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (name, source, additional_notes, supply_node, geography, supply_cost_type_id, currency,
         currency_year_id, energy_or_capacity_unit, time_unit, is_capital_cost, cost_of_capital,
         book_life, throughput_correlation, interpolation_method, extrapolation_method,
         extrapolation_growth) = tup

        obj = cls(scenario, name=name, source=source, additional_notes=additional_notes, supply_node=supply_node,
                  geography=geography, supply_cost_type_id=supply_cost_type_id, currency=currency,
                  currency_year_id=currency_year_id, energy_or_capacity_unit=energy_or_capacity_unit,
                  time_unit=time_unit, is_capital_cost=is_capital_cost, cost_of_capital=cost_of_capital,
                  book_life=book_life, throughput_correlation=throughput_correlation,
                  interpolation_method=interpolation_method, extrapolation_method=extrapolation_method,
                  extrapolation_growth=extrapolation_growth)

        return obj

class SupplyEfficiency(DataObject):
    _instances_by_key = {}
    _key_col = "name"

    def __init__(self, scenario, name=None, geography=None, source=None, notes=None, input_unit=None, output_unit=None,
                 interpolation_method=None, extrapolation_method=None, extrapolation_growth=None):

        DataObject.__init__(self, scenario, key=name, data_table_name="SupplyEfficiencyData")
        SupplyEfficiency._instances_by_key[self._key] = self

        self.name = name
        self.geography = geography
        self.source = source
        self.notes = notes
        self.input_unit = input_unit
        self.output_unit = output_unit
        self.interpolation_method = interpolation_method
        self.extrapolation_method = extrapolation_method
        self.extrapolation_growth = extrapolation_growth

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (name, geography, source, notes, input_unit, output_unit, interpolation_method,
         extrapolation_method, extrapolation_growth) = tup

        obj = cls(scenario, name=name, geography=geography, source=source, notes=notes, input_unit=input_unit,
                  output_unit=output_unit, interpolation_method=interpolation_method,
                  extrapolation_method=extrapolation_method, extrapolation_growth=extrapolation_growth)

        return obj

class SupplyEmissions(DataObject):
    _instances_by_key = {}
    _key_col = "supply_node"

    def __init__(self, scenario, supply_node=None, geography=None, other_index_1=None, mass_unit=None,
                 denominator_unit=None, interpolation_method=None, extrapolation_method=None,
                 extrapolation_growth=None, source=None, notes=None):

        DataObject.__init__(self, scenario, key=supply_node, data_table_name="SupplyEmissionsData")
        SupplyEmissions._instances_by_key[self._key] = self

        self.supply_node = supply_node
        self.geography = geography
        self.other_index_1 = other_index_1
        self.mass_unit = mass_unit
        self.denominator_unit = denominator_unit
        self.interpolation_method = interpolation_method
        self.extrapolation_method = extrapolation_method
        self.extrapolation_growth = extrapolation_growth
        self.source = source
        self.notes = notes

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (supply_node, geography, other_index_1, mass_unit, denominator_unit, interpolation_method,
         extrapolation_method, extrapolation_growth, source, notes) = tup

        obj = cls(scenario, supply_node=supply_node, geography=geography, other_index_1=other_index_1,
                  mass_unit=mass_unit, denominator_unit=denominator_unit,
                  interpolation_method=interpolation_method, extrapolation_method=extrapolation_method,
                  extrapolation_growth=extrapolation_growth, source=source, notes=notes)

        return obj

class SupplyExport(DataObject):
    _instances_by_key = {}
    _key_col = "supply_node"

    def __init__(self, scenario, supply_node=None, geography=None, other_index_1=None, unit=None,
                 interpolation_method=None, extrapolation_method=None, extrapolation_growth=None):

        DataObject.__init__(self, scenario, key=supply_node, data_table_name="SupplyExportData")
        SupplyExport._instances_by_key[self._key] = self

        self.supply_node = supply_node
        self.geography = geography
        self.other_index_1 = other_index_1
        self.unit = unit
        self.interpolation_method = interpolation_method
        self.extrapolation_method = extrapolation_method
        self.extrapolation_growth = extrapolation_growth

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (supply_node, geography, other_index_1, unit, interpolation_method, extrapolation_method,
         extrapolation_growth) = tup

        obj = cls(scenario, supply_node=supply_node, geography=geography, other_index_1=other_index_1, unit=unit,
                  interpolation_method=interpolation_method, extrapolation_method=extrapolation_method,
                  extrapolation_growth=extrapolation_growth)

        return obj

class SupplyExportMeasures(DataObject):
    _instances_by_key = {}
    _key_col = "name"

    def __init__(self, scenario, supply_node=None, name=None, geography=None, other_index_1=None,
                 interpolation_method=None, extrapolation_method=None, unit=None):

        DataObject.__init__(self, scenario, key=name, data_table_name="SupplyExportMeasuresData")
        SupplyExportMeasures._instances_by_key[self._key] = self

        self.supply_node = supply_node
        self.name = name
        self.geography = geography
        self.other_index_1 = other_index_1
        self.interpolation_method = interpolation_method
        self.extrapolation_method = extrapolation_method
        self.unit = unit

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (supply_node, name, geography, other_index_1, interpolation_method, extrapolation_method,
         unit) = tup

        obj = cls(scenario, supply_node=supply_node, name=name, geography=geography, other_index_1=other_index_1,
                  interpolation_method=interpolation_method, extrapolation_method=extrapolation_method,
                  unit=unit)

        return obj

class SupplyNodes(DataObject):
    _instances_by_key = {}
    _key_col = "name"

    def __init__(self, scenario, name=None, supply_type=None, tradable_geography=None, is_active=None, is_curtailable=None,
                 is_exportable=None, is_flexible=None, residual_supply_node=None, mean_lifetime=None,
                 lifetime_variance=None, max_lifetime=None, min_lifetime=None, stock_decay_function=None,
                 cost_of_capital=None, book_life=None, geography_map_key=None, shape=None,
                 max_lag_hours=None, max_lead_hours=None, enforce_potential_constraint=None,
                 overflow_node=None):

        DataObject.__init__(self, scenario, key=name, data_table_name="")
        SupplyNodes._instances_by_key[self._key] = self

        self.name = name
        self.supply_type = supply_type
        self.tradable_geography = tradable_geography
        self.is_active = is_active
        self.is_curtailable = is_curtailable
        self.is_exportable = is_exportable
        self.is_flexible = is_flexible
        self.residual_supply_node = residual_supply_node
        self.mean_lifetime = mean_lifetime
        self.lifetime_variance = lifetime_variance
        self.max_lifetime = max_lifetime
        self.min_lifetime = min_lifetime
        self.stock_decay_function = stock_decay_function
        self.cost_of_capital = cost_of_capital
        self.book_life = book_life
        self.geography_map_key = geography_map_key
        self.shape = shape
        self.max_lag_hours = max_lag_hours
        self.max_lead_hours = max_lead_hours
        self.enforce_potential_constraint = enforce_potential_constraint
        self.overflow_node = overflow_node

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (name, supply_type, tradable_geography, is_active, is_curtailable, is_exportable,
         is_flexible, residual_supply_node, mean_lifetime, lifetime_variance, max_lifetime,
         min_lifetime, stock_decay_function, cost_of_capital, book_life, geography_map_key, shape,
         max_lag_hours, max_lead_hours, enforce_potential_constraint, overflow_node) = tup

        obj = cls(scenario, name=name, supply_type=supply_type, tradable_geography=tradable_geography,
                  is_active=is_active, is_curtailable=is_curtailable, is_exportable=is_exportable,
                  is_flexible=is_flexible, residual_supply_node=residual_supply_node,
                  mean_lifetime=mean_lifetime, lifetime_variance=lifetime_variance,
                  max_lifetime=max_lifetime, min_lifetime=min_lifetime,
                  stock_decay_function=stock_decay_function, cost_of_capital=cost_of_capital,
                  book_life=book_life, geography_map_key=geography_map_key, shape=shape,
                  max_lag_hours=max_lag_hours, max_lead_hours=max_lead_hours,
                  enforce_potential_constraint=enforce_potential_constraint, overflow_node=overflow_node)

        return obj

class SupplyPotential(DataObject):
    _instances_by_key = {}
    _key_col = "supply_node"

    def __init__(self, scenario, enforce=False, supply_node=None, geography=None, other_index_1=None, unit=None,
                 time_unit=None, interpolation_method=None, extrapolation_growth=None,
                 extrapolation_method=None, geography_map_key=None):

        DataObject.__init__(self, scenario, key=supply_node, data_table_name="SupplyPotentialData")
        SupplyPotential._instances_by_key[self._key] = self

        self.enforce = enforce
        self.supply_node = supply_node
        self.geography = geography
        self.other_index_1 = other_index_1
        self.unit = unit
        self.time_unit = time_unit
        self.interpolation_method = interpolation_method
        self.extrapolation_growth = extrapolation_growth
        self.extrapolation_method = extrapolation_method
        self.geography_map_key = geography_map_key

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (supply_node, geography, other_index_1, unit, time_unit, interpolation_method,
         extrapolation_growth, extrapolation_method, geography_map_key) = tup

        obj = cls(scenario, kwargs.get("enforce", False), supply_node=supply_node, geography=geography,
                  other_index_1=other_index_1, unit=unit, time_unit=time_unit,
                  interpolation_method=interpolation_method, extrapolation_growth=extrapolation_growth,
                  extrapolation_method=extrapolation_method, geography_map_key=geography_map_key)

        return obj

class SupplyPotentialConversion(DataObject):
    _instances_by_key = {}
    _key_col = "supply_node"

    def __init__(self, scenario, supply_node=None, geography=None, other_index_1=None, energy_unit_numerator=None,
                 resource_unit_denominator=None, interpolation_method=None, extrapolation_method=None,
                 extrapolation_growth=None):

        DataObject.__init__(self, scenario, key=supply_node, data_table_name="SupplyPotentialConversionData")
        SupplyPotentialConversion._instances_by_key[self._key] = self

        self.supply_node = supply_node
        self.geography = geography
        self.other_index_1 = other_index_1
        self.energy_unit_numerator = energy_unit_numerator
        self.resource_unit_denominator = resource_unit_denominator
        self.interpolation_method = interpolation_method
        self.extrapolation_method = extrapolation_method
        self.extrapolation_growth = extrapolation_growth

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (supply_node, geography, other_index_1, energy_unit_numerator, resource_unit_denominator,
         interpolation_method, extrapolation_method, extrapolation_growth) = tup

        obj = cls(scenario, supply_node=supply_node, geography=geography, other_index_1=other_index_1,
                  energy_unit_numerator=energy_unit_numerator,
                  resource_unit_denominator=resource_unit_denominator,
                  interpolation_method=interpolation_method, extrapolation_method=extrapolation_method,
                  extrapolation_growth=extrapolation_growth)

        return obj

class SupplySales(DataObject):
    _instances_by_key = {}
    _key_col = "supply_node"

    def __init__(self, scenario, supply_node=None, geography=None, capacity_or_energy_unit=None, time_unit=None,
                 interpolation_method=None, extrapolation_method=None, extrapolation_growth=None,
                 geography_map_key=None):

        DataObject.__init__(self, scenario, key=supply_node, data_table_name="SupplySalesData")
        SupplySales._instances_by_key[self._key] = self

        self.supply_node = supply_node
        self.geography = geography
        self.capacity_or_energy_unit = capacity_or_energy_unit
        self.time_unit = time_unit
        self.interpolation_method = interpolation_method
        self.extrapolation_method = extrapolation_method
        self.extrapolation_growth = extrapolation_growth
        self.geography_map_key = geography_map_key

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (supply_node, geography, capacity_or_energy_unit, time_unit, interpolation_method,
         extrapolation_method, extrapolation_growth, geography_map_key) = tup

        obj = cls(scenario, supply_node=supply_node, geography=geography,
                  capacity_or_energy_unit=capacity_or_energy_unit, time_unit=time_unit,
                  interpolation_method=interpolation_method, extrapolation_method=extrapolation_method,
                  extrapolation_growth=extrapolation_growth, geography_map_key=geography_map_key)

        return obj

class SupplySalesMeasures(DataObject):
    _instances_by_key = {}
    _key_col = "name"

    def __init__(self, scenario, name=None, supply_technology=None, supply_node=None, geography=None, other_index_1=None,
                 interpolation_method=None, extrapolation_method=None, extrapolation_growth=None,
                 geography_map_key=None):

        DataObject.__init__(self, scenario, key=name, data_table_name="SupplySalesMeasuresData")
        SupplySalesMeasures._instances_by_key[self._key] = self

        self.name = name
        self.supply_technology = supply_technology
        self.supply_node = supply_node
        self.geography = geography
        self.other_index_1 = other_index_1
        self.interpolation_method = interpolation_method
        self.extrapolation_method = extrapolation_method
        self.extrapolation_growth = extrapolation_growth
        self.geography_map_key = geography_map_key

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (name, supply_technology, supply_node, geography, other_index_1, interpolation_method,
         extrapolation_method, extrapolation_growth, geography_map_key) = tup

        obj = cls(scenario, name=name, supply_technology=supply_technology, supply_node=supply_node,
                  geography=geography, other_index_1=other_index_1,
                  interpolation_method=interpolation_method, extrapolation_method=extrapolation_method,
                  extrapolation_growth=extrapolation_growth, geography_map_key=geography_map_key)

        return obj

class SupplySalesShare(DataObject):
    _instances_by_key = {}
    _key_col = "supply_node"

    def __init__(self, scenario, supply_node=None, geography=None, interpolation_method=None, extrapolation_method=None,
                 extrapolation_growth=None):

        DataObject.__init__(self, scenario, key=supply_node, data_table_name="SupplySalesShareData")
        SupplySalesShare._instances_by_key[self._key] = self

        self.supply_node = supply_node
        self.geography = geography
        self.interpolation_method = interpolation_method
        self.extrapolation_method = extrapolation_method
        self.extrapolation_growth = extrapolation_growth

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (supply_node, geography, interpolation_method, extrapolation_method, extrapolation_growth) = tup

        obj = cls(scenario, supply_node=supply_node, geography=geography, interpolation_method=interpolation_method,
                  extrapolation_method=extrapolation_method, extrapolation_growth=extrapolation_growth)

        return obj

class SupplySalesShareMeasures(DataObject):
    _instances_by_key = {}
    _key_col = "name"

    def __init__(self, scenario, name=None, supply_node=None, supply_technology=None, replaced_supply_technology=None,
                 geography=None, capacity_or_energy_unit=None, time_unit=None, interpolation_method=None,
                 extrapolation_method=None, extrapolation_growth=None, other_index_1=None):

        DataObject.__init__(self, scenario, key=name, data_table_name="SupplySalesShareMeasuresData")
        SupplySalesShareMeasures._instances_by_key[self._key] = self

        self.name = name
        self.supply_node = supply_node
        self.supply_technology = supply_technology
        self.replaced_supply_technology = replaced_supply_technology
        self.geography = geography
        self.capacity_or_energy_unit = capacity_or_energy_unit
        self.time_unit = time_unit
        self.interpolation_method = interpolation_method
        self.extrapolation_method = extrapolation_method
        self.extrapolation_growth = extrapolation_growth
        self.other_index_1 = other_index_1

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (name, supply_node, supply_technology, replaced_supply_technology, geography,
         capacity_or_energy_unit, time_unit, interpolation_method, extrapolation_method,
         extrapolation_growth, other_index_1) = tup

        obj = cls(scenario, name=name, supply_node=supply_node, supply_technology=supply_technology,
                  replaced_supply_technology=replaced_supply_technology, geography=geography,
                  capacity_or_energy_unit=capacity_or_energy_unit, time_unit=time_unit,
                  interpolation_method=interpolation_method, extrapolation_method=extrapolation_method,
                  extrapolation_growth=extrapolation_growth, other_index_1=other_index_1)

        return obj

class SupplyStock(DataObject):
    _instances_by_key = {}
    _key_col = "supply_node"

    def __init__(self, scenario, supply_node=None, geography=None, capacity_or_energy_unit=None, time_unit=None,
                 interpolation_method=None, extrapolation_method=None, extrapolation_growth=None,
                 geography_map_key=None):

        DataObject.__init__(self, scenario, key=supply_node, data_table_name="SupplyStockData")
        SupplyStock._instances_by_key[self._key] = self

        self.supply_node = supply_node
        self.geography = geography
        self.capacity_or_energy_unit = capacity_or_energy_unit
        self.time_unit = time_unit
        self.interpolation_method = interpolation_method
        self.extrapolation_method = extrapolation_method
        self.extrapolation_growth = extrapolation_growth
        self.geography_map_key = geography_map_key

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (supply_node, geography, capacity_or_energy_unit, time_unit, interpolation_method,
         extrapolation_method, extrapolation_growth, geography_map_key) = tup

        obj = cls(scenario, supply_node=supply_node, geography=geography,
                  capacity_or_energy_unit=capacity_or_energy_unit, time_unit=time_unit,
                  interpolation_method=interpolation_method, extrapolation_method=extrapolation_method,
                  extrapolation_growth=extrapolation_growth, geography_map_key=geography_map_key)

        return obj

class SupplyStockMeasures(DataObject):
    _instances_by_key = {}
    _key_col = "name"

    def __init__(self, scenario, name=None, supply_technology=None, supply_node=None, geography=None, other_index_1=None,
                 capacity_or_energy_unit=None, time_unit=None, interpolation_method=None,
                 extrapolation_method=None, extrapolation_growth=None, geography_map_key=None):

        DataObject.__init__(self, scenario, key=name, data_table_name="SupplyStockMeasuresData")
        SupplyStockMeasures._instances_by_key[self._key] = self

        self.name = name
        self.supply_technology = supply_technology
        self.supply_node = supply_node
        self.geography = geography
        self.other_index_1 = other_index_1
        self.capacity_or_energy_unit = capacity_or_energy_unit
        self.time_unit = time_unit
        self.interpolation_method = interpolation_method
        self.extrapolation_method = extrapolation_method
        self.extrapolation_growth = extrapolation_growth
        self.geography_map_key = geography_map_key

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (name, supply_technology, supply_node, geography, other_index_1, capacity_or_energy_unit,
         time_unit, interpolation_method, extrapolation_method, extrapolation_growth,
         geography_map_key) = tup

        obj = cls(scenario, name=name, supply_technology=supply_technology, supply_node=supply_node,
                  geography=geography, other_index_1=other_index_1,
                  capacity_or_energy_unit=capacity_or_energy_unit, time_unit=time_unit,
                  interpolation_method=interpolation_method, extrapolation_method=extrapolation_method,
                  extrapolation_growth=extrapolation_growth, geography_map_key=geography_map_key)

        return obj

class SupplyTechs(DataObject):
    _instances_by_key = {}
    _key_col = "name"

    def __init__(self, scenario, name=None, supply_node=None, source=None, additional_description=None,
                 stock_decay_function=None, book_life=None, mean_lifetime=None, lifetime_variance=None,
                 min_lifetime=None, max_lifetime=None, discharge_duration=None, cost_of_capital=None,
                 shape=None, max_lag_hours=None, max_lead_hours=None, thermal_capacity_multiplier=None):

        DataObject.__init__(self, scenario, key=name, data_table_name="")
        SupplyTechs._instances_by_key[self._key] = self

        self.name = name
        self.supply_node = supply_node
        self.source = source
        self.additional_description = additional_description
        self.stock_decay_function = stock_decay_function
        self.book_life = book_life
        self.mean_lifetime = mean_lifetime
        self.lifetime_variance = lifetime_variance
        self.min_lifetime = min_lifetime
        self.max_lifetime = max_lifetime
        self.discharge_duration = discharge_duration
        self.cost_of_capital = cost_of_capital
        self.shape = shape
        self.max_lag_hours = max_lag_hours
        self.max_lead_hours = max_lead_hours
        self.thermal_capacity_multiplier = thermal_capacity_multiplier

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (name, supply_node, source, additional_description, stock_decay_function, book_life,
         mean_lifetime, lifetime_variance, min_lifetime, max_lifetime, discharge_duration,
         cost_of_capital, shape, max_lag_hours, max_lead_hours, thermal_capacity_multiplier) = tup

        obj = cls(scenario, name=name, supply_node=supply_node, source=source,
                  additional_description=additional_description, stock_decay_function=stock_decay_function,
                  book_life=book_life, mean_lifetime=mean_lifetime, lifetime_variance=lifetime_variance,
                  min_lifetime=min_lifetime, max_lifetime=max_lifetime,
                  discharge_duration=discharge_duration, cost_of_capital=cost_of_capital, shape=shape,
                  max_lag_hours=max_lag_hours, max_lead_hours=max_lead_hours,
                  thermal_capacity_multiplier=thermal_capacity_multiplier)

        return obj

class SupplyTechsCO2Capture(DataObject):
    _instances_by_key = {}
    _key_col = "supply_tech"

    def __init__(self, scenario, supply_tech=None, definition=None, geography=None, reference_tech_id=None,
                 interpolation_method=None, extrapolation_method=None, extrapolation_growth=None,
                 age_growth_or_decay_type=None, age_growth_or_decay=None):

        DataObject.__init__(self, scenario, key=supply_tech, data_table_name="SupplyTechsCO2CaptureData")
        SupplyTechsCO2Capture._instances_by_key[self._key] = self

        self.supply_tech = supply_tech
        self.definition = definition
        self.geography = geography
        self.reference_tech_id = reference_tech_id
        self.interpolation_method = interpolation_method
        self.extrapolation_method = extrapolation_method
        self.extrapolation_growth = extrapolation_growth
        self.age_growth_or_decay_type = age_growth_or_decay_type
        self.age_growth_or_decay = age_growth_or_decay

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (supply_tech, definition, geography, reference_tech_id, interpolation_method,
         extrapolation_method, extrapolation_growth, age_growth_or_decay_type, age_growth_or_decay) = tup

        obj = cls(scenario, supply_tech=supply_tech, definition=definition, geography=geography,
                  reference_tech_id=reference_tech_id, interpolation_method=interpolation_method,
                  extrapolation_method=extrapolation_method, extrapolation_growth=extrapolation_growth,
                  age_growth_or_decay_type=age_growth_or_decay_type,
                  age_growth_or_decay=age_growth_or_decay)

        return obj

class SupplyTechsCapacityFactor(DataObject):
    _instances_by_key = {}
    _key_col = "supply_tech"

    def __init__(self, scenario, supply_tech=None, geography=None, reference_tech_id=None, definition=None,
                 interpolation_method=None, extrapolation_method=None, extrapolation_growth=None,
                 age_growth_or_decay_type=None, age_growth_or_decay=None):

        DataObject.__init__(self, scenario, key=supply_tech, data_table_name="SupplyTechsCapacityFactorData")
        SupplyTechsCapacityFactor._instances_by_key[self._key] = self

        self.supply_tech = supply_tech
        self.geography = geography
        self.reference_tech_id = reference_tech_id
        self.definition = definition
        self.interpolation_method = interpolation_method
        self.extrapolation_method = extrapolation_method
        self.extrapolation_growth = extrapolation_growth
        self.age_growth_or_decay_type = age_growth_or_decay_type
        self.age_growth_or_decay = age_growth_or_decay

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (supply_tech, geography, reference_tech_id, definition, interpolation_method,
         extrapolation_method, extrapolation_growth, age_growth_or_decay_type, age_growth_or_decay) = tup

        obj = cls(scenario, supply_tech=supply_tech, geography=geography, reference_tech_id=reference_tech_id,
                  definition=definition, interpolation_method=interpolation_method,
                  extrapolation_method=extrapolation_method, extrapolation_growth=extrapolation_growth,
                  age_growth_or_decay_type=age_growth_or_decay_type,
                  age_growth_or_decay=age_growth_or_decay)

        return obj

class SupplyTechsCapitalCost(DataObject):
    _instances_by_key = {}
    _key_col = "supply_tech"

    def __init__(self, scenario, supply_tech=None, definition=None, reference_tech_id=None, geography=None, currency=None,
                 currency_year_id=None, capacity_or_energy_unit=None, time_unit=None, is_levelized=None,
                 interpolation_method=None, extrapolation_method=None, extrapolation_growth=None,
                 source=None, notes=None, geography_map_key=None):

        DataObject.__init__(self, scenario, key=supply_tech, data_table_name="")
        SupplyTechsCapitalCost._instances_by_key[self._key] = self

        self.supply_tech = supply_tech
        self.definition = definition
        self.reference_tech_id = reference_tech_id
        self.geography = geography
        self.currency = currency
        self.currency_year_id = currency_year_id
        self.capacity_or_energy_unit = capacity_or_energy_unit
        self.time_unit = time_unit
        self.is_levelized = is_levelized
        self.interpolation_method = interpolation_method
        self.extrapolation_method = extrapolation_method
        self.extrapolation_growth = extrapolation_growth
        self.source = source
        self.notes = notes
        self.geography_map_key = geography_map_key

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (supply_tech, definition, reference_tech_id, geography, currency, currency_year_id,
         capacity_or_energy_unit, time_unit, is_levelized, interpolation_method,
         extrapolation_method, extrapolation_growth, source, notes, geography_map_key) = tup

        obj = cls(scenario, supply_tech=supply_tech, definition=definition, reference_tech_id=reference_tech_id,
                  geography=geography, currency=currency, currency_year_id=currency_year_id,
                  capacity_or_energy_unit=capacity_or_energy_unit, time_unit=time_unit,
                  is_levelized=is_levelized, interpolation_method=interpolation_method,
                  extrapolation_method=extrapolation_method, extrapolation_growth=extrapolation_growth,
                  source=source, notes=notes, geography_map_key=geography_map_key)

        return obj

class SupplyTechsEfficiency(DataObject):
    _instances_by_key = {}
    _key_col = "supply_tech"

    def __init__(self, scenario, supply_tech=None, geography=None, definition=None, reference_tech=None, input_unit=None,
                 output_unit=None, interpolation_method=None, extrapolation_method=None,
                 extrapolation_growth=None, age_growth_or_decay_type=None, age_growth_or_decay=None,
                 source=None, notes=None):

        DataObject.__init__(self, scenario, key=supply_tech, data_table_name="SupplyTechsEfficiencyData")
        SupplyTechsEfficiency._instances_by_key[self._key] = self

        self.supply_tech = supply_tech
        self.geography = geography
        self.definition = definition
        self.reference_tech = reference_tech
        self.input_unit = input_unit
        self.output_unit = output_unit
        self.interpolation_method = interpolation_method
        self.extrapolation_method = extrapolation_method
        self.extrapolation_growth = extrapolation_growth
        self.age_growth_or_decay_type = age_growth_or_decay_type
        self.age_growth_or_decay = age_growth_or_decay
        self.source = source
        self.notes = notes

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (supply_tech, geography, definition, reference_tech, input_unit, output_unit,
         interpolation_method, extrapolation_method, extrapolation_growth,
         age_growth_or_decay_type, age_growth_or_decay, source, notes) = tup

        obj = cls(scenario, supply_tech=supply_tech, geography=geography, definition=definition,
                  reference_tech=reference_tech, input_unit=input_unit, output_unit=output_unit,
                  interpolation_method=interpolation_method, extrapolation_method=extrapolation_method,
                  extrapolation_growth=extrapolation_growth,
                  age_growth_or_decay_type=age_growth_or_decay_type,
                  age_growth_or_decay=age_growth_or_decay, source=source, notes=notes)

        return obj

class SupplyTechsFixedMaintenanceCost(DataObject):
    _instances_by_key = {}
    _key_col = "supply_tech"

    def __init__(self, scenario, supply_tech=None, definition=None, reference_tech_id=None, geography=None, currency=None,
                 currency_year_id=None, capacity_or_energy_unit=None, time_unit=None,
                 interpolation_method=None, extrapolation_method=None, extrapolation_growth=None,
                 age_growth_or_decay_type=None, age_growth_or_decay=None, source=None, notes=None):

        DataObject.__init__(self, scenario, key=supply_tech, data_table_name="SupplyTechsFixedMaintenanceCostData")
        SupplyTechsFixedMaintenanceCost._instances_by_key[self._key] = self

        self.supply_tech = supply_tech
        self.definition = definition
        self.reference_tech_id = reference_tech_id
        self.geography = geography
        self.currency = currency
        self.currency_year_id = currency_year_id
        self.capacity_or_energy_unit = capacity_or_energy_unit
        self.time_unit = time_unit
        self.interpolation_method = interpolation_method
        self.extrapolation_method = extrapolation_method
        self.extrapolation_growth = extrapolation_growth
        self.age_growth_or_decay_type = age_growth_or_decay_type
        self.age_growth_or_decay = age_growth_or_decay
        self.source = source
        self.notes = notes

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (supply_tech, definition, reference_tech_id, geography, currency, currency_year_id,
         capacity_or_energy_unit, time_unit, interpolation_method, extrapolation_method,
         extrapolation_growth, age_growth_or_decay_type, age_growth_or_decay, source, notes) = tup

        obj = cls(scenario, supply_tech=supply_tech, definition=definition, reference_tech_id=reference_tech_id,
                  geography=geography, currency=currency, currency_year_id=currency_year_id,
                  capacity_or_energy_unit=capacity_or_energy_unit, time_unit=time_unit,
                  interpolation_method=interpolation_method, extrapolation_method=extrapolation_method,
                  extrapolation_growth=extrapolation_growth,
                  age_growth_or_decay_type=age_growth_or_decay_type,
                  age_growth_or_decay=age_growth_or_decay, source=source, notes=notes)

        return obj

class SupplyTechsInstallationCost(DataObject):
    _instances_by_key = {}
    _key_col = "supply_tech"

    def __init__(self, scenario, supply_tech=None, definition=None, geography=None, reference_tech_id=None, currency=None,
                 currency_year_id=None, capacity_or_energy_unit=None, time_unit=None, is_levelized=None,
                 interpolation_method=None, extrapolation_method=None, extrapolation_growth=None,
                 source=None, notes=None):

        DataObject.__init__(self, scenario, key=supply_tech, data_table_name="")
        SupplyTechsInstallationCost._instances_by_key[self._key] = self

        self.supply_tech = supply_tech
        self.definition = definition
        self.geography = geography
        self.reference_tech_id = reference_tech_id
        self.currency = currency
        self.currency_year_id = currency_year_id
        self.capacity_or_energy_unit = capacity_or_energy_unit
        self.time_unit = time_unit
        self.is_levelized = is_levelized
        self.interpolation_method = interpolation_method
        self.extrapolation_method = extrapolation_method
        self.extrapolation_growth = extrapolation_growth
        self.source = source
        self.notes = notes

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (supply_tech, definition, geography, reference_tech_id, currency, currency_year_id,
         capacity_or_energy_unit, time_unit, is_levelized, interpolation_method,
         extrapolation_method, extrapolation_growth, source, notes) = tup

        obj = cls(scenario, supply_tech=supply_tech, definition=definition, geography=geography,
                  reference_tech_id=reference_tech_id, currency=currency,
                  currency_year_id=currency_year_id, capacity_or_energy_unit=capacity_or_energy_unit,
                  time_unit=time_unit, is_levelized=is_levelized,
                  interpolation_method=interpolation_method, extrapolation_method=extrapolation_method,
                  extrapolation_growth=extrapolation_growth, source=source, notes=notes)

        return obj

class SupplyTechsVariableMaintenanceCost(DataObject):
    _instances_by_key = {}
    _key_col = "supply_tech"

    def __init__(self, scenario, supply_tech=None, definition=None, reference_tech_id=None, currency=None, geography=None,
                 currency_year_id=None, energy_unit=None, interpolation_method=None,
                 extrapolation_method=None, extrapolation_growth=None, age_growth_or_decay_type=None,
                 age_growth_or_decay=None, source=None, notes=None):

        DataObject.__init__(self, scenario, key=supply_tech, data_table_name="SupplyTechsVariableMaintenanceCostData")
        SupplyTechsVariableMaintenanceCost._instances_by_key[self._key] = self

        self.supply_tech = supply_tech
        self.definition = definition
        self.reference_tech_id = reference_tech_id
        self.currency = currency
        self.geography = geography
        self.currency_year_id = currency_year_id
        self.energy_unit = energy_unit
        self.interpolation_method = interpolation_method
        self.extrapolation_method = extrapolation_method
        self.extrapolation_growth = extrapolation_growth
        self.age_growth_or_decay_type = age_growth_or_decay_type
        self.age_growth_or_decay = age_growth_or_decay
        self.source = source
        self.notes = notes

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (supply_tech, definition, reference_tech_id, currency, geography, currency_year_id,
         energy_unit, interpolation_method, extrapolation_method, extrapolation_growth,
         age_growth_or_decay_type, age_growth_or_decay, source, notes) = tup

        obj = cls(scenario, supply_tech=supply_tech, definition=definition, reference_tech_id=reference_tech_id,
                  currency=currency, geography=geography, currency_year_id=currency_year_id,
                  energy_unit=energy_unit, interpolation_method=interpolation_method,
                  extrapolation_method=extrapolation_method, extrapolation_growth=extrapolation_growth,
                  age_growth_or_decay_type=age_growth_or_decay_type,
                  age_growth_or_decay=age_growth_or_decay, source=source, notes=notes)

        return obj

class TimeZones(DataObject):
    _instances_by_key = {}
    _key_col = "name"

    def __init__(self, scenario, id=None, name=None, utc_shift=None):

        DataObject.__init__(self, scenario, key=name, data_table_name="")
        TimeZones._instances_by_key[self._key] = self

        self.id = id
        self.name = name
        self.utc_shift = utc_shift

    @classmethod
    def from_tuple(cls, scenario, tup, **kwargs):    
        (id, name, utc_shift) = tup

        obj = cls(scenario, id=id, name=name, utc_shift=utc_shift)

        return obj

