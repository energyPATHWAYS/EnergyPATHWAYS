#
# This is a generated file. Manual edits may be lost!
#
import sys
from energyPATHWAYS.data_object import DataObject # superclass of generated classes

_Module = sys.modules[__name__]  # get ref to our own module object

class BlendNodeBlendMeasures(DataObject):
    _instances_by_key = {}
    _table_name = "BlendNodeBlendMeasures"
    _key_col = "name"
    _cols = ["blend_node", "extrapolation_growth", "extrapolation_method", "geography",
             "interpolation_method", "name", "notes", "other_index_1", "source", "supply_node"]
    _df_cols = ["gau", "demand_sector", "value", "year"]
    _df_filters = []
    _data_table_name = None

    def __init__(self, name, scenario):
        DataObject.__init__(self, name, scenario)

        BlendNodeBlendMeasures._instances_by_key[self._key] = self

        self.blend_node = None
        self.extrapolation_growth = None
        self.extrapolation_method = None
        self.geography = None
        self.interpolation_method = None
        self.name = None
        self.notes = None
        self.other_index_1 = None
        self.source = None
        self.supply_node = None

    def set_args(self, scenario, blend_node=None, extrapolation_growth=None, extrapolation_method=None, geography=None,
                 interpolation_method=None, name=None, notes=None, other_index_1=None, source=None,
                 supply_node=None):
        self.check_scenario(scenario)

        self.blend_node = blend_node
        self.extrapolation_growth = extrapolation_growth
        self.extrapolation_method = extrapolation_method
        self.geography = geography
        self.interpolation_method = interpolation_method
        self.name = name
        self.notes = notes
        self.other_index_1 = other_index_1
        self.source = source
        self.supply_node = supply_node

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (name, blend_node, supply_node, geography, other_index_1, interpolation_method,
         extrapolation_method, extrapolation_growth, source, notes,) = tup

        self.set_args(scenario, blend_node=blend_node, extrapolation_growth=extrapolation_growth,
                  extrapolation_method=extrapolation_method, geography=geography,
                  interpolation_method=interpolation_method, name=name, notes=notes,
                  other_index_1=other_index_1, source=source, supply_node=supply_node)

class CO2PriceMeasures(DataObject):
    _instances_by_key = {}
    _table_name = "CO2PriceMeasures"
    _key_col = "name"
    _cols = ["extrapolation_growth", "extrapolation_method", "geography", "geography_map_key",
             "interpolation_method", "name", "notes", "source", "supply_node"]
    _df_cols = ["gau", "sensitivity", "value", "year"]
    _df_filters = []
    _data_table_name = None

    def __init__(self, name, scenario):
        DataObject.__init__(self, name, scenario)

        CO2PriceMeasures._instances_by_key[self._key] = self

        self.extrapolation_growth = None
        self.extrapolation_method = None
        self.geography = None
        self.geography_map_key = None
        self.interpolation_method = None
        self.name = None
        self.notes = None
        self.source = None
        self.supply_node = None

    def set_args(self, scenario, extrapolation_growth=None, extrapolation_method=None, geography=None,
                 geography_map_key=None, interpolation_method=None, name=None, notes=None, source=None,
                 supply_node=None):
        self.check_scenario(scenario)

        self.extrapolation_growth = extrapolation_growth
        self.extrapolation_method = extrapolation_method
        self.geography = geography
        self.geography_map_key = geography_map_key
        self.interpolation_method = interpolation_method
        self.name = name
        self.notes = notes
        self.source = source
        self.supply_node = supply_node

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (name, geography, interpolation_method, extrapolation_method, extrapolation_growth,
         geography_map_key, supply_node, source, notes,) = tup

        self.set_args(scenario, extrapolation_growth=extrapolation_growth, extrapolation_method=extrapolation_method,
                  geography=geography, geography_map_key=geography_map_key,
                  interpolation_method=interpolation_method, name=name, notes=notes, source=source,
                  supply_node=supply_node)

class DemandDrivers(DataObject):
    _instances_by_key = {}
    _table_name = "DemandDrivers"
    _key_col = "name"
    _cols = ["base_driver", "extrapolation_growth", "extrapolation_method", "geography",
             "geography_map_key", "input_type", "interpolation_method", "name", "notes",
             "other_index_1", "other_index_2", "source", "unit_base", "unit_prefix"]
    _df_cols = ["gau", "value", "oth_2", "oth_1", "year", "sensitivity"]
    _df_filters = []
    _data_table_name = None

    def __init__(self, name, scenario):
        DataObject.__init__(self, name, scenario)

        DemandDrivers._instances_by_key[self._key] = self

        self.base_driver = None
        self.extrapolation_growth = None
        self.extrapolation_method = None
        self.geography = None
        self.geography_map_key = None
        self.input_type = None
        self.interpolation_method = None
        self.name = None
        self.notes = None
        self.other_index_1 = None
        self.other_index_2 = None
        self.source = None
        self.unit_base = None
        self.unit_prefix = None

    def set_args(self, scenario, base_driver=None, extrapolation_growth=None, extrapolation_method=None, geography=None,
                 geography_map_key=None, input_type=None, interpolation_method=None, name=None,
                 notes=None, other_index_1=None, other_index_2=None, source=None, unit_base=None,
                 unit_prefix=None):
        self.check_scenario(scenario)

        self.base_driver = base_driver
        self.extrapolation_growth = extrapolation_growth
        self.extrapolation_method = extrapolation_method
        self.geography = geography
        self.geography_map_key = geography_map_key
        self.input_type = input_type
        self.interpolation_method = interpolation_method
        self.name = name
        self.notes = notes
        self.other_index_1 = other_index_1
        self.other_index_2 = other_index_2
        self.source = source
        self.unit_base = unit_base
        self.unit_prefix = unit_prefix

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (name, base_driver, input_type, unit_prefix, unit_base, geography, other_index_1,
         other_index_2, geography_map_key, interpolation_method, extrapolation_method,
         extrapolation_growth, source, notes,) = tup

        self.set_args(scenario, base_driver=base_driver, extrapolation_growth=extrapolation_growth,
                  extrapolation_method=extrapolation_method, geography=geography,
                  geography_map_key=geography_map_key, input_type=input_type,
                  interpolation_method=interpolation_method, name=name, notes=notes,
                  other_index_1=other_index_1, other_index_2=other_index_2, source=source,
                  unit_base=unit_base, unit_prefix=unit_prefix)

class DemandEnergyDemands(DataObject):
    _instances_by_key = {}
    _table_name = "DemandEnergyDemands"
    _key_col = "subsector"
    _cols = ["demand_technology_index", "driver_1", "driver_2", "driver_denominator_1",
             "driver_denominator_2", "extrapolation_growth", "extrapolation_method",
             "final_energy_index", "geography", "geography_map_key", "input_type",
             "interpolation_method", "is_stock_dependent", "notes", "other_index_1", "other_index_2",
             "source", "subsector", "unit"]
    _df_cols = ["gau", "demand_technology", "value", "oth_2", "oth_1", "year", "final_energy",
             "sensitivity"]
    _df_filters = []
    _data_table_name = None

    def __init__(self, subsector, scenario):
        DataObject.__init__(self, subsector, scenario)

        DemandEnergyDemands._instances_by_key[self._key] = self

        self.demand_technology_index = None
        self.driver_1 = None
        self.driver_2 = None
        self.driver_denominator_1 = None
        self.driver_denominator_2 = None
        self.extrapolation_growth = None
        self.extrapolation_method = None
        self.final_energy_index = None
        self.geography = None
        self.geography_map_key = None
        self.input_type = None
        self.interpolation_method = None
        self.is_stock_dependent = None
        self.notes = None
        self.other_index_1 = None
        self.other_index_2 = None
        self.source = None
        self.subsector = None
        self.unit = None

    def set_args(self, scenario, demand_technology_index=None, driver_1=None, driver_2=None, driver_denominator_1=None,
                 driver_denominator_2=None, extrapolation_growth=None, extrapolation_method=None,
                 final_energy_index=None, geography=None, geography_map_key=None, input_type=None,
                 interpolation_method=None, is_stock_dependent=None, notes=None, other_index_1=None,
                 other_index_2=None, source=None, subsector=None, unit=None):
        self.check_scenario(scenario)

        self.demand_technology_index = demand_technology_index
        self.driver_1 = driver_1
        self.driver_2 = driver_2
        self.driver_denominator_1 = driver_denominator_1
        self.driver_denominator_2 = driver_denominator_2
        self.extrapolation_growth = extrapolation_growth
        self.extrapolation_method = extrapolation_method
        self.final_energy_index = final_energy_index
        self.geography = geography
        self.geography_map_key = geography_map_key
        self.input_type = input_type
        self.interpolation_method = interpolation_method
        self.is_stock_dependent = is_stock_dependent
        self.notes = notes
        self.other_index_1 = other_index_1
        self.other_index_2 = other_index_2
        self.source = source
        self.subsector = subsector
        self.unit = unit

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (subsector, is_stock_dependent, input_type, unit, driver_denominator_1,
         driver_denominator_2, driver_1, driver_2, geography, final_energy_index,
         demand_technology_index, other_index_1, other_index_2, interpolation_method,
         extrapolation_method, extrapolation_growth, geography_map_key, source, notes,) = tup

        self.set_args(scenario, demand_technology_index=demand_technology_index, driver_1=driver_1, driver_2=driver_2,
                  driver_denominator_1=driver_denominator_1, driver_denominator_2=driver_denominator_2,
                  extrapolation_growth=extrapolation_growth, extrapolation_method=extrapolation_method,
                  final_energy_index=final_energy_index, geography=geography,
                  geography_map_key=geography_map_key, input_type=input_type,
                  interpolation_method=interpolation_method, is_stock_dependent=is_stock_dependent,
                  notes=notes, other_index_1=other_index_1, other_index_2=other_index_2, source=source,
                  subsector=subsector, unit=unit)

class DemandEnergyEfficiencyMeasures(DataObject):
    _instances_by_key = {}
    _table_name = "DemandEnergyEfficiencyMeasures"
    _key_col = "name"
    _cols = ["extrapolation_growth", "extrapolation_method", "geography", "input_type",
             "interpolation_method", "lifetime_variance", "max_lifetime", "mean_lifetime",
             "min_lifetime", "name", "notes", "other_index_1", "other_index_2", "source",
             "stock_decay_function", "subsector", "unit"]
    _df_cols = ["gau", "value", "oth_2", "oth_1", "year", "final_energy"]
    _df_filters = []
    _data_table_name = None

    def __init__(self, name, scenario):
        DataObject.__init__(self, name, scenario)

        DemandEnergyEfficiencyMeasures._instances_by_key[self._key] = self

        self.extrapolation_growth = None
        self.extrapolation_method = None
        self.geography = None
        self.input_type = None
        self.interpolation_method = None
        self.lifetime_variance = None
        self.max_lifetime = None
        self.mean_lifetime = None
        self.min_lifetime = None
        self.name = None
        self.notes = None
        self.other_index_1 = None
        self.other_index_2 = None
        self.source = None
        self.stock_decay_function = None
        self.subsector = None
        self.unit = None

    def set_args(self, scenario, extrapolation_growth=None, extrapolation_method=None, geography=None, input_type=None,
                 interpolation_method=None, lifetime_variance=None, max_lifetime=None, mean_lifetime=None,
                 min_lifetime=None, name=None, notes=None, other_index_1=None, other_index_2=None,
                 source=None, stock_decay_function=None, subsector=None, unit=None):
        self.check_scenario(scenario)

        self.extrapolation_growth = extrapolation_growth
        self.extrapolation_method = extrapolation_method
        self.geography = geography
        self.input_type = input_type
        self.interpolation_method = interpolation_method
        self.lifetime_variance = lifetime_variance
        self.max_lifetime = max_lifetime
        self.mean_lifetime = mean_lifetime
        self.min_lifetime = min_lifetime
        self.name = name
        self.notes = notes
        self.other_index_1 = other_index_1
        self.other_index_2 = other_index_2
        self.source = source
        self.stock_decay_function = stock_decay_function
        self.subsector = subsector
        self.unit = unit

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (name, subsector, input_type, unit, geography, other_index_1, other_index_2,
         interpolation_method, extrapolation_method, extrapolation_growth, stock_decay_function,
         min_lifetime, max_lifetime, mean_lifetime, lifetime_variance, source, notes,) = tup

        self.set_args(scenario, extrapolation_growth=extrapolation_growth, extrapolation_method=extrapolation_method,
                  geography=geography, input_type=input_type, interpolation_method=interpolation_method,
                  lifetime_variance=lifetime_variance, max_lifetime=max_lifetime,
                  mean_lifetime=mean_lifetime, min_lifetime=min_lifetime, name=name, notes=notes,
                  other_index_1=other_index_1, other_index_2=other_index_2, source=source,
                  stock_decay_function=stock_decay_function, subsector=subsector, unit=unit)

class DemandEnergyEfficiencyMeasuresCost(DataObject):
    _instances_by_key = {}
    _table_name = "DemandEnergyEfficiencyMeasuresCost"
    _key_col = "parent"
    _cols = ["cost_denominator_unit", "cost_of_capital", "currency", "currency_year",
             "extrapolation_growth", "extrapolation_method", "geography", "interpolation_method",
             "is_levelized", "notes", "other_index_1", "other_index_2", "parent", "source"]
    _df_cols = ["vintage", "gau", "value", "oth_2", "oth_1", "final_energy"]
    _df_filters = []
    _data_table_name = None

    def __init__(self, parent, scenario):
        DataObject.__init__(self, parent, scenario)

        DemandEnergyEfficiencyMeasuresCost._instances_by_key[self._key] = self

        self.cost_denominator_unit = None
        self.cost_of_capital = None
        self.currency = None
        self.currency_year = None
        self.extrapolation_growth = None
        self.extrapolation_method = None
        self.geography = None
        self.interpolation_method = None
        self.is_levelized = None
        self.notes = None
        self.other_index_1 = None
        self.other_index_2 = None
        self.parent = None
        self.source = None

    def set_args(self, scenario, cost_denominator_unit=None, cost_of_capital=None, currency=None, currency_year=None,
                 extrapolation_growth=None, extrapolation_method=None, geography=None,
                 interpolation_method=None, is_levelized=None, notes=None, other_index_1=None,
                 other_index_2=None, parent=None, source=None):
        self.check_scenario(scenario)

        self.cost_denominator_unit = cost_denominator_unit
        self.cost_of_capital = cost_of_capital
        self.currency = currency
        self.currency_year = currency_year
        self.extrapolation_growth = extrapolation_growth
        self.extrapolation_method = extrapolation_method
        self.geography = geography
        self.interpolation_method = interpolation_method
        self.is_levelized = is_levelized
        self.notes = notes
        self.other_index_1 = other_index_1
        self.other_index_2 = other_index_2
        self.parent = parent
        self.source = source

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (parent, currency, currency_year, cost_denominator_unit, cost_of_capital, is_levelized,
         geography, other_index_1, other_index_2, interpolation_method, extrapolation_method,
         extrapolation_growth, source, notes,) = tup

        self.set_args(scenario, cost_denominator_unit=cost_denominator_unit, cost_of_capital=cost_of_capital,
                  currency=currency, currency_year=currency_year,
                  extrapolation_growth=extrapolation_growth, extrapolation_method=extrapolation_method,
                  geography=geography, interpolation_method=interpolation_method,
                  is_levelized=is_levelized, notes=notes, other_index_1=other_index_1,
                  other_index_2=other_index_2, parent=parent, source=source)

class DemandFlexibleLoadMeasures(DataObject):
    _instances_by_key = {}
    _table_name = "DemandFlexibleLoadMeasures"
    _key_col = "name"
    _cols = ["extrapolation_growth", "extrapolation_method", "geography", "interpolation_method",
             "name", "notes", "other_index_1", "source", "subsector"]
    _df_cols = ["gau", "demand_technology", "value", "oth_1", "year"]
    _df_filters = []
    _data_table_name = None

    def __init__(self, name, scenario):
        DataObject.__init__(self, name, scenario)

        DemandFlexibleLoadMeasures._instances_by_key[self._key] = self

        self.extrapolation_growth = None
        self.extrapolation_method = None
        self.geography = None
        self.interpolation_method = None
        self.name = None
        self.notes = None
        self.other_index_1 = None
        self.source = None
        self.subsector = None

    def set_args(self, scenario, extrapolation_growth=None, extrapolation_method=None, geography=None,
                 interpolation_method=None, name=None, notes=None, other_index_1=None, source=None,
                 subsector=None):
        self.check_scenario(scenario)

        self.extrapolation_growth = extrapolation_growth
        self.extrapolation_method = extrapolation_method
        self.geography = geography
        self.interpolation_method = interpolation_method
        self.name = name
        self.notes = notes
        self.other_index_1 = other_index_1
        self.source = source
        self.subsector = subsector

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (name, subsector, geography, other_index_1, interpolation_method, extrapolation_method,
         extrapolation_growth, source, notes,) = tup

        self.set_args(scenario, extrapolation_growth=extrapolation_growth, extrapolation_method=extrapolation_method,
                  geography=geography, interpolation_method=interpolation_method, name=name, notes=notes,
                  other_index_1=other_index_1, source=source, subsector=subsector)

class DemandFuelSwitchingMeasures(DataObject):
    _instances_by_key = {}
    _table_name = "DemandFuelSwitchingMeasures"
    _key_col = "name"
    _cols = ["final_energy_from", "final_energy_to", "lifetime_variance", "max_lifetime",
             "mean_lifetime", "min_lifetime", "name", "stock_decay_function", "subsector"]
    _df_cols = []
    _df_filters = []
    _data_table_name = None

    def __init__(self, name, scenario):
        DataObject.__init__(self, name, scenario)

        DemandFuelSwitchingMeasures._instances_by_key[self._key] = self

        self.final_energy_from = None
        self.final_energy_to = None
        self.lifetime_variance = None
        self.max_lifetime = None
        self.mean_lifetime = None
        self.min_lifetime = None
        self.name = None
        self.stock_decay_function = None
        self.subsector = None

    def set_args(self, scenario, final_energy_from=None, final_energy_to=None, lifetime_variance=None, max_lifetime=None,
                 mean_lifetime=None, min_lifetime=None, name=None, stock_decay_function=None,
                 subsector=None):
        self.check_scenario(scenario)

        self.final_energy_from = final_energy_from
        self.final_energy_to = final_energy_to
        self.lifetime_variance = lifetime_variance
        self.max_lifetime = max_lifetime
        self.mean_lifetime = mean_lifetime
        self.min_lifetime = min_lifetime
        self.name = name
        self.stock_decay_function = stock_decay_function
        self.subsector = subsector

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (name, subsector, final_energy_from, final_energy_to, stock_decay_function, max_lifetime,
         min_lifetime, mean_lifetime, lifetime_variance,) = tup

        self.set_args(scenario, final_energy_from=final_energy_from, final_energy_to=final_energy_to,
                  lifetime_variance=lifetime_variance, max_lifetime=max_lifetime,
                  mean_lifetime=mean_lifetime, min_lifetime=min_lifetime, name=name,
                  stock_decay_function=stock_decay_function, subsector=subsector)

class DemandFuelSwitchingMeasuresCost(DataObject):
    _instances_by_key = {}
    _table_name = "DemandFuelSwitchingMeasuresCost"
    _key_col = "parent"
    _cols = ["cost_denominator_unit", "cost_of_capital", "currency", "currency_year",
             "extrapolation_growth", "extrapolation_method", "geography", "interpolation_method",
             "is_levelized", "notes", "other_index_1", "other_index_2", "parent", "source"]
    _df_cols = ["vintage", "gau", "value", "oth_2", "oth_1"]
    _df_filters = []
    _data_table_name = None

    def __init__(self, parent, scenario):
        DataObject.__init__(self, parent, scenario)

        DemandFuelSwitchingMeasuresCost._instances_by_key[self._key] = self

        self.cost_denominator_unit = None
        self.cost_of_capital = None
        self.currency = None
        self.currency_year = None
        self.extrapolation_growth = None
        self.extrapolation_method = None
        self.geography = None
        self.interpolation_method = None
        self.is_levelized = None
        self.notes = None
        self.other_index_1 = None
        self.other_index_2 = None
        self.parent = None
        self.source = None

    def set_args(self, scenario, cost_denominator_unit=None, cost_of_capital=None, currency=None, currency_year=None,
                 extrapolation_growth=None, extrapolation_method=None, geography=None,
                 interpolation_method=None, is_levelized=None, notes=None, other_index_1=None,
                 other_index_2=None, parent=None, source=None):
        self.check_scenario(scenario)

        self.cost_denominator_unit = cost_denominator_unit
        self.cost_of_capital = cost_of_capital
        self.currency = currency
        self.currency_year = currency_year
        self.extrapolation_growth = extrapolation_growth
        self.extrapolation_method = extrapolation_method
        self.geography = geography
        self.interpolation_method = interpolation_method
        self.is_levelized = is_levelized
        self.notes = notes
        self.other_index_1 = other_index_1
        self.other_index_2 = other_index_2
        self.parent = parent
        self.source = source

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (parent, currency, currency_year, cost_denominator_unit, cost_of_capital, is_levelized,
         geography, other_index_1, other_index_2, interpolation_method, extrapolation_method,
         extrapolation_growth, source, notes,) = tup

        self.set_args(scenario, cost_denominator_unit=cost_denominator_unit, cost_of_capital=cost_of_capital,
                  currency=currency, currency_year=currency_year,
                  extrapolation_growth=extrapolation_growth, extrapolation_method=extrapolation_method,
                  geography=geography, interpolation_method=interpolation_method,
                  is_levelized=is_levelized, notes=notes, other_index_1=other_index_1,
                  other_index_2=other_index_2, parent=parent, source=source)

class DemandFuelSwitchingMeasuresEnergyIntensity(DataObject):
    _instances_by_key = {}
    _table_name = "DemandFuelSwitchingMeasuresEnergyIntensity"
    _key_col = "parent"
    _cols = ["extrapolation_growth", "extrapolation_method", "geography", "interpolation_method",
             "notes", "other_index_1", "other_index_2", "parent", "source"]
    _df_cols = ["gau", "value", "oth_2", "oth_1", "year"]
    _df_filters = []
    _data_table_name = None

    def __init__(self, parent, scenario):
        DataObject.__init__(self, parent, scenario)

        DemandFuelSwitchingMeasuresEnergyIntensity._instances_by_key[self._key] = self

        self.extrapolation_growth = None
        self.extrapolation_method = None
        self.geography = None
        self.interpolation_method = None
        self.notes = None
        self.other_index_1 = None
        self.other_index_2 = None
        self.parent = None
        self.source = None

    def set_args(self, scenario, extrapolation_growth=None, extrapolation_method=None, geography=None,
                 interpolation_method=None, notes=None, other_index_1=None, other_index_2=None,
                 parent=None, source=None):
        self.check_scenario(scenario)

        self.extrapolation_growth = extrapolation_growth
        self.extrapolation_method = extrapolation_method
        self.geography = geography
        self.interpolation_method = interpolation_method
        self.notes = notes
        self.other_index_1 = other_index_1
        self.other_index_2 = other_index_2
        self.parent = parent
        self.source = source

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (parent, geography, other_index_1, other_index_2, interpolation_method,
         extrapolation_method, extrapolation_growth, source, notes,) = tup

        self.set_args(scenario, extrapolation_growth=extrapolation_growth, extrapolation_method=extrapolation_method,
                  geography=geography, interpolation_method=interpolation_method, notes=notes,
                  other_index_1=other_index_1, other_index_2=other_index_2, parent=parent, source=source)

class DemandFuelSwitchingMeasuresImpact(DataObject):
    _instances_by_key = {}
    _table_name = "DemandFuelSwitchingMeasuresImpact"
    _key_col = "parent"
    _cols = ["extrapolation_growth", "extrapolation_method", "geography", "input_type",
             "interpolation_method", "notes", "other_index_1", "other_index_2", "parent", "source",
             "unit"]
    _df_cols = ["gau", "value", "oth_2", "oth_1", "year"]
    _df_filters = []
    _data_table_name = None

    def __init__(self, parent, scenario):
        DataObject.__init__(self, parent, scenario)

        DemandFuelSwitchingMeasuresImpact._instances_by_key[self._key] = self

        self.extrapolation_growth = None
        self.extrapolation_method = None
        self.geography = None
        self.input_type = None
        self.interpolation_method = None
        self.notes = None
        self.other_index_1 = None
        self.other_index_2 = None
        self.parent = None
        self.source = None
        self.unit = None

    def set_args(self, scenario, extrapolation_growth=None, extrapolation_method=None, geography=None, input_type=None,
                 interpolation_method=None, notes=None, other_index_1=None, other_index_2=None,
                 parent=None, source=None, unit=None):
        self.check_scenario(scenario)

        self.extrapolation_growth = extrapolation_growth
        self.extrapolation_method = extrapolation_method
        self.geography = geography
        self.input_type = input_type
        self.interpolation_method = interpolation_method
        self.notes = notes
        self.other_index_1 = other_index_1
        self.other_index_2 = other_index_2
        self.parent = parent
        self.source = source
        self.unit = unit

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (parent, input_type, unit, geography, other_index_1, other_index_2, interpolation_method,
         extrapolation_method, extrapolation_growth, source, notes,) = tup

        self.set_args(scenario, extrapolation_growth=extrapolation_growth, extrapolation_method=extrapolation_method,
                  geography=geography, input_type=input_type, interpolation_method=interpolation_method,
                  notes=notes, other_index_1=other_index_1, other_index_2=other_index_2, parent=parent,
                  source=source, unit=unit)

class DemandSales(DataObject):
    _instances_by_key = {}
    _table_name = "DemandSales"
    _key_col = "demand_technology"
    _cols = ["demand_technology", "extrapolation_growth", "extrapolation_method", "geography",
             "input_type", "interpolation_method", "notes", "other_index_1", "other_index_2",
             "source", "subsector"]
    _df_cols = ["vintage", "gau", "value", "oth_2", "oth_1"]
    _df_filters = []
    _data_table_name = None

    def __init__(self, demand_technology, scenario):
        DataObject.__init__(self, demand_technology, scenario)

        DemandSales._instances_by_key[self._key] = self

        self.demand_technology = None
        self.extrapolation_growth = None
        self.extrapolation_method = None
        self.geography = None
        self.input_type = None
        self.interpolation_method = None
        self.notes = None
        self.other_index_1 = None
        self.other_index_2 = None
        self.source = None
        self.subsector = None

    def set_args(self, scenario, demand_technology=None, extrapolation_growth=None, extrapolation_method=None,
                 geography=None, input_type=None, interpolation_method=None, notes=None,
                 other_index_1=None, other_index_2=None, source=None, subsector=None):
        self.check_scenario(scenario)

        self.demand_technology = demand_technology
        self.extrapolation_growth = extrapolation_growth
        self.extrapolation_method = extrapolation_method
        self.geography = geography
        self.input_type = input_type
        self.interpolation_method = interpolation_method
        self.notes = notes
        self.other_index_1 = other_index_1
        self.other_index_2 = other_index_2
        self.source = source
        self.subsector = subsector

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (subsector, geography, other_index_1, other_index_2, input_type, interpolation_method,
         extrapolation_method, extrapolation_growth, source, notes, demand_technology,) = tup

        self.set_args(scenario, demand_technology=demand_technology, extrapolation_growth=extrapolation_growth,
                  extrapolation_method=extrapolation_method, geography=geography, input_type=input_type,
                  interpolation_method=interpolation_method, notes=notes, other_index_1=other_index_1,
                  other_index_2=other_index_2, source=source, subsector=subsector)

class DemandSalesShareMeasures(DataObject):
    _instances_by_key = {}
    _table_name = "DemandSalesShareMeasures"
    _key_col = "name"
    _cols = ["demand_technology", "extrapolation_growth", "extrapolation_method", "geography",
             "input_type", "interpolation_method", "name", "notes", "other_index_1",
             "replaced_demand_tech", "source", "subsector"]
    _df_cols = ["vintage", "gau", "oth_1", "value"]
    _df_filters = []
    _data_table_name = None

    def __init__(self, name, scenario):
        DataObject.__init__(self, name, scenario)

        DemandSalesShareMeasures._instances_by_key[self._key] = self

        self.demand_technology = None
        self.extrapolation_growth = None
        self.extrapolation_method = None
        self.geography = None
        self.input_type = None
        self.interpolation_method = None
        self.name = None
        self.notes = None
        self.other_index_1 = None
        self.replaced_demand_tech = None
        self.source = None
        self.subsector = None

    def set_args(self, scenario, demand_technology=None, extrapolation_growth=None, extrapolation_method=None,
                 geography=None, input_type=None, interpolation_method=None, name=None, notes=None,
                 other_index_1=None, replaced_demand_tech=None, source=None, subsector=None):
        self.check_scenario(scenario)

        self.demand_technology = demand_technology
        self.extrapolation_growth = extrapolation_growth
        self.extrapolation_method = extrapolation_method
        self.geography = geography
        self.input_type = input_type
        self.interpolation_method = interpolation_method
        self.name = name
        self.notes = notes
        self.other_index_1 = other_index_1
        self.replaced_demand_tech = replaced_demand_tech
        self.source = source
        self.subsector = subsector

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (name, subsector, geography, other_index_1, demand_technology, replaced_demand_tech,
         input_type, interpolation_method, extrapolation_method, extrapolation_growth, source,
         notes,) = tup

        self.set_args(scenario, demand_technology=demand_technology, extrapolation_growth=extrapolation_growth,
                  extrapolation_method=extrapolation_method, geography=geography, input_type=input_type,
                  interpolation_method=interpolation_method, name=name, notes=notes,
                  other_index_1=other_index_1, replaced_demand_tech=replaced_demand_tech, source=source,
                  subsector=subsector)

class DemandSectors(DataObject):
    _instances_by_key = {}
    _table_name = "DemandSectors"
    _key_col = "name"
    _cols = ["max_lag_hours", "max_lead_hours", "name", "shape"]
    _df_cols = []
    _df_filters = []
    _data_table_name = None

    def __init__(self, name, scenario):
        DataObject.__init__(self, name, scenario)

        DemandSectors._instances_by_key[self._key] = self

        self.max_lag_hours = None
        self.max_lead_hours = None
        self.name = None
        self.shape = None

    def set_args(self, scenario, max_lag_hours=None, max_lead_hours=None, name=None, shape=None):
        self.check_scenario(scenario)

        self.max_lag_hours = max_lag_hours
        self.max_lead_hours = max_lead_hours
        self.name = name
        self.shape = shape

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (name, shape, max_lead_hours, max_lag_hours,) = tup

        self.set_args(scenario, max_lag_hours=max_lag_hours, max_lead_hours=max_lead_hours, name=name, shape=shape)

class DemandServiceDemandMeasures(DataObject):
    _instances_by_key = {}
    _table_name = "DemandServiceDemandMeasures"
    _key_col = "name"
    _cols = ["extrapolation_growth", "extrapolation_method", "geography", "geography_map_key",
             "input_type", "interpolation_method", "lifetime_variance", "max_lifetime",
             "mean_lifetime", "min_lifetime", "name", "notes", "other_index_1", "other_index_2",
             "source", "stock_decay_function", "subsector", "unit"]
    _df_cols = ["gau", "value", "oth_2", "oth_1", "year"]
    _df_filters = []
    _data_table_name = None

    def __init__(self, name, scenario):
        DataObject.__init__(self, name, scenario)

        DemandServiceDemandMeasures._instances_by_key[self._key] = self

        self.extrapolation_growth = None
        self.extrapolation_method = None
        self.geography = None
        self.geography_map_key = None
        self.input_type = None
        self.interpolation_method = None
        self.lifetime_variance = None
        self.max_lifetime = None
        self.mean_lifetime = None
        self.min_lifetime = None
        self.name = None
        self.notes = None
        self.other_index_1 = None
        self.other_index_2 = None
        self.source = None
        self.stock_decay_function = None
        self.subsector = None
        self.unit = None

    def set_args(self, scenario, extrapolation_growth=None, extrapolation_method=None, geography=None,
                 geography_map_key=None, input_type=None, interpolation_method=None,
                 lifetime_variance=None, max_lifetime=None, mean_lifetime=None, min_lifetime=None,
                 name=None, notes=None, other_index_1=None, other_index_2=None, source=None,
                 stock_decay_function=None, subsector=None, unit=None):
        self.check_scenario(scenario)

        self.extrapolation_growth = extrapolation_growth
        self.extrapolation_method = extrapolation_method
        self.geography = geography
        self.geography_map_key = geography_map_key
        self.input_type = input_type
        self.interpolation_method = interpolation_method
        self.lifetime_variance = lifetime_variance
        self.max_lifetime = max_lifetime
        self.mean_lifetime = mean_lifetime
        self.min_lifetime = min_lifetime
        self.name = name
        self.notes = notes
        self.other_index_1 = other_index_1
        self.other_index_2 = other_index_2
        self.source = source
        self.stock_decay_function = stock_decay_function
        self.subsector = subsector
        self.unit = unit

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (name, subsector, input_type, unit, geography, other_index_1, other_index_2,
         interpolation_method, extrapolation_method, extrapolation_growth, stock_decay_function,
         min_lifetime, max_lifetime, mean_lifetime, lifetime_variance, geography_map_key, source,
         notes,) = tup

        self.set_args(scenario, extrapolation_growth=extrapolation_growth, extrapolation_method=extrapolation_method,
                  geography=geography, geography_map_key=geography_map_key, input_type=input_type,
                  interpolation_method=interpolation_method, lifetime_variance=lifetime_variance,
                  max_lifetime=max_lifetime, mean_lifetime=mean_lifetime, min_lifetime=min_lifetime,
                  name=name, notes=notes, other_index_1=other_index_1, other_index_2=other_index_2,
                  source=source, stock_decay_function=stock_decay_function, subsector=subsector, unit=unit)

class DemandServiceDemandMeasuresCost(DataObject):
    _instances_by_key = {}
    _table_name = "DemandServiceDemandMeasuresCost"
    _key_col = "parent"
    _cols = ["cost_denominator_unit", "cost_of_capital", "currency", "currency_year",
             "extrapolation_growth", "extrapolation_method", "geography", "interpolation_method",
             "is_levelized", "notes", "other_index_1", "other_index_2", "parent", "source"]
    _df_cols = ["vintage", "gau", "value", "oth_2", "oth_1"]
    _df_filters = []
    _data_table_name = None

    def __init__(self, parent, scenario):
        DataObject.__init__(self, parent, scenario)

        DemandServiceDemandMeasuresCost._instances_by_key[self._key] = self

        self.cost_denominator_unit = None
        self.cost_of_capital = None
        self.currency = None
        self.currency_year = None
        self.extrapolation_growth = None
        self.extrapolation_method = None
        self.geography = None
        self.interpolation_method = None
        self.is_levelized = None
        self.notes = None
        self.other_index_1 = None
        self.other_index_2 = None
        self.parent = None
        self.source = None

    def set_args(self, scenario, cost_denominator_unit=None, cost_of_capital=None, currency=None, currency_year=None,
                 extrapolation_growth=None, extrapolation_method=None, geography=None,
                 interpolation_method=None, is_levelized=None, notes=None, other_index_1=None,
                 other_index_2=None, parent=None, source=None):
        self.check_scenario(scenario)

        self.cost_denominator_unit = cost_denominator_unit
        self.cost_of_capital = cost_of_capital
        self.currency = currency
        self.currency_year = currency_year
        self.extrapolation_growth = extrapolation_growth
        self.extrapolation_method = extrapolation_method
        self.geography = geography
        self.interpolation_method = interpolation_method
        self.is_levelized = is_levelized
        self.notes = notes
        self.other_index_1 = other_index_1
        self.other_index_2 = other_index_2
        self.parent = parent
        self.source = source

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (parent, currency, currency_year, cost_denominator_unit, cost_of_capital, is_levelized,
         geography, other_index_1, other_index_2, interpolation_method, extrapolation_method,
         extrapolation_growth, source, notes,) = tup

        self.set_args(scenario, cost_denominator_unit=cost_denominator_unit, cost_of_capital=cost_of_capital,
                  currency=currency, currency_year=currency_year,
                  extrapolation_growth=extrapolation_growth, extrapolation_method=extrapolation_method,
                  geography=geography, interpolation_method=interpolation_method,
                  is_levelized=is_levelized, notes=notes, other_index_1=other_index_1,
                  other_index_2=other_index_2, parent=parent, source=source)

class DemandServiceDemands(DataObject):
    _instances_by_key = {}
    _table_name = "DemandServiceDemands"
    _key_col = "subsector"
    _cols = ["demand_technology_index", "driver_1", "driver_2", "driver_denominator_1",
             "driver_denominator_2", "extrapolation_growth", "extrapolation_method",
             "final_energy_index", "geography", "geography_map_key", "input_type",
             "interpolation_method", "is_stock_dependent", "notes", "other_index_1", "other_index_2",
             "source", "subsector", "unit"]
    _df_cols = ["gau", "demand_technology", "value", "oth_2", "oth_1", "year", "final_energy",
             "sensitivity"]
    _df_filters = []
    _data_table_name = None

    def __init__(self, subsector, scenario):
        DataObject.__init__(self, subsector, scenario)

        DemandServiceDemands._instances_by_key[self._key] = self

        self.demand_technology_index = None
        self.driver_1 = None
        self.driver_2 = None
        self.driver_denominator_1 = None
        self.driver_denominator_2 = None
        self.extrapolation_growth = None
        self.extrapolation_method = None
        self.final_energy_index = None
        self.geography = None
        self.geography_map_key = None
        self.input_type = None
        self.interpolation_method = None
        self.is_stock_dependent = None
        self.notes = None
        self.other_index_1 = None
        self.other_index_2 = None
        self.source = None
        self.subsector = None
        self.unit = None

    def set_args(self, scenario, demand_technology_index=None, driver_1=None, driver_2=None, driver_denominator_1=None,
                 driver_denominator_2=None, extrapolation_growth=None, extrapolation_method=None,
                 final_energy_index=None, geography=None, geography_map_key=None, input_type=None,
                 interpolation_method=None, is_stock_dependent=None, notes=None, other_index_1=None,
                 other_index_2=None, source=None, subsector=None, unit=None):
        self.check_scenario(scenario)

        self.demand_technology_index = demand_technology_index
        self.driver_1 = driver_1
        self.driver_2 = driver_2
        self.driver_denominator_1 = driver_denominator_1
        self.driver_denominator_2 = driver_denominator_2
        self.extrapolation_growth = extrapolation_growth
        self.extrapolation_method = extrapolation_method
        self.final_energy_index = final_energy_index
        self.geography = geography
        self.geography_map_key = geography_map_key
        self.input_type = input_type
        self.interpolation_method = interpolation_method
        self.is_stock_dependent = is_stock_dependent
        self.notes = notes
        self.other_index_1 = other_index_1
        self.other_index_2 = other_index_2
        self.source = source
        self.subsector = subsector
        self.unit = unit

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (subsector, is_stock_dependent, input_type, unit, driver_denominator_1,
         driver_denominator_2, driver_1, driver_2, geography, final_energy_index,
         demand_technology_index, other_index_1, other_index_2, interpolation_method,
         extrapolation_method, extrapolation_growth, geography_map_key, source, notes,) = tup

        self.set_args(scenario, demand_technology_index=demand_technology_index, driver_1=driver_1, driver_2=driver_2,
                  driver_denominator_1=driver_denominator_1, driver_denominator_2=driver_denominator_2,
                  extrapolation_growth=extrapolation_growth, extrapolation_method=extrapolation_method,
                  final_energy_index=final_energy_index, geography=geography,
                  geography_map_key=geography_map_key, input_type=input_type,
                  interpolation_method=interpolation_method, is_stock_dependent=is_stock_dependent,
                  notes=notes, other_index_1=other_index_1, other_index_2=other_index_2, source=source,
                  subsector=subsector, unit=unit)

class DemandServiceEfficiency(DataObject):
    _instances_by_key = {}
    _table_name = "DemandServiceEfficiency"
    _key_col = "subsector"
    _cols = ["denominator_unit", "energy_unit", "extrapolation_growth", "extrapolation_method",
             "geography", "geography_map_key", "interpolation_method", "notes", "other_index_1",
             "other_index_2", "sensitivity", "source", "subsector"]
    _df_cols = ["gau", "value", "oth_2", "oth_1", "year", "final_energy"]
    _df_filters = []
    _data_table_name = None

    def __init__(self, subsector, scenario):
        DataObject.__init__(self, subsector, scenario)

        DemandServiceEfficiency._instances_by_key[self._key] = self

        self.denominator_unit = None
        self.energy_unit = None
        self.extrapolation_growth = None
        self.extrapolation_method = None
        self.geography = None
        self.geography_map_key = None
        self.interpolation_method = None
        self.notes = None
        self.other_index_1 = None
        self.other_index_2 = None
        self.sensitivity = None
        self.source = None
        self.subsector = None

    def set_args(self, scenario, denominator_unit=None, energy_unit=None, extrapolation_growth=None,
                 extrapolation_method=None, geography=None, geography_map_key=None,
                 interpolation_method=None, notes=None, other_index_1=None, other_index_2=None,
                 sensitivity=None, source=None, subsector=None):
        self.check_scenario(scenario)

        self.denominator_unit = denominator_unit
        self.energy_unit = energy_unit
        self.extrapolation_growth = extrapolation_growth
        self.extrapolation_method = extrapolation_method
        self.geography = geography
        self.geography_map_key = geography_map_key
        self.interpolation_method = interpolation_method
        self.notes = notes
        self.other_index_1 = other_index_1
        self.other_index_2 = other_index_2
        self.sensitivity = sensitivity
        self.source = source
        self.subsector = subsector

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (subsector, energy_unit, denominator_unit, geography, other_index_1, other_index_2,
         interpolation_method, extrapolation_method, extrapolation_growth, geography_map_key,
         source, notes, sensitivity,) = tup

        self.set_args(scenario, denominator_unit=denominator_unit, energy_unit=energy_unit,
                  extrapolation_growth=extrapolation_growth, extrapolation_method=extrapolation_method,
                  geography=geography, geography_map_key=geography_map_key,
                  interpolation_method=interpolation_method, notes=notes, other_index_1=other_index_1,
                  other_index_2=other_index_2, sensitivity=sensitivity, source=source, subsector=subsector)

class DemandServiceLink(DataObject):
    _instances_by_key = {}
    _table_name = "DemandServiceLink"
    _key_col = "name"
    _cols = ["linked_subsector", "name", "service_demand_share", "subsector", "year"]
    _df_cols = []
    _df_filters = []
    _data_table_name = None

    def __init__(self, name, scenario):
        DataObject.__init__(self, name, scenario)

        DemandServiceLink._instances_by_key[self._key] = self

        self.linked_subsector = None
        self.name = None
        self.service_demand_share = None
        self.subsector = None
        self.year = None

    def set_args(self, scenario, linked_subsector=None, name=None, service_demand_share=None, subsector=None, year=None):
        self.check_scenario(scenario)

        self.linked_subsector = linked_subsector
        self.name = name
        self.service_demand_share = service_demand_share
        self.subsector = subsector
        self.year = year

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (name, subsector, linked_subsector, service_demand_share, year,) = tup

        self.set_args(scenario, linked_subsector=linked_subsector, name=name, service_demand_share=service_demand_share,
                  subsector=subsector, year=year)

class DemandStock(DataObject):
    _instances_by_key = {}
    _table_name = "DemandStock"
    _key_col = "subsector"
    _cols = ["demand_stock_unit_type", "driver_1", "driver_2", "driver_denominator_1",
             "driver_denominator_2", "extrapolation_growth", "extrapolation_method", "geography",
             "geography_map_key", "input_type", "interpolation_method", "is_service_demand_dependent",
             "notes", "other_index_1", "other_index_2", "source", "specify_stocks_past_current_year",
             "subsector", "time_unit", "unit"]
    _df_cols = ["gau", "demand_technology", "value", "oth_2", "oth_1", "year"]
    _df_filters = []
    _data_table_name = None

    def __init__(self, subsector, scenario):
        DataObject.__init__(self, subsector, scenario)

        DemandStock._instances_by_key[self._key] = self

        self.demand_stock_unit_type = None
        self.driver_1 = None
        self.driver_2 = None
        self.driver_denominator_1 = None
        self.driver_denominator_2 = None
        self.extrapolation_growth = None
        self.extrapolation_method = None
        self.geography = None
        self.geography_map_key = None
        self.input_type = None
        self.interpolation_method = None
        self.is_service_demand_dependent = None
        self.notes = None
        self.other_index_1 = None
        self.other_index_2 = None
        self.source = None
        self.specify_stocks_past_current_year = None
        self.subsector = None
        self.time_unit = None
        self.unit = None

    def set_args(self, scenario, demand_stock_unit_type=None, driver_1=None, driver_2=None, driver_denominator_1=None,
                 driver_denominator_2=None, extrapolation_growth=None, extrapolation_method=None,
                 geography=None, geography_map_key=None, input_type=None, interpolation_method=None,
                 is_service_demand_dependent=None, notes=None, other_index_1=None, other_index_2=None,
                 source=None, specify_stocks_past_current_year=None, subsector=None, time_unit=None,
                 unit=None):
        self.check_scenario(scenario)

        self.demand_stock_unit_type = demand_stock_unit_type
        self.driver_1 = driver_1
        self.driver_2 = driver_2
        self.driver_denominator_1 = driver_denominator_1
        self.driver_denominator_2 = driver_denominator_2
        self.extrapolation_growth = extrapolation_growth
        self.extrapolation_method = extrapolation_method
        self.geography = geography
        self.geography_map_key = geography_map_key
        self.input_type = input_type
        self.interpolation_method = interpolation_method
        self.is_service_demand_dependent = is_service_demand_dependent
        self.notes = notes
        self.other_index_1 = other_index_1
        self.other_index_2 = other_index_2
        self.source = source
        self.specify_stocks_past_current_year = specify_stocks_past_current_year
        self.subsector = subsector
        self.time_unit = time_unit
        self.unit = unit

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (subsector, is_service_demand_dependent, driver_denominator_1, driver_denominator_2,
         driver_1, driver_2, geography, other_index_1, other_index_2, geography_map_key,
         input_type, demand_stock_unit_type, unit, time_unit, interpolation_method,
         extrapolation_method, extrapolation_growth, specify_stocks_past_current_year, source,
         notes,) = tup

        self.set_args(scenario, demand_stock_unit_type=demand_stock_unit_type, driver_1=driver_1, driver_2=driver_2,
                  driver_denominator_1=driver_denominator_1, driver_denominator_2=driver_denominator_2,
                  extrapolation_growth=extrapolation_growth, extrapolation_method=extrapolation_method,
                  geography=geography, geography_map_key=geography_map_key, input_type=input_type,
                  interpolation_method=interpolation_method,
                  is_service_demand_dependent=is_service_demand_dependent, notes=notes,
                  other_index_1=other_index_1, other_index_2=other_index_2, source=source,
                  specify_stocks_past_current_year=specify_stocks_past_current_year, subsector=subsector,
                  time_unit=time_unit, unit=unit)

class DemandStockMeasures(DataObject):
    _instances_by_key = {}
    _table_name = "DemandStockMeasures"
    _key_col = "name"
    _cols = ["demand_technology", "extrapolation_growth", "extrapolation_method", "geography",
             "interpolation_method", "name", "notes", "other_index_1", "source", "subsector"]
    _df_cols = ["gau", "oth_1", "value", "year"]
    _df_filters = []
    _data_table_name = None

    def __init__(self, name, scenario):
        DataObject.__init__(self, name, scenario)

        DemandStockMeasures._instances_by_key[self._key] = self

        self.demand_technology = None
        self.extrapolation_growth = None
        self.extrapolation_method = None
        self.geography = None
        self.interpolation_method = None
        self.name = None
        self.notes = None
        self.other_index_1 = None
        self.source = None
        self.subsector = None

    def set_args(self, scenario, demand_technology=None, extrapolation_growth=None, extrapolation_method=None,
                 geography=None, interpolation_method=None, name=None, notes=None, other_index_1=None,
                 source=None, subsector=None):
        self.check_scenario(scenario)

        self.demand_technology = demand_technology
        self.extrapolation_growth = extrapolation_growth
        self.extrapolation_method = extrapolation_method
        self.geography = geography
        self.interpolation_method = interpolation_method
        self.name = name
        self.notes = notes
        self.other_index_1 = other_index_1
        self.source = source
        self.subsector = subsector

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (name, subsector, geography, other_index_1, demand_technology, interpolation_method,
         extrapolation_method, extrapolation_growth, source, notes,) = tup

        self.set_args(scenario, demand_technology=demand_technology, extrapolation_growth=extrapolation_growth,
                  extrapolation_method=extrapolation_method, geography=geography,
                  interpolation_method=interpolation_method, name=name, notes=notes,
                  other_index_1=other_index_1, source=source, subsector=subsector)

class DemandSubsectors(DataObject):
    _instances_by_key = {}
    _table_name = "DemandSubsectors"
    _key_col = "name"
    _cols = ["cost_of_capital", "is_active", "max_lag_hours", "max_lead_hours", "name", "sector",
             "shape"]
    _df_cols = []
    _df_filters = []
    _data_table_name = None

    def __init__(self, name, scenario):
        DataObject.__init__(self, name, scenario)

        DemandSubsectors._instances_by_key[self._key] = self

        self.cost_of_capital = None
        self.is_active = None
        self.max_lag_hours = None
        self.max_lead_hours = None
        self.name = None
        self.sector = None
        self.shape = None

    def set_args(self, scenario, cost_of_capital=None, is_active=None, max_lag_hours=None, max_lead_hours=None, name=None,
                 sector=None, shape=None):
        self.check_scenario(scenario)

        self.cost_of_capital = cost_of_capital
        self.is_active = is_active
        self.max_lag_hours = max_lag_hours
        self.max_lead_hours = max_lead_hours
        self.name = name
        self.sector = sector
        self.shape = shape

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (name, sector, cost_of_capital, is_active, shape, max_lead_hours, max_lag_hours,) = tup

        self.set_args(scenario, cost_of_capital=cost_of_capital, is_active=is_active, max_lag_hours=max_lag_hours,
                  max_lead_hours=max_lead_hours, name=name, sector=sector, shape=shape)

class DemandTechs(DataObject):
    _instances_by_key = {}
    _table_name = "DemandTechs"
    _key_col = "name"
    _cols = ["additional_description", "cost_of_capital", "demand_tech_unit_type", "lifetime_variance",
             "linked", "max_lag_hours", "max_lead_hours", "max_lifetime", "mean_lifetime",
             "min_lifetime", "name", "shape", "source", "stock_decay_function", "stock_link_ratio",
             "subsector", "time_unit", "unit"]
    _df_cols = []
    _df_filters = []
    _data_table_name = None

    def __init__(self, name, scenario):
        DataObject.__init__(self, name, scenario)

        DemandTechs._instances_by_key[self._key] = self

        self.additional_description = None
        self.cost_of_capital = None
        self.demand_tech_unit_type = None
        self.lifetime_variance = None
        self.linked = None
        self.max_lag_hours = None
        self.max_lead_hours = None
        self.max_lifetime = None
        self.mean_lifetime = None
        self.min_lifetime = None
        self.name = None
        self.shape = None
        self.source = None
        self.stock_decay_function = None
        self.stock_link_ratio = None
        self.subsector = None
        self.time_unit = None
        self.unit = None

    def set_args(self, scenario, additional_description=None, cost_of_capital=None, demand_tech_unit_type=None,
                 lifetime_variance=None, linked=None, max_lag_hours=None, max_lead_hours=None,
                 max_lifetime=None, mean_lifetime=None, min_lifetime=None, name=None, shape=None,
                 source=None, stock_decay_function=None, stock_link_ratio=None, subsector=None,
                 time_unit=None, unit=None):
        self.check_scenario(scenario)

        self.additional_description = additional_description
        self.cost_of_capital = cost_of_capital
        self.demand_tech_unit_type = demand_tech_unit_type
        self.lifetime_variance = lifetime_variance
        self.linked = linked
        self.max_lag_hours = max_lag_hours
        self.max_lead_hours = max_lead_hours
        self.max_lifetime = max_lifetime
        self.mean_lifetime = mean_lifetime
        self.min_lifetime = min_lifetime
        self.name = name
        self.shape = shape
        self.source = source
        self.stock_decay_function = stock_decay_function
        self.stock_link_ratio = stock_link_ratio
        self.subsector = subsector
        self.time_unit = time_unit
        self.unit = unit

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (name, linked, stock_link_ratio, subsector, min_lifetime, max_lifetime, source,
         additional_description, demand_tech_unit_type, unit, time_unit, cost_of_capital,
         stock_decay_function, mean_lifetime, lifetime_variance, shape, max_lead_hours,
         max_lag_hours,) = tup

        self.set_args(scenario, additional_description=additional_description, cost_of_capital=cost_of_capital,
                  demand_tech_unit_type=demand_tech_unit_type, lifetime_variance=lifetime_variance,
                  linked=linked, max_lag_hours=max_lag_hours, max_lead_hours=max_lead_hours,
                  max_lifetime=max_lifetime, mean_lifetime=mean_lifetime, min_lifetime=min_lifetime,
                  name=name, shape=shape, source=source, stock_decay_function=stock_decay_function,
                  stock_link_ratio=stock_link_ratio, subsector=subsector, time_unit=time_unit, unit=unit)

class DemandTechsAuxEfficiency(DataObject):
    _instances_by_key = {}
    _table_name = "DemandTechsAuxEfficiency"
    _key_col = "demand_technology"
    _cols = ["age_growth_or_decay", "age_growth_or_decay_type", "definition",
             "demand_tech_efficiency_types", "demand_technology", "denominator_unit",
             "extrapolation_growth", "extrapolation_method", "final_energy", "geography",
             "interpolation_method", "is_numerator_service", "notes", "numerator_unit",
             "other_index_1", "other_index_2", "reference_tech", "shape", "source"]
    _df_cols = ["vintage", "gau", "value", "oth_2", "oth_1", "sensitivity"]
    _df_filters = []
    _data_table_name = None

    def __init__(self, demand_technology, scenario):
        DataObject.__init__(self, demand_technology, scenario)

        DemandTechsAuxEfficiency._instances_by_key[self._key] = self

        self.age_growth_or_decay = None
        self.age_growth_or_decay_type = None
        self.definition = None
        self.demand_tech_efficiency_types = None
        self.demand_technology = None
        self.denominator_unit = None
        self.extrapolation_growth = None
        self.extrapolation_method = None
        self.final_energy = None
        self.geography = None
        self.interpolation_method = None
        self.is_numerator_service = None
        self.notes = None
        self.numerator_unit = None
        self.other_index_1 = None
        self.other_index_2 = None
        self.reference_tech = None
        self.shape = None
        self.source = None

    def set_args(self, scenario, age_growth_or_decay=None, age_growth_or_decay_type=None, definition=None,
                 demand_tech_efficiency_types=None, demand_technology=None, denominator_unit=None,
                 extrapolation_growth=None, extrapolation_method=None, final_energy=None, geography=None,
                 interpolation_method=None, is_numerator_service=None, notes=None, numerator_unit=None,
                 other_index_1=None, other_index_2=None, reference_tech=None, shape=None, source=None):
        self.check_scenario(scenario)

        self.age_growth_or_decay = age_growth_or_decay
        self.age_growth_or_decay_type = age_growth_or_decay_type
        self.definition = definition
        self.demand_tech_efficiency_types = demand_tech_efficiency_types
        self.demand_technology = demand_technology
        self.denominator_unit = denominator_unit
        self.extrapolation_growth = extrapolation_growth
        self.extrapolation_method = extrapolation_method
        self.final_energy = final_energy
        self.geography = geography
        self.interpolation_method = interpolation_method
        self.is_numerator_service = is_numerator_service
        self.notes = notes
        self.numerator_unit = numerator_unit
        self.other_index_1 = other_index_1
        self.other_index_2 = other_index_2
        self.reference_tech = reference_tech
        self.shape = shape
        self.source = source

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (demand_technology, definition, reference_tech, geography, other_index_1, other_index_2,
         final_energy, demand_tech_efficiency_types, is_numerator_service, numerator_unit,
         denominator_unit, interpolation_method, extrapolation_method, extrapolation_growth,
         age_growth_or_decay_type, age_growth_or_decay, shape, source, notes,) = tup

        self.set_args(scenario, age_growth_or_decay=age_growth_or_decay,
                  age_growth_or_decay_type=age_growth_or_decay_type, definition=definition,
                  demand_tech_efficiency_types=demand_tech_efficiency_types,
                  demand_technology=demand_technology, denominator_unit=denominator_unit,
                  extrapolation_growth=extrapolation_growth, extrapolation_method=extrapolation_method,
                  final_energy=final_energy, geography=geography,
                  interpolation_method=interpolation_method, is_numerator_service=is_numerator_service,
                  notes=notes, numerator_unit=numerator_unit, other_index_1=other_index_1,
                  other_index_2=other_index_2, reference_tech=reference_tech, shape=shape, source=source)

class DemandTechsCapitalCost(DataObject):
    _instances_by_key = {}
    _table_name = "DemandTechsCapitalCost"
    _key_col = "demand_technology"
    _cols = ["currency", "currency_year", "definition", "demand_technology", "extrapolation_growth",
             "extrapolation_method", "geography", "interpolation_method", "is_levelized",
             "new_or_replacement", "notes", "other_index_1", "other_index_2", "reference_tech",
             "reference_tech_operation", "source"]
    _df_cols = ["vintage", "gau", "value", "oth_2", "oth_1", "sensitivity"]
    _df_filters = []
    _data_table_name = None

    def __init__(self, demand_technology, scenario):
        DataObject.__init__(self, demand_technology, scenario)

        DemandTechsCapitalCost._instances_by_key[self._key] = self

        self.currency = None
        self.currency_year = None
        self.definition = None
        self.demand_technology = None
        self.extrapolation_growth = None
        self.extrapolation_method = None
        self.geography = None
        self.interpolation_method = None
        self.is_levelized = None
        self.new_or_replacement = None
        self.notes = None
        self.other_index_1 = None
        self.other_index_2 = None
        self.reference_tech = None
        self.reference_tech_operation = None
        self.source = None

    def set_args(self, scenario, currency=None, currency_year=None, definition=None, demand_technology=None,
                 extrapolation_growth=None, extrapolation_method=None, geography=None,
                 interpolation_method=None, is_levelized=None, new_or_replacement=None, notes=None,
                 other_index_1=None, other_index_2=None, reference_tech=None,
                 reference_tech_operation=None, source=None):
        self.check_scenario(scenario)

        self.currency = currency
        self.currency_year = currency_year
        self.definition = definition
        self.demand_technology = demand_technology
        self.extrapolation_growth = extrapolation_growth
        self.extrapolation_method = extrapolation_method
        self.geography = geography
        self.interpolation_method = interpolation_method
        self.is_levelized = is_levelized
        self.new_or_replacement = new_or_replacement
        self.notes = notes
        self.other_index_1 = other_index_1
        self.other_index_2 = other_index_2
        self.reference_tech = reference_tech
        self.reference_tech_operation = reference_tech_operation
        self.source = source

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (demand_technology, definition, reference_tech, geography, other_index_1, other_index_2,
         currency, currency_year, is_levelized, interpolation_method, extrapolation_method,
         extrapolation_growth, reference_tech_operation, source, notes, new_or_replacement,) = tup

        self.set_args(scenario, currency=currency, currency_year=currency_year, definition=definition,
                  demand_technology=demand_technology, extrapolation_growth=extrapolation_growth,
                  extrapolation_method=extrapolation_method, geography=geography,
                  interpolation_method=interpolation_method, is_levelized=is_levelized,
                  new_or_replacement=new_or_replacement, notes=notes, other_index_1=other_index_1,
                  other_index_2=other_index_2, reference_tech=reference_tech,
                  reference_tech_operation=reference_tech_operation, source=source)

class DemandTechsFixedMaintenanceCost(DataObject):
    _instances_by_key = {}
    _table_name = "DemandTechsFixedMaintenanceCost"
    _key_col = "demand_technology"
    _cols = ["additional_description", "age_growth_or_decay", "age_growth_or_decay_type", "currency",
             "currency_year", "definition", "demand_technology", "extrapolation_growth",
             "extrapolation_method", "geography", "interpolation_method", "notes", "other_index_1",
             "other_index_2", "reference_tech", "source"]
    _df_cols = ["vintage", "gau", "value", "oth_2", "oth_1", "sensitivity"]
    _df_filters = []
    _data_table_name = None

    def __init__(self, demand_technology, scenario):
        DataObject.__init__(self, demand_technology, scenario)

        DemandTechsFixedMaintenanceCost._instances_by_key[self._key] = self

        self.additional_description = None
        self.age_growth_or_decay = None
        self.age_growth_or_decay_type = None
        self.currency = None
        self.currency_year = None
        self.definition = None
        self.demand_technology = None
        self.extrapolation_growth = None
        self.extrapolation_method = None
        self.geography = None
        self.interpolation_method = None
        self.notes = None
        self.other_index_1 = None
        self.other_index_2 = None
        self.reference_tech = None
        self.source = None

    def set_args(self, scenario, additional_description=None, age_growth_or_decay=None, age_growth_or_decay_type=None,
                 currency=None, currency_year=None, definition=None, demand_technology=None,
                 extrapolation_growth=None, extrapolation_method=None, geography=None,
                 interpolation_method=None, notes=None, other_index_1=None, other_index_2=None,
                 reference_tech=None, source=None):
        self.check_scenario(scenario)

        self.additional_description = additional_description
        self.age_growth_or_decay = age_growth_or_decay
        self.age_growth_or_decay_type = age_growth_or_decay_type
        self.currency = currency
        self.currency_year = currency_year
        self.definition = definition
        self.demand_technology = demand_technology
        self.extrapolation_growth = extrapolation_growth
        self.extrapolation_method = extrapolation_method
        self.geography = geography
        self.interpolation_method = interpolation_method
        self.notes = notes
        self.other_index_1 = other_index_1
        self.other_index_2 = other_index_2
        self.reference_tech = reference_tech
        self.source = source

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (demand_technology, definition, reference_tech, geography, other_index_1, other_index_2,
         currency, currency_year, interpolation_method, extrapolation_method,
         extrapolation_growth, age_growth_or_decay_type, age_growth_or_decay,
         additional_description, source, notes,) = tup

        self.set_args(scenario, additional_description=additional_description, age_growth_or_decay=age_growth_or_decay,
                  age_growth_or_decay_type=age_growth_or_decay_type, currency=currency,
                  currency_year=currency_year, definition=definition, demand_technology=demand_technology,
                  extrapolation_growth=extrapolation_growth, extrapolation_method=extrapolation_method,
                  geography=geography, interpolation_method=interpolation_method, notes=notes,
                  other_index_1=other_index_1, other_index_2=other_index_2, reference_tech=reference_tech,
                  source=source)

class DemandTechsFuelSwitchCost(DataObject):
    _instances_by_key = {}
    _table_name = "DemandTechsFuelSwitchCost"
    _key_col = "demand_technology"
    _cols = ["currency", "currency_year", "definition", "demand_technology", "extrapolation_growth",
             "extrapolation_method", "geography", "interpolation_method", "is_levelized", "notes",
             "other_index_1", "other_index_2", "reference_tech", "source"]
    _df_cols = ["vintage", "gau", "value", "oth_2", "oth_1", "sensitivity"]
    _df_filters = []
    _data_table_name = None

    def __init__(self, demand_technology, scenario):
        DataObject.__init__(self, demand_technology, scenario)

        DemandTechsFuelSwitchCost._instances_by_key[self._key] = self

        self.currency = None
        self.currency_year = None
        self.definition = None
        self.demand_technology = None
        self.extrapolation_growth = None
        self.extrapolation_method = None
        self.geography = None
        self.interpolation_method = None
        self.is_levelized = None
        self.notes = None
        self.other_index_1 = None
        self.other_index_2 = None
        self.reference_tech = None
        self.source = None

    def set_args(self, scenario, currency=None, currency_year=None, definition=None, demand_technology=None,
                 extrapolation_growth=None, extrapolation_method=None, geography=None,
                 interpolation_method=None, is_levelized=None, notes=None, other_index_1=None,
                 other_index_2=None, reference_tech=None, source=None):
        self.check_scenario(scenario)

        self.currency = currency
        self.currency_year = currency_year
        self.definition = definition
        self.demand_technology = demand_technology
        self.extrapolation_growth = extrapolation_growth
        self.extrapolation_method = extrapolation_method
        self.geography = geography
        self.interpolation_method = interpolation_method
        self.is_levelized = is_levelized
        self.notes = notes
        self.other_index_1 = other_index_1
        self.other_index_2 = other_index_2
        self.reference_tech = reference_tech
        self.source = source

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (demand_technology, definition, reference_tech, geography, other_index_1, other_index_2,
         currency, currency_year, is_levelized, interpolation_method, extrapolation_method,
         extrapolation_growth, source, notes,) = tup

        self.set_args(scenario, currency=currency, currency_year=currency_year, definition=definition,
                  demand_technology=demand_technology, extrapolation_growth=extrapolation_growth,
                  extrapolation_method=extrapolation_method, geography=geography,
                  interpolation_method=interpolation_method, is_levelized=is_levelized, notes=notes,
                  other_index_1=other_index_1, other_index_2=other_index_2, reference_tech=reference_tech,
                  source=source)

class DemandTechsInstallationCost(DataObject):
    _instances_by_key = {}
    _table_name = "DemandTechsInstallationCost"
    _key_col = "demand_technology"
    _cols = ["currency", "currency_year", "definition", "demand_technology", "extrapolation_growth",
             "extrapolation_method", "geography", "interpolation_method", "is_levelized",
             "new_or_replacement", "notes", "other_index_1", "other_index_2", "reference_tech",
             "source"]
    _df_cols = ["vintage", "gau", "value", "oth_2", "oth_1", "sensitivity"]
    _df_filters = []
    _data_table_name = None

    def __init__(self, demand_technology, scenario):
        DataObject.__init__(self, demand_technology, scenario)

        DemandTechsInstallationCost._instances_by_key[self._key] = self

        self.currency = None
        self.currency_year = None
        self.definition = None
        self.demand_technology = None
        self.extrapolation_growth = None
        self.extrapolation_method = None
        self.geography = None
        self.interpolation_method = None
        self.is_levelized = None
        self.new_or_replacement = None
        self.notes = None
        self.other_index_1 = None
        self.other_index_2 = None
        self.reference_tech = None
        self.source = None

    def set_args(self, scenario, currency=None, currency_year=None, definition=None, demand_technology=None,
                 extrapolation_growth=None, extrapolation_method=None, geography=None,
                 interpolation_method=None, is_levelized=None, new_or_replacement=None, notes=None,
                 other_index_1=None, other_index_2=None, reference_tech=None, source=None):
        self.check_scenario(scenario)

        self.currency = currency
        self.currency_year = currency_year
        self.definition = definition
        self.demand_technology = demand_technology
        self.extrapolation_growth = extrapolation_growth
        self.extrapolation_method = extrapolation_method
        self.geography = geography
        self.interpolation_method = interpolation_method
        self.is_levelized = is_levelized
        self.new_or_replacement = new_or_replacement
        self.notes = notes
        self.other_index_1 = other_index_1
        self.other_index_2 = other_index_2
        self.reference_tech = reference_tech
        self.source = source

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (demand_technology, definition, reference_tech, geography, other_index_1, other_index_2,
         currency, currency_year, is_levelized, interpolation_method, extrapolation_method,
         extrapolation_growth, source, notes, new_or_replacement,) = tup

        self.set_args(scenario, currency=currency, currency_year=currency_year, definition=definition,
                  demand_technology=demand_technology, extrapolation_growth=extrapolation_growth,
                  extrapolation_method=extrapolation_method, geography=geography,
                  interpolation_method=interpolation_method, is_levelized=is_levelized,
                  new_or_replacement=new_or_replacement, notes=notes, other_index_1=other_index_1,
                  other_index_2=other_index_2, reference_tech=reference_tech, source=source)

class DemandTechsMainEfficiency(DataObject):
    _instances_by_key = {}
    _table_name = "DemandTechsMainEfficiency"
    _key_col = "demand_technology"
    _cols = ["age_growth_or_decay", "age_growth_or_decay_type", "definition", "demand_technology",
             "denominator_unit", "extrapolation_growth", "extrapolation_method", "final_energy",
             "geography", "geography_map_key", "interpolation_method", "is_numerator_service",
             "notes", "numerator_unit", "other_index_1", "other_index_2", "reference_tech", "source",
             "utility_factor"]
    _df_cols = ["vintage", "gau", "value", "oth_2", "oth_1", "sensitivity"]
    _df_filters = []
    _data_table_name = None

    def __init__(self, demand_technology, scenario):
        DataObject.__init__(self, demand_technology, scenario)

        DemandTechsMainEfficiency._instances_by_key[self._key] = self

        self.age_growth_or_decay = None
        self.age_growth_or_decay_type = None
        self.definition = None
        self.demand_technology = None
        self.denominator_unit = None
        self.extrapolation_growth = None
        self.extrapolation_method = None
        self.final_energy = None
        self.geography = None
        self.geography_map_key = None
        self.interpolation_method = None
        self.is_numerator_service = None
        self.notes = None
        self.numerator_unit = None
        self.other_index_1 = None
        self.other_index_2 = None
        self.reference_tech = None
        self.source = None
        self.utility_factor = None

    def set_args(self, scenario, age_growth_or_decay=None, age_growth_or_decay_type=None, definition=None,
                 demand_technology=None, denominator_unit=None, extrapolation_growth=None,
                 extrapolation_method=None, final_energy=None, geography=None, geography_map_key=None,
                 interpolation_method=None, is_numerator_service=None, notes=None, numerator_unit=None,
                 other_index_1=None, other_index_2=None, reference_tech=None, source=None,
                 utility_factor=None):
        self.check_scenario(scenario)

        self.age_growth_or_decay = age_growth_or_decay
        self.age_growth_or_decay_type = age_growth_or_decay_type
        self.definition = definition
        self.demand_technology = demand_technology
        self.denominator_unit = denominator_unit
        self.extrapolation_growth = extrapolation_growth
        self.extrapolation_method = extrapolation_method
        self.final_energy = final_energy
        self.geography = geography
        self.geography_map_key = geography_map_key
        self.interpolation_method = interpolation_method
        self.is_numerator_service = is_numerator_service
        self.notes = notes
        self.numerator_unit = numerator_unit
        self.other_index_1 = other_index_1
        self.other_index_2 = other_index_2
        self.reference_tech = reference_tech
        self.source = source
        self.utility_factor = utility_factor

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (demand_technology, definition, reference_tech, geography, other_index_1, other_index_2,
         final_energy, utility_factor, is_numerator_service, numerator_unit, denominator_unit,
         interpolation_method, extrapolation_method, extrapolation_growth,
         age_growth_or_decay_type, age_growth_or_decay, geography_map_key, source, notes,) = tup

        self.set_args(scenario, age_growth_or_decay=age_growth_or_decay,
                  age_growth_or_decay_type=age_growth_or_decay_type, definition=definition,
                  demand_technology=demand_technology, denominator_unit=denominator_unit,
                  extrapolation_growth=extrapolation_growth, extrapolation_method=extrapolation_method,
                  final_energy=final_energy, geography=geography, geography_map_key=geography_map_key,
                  interpolation_method=interpolation_method, is_numerator_service=is_numerator_service,
                  notes=notes, numerator_unit=numerator_unit, other_index_1=other_index_1,
                  other_index_2=other_index_2, reference_tech=reference_tech, source=source,
                  utility_factor=utility_factor)

class DemandTechsParasiticEnergy(DataObject):
    _instances_by_key = {}
    _table_name = "DemandTechsParasiticEnergy"
    _key_col = "demand_technology"
    _cols = ["age_growth_or_decay", "age_growth_or_decay_type", "definition", "demand_technology",
             "energy_unit", "extrapolation_growth", "extrapolation_method", "geography",
             "interpolation_method", "notes", "other_index_1", "other_index_2", "reference_tech",
             "source", "time_unit"]
    _df_cols = ["vintage", "gau", "value", "oth_2", "oth_1", "final_energy", "sensitivity"]
    _df_filters = []
    _data_table_name = None

    def __init__(self, demand_technology, scenario):
        DataObject.__init__(self, demand_technology, scenario)

        DemandTechsParasiticEnergy._instances_by_key[self._key] = self

        self.age_growth_or_decay = None
        self.age_growth_or_decay_type = None
        self.definition = None
        self.demand_technology = None
        self.energy_unit = None
        self.extrapolation_growth = None
        self.extrapolation_method = None
        self.geography = None
        self.interpolation_method = None
        self.notes = None
        self.other_index_1 = None
        self.other_index_2 = None
        self.reference_tech = None
        self.source = None
        self.time_unit = None

    def set_args(self, scenario, age_growth_or_decay=None, age_growth_or_decay_type=None, definition=None,
                 demand_technology=None, energy_unit=None, extrapolation_growth=None,
                 extrapolation_method=None, geography=None, interpolation_method=None, notes=None,
                 other_index_1=None, other_index_2=None, reference_tech=None, source=None, time_unit=None):
        self.check_scenario(scenario)

        self.age_growth_or_decay = age_growth_or_decay
        self.age_growth_or_decay_type = age_growth_or_decay_type
        self.definition = definition
        self.demand_technology = demand_technology
        self.energy_unit = energy_unit
        self.extrapolation_growth = extrapolation_growth
        self.extrapolation_method = extrapolation_method
        self.geography = geography
        self.interpolation_method = interpolation_method
        self.notes = notes
        self.other_index_1 = other_index_1
        self.other_index_2 = other_index_2
        self.reference_tech = reference_tech
        self.source = source
        self.time_unit = time_unit

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (demand_technology, definition, reference_tech, geography, other_index_1, other_index_2,
         energy_unit, time_unit, interpolation_method, extrapolation_method, extrapolation_growth,
         age_growth_or_decay_type, age_growth_or_decay, source, notes,) = tup

        self.set_args(scenario, age_growth_or_decay=age_growth_or_decay,
                  age_growth_or_decay_type=age_growth_or_decay_type, definition=definition,
                  demand_technology=demand_technology, energy_unit=energy_unit,
                  extrapolation_growth=extrapolation_growth, extrapolation_method=extrapolation_method,
                  geography=geography, interpolation_method=interpolation_method, notes=notes,
                  other_index_1=other_index_1, other_index_2=other_index_2, reference_tech=reference_tech,
                  source=source, time_unit=time_unit)

class DemandTechsServiceDemandModifier(DataObject):
    _instances_by_key = {}
    _table_name = "DemandTechsServiceDemandModifier"
    _key_col = "demand_technology"
    _cols = ["age_growth_or_decay", "age_growth_or_decay_type", "demand_technology",
             "extrapolation_growth", "extrapolation_method", "geography", "interpolation_method",
             "notes", "other_index_1", "other_index_2", "source"]
    _df_cols = ["vintage", "gau", "value", "oth_2", "oth_1", "sensitivity"]
    _df_filters = []
    _data_table_name = None

    def __init__(self, demand_technology, scenario):
        DataObject.__init__(self, demand_technology, scenario)

        DemandTechsServiceDemandModifier._instances_by_key[self._key] = self

        self.age_growth_or_decay = None
        self.age_growth_or_decay_type = None
        self.demand_technology = None
        self.extrapolation_growth = None
        self.extrapolation_method = None
        self.geography = None
        self.interpolation_method = None
        self.notes = None
        self.other_index_1 = None
        self.other_index_2 = None
        self.source = None

    def set_args(self, scenario, age_growth_or_decay=None, age_growth_or_decay_type=None, demand_technology=None,
                 extrapolation_growth=None, extrapolation_method=None, geography=None,
                 interpolation_method=None, notes=None, other_index_1=None, other_index_2=None,
                 source=None):
        self.check_scenario(scenario)

        self.age_growth_or_decay = age_growth_or_decay
        self.age_growth_or_decay_type = age_growth_or_decay_type
        self.demand_technology = demand_technology
        self.extrapolation_growth = extrapolation_growth
        self.extrapolation_method = extrapolation_method
        self.geography = geography
        self.interpolation_method = interpolation_method
        self.notes = notes
        self.other_index_1 = other_index_1
        self.other_index_2 = other_index_2
        self.source = source

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (demand_technology, geography, other_index_1, other_index_2, interpolation_method,
         extrapolation_method, extrapolation_growth, age_growth_or_decay_type,
         age_growth_or_decay, source, notes,) = tup

        self.set_args(scenario, age_growth_or_decay=age_growth_or_decay,
                  age_growth_or_decay_type=age_growth_or_decay_type, demand_technology=demand_technology,
                  extrapolation_growth=extrapolation_growth, extrapolation_method=extrapolation_method,
                  geography=geography, interpolation_method=interpolation_method, notes=notes,
                  other_index_1=other_index_1, other_index_2=other_index_2, source=source)

class DemandTechsServiceLink(DataObject):
    _instances_by_key = {}
    _table_name = "DemandTechsServiceLink"
    _key_col = "name"
    _cols = ["age_growth_or_decay", "age_growth_or_decay_type", "definition", "demand_technology",
             "extrapolation_growth", "extrapolation_method", "geography", "interpolation_method",
             "name", "notes", "other_index_1", "other_index_2", "reference", "service_link", "source"]
    _df_cols = ["vintage", "gau", "oth_1", "oth_2", "value"]
    _df_filters = []
    _data_table_name = None

    def __init__(self, name, scenario):
        DataObject.__init__(self, name, scenario)

        DemandTechsServiceLink._instances_by_key[self._key] = self

        self.age_growth_or_decay = None
        self.age_growth_or_decay_type = None
        self.definition = None
        self.demand_technology = None
        self.extrapolation_growth = None
        self.extrapolation_method = None
        self.geography = None
        self.interpolation_method = None
        self.name = None
        self.notes = None
        self.other_index_1 = None
        self.other_index_2 = None
        self.reference = None
        self.service_link = None
        self.source = None

    def set_args(self, scenario, age_growth_or_decay=None, age_growth_or_decay_type=None, definition=None,
                 demand_technology=None, extrapolation_growth=None, extrapolation_method=None,
                 geography=None, interpolation_method=None, name=None, notes=None, other_index_1=None,
                 other_index_2=None, reference=None, service_link=None, source=None):
        self.check_scenario(scenario)

        self.age_growth_or_decay = age_growth_or_decay
        self.age_growth_or_decay_type = age_growth_or_decay_type
        self.definition = definition
        self.demand_technology = demand_technology
        self.extrapolation_growth = extrapolation_growth
        self.extrapolation_method = extrapolation_method
        self.geography = geography
        self.interpolation_method = interpolation_method
        self.name = name
        self.notes = notes
        self.other_index_1 = other_index_1
        self.other_index_2 = other_index_2
        self.reference = reference
        self.service_link = service_link
        self.source = source

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (name, service_link, demand_technology, definition, reference, geography, other_index_1,
         other_index_2, interpolation_method, extrapolation_method, extrapolation_growth,
         age_growth_or_decay_type, age_growth_or_decay, source, notes,) = tup

        self.set_args(scenario, age_growth_or_decay=age_growth_or_decay,
                  age_growth_or_decay_type=age_growth_or_decay_type, definition=definition,
                  demand_technology=demand_technology, extrapolation_growth=extrapolation_growth,
                  extrapolation_method=extrapolation_method, geography=geography,
                  interpolation_method=interpolation_method, name=name, notes=notes,
                  other_index_1=other_index_1, other_index_2=other_index_2, reference=reference,
                  service_link=service_link, source=source)

class DispatchFeedersAllocation(DataObject):
    _instances_by_key = {}
    _table_name = "DispatchFeedersAllocation"
    _key_col = "name"
    _cols = ["extrapolation_method", "geography", "geography_map_key", "input_type",
             "interpolation_method", "name", "notes", "source"]
    _df_cols = ["gau", "year", "value", "dispatch_feeder", "demand_sector"]
    _df_filters = []
    _data_table_name = None

    def __init__(self, name, scenario):
        DataObject.__init__(self, name, scenario)

        DispatchFeedersAllocation._instances_by_key[self._key] = self

        self.extrapolation_method = None
        self.geography = None
        self.geography_map_key = None
        self.input_type = None
        self.interpolation_method = None
        self.name = None
        self.notes = None
        self.source = None

    def set_args(self, scenario, extrapolation_method=None, geography=None, geography_map_key=None, input_type=None,
                 interpolation_method=None, name=None, notes=None, source=None):
        self.check_scenario(scenario)

        self.extrapolation_method = extrapolation_method
        self.geography = geography
        self.geography_map_key = geography_map_key
        self.input_type = input_type
        self.interpolation_method = interpolation_method
        self.name = name
        self.notes = notes
        self.source = source

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (name, geography, geography_map_key, input_type, interpolation_method,
         extrapolation_method, source, notes,) = tup

        self.set_args(scenario, extrapolation_method=extrapolation_method, geography=geography,
                  geography_map_key=geography_map_key, input_type=input_type,
                  interpolation_method=interpolation_method, name=name, notes=notes, source=source)

class DispatchNodeConfig(DataObject):
    _instances_by_key = {}
    _table_name = "DispatchNodeConfig"
    _key_col = "supply_node"
    _cols = ["dispatch_order", "dispatch_window", "geography", "optimized", "supply_node"]
    _df_cols = []
    _df_filters = []
    _data_table_name = None

    def __init__(self, supply_node, scenario):
        DataObject.__init__(self, supply_node, scenario)

        DispatchNodeConfig._instances_by_key[self._key] = self

        self.dispatch_order = None
        self.dispatch_window = None
        self.geography = None
        self.optimized = None
        self.supply_node = None

    def set_args(self, scenario, dispatch_order=None, dispatch_window=None, geography=None, optimized=None,
                 supply_node=None):
        self.check_scenario(scenario)

        self.dispatch_order = dispatch_order
        self.dispatch_window = dispatch_window
        self.geography = geography
        self.optimized = optimized
        self.supply_node = supply_node

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (supply_node, dispatch_order, dispatch_window, geography, optimized,) = tup

        self.set_args(scenario, dispatch_order=dispatch_order, dispatch_window=dispatch_window, geography=geography,
                  optimized=optimized, supply_node=supply_node)

class DispatchTransmissionConstraint(DataObject):
    _instances_by_key = {}
    _table_name = "DispatchTransmissionConstraint"
    _key_col = "name"
    _cols = ["description", "energy_unit", "extrapolation_method", "geography_description",
             "hurdle_currency", "hurdle_currency_year", "interpolation_method", "name", "notes",
             "source", "time_zone"]
    _df_cols = ["gau_to", "gau_from", "hour", "sensitivity", "value", "month", "day_type", "year"]
    _df_filters = []
    _data_table_name = None

    def __init__(self, name, scenario):
        DataObject.__init__(self, name, scenario)

        DispatchTransmissionConstraint._instances_by_key[self._key] = self

        self.description = None
        self.energy_unit = None
        self.extrapolation_method = None
        self.geography_description = None
        self.hurdle_currency = None
        self.hurdle_currency_year = None
        self.interpolation_method = None
        self.name = None
        self.notes = None
        self.source = None
        self.time_zone = None

    def set_args(self, scenario, description=None, energy_unit=None, extrapolation_method=None, geography_description=None,
                 hurdle_currency=None, hurdle_currency_year=None, interpolation_method=None, name=None,
                 notes=None, source=None, time_zone=None):
        self.check_scenario(scenario)

        self.description = description
        self.energy_unit = energy_unit
        self.extrapolation_method = extrapolation_method
        self.geography_description = geography_description
        self.hurdle_currency = hurdle_currency
        self.hurdle_currency_year = hurdle_currency_year
        self.interpolation_method = interpolation_method
        self.name = name
        self.notes = notes
        self.source = source
        self.time_zone = time_zone

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (name, description, geography_description, time_zone, interpolation_method,
         extrapolation_method, hurdle_currency, hurdle_currency_year, energy_unit, source, notes,) = tup

        self.set_args(scenario, description=description, energy_unit=energy_unit,
                  extrapolation_method=extrapolation_method, geography_description=geography_description,
                  hurdle_currency=hurdle_currency, hurdle_currency_year=hurdle_currency_year,
                  interpolation_method=interpolation_method, name=name, notes=notes, source=source,
                  time_zone=time_zone)

class DispatchTransmissionCost(DataObject):
    _instances_by_key = {}
    _table_name = "DispatchTransmissionCost"
    _key_col = "name"
    _cols = ["capacity_or_energy_unit", "cost_incremental", "cost_of_capital", "currency",
             "currency_year", "extrapolation_method", "geography_map_key", "interpolation_method",
             "is_levelized", "lifetime", "name", "time_unit"]
    _df_cols = ["gau_to", "gau_from", "sensitivity", "value", "year"]
    _df_filters = []
    _data_table_name = None

    def __init__(self, name, scenario):
        DataObject.__init__(self, name, scenario)

        DispatchTransmissionCost._instances_by_key[self._key] = self

        self.capacity_or_energy_unit = None
        self.cost_incremental = None
        self.cost_of_capital = None
        self.currency = None
        self.currency_year = None
        self.extrapolation_method = None
        self.geography_map_key = None
        self.interpolation_method = None
        self.is_levelized = None
        self.lifetime = None
        self.name = None
        self.time_unit = None

    def set_args(self, scenario, capacity_or_energy_unit=None, cost_incremental=None, cost_of_capital=None, currency=None,
                 currency_year=None, extrapolation_method=None, geography_map_key=None,
                 interpolation_method=None, is_levelized=None, lifetime=None, name=None, time_unit=None):
        self.check_scenario(scenario)

        self.capacity_or_energy_unit = capacity_or_energy_unit
        self.cost_incremental = cost_incremental
        self.cost_of_capital = cost_of_capital
        self.currency = currency
        self.currency_year = currency_year
        self.extrapolation_method = extrapolation_method
        self.geography_map_key = geography_map_key
        self.interpolation_method = interpolation_method
        self.is_levelized = is_levelized
        self.lifetime = lifetime
        self.name = name
        self.time_unit = time_unit

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (name, currency, currency_year, capacity_or_energy_unit, interpolation_method,
         extrapolation_method, time_unit, geography_map_key, is_levelized, lifetime,
         cost_incremental, cost_of_capital,) = tup

        self.set_args(scenario, capacity_or_energy_unit=capacity_or_energy_unit, cost_incremental=cost_incremental,
                  cost_of_capital=cost_of_capital, currency=currency, currency_year=currency_year,
                  extrapolation_method=extrapolation_method, geography_map_key=geography_map_key,
                  interpolation_method=interpolation_method, is_levelized=is_levelized, lifetime=lifetime,
                  name=name, time_unit=time_unit)

class DispatchTransmissionHurdleRate(DataObject):
    _instances_by_key = {}
    _table_name = "DispatchTransmissionHurdleRate"
    _key_col = "name"
    _cols = ["energy_unit", "extrapolation_method", "interpolation_method", "name"]
    _df_cols = ["gau_to", "gau_from", "hour", "sensitivity", "value", "month", "day_type", "year"]
    _df_filters = []
    _data_table_name = None

    def __init__(self, name, scenario):
        DataObject.__init__(self, name, scenario)

        DispatchTransmissionHurdleRate._instances_by_key[self._key] = self

        self.energy_unit = None
        self.extrapolation_method = None
        self.interpolation_method = None
        self.name = None

    def set_args(self, scenario, energy_unit=None, extrapolation_method=None, interpolation_method=None, name=None):
        self.check_scenario(scenario)

        self.energy_unit = energy_unit
        self.extrapolation_method = extrapolation_method
        self.interpolation_method = interpolation_method
        self.name = name

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (name, energy_unit, interpolation_method, extrapolation_method,) = tup

        self.set_args(scenario, energy_unit=energy_unit, extrapolation_method=extrapolation_method,
                  interpolation_method=interpolation_method, name=name)

class DispatchTransmissionLosses(DataObject):
    _instances_by_key = {}
    _table_name = "DispatchTransmissionLosses"
    _key_col = "name"
    _cols = ["extrapolation_method", "interpolation_method", "name"]
    _df_cols = ["gau_to", "gau_from", "hour", "sensitivity", "value", "month", "day_type", "year"]
    _df_filters = []
    _data_table_name = None

    def __init__(self, name, scenario):
        DataObject.__init__(self, name, scenario)

        DispatchTransmissionLosses._instances_by_key[self._key] = self

        self.extrapolation_method = None
        self.interpolation_method = None
        self.name = None

    def set_args(self, scenario, extrapolation_method=None, interpolation_method=None, name=None):
        self.check_scenario(scenario)

        self.extrapolation_method = extrapolation_method
        self.interpolation_method = interpolation_method
        self.name = name

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (name, interpolation_method, extrapolation_method,) = tup

        self.set_args(scenario, extrapolation_method=extrapolation_method, interpolation_method=interpolation_method,
                  name=name)

class ImportCost(DataObject):
    _instances_by_key = {}
    _table_name = "ImportCost"
    _key_col = "import_node"
    _cols = ["cost_method", "currency", "currency_year", "denominator_unit", "extrapolation_growth",
             "extrapolation_method", "geography", "import_node", "interpolation_method", "notes",
             "source"]
    _df_cols = ["sensitivity", "demand_sector", "value", "resource_bin", "year", "gau"]
    _df_filters = []
    _data_table_name = None

    def __init__(self, import_node, scenario):
        DataObject.__init__(self, import_node, scenario)

        ImportCost._instances_by_key[self._key] = self

        self.cost_method = None
        self.currency = None
        self.currency_year = None
        self.denominator_unit = None
        self.extrapolation_growth = None
        self.extrapolation_method = None
        self.geography = None
        self.import_node = None
        self.interpolation_method = None
        self.notes = None
        self.source = None

    def set_args(self, scenario, cost_method=None, currency=None, currency_year=None, denominator_unit=None,
                 extrapolation_growth=None, extrapolation_method=None, geography=None, import_node=None,
                 interpolation_method=None, notes=None, source=None):
        self.check_scenario(scenario)

        self.cost_method = cost_method
        self.currency = currency
        self.currency_year = currency_year
        self.denominator_unit = denominator_unit
        self.extrapolation_growth = extrapolation_growth
        self.extrapolation_method = extrapolation_method
        self.geography = geography
        self.import_node = import_node
        self.interpolation_method = interpolation_method
        self.notes = notes
        self.source = source

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (import_node, source, notes, geography, currency, currency_year, denominator_unit,
         interpolation_method, extrapolation_method, extrapolation_growth, cost_method,) = tup

        self.set_args(scenario, cost_method=cost_method, currency=currency, currency_year=currency_year,
                  denominator_unit=denominator_unit, extrapolation_growth=extrapolation_growth,
                  extrapolation_method=extrapolation_method, geography=geography, import_node=import_node,
                  interpolation_method=interpolation_method, notes=notes, source=source)

class PrimaryCost(DataObject):
    _instances_by_key = {}
    _table_name = "PrimaryCost"
    _key_col = "primary_node"
    _cols = ["cost_method", "currency", "currency_year", "denominator_unit", "extrapolation_growth",
             "extrapolation_method", "geography", "interpolation_method", "notes", "other_index_1",
             "primary_node", "source"]
    _df_cols = ["sensitivity", "year", "value", "resource_bin", "oth_1", "demand_sector", "gau"]
    _df_filters = []
    _data_table_name = None

    def __init__(self, primary_node, scenario):
        DataObject.__init__(self, primary_node, scenario)

        PrimaryCost._instances_by_key[self._key] = self

        self.cost_method = None
        self.currency = None
        self.currency_year = None
        self.denominator_unit = None
        self.extrapolation_growth = None
        self.extrapolation_method = None
        self.geography = None
        self.interpolation_method = None
        self.notes = None
        self.other_index_1 = None
        self.primary_node = None
        self.source = None

    def set_args(self, scenario, cost_method=None, currency=None, currency_year=None, denominator_unit=None,
                 extrapolation_growth=None, extrapolation_method=None, geography=None,
                 interpolation_method=None, notes=None, other_index_1=None, primary_node=None, source=None):
        self.check_scenario(scenario)

        self.cost_method = cost_method
        self.currency = currency
        self.currency_year = currency_year
        self.denominator_unit = denominator_unit
        self.extrapolation_growth = extrapolation_growth
        self.extrapolation_method = extrapolation_method
        self.geography = geography
        self.interpolation_method = interpolation_method
        self.notes = notes
        self.other_index_1 = other_index_1
        self.primary_node = primary_node
        self.source = source

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (primary_node, geography, other_index_1, currency, currency_year, denominator_unit,
         interpolation_method, extrapolation_method, extrapolation_growth, cost_method, source,
         notes,) = tup

        self.set_args(scenario, cost_method=cost_method, currency=currency, currency_year=currency_year,
                  denominator_unit=denominator_unit, extrapolation_growth=extrapolation_growth,
                  extrapolation_method=extrapolation_method, geography=geography,
                  interpolation_method=interpolation_method, notes=notes, other_index_1=other_index_1,
                  primary_node=primary_node, source=source)

class StorageTechsDuration(DataObject):
    _instances_by_key = {}
    _table_name = "StorageTechsDuration"
    _key_col = "supply_tech"
    _cols = ["definition", "extrapolation_method", "geography", "interpolation_method", "notes",
             "reference_tech", "source", "supply_tech", "time_unit"]
    _df_cols = ["gau", "value", "oth_2", "oth_1", "year", "sensitivity"]
    _df_filters = []
    _data_table_name = None

    def __init__(self, supply_tech, scenario):
        DataObject.__init__(self, supply_tech, scenario)

        StorageTechsDuration._instances_by_key[self._key] = self

        self.definition = None
        self.extrapolation_method = None
        self.geography = None
        self.interpolation_method = None
        self.notes = None
        self.reference_tech = None
        self.source = None
        self.supply_tech = None
        self.time_unit = None

    def set_args(self, scenario, definition=None, extrapolation_method=None, geography=None, interpolation_method=None,
                 notes=None, reference_tech=None, source=None, supply_tech=None, time_unit=None):
        self.check_scenario(scenario)

        self.definition = definition
        self.extrapolation_method = extrapolation_method
        self.geography = geography
        self.interpolation_method = interpolation_method
        self.notes = notes
        self.reference_tech = reference_tech
        self.source = source
        self.supply_tech = supply_tech
        self.time_unit = time_unit

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (supply_tech, definition, reference_tech, geography, interpolation_method,
         extrapolation_method, time_unit, source, notes,) = tup

        self.set_args(scenario, definition=definition, extrapolation_method=extrapolation_method, geography=geography,
                  interpolation_method=interpolation_method, notes=notes, reference_tech=reference_tech,
                  source=source, supply_tech=supply_tech, time_unit=time_unit)

class SupplyCapacityFactor(DataObject):
    _instances_by_key = {}
    _table_name = "SupplyCapacityFactor"
    _key_col = "supply_node"
    _cols = ["age_growth_or_decay", "age_growth_or_decay_type", "extrapolation_growth",
             "extrapolation_method", "geography", "interpolation_method", "notes", "source",
             "supply_node", "unit"]
    _df_cols = ["gau", "demand_sector", "value", "resource_bin", "year"]
    _df_filters = []
    _data_table_name = None

    def __init__(self, supply_node, scenario):
        DataObject.__init__(self, supply_node, scenario)

        SupplyCapacityFactor._instances_by_key[self._key] = self

        self.age_growth_or_decay = None
        self.age_growth_or_decay_type = None
        self.extrapolation_growth = None
        self.extrapolation_method = None
        self.geography = None
        self.interpolation_method = None
        self.notes = None
        self.source = None
        self.supply_node = None
        self.unit = None

    def set_args(self, scenario, age_growth_or_decay=None, age_growth_or_decay_type=None, extrapolation_growth=None,
                 extrapolation_method=None, geography=None, interpolation_method=None, notes=None,
                 source=None, supply_node=None, unit=None):
        self.check_scenario(scenario)

        self.age_growth_or_decay = age_growth_or_decay
        self.age_growth_or_decay_type = age_growth_or_decay_type
        self.extrapolation_growth = extrapolation_growth
        self.extrapolation_method = extrapolation_method
        self.geography = geography
        self.interpolation_method = interpolation_method
        self.notes = notes
        self.source = source
        self.supply_node = supply_node
        self.unit = unit

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (supply_node, geography, unit, interpolation_method, extrapolation_method,
         extrapolation_growth, age_growth_or_decay_type, age_growth_or_decay, source, notes,) = tup

        self.set_args(scenario, age_growth_or_decay=age_growth_or_decay,
                  age_growth_or_decay_type=age_growth_or_decay_type,
                  extrapolation_growth=extrapolation_growth, extrapolation_method=extrapolation_method,
                  geography=geography, interpolation_method=interpolation_method, notes=notes,
                  source=source, supply_node=supply_node, unit=unit)

class SupplyCost(DataObject):
    _instances_by_key = {}
    _table_name = "SupplyCost"
    _key_col = "name"
    _cols = ["additional_notes", "book_life", "cost_of_capital", "currency", "currency_year",
             "energy_or_capacity_unit", "extrapolation_growth", "extrapolation_method", "geography",
             "interpolation_method", "is_capital_cost", "name", "notes", "source", "supply_cost_type",
             "supply_node", "throughput_correlation", "time_unit"]
    _df_cols = ["sensitivity", "demand_sector", "value", "resource_bin", "year", "gau"]
    _df_filters = []
    _data_table_name = None

    def __init__(self, name, scenario):
        DataObject.__init__(self, name, scenario)

        SupplyCost._instances_by_key[self._key] = self

        self.additional_notes = None
        self.book_life = None
        self.cost_of_capital = None
        self.currency = None
        self.currency_year = None
        self.energy_or_capacity_unit = None
        self.extrapolation_growth = None
        self.extrapolation_method = None
        self.geography = None
        self.interpolation_method = None
        self.is_capital_cost = None
        self.name = None
        self.notes = None
        self.source = None
        self.supply_cost_type = None
        self.supply_node = None
        self.throughput_correlation = None
        self.time_unit = None

    def set_args(self, scenario, additional_notes=None, book_life=None, cost_of_capital=None, currency=None,
                 currency_year=None, energy_or_capacity_unit=None, extrapolation_growth=None,
                 extrapolation_method=None, geography=None, interpolation_method=None,
                 is_capital_cost=None, name=None, notes=None, source=None, supply_cost_type=None,
                 supply_node=None, throughput_correlation=None, time_unit=None):
        self.check_scenario(scenario)

        self.additional_notes = additional_notes
        self.book_life = book_life
        self.cost_of_capital = cost_of_capital
        self.currency = currency
        self.currency_year = currency_year
        self.energy_or_capacity_unit = energy_or_capacity_unit
        self.extrapolation_growth = extrapolation_growth
        self.extrapolation_method = extrapolation_method
        self.geography = geography
        self.interpolation_method = interpolation_method
        self.is_capital_cost = is_capital_cost
        self.name = name
        self.notes = notes
        self.source = source
        self.supply_cost_type = supply_cost_type
        self.supply_node = supply_node
        self.throughput_correlation = throughput_correlation
        self.time_unit = time_unit

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (name, source, additional_notes, supply_node, geography, supply_cost_type, currency,
         currency_year, energy_or_capacity_unit, time_unit, is_capital_cost, cost_of_capital,
         book_life, throughput_correlation, interpolation_method, extrapolation_method,
         extrapolation_growth, notes,) = tup

        self.set_args(scenario, additional_notes=additional_notes, book_life=book_life, cost_of_capital=cost_of_capital,
                  currency=currency, currency_year=currency_year,
                  energy_or_capacity_unit=energy_or_capacity_unit,
                  extrapolation_growth=extrapolation_growth, extrapolation_method=extrapolation_method,
                  geography=geography, interpolation_method=interpolation_method,
                  is_capital_cost=is_capital_cost, name=name, notes=notes, source=source,
                  supply_cost_type=supply_cost_type, supply_node=supply_node,
                  throughput_correlation=throughput_correlation, time_unit=time_unit)

class SupplyEfficiency(DataObject):
    _instances_by_key = {}
    _table_name = "SupplyEfficiency"
    _key_col = "name"
    _cols = ["extrapolation_growth", "extrapolation_method", "geography", "input_unit",
             "interpolation_method", "name", "notes", "output_unit", "source"]
    _df_cols = ["efficiency_type", "sensitivity", "demand_sector", "value", "resource_bin", "year",
             "supply_node", "gau"]
    _df_filters = []
    _data_table_name = None

    def __init__(self, name, scenario):
        DataObject.__init__(self, name, scenario)

        SupplyEfficiency._instances_by_key[self._key] = self

        self.extrapolation_growth = None
        self.extrapolation_method = None
        self.geography = None
        self.input_unit = None
        self.interpolation_method = None
        self.name = None
        self.notes = None
        self.output_unit = None
        self.source = None

    def set_args(self, scenario, extrapolation_growth=None, extrapolation_method=None, geography=None, input_unit=None,
                 interpolation_method=None, name=None, notes=None, output_unit=None, source=None):
        self.check_scenario(scenario)

        self.extrapolation_growth = extrapolation_growth
        self.extrapolation_method = extrapolation_method
        self.geography = geography
        self.input_unit = input_unit
        self.interpolation_method = interpolation_method
        self.name = name
        self.notes = notes
        self.output_unit = output_unit
        self.source = source

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (name, geography, source, notes, input_unit, output_unit, interpolation_method,
         extrapolation_method, extrapolation_growth,) = tup

        self.set_args(scenario, extrapolation_growth=extrapolation_growth, extrapolation_method=extrapolation_method,
                  geography=geography, input_unit=input_unit, interpolation_method=interpolation_method,
                  name=name, notes=notes, output_unit=output_unit, source=source)

class SupplyEmissions(DataObject):
    _instances_by_key = {}
    _table_name = "SupplyEmissions"
    _key_col = "supply_node"
    _cols = ["denominator_unit", "extrapolation_growth", "extrapolation_method", "geography",
             "interpolation_method", "mass_unit", "notes", "other_index_1", "source", "supply_node"]
    _df_cols = ["gau", "demand_sector", "value", "ghg", "oth_1", "year", "sensitivity", "ghg_type"]
    _df_filters = []
    _data_table_name = None

    def __init__(self, supply_node, scenario):
        DataObject.__init__(self, supply_node, scenario)

        SupplyEmissions._instances_by_key[self._key] = self

        self.denominator_unit = None
        self.extrapolation_growth = None
        self.extrapolation_method = None
        self.geography = None
        self.interpolation_method = None
        self.mass_unit = None
        self.notes = None
        self.other_index_1 = None
        self.source = None
        self.supply_node = None

    def set_args(self, scenario, denominator_unit=None, extrapolation_growth=None, extrapolation_method=None,
                 geography=None, interpolation_method=None, mass_unit=None, notes=None,
                 other_index_1=None, source=None, supply_node=None):
        self.check_scenario(scenario)

        self.denominator_unit = denominator_unit
        self.extrapolation_growth = extrapolation_growth
        self.extrapolation_method = extrapolation_method
        self.geography = geography
        self.interpolation_method = interpolation_method
        self.mass_unit = mass_unit
        self.notes = notes
        self.other_index_1 = other_index_1
        self.source = source
        self.supply_node = supply_node

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (supply_node, geography, other_index_1, mass_unit, denominator_unit, interpolation_method,
         extrapolation_method, extrapolation_growth, source, notes,) = tup

        self.set_args(scenario, denominator_unit=denominator_unit, extrapolation_growth=extrapolation_growth,
                  extrapolation_method=extrapolation_method, geography=geography,
                  interpolation_method=interpolation_method, mass_unit=mass_unit, notes=notes,
                  other_index_1=other_index_1, source=source, supply_node=supply_node)

class SupplyExport(DataObject):
    _instances_by_key = {}
    _table_name = "SupplyExport"
    _key_col = "supply_node"
    _cols = ["extrapolation_growth", "extrapolation_method", "geography", "geography_map_key",
             "interpolation_method", "notes", "other_index_1", "sensitivity", "source", "supply_node",
             "unit"]
    _df_cols = ["gau", "value", "resource_bin", "oth_1", "year"]
    _df_filters = []
    _data_table_name = None

    def __init__(self, supply_node, scenario):
        DataObject.__init__(self, supply_node, scenario)

        SupplyExport._instances_by_key[self._key] = self

        self.extrapolation_growth = None
        self.extrapolation_method = None
        self.geography = None
        self.geography_map_key = None
        self.interpolation_method = None
        self.notes = None
        self.other_index_1 = None
        self.sensitivity = None
        self.source = None
        self.supply_node = None
        self.unit = None

    def set_args(self, scenario, extrapolation_growth=None, extrapolation_method=None, geography=None,
                 geography_map_key=None, interpolation_method=None, notes=None, other_index_1=None,
                 sensitivity=None, source=None, supply_node=None, unit=None):
        self.check_scenario(scenario)

        self.extrapolation_growth = extrapolation_growth
        self.extrapolation_method = extrapolation_method
        self.geography = geography
        self.geography_map_key = geography_map_key
        self.interpolation_method = interpolation_method
        self.notes = notes
        self.other_index_1 = other_index_1
        self.sensitivity = sensitivity
        self.source = source
        self.supply_node = supply_node
        self.unit = unit

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (supply_node, geography, other_index_1, unit, interpolation_method, extrapolation_method,
         extrapolation_growth, geography_map_key, source, notes, sensitivity,) = tup

        self.set_args(scenario, extrapolation_growth=extrapolation_growth, extrapolation_method=extrapolation_method,
                  geography=geography, geography_map_key=geography_map_key,
                  interpolation_method=interpolation_method, notes=notes, other_index_1=other_index_1,
                  sensitivity=sensitivity, source=source, supply_node=supply_node, unit=unit)

class SupplyExportMeasures(DataObject):
    _instances_by_key = {}
    _table_name = "SupplyExportMeasures"
    _key_col = "name"
    _cols = ["extrapolation_method", "geography", "interpolation_method", "name", "notes",
             "other_index_1", "source", "supply_node", "unit"]
    _df_cols = ["gau", "oth_1", "value", "year"]
    _df_filters = []
    _data_table_name = None

    def __init__(self, name, scenario):
        DataObject.__init__(self, name, scenario)

        SupplyExportMeasures._instances_by_key[self._key] = self

        self.extrapolation_method = None
        self.geography = None
        self.interpolation_method = None
        self.name = None
        self.notes = None
        self.other_index_1 = None
        self.source = None
        self.supply_node = None
        self.unit = None

    def set_args(self, scenario, extrapolation_method=None, geography=None, interpolation_method=None, name=None,
                 notes=None, other_index_1=None, source=None, supply_node=None, unit=None):
        self.check_scenario(scenario)

        self.extrapolation_method = extrapolation_method
        self.geography = geography
        self.interpolation_method = interpolation_method
        self.name = name
        self.notes = notes
        self.other_index_1 = other_index_1
        self.source = source
        self.supply_node = supply_node
        self.unit = unit

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (supply_node, name, geography, other_index_1, interpolation_method, extrapolation_method,
         unit, source, notes,) = tup

        self.set_args(scenario, extrapolation_method=extrapolation_method, geography=geography,
                  interpolation_method=interpolation_method, name=name, notes=notes,
                  other_index_1=other_index_1, source=source, supply_node=supply_node, unit=unit)

class SupplyNodes(DataObject):
    _instances_by_key = {}
    _table_name = "SupplyNodes"
    _key_col = "name"
    _cols = ["book_life", "cost_of_capital", "enforce_potential_constraint", "final_energy_link",
             "geography_map_key", "is_active", "is_curtailable", "is_exportable", "is_flexible",
             "lifetime_variance", "max_lag_hours", "max_lead_hours", "max_lifetime", "mean_lifetime",
             "min_lifetime", "name", "overflow_node", "residual_supply_node", "shape",
             "stock_decay_function", "supply_type", "tradable_geography"]
    _df_cols = []
    _df_filters = []
    _data_table_name = None

    def __init__(self, name, scenario):
        DataObject.__init__(self, name, scenario)

        SupplyNodes._instances_by_key[self._key] = self

        self.book_life = None
        self.cost_of_capital = None
        self.enforce_potential_constraint = None
        self.final_energy_link = None
        self.geography_map_key = None
        self.is_active = None
        self.is_curtailable = None
        self.is_exportable = None
        self.is_flexible = None
        self.lifetime_variance = None
        self.max_lag_hours = None
        self.max_lead_hours = None
        self.max_lifetime = None
        self.mean_lifetime = None
        self.min_lifetime = None
        self.name = None
        self.overflow_node = None
        self.residual_supply_node = None
        self.shape = None
        self.stock_decay_function = None
        self.supply_type = None
        self.tradable_geography = None

    def set_args(self, scenario, book_life=None, cost_of_capital=None, enforce_potential_constraint=None,
                 final_energy_link=None, geography_map_key=None, is_active=None, is_curtailable=None,
                 is_exportable=None, is_flexible=None, lifetime_variance=None, max_lag_hours=None,
                 max_lead_hours=None, max_lifetime=None, mean_lifetime=None, min_lifetime=None, name=None,
                 overflow_node=None, residual_supply_node=None, shape=None, stock_decay_function=None,
                 supply_type=None, tradable_geography=None):
        self.check_scenario(scenario)

        self.book_life = book_life
        self.cost_of_capital = cost_of_capital
        self.enforce_potential_constraint = enforce_potential_constraint
        self.final_energy_link = final_energy_link
        self.geography_map_key = geography_map_key
        self.is_active = is_active
        self.is_curtailable = is_curtailable
        self.is_exportable = is_exportable
        self.is_flexible = is_flexible
        self.lifetime_variance = lifetime_variance
        self.max_lag_hours = max_lag_hours
        self.max_lead_hours = max_lead_hours
        self.max_lifetime = max_lifetime
        self.mean_lifetime = mean_lifetime
        self.min_lifetime = min_lifetime
        self.name = name
        self.overflow_node = overflow_node
        self.residual_supply_node = residual_supply_node
        self.shape = shape
        self.stock_decay_function = stock_decay_function
        self.supply_type = supply_type
        self.tradable_geography = tradable_geography

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (name, supply_type, tradable_geography, is_active, final_energy_link, is_curtailable,
         is_exportable, is_flexible, residual_supply_node, mean_lifetime, lifetime_variance,
         max_lifetime, min_lifetime, stock_decay_function, cost_of_capital, book_life,
         geography_map_key, shape, max_lag_hours, max_lead_hours, enforce_potential_constraint,
         overflow_node,) = tup

        self.set_args(scenario, book_life=book_life, cost_of_capital=cost_of_capital,
                  enforce_potential_constraint=enforce_potential_constraint,
                  final_energy_link=final_energy_link, geography_map_key=geography_map_key,
                  is_active=is_active, is_curtailable=is_curtailable, is_exportable=is_exportable,
                  is_flexible=is_flexible, lifetime_variance=lifetime_variance,
                  max_lag_hours=max_lag_hours, max_lead_hours=max_lead_hours, max_lifetime=max_lifetime,
                  mean_lifetime=mean_lifetime, min_lifetime=min_lifetime, name=name,
                  overflow_node=overflow_node, residual_supply_node=residual_supply_node, shape=shape,
                  stock_decay_function=stock_decay_function, supply_type=supply_type,
                  tradable_geography=tradable_geography)

class SupplyPotential(DataObject):
    _instances_by_key = {}
    _table_name = "SupplyPotential"
    _key_col = "supply_node"
    _cols = ["extrapolation_growth", "extrapolation_method", "geography", "geography_map_key",
             "interpolation_method", "notes", "other_index_1", "source", "supply_node", "time_unit",
             "unit"]
    _df_cols = ["gau", "year", "value", "resource_bin", "oth_1", "demand_sector", "sensitivity"]
    _df_filters = []
    _data_table_name = None

    def __init__(self, supply_node, scenario):
        DataObject.__init__(self, supply_node, scenario)

        SupplyPotential._instances_by_key[self._key] = self

        self.extrapolation_growth = None
        self.extrapolation_method = None
        self.geography = None
        self.geography_map_key = None
        self.interpolation_method = None
        self.notes = None
        self.other_index_1 = None
        self.source = None
        self.supply_node = None
        self.time_unit = None
        self.unit = None

    def set_args(self, scenario, extrapolation_growth=None, extrapolation_method=None, geography=None,
                 geography_map_key=None, interpolation_method=None, notes=None, other_index_1=None,
                 source=None, supply_node=None, time_unit=None, unit=None):
        self.check_scenario(scenario)

        self.extrapolation_growth = extrapolation_growth
        self.extrapolation_method = extrapolation_method
        self.geography = geography
        self.geography_map_key = geography_map_key
        self.interpolation_method = interpolation_method
        self.notes = notes
        self.other_index_1 = other_index_1
        self.source = source
        self.supply_node = supply_node
        self.time_unit = time_unit
        self.unit = unit

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (supply_node, geography, other_index_1, unit, time_unit, interpolation_method,
         extrapolation_growth, extrapolation_method, geography_map_key, source, notes,) = tup

        self.set_args(scenario, extrapolation_growth=extrapolation_growth, extrapolation_method=extrapolation_method,
                  geography=geography, geography_map_key=geography_map_key,
                  interpolation_method=interpolation_method, notes=notes, other_index_1=other_index_1,
                  source=source, supply_node=supply_node, time_unit=time_unit, unit=unit)

class SupplyPotentialConversion(DataObject):
    _instances_by_key = {}
    _table_name = "SupplyPotentialConversion"
    _key_col = "supply_node"
    _cols = ["energy_unit_numerator", "extrapolation_growth", "extrapolation_method", "geography",
             "interpolation_method", "notes", "other_index_1", "resource_unit_denominator", "source",
             "supply_node"]
    _df_cols = ["gau", "value", "resource_bin", "oth_1", "year"]
    _df_filters = []
    _data_table_name = None

    def __init__(self, supply_node, scenario):
        DataObject.__init__(self, supply_node, scenario)

        SupplyPotentialConversion._instances_by_key[self._key] = self

        self.energy_unit_numerator = None
        self.extrapolation_growth = None
        self.extrapolation_method = None
        self.geography = None
        self.interpolation_method = None
        self.notes = None
        self.other_index_1 = None
        self.resource_unit_denominator = None
        self.source = None
        self.supply_node = None

    def set_args(self, scenario, energy_unit_numerator=None, extrapolation_growth=None, extrapolation_method=None,
                 geography=None, interpolation_method=None, notes=None, other_index_1=None,
                 resource_unit_denominator=None, source=None, supply_node=None):
        self.check_scenario(scenario)

        self.energy_unit_numerator = energy_unit_numerator
        self.extrapolation_growth = extrapolation_growth
        self.extrapolation_method = extrapolation_method
        self.geography = geography
        self.interpolation_method = interpolation_method
        self.notes = notes
        self.other_index_1 = other_index_1
        self.resource_unit_denominator = resource_unit_denominator
        self.source = source
        self.supply_node = supply_node

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (supply_node, geography, other_index_1, energy_unit_numerator, resource_unit_denominator,
         interpolation_method, extrapolation_method, extrapolation_growth, source, notes,) = tup

        self.set_args(scenario, energy_unit_numerator=energy_unit_numerator, extrapolation_growth=extrapolation_growth,
                  extrapolation_method=extrapolation_method, geography=geography,
                  interpolation_method=interpolation_method, notes=notes, other_index_1=other_index_1,
                  resource_unit_denominator=resource_unit_denominator, source=source,
                  supply_node=supply_node)

class SupplySales(DataObject):
    _instances_by_key = {}
    _table_name = "SupplySales"
    _key_col = "supply_technology"
    _cols = ["capacity_or_energy_unit", "extrapolation_growth", "extrapolation_method", "geography",
             "geography_map_key", "interpolation_method", "notes", "source", "supply_node",
             "supply_technology", "time_unit"]
    _df_cols = ["vintage", "gau", "value", "resource_bin", "demand_sector"]
    _df_filters = []
    _data_table_name = None

    def __init__(self, supply_technology, scenario):
        DataObject.__init__(self, supply_technology, scenario)

        SupplySales._instances_by_key[self._key] = self

        self.capacity_or_energy_unit = None
        self.extrapolation_growth = None
        self.extrapolation_method = None
        self.geography = None
        self.geography_map_key = None
        self.interpolation_method = None
        self.notes = None
        self.source = None
        self.supply_node = None
        self.supply_technology = None
        self.time_unit = None

    def set_args(self, scenario, capacity_or_energy_unit=None, extrapolation_growth=None, extrapolation_method=None,
                 geography=None, geography_map_key=None, interpolation_method=None, notes=None,
                 source=None, supply_node=None, supply_technology=None, time_unit=None):
        self.check_scenario(scenario)

        self.capacity_or_energy_unit = capacity_or_energy_unit
        self.extrapolation_growth = extrapolation_growth
        self.extrapolation_method = extrapolation_method
        self.geography = geography
        self.geography_map_key = geography_map_key
        self.interpolation_method = interpolation_method
        self.notes = notes
        self.source = source
        self.supply_node = supply_node
        self.supply_technology = supply_technology
        self.time_unit = time_unit

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (supply_node, geography, capacity_or_energy_unit, time_unit, interpolation_method,
         extrapolation_method, extrapolation_growth, geography_map_key, source, notes,
         supply_technology,) = tup

        self.set_args(scenario, capacity_or_energy_unit=capacity_or_energy_unit,
                  extrapolation_growth=extrapolation_growth, extrapolation_method=extrapolation_method,
                  geography=geography, geography_map_key=geography_map_key,
                  interpolation_method=interpolation_method, notes=notes, source=source,
                  supply_node=supply_node, supply_technology=supply_technology, time_unit=time_unit)

class SupplySalesMeasures(DataObject):
    _instances_by_key = {}
    _table_name = "SupplySalesMeasures"
    _key_col = "name"
    _cols = ["extrapolation_growth", "extrapolation_method", "geography", "geography_map_key",
             "interpolation_method", "name", "notes", "other_index_1", "source", "supply_node",
             "supply_technology"]
    _df_cols = ["vintage", "gau", "value", "resource_bin", "oth_1", "demand_sector"]
    _df_filters = []
    _data_table_name = None

    def __init__(self, name, scenario):
        DataObject.__init__(self, name, scenario)

        SupplySalesMeasures._instances_by_key[self._key] = self

        self.extrapolation_growth = None
        self.extrapolation_method = None
        self.geography = None
        self.geography_map_key = None
        self.interpolation_method = None
        self.name = None
        self.notes = None
        self.other_index_1 = None
        self.source = None
        self.supply_node = None
        self.supply_technology = None

    def set_args(self, scenario, extrapolation_growth=None, extrapolation_method=None, geography=None,
                 geography_map_key=None, interpolation_method=None, name=None, notes=None,
                 other_index_1=None, source=None, supply_node=None, supply_technology=None):
        self.check_scenario(scenario)

        self.extrapolation_growth = extrapolation_growth
        self.extrapolation_method = extrapolation_method
        self.geography = geography
        self.geography_map_key = geography_map_key
        self.interpolation_method = interpolation_method
        self.name = name
        self.notes = notes
        self.other_index_1 = other_index_1
        self.source = source
        self.supply_node = supply_node
        self.supply_technology = supply_technology

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (name, supply_technology, supply_node, geography, other_index_1, interpolation_method,
         extrapolation_method, extrapolation_growth, geography_map_key, source, notes,) = tup

        self.set_args(scenario, extrapolation_growth=extrapolation_growth, extrapolation_method=extrapolation_method,
                  geography=geography, geography_map_key=geography_map_key,
                  interpolation_method=interpolation_method, name=name, notes=notes,
                  other_index_1=other_index_1, source=source, supply_node=supply_node,
                  supply_technology=supply_technology)

class SupplySalesShare(DataObject):
    _instances_by_key = {}
    _table_name = "SupplySalesShare"
    _key_col = "supply_technology"
    _cols = ["extrapolation_growth", "extrapolation_method", "geography", "interpolation_method",
             "notes", "source", "supply_node", "supply_technology"]
    _df_cols = ["vintage", "gau", "value", "demand_sector"]
    _df_filters = []
    _data_table_name = None

    def __init__(self, supply_technology, scenario):
        DataObject.__init__(self, supply_technology, scenario)

        SupplySalesShare._instances_by_key[self._key] = self

        self.extrapolation_growth = None
        self.extrapolation_method = None
        self.geography = None
        self.interpolation_method = None
        self.notes = None
        self.source = None
        self.supply_node = None
        self.supply_technology = None

    def set_args(self, scenario, extrapolation_growth=None, extrapolation_method=None, geography=None,
                 interpolation_method=None, notes=None, source=None, supply_node=None,
                 supply_technology=None):
        self.check_scenario(scenario)

        self.extrapolation_growth = extrapolation_growth
        self.extrapolation_method = extrapolation_method
        self.geography = geography
        self.interpolation_method = interpolation_method
        self.notes = notes
        self.source = source
        self.supply_node = supply_node
        self.supply_technology = supply_technology

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (supply_node, geography, interpolation_method, extrapolation_method, extrapolation_growth,
         source, notes, supply_technology,) = tup

        self.set_args(scenario, extrapolation_growth=extrapolation_growth, extrapolation_method=extrapolation_method,
                  geography=geography, interpolation_method=interpolation_method, notes=notes,
                  source=source, supply_node=supply_node, supply_technology=supply_technology)

class SupplySalesShareMeasures(DataObject):
    _instances_by_key = {}
    _table_name = "SupplySalesShareMeasures"
    _key_col = "name"
    _cols = ["capacity_or_energy_unit", "extrapolation_growth", "extrapolation_method", "geography",
             "interpolation_method", "name", "notes", "other_index_1", "replaced_supply_technology",
             "source", "supply_node", "supply_technology", "time_unit"]
    _df_cols = ["vintage", "gau", "value", "resource_bin", "oth_1", "demand_sector"]
    _df_filters = []
    _data_table_name = None

    def __init__(self, name, scenario):
        DataObject.__init__(self, name, scenario)

        SupplySalesShareMeasures._instances_by_key[self._key] = self

        self.capacity_or_energy_unit = None
        self.extrapolation_growth = None
        self.extrapolation_method = None
        self.geography = None
        self.interpolation_method = None
        self.name = None
        self.notes = None
        self.other_index_1 = None
        self.replaced_supply_technology = None
        self.source = None
        self.supply_node = None
        self.supply_technology = None
        self.time_unit = None

    def set_args(self, scenario, capacity_or_energy_unit=None, extrapolation_growth=None, extrapolation_method=None,
                 geography=None, interpolation_method=None, name=None, notes=None, other_index_1=None,
                 replaced_supply_technology=None, source=None, supply_node=None, supply_technology=None,
                 time_unit=None):
        self.check_scenario(scenario)

        self.capacity_or_energy_unit = capacity_or_energy_unit
        self.extrapolation_growth = extrapolation_growth
        self.extrapolation_method = extrapolation_method
        self.geography = geography
        self.interpolation_method = interpolation_method
        self.name = name
        self.notes = notes
        self.other_index_1 = other_index_1
        self.replaced_supply_technology = replaced_supply_technology
        self.source = source
        self.supply_node = supply_node
        self.supply_technology = supply_technology
        self.time_unit = time_unit

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (name, supply_node, supply_technology, replaced_supply_technology, geography,
         capacity_or_energy_unit, time_unit, interpolation_method, extrapolation_method,
         extrapolation_growth, other_index_1, source, notes,) = tup

        self.set_args(scenario, capacity_or_energy_unit=capacity_or_energy_unit,
                  extrapolation_growth=extrapolation_growth, extrapolation_method=extrapolation_method,
                  geography=geography, interpolation_method=interpolation_method, name=name, notes=notes,
                  other_index_1=other_index_1, replaced_supply_technology=replaced_supply_technology,
                  source=source, supply_node=supply_node, supply_technology=supply_technology,
                  time_unit=time_unit)

class SupplyStock(DataObject):
    _instances_by_key = {}
    _table_name = "SupplyStock"
    _key_col = "supply_node"
    _cols = ["capacity_or_energy_unit", "extrapolation_growth", "extrapolation_method", "geography",
             "geography_map_key", "interpolation_method", "notes", "source", "supply_node",
             "time_unit"]
    _df_cols = ["sensitivity", "demand_sector", "value", "resource_bin", "year", "supply_technology",
             "gau"]
    _df_filters = []
    _data_table_name = None

    def __init__(self, supply_node, scenario):
        DataObject.__init__(self, supply_node, scenario)

        SupplyStock._instances_by_key[self._key] = self

        self.capacity_or_energy_unit = None
        self.extrapolation_growth = None
        self.extrapolation_method = None
        self.geography = None
        self.geography_map_key = None
        self.interpolation_method = None
        self.notes = None
        self.source = None
        self.supply_node = None
        self.time_unit = None

    def set_args(self, scenario, capacity_or_energy_unit=None, extrapolation_growth=None, extrapolation_method=None,
                 geography=None, geography_map_key=None, interpolation_method=None, notes=None,
                 source=None, supply_node=None, time_unit=None):
        self.check_scenario(scenario)

        self.capacity_or_energy_unit = capacity_or_energy_unit
        self.extrapolation_growth = extrapolation_growth
        self.extrapolation_method = extrapolation_method
        self.geography = geography
        self.geography_map_key = geography_map_key
        self.interpolation_method = interpolation_method
        self.notes = notes
        self.source = source
        self.supply_node = supply_node
        self.time_unit = time_unit

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (supply_node, geography, capacity_or_energy_unit, time_unit, interpolation_method,
         extrapolation_method, extrapolation_growth, geography_map_key, source, notes,) = tup

        self.set_args(scenario, capacity_or_energy_unit=capacity_or_energy_unit,
                  extrapolation_growth=extrapolation_growth, extrapolation_method=extrapolation_method,
                  geography=geography, geography_map_key=geography_map_key,
                  interpolation_method=interpolation_method, notes=notes, source=source,
                  supply_node=supply_node, time_unit=time_unit)

class SupplyStockMeasures(DataObject):
    _instances_by_key = {}
    _table_name = "SupplyStockMeasures"
    _key_col = "name"
    _cols = ["capacity_or_energy_unit", "extrapolation_growth", "extrapolation_method", "geography",
             "geography_map_key", "interpolation_method", "name", "notes", "other_index_1", "source",
             "supply_node", "supply_technology", "time_unit"]
    _df_cols = ["gau", "demand_sector", "value", "resource_bin", "oth_1", "year"]
    _df_filters = []
    _data_table_name = None

    def __init__(self, name, scenario):
        DataObject.__init__(self, name, scenario)

        SupplyStockMeasures._instances_by_key[self._key] = self

        self.capacity_or_energy_unit = None
        self.extrapolation_growth = None
        self.extrapolation_method = None
        self.geography = None
        self.geography_map_key = None
        self.interpolation_method = None
        self.name = None
        self.notes = None
        self.other_index_1 = None
        self.source = None
        self.supply_node = None
        self.supply_technology = None
        self.time_unit = None

    def set_args(self, scenario, capacity_or_energy_unit=None, extrapolation_growth=None, extrapolation_method=None,
                 geography=None, geography_map_key=None, interpolation_method=None, name=None, notes=None,
                 other_index_1=None, source=None, supply_node=None, supply_technology=None, time_unit=None):
        self.check_scenario(scenario)

        self.capacity_or_energy_unit = capacity_or_energy_unit
        self.extrapolation_growth = extrapolation_growth
        self.extrapolation_method = extrapolation_method
        self.geography = geography
        self.geography_map_key = geography_map_key
        self.interpolation_method = interpolation_method
        self.name = name
        self.notes = notes
        self.other_index_1 = other_index_1
        self.source = source
        self.supply_node = supply_node
        self.supply_technology = supply_technology
        self.time_unit = time_unit

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (name, supply_technology, supply_node, geography, other_index_1, capacity_or_energy_unit,
         time_unit, interpolation_method, extrapolation_method, extrapolation_growth,
         geography_map_key, source, notes,) = tup

        self.set_args(scenario, capacity_or_energy_unit=capacity_or_energy_unit,
                  extrapolation_growth=extrapolation_growth, extrapolation_method=extrapolation_method,
                  geography=geography, geography_map_key=geography_map_key,
                  interpolation_method=interpolation_method, name=name, notes=notes,
                  other_index_1=other_index_1, source=source, supply_node=supply_node,
                  supply_technology=supply_technology, time_unit=time_unit)

class SupplyTechs(DataObject):
    _instances_by_key = {}
    _table_name = "SupplyTechs"
    _key_col = "name"
    _cols = ["additional_description", "book_life", "cost_of_capital", "discharge_duration",
             "lifetime_variance", "max_lag_hours", "max_lead_hours", "max_lifetime", "mean_lifetime",
             "min_lifetime", "name", "shape", "source", "stock_decay_function", "supply_node",
             "thermal_capacity_multiplier"]
    _df_cols = []
    _df_filters = []
    _data_table_name = None

    def __init__(self, name, scenario):
        DataObject.__init__(self, name, scenario)

        SupplyTechs._instances_by_key[self._key] = self

        self.additional_description = None
        self.book_life = None
        self.cost_of_capital = None
        self.discharge_duration = None
        self.lifetime_variance = None
        self.max_lag_hours = None
        self.max_lead_hours = None
        self.max_lifetime = None
        self.mean_lifetime = None
        self.min_lifetime = None
        self.name = None
        self.shape = None
        self.source = None
        self.stock_decay_function = None
        self.supply_node = None
        self.thermal_capacity_multiplier = None

    def set_args(self, scenario, additional_description=None, book_life=None, cost_of_capital=None,
                 discharge_duration=None, lifetime_variance=None, max_lag_hours=None, max_lead_hours=None,
                 max_lifetime=None, mean_lifetime=None, min_lifetime=None, name=None, shape=None,
                 source=None, stock_decay_function=None, supply_node=None,
                 thermal_capacity_multiplier=None):
        self.check_scenario(scenario)

        self.additional_description = additional_description
        self.book_life = book_life
        self.cost_of_capital = cost_of_capital
        self.discharge_duration = discharge_duration
        self.lifetime_variance = lifetime_variance
        self.max_lag_hours = max_lag_hours
        self.max_lead_hours = max_lead_hours
        self.max_lifetime = max_lifetime
        self.mean_lifetime = mean_lifetime
        self.min_lifetime = min_lifetime
        self.name = name
        self.shape = shape
        self.source = source
        self.stock_decay_function = stock_decay_function
        self.supply_node = supply_node
        self.thermal_capacity_multiplier = thermal_capacity_multiplier

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (name, supply_node, source, additional_description, stock_decay_function, book_life,
         mean_lifetime, lifetime_variance, min_lifetime, max_lifetime, discharge_duration,
         cost_of_capital, shape, max_lag_hours, max_lead_hours, thermal_capacity_multiplier,) = tup

        self.set_args(scenario, additional_description=additional_description, book_life=book_life,
                  cost_of_capital=cost_of_capital, discharge_duration=discharge_duration,
                  lifetime_variance=lifetime_variance, max_lag_hours=max_lag_hours,
                  max_lead_hours=max_lead_hours, max_lifetime=max_lifetime, mean_lifetime=mean_lifetime,
                  min_lifetime=min_lifetime, name=name, shape=shape, source=source,
                  stock_decay_function=stock_decay_function, supply_node=supply_node,
                  thermal_capacity_multiplier=thermal_capacity_multiplier)

class SupplyTechsCO2Capture(DataObject):
    _instances_by_key = {}
    _table_name = "SupplyTechsCO2Capture"
    _key_col = "supply_tech"
    _cols = ["age_growth_or_decay", "age_growth_or_decay_type", "definition", "extrapolation_growth",
             "extrapolation_method", "geography", "interpolation_method", "notes", "reference_tech",
             "source", "supply_tech"]
    _df_cols = ["vintage", "gau", "resource_bin", "value"]
    _df_filters = []
    _data_table_name = None

    def __init__(self, supply_tech, scenario):
        DataObject.__init__(self, supply_tech, scenario)

        SupplyTechsCO2Capture._instances_by_key[self._key] = self

        self.age_growth_or_decay = None
        self.age_growth_or_decay_type = None
        self.definition = None
        self.extrapolation_growth = None
        self.extrapolation_method = None
        self.geography = None
        self.interpolation_method = None
        self.notes = None
        self.reference_tech = None
        self.source = None
        self.supply_tech = None

    def set_args(self, scenario, age_growth_or_decay=None, age_growth_or_decay_type=None, definition=None,
                 extrapolation_growth=None, extrapolation_method=None, geography=None,
                 interpolation_method=None, notes=None, reference_tech=None, source=None, supply_tech=None):
        self.check_scenario(scenario)

        self.age_growth_or_decay = age_growth_or_decay
        self.age_growth_or_decay_type = age_growth_or_decay_type
        self.definition = definition
        self.extrapolation_growth = extrapolation_growth
        self.extrapolation_method = extrapolation_method
        self.geography = geography
        self.interpolation_method = interpolation_method
        self.notes = notes
        self.reference_tech = reference_tech
        self.source = source
        self.supply_tech = supply_tech

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (supply_tech, definition, geography, reference_tech, interpolation_method,
         extrapolation_method, extrapolation_growth, age_growth_or_decay_type,
         age_growth_or_decay, source, notes,) = tup

        self.set_args(scenario, age_growth_or_decay=age_growth_or_decay,
                  age_growth_or_decay_type=age_growth_or_decay_type, definition=definition,
                  extrapolation_growth=extrapolation_growth, extrapolation_method=extrapolation_method,
                  geography=geography, interpolation_method=interpolation_method, notes=notes,
                  reference_tech=reference_tech, source=source, supply_tech=supply_tech)

class SupplyTechsCapacityFactor(DataObject):
    _instances_by_key = {}
    _table_name = "SupplyTechsCapacityFactor"
    _key_col = "supply_tech"
    _cols = ["age_growth_or_decay", "age_growth_or_decay_type", "definition", "extrapolation_growth",
             "extrapolation_method", "geography", "interpolation_method", "notes", "reference_tech",
             "source", "supply_tech"]
    _df_cols = ["vintage", "sensitivity", "value", "resource_bin", "oth_1", "gau"]
    _df_filters = []
    _data_table_name = None

    def __init__(self, supply_tech, scenario):
        DataObject.__init__(self, supply_tech, scenario)

        SupplyTechsCapacityFactor._instances_by_key[self._key] = self

        self.age_growth_or_decay = None
        self.age_growth_or_decay_type = None
        self.definition = None
        self.extrapolation_growth = None
        self.extrapolation_method = None
        self.geography = None
        self.interpolation_method = None
        self.notes = None
        self.reference_tech = None
        self.source = None
        self.supply_tech = None

    def set_args(self, scenario, age_growth_or_decay=None, age_growth_or_decay_type=None, definition=None,
                 extrapolation_growth=None, extrapolation_method=None, geography=None,
                 interpolation_method=None, notes=None, reference_tech=None, source=None, supply_tech=None):
        self.check_scenario(scenario)

        self.age_growth_or_decay = age_growth_or_decay
        self.age_growth_or_decay_type = age_growth_or_decay_type
        self.definition = definition
        self.extrapolation_growth = extrapolation_growth
        self.extrapolation_method = extrapolation_method
        self.geography = geography
        self.interpolation_method = interpolation_method
        self.notes = notes
        self.reference_tech = reference_tech
        self.source = source
        self.supply_tech = supply_tech

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (supply_tech, geography, reference_tech, definition, interpolation_method,
         extrapolation_method, extrapolation_growth, age_growth_or_decay_type,
         age_growth_or_decay, source, notes,) = tup

        self.set_args(scenario, age_growth_or_decay=age_growth_or_decay,
                  age_growth_or_decay_type=age_growth_or_decay_type, definition=definition,
                  extrapolation_growth=extrapolation_growth, extrapolation_method=extrapolation_method,
                  geography=geography, interpolation_method=interpolation_method, notes=notes,
                  reference_tech=reference_tech, source=source, supply_tech=supply_tech)

class SupplyTechsCapitalCost(DataObject):
    _instances_by_key = {}
    _table_name = "SupplyTechsCapitalCost"
    _key_col = "supply_tech"
    _cols = ["capacity_or_energy", "capacity_or_energy_unit", "cost_of_capital", "currency",
             "currency_year", "definition", "extrapolation_growth", "extrapolation_method",
             "geography", "geography_map_key", "interpolation_method", "is_levelized",
             "new_or_replacement", "notes", "reference_tech", "source", "supply_tech", "time_unit"]
    _df_cols = ["vintage", "sensitivity", "value", "resource_bin", "demand_sector", "gau"]
    _df_filters = []
    _data_table_name = None

    def __init__(self, supply_tech, scenario):
        DataObject.__init__(self, supply_tech, scenario)

        SupplyTechsCapitalCost._instances_by_key[self._key] = self

        self.capacity_or_energy = None
        self.capacity_or_energy_unit = None
        self.cost_of_capital = None
        self.currency = None
        self.currency_year = None
        self.definition = None
        self.extrapolation_growth = None
        self.extrapolation_method = None
        self.geography = None
        self.geography_map_key = None
        self.interpolation_method = None
        self.is_levelized = None
        self.new_or_replacement = None
        self.notes = None
        self.reference_tech = None
        self.source = None
        self.supply_tech = None
        self.time_unit = None

    def set_args(self, scenario, capacity_or_energy=None, capacity_or_energy_unit=None, cost_of_capital=None,
                 currency=None, currency_year=None, definition=None, extrapolation_growth=None,
                 extrapolation_method=None, geography=None, geography_map_key=None,
                 interpolation_method=None, is_levelized=None, new_or_replacement=None, notes=None,
                 reference_tech=None, source=None, supply_tech=None, time_unit=None):
        self.check_scenario(scenario)

        self.capacity_or_energy = capacity_or_energy
        self.capacity_or_energy_unit = capacity_or_energy_unit
        self.cost_of_capital = cost_of_capital
        self.currency = currency
        self.currency_year = currency_year
        self.definition = definition
        self.extrapolation_growth = extrapolation_growth
        self.extrapolation_method = extrapolation_method
        self.geography = geography
        self.geography_map_key = geography_map_key
        self.interpolation_method = interpolation_method
        self.is_levelized = is_levelized
        self.new_or_replacement = new_or_replacement
        self.notes = notes
        self.reference_tech = reference_tech
        self.source = source
        self.supply_tech = supply_tech
        self.time_unit = time_unit

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (supply_tech, capacity_or_energy, definition, reference_tech, geography, currency,
         currency_year, cost_of_capital, capacity_or_energy_unit, time_unit, is_levelized,
         interpolation_method, extrapolation_method, extrapolation_growth, source, notes,
         geography_map_key, new_or_replacement,) = tup

        self.set_args(scenario, capacity_or_energy=capacity_or_energy, capacity_or_energy_unit=capacity_or_energy_unit,
                  cost_of_capital=cost_of_capital, currency=currency, currency_year=currency_year,
                  definition=definition, extrapolation_growth=extrapolation_growth,
                  extrapolation_method=extrapolation_method, geography=geography,
                  geography_map_key=geography_map_key, interpolation_method=interpolation_method,
                  is_levelized=is_levelized, new_or_replacement=new_or_replacement, notes=notes,
                  reference_tech=reference_tech, source=source, supply_tech=supply_tech,
                  time_unit=time_unit)

class SupplyTechsEfficiency(DataObject):
    _instances_by_key = {}
    _table_name = "SupplyTechsEfficiency"
    _key_col = "supply_tech"
    _cols = ["age_growth_or_decay", "age_growth_or_decay_type", "definition", "extrapolation_growth",
             "extrapolation_method", "geography", "input_unit", "interpolation_method", "notes",
             "output_unit", "reference_tech", "source", "supply_tech"]
    _df_cols = ["efficiency_type", "vintage", "sensitivity", "value", "resource_bin", "demand_sector",
             "supply_node", "gau"]
    _df_filters = []
    _data_table_name = None

    def __init__(self, supply_tech, scenario):
        DataObject.__init__(self, supply_tech, scenario)

        SupplyTechsEfficiency._instances_by_key[self._key] = self

        self.age_growth_or_decay = None
        self.age_growth_or_decay_type = None
        self.definition = None
        self.extrapolation_growth = None
        self.extrapolation_method = None
        self.geography = None
        self.input_unit = None
        self.interpolation_method = None
        self.notes = None
        self.output_unit = None
        self.reference_tech = None
        self.source = None
        self.supply_tech = None

    def set_args(self, scenario, age_growth_or_decay=None, age_growth_or_decay_type=None, definition=None,
                 extrapolation_growth=None, extrapolation_method=None, geography=None, input_unit=None,
                 interpolation_method=None, notes=None, output_unit=None, reference_tech=None,
                 source=None, supply_tech=None):
        self.check_scenario(scenario)

        self.age_growth_or_decay = age_growth_or_decay
        self.age_growth_or_decay_type = age_growth_or_decay_type
        self.definition = definition
        self.extrapolation_growth = extrapolation_growth
        self.extrapolation_method = extrapolation_method
        self.geography = geography
        self.input_unit = input_unit
        self.interpolation_method = interpolation_method
        self.notes = notes
        self.output_unit = output_unit
        self.reference_tech = reference_tech
        self.source = source
        self.supply_tech = supply_tech

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (supply_tech, geography, definition, reference_tech, input_unit, output_unit,
         interpolation_method, extrapolation_method, extrapolation_growth,
         age_growth_or_decay_type, age_growth_or_decay, source, notes,) = tup

        self.set_args(scenario, age_growth_or_decay=age_growth_or_decay,
                  age_growth_or_decay_type=age_growth_or_decay_type, definition=definition,
                  extrapolation_growth=extrapolation_growth, extrapolation_method=extrapolation_method,
                  geography=geography, input_unit=input_unit, interpolation_method=interpolation_method,
                  notes=notes, output_unit=output_unit, reference_tech=reference_tech, source=source,
                  supply_tech=supply_tech)

class SupplyTechsFixedMaintenanceCost(DataObject):
    _instances_by_key = {}
    _table_name = "SupplyTechsFixedMaintenanceCost"
    _key_col = "supply_tech"
    _cols = ["age_growth_or_decay", "age_growth_or_decay_type", "capacity_or_energy_unit", "currency",
             "currency_year", "definition", "extrapolation_growth", "extrapolation_method",
             "geography", "interpolation_method", "notes", "reference_tech", "source", "supply_tech",
             "time_unit"]
    _df_cols = ["vintage", "sensitivity", "value", "resource_bin", "demand_sector", "gau"]
    _df_filters = []
    _data_table_name = None

    def __init__(self, supply_tech, scenario):
        DataObject.__init__(self, supply_tech, scenario)

        SupplyTechsFixedMaintenanceCost._instances_by_key[self._key] = self

        self.age_growth_or_decay = None
        self.age_growth_or_decay_type = None
        self.capacity_or_energy_unit = None
        self.currency = None
        self.currency_year = None
        self.definition = None
        self.extrapolation_growth = None
        self.extrapolation_method = None
        self.geography = None
        self.interpolation_method = None
        self.notes = None
        self.reference_tech = None
        self.source = None
        self.supply_tech = None
        self.time_unit = None

    def set_args(self, scenario, age_growth_or_decay=None, age_growth_or_decay_type=None, capacity_or_energy_unit=None,
                 currency=None, currency_year=None, definition=None, extrapolation_growth=None,
                 extrapolation_method=None, geography=None, interpolation_method=None, notes=None,
                 reference_tech=None, source=None, supply_tech=None, time_unit=None):
        self.check_scenario(scenario)

        self.age_growth_or_decay = age_growth_or_decay
        self.age_growth_or_decay_type = age_growth_or_decay_type
        self.capacity_or_energy_unit = capacity_or_energy_unit
        self.currency = currency
        self.currency_year = currency_year
        self.definition = definition
        self.extrapolation_growth = extrapolation_growth
        self.extrapolation_method = extrapolation_method
        self.geography = geography
        self.interpolation_method = interpolation_method
        self.notes = notes
        self.reference_tech = reference_tech
        self.source = source
        self.supply_tech = supply_tech
        self.time_unit = time_unit

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (supply_tech, definition, reference_tech, geography, currency, currency_year,
         capacity_or_energy_unit, time_unit, interpolation_method, extrapolation_method,
         extrapolation_growth, age_growth_or_decay_type, age_growth_or_decay, source, notes,) = tup

        self.set_args(scenario, age_growth_or_decay=age_growth_or_decay,
                  age_growth_or_decay_type=age_growth_or_decay_type,
                  capacity_or_energy_unit=capacity_or_energy_unit, currency=currency,
                  currency_year=currency_year, definition=definition,
                  extrapolation_growth=extrapolation_growth, extrapolation_method=extrapolation_method,
                  geography=geography, interpolation_method=interpolation_method, notes=notes,
                  reference_tech=reference_tech, source=source, supply_tech=supply_tech,
                  time_unit=time_unit)

class SupplyTechsInstallationCost(DataObject):
    _instances_by_key = {}
    _table_name = "SupplyTechsInstallationCost"
    _key_col = "supply_tech"
    _cols = ["capacity_or_energy_unit", "currency", "currency_year", "definition",
             "extrapolation_growth", "extrapolation_method", "geography", "interpolation_method",
             "is_levelized", "new_or_replacement", "notes", "reference_tech", "source", "supply_tech",
             "time_unit"]
    _df_cols = ["vintage", "sensitivity", "value", "resource_bin", "demand_sector", "gau"]
    _df_filters = []
    _data_table_name = None

    def __init__(self, supply_tech, scenario):
        DataObject.__init__(self, supply_tech, scenario)

        SupplyTechsInstallationCost._instances_by_key[self._key] = self

        self.capacity_or_energy_unit = None
        self.currency = None
        self.currency_year = None
        self.definition = None
        self.extrapolation_growth = None
        self.extrapolation_method = None
        self.geography = None
        self.interpolation_method = None
        self.is_levelized = None
        self.new_or_replacement = None
        self.notes = None
        self.reference_tech = None
        self.source = None
        self.supply_tech = None
        self.time_unit = None

    def set_args(self, scenario, capacity_or_energy_unit=None, currency=None, currency_year=None, definition=None,
                 extrapolation_growth=None, extrapolation_method=None, geography=None,
                 interpolation_method=None, is_levelized=None, new_or_replacement=None, notes=None,
                 reference_tech=None, source=None, supply_tech=None, time_unit=None):
        self.check_scenario(scenario)

        self.capacity_or_energy_unit = capacity_or_energy_unit
        self.currency = currency
        self.currency_year = currency_year
        self.definition = definition
        self.extrapolation_growth = extrapolation_growth
        self.extrapolation_method = extrapolation_method
        self.geography = geography
        self.interpolation_method = interpolation_method
        self.is_levelized = is_levelized
        self.new_or_replacement = new_or_replacement
        self.notes = notes
        self.reference_tech = reference_tech
        self.source = source
        self.supply_tech = supply_tech
        self.time_unit = time_unit

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (supply_tech, definition, geography, reference_tech, currency, currency_year,
         capacity_or_energy_unit, time_unit, is_levelized, interpolation_method,
         extrapolation_method, extrapolation_growth, source, notes, new_or_replacement,) = tup

        self.set_args(scenario, capacity_or_energy_unit=capacity_or_energy_unit, currency=currency,
                  currency_year=currency_year, definition=definition,
                  extrapolation_growth=extrapolation_growth, extrapolation_method=extrapolation_method,
                  geography=geography, interpolation_method=interpolation_method,
                  is_levelized=is_levelized, new_or_replacement=new_or_replacement, notes=notes,
                  reference_tech=reference_tech, source=source, supply_tech=supply_tech,
                  time_unit=time_unit)

class SupplyTechsVariableMaintenanceCost(DataObject):
    _instances_by_key = {}
    _table_name = "SupplyTechsVariableMaintenanceCost"
    _key_col = "supply_tech"
    _cols = ["age_growth_or_decay", "age_growth_or_decay_type", "currency", "currency_year",
             "definition", "energy_unit", "extrapolation_growth", "extrapolation_method", "geography",
             "interpolation_method", "notes", "reference_tech", "source", "supply_tech"]
    _df_cols = ["vintage", "sensitivity", "value", "resource_bin", "demand_sector", "gau"]
    _df_filters = []
    _data_table_name = None

    def __init__(self, supply_tech, scenario):
        DataObject.__init__(self, supply_tech, scenario)

        SupplyTechsVariableMaintenanceCost._instances_by_key[self._key] = self

        self.age_growth_or_decay = None
        self.age_growth_or_decay_type = None
        self.currency = None
        self.currency_year = None
        self.definition = None
        self.energy_unit = None
        self.extrapolation_growth = None
        self.extrapolation_method = None
        self.geography = None
        self.interpolation_method = None
        self.notes = None
        self.reference_tech = None
        self.source = None
        self.supply_tech = None

    def set_args(self, scenario, age_growth_or_decay=None, age_growth_or_decay_type=None, currency=None,
                 currency_year=None, definition=None, energy_unit=None, extrapolation_growth=None,
                 extrapolation_method=None, geography=None, interpolation_method=None, notes=None,
                 reference_tech=None, source=None, supply_tech=None):
        self.check_scenario(scenario)

        self.age_growth_or_decay = age_growth_or_decay
        self.age_growth_or_decay_type = age_growth_or_decay_type
        self.currency = currency
        self.currency_year = currency_year
        self.definition = definition
        self.energy_unit = energy_unit
        self.extrapolation_growth = extrapolation_growth
        self.extrapolation_method = extrapolation_method
        self.geography = geography
        self.interpolation_method = interpolation_method
        self.notes = notes
        self.reference_tech = reference_tech
        self.source = source
        self.supply_tech = supply_tech

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (supply_tech, definition, reference_tech, currency, geography, currency_year, energy_unit,
         interpolation_method, extrapolation_method, extrapolation_growth,
         age_growth_or_decay_type, age_growth_or_decay, source, notes,) = tup

        self.set_args(scenario, age_growth_or_decay=age_growth_or_decay,
                  age_growth_or_decay_type=age_growth_or_decay_type, currency=currency,
                  currency_year=currency_year, definition=definition, energy_unit=energy_unit,
                  extrapolation_growth=extrapolation_growth, extrapolation_method=extrapolation_method,
                  geography=geography, interpolation_method=interpolation_method, notes=notes,
                  reference_tech=reference_tech, source=source, supply_tech=supply_tech)

