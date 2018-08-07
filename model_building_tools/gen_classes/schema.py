#
# This is a generated file. Manual edits may be lost!
#
import sys
from energyPATHWAYS.error import UnknownDataClass
from energyPATHWAYS.data_object import DataObject

_Module = sys.modules[__name__]  # get ref to our own module object

def class_for_table(tbl_name):
    try:
        cls = getattr(_Module, tbl_name)
    except AttributeError:
        raise UnknownDataClass(tbl_name)

    return cls

class Agriculture(DataObject):
    _instances_by_key = {}
    _key_col = "parent"
    _cols = ["parent", "gau", "dispatch_feeder", "resource_bin", "dispatch_constraint", "year",
             "month", "week", "hour", "day_type", "weather_datetime", "value", "id"]
    _table_name = "Agriculture"
    _data_table_name = None

    def __init__(self, parent, scenario):
        DataObject.__init__(self, parent, scenario)

        Agriculture._instances_by_key[self._key] = self

        self.parent = None
        self.gau = None
        self.dispatch_feeder = None
        self.resource_bin = None
        self.dispatch_constraint = None
        self.year = None
        self.month = None
        self.week = None
        self.hour = None
        self.day_type = None
        self.weather_datetime = None
        self.value = None
        self.id = None

    def set_args(self, scenario, parent=None, gau=None, dispatch_feeder=None, resource_bin=None, dispatch_constraint=None,
                 year=None, month=None, week=None, hour=None, day_type=None, weather_datetime=None,
                 value=None, id=None):
        self.parent = parent
        self.gau = gau
        self.dispatch_feeder = dispatch_feeder
        self.resource_bin = resource_bin
        self.dispatch_constraint = dispatch_constraint
        self.year = year
        self.month = month
        self.week = week
        self.hour = hour
        self.day_type = day_type
        self.weather_datetime = weather_datetime
        self.value = value
        self.id = id

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (parent, gau, dispatch_feeder, resource_bin, dispatch_constraint, year, month, week, hour,
         day_type, weather_datetime, value, id) = tup

        self.set_args(scenario, parent=parent, gau=gau, dispatch_feeder=dispatch_feeder, resource_bin=resource_bin,
                  dispatch_constraint=dispatch_constraint, year=year, month=month, week=week, hour=hour,
                  day_type=day_type, weather_datetime=weather_datetime, value=value, id=id)

class BPA_Imports_CA(DataObject):
    _instances_by_key = {}
    _key_col = "parent"
    _cols = ["parent", "gau", "dispatch_feeder", "resource_bin", "dispatch_constraint", "year",
             "month", "week", "hour", "day_type", "weather_datetime", "value", "id"]
    _table_name = "BPA_Imports_CA"
    _data_table_name = None

    def __init__(self, parent, scenario):
        DataObject.__init__(self, parent, scenario)

        BPA_Imports_CA._instances_by_key[self._key] = self

        self.parent = None
        self.gau = None
        self.dispatch_feeder = None
        self.resource_bin = None
        self.dispatch_constraint = None
        self.year = None
        self.month = None
        self.week = None
        self.hour = None
        self.day_type = None
        self.weather_datetime = None
        self.value = None
        self.id = None

    def set_args(self, scenario, parent=None, gau=None, dispatch_feeder=None, resource_bin=None, dispatch_constraint=None,
                 year=None, month=None, week=None, hour=None, day_type=None, weather_datetime=None,
                 value=None, id=None):
        self.parent = parent
        self.gau = gau
        self.dispatch_feeder = dispatch_feeder
        self.resource_bin = resource_bin
        self.dispatch_constraint = dispatch_constraint
        self.year = year
        self.month = month
        self.week = week
        self.hour = hour
        self.day_type = day_type
        self.weather_datetime = weather_datetime
        self.value = value
        self.id = id

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (parent, gau, dispatch_feeder, resource_bin, dispatch_constraint, year, month, week, hour,
         day_type, weather_datetime, value, id) = tup

        self.set_args(scenario, parent=parent, gau=gau, dispatch_feeder=dispatch_feeder, resource_bin=resource_bin,
                  dispatch_constraint=dispatch_constraint, year=year, month=month, week=week, hour=hour,
                  day_type=day_type, weather_datetime=weather_datetime, value=value, id=id)

class BlendNodeBlendMeasures(DataObject):
    _instances_by_key = {}
    _key_col = "name"
    _cols = ["name", "blend_node", "supply_node", "geography", "other_index_1", "interpolation_method",
             "extrapolation_method", "extrapolation_growth"]
    _table_name = "BlendNodeBlendMeasures"
    _data_table_name = 'BlendNodeBlendMeasuresData'

    def __init__(self, name, scenario):
        DataObject.__init__(self, name, scenario)

        BlendNodeBlendMeasures._instances_by_key[self._key] = self

        self.name = None
        self.blend_node = None
        self.supply_node = None
        self.geography = None
        self.other_index_1 = None
        self.interpolation_method = None
        self.extrapolation_method = None
        self.extrapolation_growth = None

    def set_args(self, scenario, name=None, blend_node=None, supply_node=None, geography=None, other_index_1=None,
                 interpolation_method=None, extrapolation_method=None, extrapolation_growth=None):
        self.name = name
        self.blend_node = blend_node
        self.supply_node = supply_node
        self.geography = geography
        self.other_index_1 = other_index_1
        self.interpolation_method = interpolation_method
        self.extrapolation_method = extrapolation_method
        self.extrapolation_growth = extrapolation_growth

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (name, blend_node, supply_node, geography, other_index_1, interpolation_method,
         extrapolation_method, extrapolation_growth) = tup

        self.set_args(scenario, name=name, blend_node=blend_node, supply_node=supply_node, geography=geography,
                  other_index_1=other_index_1, interpolation_method=interpolation_method,
                  extrapolation_method=extrapolation_method, extrapolation_growth=extrapolation_growth)

class CO2PriceMeasures(DataObject):
    _instances_by_key = {}
    _key_col = "name"
    _cols = ["name", "geography", "interpolation_method", "extrapolation_method",
             "extrapolation_growth", "geography_map_key", "supply_node"]
    _table_name = "CO2PriceMeasures"
    _data_table_name = 'CO2PriceMeasuresData'

    def __init__(self, name, scenario):
        DataObject.__init__(self, name, scenario)

        CO2PriceMeasures._instances_by_key[self._key] = self

        self.name = None
        self.geography = None
        self.interpolation_method = None
        self.extrapolation_method = None
        self.extrapolation_growth = None
        self.geography_map_key = None
        self.supply_node = None

    def set_args(self, scenario, name=None, geography=None, interpolation_method=None, extrapolation_method=None,
                 extrapolation_growth=None, geography_map_key=None, supply_node=None):
        self.name = name
        self.geography = geography
        self.interpolation_method = interpolation_method
        self.extrapolation_method = extrapolation_method
        self.extrapolation_growth = extrapolation_growth
        self.geography_map_key = geography_map_key
        self.supply_node = supply_node

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (name, geography, interpolation_method, extrapolation_method, extrapolation_growth,
         geography_map_key, supply_node) = tup

        self.set_args(scenario, name=name, geography=geography, interpolation_method=interpolation_method,
                  extrapolation_method=extrapolation_method, extrapolation_growth=extrapolation_growth,
                  geography_map_key=geography_map_key, supply_node=supply_node)

class Commercial_Cooking(DataObject):
    _instances_by_key = {}
    _key_col = "parent"
    _cols = ["parent", "gau", "dispatch_feeder", "resource_bin", "dispatch_constraint", "year",
             "month", "week", "hour", "day_type", "weather_datetime", "value", "id"]
    _table_name = "Commercial_Cooking"
    _data_table_name = None

    def __init__(self, parent, scenario):
        DataObject.__init__(self, parent, scenario)

        Commercial_Cooking._instances_by_key[self._key] = self

        self.parent = None
        self.gau = None
        self.dispatch_feeder = None
        self.resource_bin = None
        self.dispatch_constraint = None
        self.year = None
        self.month = None
        self.week = None
        self.hour = None
        self.day_type = None
        self.weather_datetime = None
        self.value = None
        self.id = None

    def set_args(self, scenario, parent=None, gau=None, dispatch_feeder=None, resource_bin=None, dispatch_constraint=None,
                 year=None, month=None, week=None, hour=None, day_type=None, weather_datetime=None,
                 value=None, id=None):
        self.parent = parent
        self.gau = gau
        self.dispatch_feeder = dispatch_feeder
        self.resource_bin = resource_bin
        self.dispatch_constraint = dispatch_constraint
        self.year = year
        self.month = month
        self.week = week
        self.hour = hour
        self.day_type = day_type
        self.weather_datetime = weather_datetime
        self.value = value
        self.id = id

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (parent, gau, dispatch_feeder, resource_bin, dispatch_constraint, year, month, week, hour,
         day_type, weather_datetime, value, id) = tup

        self.set_args(scenario, parent=parent, gau=gau, dispatch_feeder=dispatch_feeder, resource_bin=resource_bin,
                  dispatch_constraint=dispatch_constraint, year=year, month=month, week=week, hour=hour,
                  day_type=day_type, weather_datetime=weather_datetime, value=value, id=id)

class Commercial_LightingInternal(DataObject):
    _instances_by_key = {}
    _key_col = "parent"
    _cols = ["parent", "gau", "dispatch_feeder", "resource_bin", "dispatch_constraint", "year",
             "month", "week", "hour", "day_type", "weather_datetime", "value", "id"]
    _table_name = "Commercial_LightingInternal"
    _data_table_name = None

    def __init__(self, parent, scenario):
        DataObject.__init__(self, parent, scenario)

        Commercial_LightingInternal._instances_by_key[self._key] = self

        self.parent = None
        self.gau = None
        self.dispatch_feeder = None
        self.resource_bin = None
        self.dispatch_constraint = None
        self.year = None
        self.month = None
        self.week = None
        self.hour = None
        self.day_type = None
        self.weather_datetime = None
        self.value = None
        self.id = None

    def set_args(self, scenario, parent=None, gau=None, dispatch_feeder=None, resource_bin=None, dispatch_constraint=None,
                 year=None, month=None, week=None, hour=None, day_type=None, weather_datetime=None,
                 value=None, id=None):
        self.parent = parent
        self.gau = gau
        self.dispatch_feeder = dispatch_feeder
        self.resource_bin = resource_bin
        self.dispatch_constraint = dispatch_constraint
        self.year = year
        self.month = month
        self.week = week
        self.hour = hour
        self.day_type = day_type
        self.weather_datetime = weather_datetime
        self.value = value
        self.id = id

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (parent, gau, dispatch_feeder, resource_bin, dispatch_constraint, year, month, week, hour,
         day_type, weather_datetime, value, id) = tup

        self.set_args(scenario, parent=parent, gau=gau, dispatch_feeder=dispatch_feeder, resource_bin=resource_bin,
                  dispatch_constraint=dispatch_constraint, year=year, month=month, week=week, hour=hour,
                  day_type=day_type, weather_datetime=weather_datetime, value=value, id=id)

class Commercial_OfficeEquipment(DataObject):
    _instances_by_key = {}
    _key_col = "parent"
    _cols = ["parent", "gau", "dispatch_feeder", "resource_bin", "dispatch_constraint", "year",
             "month", "week", "hour", "day_type", "weather_datetime", "value", "id"]
    _table_name = "Commercial_OfficeEquipment"
    _data_table_name = None

    def __init__(self, parent, scenario):
        DataObject.__init__(self, parent, scenario)

        Commercial_OfficeEquipment._instances_by_key[self._key] = self

        self.parent = None
        self.gau = None
        self.dispatch_feeder = None
        self.resource_bin = None
        self.dispatch_constraint = None
        self.year = None
        self.month = None
        self.week = None
        self.hour = None
        self.day_type = None
        self.weather_datetime = None
        self.value = None
        self.id = None

    def set_args(self, scenario, parent=None, gau=None, dispatch_feeder=None, resource_bin=None, dispatch_constraint=None,
                 year=None, month=None, week=None, hour=None, day_type=None, weather_datetime=None,
                 value=None, id=None):
        self.parent = parent
        self.gau = gau
        self.dispatch_feeder = dispatch_feeder
        self.resource_bin = resource_bin
        self.dispatch_constraint = dispatch_constraint
        self.year = year
        self.month = month
        self.week = week
        self.hour = hour
        self.day_type = day_type
        self.weather_datetime = weather_datetime
        self.value = value
        self.id = id

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (parent, gau, dispatch_feeder, resource_bin, dispatch_constraint, year, month, week, hour,
         day_type, weather_datetime, value, id) = tup

        self.set_args(scenario, parent=parent, gau=gau, dispatch_feeder=dispatch_feeder, resource_bin=resource_bin,
                  dispatch_constraint=dispatch_constraint, year=year, month=month, week=week, hour=hour,
                  day_type=day_type, weather_datetime=weather_datetime, value=value, id=id)

class Commercial_Refrigeration(DataObject):
    _instances_by_key = {}
    _key_col = "parent"
    _cols = ["parent", "gau", "dispatch_feeder", "resource_bin", "dispatch_constraint", "year",
             "month", "week", "hour", "day_type", "weather_datetime", "value", "id"]
    _table_name = "Commercial_Refrigeration"
    _data_table_name = None

    def __init__(self, parent, scenario):
        DataObject.__init__(self, parent, scenario)

        Commercial_Refrigeration._instances_by_key[self._key] = self

        self.parent = None
        self.gau = None
        self.dispatch_feeder = None
        self.resource_bin = None
        self.dispatch_constraint = None
        self.year = None
        self.month = None
        self.week = None
        self.hour = None
        self.day_type = None
        self.weather_datetime = None
        self.value = None
        self.id = None

    def set_args(self, scenario, parent=None, gau=None, dispatch_feeder=None, resource_bin=None, dispatch_constraint=None,
                 year=None, month=None, week=None, hour=None, day_type=None, weather_datetime=None,
                 value=None, id=None):
        self.parent = parent
        self.gau = gau
        self.dispatch_feeder = dispatch_feeder
        self.resource_bin = resource_bin
        self.dispatch_constraint = dispatch_constraint
        self.year = year
        self.month = month
        self.week = week
        self.hour = hour
        self.day_type = day_type
        self.weather_datetime = weather_datetime
        self.value = value
        self.id = id

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (parent, gau, dispatch_feeder, resource_bin, dispatch_constraint, year, month, week, hour,
         day_type, weather_datetime, value, id) = tup

        self.set_args(scenario, parent=parent, gau=gau, dispatch_feeder=dispatch_feeder, resource_bin=resource_bin,
                  dispatch_constraint=dispatch_constraint, year=year, month=month, week=week, hour=hour,
                  day_type=day_type, weather_datetime=weather_datetime, value=value, id=id)

class Commercial_Ventilation(DataObject):
    _instances_by_key = {}
    _key_col = "parent"
    _cols = ["parent", "gau", "dispatch_feeder", "resource_bin", "dispatch_constraint", "year",
             "month", "week", "hour", "day_type", "weather_datetime", "value", "id"]
    _table_name = "Commercial_Ventilation"
    _data_table_name = None

    def __init__(self, parent, scenario):
        DataObject.__init__(self, parent, scenario)

        Commercial_Ventilation._instances_by_key[self._key] = self

        self.parent = None
        self.gau = None
        self.dispatch_feeder = None
        self.resource_bin = None
        self.dispatch_constraint = None
        self.year = None
        self.month = None
        self.week = None
        self.hour = None
        self.day_type = None
        self.weather_datetime = None
        self.value = None
        self.id = None

    def set_args(self, scenario, parent=None, gau=None, dispatch_feeder=None, resource_bin=None, dispatch_constraint=None,
                 year=None, month=None, week=None, hour=None, day_type=None, weather_datetime=None,
                 value=None, id=None):
        self.parent = parent
        self.gau = gau
        self.dispatch_feeder = dispatch_feeder
        self.resource_bin = resource_bin
        self.dispatch_constraint = dispatch_constraint
        self.year = year
        self.month = month
        self.week = week
        self.hour = hour
        self.day_type = day_type
        self.weather_datetime = weather_datetime
        self.value = value
        self.id = id

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (parent, gau, dispatch_feeder, resource_bin, dispatch_constraint, year, month, week, hour,
         day_type, weather_datetime, value, id) = tup

        self.set_args(scenario, parent=parent, gau=gau, dispatch_feeder=dispatch_feeder, resource_bin=resource_bin,
                  dispatch_constraint=dispatch_constraint, year=year, month=month, week=week, hour=hour,
                  day_type=day_type, weather_datetime=weather_datetime, value=value, id=id)

class Commercial_WaterHeating(DataObject):
    _instances_by_key = {}
    _key_col = "parent"
    _cols = ["parent", "gau", "dispatch_feeder", "resource_bin", "dispatch_constraint", "year",
             "month", "week", "hour", "day_type", "weather_datetime", "value", "id"]
    _table_name = "Commercial_WaterHeating"
    _data_table_name = None

    def __init__(self, parent, scenario):
        DataObject.__init__(self, parent, scenario)

        Commercial_WaterHeating._instances_by_key[self._key] = self

        self.parent = None
        self.gau = None
        self.dispatch_feeder = None
        self.resource_bin = None
        self.dispatch_constraint = None
        self.year = None
        self.month = None
        self.week = None
        self.hour = None
        self.day_type = None
        self.weather_datetime = None
        self.value = None
        self.id = None

    def set_args(self, scenario, parent=None, gau=None, dispatch_feeder=None, resource_bin=None, dispatch_constraint=None,
                 year=None, month=None, week=None, hour=None, day_type=None, weather_datetime=None,
                 value=None, id=None):
        self.parent = parent
        self.gau = gau
        self.dispatch_feeder = dispatch_feeder
        self.resource_bin = resource_bin
        self.dispatch_constraint = dispatch_constraint
        self.year = year
        self.month = month
        self.week = week
        self.hour = hour
        self.day_type = day_type
        self.weather_datetime = weather_datetime
        self.value = value
        self.id = id

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (parent, gau, dispatch_feeder, resource_bin, dispatch_constraint, year, month, week, hour,
         day_type, weather_datetime, value, id) = tup

        self.set_args(scenario, parent=parent, gau=gau, dispatch_feeder=dispatch_feeder, resource_bin=resource_bin,
                  dispatch_constraint=dispatch_constraint, year=year, month=month, week=week, hour=hour,
                  day_type=day_type, weather_datetime=weather_datetime, value=value, id=id)

class DemandCO2CaptureMeasures(DataObject):
    _instances_by_key = {}
    _key_col = "name"
    _cols = ["name", "subsector", "input_type", "unit", "geography", "other_index_1", "other_index_2",
             "interpolation_method", "extrapolation_method", "extrapolation_growth",
             "stock_decay_function", "min_lifetime", "max_lifetime", "mean_lifetime",
             "lifetime_variance"]
    _table_name = "DemandCO2CaptureMeasures"
    _data_table_name = None

    def __init__(self, name, scenario):
        DataObject.__init__(self, name, scenario)

        DemandCO2CaptureMeasures._instances_by_key[self._key] = self

        self.name = None
        self.subsector = None
        self.input_type = None
        self.unit = None
        self.geography = None
        self.other_index_1 = None
        self.other_index_2 = None
        self.interpolation_method = None
        self.extrapolation_method = None
        self.extrapolation_growth = None
        self.stock_decay_function = None
        self.min_lifetime = None
        self.max_lifetime = None
        self.mean_lifetime = None
        self.lifetime_variance = None

    def set_args(self, scenario, name=None, subsector=None, input_type=None, unit=None, geography=None, other_index_1=None,
                 other_index_2=None, interpolation_method=None, extrapolation_method=None,
                 extrapolation_growth=None, stock_decay_function=None, min_lifetime=None,
                 max_lifetime=None, mean_lifetime=None, lifetime_variance=None):
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

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (name, subsector, input_type, unit, geography, other_index_1, other_index_2,
         interpolation_method, extrapolation_method, extrapolation_growth, stock_decay_function,
         min_lifetime, max_lifetime, mean_lifetime, lifetime_variance) = tup

        self.set_args(scenario, name=name, subsector=subsector, input_type=input_type, unit=unit, geography=geography,
                  other_index_1=other_index_1, other_index_2=other_index_2,
                  interpolation_method=interpolation_method, extrapolation_method=extrapolation_method,
                  extrapolation_growth=extrapolation_growth, stock_decay_function=stock_decay_function,
                  min_lifetime=min_lifetime, max_lifetime=max_lifetime, mean_lifetime=mean_lifetime,
                  lifetime_variance=lifetime_variance)

class DemandDrivers(DataObject):
    _instances_by_key = {}
    _key_col = "name"
    _cols = ["name", "base_driver", "input_type", "unit_prefix", "unit_base", "geography",
             "other_index_1", "other_index_2", "geography_map_key", "interpolation_method",
             "extrapolation_method", "extrapolation_growth", "source"]
    _table_name = "DemandDrivers"
    _data_table_name = 'DemandDriversData'

    def __init__(self, name, scenario):
        DataObject.__init__(self, name, scenario)

        DemandDrivers._instances_by_key[self._key] = self

        self.name = None
        self.base_driver = None
        self.input_type = None
        self.unit_prefix = None
        self.unit_base = None
        self.geography = None
        self.other_index_1 = None
        self.other_index_2 = None
        self.geography_map_key = None
        self.interpolation_method = None
        self.extrapolation_method = None
        self.extrapolation_growth = None
        self.source = None

    def set_args(self, scenario, name=None, base_driver=None, input_type=None, unit_prefix=None, unit_base=None,
                 geography=None, other_index_1=None, other_index_2=None, geography_map_key=None,
                 interpolation_method=None, extrapolation_method=None, extrapolation_growth=None,
                 source=None):
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

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (name, base_driver, input_type, unit_prefix, unit_base, geography, other_index_1,
         other_index_2, geography_map_key, interpolation_method, extrapolation_method,
         extrapolation_growth, source) = tup

        self.set_args(scenario, name=name, base_driver=base_driver, input_type=input_type, unit_prefix=unit_prefix,
                  unit_base=unit_base, geography=geography, other_index_1=other_index_1,
                  other_index_2=other_index_2, geography_map_key=geography_map_key,
                  interpolation_method=interpolation_method, extrapolation_method=extrapolation_method,
                  extrapolation_growth=extrapolation_growth, source=source)

class DemandEnergyDemands(DataObject):
    _instances_by_key = {}
    _key_col = "subsector"
    _cols = ["subsector", "is_stock_dependent", "input_type", "unit", "driver_denominator_1",
             "driver_denominator_2", "driver_1", "driver_2", "geography", "final_energy_index",
             "demand_technology_index", "other_index_1", "other_index_2", "interpolation_method",
             "extrapolation_method", "extrapolation_growth", "geography_map_key"]
    _table_name = "DemandEnergyDemands"
    _data_table_name = 'DemandEnergyDemandsData'

    def __init__(self, subsector, scenario):
        DataObject.__init__(self, subsector, scenario)

        DemandEnergyDemands._instances_by_key[self._key] = self

        self.subsector = None
        self.is_stock_dependent = None
        self.input_type = None
        self.unit = None
        self.driver_denominator_1 = None
        self.driver_denominator_2 = None
        self.driver_1 = None
        self.driver_2 = None
        self.geography = None
        self.final_energy_index = None
        self.demand_technology_index = None
        self.other_index_1 = None
        self.other_index_2 = None
        self.interpolation_method = None
        self.extrapolation_method = None
        self.extrapolation_growth = None
        self.geography_map_key = None

    def set_args(self, scenario, subsector=None, is_stock_dependent=None, input_type=None, unit=None,
                 driver_denominator_1=None, driver_denominator_2=None, driver_1=None, driver_2=None,
                 geography=None, final_energy_index=None, demand_technology_index=None,
                 other_index_1=None, other_index_2=None, interpolation_method=None,
                 extrapolation_method=None, extrapolation_growth=None, geography_map_key=None):
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

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (subsector, is_stock_dependent, input_type, unit, driver_denominator_1,
         driver_denominator_2, driver_1, driver_2, geography, final_energy_index,
         demand_technology_index, other_index_1, other_index_2, interpolation_method,
         extrapolation_method, extrapolation_growth, geography_map_key) = tup

        self.set_args(scenario, subsector=subsector, is_stock_dependent=is_stock_dependent, input_type=input_type,
                  unit=unit, driver_denominator_1=driver_denominator_1,
                  driver_denominator_2=driver_denominator_2, driver_1=driver_1, driver_2=driver_2,
                  geography=geography, final_energy_index=final_energy_index,
                  demand_technology_index=demand_technology_index, other_index_1=other_index_1,
                  other_index_2=other_index_2, interpolation_method=interpolation_method,
                  extrapolation_method=extrapolation_method, extrapolation_growth=extrapolation_growth,
                  geography_map_key=geography_map_key)

class DemandEnergyEfficiencyMeasures(DataObject):
    _instances_by_key = {}
    _key_col = "name"
    _cols = ["name", "subsector", "input_type", "unit", "geography", "other_index_1", "other_index_2",
             "interpolation_method", "extrapolation_method", "extrapolation_growth",
             "stock_decay_function", "min_lifetime", "max_lifetime", "mean_lifetime",
             "lifetime_variance"]
    _table_name = "DemandEnergyEfficiencyMeasures"
    _data_table_name = 'DemandEnergyEfficiencyMeasuresData'

    def __init__(self, name, scenario):
        DataObject.__init__(self, name, scenario)

        DemandEnergyEfficiencyMeasures._instances_by_key[self._key] = self

        self.name = None
        self.subsector = None
        self.input_type = None
        self.unit = None
        self.geography = None
        self.other_index_1 = None
        self.other_index_2 = None
        self.interpolation_method = None
        self.extrapolation_method = None
        self.extrapolation_growth = None
        self.stock_decay_function = None
        self.min_lifetime = None
        self.max_lifetime = None
        self.mean_lifetime = None
        self.lifetime_variance = None

    def set_args(self, scenario, name=None, subsector=None, input_type=None, unit=None, geography=None, other_index_1=None,
                 other_index_2=None, interpolation_method=None, extrapolation_method=None,
                 extrapolation_growth=None, stock_decay_function=None, min_lifetime=None,
                 max_lifetime=None, mean_lifetime=None, lifetime_variance=None):
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

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (name, subsector, input_type, unit, geography, other_index_1, other_index_2,
         interpolation_method, extrapolation_method, extrapolation_growth, stock_decay_function,
         min_lifetime, max_lifetime, mean_lifetime, lifetime_variance) = tup

        self.set_args(scenario, name=name, subsector=subsector, input_type=input_type, unit=unit, geography=geography,
                  other_index_1=other_index_1, other_index_2=other_index_2,
                  interpolation_method=interpolation_method, extrapolation_method=extrapolation_method,
                  extrapolation_growth=extrapolation_growth, stock_decay_function=stock_decay_function,
                  min_lifetime=min_lifetime, max_lifetime=max_lifetime, mean_lifetime=mean_lifetime,
                  lifetime_variance=lifetime_variance)

class DemandEnergyEfficiencyMeasuresCost(DataObject):
    _instances_by_key = {}
    _key_col = "parent"
    _cols = ["parent", "currency", "currency_year_id", "cost_denominator_unit", "cost_of_capital",
             "is_levelized", "geography", "other_index_1", "other_index_2", "interpolation_method",
             "extrapolation_method", "extrapolation_growth"]
    _table_name = "DemandEnergyEfficiencyMeasuresCost"
    _data_table_name = 'DemandEnergyEfficiencyMeasuresCostData'

    def __init__(self, parent, scenario):
        DataObject.__init__(self, parent, scenario)

        DemandEnergyEfficiencyMeasuresCost._instances_by_key[self._key] = self

        self.parent = None
        self.currency = None
        self.currency_year_id = None
        self.cost_denominator_unit = None
        self.cost_of_capital = None
        self.is_levelized = None
        self.geography = None
        self.other_index_1 = None
        self.other_index_2 = None
        self.interpolation_method = None
        self.extrapolation_method = None
        self.extrapolation_growth = None

    def set_args(self, scenario, parent=None, currency=None, currency_year_id=None, cost_denominator_unit=None,
                 cost_of_capital=None, is_levelized=None, geography=None, other_index_1=None,
                 other_index_2=None, interpolation_method=None, extrapolation_method=None,
                 extrapolation_growth=None):
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

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (parent, currency, currency_year_id, cost_denominator_unit, cost_of_capital, is_levelized,
         geography, other_index_1, other_index_2, interpolation_method, extrapolation_method,
         extrapolation_growth) = tup

        self.set_args(scenario, parent=parent, currency=currency, currency_year_id=currency_year_id,
                  cost_denominator_unit=cost_denominator_unit, cost_of_capital=cost_of_capital,
                  is_levelized=is_levelized, geography=geography, other_index_1=other_index_1,
                  other_index_2=other_index_2, interpolation_method=interpolation_method,
                  extrapolation_method=extrapolation_method, extrapolation_growth=extrapolation_growth)

class DemandFlexibleLoadMeasures(DataObject):
    _instances_by_key = {}
    _key_col = "subsector"
    _cols = ["subsector", "geography", "other_index_1", "interpolation_method", "extrapolation_method",
             "extrapolation_growth", "name"]
    _table_name = "DemandFlexibleLoadMeasures"
    _data_table_name = 'DemandFlexibleLoadMeasuresData'

    def __init__(self, subsector, scenario):
        DataObject.__init__(self, subsector, scenario)

        DemandFlexibleLoadMeasures._instances_by_key[self._key] = self

        self.subsector = None
        self.geography = None
        self.other_index_1 = None
        self.interpolation_method = None
        self.extrapolation_method = None
        self.extrapolation_growth = None
        self.name = None

    def set_args(self, scenario, subsector=None, geography=None, other_index_1=None, interpolation_method=None,
                 extrapolation_method=None, extrapolation_growth=None, name=None):
        self.subsector = subsector
        self.geography = geography
        self.other_index_1 = other_index_1
        self.interpolation_method = interpolation_method
        self.extrapolation_method = extrapolation_method
        self.extrapolation_growth = extrapolation_growth
        self.name = name

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (subsector, geography, other_index_1, interpolation_method, extrapolation_method,
         extrapolation_growth, name) = tup

        self.set_args(scenario, subsector=subsector, geography=geography, other_index_1=other_index_1,
                  interpolation_method=interpolation_method, extrapolation_method=extrapolation_method,
                  extrapolation_growth=extrapolation_growth, name=name)

class DemandFuelSwitchingMeasures(DataObject):
    _instances_by_key = {}
    _key_col = "name"
    _cols = ["name", "subsector", "final_energy_from", "final_energy_to", "stock_decay_function",
             "max_lifetime", "min_lifetime", "mean_lifetime", "lifetime_variance"]
    _table_name = "DemandFuelSwitchingMeasures"
    _data_table_name = None

    def __init__(self, name, scenario):
        DataObject.__init__(self, name, scenario)

        DemandFuelSwitchingMeasures._instances_by_key[self._key] = self

        self.name = None
        self.subsector = None
        self.final_energy_from = None
        self.final_energy_to = None
        self.stock_decay_function = None
        self.max_lifetime = None
        self.min_lifetime = None
        self.mean_lifetime = None
        self.lifetime_variance = None

    def set_args(self, scenario, name=None, subsector=None, final_energy_from=None, final_energy_to=None,
                 stock_decay_function=None, max_lifetime=None, min_lifetime=None, mean_lifetime=None,
                 lifetime_variance=None):
        self.name = name
        self.subsector = subsector
        self.final_energy_from = final_energy_from
        self.final_energy_to = final_energy_to
        self.stock_decay_function = stock_decay_function
        self.max_lifetime = max_lifetime
        self.min_lifetime = min_lifetime
        self.mean_lifetime = mean_lifetime
        self.lifetime_variance = lifetime_variance

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (name, subsector, final_energy_from, final_energy_to, stock_decay_function, max_lifetime,
         min_lifetime, mean_lifetime, lifetime_variance) = tup

        self.set_args(scenario, name=name, subsector=subsector, final_energy_from=final_energy_from,
                  final_energy_to=final_energy_to, stock_decay_function=stock_decay_function,
                  max_lifetime=max_lifetime, min_lifetime=min_lifetime, mean_lifetime=mean_lifetime,
                  lifetime_variance=lifetime_variance)

class DemandFuelSwitchingMeasuresCost(DataObject):
    _instances_by_key = {}
    _key_col = "parent"
    _cols = ["parent", "currency", "currency_year_id", "cost_denominator_unit", "cost_of_capital",
             "is_levelized", "geography", "other_index_1", "other_index_2", "interpolation_method",
             "extrapolation_method", "extrapolation_growth"]
    _table_name = "DemandFuelSwitchingMeasuresCost"
    _data_table_name = 'DemandFuelSwitchingMeasuresCostData'

    def __init__(self, parent, scenario):
        DataObject.__init__(self, parent, scenario)

        DemandFuelSwitchingMeasuresCost._instances_by_key[self._key] = self

        self.parent = None
        self.currency = None
        self.currency_year_id = None
        self.cost_denominator_unit = None
        self.cost_of_capital = None
        self.is_levelized = None
        self.geography = None
        self.other_index_1 = None
        self.other_index_2 = None
        self.interpolation_method = None
        self.extrapolation_method = None
        self.extrapolation_growth = None

    def set_args(self, scenario, parent=None, currency=None, currency_year_id=None, cost_denominator_unit=None,
                 cost_of_capital=None, is_levelized=None, geography=None, other_index_1=None,
                 other_index_2=None, interpolation_method=None, extrapolation_method=None,
                 extrapolation_growth=None):
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

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (parent, currency, currency_year_id, cost_denominator_unit, cost_of_capital, is_levelized,
         geography, other_index_1, other_index_2, interpolation_method, extrapolation_method,
         extrapolation_growth) = tup

        self.set_args(scenario, parent=parent, currency=currency, currency_year_id=currency_year_id,
                  cost_denominator_unit=cost_denominator_unit, cost_of_capital=cost_of_capital,
                  is_levelized=is_levelized, geography=geography, other_index_1=other_index_1,
                  other_index_2=other_index_2, interpolation_method=interpolation_method,
                  extrapolation_method=extrapolation_method, extrapolation_growth=extrapolation_growth)

class DemandFuelSwitchingMeasuresEnergyIntensity(DataObject):
    _instances_by_key = {}
    _key_col = "parent"
    _cols = ["parent", "geography", "other_index_1", "other_index_2", "interpolation_method",
             "extrapolation_method", "extrapolation_growth"]
    _table_name = "DemandFuelSwitchingMeasuresEnergyIntensity"
    _data_table_name = 'DemandFuelSwitchingMeasuresEnergyIntensityData'

    def __init__(self, parent, scenario):
        DataObject.__init__(self, parent, scenario)

        DemandFuelSwitchingMeasuresEnergyIntensity._instances_by_key[self._key] = self

        self.parent = None
        self.geography = None
        self.other_index_1 = None
        self.other_index_2 = None
        self.interpolation_method = None
        self.extrapolation_method = None
        self.extrapolation_growth = None

    def set_args(self, scenario, parent=None, geography=None, other_index_1=None, other_index_2=None,
                 interpolation_method=None, extrapolation_method=None, extrapolation_growth=None):
        self.parent = parent
        self.geography = geography
        self.other_index_1 = other_index_1
        self.other_index_2 = other_index_2
        self.interpolation_method = interpolation_method
        self.extrapolation_method = extrapolation_method
        self.extrapolation_growth = extrapolation_growth

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (parent, geography, other_index_1, other_index_2, interpolation_method,
         extrapolation_method, extrapolation_growth) = tup

        self.set_args(scenario, parent=parent, geography=geography, other_index_1=other_index_1,
                  other_index_2=other_index_2, interpolation_method=interpolation_method,
                  extrapolation_method=extrapolation_method, extrapolation_growth=extrapolation_growth)

class DemandFuelSwitchingMeasuresImpact(DataObject):
    _instances_by_key = {}
    _key_col = "parent"
    _cols = ["parent", "input_type", "unit", "geography", "other_index_1", "other_index_2",
             "interpolation_method", "extrapolation_method", "extrapolation_growth"]
    _table_name = "DemandFuelSwitchingMeasuresImpact"
    _data_table_name = 'DemandFuelSwitchingMeasuresImpactData'

    def __init__(self, parent, scenario):
        DataObject.__init__(self, parent, scenario)

        DemandFuelSwitchingMeasuresImpact._instances_by_key[self._key] = self

        self.parent = None
        self.input_type = None
        self.unit = None
        self.geography = None
        self.other_index_1 = None
        self.other_index_2 = None
        self.interpolation_method = None
        self.extrapolation_method = None
        self.extrapolation_growth = None

    def set_args(self, scenario, parent=None, input_type=None, unit=None, geography=None, other_index_1=None,
                 other_index_2=None, interpolation_method=None, extrapolation_method=None,
                 extrapolation_growth=None):
        self.parent = parent
        self.input_type = input_type
        self.unit = unit
        self.geography = geography
        self.other_index_1 = other_index_1
        self.other_index_2 = other_index_2
        self.interpolation_method = interpolation_method
        self.extrapolation_method = extrapolation_method
        self.extrapolation_growth = extrapolation_growth

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (parent, input_type, unit, geography, other_index_1, other_index_2, interpolation_method,
         extrapolation_method, extrapolation_growth) = tup

        self.set_args(scenario, parent=parent, input_type=input_type, unit=unit, geography=geography,
                  other_index_1=other_index_1, other_index_2=other_index_2,
                  interpolation_method=interpolation_method, extrapolation_method=extrapolation_method,
                  extrapolation_growth=extrapolation_growth)

class DemandSales(DataObject):
    _instances_by_key = {}
    _key_col = "subsector"
    _cols = ["subsector", "geography", "other_index_1", "other_index_2", "input_type",
             "interpolation_method", "extrapolation_method", "extrapolation_growth"]
    _table_name = "DemandSales"
    _data_table_name = 'DemandSalesData'

    def __init__(self, subsector, scenario):
        DataObject.__init__(self, subsector, scenario)

        DemandSales._instances_by_key[self._key] = self

        self.subsector = None
        self.geography = None
        self.other_index_1 = None
        self.other_index_2 = None
        self.input_type = None
        self.interpolation_method = None
        self.extrapolation_method = None
        self.extrapolation_growth = None

    def set_args(self, scenario, subsector=None, geography=None, other_index_1=None, other_index_2=None, input_type=None,
                 interpolation_method=None, extrapolation_method=None, extrapolation_growth=None):
        self.subsector = subsector
        self.geography = geography
        self.other_index_1 = other_index_1
        self.other_index_2 = other_index_2
        self.input_type = input_type
        self.interpolation_method = interpolation_method
        self.extrapolation_method = extrapolation_method
        self.extrapolation_growth = extrapolation_growth

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (subsector, geography, other_index_1, other_index_2, input_type, interpolation_method,
         extrapolation_method, extrapolation_growth) = tup

        self.set_args(scenario, subsector=subsector, geography=geography, other_index_1=other_index_1,
                  other_index_2=other_index_2, input_type=input_type,
                  interpolation_method=interpolation_method, extrapolation_method=extrapolation_method,
                  extrapolation_growth=extrapolation_growth)

class DemandSalesShareMeasures(DataObject):
    _instances_by_key = {}
    _key_col = "name"
    _cols = ["subsector", "geography", "other_index_1", "demand_technology", "replaced_demand_tech",
             "input_type", "interpolation_method", "extrapolation_method", "extrapolation_growth",
             "name"]
    _table_name = "DemandSalesShareMeasures"
    _data_table_name = 'DemandSalesShareMeasuresData'

    def __init__(self, name, scenario):
        DataObject.__init__(self, name, scenario)

        DemandSalesShareMeasures._instances_by_key[self._key] = self

        self.subsector = None
        self.geography = None
        self.other_index_1 = None
        self.demand_technology = None
        self.replaced_demand_tech = None
        self.input_type = None
        self.interpolation_method = None
        self.extrapolation_method = None
        self.extrapolation_growth = None
        self.name = None

    def set_args(self, scenario, subsector=None, geography=None, other_index_1=None, demand_technology=None,
                 replaced_demand_tech=None, input_type=None, interpolation_method=None,
                 extrapolation_method=None, extrapolation_growth=None, name=None):
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

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (subsector, geography, other_index_1, demand_technology, replaced_demand_tech, input_type,
         interpolation_method, extrapolation_method, extrapolation_growth, name) = tup

        self.set_args(scenario, subsector=subsector, geography=geography, other_index_1=other_index_1,
                  demand_technology=demand_technology, replaced_demand_tech=replaced_demand_tech,
                  input_type=input_type, interpolation_method=interpolation_method,
                  extrapolation_method=extrapolation_method, extrapolation_growth=extrapolation_growth,
                  name=name)

class DemandSectors(DataObject):
    _instances_by_key = {}
    _key_col = "name"
    _cols = ["name", "shape", "max_lead_hours", "max_lag_hours"]
    _table_name = "DemandSectors"
    _data_table_name = None

    def __init__(self, name, scenario):
        DataObject.__init__(self, name, scenario)

        DemandSectors._instances_by_key[self._key] = self

        self.name = None
        self.shape = None
        self.max_lead_hours = None
        self.max_lag_hours = None

    def set_args(self, scenario, name=None, shape=None, max_lead_hours=None, max_lag_hours=None):
        self.name = name
        self.shape = shape
        self.max_lead_hours = max_lead_hours
        self.max_lag_hours = max_lag_hours

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (name, shape, max_lead_hours, max_lag_hours) = tup

        self.set_args(scenario, name=name, shape=shape, max_lead_hours=max_lead_hours, max_lag_hours=max_lag_hours)

class DemandServiceDemandMeasures(DataObject):
    _instances_by_key = {}
    _key_col = "name"
    _cols = ["name", "subsector", "input_type", "unit", "geography", "other_index_1", "other_index_2",
             "interpolation_method", "extrapolation_method", "extrapolation_growth",
             "stock_decay_function", "min_lifetime", "max_lifetime", "mean_lifetime",
             "lifetime_variance", "geography_map_key_id"]
    _table_name = "DemandServiceDemandMeasures"
    _data_table_name = 'DemandServiceDemandMeasuresData'

    def __init__(self, name, scenario):
        DataObject.__init__(self, name, scenario)

        DemandServiceDemandMeasures._instances_by_key[self._key] = self

        self.name = None
        self.subsector = None
        self.input_type = None
        self.unit = None
        self.geography = None
        self.other_index_1 = None
        self.other_index_2 = None
        self.interpolation_method = None
        self.extrapolation_method = None
        self.extrapolation_growth = None
        self.stock_decay_function = None
        self.min_lifetime = None
        self.max_lifetime = None
        self.mean_lifetime = None
        self.lifetime_variance = None
        self.geography_map_key_id = None

    def set_args(self, scenario, name=None, subsector=None, input_type=None, unit=None, geography=None, other_index_1=None,
                 other_index_2=None, interpolation_method=None, extrapolation_method=None,
                 extrapolation_growth=None, stock_decay_function=None, min_lifetime=None,
                 max_lifetime=None, mean_lifetime=None, lifetime_variance=None, geography_map_key_id=None):
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
        self.geography_map_key_id = geography_map_key_id

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (name, subsector, input_type, unit, geography, other_index_1, other_index_2,
         interpolation_method, extrapolation_method, extrapolation_growth, stock_decay_function,
         min_lifetime, max_lifetime, mean_lifetime, lifetime_variance, geography_map_key_id) = tup

        self.set_args(scenario, name=name, subsector=subsector, input_type=input_type, unit=unit, geography=geography,
                  other_index_1=other_index_1, other_index_2=other_index_2,
                  interpolation_method=interpolation_method, extrapolation_method=extrapolation_method,
                  extrapolation_growth=extrapolation_growth, stock_decay_function=stock_decay_function,
                  min_lifetime=min_lifetime, max_lifetime=max_lifetime, mean_lifetime=mean_lifetime,
                  lifetime_variance=lifetime_variance, geography_map_key_id=geography_map_key_id)

class DemandServiceDemandMeasuresCost(DataObject):
    _instances_by_key = {}
    _key_col = "parent"
    _cols = ["parent", "currency", "currency_year_id", "cost_denominator_unit", "cost_of_capital",
             "is_levelized", "geography", "other_index_1", "other_index_2", "interpolation_method",
             "extrapolation_method", "extrapolation_growth"]
    _table_name = "DemandServiceDemandMeasuresCost"
    _data_table_name = 'DemandServiceDemandMeasuresCostData'

    def __init__(self, parent, scenario):
        DataObject.__init__(self, parent, scenario)

        DemandServiceDemandMeasuresCost._instances_by_key[self._key] = self

        self.parent = None
        self.currency = None
        self.currency_year_id = None
        self.cost_denominator_unit = None
        self.cost_of_capital = None
        self.is_levelized = None
        self.geography = None
        self.other_index_1 = None
        self.other_index_2 = None
        self.interpolation_method = None
        self.extrapolation_method = None
        self.extrapolation_growth = None

    def set_args(self, scenario, parent=None, currency=None, currency_year_id=None, cost_denominator_unit=None,
                 cost_of_capital=None, is_levelized=None, geography=None, other_index_1=None,
                 other_index_2=None, interpolation_method=None, extrapolation_method=None,
                 extrapolation_growth=None):
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

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (parent, currency, currency_year_id, cost_denominator_unit, cost_of_capital, is_levelized,
         geography, other_index_1, other_index_2, interpolation_method, extrapolation_method,
         extrapolation_growth) = tup

        self.set_args(scenario, parent=parent, currency=currency, currency_year_id=currency_year_id,
                  cost_denominator_unit=cost_denominator_unit, cost_of_capital=cost_of_capital,
                  is_levelized=is_levelized, geography=geography, other_index_1=other_index_1,
                  other_index_2=other_index_2, interpolation_method=interpolation_method,
                  extrapolation_method=extrapolation_method, extrapolation_growth=extrapolation_growth)

class DemandServiceDemands(DataObject):
    _instances_by_key = {}
    _key_col = "subsector"
    _cols = ["subsector", "is_stock_dependent", "input_type", "unit", "driver_denominator_1",
             "driver_denominator_2", "driver_1", "driver_2", "geography", "final_energy_index",
             "demand_technology_index", "other_index_1", "other_index_2", "interpolation_method",
             "extrapolation_method", "extrapolation_growth", "geography_map_key"]
    _table_name = "DemandServiceDemands"
    _data_table_name = 'DemandServiceDemandsData'

    def __init__(self, subsector, scenario):
        DataObject.__init__(self, subsector, scenario)

        DemandServiceDemands._instances_by_key[self._key] = self

        self.subsector = None
        self.is_stock_dependent = None
        self.input_type = None
        self.unit = None
        self.driver_denominator_1 = None
        self.driver_denominator_2 = None
        self.driver_1 = None
        self.driver_2 = None
        self.geography = None
        self.final_energy_index = None
        self.demand_technology_index = None
        self.other_index_1 = None
        self.other_index_2 = None
        self.interpolation_method = None
        self.extrapolation_method = None
        self.extrapolation_growth = None
        self.geography_map_key = None

    def set_args(self, scenario, subsector=None, is_stock_dependent=None, input_type=None, unit=None,
                 driver_denominator_1=None, driver_denominator_2=None, driver_1=None, driver_2=None,
                 geography=None, final_energy_index=None, demand_technology_index=None,
                 other_index_1=None, other_index_2=None, interpolation_method=None,
                 extrapolation_method=None, extrapolation_growth=None, geography_map_key=None):
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

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (subsector, is_stock_dependent, input_type, unit, driver_denominator_1,
         driver_denominator_2, driver_1, driver_2, geography, final_energy_index,
         demand_technology_index, other_index_1, other_index_2, interpolation_method,
         extrapolation_method, extrapolation_growth, geography_map_key) = tup

        self.set_args(scenario, subsector=subsector, is_stock_dependent=is_stock_dependent, input_type=input_type,
                  unit=unit, driver_denominator_1=driver_denominator_1,
                  driver_denominator_2=driver_denominator_2, driver_1=driver_1, driver_2=driver_2,
                  geography=geography, final_energy_index=final_energy_index,
                  demand_technology_index=demand_technology_index, other_index_1=other_index_1,
                  other_index_2=other_index_2, interpolation_method=interpolation_method,
                  extrapolation_method=extrapolation_method, extrapolation_growth=extrapolation_growth,
                  geography_map_key=geography_map_key)

class DemandServiceEfficiency(DataObject):
    _instances_by_key = {}
    _key_col = "subsector"
    _cols = ["subsector", "energy_unit", "denominator_unit", "geography", "other_index_1",
             "other_index_2", "interpolation_method", "extrapolation_method", "extrapolation_growth",
             "geography_map_key"]
    _table_name = "DemandServiceEfficiency"
    _data_table_name = 'DemandServiceEfficiencyData'

    def __init__(self, subsector, scenario):
        DataObject.__init__(self, subsector, scenario)

        DemandServiceEfficiency._instances_by_key[self._key] = self

        self.subsector = None
        self.energy_unit = None
        self.denominator_unit = None
        self.geography = None
        self.other_index_1 = None
        self.other_index_2 = None
        self.interpolation_method = None
        self.extrapolation_method = None
        self.extrapolation_growth = None
        self.geography_map_key = None

    def set_args(self, scenario, subsector=None, energy_unit=None, denominator_unit=None, geography=None,
                 other_index_1=None, other_index_2=None, interpolation_method=None,
                 extrapolation_method=None, extrapolation_growth=None, geography_map_key=None):
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

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (subsector, energy_unit, denominator_unit, geography, other_index_1, other_index_2,
         interpolation_method, extrapolation_method, extrapolation_growth, geography_map_key) = tup

        self.set_args(scenario, subsector=subsector, energy_unit=energy_unit, denominator_unit=denominator_unit,
                  geography=geography, other_index_1=other_index_1, other_index_2=other_index_2,
                  interpolation_method=interpolation_method, extrapolation_method=extrapolation_method,
                  extrapolation_growth=extrapolation_growth, geography_map_key=geography_map_key)

class DemandServiceLink(DataObject):
    _instances_by_key = {}
    _key_col = "name"
    _cols = ["subsector", "linked_subsector", "service_demand_share", "year", "name"]
    _table_name = "DemandServiceLink"
    _data_table_name = 'DemandServiceLinkData'

    def __init__(self, name, scenario):
        DataObject.__init__(self, name, scenario)

        DemandServiceLink._instances_by_key[self._key] = self

        self.subsector = None
        self.linked_subsector = None
        self.service_demand_share = None
        self.year = None
        self.name = None

    def set_args(self, scenario, subsector=None, linked_subsector=None, service_demand_share=None, year=None, name=None):
        self.subsector = subsector
        self.linked_subsector = linked_subsector
        self.service_demand_share = service_demand_share
        self.year = year
        self.name = name

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (subsector, linked_subsector, service_demand_share, year, name) = tup

        self.set_args(scenario, subsector=subsector, linked_subsector=linked_subsector,
                  service_demand_share=service_demand_share, year=year, name=name)

class DemandStock(DataObject):
    _instances_by_key = {}
    _key_col = "subsector"
    _cols = ["subsector", "is_service_demand_dependent", "driver_denominator_1",
             "driver_denominator_2", "driver_1", "driver_2", "geography", "other_index_1",
             "other_index_2", "geography_map_key", "input_type", "demand_stock_unit_type", "unit",
             "time_unit", "interpolation_method", "extrapolation_method", "extrapolation_growth",
             "specify_stocks_past_current_year"]
    _table_name = "DemandStock"
    _data_table_name = 'DemandStockData'

    def __init__(self, subsector, scenario):
        DataObject.__init__(self, subsector, scenario)

        DemandStock._instances_by_key[self._key] = self

        self.subsector = None
        self.is_service_demand_dependent = None
        self.driver_denominator_1 = None
        self.driver_denominator_2 = None
        self.driver_1 = None
        self.driver_2 = None
        self.geography = None
        self.other_index_1 = None
        self.other_index_2 = None
        self.geography_map_key = None
        self.input_type = None
        self.demand_stock_unit_type = None
        self.unit = None
        self.time_unit = None
        self.interpolation_method = None
        self.extrapolation_method = None
        self.extrapolation_growth = None
        self.specify_stocks_past_current_year = None

    def set_args(self, scenario, subsector=None, is_service_demand_dependent=None, driver_denominator_1=None,
                 driver_denominator_2=None, driver_1=None, driver_2=None, geography=None,
                 other_index_1=None, other_index_2=None, geography_map_key=None, input_type=None,
                 demand_stock_unit_type=None, unit=None, time_unit=None, interpolation_method=None,
                 extrapolation_method=None, extrapolation_growth=None,
                 specify_stocks_past_current_year=None):
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
        self.specify_stocks_past_current_year = specify_stocks_past_current_year

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (subsector, is_service_demand_dependent, driver_denominator_1, driver_denominator_2,
         driver_1, driver_2, geography, other_index_1, other_index_2, geography_map_key,
         input_type, demand_stock_unit_type, unit, time_unit, interpolation_method,
         extrapolation_method, extrapolation_growth, specify_stocks_past_current_year) = tup

        self.set_args(scenario, subsector=subsector, is_service_demand_dependent=is_service_demand_dependent,
                  driver_denominator_1=driver_denominator_1, driver_denominator_2=driver_denominator_2,
                  driver_1=driver_1, driver_2=driver_2, geography=geography, other_index_1=other_index_1,
                  other_index_2=other_index_2, geography_map_key=geography_map_key, input_type=input_type,
                  demand_stock_unit_type=demand_stock_unit_type, unit=unit, time_unit=time_unit,
                  interpolation_method=interpolation_method, extrapolation_method=extrapolation_method,
                  extrapolation_growth=extrapolation_growth,
                  specify_stocks_past_current_year=specify_stocks_past_current_year)

class DemandStockMeasures(DataObject):
    _instances_by_key = {}
    _key_col = "name"
    _cols = ["subsector", "geography", "other_index_1", "demand_technology", "interpolation_method",
             "extrapolation_method", "extrapolation_growth", "name"]
    _table_name = "DemandStockMeasures"
    _data_table_name = 'DemandStockMeasuresData'

    def __init__(self, name, scenario):
        DataObject.__init__(self, name, scenario)

        DemandStockMeasures._instances_by_key[self._key] = self

        self.subsector = None
        self.geography = None
        self.other_index_1 = None
        self.demand_technology = None
        self.interpolation_method = None
        self.extrapolation_method = None
        self.extrapolation_growth = None
        self.name = None

    def set_args(self, scenario, subsector=None, geography=None, other_index_1=None, demand_technology=None,
                 interpolation_method=None, extrapolation_method=None, extrapolation_growth=None,
                 name=None):
        self.subsector = subsector
        self.geography = geography
        self.other_index_1 = other_index_1
        self.demand_technology = demand_technology
        self.interpolation_method = interpolation_method
        self.extrapolation_method = extrapolation_method
        self.extrapolation_growth = extrapolation_growth
        self.name = name

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (subsector, geography, other_index_1, demand_technology, interpolation_method,
         extrapolation_method, extrapolation_growth, name) = tup

        self.set_args(scenario, subsector=subsector, geography=geography, other_index_1=other_index_1,
                  demand_technology=demand_technology, interpolation_method=interpolation_method,
                  extrapolation_method=extrapolation_method, extrapolation_growth=extrapolation_growth,
                  name=name)

class DemandSubsectors(DataObject):
    _instances_by_key = {}
    _key_col = "name"
    _cols = ["sector", "name", "cost_of_capital", "is_active", "shape", "max_lead_hours",
             "max_lag_hours"]
    _table_name = "DemandSubsectors"
    _data_table_name = None

    def __init__(self, name, scenario):
        DataObject.__init__(self, name, scenario)

        DemandSubsectors._instances_by_key[self._key] = self

        self.sector = None
        self.name = None
        self.cost_of_capital = None
        self.is_active = None
        self.shape = None
        self.max_lead_hours = None
        self.max_lag_hours = None

    def set_args(self, scenario, sector=None, name=None, cost_of_capital=None, is_active=None, shape=None,
                 max_lead_hours=None, max_lag_hours=None):
        self.sector = sector
        self.name = name
        self.cost_of_capital = cost_of_capital
        self.is_active = is_active
        self.shape = shape
        self.max_lead_hours = max_lead_hours
        self.max_lag_hours = max_lag_hours

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (sector, name, cost_of_capital, is_active, shape, max_lead_hours, max_lag_hours) = tup

        self.set_args(scenario, sector=sector, name=name, cost_of_capital=cost_of_capital, is_active=is_active,
                  shape=shape, max_lead_hours=max_lead_hours, max_lag_hours=max_lag_hours)

class DemandTechs(DataObject):
    _instances_by_key = {}
    _key_col = "name"
    _cols = ["linked", "stock_link_ratio", "subsector", "name", "min_lifetime", "max_lifetime",
             "source", "additional_description", "demand_tech_unit_type", "unit", "time_unit",
             "cost_of_capital", "stock_decay_function", "mean_lifetime", "lifetime_variance", "shape",
             "max_lead_hours", "max_lag_hours"]
    _table_name = "DemandTechs"
    _data_table_name = None

    def __init__(self, name, scenario):
        DataObject.__init__(self, name, scenario)

        DemandTechs._instances_by_key[self._key] = self

        self.linked = None
        self.stock_link_ratio = None
        self.subsector = None
        self.name = None
        self.min_lifetime = None
        self.max_lifetime = None
        self.source = None
        self.additional_description = None
        self.demand_tech_unit_type = None
        self.unit = None
        self.time_unit = None
        self.cost_of_capital = None
        self.stock_decay_function = None
        self.mean_lifetime = None
        self.lifetime_variance = None
        self.shape = None
        self.max_lead_hours = None
        self.max_lag_hours = None

    def set_args(self, scenario, linked=None, stock_link_ratio=None, subsector=None, name=None, min_lifetime=None,
                 max_lifetime=None, source=None, additional_description=None, demand_tech_unit_type=None,
                 unit=None, time_unit=None, cost_of_capital=None, stock_decay_function=None,
                 mean_lifetime=None, lifetime_variance=None, shape=None, max_lead_hours=None,
                 max_lag_hours=None):
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

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (linked, stock_link_ratio, subsector, name, min_lifetime, max_lifetime, source,
         additional_description, demand_tech_unit_type, unit, time_unit, cost_of_capital,
         stock_decay_function, mean_lifetime, lifetime_variance, shape, max_lead_hours,
         max_lag_hours) = tup

        self.set_args(scenario, linked=linked, stock_link_ratio=stock_link_ratio, subsector=subsector, name=name,
                  min_lifetime=min_lifetime, max_lifetime=max_lifetime, source=source,
                  additional_description=additional_description,
                  demand_tech_unit_type=demand_tech_unit_type, unit=unit, time_unit=time_unit,
                  cost_of_capital=cost_of_capital, stock_decay_function=stock_decay_function,
                  mean_lifetime=mean_lifetime, lifetime_variance=lifetime_variance, shape=shape,
                  max_lead_hours=max_lead_hours, max_lag_hours=max_lag_hours)

class DemandTechsAuxEfficiency(DataObject):
    _instances_by_key = {}
    _key_col = "demand_technology"
    _cols = ["demand_technology", "definition", "reference_tech_id", "geography", "other_index_1",
             "other_index_2", "final_energy", "demand_tech_efficiency_types", "is_numerator_service",
             "numerator_unit", "denominator_unit", "interpolation_method", "extrapolation_method",
             "extrapolation_growth", "age_growth_or_decay_type", "age_growth_or_decay", "shape"]
    _table_name = "DemandTechsAuxEfficiency"
    _data_table_name = 'DemandTechsAuxEfficiencyData'

    def __init__(self, demand_technology, scenario):
        DataObject.__init__(self, demand_technology, scenario)

        DemandTechsAuxEfficiency._instances_by_key[self._key] = self

        self.demand_technology = None
        self.definition = None
        self.reference_tech_id = None
        self.geography = None
        self.other_index_1 = None
        self.other_index_2 = None
        self.final_energy = None
        self.demand_tech_efficiency_types = None
        self.is_numerator_service = None
        self.numerator_unit = None
        self.denominator_unit = None
        self.interpolation_method = None
        self.extrapolation_method = None
        self.extrapolation_growth = None
        self.age_growth_or_decay_type = None
        self.age_growth_or_decay = None
        self.shape = None

    def set_args(self, scenario, demand_technology=None, definition=None, reference_tech_id=None, geography=None,
                 other_index_1=None, other_index_2=None, final_energy=None,
                 demand_tech_efficiency_types=None, is_numerator_service=None, numerator_unit=None,
                 denominator_unit=None, interpolation_method=None, extrapolation_method=None,
                 extrapolation_growth=None, age_growth_or_decay_type=None, age_growth_or_decay=None,
                 shape=None):
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

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (demand_technology, definition, reference_tech_id, geography, other_index_1, other_index_2,
         final_energy, demand_tech_efficiency_types, is_numerator_service, numerator_unit,
         denominator_unit, interpolation_method, extrapolation_method, extrapolation_growth,
         age_growth_or_decay_type, age_growth_or_decay, shape) = tup

        self.set_args(scenario, demand_technology=demand_technology, definition=definition,
                  reference_tech_id=reference_tech_id, geography=geography, other_index_1=other_index_1,
                  other_index_2=other_index_2, final_energy=final_energy,
                  demand_tech_efficiency_types=demand_tech_efficiency_types,
                  is_numerator_service=is_numerator_service, numerator_unit=numerator_unit,
                  denominator_unit=denominator_unit, interpolation_method=interpolation_method,
                  extrapolation_method=extrapolation_method, extrapolation_growth=extrapolation_growth,
                  age_growth_or_decay_type=age_growth_or_decay_type,
                  age_growth_or_decay=age_growth_or_decay, shape=shape)

class DemandTechsCapitalCost(DataObject):
    _instances_by_key = {}
    _key_col = "demand_technology"
    _cols = ["demand_technology", "definition", "reference_tech_id", "geography", "other_index_1",
             "other_index_2", "currency", "currency_year_id", "is_levelized", "interpolation_method",
             "extrapolation_method", "extrapolation_growth", "reference_tech_operation"]
    _table_name = "DemandTechsCapitalCost"
    _data_table_name = None

    def __init__(self, demand_technology, scenario):
        DataObject.__init__(self, demand_technology, scenario)

        DemandTechsCapitalCost._instances_by_key[self._key] = self

        self.demand_technology = None
        self.definition = None
        self.reference_tech_id = None
        self.geography = None
        self.other_index_1 = None
        self.other_index_2 = None
        self.currency = None
        self.currency_year_id = None
        self.is_levelized = None
        self.interpolation_method = None
        self.extrapolation_method = None
        self.extrapolation_growth = None
        self.reference_tech_operation = None

    def set_args(self, scenario, demand_technology=None, definition=None, reference_tech_id=None, geography=None,
                 other_index_1=None, other_index_2=None, currency=None, currency_year_id=None,
                 is_levelized=None, interpolation_method=None, extrapolation_method=None,
                 extrapolation_growth=None, reference_tech_operation=None):
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

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (demand_technology, definition, reference_tech_id, geography, other_index_1, other_index_2,
         currency, currency_year_id, is_levelized, interpolation_method, extrapolation_method,
         extrapolation_growth, reference_tech_operation) = tup

        self.set_args(scenario, demand_technology=demand_technology, definition=definition,
                  reference_tech_id=reference_tech_id, geography=geography, other_index_1=other_index_1,
                  other_index_2=other_index_2, currency=currency, currency_year_id=currency_year_id,
                  is_levelized=is_levelized, interpolation_method=interpolation_method,
                  extrapolation_method=extrapolation_method, extrapolation_growth=extrapolation_growth,
                  reference_tech_operation=reference_tech_operation)

class DemandTechsFixedMaintenanceCost(DataObject):
    _instances_by_key = {}
    _key_col = "demand_technology"
    _cols = ["demand_technology", "definition", "reference_tech_id", "geography", "other_index_1",
             "other_index_2", "currency", "currency_year_id", "interpolation_method",
             "extrapolation_method", "extrapolation_growth", "age_growth_or_decay_type",
             "age_growth_or_decay", "additional_description"]
    _table_name = "DemandTechsFixedMaintenanceCost"
    _data_table_name = 'DemandTechsFixedMaintenanceCostData'

    def __init__(self, demand_technology, scenario):
        DataObject.__init__(self, demand_technology, scenario)

        DemandTechsFixedMaintenanceCost._instances_by_key[self._key] = self

        self.demand_technology = None
        self.definition = None
        self.reference_tech_id = None
        self.geography = None
        self.other_index_1 = None
        self.other_index_2 = None
        self.currency = None
        self.currency_year_id = None
        self.interpolation_method = None
        self.extrapolation_method = None
        self.extrapolation_growth = None
        self.age_growth_or_decay_type = None
        self.age_growth_or_decay = None
        self.additional_description = None

    def set_args(self, scenario, demand_technology=None, definition=None, reference_tech_id=None, geography=None,
                 other_index_1=None, other_index_2=None, currency=None, currency_year_id=None,
                 interpolation_method=None, extrapolation_method=None, extrapolation_growth=None,
                 age_growth_or_decay_type=None, age_growth_or_decay=None, additional_description=None):
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

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (demand_technology, definition, reference_tech_id, geography, other_index_1, other_index_2,
         currency, currency_year_id, interpolation_method, extrapolation_method,
         extrapolation_growth, age_growth_or_decay_type, age_growth_or_decay,
         additional_description) = tup

        self.set_args(scenario, demand_technology=demand_technology, definition=definition,
                  reference_tech_id=reference_tech_id, geography=geography, other_index_1=other_index_1,
                  other_index_2=other_index_2, currency=currency, currency_year_id=currency_year_id,
                  interpolation_method=interpolation_method, extrapolation_method=extrapolation_method,
                  extrapolation_growth=extrapolation_growth,
                  age_growth_or_decay_type=age_growth_or_decay_type,
                  age_growth_or_decay=age_growth_or_decay, additional_description=additional_description)

class DemandTechsFuelSwitchCost(DataObject):
    _instances_by_key = {}
    _key_col = "demand_technology"
    _cols = ["demand_technology", "definition", "reference_tech_id", "geography", "other_index_1",
             "other_index_2", "currency", "currency_year_id", "is_levelized", "interpolation_method",
             "extrapolation_method", "extrapolation_growth"]
    _table_name = "DemandTechsFuelSwitchCost"
    _data_table_name = 'DemandTechsFuelSwitchCostData'

    def __init__(self, demand_technology, scenario):
        DataObject.__init__(self, demand_technology, scenario)

        DemandTechsFuelSwitchCost._instances_by_key[self._key] = self

        self.demand_technology = None
        self.definition = None
        self.reference_tech_id = None
        self.geography = None
        self.other_index_1 = None
        self.other_index_2 = None
        self.currency = None
        self.currency_year_id = None
        self.is_levelized = None
        self.interpolation_method = None
        self.extrapolation_method = None
        self.extrapolation_growth = None

    def set_args(self, scenario, demand_technology=None, definition=None, reference_tech_id=None, geography=None,
                 other_index_1=None, other_index_2=None, currency=None, currency_year_id=None,
                 is_levelized=None, interpolation_method=None, extrapolation_method=None,
                 extrapolation_growth=None):
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

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (demand_technology, definition, reference_tech_id, geography, other_index_1, other_index_2,
         currency, currency_year_id, is_levelized, interpolation_method, extrapolation_method,
         extrapolation_growth) = tup

        self.set_args(scenario, demand_technology=demand_technology, definition=definition,
                  reference_tech_id=reference_tech_id, geography=geography, other_index_1=other_index_1,
                  other_index_2=other_index_2, currency=currency, currency_year_id=currency_year_id,
                  is_levelized=is_levelized, interpolation_method=interpolation_method,
                  extrapolation_method=extrapolation_method, extrapolation_growth=extrapolation_growth)

class DemandTechsInstallationCost(DataObject):
    _instances_by_key = {}
    _key_col = "demand_technology"
    _cols = ["demand_technology", "definition", "reference_tech_id", "geography", "other_index_1",
             "other_index_2", "currency", "currency_year_id", "is_levelized", "interpolation_method",
             "extrapolation_method", "extrapolation_growth"]
    _table_name = "DemandTechsInstallationCost"
    _data_table_name = None

    def __init__(self, demand_technology, scenario):
        DataObject.__init__(self, demand_technology, scenario)

        DemandTechsInstallationCost._instances_by_key[self._key] = self

        self.demand_technology = None
        self.definition = None
        self.reference_tech_id = None
        self.geography = None
        self.other_index_1 = None
        self.other_index_2 = None
        self.currency = None
        self.currency_year_id = None
        self.is_levelized = None
        self.interpolation_method = None
        self.extrapolation_method = None
        self.extrapolation_growth = None

    def set_args(self, scenario, demand_technology=None, definition=None, reference_tech_id=None, geography=None,
                 other_index_1=None, other_index_2=None, currency=None, currency_year_id=None,
                 is_levelized=None, interpolation_method=None, extrapolation_method=None,
                 extrapolation_growth=None):
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

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (demand_technology, definition, reference_tech_id, geography, other_index_1, other_index_2,
         currency, currency_year_id, is_levelized, interpolation_method, extrapolation_method,
         extrapolation_growth) = tup

        self.set_args(scenario, demand_technology=demand_technology, definition=definition,
                  reference_tech_id=reference_tech_id, geography=geography, other_index_1=other_index_1,
                  other_index_2=other_index_2, currency=currency, currency_year_id=currency_year_id,
                  is_levelized=is_levelized, interpolation_method=interpolation_method,
                  extrapolation_method=extrapolation_method, extrapolation_growth=extrapolation_growth)

class DemandTechsMainEfficiency(DataObject):
    _instances_by_key = {}
    _key_col = "demand_technology"
    _cols = ["demand_technology", "definition", "reference_tech_id", "geography", "other_index_1",
             "other_index_2", "final_energy", "utility_factor", "is_numerator_service",
             "numerator_unit", "denominator_unit", "interpolation_method", "extrapolation_method",
             "extrapolation_growth", "age_growth_or_decay_type", "age_growth_or_decay",
             "geography_map_key"]
    _table_name = "DemandTechsMainEfficiency"
    _data_table_name = 'DemandTechsMainEfficiencyData'

    def __init__(self, demand_technology, scenario):
        DataObject.__init__(self, demand_technology, scenario)

        DemandTechsMainEfficiency._instances_by_key[self._key] = self

        self.demand_technology = None
        self.definition = None
        self.reference_tech_id = None
        self.geography = None
        self.other_index_1 = None
        self.other_index_2 = None
        self.final_energy = None
        self.utility_factor = None
        self.is_numerator_service = None
        self.numerator_unit = None
        self.denominator_unit = None
        self.interpolation_method = None
        self.extrapolation_method = None
        self.extrapolation_growth = None
        self.age_growth_or_decay_type = None
        self.age_growth_or_decay = None
        self.geography_map_key = None

    def set_args(self, scenario, demand_technology=None, definition=None, reference_tech_id=None, geography=None,
                 other_index_1=None, other_index_2=None, final_energy=None, utility_factor=None,
                 is_numerator_service=None, numerator_unit=None, denominator_unit=None,
                 interpolation_method=None, extrapolation_method=None, extrapolation_growth=None,
                 age_growth_or_decay_type=None, age_growth_or_decay=None, geography_map_key=None):
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

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (demand_technology, definition, reference_tech_id, geography, other_index_1, other_index_2,
         final_energy, utility_factor, is_numerator_service, numerator_unit, denominator_unit,
         interpolation_method, extrapolation_method, extrapolation_growth,
         age_growth_or_decay_type, age_growth_or_decay, geography_map_key) = tup

        self.set_args(scenario, demand_technology=demand_technology, definition=definition,
                  reference_tech_id=reference_tech_id, geography=geography, other_index_1=other_index_1,
                  other_index_2=other_index_2, final_energy=final_energy, utility_factor=utility_factor,
                  is_numerator_service=is_numerator_service, numerator_unit=numerator_unit,
                  denominator_unit=denominator_unit, interpolation_method=interpolation_method,
                  extrapolation_method=extrapolation_method, extrapolation_growth=extrapolation_growth,
                  age_growth_or_decay_type=age_growth_or_decay_type,
                  age_growth_or_decay=age_growth_or_decay, geography_map_key=geography_map_key)

class DemandTechsParasiticEnergy(DataObject):
    _instances_by_key = {}
    _key_col = "demand_technology"
    _cols = ["demand_technology", "definition", "reference_tech_id", "geography", "other_index_1",
             "other_index_2", "energy_unit", "time_unit", "interpolation_method",
             "extrapolation_method", "extrapolation_growth", "age_growth_or_decay_type",
             "age_growth_or_decay"]
    _table_name = "DemandTechsParasiticEnergy"
    _data_table_name = 'DemandTechsParasiticEnergyData'

    def __init__(self, demand_technology, scenario):
        DataObject.__init__(self, demand_technology, scenario)

        DemandTechsParasiticEnergy._instances_by_key[self._key] = self

        self.demand_technology = None
        self.definition = None
        self.reference_tech_id = None
        self.geography = None
        self.other_index_1 = None
        self.other_index_2 = None
        self.energy_unit = None
        self.time_unit = None
        self.interpolation_method = None
        self.extrapolation_method = None
        self.extrapolation_growth = None
        self.age_growth_or_decay_type = None
        self.age_growth_or_decay = None

    def set_args(self, scenario, demand_technology=None, definition=None, reference_tech_id=None, geography=None,
                 other_index_1=None, other_index_2=None, energy_unit=None, time_unit=None,
                 interpolation_method=None, extrapolation_method=None, extrapolation_growth=None,
                 age_growth_or_decay_type=None, age_growth_or_decay=None):
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

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (demand_technology, definition, reference_tech_id, geography, other_index_1, other_index_2,
         energy_unit, time_unit, interpolation_method, extrapolation_method, extrapolation_growth,
         age_growth_or_decay_type, age_growth_or_decay) = tup

        self.set_args(scenario, demand_technology=demand_technology, definition=definition,
                  reference_tech_id=reference_tech_id, geography=geography, other_index_1=other_index_1,
                  other_index_2=other_index_2, energy_unit=energy_unit, time_unit=time_unit,
                  interpolation_method=interpolation_method, extrapolation_method=extrapolation_method,
                  extrapolation_growth=extrapolation_growth,
                  age_growth_or_decay_type=age_growth_or_decay_type,
                  age_growth_or_decay=age_growth_or_decay)

class DemandTechsServiceDemandModifier(DataObject):
    _instances_by_key = {}
    _key_col = "demand_technology"
    _cols = ["demand_technology", "geography", "other_index_1", "other_index_2",
             "interpolation_method", "extrapolation_method", "extrapolation_growth",
             "age_growth_or_decay_type", "age_growth_or_decay"]
    _table_name = "DemandTechsServiceDemandModifier"
    _data_table_name = 'DemandTechsServiceDemandModifierData'

    def __init__(self, demand_technology, scenario):
        DataObject.__init__(self, demand_technology, scenario)

        DemandTechsServiceDemandModifier._instances_by_key[self._key] = self

        self.demand_technology = None
        self.geography = None
        self.other_index_1 = None
        self.other_index_2 = None
        self.interpolation_method = None
        self.extrapolation_method = None
        self.extrapolation_growth = None
        self.age_growth_or_decay_type = None
        self.age_growth_or_decay = None

    def set_args(self, scenario, demand_technology=None, geography=None, other_index_1=None, other_index_2=None,
                 interpolation_method=None, extrapolation_method=None, extrapolation_growth=None,
                 age_growth_or_decay_type=None, age_growth_or_decay=None):
        self.demand_technology = demand_technology
        self.geography = geography
        self.other_index_1 = other_index_1
        self.other_index_2 = other_index_2
        self.interpolation_method = interpolation_method
        self.extrapolation_method = extrapolation_method
        self.extrapolation_growth = extrapolation_growth
        self.age_growth_or_decay_type = age_growth_or_decay_type
        self.age_growth_or_decay = age_growth_or_decay

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (demand_technology, geography, other_index_1, other_index_2, interpolation_method,
         extrapolation_method, extrapolation_growth, age_growth_or_decay_type, age_growth_or_decay) = tup

        self.set_args(scenario, demand_technology=demand_technology, geography=geography, other_index_1=other_index_1,
                  other_index_2=other_index_2, interpolation_method=interpolation_method,
                  extrapolation_method=extrapolation_method, extrapolation_growth=extrapolation_growth,
                  age_growth_or_decay_type=age_growth_or_decay_type,
                  age_growth_or_decay=age_growth_or_decay)

class DemandTechsServiceLink(DataObject):
    _instances_by_key = {}
    _key_col = "name"
    _cols = ["service_link", "demand_technology", "definition", "reference_id", "geography",
             "other_index_1", "other_index_2", "interpolation_method", "extrapolation_method",
             "extrapolation_growth", "age_growth_or_decay_type", "age_growth_or_decay", "name"]
    _table_name = "DemandTechsServiceLink"
    _data_table_name = 'DemandTechsServiceLinkData'

    def __init__(self, name, scenario):
        DataObject.__init__(self, name, scenario)

        DemandTechsServiceLink._instances_by_key[self._key] = self

        self.service_link = None
        self.demand_technology = None
        self.definition = None
        self.reference_id = None
        self.geography = None
        self.other_index_1 = None
        self.other_index_2 = None
        self.interpolation_method = None
        self.extrapolation_method = None
        self.extrapolation_growth = None
        self.age_growth_or_decay_type = None
        self.age_growth_or_decay = None
        self.name = None

    def set_args(self, scenario, service_link=None, demand_technology=None, definition=None, reference_id=None,
                 geography=None, other_index_1=None, other_index_2=None, interpolation_method=None,
                 extrapolation_method=None, extrapolation_growth=None, age_growth_or_decay_type=None,
                 age_growth_or_decay=None, name=None):
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
        self.name = name

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (service_link, demand_technology, definition, reference_id, geography, other_index_1,
         other_index_2, interpolation_method, extrapolation_method, extrapolation_growth,
         age_growth_or_decay_type, age_growth_or_decay, name) = tup

        self.set_args(scenario, service_link=service_link, demand_technology=demand_technology, definition=definition,
                  reference_id=reference_id, geography=geography, other_index_1=other_index_1,
                  other_index_2=other_index_2, interpolation_method=interpolation_method,
                  extrapolation_method=extrapolation_method, extrapolation_growth=extrapolation_growth,
                  age_growth_or_decay_type=age_growth_or_decay_type,
                  age_growth_or_decay=age_growth_or_decay, name=name)

class DispatchFeedersAllocation(DataObject):
    _instances_by_key = {}
    _key_col = "name"
    _cols = ["name", "geography", "geography_map_key", "input_type", "interpolation_method",
             "extrapolation_method"]
    _table_name = "DispatchFeedersAllocation"
    _data_table_name = 'DispatchFeedersAllocationData'

    def __init__(self, name, scenario):
        DataObject.__init__(self, name, scenario)

        DispatchFeedersAllocation._instances_by_key[self._key] = self

        self.name = None
        self.geography = None
        self.geography_map_key = None
        self.input_type = None
        self.interpolation_method = None
        self.extrapolation_method = None

    def set_args(self, scenario, name=None, geography=None, geography_map_key=None, input_type=None,
                 interpolation_method=None, extrapolation_method=None):
        self.name = name
        self.geography = geography
        self.geography_map_key = geography_map_key
        self.input_type = input_type
        self.interpolation_method = interpolation_method
        self.extrapolation_method = extrapolation_method

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (name, geography, geography_map_key, input_type, interpolation_method, extrapolation_method) = tup

        self.set_args(scenario, name=name, geography=geography, geography_map_key=geography_map_key,
                  input_type=input_type, interpolation_method=interpolation_method,
                  extrapolation_method=extrapolation_method)

class DispatchNodeConfig(DataObject):
    _instances_by_key = {}
    _key_col = "supply_node"
    _cols = ["supply_node", "dispatch_order", "dispatch_window", "geography", "optimized"]
    _table_name = "DispatchNodeConfig"
    _data_table_name = None

    def __init__(self, supply_node, scenario):
        DataObject.__init__(self, supply_node, scenario)

        DispatchNodeConfig._instances_by_key[self._key] = self

        self.supply_node = None
        self.dispatch_order = None
        self.dispatch_window = None
        self.geography = None
        self.optimized = None

    def set_args(self, scenario, supply_node=None, dispatch_order=None, dispatch_window=None, geography=None,
                 optimized=None):
        self.supply_node = supply_node
        self.dispatch_order = dispatch_order
        self.dispatch_window = dispatch_window
        self.geography = geography
        self.optimized = optimized

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (supply_node, dispatch_order, dispatch_window, geography, optimized) = tup

        self.set_args(scenario, supply_node=supply_node, dispatch_order=dispatch_order, dispatch_window=dispatch_window,
                  geography=geography, optimized=optimized)

class DispatchTransmissionConstraint(DataObject):
    _instances_by_key = {}
    _key_col = "name"
    _cols = ["name", "description", "geography_description", "time_zone_id", "interpolation_method",
             "extrapolation_method", "hurdle_currency_id", "hurdle_currency_year_id", "energy_unit"]
    _table_name = "DispatchTransmissionConstraint"
    _data_table_name = 'DispatchTransmissionConstraintData'

    def __init__(self, name, scenario):
        DataObject.__init__(self, name, scenario)

        DispatchTransmissionConstraint._instances_by_key[self._key] = self

        self.name = None
        self.description = None
        self.geography_description = None
        self.time_zone_id = None
        self.interpolation_method = None
        self.extrapolation_method = None
        self.hurdle_currency_id = None
        self.hurdle_currency_year_id = None
        self.energy_unit = None

    def set_args(self, scenario, name=None, description=None, geography_description=None, time_zone_id=None,
                 interpolation_method=None, extrapolation_method=None, hurdle_currency_id=None,
                 hurdle_currency_year_id=None, energy_unit=None):
        self.name = name
        self.description = description
        self.geography_description = geography_description
        self.time_zone_id = time_zone_id
        self.interpolation_method = interpolation_method
        self.extrapolation_method = extrapolation_method
        self.hurdle_currency_id = hurdle_currency_id
        self.hurdle_currency_year_id = hurdle_currency_year_id
        self.energy_unit = energy_unit

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (name, description, geography_description, time_zone_id, interpolation_method,
         extrapolation_method, hurdle_currency_id, hurdle_currency_year_id, energy_unit) = tup

        self.set_args(scenario, name=name, description=description, geography_description=geography_description,
                  time_zone_id=time_zone_id, interpolation_method=interpolation_method,
                  extrapolation_method=extrapolation_method, hurdle_currency_id=hurdle_currency_id,
                  hurdle_currency_year_id=hurdle_currency_year_id, energy_unit=energy_unit)

class EV(DataObject):
    _instances_by_key = {}
    _key_col = "parent"
    _cols = ["parent", "gau", "dispatch_feeder", "resource_bin", "dispatch_constraint", "year",
             "month", "week", "hour", "day_type", "weather_datetime", "value", "id"]
    _table_name = "EV"
    _data_table_name = None

    def __init__(self, parent, scenario):
        DataObject.__init__(self, parent, scenario)

        EV._instances_by_key[self._key] = self

        self.parent = None
        self.gau = None
        self.dispatch_feeder = None
        self.resource_bin = None
        self.dispatch_constraint = None
        self.year = None
        self.month = None
        self.week = None
        self.hour = None
        self.day_type = None
        self.weather_datetime = None
        self.value = None
        self.id = None

    def set_args(self, scenario, parent=None, gau=None, dispatch_feeder=None, resource_bin=None, dispatch_constraint=None,
                 year=None, month=None, week=None, hour=None, day_type=None, weather_datetime=None,
                 value=None, id=None):
        self.parent = parent
        self.gau = gau
        self.dispatch_feeder = dispatch_feeder
        self.resource_bin = resource_bin
        self.dispatch_constraint = dispatch_constraint
        self.year = year
        self.month = month
        self.week = week
        self.hour = hour
        self.day_type = day_type
        self.weather_datetime = weather_datetime
        self.value = value
        self.id = id

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (parent, gau, dispatch_feeder, resource_bin, dispatch_constraint, year, month, week, hour,
         day_type, weather_datetime, value, id) = tup

        self.set_args(scenario, parent=parent, gau=gau, dispatch_feeder=dispatch_feeder, resource_bin=resource_bin,
                  dispatch_constraint=dispatch_constraint, year=year, month=month, week=week, hour=hour,
                  day_type=day_type, weather_datetime=weather_datetime, value=value, id=id)

class Electricity_Exports(DataObject):
    _instances_by_key = {}
    _key_col = "parent"
    _cols = ["parent", "gau", "dispatch_feeder", "resource_bin", "dispatch_constraint", "year",
             "month", "week", "hour", "day_type", "weather_datetime", "value", "id"]
    _table_name = "Electricity_Exports"
    _data_table_name = None

    def __init__(self, parent, scenario):
        DataObject.__init__(self, parent, scenario)

        Electricity_Exports._instances_by_key[self._key] = self

        self.parent = None
        self.gau = None
        self.dispatch_feeder = None
        self.resource_bin = None
        self.dispatch_constraint = None
        self.year = None
        self.month = None
        self.week = None
        self.hour = None
        self.day_type = None
        self.weather_datetime = None
        self.value = None
        self.id = None

    def set_args(self, scenario, parent=None, gau=None, dispatch_feeder=None, resource_bin=None, dispatch_constraint=None,
                 year=None, month=None, week=None, hour=None, day_type=None, weather_datetime=None,
                 value=None, id=None):
        self.parent = parent
        self.gau = gau
        self.dispatch_feeder = dispatch_feeder
        self.resource_bin = resource_bin
        self.dispatch_constraint = dispatch_constraint
        self.year = year
        self.month = month
        self.week = week
        self.hour = hour
        self.day_type = day_type
        self.weather_datetime = weather_datetime
        self.value = value
        self.id = id

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (parent, gau, dispatch_feeder, resource_bin, dispatch_constraint, year, month, week, hour,
         day_type, weather_datetime, value, id) = tup

        self.set_args(scenario, parent=parent, gau=gau, dispatch_feeder=dispatch_feeder, resource_bin=resource_bin,
                  dispatch_constraint=dispatch_constraint, year=year, month=month, week=week, hour=hour,
                  day_type=day_type, weather_datetime=weather_datetime, value=value, id=id)

class Electricity_Exports_CA(DataObject):
    _instances_by_key = {}
    _key_col = "parent"
    _cols = ["parent", "gau", "dispatch_feeder", "resource_bin", "dispatch_constraint", "year",
             "month", "week", "hour", "day_type", "weather_datetime", "value", "id"]
    _table_name = "Electricity_Exports_CA"
    _data_table_name = None

    def __init__(self, parent, scenario):
        DataObject.__init__(self, parent, scenario)

        Electricity_Exports_CA._instances_by_key[self._key] = self

        self.parent = None
        self.gau = None
        self.dispatch_feeder = None
        self.resource_bin = None
        self.dispatch_constraint = None
        self.year = None
        self.month = None
        self.week = None
        self.hour = None
        self.day_type = None
        self.weather_datetime = None
        self.value = None
        self.id = None

    def set_args(self, scenario, parent=None, gau=None, dispatch_feeder=None, resource_bin=None, dispatch_constraint=None,
                 year=None, month=None, week=None, hour=None, day_type=None, weather_datetime=None,
                 value=None, id=None):
        self.parent = parent
        self.gau = gau
        self.dispatch_feeder = dispatch_feeder
        self.resource_bin = resource_bin
        self.dispatch_constraint = dispatch_constraint
        self.year = year
        self.month = month
        self.week = week
        self.hour = hour
        self.day_type = day_type
        self.weather_datetime = weather_datetime
        self.value = value
        self.id = id

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (parent, gau, dispatch_feeder, resource_bin, dispatch_constraint, year, month, week, hour,
         day_type, weather_datetime, value, id) = tup

        self.set_args(scenario, parent=parent, gau=gau, dispatch_feeder=dispatch_feeder, resource_bin=resource_bin,
                  dispatch_constraint=dispatch_constraint, year=year, month=month, week=week, hour=hour,
                  day_type=day_type, weather_datetime=weather_datetime, value=value, id=id)

class Electricity_Imports(DataObject):
    _instances_by_key = {}
    _key_col = "parent"
    _cols = ["parent", "gau", "dispatch_feeder", "resource_bin", "dispatch_constraint", "year",
             "month", "week", "hour", "day_type", "weather_datetime", "value", "id"]
    _table_name = "Electricity_Imports"
    _data_table_name = None

    def __init__(self, parent, scenario):
        DataObject.__init__(self, parent, scenario)

        Electricity_Imports._instances_by_key[self._key] = self

        self.parent = None
        self.gau = None
        self.dispatch_feeder = None
        self.resource_bin = None
        self.dispatch_constraint = None
        self.year = None
        self.month = None
        self.week = None
        self.hour = None
        self.day_type = None
        self.weather_datetime = None
        self.value = None
        self.id = None

    def set_args(self, scenario, parent=None, gau=None, dispatch_feeder=None, resource_bin=None, dispatch_constraint=None,
                 year=None, month=None, week=None, hour=None, day_type=None, weather_datetime=None,
                 value=None, id=None):
        self.parent = parent
        self.gau = gau
        self.dispatch_feeder = dispatch_feeder
        self.resource_bin = resource_bin
        self.dispatch_constraint = dispatch_constraint
        self.year = year
        self.month = month
        self.week = week
        self.hour = hour
        self.day_type = day_type
        self.weather_datetime = weather_datetime
        self.value = value
        self.id = id

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (parent, gau, dispatch_feeder, resource_bin, dispatch_constraint, year, month, week, hour,
         day_type, weather_datetime, value, id) = tup

        self.set_args(scenario, parent=parent, gau=gau, dispatch_feeder=dispatch_feeder, resource_bin=resource_bin,
                  dispatch_constraint=dispatch_constraint, year=year, month=month, week=week, hour=hour,
                  day_type=day_type, weather_datetime=weather_datetime, value=value, id=id)

class FinalEnergy(DataObject):
    _instances_by_key = {}
    _key_col = "name"
    _cols = ["name", "shape"]
    _table_name = "FinalEnergy"
    _data_table_name = None

    def __init__(self, name, scenario):
        DataObject.__init__(self, name, scenario)

        FinalEnergy._instances_by_key[self._key] = self

        self.name = None
        self.shape = None

    def set_args(self, scenario, name=None, shape=None):
        self.name = name
        self.shape = shape

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (name, shape) = tup

        self.set_args(scenario, name=name, shape=shape)

class GreenhouseGases(DataObject):
    _instances_by_key = {}
    _key_col = "name"
    _cols = ["name", "long_name"]
    _table_name = "GreenhouseGases"
    _data_table_name = None

    def __init__(self, name, scenario):
        DataObject.__init__(self, name, scenario)

        GreenhouseGases._instances_by_key[self._key] = self

        self.name = None
        self.long_name = None

    def set_args(self, scenario, name=None, long_name=None):
        self.name = name
        self.long_name = long_name

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (name, long_name) = tup

        self.set_args(scenario, name=name, long_name=long_name)

class ImportCost(DataObject):
    _instances_by_key = {}
    _key_col = "import_node"
    _cols = ["import_node", "source", "notes", "geography", "currency", "currency_year_id",
             "denominator_unit", "interpolation_method", "extrapolation_method",
             "extrapolation_growth", "cost_method_id"]
    _table_name = "ImportCost"
    _data_table_name = 'ImportCostData'

    def __init__(self, import_node, scenario):
        DataObject.__init__(self, import_node, scenario)

        ImportCost._instances_by_key[self._key] = self

        self.import_node = None
        self.source = None
        self.notes = None
        self.geography = None
        self.currency = None
        self.currency_year_id = None
        self.denominator_unit = None
        self.interpolation_method = None
        self.extrapolation_method = None
        self.extrapolation_growth = None
        self.cost_method_id = None

    def set_args(self, scenario, import_node=None, source=None, notes=None, geography=None, currency=None,
                 currency_year_id=None, denominator_unit=None, interpolation_method=None,
                 extrapolation_method=None, extrapolation_growth=None, cost_method_id=None):
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

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (import_node, source, notes, geography, currency, currency_year_id, denominator_unit,
         interpolation_method, extrapolation_method, extrapolation_growth, cost_method_id) = tup

        self.set_args(scenario, import_node=import_node, source=source, notes=notes, geography=geography,
                  currency=currency, currency_year_id=currency_year_id, denominator_unit=denominator_unit,
                  interpolation_method=interpolation_method, extrapolation_method=extrapolation_method,
                  extrapolation_growth=extrapolation_growth, cost_method_id=cost_method_id)

class ImportPrimaryCostMethod(DataObject):
    _instances_by_key = {}
    _key_col = "name"
    _cols = ["id", "name"]
    _table_name = "ImportPrimaryCostMethod"
    _data_table_name = None

    def __init__(self, name, scenario):
        DataObject.__init__(self, name, scenario)

        ImportPrimaryCostMethod._instances_by_key[self._key] = self

        self.id = None
        self.name = None

    def set_args(self, scenario, id=None, name=None):
        self.id = id
        self.name = name

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (id, name) = tup

        self.set_args(scenario, id=id, name=name)

class IndexLevels(DataObject):
    _instances_by_key = {}
    _key_col = "index_level"
    _cols = ["id", "index_level", "data_column_name"]
    _table_name = "IndexLevels"
    _data_table_name = None

    def __init__(self, index_level, scenario):
        DataObject.__init__(self, index_level, scenario)

        IndexLevels._instances_by_key[self._key] = self

        self.id = None
        self.index_level = None
        self.data_column_name = None

    def set_args(self, scenario, id=None, index_level=None, data_column_name=None):
        self.id = id
        self.index_level = index_level
        self.data_column_name = data_column_name

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (id, index_level, data_column_name) = tup

        self.set_args(scenario, id=id, index_level=index_level, data_column_name=data_column_name)

class Industrial_MachineDrives(DataObject):
    _instances_by_key = {}
    _key_col = "parent"
    _cols = ["parent", "gau", "dispatch_feeder", "resource_bin", "dispatch_constraint", "year",
             "month", "week", "hour", "day_type", "weather_datetime", "value", "id"]
    _table_name = "Industrial_MachineDrives"
    _data_table_name = None

    def __init__(self, parent, scenario):
        DataObject.__init__(self, parent, scenario)

        Industrial_MachineDrives._instances_by_key[self._key] = self

        self.parent = None
        self.gau = None
        self.dispatch_feeder = None
        self.resource_bin = None
        self.dispatch_constraint = None
        self.year = None
        self.month = None
        self.week = None
        self.hour = None
        self.day_type = None
        self.weather_datetime = None
        self.value = None
        self.id = None

    def set_args(self, scenario, parent=None, gau=None, dispatch_feeder=None, resource_bin=None, dispatch_constraint=None,
                 year=None, month=None, week=None, hour=None, day_type=None, weather_datetime=None,
                 value=None, id=None):
        self.parent = parent
        self.gau = gau
        self.dispatch_feeder = dispatch_feeder
        self.resource_bin = resource_bin
        self.dispatch_constraint = dispatch_constraint
        self.year = year
        self.month = month
        self.week = week
        self.hour = hour
        self.day_type = day_type
        self.weather_datetime = weather_datetime
        self.value = value
        self.id = id

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (parent, gau, dispatch_feeder, resource_bin, dispatch_constraint, year, month, week, hour,
         day_type, weather_datetime, value, id) = tup

        self.set_args(scenario, parent=parent, gau=gau, dispatch_feeder=dispatch_feeder, resource_bin=resource_bin,
                  dispatch_constraint=dispatch_constraint, year=year, month=month, week=week, hour=hour,
                  day_type=day_type, weather_datetime=weather_datetime, value=value, id=id)

class Industrial_Other(DataObject):
    _instances_by_key = {}
    _key_col = "parent"
    _cols = ["parent", "gau", "dispatch_feeder", "resource_bin", "dispatch_constraint", "year",
             "month", "week", "hour", "day_type", "weather_datetime", "value", "id"]
    _table_name = "Industrial_Other"
    _data_table_name = None

    def __init__(self, parent, scenario):
        DataObject.__init__(self, parent, scenario)

        Industrial_Other._instances_by_key[self._key] = self

        self.parent = None
        self.gau = None
        self.dispatch_feeder = None
        self.resource_bin = None
        self.dispatch_constraint = None
        self.year = None
        self.month = None
        self.week = None
        self.hour = None
        self.day_type = None
        self.weather_datetime = None
        self.value = None
        self.id = None

    def set_args(self, scenario, parent=None, gau=None, dispatch_feeder=None, resource_bin=None, dispatch_constraint=None,
                 year=None, month=None, week=None, hour=None, day_type=None, weather_datetime=None,
                 value=None, id=None):
        self.parent = parent
        self.gau = gau
        self.dispatch_feeder = dispatch_feeder
        self.resource_bin = resource_bin
        self.dispatch_constraint = dispatch_constraint
        self.year = year
        self.month = month
        self.week = week
        self.hour = hour
        self.day_type = day_type
        self.weather_datetime = weather_datetime
        self.value = value
        self.id = id

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (parent, gau, dispatch_feeder, resource_bin, dispatch_constraint, year, month, week, hour,
         day_type, weather_datetime, value, id) = tup

        self.set_args(scenario, parent=parent, gau=gau, dispatch_feeder=dispatch_feeder, resource_bin=resource_bin,
                  dispatch_constraint=dispatch_constraint, year=year, month=month, week=week, hour=hour,
                  day_type=day_type, weather_datetime=weather_datetime, value=value, id=id)

class Industrial_ProcessHeating(DataObject):
    _instances_by_key = {}
    _key_col = "parent"
    _cols = ["parent", "gau", "dispatch_feeder", "resource_bin", "dispatch_constraint", "year",
             "month", "week", "hour", "day_type", "weather_datetime", "value", "id"]
    _table_name = "Industrial_ProcessHeating"
    _data_table_name = None

    def __init__(self, parent, scenario):
        DataObject.__init__(self, parent, scenario)

        Industrial_ProcessHeating._instances_by_key[self._key] = self

        self.parent = None
        self.gau = None
        self.dispatch_feeder = None
        self.resource_bin = None
        self.dispatch_constraint = None
        self.year = None
        self.month = None
        self.week = None
        self.hour = None
        self.day_type = None
        self.weather_datetime = None
        self.value = None
        self.id = None

    def set_args(self, scenario, parent=None, gau=None, dispatch_feeder=None, resource_bin=None, dispatch_constraint=None,
                 year=None, month=None, week=None, hour=None, day_type=None, weather_datetime=None,
                 value=None, id=None):
        self.parent = parent
        self.gau = gau
        self.dispatch_feeder = dispatch_feeder
        self.resource_bin = resource_bin
        self.dispatch_constraint = dispatch_constraint
        self.year = year
        self.month = month
        self.week = week
        self.hour = hour
        self.day_type = day_type
        self.weather_datetime = weather_datetime
        self.value = value
        self.id = id

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (parent, gau, dispatch_feeder, resource_bin, dispatch_constraint, year, month, week, hour,
         day_type, weather_datetime, value, id) = tup

        self.set_args(scenario, parent=parent, gau=gau, dispatch_feeder=dispatch_feeder, resource_bin=resource_bin,
                  dispatch_constraint=dispatch_constraint, year=year, month=month, week=week, hour=hour,
                  day_type=day_type, weather_datetime=weather_datetime, value=value, id=id)

class OtherIndexesData_copy(DataObject):
    _instances_by_key = {}
    _key_col = "name"
    _cols = ["id", "name", "other_index"]
    _table_name = "OtherIndexesData_copy"
    _data_table_name = None

    def __init__(self, name, scenario):
        DataObject.__init__(self, name, scenario)

        OtherIndexesData_copy._instances_by_key[self._key] = self

        self.id = None
        self.name = None
        self.other_index = None

    def set_args(self, scenario, id=None, name=None, other_index=None):
        self.id = id
        self.name = name
        self.other_index = other_index

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (id, name, other_index) = tup

        self.set_args(scenario, id=id, name=name, other_index=other_index)

class PrimaryCost(DataObject):
    _instances_by_key = {}
    _key_col = "primary_node"
    _cols = ["primary_node", "geography", "other_index_1", "currency", "currency_year_id",
             "denominator_unit", "interpolation_method", "extrapolation_method",
             "extrapolation_growth", "cost_method_id"]
    _table_name = "PrimaryCost"
    _data_table_name = 'PrimaryCostData'

    def __init__(self, primary_node, scenario):
        DataObject.__init__(self, primary_node, scenario)

        PrimaryCost._instances_by_key[self._key] = self

        self.primary_node = None
        self.geography = None
        self.other_index_1 = None
        self.currency = None
        self.currency_year_id = None
        self.denominator_unit = None
        self.interpolation_method = None
        self.extrapolation_method = None
        self.extrapolation_growth = None
        self.cost_method_id = None

    def set_args(self, scenario, primary_node=None, geography=None, other_index_1=None, currency=None,
                 currency_year_id=None, denominator_unit=None, interpolation_method=None,
                 extrapolation_method=None, extrapolation_growth=None, cost_method_id=None):
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

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (primary_node, geography, other_index_1, currency, currency_year_id, denominator_unit,
         interpolation_method, extrapolation_method, extrapolation_growth, cost_method_id) = tup

        self.set_args(scenario, primary_node=primary_node, geography=geography, other_index_1=other_index_1,
                  currency=currency, currency_year_id=currency_year_id, denominator_unit=denominator_unit,
                  interpolation_method=interpolation_method, extrapolation_method=extrapolation_method,
                  extrapolation_growth=extrapolation_growth, cost_method_id=cost_method_id)

class Shapes(DataObject):
    _instances_by_key = {}
    _key_col = "name"
    _cols = ["name", "shape_type", "shape_unit_type", "time_zone_id", "geography", "other_index_1",
             "other_index_2", "geography_map_key", "interpolation_method", "extrapolation_method",
             "input_type", "supply_or_demand_side", "is_active"]
    _table_name = "Shapes"
    _data_table_name = None

    def __init__(self, name, scenario):
        DataObject.__init__(self, name, scenario)

        Shapes._instances_by_key[self._key] = self

        self.name = None
        self.shape_type = None
        self.shape_unit_type = None
        self.time_zone_id = None
        self.geography = None
        self.other_index_1 = None
        self.other_index_2 = None
        self.geography_map_key = None
        self.interpolation_method = None
        self.extrapolation_method = None
        self.input_type = None
        self.supply_or_demand_side = None
        self.is_active = None

    def set_args(self, scenario, name=None, shape_type=None, shape_unit_type=None, time_zone_id=None, geography=None,
                 other_index_1=None, other_index_2=None, geography_map_key=None,
                 interpolation_method=None, extrapolation_method=None, input_type=None,
                 supply_or_demand_side=None, is_active=None):
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
        self.supply_or_demand_side = supply_or_demand_side
        self.is_active = is_active

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (name, shape_type, shape_unit_type, time_zone_id, geography, other_index_1, other_index_2,
         geography_map_key, interpolation_method, extrapolation_method, input_type,
         supply_or_demand_side, is_active) = tup

        self.set_args(scenario, name=name, shape_type=shape_type, shape_unit_type=shape_unit_type,
                  time_zone_id=time_zone_id, geography=geography, other_index_1=other_index_1,
                  other_index_2=other_index_2, geography_map_key=geography_map_key,
                  interpolation_method=interpolation_method, extrapolation_method=extrapolation_method,
                  input_type=input_type, supply_or_demand_side=supply_or_demand_side, is_active=is_active)

class StorageTechsCapacityCapitalCost(DataObject):
    _instances_by_key = {}
    _key_col = "supply_tech"
    _cols = ["supply_tech", "definition", "reference_tech", "currency", "geography",
             "currency_year_id", "capacity_or_energy_unit", "is_levelized", "cost_of_capital",
             "interpolation_method", "extrapolation_method", "time_unit"]
    _table_name = "StorageTechsCapacityCapitalCost"
    _data_table_name = None

    def __init__(self, supply_tech, scenario):
        DataObject.__init__(self, supply_tech, scenario)

        StorageTechsCapacityCapitalCost._instances_by_key[self._key] = self

        self.supply_tech = None
        self.definition = None
        self.reference_tech = None
        self.currency = None
        self.geography = None
        self.currency_year_id = None
        self.capacity_or_energy_unit = None
        self.is_levelized = None
        self.cost_of_capital = None
        self.interpolation_method = None
        self.extrapolation_method = None
        self.time_unit = None

    def set_args(self, scenario, supply_tech=None, definition=None, reference_tech=None, currency=None, geography=None,
                 currency_year_id=None, capacity_or_energy_unit=None, is_levelized=None,
                 cost_of_capital=None, interpolation_method=None, extrapolation_method=None,
                 time_unit=None):
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

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (supply_tech, definition, reference_tech, currency, geography, currency_year_id,
         capacity_or_energy_unit, is_levelized, cost_of_capital, interpolation_method,
         extrapolation_method, time_unit) = tup

        self.set_args(scenario, supply_tech=supply_tech, definition=definition, reference_tech=reference_tech,
                  currency=currency, geography=geography, currency_year_id=currency_year_id,
                  capacity_or_energy_unit=capacity_or_energy_unit, is_levelized=is_levelized,
                  cost_of_capital=cost_of_capital, interpolation_method=interpolation_method,
                  extrapolation_method=extrapolation_method, time_unit=time_unit)

class StorageTechsDuration(DataObject):
    _instances_by_key = {}
    _key_col = "supply_tech"
    _cols = ["supply_tech", "definition", "reference_tech", "geography", "interpolation_method",
             "extrapolation_method", "time_unit"]
    _table_name = "StorageTechsDuration"
    _data_table_name = 'StorageTechsDurationData'

    def __init__(self, supply_tech, scenario):
        DataObject.__init__(self, supply_tech, scenario)

        StorageTechsDuration._instances_by_key[self._key] = self

        self.supply_tech = None
        self.definition = None
        self.reference_tech = None
        self.geography = None
        self.interpolation_method = None
        self.extrapolation_method = None
        self.time_unit = None

    def set_args(self, scenario, supply_tech=None, definition=None, reference_tech=None, geography=None,
                 interpolation_method=None, extrapolation_method=None, time_unit=None):
        self.supply_tech = supply_tech
        self.definition = definition
        self.reference_tech = reference_tech
        self.geography = geography
        self.interpolation_method = interpolation_method
        self.extrapolation_method = extrapolation_method
        self.time_unit = time_unit

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (supply_tech, definition, reference_tech, geography, interpolation_method,
         extrapolation_method, time_unit) = tup

        self.set_args(scenario, supply_tech=supply_tech, definition=definition, reference_tech=reference_tech,
                  geography=geography, interpolation_method=interpolation_method,
                  extrapolation_method=extrapolation_method, time_unit=time_unit)

class StorageTechsEnergyCapitalCost(DataObject):
    _instances_by_key = {}
    _key_col = "supply_tech"
    _cols = ["supply_tech", "definition", "reference_tech", "currency", "geography",
             "currency_year_id", "energy_unit", "is_levelized", "cost_of_capital",
             "interpolation_method", "extrapolation_method"]
    _table_name = "StorageTechsEnergyCapitalCost"
    _data_table_name = None

    def __init__(self, supply_tech, scenario):
        DataObject.__init__(self, supply_tech, scenario)

        StorageTechsEnergyCapitalCost._instances_by_key[self._key] = self

        self.supply_tech = None
        self.definition = None
        self.reference_tech = None
        self.currency = None
        self.geography = None
        self.currency_year_id = None
        self.energy_unit = None
        self.is_levelized = None
        self.cost_of_capital = None
        self.interpolation_method = None
        self.extrapolation_method = None

    def set_args(self, scenario, supply_tech=None, definition=None, reference_tech=None, currency=None, geography=None,
                 currency_year_id=None, energy_unit=None, is_levelized=None, cost_of_capital=None,
                 interpolation_method=None, extrapolation_method=None):
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

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (supply_tech, definition, reference_tech, currency, geography, currency_year_id,
         energy_unit, is_levelized, cost_of_capital, interpolation_method, extrapolation_method) = tup

        self.set_args(scenario, supply_tech=supply_tech, definition=definition, reference_tech=reference_tech,
                  currency=currency, geography=geography, currency_year_id=currency_year_id,
                  energy_unit=energy_unit, is_levelized=is_levelized, cost_of_capital=cost_of_capital,
                  interpolation_method=interpolation_method, extrapolation_method=extrapolation_method)

class Streetlights(DataObject):
    _instances_by_key = {}
    _key_col = "parent"
    _cols = ["parent", "gau", "dispatch_feeder", "resource_bin", "dispatch_constraint", "year",
             "month", "week", "hour", "day_type", "weather_datetime", "value", "id"]
    _table_name = "Streetlights"
    _data_table_name = None

    def __init__(self, parent, scenario):
        DataObject.__init__(self, parent, scenario)

        Streetlights._instances_by_key[self._key] = self

        self.parent = None
        self.gau = None
        self.dispatch_feeder = None
        self.resource_bin = None
        self.dispatch_constraint = None
        self.year = None
        self.month = None
        self.week = None
        self.hour = None
        self.day_type = None
        self.weather_datetime = None
        self.value = None
        self.id = None

    def set_args(self, scenario, parent=None, gau=None, dispatch_feeder=None, resource_bin=None, dispatch_constraint=None,
                 year=None, month=None, week=None, hour=None, day_type=None, weather_datetime=None,
                 value=None, id=None):
        self.parent = parent
        self.gau = gau
        self.dispatch_feeder = dispatch_feeder
        self.resource_bin = resource_bin
        self.dispatch_constraint = dispatch_constraint
        self.year = year
        self.month = month
        self.week = week
        self.hour = hour
        self.day_type = day_type
        self.weather_datetime = weather_datetime
        self.value = value
        self.id = id

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (parent, gau, dispatch_feeder, resource_bin, dispatch_constraint, year, month, week, hour,
         day_type, weather_datetime, value, id) = tup

        self.set_args(scenario, parent=parent, gau=gau, dispatch_feeder=dispatch_feeder, resource_bin=resource_bin,
                  dispatch_constraint=dispatch_constraint, year=year, month=month, week=week, hour=hour,
                  day_type=day_type, weather_datetime=weather_datetime, value=value, id=id)

class SupplyCapacityFactor(DataObject):
    _instances_by_key = {}
    _key_col = "supply_node"
    _cols = ["supply_node", "geography", "unit", "interpolation_method", "extrapolation_method",
             "extrapolation_growth", "age_growth_or_decay_type", "age_growth_or_decay"]
    _table_name = "SupplyCapacityFactor"
    _data_table_name = 'SupplyCapacityFactorData'

    def __init__(self, supply_node, scenario):
        DataObject.__init__(self, supply_node, scenario)

        SupplyCapacityFactor._instances_by_key[self._key] = self

        self.supply_node = None
        self.geography = None
        self.unit = None
        self.interpolation_method = None
        self.extrapolation_method = None
        self.extrapolation_growth = None
        self.age_growth_or_decay_type = None
        self.age_growth_or_decay = None

    def set_args(self, scenario, supply_node=None, geography=None, unit=None, interpolation_method=None,
                 extrapolation_method=None, extrapolation_growth=None, age_growth_or_decay_type=None,
                 age_growth_or_decay=None):
        self.supply_node = supply_node
        self.geography = geography
        self.unit = unit
        self.interpolation_method = interpolation_method
        self.extrapolation_method = extrapolation_method
        self.extrapolation_growth = extrapolation_growth
        self.age_growth_or_decay_type = age_growth_or_decay_type
        self.age_growth_or_decay = age_growth_or_decay

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (supply_node, geography, unit, interpolation_method, extrapolation_method,
         extrapolation_growth, age_growth_or_decay_type, age_growth_or_decay) = tup

        self.set_args(scenario, supply_node=supply_node, geography=geography, unit=unit,
                  interpolation_method=interpolation_method, extrapolation_method=extrapolation_method,
                  extrapolation_growth=extrapolation_growth,
                  age_growth_or_decay_type=age_growth_or_decay_type,
                  age_growth_or_decay=age_growth_or_decay)

class SupplyCost(DataObject):
    _instances_by_key = {}
    _key_col = "name"
    _cols = ["name", "source", "additional_notes", "supply_node", "geography", "supply_cost_type_id",
             "currency", "currency_year_id", "energy_or_capacity_unit", "time_unit",
             "is_capital_cost", "cost_of_capital", "book_life", "throughput_correlation",
             "interpolation_method", "extrapolation_method", "extrapolation_growth"]
    _table_name = "SupplyCost"
    _data_table_name = 'SupplyCostData'

    def __init__(self, name, scenario):
        DataObject.__init__(self, name, scenario)

        SupplyCost._instances_by_key[self._key] = self

        self.name = None
        self.source = None
        self.additional_notes = None
        self.supply_node = None
        self.geography = None
        self.supply_cost_type_id = None
        self.currency = None
        self.currency_year_id = None
        self.energy_or_capacity_unit = None
        self.time_unit = None
        self.is_capital_cost = None
        self.cost_of_capital = None
        self.book_life = None
        self.throughput_correlation = None
        self.interpolation_method = None
        self.extrapolation_method = None
        self.extrapolation_growth = None

    def set_args(self, scenario, name=None, source=None, additional_notes=None, supply_node=None, geography=None,
                 supply_cost_type_id=None, currency=None, currency_year_id=None,
                 energy_or_capacity_unit=None, time_unit=None, is_capital_cost=None, cost_of_capital=None,
                 book_life=None, throughput_correlation=None, interpolation_method=None,
                 extrapolation_method=None, extrapolation_growth=None):
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

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (name, source, additional_notes, supply_node, geography, supply_cost_type_id, currency,
         currency_year_id, energy_or_capacity_unit, time_unit, is_capital_cost, cost_of_capital,
         book_life, throughput_correlation, interpolation_method, extrapolation_method,
         extrapolation_growth) = tup

        self.set_args(scenario, name=name, source=source, additional_notes=additional_notes, supply_node=supply_node,
                  geography=geography, supply_cost_type_id=supply_cost_type_id, currency=currency,
                  currency_year_id=currency_year_id, energy_or_capacity_unit=energy_or_capacity_unit,
                  time_unit=time_unit, is_capital_cost=is_capital_cost, cost_of_capital=cost_of_capital,
                  book_life=book_life, throughput_correlation=throughput_correlation,
                  interpolation_method=interpolation_method, extrapolation_method=extrapolation_method,
                  extrapolation_growth=extrapolation_growth)

class SupplyEfficiency(DataObject):
    _instances_by_key = {}
    _key_col = "name"
    _cols = ["name", "geography", "source", "notes", "input_unit", "output_unit",
             "interpolation_method", "extrapolation_method", "extrapolation_growth"]
    _table_name = "SupplyEfficiency"
    _data_table_name = 'SupplyEfficiencyData'

    def __init__(self, name, scenario):
        DataObject.__init__(self, name, scenario)

        SupplyEfficiency._instances_by_key[self._key] = self

        self.name = None
        self.geography = None
        self.source = None
        self.notes = None
        self.input_unit = None
        self.output_unit = None
        self.interpolation_method = None
        self.extrapolation_method = None
        self.extrapolation_growth = None

    def set_args(self, scenario, name=None, geography=None, source=None, notes=None, input_unit=None, output_unit=None,
                 interpolation_method=None, extrapolation_method=None, extrapolation_growth=None):
        self.name = name
        self.geography = geography
        self.source = source
        self.notes = notes
        self.input_unit = input_unit
        self.output_unit = output_unit
        self.interpolation_method = interpolation_method
        self.extrapolation_method = extrapolation_method
        self.extrapolation_growth = extrapolation_growth

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (name, geography, source, notes, input_unit, output_unit, interpolation_method,
         extrapolation_method, extrapolation_growth) = tup

        self.set_args(scenario, name=name, geography=geography, source=source, notes=notes, input_unit=input_unit,
                  output_unit=output_unit, interpolation_method=interpolation_method,
                  extrapolation_method=extrapolation_method, extrapolation_growth=extrapolation_growth)

class SupplyEmissions(DataObject):
    _instances_by_key = {}
    _key_col = "supply_node"
    _cols = ["supply_node", "geography", "other_index_1", "mass_unit", "denominator_unit",
             "interpolation_method", "extrapolation_method", "extrapolation_growth", "source", "notes"]
    _table_name = "SupplyEmissions"
    _data_table_name = 'SupplyEmissionsData'

    def __init__(self, supply_node, scenario):
        DataObject.__init__(self, supply_node, scenario)

        SupplyEmissions._instances_by_key[self._key] = self

        self.supply_node = None
        self.geography = None
        self.other_index_1 = None
        self.mass_unit = None
        self.denominator_unit = None
        self.interpolation_method = None
        self.extrapolation_method = None
        self.extrapolation_growth = None
        self.source = None
        self.notes = None

    def set_args(self, scenario, supply_node=None, geography=None, other_index_1=None, mass_unit=None,
                 denominator_unit=None, interpolation_method=None, extrapolation_method=None,
                 extrapolation_growth=None, source=None, notes=None):
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

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (supply_node, geography, other_index_1, mass_unit, denominator_unit, interpolation_method,
         extrapolation_method, extrapolation_growth, source, notes) = tup

        self.set_args(scenario, supply_node=supply_node, geography=geography, other_index_1=other_index_1,
                  mass_unit=mass_unit, denominator_unit=denominator_unit,
                  interpolation_method=interpolation_method, extrapolation_method=extrapolation_method,
                  extrapolation_growth=extrapolation_growth, source=source, notes=notes)

class SupplyExport(DataObject):
    _instances_by_key = {}
    _key_col = "supply_node"
    _cols = ["supply_node", "geography", "other_index_1", "unit", "interpolation_method",
             "extrapolation_method", "extrapolation_growth", "geography_map_key"]
    _table_name = "SupplyExport"
    _data_table_name = 'SupplyExportData'

    def __init__(self, supply_node, scenario):
        DataObject.__init__(self, supply_node, scenario)

        SupplyExport._instances_by_key[self._key] = self

        self.supply_node = None
        self.geography = None
        self.other_index_1 = None
        self.unit = None
        self.interpolation_method = None
        self.extrapolation_method = None
        self.extrapolation_growth = None
        self.geography_map_key = None

    def set_args(self, scenario, supply_node=None, geography=None, other_index_1=None, unit=None,
                 interpolation_method=None, extrapolation_method=None, extrapolation_growth=None,
                 geography_map_key=None):
        self.supply_node = supply_node
        self.geography = geography
        self.other_index_1 = other_index_1
        self.unit = unit
        self.interpolation_method = interpolation_method
        self.extrapolation_method = extrapolation_method
        self.extrapolation_growth = extrapolation_growth
        self.geography_map_key = geography_map_key

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (supply_node, geography, other_index_1, unit, interpolation_method, extrapolation_method,
         extrapolation_growth, geography_map_key) = tup

        self.set_args(scenario, supply_node=supply_node, geography=geography, other_index_1=other_index_1, unit=unit,
                  interpolation_method=interpolation_method, extrapolation_method=extrapolation_method,
                  extrapolation_growth=extrapolation_growth, geography_map_key=geography_map_key)

class SupplyExportMeasures(DataObject):
    _instances_by_key = {}
    _key_col = "name"
    _cols = ["supply_node", "name", "geography", "other_index_1", "interpolation_method",
             "extrapolation_method", "unit"]
    _table_name = "SupplyExportMeasures"
    _data_table_name = 'SupplyExportMeasuresData'

    def __init__(self, name, scenario):
        DataObject.__init__(self, name, scenario)

        SupplyExportMeasures._instances_by_key[self._key] = self

        self.supply_node = None
        self.name = None
        self.geography = None
        self.other_index_1 = None
        self.interpolation_method = None
        self.extrapolation_method = None
        self.unit = None

    def set_args(self, scenario, supply_node=None, name=None, geography=None, other_index_1=None,
                 interpolation_method=None, extrapolation_method=None, unit=None):
        self.supply_node = supply_node
        self.name = name
        self.geography = geography
        self.other_index_1 = other_index_1
        self.interpolation_method = interpolation_method
        self.extrapolation_method = extrapolation_method
        self.unit = unit

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (supply_node, name, geography, other_index_1, interpolation_method, extrapolation_method,
         unit) = tup

        self.set_args(scenario, supply_node=supply_node, name=name, geography=geography, other_index_1=other_index_1,
                  interpolation_method=interpolation_method, extrapolation_method=extrapolation_method,
                  unit=unit)

class SupplyNodes(DataObject):
    _instances_by_key = {}
    _key_col = "name"
    _cols = ["name", "supply_type", "tradable_geography", "is_active", "is_curtailable",
             "is_exportable", "is_flexible", "residual_supply_node", "mean_lifetime",
             "lifetime_variance", "max_lifetime", "min_lifetime", "stock_decay_function",
             "cost_of_capital", "book_life", "geography_map_key", "shape", "max_lag_hours",
             "max_lead_hours", "enforce_potential_constraint", "overflow_node"]
    _table_name = "SupplyNodes"
    _data_table_name = None

    def __init__(self, name, scenario):
        DataObject.__init__(self, name, scenario)

        SupplyNodes._instances_by_key[self._key] = self

        self.name = None
        self.supply_type = None
        self.tradable_geography = None
        self.is_active = None
        self.is_curtailable = None
        self.is_exportable = None
        self.is_flexible = None
        self.residual_supply_node = None
        self.mean_lifetime = None
        self.lifetime_variance = None
        self.max_lifetime = None
        self.min_lifetime = None
        self.stock_decay_function = None
        self.cost_of_capital = None
        self.book_life = None
        self.geography_map_key = None
        self.shape = None
        self.max_lag_hours = None
        self.max_lead_hours = None
        self.enforce_potential_constraint = None
        self.overflow_node = None

    def set_args(self, scenario, name=None, supply_type=None, tradable_geography=None, is_active=None, is_curtailable=None,
                 is_exportable=None, is_flexible=None, residual_supply_node=None, mean_lifetime=None,
                 lifetime_variance=None, max_lifetime=None, min_lifetime=None, stock_decay_function=None,
                 cost_of_capital=None, book_life=None, geography_map_key=None, shape=None,
                 max_lag_hours=None, max_lead_hours=None, enforce_potential_constraint=None,
                 overflow_node=None):
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

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (name, supply_type, tradable_geography, is_active, is_curtailable, is_exportable,
         is_flexible, residual_supply_node, mean_lifetime, lifetime_variance, max_lifetime,
         min_lifetime, stock_decay_function, cost_of_capital, book_life, geography_map_key, shape,
         max_lag_hours, max_lead_hours, enforce_potential_constraint, overflow_node) = tup

        self.set_args(scenario, name=name, supply_type=supply_type, tradable_geography=tradable_geography,
                  is_active=is_active, is_curtailable=is_curtailable, is_exportable=is_exportable,
                  is_flexible=is_flexible, residual_supply_node=residual_supply_node,
                  mean_lifetime=mean_lifetime, lifetime_variance=lifetime_variance,
                  max_lifetime=max_lifetime, min_lifetime=min_lifetime,
                  stock_decay_function=stock_decay_function, cost_of_capital=cost_of_capital,
                  book_life=book_life, geography_map_key=geography_map_key, shape=shape,
                  max_lag_hours=max_lag_hours, max_lead_hours=max_lead_hours,
                  enforce_potential_constraint=enforce_potential_constraint, overflow_node=overflow_node)

class SupplyPotential(DataObject):
    _instances_by_key = {}
    _key_col = "supply_node"
    _cols = ["supply_node", "geography", "other_index_1", "unit", "time_unit", "interpolation_method",
             "extrapolation_growth", "extrapolation_method", "geography_map_key"]
    _table_name = "SupplyPotential"
    _data_table_name = 'SupplyPotentialData'

    def __init__(self, supply_node, scenario):
        DataObject.__init__(self, supply_node, scenario)

        SupplyPotential._instances_by_key[self._key] = self

        self.enforce = None
        self.supply_node = None
        self.geography = None
        self.other_index_1 = None
        self.unit = None
        self.time_unit = None
        self.interpolation_method = None
        self.extrapolation_growth = None
        self.extrapolation_method = None
        self.geography_map_key = None

    def set_args(self, scenario, enforce=False, supply_node=None, geography=None, other_index_1=None, unit=None,
                 time_unit=None, interpolation_method=None, extrapolation_growth=None,
                 extrapolation_method=None, geography_map_key=None):
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

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (supply_node, geography, other_index_1, unit, time_unit, interpolation_method,
         extrapolation_growth, extrapolation_method, geography_map_key) = tup

        self.set_args(scenario, kwargs.get("enforce", False), supply_node=supply_node, geography=geography,
                  other_index_1=other_index_1, unit=unit, time_unit=time_unit,
                  interpolation_method=interpolation_method, extrapolation_growth=extrapolation_growth,
                  extrapolation_method=extrapolation_method, geography_map_key=geography_map_key)

class SupplyPotentialConversion(DataObject):
    _instances_by_key = {}
    _key_col = "supply_node"
    _cols = ["supply_node", "geography", "other_index_1", "energy_unit_numerator",
             "resource_unit_denominator", "interpolation_method", "extrapolation_method",
             "extrapolation_growth"]
    _table_name = "SupplyPotentialConversion"
    _data_table_name = 'SupplyPotentialConversionData'

    def __init__(self, supply_node, scenario):
        DataObject.__init__(self, supply_node, scenario)

        SupplyPotentialConversion._instances_by_key[self._key] = self

        self.supply_node = None
        self.geography = None
        self.other_index_1 = None
        self.energy_unit_numerator = None
        self.resource_unit_denominator = None
        self.interpolation_method = None
        self.extrapolation_method = None
        self.extrapolation_growth = None

    def set_args(self, scenario, supply_node=None, geography=None, other_index_1=None, energy_unit_numerator=None,
                 resource_unit_denominator=None, interpolation_method=None, extrapolation_method=None,
                 extrapolation_growth=None):
        self.supply_node = supply_node
        self.geography = geography
        self.other_index_1 = other_index_1
        self.energy_unit_numerator = energy_unit_numerator
        self.resource_unit_denominator = resource_unit_denominator
        self.interpolation_method = interpolation_method
        self.extrapolation_method = extrapolation_method
        self.extrapolation_growth = extrapolation_growth

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (supply_node, geography, other_index_1, energy_unit_numerator, resource_unit_denominator,
         interpolation_method, extrapolation_method, extrapolation_growth) = tup

        self.set_args(scenario, supply_node=supply_node, geography=geography, other_index_1=other_index_1,
                  energy_unit_numerator=energy_unit_numerator,
                  resource_unit_denominator=resource_unit_denominator,
                  interpolation_method=interpolation_method, extrapolation_method=extrapolation_method,
                  extrapolation_growth=extrapolation_growth)

class SupplySales(DataObject):
    _instances_by_key = {}
    _key_col = "supply_node"
    _cols = ["supply_node", "geography", "capacity_or_energy_unit", "time_unit",
             "interpolation_method", "extrapolation_method", "extrapolation_growth",
             "geography_map_key"]
    _table_name = "SupplySales"
    _data_table_name = 'SupplySalesData'

    def __init__(self, supply_node, scenario):
        DataObject.__init__(self, supply_node, scenario)

        SupplySales._instances_by_key[self._key] = self

        self.supply_node = None
        self.geography = None
        self.capacity_or_energy_unit = None
        self.time_unit = None
        self.interpolation_method = None
        self.extrapolation_method = None
        self.extrapolation_growth = None
        self.geography_map_key = None

    def set_args(self, scenario, supply_node=None, geography=None, capacity_or_energy_unit=None, time_unit=None,
                 interpolation_method=None, extrapolation_method=None, extrapolation_growth=None,
                 geography_map_key=None):
        self.supply_node = supply_node
        self.geography = geography
        self.capacity_or_energy_unit = capacity_or_energy_unit
        self.time_unit = time_unit
        self.interpolation_method = interpolation_method
        self.extrapolation_method = extrapolation_method
        self.extrapolation_growth = extrapolation_growth
        self.geography_map_key = geography_map_key

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (supply_node, geography, capacity_or_energy_unit, time_unit, interpolation_method,
         extrapolation_method, extrapolation_growth, geography_map_key) = tup

        self.set_args(scenario, supply_node=supply_node, geography=geography,
                  capacity_or_energy_unit=capacity_or_energy_unit, time_unit=time_unit,
                  interpolation_method=interpolation_method, extrapolation_method=extrapolation_method,
                  extrapolation_growth=extrapolation_growth, geography_map_key=geography_map_key)

class SupplySalesMeasures(DataObject):
    _instances_by_key = {}
    _key_col = "name"
    _cols = ["name", "supply_technology", "supply_node", "geography", "other_index_1",
             "interpolation_method", "extrapolation_method", "extrapolation_growth",
             "geography_map_key"]
    _table_name = "SupplySalesMeasures"
    _data_table_name = 'SupplySalesMeasuresData'

    def __init__(self, name, scenario):
        DataObject.__init__(self, name, scenario)

        SupplySalesMeasures._instances_by_key[self._key] = self

        self.name = None
        self.supply_technology = None
        self.supply_node = None
        self.geography = None
        self.other_index_1 = None
        self.interpolation_method = None
        self.extrapolation_method = None
        self.extrapolation_growth = None
        self.geography_map_key = None

    def set_args(self, scenario, name=None, supply_technology=None, supply_node=None, geography=None, other_index_1=None,
                 interpolation_method=None, extrapolation_method=None, extrapolation_growth=None,
                 geography_map_key=None):
        self.name = name
        self.supply_technology = supply_technology
        self.supply_node = supply_node
        self.geography = geography
        self.other_index_1 = other_index_1
        self.interpolation_method = interpolation_method
        self.extrapolation_method = extrapolation_method
        self.extrapolation_growth = extrapolation_growth
        self.geography_map_key = geography_map_key

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (name, supply_technology, supply_node, geography, other_index_1, interpolation_method,
         extrapolation_method, extrapolation_growth, geography_map_key) = tup

        self.set_args(scenario, name=name, supply_technology=supply_technology, supply_node=supply_node,
                  geography=geography, other_index_1=other_index_1,
                  interpolation_method=interpolation_method, extrapolation_method=extrapolation_method,
                  extrapolation_growth=extrapolation_growth, geography_map_key=geography_map_key)

class SupplySalesShare(DataObject):
    _instances_by_key = {}
    _key_col = "supply_node"
    _cols = ["supply_node", "geography", "interpolation_method", "extrapolation_method",
             "extrapolation_growth"]
    _table_name = "SupplySalesShare"
    _data_table_name = 'SupplySalesShareData'

    def __init__(self, supply_node, scenario):
        DataObject.__init__(self, supply_node, scenario)

        SupplySalesShare._instances_by_key[self._key] = self

        self.supply_node = None
        self.geography = None
        self.interpolation_method = None
        self.extrapolation_method = None
        self.extrapolation_growth = None

    def set_args(self, scenario, supply_node=None, geography=None, interpolation_method=None, extrapolation_method=None,
                 extrapolation_growth=None):
        self.supply_node = supply_node
        self.geography = geography
        self.interpolation_method = interpolation_method
        self.extrapolation_method = extrapolation_method
        self.extrapolation_growth = extrapolation_growth

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (supply_node, geography, interpolation_method, extrapolation_method, extrapolation_growth) = tup

        self.set_args(scenario, supply_node=supply_node, geography=geography, interpolation_method=interpolation_method,
                  extrapolation_method=extrapolation_method, extrapolation_growth=extrapolation_growth)

class SupplySalesShareMeasures(DataObject):
    _instances_by_key = {}
    _key_col = "name"
    _cols = ["name", "supply_node", "supply_technology", "replaced_supply_technology", "geography",
             "capacity_or_energy_unit", "time_unit", "interpolation_method", "extrapolation_method",
             "extrapolation_growth", "other_index_1"]
    _table_name = "SupplySalesShareMeasures"
    _data_table_name = 'SupplySalesShareMeasuresData'

    def __init__(self, name, scenario):
        DataObject.__init__(self, name, scenario)

        SupplySalesShareMeasures._instances_by_key[self._key] = self

        self.name = None
        self.supply_node = None
        self.supply_technology = None
        self.replaced_supply_technology = None
        self.geography = None
        self.capacity_or_energy_unit = None
        self.time_unit = None
        self.interpolation_method = None
        self.extrapolation_method = None
        self.extrapolation_growth = None
        self.other_index_1 = None

    def set_args(self, scenario, name=None, supply_node=None, supply_technology=None, replaced_supply_technology=None,
                 geography=None, capacity_or_energy_unit=None, time_unit=None, interpolation_method=None,
                 extrapolation_method=None, extrapolation_growth=None, other_index_1=None):
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

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (name, supply_node, supply_technology, replaced_supply_technology, geography,
         capacity_or_energy_unit, time_unit, interpolation_method, extrapolation_method,
         extrapolation_growth, other_index_1) = tup

        self.set_args(scenario, name=name, supply_node=supply_node, supply_technology=supply_technology,
                  replaced_supply_technology=replaced_supply_technology, geography=geography,
                  capacity_or_energy_unit=capacity_or_energy_unit, time_unit=time_unit,
                  interpolation_method=interpolation_method, extrapolation_method=extrapolation_method,
                  extrapolation_growth=extrapolation_growth, other_index_1=other_index_1)

class SupplyStock(DataObject):
    _instances_by_key = {}
    _key_col = "supply_node"
    _cols = ["supply_node", "geography", "capacity_or_energy_unit", "time_unit",
             "interpolation_method", "extrapolation_method", "extrapolation_growth",
             "geography_map_key"]
    _table_name = "SupplyStock"
    _data_table_name = 'SupplyStockData'

    def __init__(self, supply_node, scenario):
        DataObject.__init__(self, supply_node, scenario)

        SupplyStock._instances_by_key[self._key] = self

        self.supply_node = None
        self.geography = None
        self.capacity_or_energy_unit = None
        self.time_unit = None
        self.interpolation_method = None
        self.extrapolation_method = None
        self.extrapolation_growth = None
        self.geography_map_key = None

    def set_args(self, scenario, supply_node=None, geography=None, capacity_or_energy_unit=None, time_unit=None,
                 interpolation_method=None, extrapolation_method=None, extrapolation_growth=None,
                 geography_map_key=None):
        self.supply_node = supply_node
        self.geography = geography
        self.capacity_or_energy_unit = capacity_or_energy_unit
        self.time_unit = time_unit
        self.interpolation_method = interpolation_method
        self.extrapolation_method = extrapolation_method
        self.extrapolation_growth = extrapolation_growth
        self.geography_map_key = geography_map_key

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (supply_node, geography, capacity_or_energy_unit, time_unit, interpolation_method,
         extrapolation_method, extrapolation_growth, geography_map_key) = tup

        self.set_args(scenario, supply_node=supply_node, geography=geography,
                  capacity_or_energy_unit=capacity_or_energy_unit, time_unit=time_unit,
                  interpolation_method=interpolation_method, extrapolation_method=extrapolation_method,
                  extrapolation_growth=extrapolation_growth, geography_map_key=geography_map_key)

class SupplyStockMeasures(DataObject):
    _instances_by_key = {}
    _key_col = "name"
    _cols = ["name", "supply_technology", "supply_node", "geography", "other_index_1",
             "capacity_or_energy_unit", "time_unit", "interpolation_method", "extrapolation_method",
             "extrapolation_growth", "geography_map_key"]
    _table_name = "SupplyStockMeasures"
    _data_table_name = 'SupplyStockMeasuresData'

    def __init__(self, name, scenario):
        DataObject.__init__(self, name, scenario)

        SupplyStockMeasures._instances_by_key[self._key] = self

        self.name = None
        self.supply_technology = None
        self.supply_node = None
        self.geography = None
        self.other_index_1 = None
        self.capacity_or_energy_unit = None
        self.time_unit = None
        self.interpolation_method = None
        self.extrapolation_method = None
        self.extrapolation_growth = None
        self.geography_map_key = None

    def set_args(self, scenario, name=None, supply_technology=None, supply_node=None, geography=None, other_index_1=None,
                 capacity_or_energy_unit=None, time_unit=None, interpolation_method=None,
                 extrapolation_method=None, extrapolation_growth=None, geography_map_key=None):
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

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (name, supply_technology, supply_node, geography, other_index_1, capacity_or_energy_unit,
         time_unit, interpolation_method, extrapolation_method, extrapolation_growth,
         geography_map_key) = tup

        self.set_args(scenario, name=name, supply_technology=supply_technology, supply_node=supply_node,
                  geography=geography, other_index_1=other_index_1,
                  capacity_or_energy_unit=capacity_or_energy_unit, time_unit=time_unit,
                  interpolation_method=interpolation_method, extrapolation_method=extrapolation_method,
                  extrapolation_growth=extrapolation_growth, geography_map_key=geography_map_key)

class SupplyTechs(DataObject):
    _instances_by_key = {}
    _key_col = "name"
    _cols = ["name", "supply_node", "source", "additional_description", "stock_decay_function",
             "book_life", "mean_lifetime", "lifetime_variance", "min_lifetime", "max_lifetime",
             "discharge_duration", "cost_of_capital", "shape", "max_lag_hours", "max_lead_hours",
             "thermal_capacity_multiplier"]
    _table_name = "SupplyTechs"
    _data_table_name = None

    def __init__(self, name, scenario):
        DataObject.__init__(self, name, scenario)

        SupplyTechs._instances_by_key[self._key] = self

        self.name = None
        self.supply_node = None
        self.source = None
        self.additional_description = None
        self.stock_decay_function = None
        self.book_life = None
        self.mean_lifetime = None
        self.lifetime_variance = None
        self.min_lifetime = None
        self.max_lifetime = None
        self.discharge_duration = None
        self.cost_of_capital = None
        self.shape = None
        self.max_lag_hours = None
        self.max_lead_hours = None
        self.thermal_capacity_multiplier = None

    def set_args(self, scenario, name=None, supply_node=None, source=None, additional_description=None,
                 stock_decay_function=None, book_life=None, mean_lifetime=None, lifetime_variance=None,
                 min_lifetime=None, max_lifetime=None, discharge_duration=None, cost_of_capital=None,
                 shape=None, max_lag_hours=None, max_lead_hours=None, thermal_capacity_multiplier=None):
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

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (name, supply_node, source, additional_description, stock_decay_function, book_life,
         mean_lifetime, lifetime_variance, min_lifetime, max_lifetime, discharge_duration,
         cost_of_capital, shape, max_lag_hours, max_lead_hours, thermal_capacity_multiplier) = tup

        self.set_args(scenario, name=name, supply_node=supply_node, source=source,
                  additional_description=additional_description, stock_decay_function=stock_decay_function,
                  book_life=book_life, mean_lifetime=mean_lifetime, lifetime_variance=lifetime_variance,
                  min_lifetime=min_lifetime, max_lifetime=max_lifetime,
                  discharge_duration=discharge_duration, cost_of_capital=cost_of_capital, shape=shape,
                  max_lag_hours=max_lag_hours, max_lead_hours=max_lead_hours,
                  thermal_capacity_multiplier=thermal_capacity_multiplier)

class SupplyTechsCO2Capture(DataObject):
    _instances_by_key = {}
    _key_col = "supply_tech"
    _cols = ["supply_tech", "definition", "geography", "reference_tech_id", "interpolation_method",
             "extrapolation_method", "extrapolation_growth", "age_growth_or_decay_type",
             "age_growth_or_decay"]
    _table_name = "SupplyTechsCO2Capture"
    _data_table_name = 'SupplyTechsCO2CaptureData'

    def __init__(self, supply_tech, scenario):
        DataObject.__init__(self, supply_tech, scenario)

        SupplyTechsCO2Capture._instances_by_key[self._key] = self

        self.supply_tech = None
        self.definition = None
        self.geography = None
        self.reference_tech_id = None
        self.interpolation_method = None
        self.extrapolation_method = None
        self.extrapolation_growth = None
        self.age_growth_or_decay_type = None
        self.age_growth_or_decay = None

    def set_args(self, scenario, supply_tech=None, definition=None, geography=None, reference_tech_id=None,
                 interpolation_method=None, extrapolation_method=None, extrapolation_growth=None,
                 age_growth_or_decay_type=None, age_growth_or_decay=None):
        self.supply_tech = supply_tech
        self.definition = definition
        self.geography = geography
        self.reference_tech_id = reference_tech_id
        self.interpolation_method = interpolation_method
        self.extrapolation_method = extrapolation_method
        self.extrapolation_growth = extrapolation_growth
        self.age_growth_or_decay_type = age_growth_or_decay_type
        self.age_growth_or_decay = age_growth_or_decay

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (supply_tech, definition, geography, reference_tech_id, interpolation_method,
         extrapolation_method, extrapolation_growth, age_growth_or_decay_type, age_growth_or_decay) = tup

        self.set_args(scenario, supply_tech=supply_tech, definition=definition, geography=geography,
                  reference_tech_id=reference_tech_id, interpolation_method=interpolation_method,
                  extrapolation_method=extrapolation_method, extrapolation_growth=extrapolation_growth,
                  age_growth_or_decay_type=age_growth_or_decay_type,
                  age_growth_or_decay=age_growth_or_decay)

class SupplyTechsCapacityFactor(DataObject):
    _instances_by_key = {}
    _key_col = "supply_tech"
    _cols = ["supply_tech", "geography", "reference_tech_id", "definition", "interpolation_method",
             "extrapolation_method", "extrapolation_growth", "age_growth_or_decay_type",
             "age_growth_or_decay"]
    _table_name = "SupplyTechsCapacityFactor"
    _data_table_name = 'SupplyTechsCapacityFactorData'

    def __init__(self, supply_tech, scenario):
        DataObject.__init__(self, supply_tech, scenario)

        SupplyTechsCapacityFactor._instances_by_key[self._key] = self

        self.supply_tech = None
        self.geography = None
        self.reference_tech_id = None
        self.definition = None
        self.interpolation_method = None
        self.extrapolation_method = None
        self.extrapolation_growth = None
        self.age_growth_or_decay_type = None
        self.age_growth_or_decay = None

    def set_args(self, scenario, supply_tech=None, geography=None, reference_tech_id=None, definition=None,
                 interpolation_method=None, extrapolation_method=None, extrapolation_growth=None,
                 age_growth_or_decay_type=None, age_growth_or_decay=None):
        self.supply_tech = supply_tech
        self.geography = geography
        self.reference_tech_id = reference_tech_id
        self.definition = definition
        self.interpolation_method = interpolation_method
        self.extrapolation_method = extrapolation_method
        self.extrapolation_growth = extrapolation_growth
        self.age_growth_or_decay_type = age_growth_or_decay_type
        self.age_growth_or_decay = age_growth_or_decay

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (supply_tech, geography, reference_tech_id, definition, interpolation_method,
         extrapolation_method, extrapolation_growth, age_growth_or_decay_type, age_growth_or_decay) = tup

        self.set_args(scenario, supply_tech=supply_tech, geography=geography, reference_tech_id=reference_tech_id,
                  definition=definition, interpolation_method=interpolation_method,
                  extrapolation_method=extrapolation_method, extrapolation_growth=extrapolation_growth,
                  age_growth_or_decay_type=age_growth_or_decay_type,
                  age_growth_or_decay=age_growth_or_decay)

class SupplyTechsCapitalCost(DataObject):
    _instances_by_key = {}
    _key_col = "supply_tech"
    _cols = ["supply_tech", "definition", "reference_tech_id", "geography", "currency",
             "currency_year_id", "capacity_or_energy_unit", "time_unit", "is_levelized",
             "interpolation_method", "extrapolation_method", "extrapolation_growth", "source",
             "notes", "geography_map_key"]
    _table_name = "SupplyTechsCapitalCost"
    _data_table_name = None

    def __init__(self, supply_tech, scenario):
        DataObject.__init__(self, supply_tech, scenario)

        SupplyTechsCapitalCost._instances_by_key[self._key] = self

        self.supply_tech = None
        self.definition = None
        self.reference_tech_id = None
        self.geography = None
        self.currency = None
        self.currency_year_id = None
        self.capacity_or_energy_unit = None
        self.time_unit = None
        self.is_levelized = None
        self.interpolation_method = None
        self.extrapolation_method = None
        self.extrapolation_growth = None
        self.source = None
        self.notes = None
        self.geography_map_key = None

    def set_args(self, scenario, supply_tech=None, definition=None, reference_tech_id=None, geography=None, currency=None,
                 currency_year_id=None, capacity_or_energy_unit=None, time_unit=None, is_levelized=None,
                 interpolation_method=None, extrapolation_method=None, extrapolation_growth=None,
                 source=None, notes=None, geography_map_key=None):
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

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (supply_tech, definition, reference_tech_id, geography, currency, currency_year_id,
         capacity_or_energy_unit, time_unit, is_levelized, interpolation_method,
         extrapolation_method, extrapolation_growth, source, notes, geography_map_key) = tup

        self.set_args(scenario, supply_tech=supply_tech, definition=definition, reference_tech_id=reference_tech_id,
                  geography=geography, currency=currency, currency_year_id=currency_year_id,
                  capacity_or_energy_unit=capacity_or_energy_unit, time_unit=time_unit,
                  is_levelized=is_levelized, interpolation_method=interpolation_method,
                  extrapolation_method=extrapolation_method, extrapolation_growth=extrapolation_growth,
                  source=source, notes=notes, geography_map_key=geography_map_key)

class SupplyTechsEfficiency(DataObject):
    _instances_by_key = {}
    _key_col = "supply_tech"
    _cols = ["supply_tech", "geography", "definition", "reference_tech", "input_unit", "output_unit",
             "interpolation_method", "extrapolation_method", "extrapolation_growth",
             "age_growth_or_decay_type", "age_growth_or_decay", "source", "notes"]
    _table_name = "SupplyTechsEfficiency"
    _data_table_name = 'SupplyTechsEfficiencyData'

    def __init__(self, supply_tech, scenario):
        DataObject.__init__(self, supply_tech, scenario)

        SupplyTechsEfficiency._instances_by_key[self._key] = self

        self.supply_tech = None
        self.geography = None
        self.definition = None
        self.reference_tech = None
        self.input_unit = None
        self.output_unit = None
        self.interpolation_method = None
        self.extrapolation_method = None
        self.extrapolation_growth = None
        self.age_growth_or_decay_type = None
        self.age_growth_or_decay = None
        self.source = None
        self.notes = None

    def set_args(self, scenario, supply_tech=None, geography=None, definition=None, reference_tech=None, input_unit=None,
                 output_unit=None, interpolation_method=None, extrapolation_method=None,
                 extrapolation_growth=None, age_growth_or_decay_type=None, age_growth_or_decay=None,
                 source=None, notes=None):
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

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (supply_tech, geography, definition, reference_tech, input_unit, output_unit,
         interpolation_method, extrapolation_method, extrapolation_growth,
         age_growth_or_decay_type, age_growth_or_decay, source, notes) = tup

        self.set_args(scenario, supply_tech=supply_tech, geography=geography, definition=definition,
                  reference_tech=reference_tech, input_unit=input_unit, output_unit=output_unit,
                  interpolation_method=interpolation_method, extrapolation_method=extrapolation_method,
                  extrapolation_growth=extrapolation_growth,
                  age_growth_or_decay_type=age_growth_or_decay_type,
                  age_growth_or_decay=age_growth_or_decay, source=source, notes=notes)

class SupplyTechsFixedMaintenanceCost(DataObject):
    _instances_by_key = {}
    _key_col = "supply_tech"
    _cols = ["supply_tech", "definition", "reference_tech_id", "geography", "currency",
             "currency_year_id", "capacity_or_energy_unit", "time_unit", "interpolation_method",
             "extrapolation_method", "extrapolation_growth", "age_growth_or_decay_type",
             "age_growth_or_decay", "source", "notes"]
    _table_name = "SupplyTechsFixedMaintenanceCost"
    _data_table_name = 'SupplyTechsFixedMaintenanceCostData'

    def __init__(self, supply_tech, scenario):
        DataObject.__init__(self, supply_tech, scenario)

        SupplyTechsFixedMaintenanceCost._instances_by_key[self._key] = self

        self.supply_tech = None
        self.definition = None
        self.reference_tech_id = None
        self.geography = None
        self.currency = None
        self.currency_year_id = None
        self.capacity_or_energy_unit = None
        self.time_unit = None
        self.interpolation_method = None
        self.extrapolation_method = None
        self.extrapolation_growth = None
        self.age_growth_or_decay_type = None
        self.age_growth_or_decay = None
        self.source = None
        self.notes = None

    def set_args(self, scenario, supply_tech=None, definition=None, reference_tech_id=None, geography=None, currency=None,
                 currency_year_id=None, capacity_or_energy_unit=None, time_unit=None,
                 interpolation_method=None, extrapolation_method=None, extrapolation_growth=None,
                 age_growth_or_decay_type=None, age_growth_or_decay=None, source=None, notes=None):
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

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (supply_tech, definition, reference_tech_id, geography, currency, currency_year_id,
         capacity_or_energy_unit, time_unit, interpolation_method, extrapolation_method,
         extrapolation_growth, age_growth_or_decay_type, age_growth_or_decay, source, notes) = tup

        self.set_args(scenario, supply_tech=supply_tech, definition=definition, reference_tech_id=reference_tech_id,
                  geography=geography, currency=currency, currency_year_id=currency_year_id,
                  capacity_or_energy_unit=capacity_or_energy_unit, time_unit=time_unit,
                  interpolation_method=interpolation_method, extrapolation_method=extrapolation_method,
                  extrapolation_growth=extrapolation_growth,
                  age_growth_or_decay_type=age_growth_or_decay_type,
                  age_growth_or_decay=age_growth_or_decay, source=source, notes=notes)

class SupplyTechsInstallationCost(DataObject):
    _instances_by_key = {}
    _key_col = "supply_tech"
    _cols = ["supply_tech", "definition", "geography", "reference_tech_id", "currency",
             "currency_year_id", "capacity_or_energy_unit", "time_unit", "is_levelized",
             "interpolation_method", "extrapolation_method", "extrapolation_growth", "source", "notes"]
    _table_name = "SupplyTechsInstallationCost"
    _data_table_name = None

    def __init__(self, supply_tech, scenario):
        DataObject.__init__(self, supply_tech, scenario)

        SupplyTechsInstallationCost._instances_by_key[self._key] = self

        self.supply_tech = None
        self.definition = None
        self.geography = None
        self.reference_tech_id = None
        self.currency = None
        self.currency_year_id = None
        self.capacity_or_energy_unit = None
        self.time_unit = None
        self.is_levelized = None
        self.interpolation_method = None
        self.extrapolation_method = None
        self.extrapolation_growth = None
        self.source = None
        self.notes = None

    def set_args(self, scenario, supply_tech=None, definition=None, geography=None, reference_tech_id=None, currency=None,
                 currency_year_id=None, capacity_or_energy_unit=None, time_unit=None, is_levelized=None,
                 interpolation_method=None, extrapolation_method=None, extrapolation_growth=None,
                 source=None, notes=None):
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

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (supply_tech, definition, geography, reference_tech_id, currency, currency_year_id,
         capacity_or_energy_unit, time_unit, is_levelized, interpolation_method,
         extrapolation_method, extrapolation_growth, source, notes) = tup

        self.set_args(scenario, supply_tech=supply_tech, definition=definition, geography=geography,
                  reference_tech_id=reference_tech_id, currency=currency,
                  currency_year_id=currency_year_id, capacity_or_energy_unit=capacity_or_energy_unit,
                  time_unit=time_unit, is_levelized=is_levelized,
                  interpolation_method=interpolation_method, extrapolation_method=extrapolation_method,
                  extrapolation_growth=extrapolation_growth, source=source, notes=notes)

class SupplyTechsVariableMaintenanceCost(DataObject):
    _instances_by_key = {}
    _key_col = "supply_tech"
    _cols = ["supply_tech", "definition", "reference_tech_id", "currency", "geography",
             "currency_year_id", "energy_unit", "interpolation_method", "extrapolation_method",
             "extrapolation_growth", "age_growth_or_decay_type", "age_growth_or_decay", "source",
             "notes"]
    _table_name = "SupplyTechsVariableMaintenanceCost"
    _data_table_name = 'SupplyTechsVariableMaintenanceCostData'

    def __init__(self, supply_tech, scenario):
        DataObject.__init__(self, supply_tech, scenario)

        SupplyTechsVariableMaintenanceCost._instances_by_key[self._key] = self

        self.supply_tech = None
        self.definition = None
        self.reference_tech_id = None
        self.currency = None
        self.geography = None
        self.currency_year_id = None
        self.energy_unit = None
        self.interpolation_method = None
        self.extrapolation_method = None
        self.extrapolation_growth = None
        self.age_growth_or_decay_type = None
        self.age_growth_or_decay = None
        self.source = None
        self.notes = None

    def set_args(self, scenario, supply_tech=None, definition=None, reference_tech_id=None, currency=None, geography=None,
                 currency_year_id=None, energy_unit=None, interpolation_method=None,
                 extrapolation_method=None, extrapolation_growth=None, age_growth_or_decay_type=None,
                 age_growth_or_decay=None, source=None, notes=None):
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

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (supply_tech, definition, reference_tech_id, currency, geography, currency_year_id,
         energy_unit, interpolation_method, extrapolation_method, extrapolation_growth,
         age_growth_or_decay_type, age_growth_or_decay, source, notes) = tup

        self.set_args(scenario, supply_tech=supply_tech, definition=definition, reference_tech_id=reference_tech_id,
                  currency=currency, geography=geography, currency_year_id=currency_year_id,
                  energy_unit=energy_unit, interpolation_method=interpolation_method,
                  extrapolation_method=extrapolation_method, extrapolation_growth=extrapolation_growth,
                  age_growth_or_decay_type=age_growth_or_decay_type,
                  age_growth_or_decay=age_growth_or_decay, source=source, notes=notes)

class TimeZones(DataObject):
    _instances_by_key = {}
    _key_col = "name"
    _cols = ["id", "name", "utc_shift"]
    _table_name = "TimeZones"
    _data_table_name = None

    def __init__(self, name, scenario):
        DataObject.__init__(self, name, scenario)

        TimeZones._instances_by_key[self._key] = self

        self.id = None
        self.name = None
        self.utc_shift = None

    def set_args(self, scenario, id=None, name=None, utc_shift=None):
        self.id = id
        self.name = name
        self.utc_shift = utc_shift

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (id, name, utc_shift) = tup

        self.set_args(scenario, id=id, name=name, utc_shift=utc_shift)

class Wave_Power(DataObject):
    _instances_by_key = {}
    _key_col = "parent"
    _cols = ["parent", "gau", "dispatch_feeder", "resource_bin", "dispatch_constraint", "year",
             "month", "week", "hour", "day_type", "weather_datetime", "value", "id"]
    _table_name = "Wave_Power"
    _data_table_name = None

    def __init__(self, parent, scenario):
        DataObject.__init__(self, parent, scenario)

        Wave_Power._instances_by_key[self._key] = self

        self.parent = None
        self.gau = None
        self.dispatch_feeder = None
        self.resource_bin = None
        self.dispatch_constraint = None
        self.year = None
        self.month = None
        self.week = None
        self.hour = None
        self.day_type = None
        self.weather_datetime = None
        self.value = None
        self.id = None

    def set_args(self, scenario, parent=None, gau=None, dispatch_feeder=None, resource_bin=None, dispatch_constraint=None,
                 year=None, month=None, week=None, hour=None, day_type=None, weather_datetime=None,
                 value=None, id=None):
        self.parent = parent
        self.gau = gau
        self.dispatch_feeder = dispatch_feeder
        self.resource_bin = resource_bin
        self.dispatch_constraint = dispatch_constraint
        self.year = year
        self.month = month
        self.week = week
        self.hour = hour
        self.day_type = day_type
        self.weather_datetime = weather_datetime
        self.value = value
        self.id = id

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (parent, gau, dispatch_feeder, resource_bin, dispatch_constraint, year, month, week, hour,
         day_type, weather_datetime, value, id) = tup

        self.set_args(scenario, parent=parent, gau=gau, dispatch_feeder=dispatch_feeder, resource_bin=resource_bin,
                  dispatch_constraint=dispatch_constraint, year=year, month=month, week=week, hour=hour,
                  day_type=day_type, weather_datetime=weather_datetime, value=value, id=id)

class boiler_com(DataObject):
    _instances_by_key = {}
    _key_col = "parent"
    _cols = ["parent", "gau", "dispatch_feeder", "resource_bin", "dispatch_constraint", "year",
             "month", "week", "hour", "day_type", "weather_datetime", "value", "id"]
    _table_name = "boiler_com"
    _data_table_name = None

    def __init__(self, parent, scenario):
        DataObject.__init__(self, parent, scenario)

        boiler_com._instances_by_key[self._key] = self

        self.parent = None
        self.gau = None
        self.dispatch_feeder = None
        self.resource_bin = None
        self.dispatch_constraint = None
        self.year = None
        self.month = None
        self.week = None
        self.hour = None
        self.day_type = None
        self.weather_datetime = None
        self.value = None
        self.id = None

    def set_args(self, scenario, parent=None, gau=None, dispatch_feeder=None, resource_bin=None, dispatch_constraint=None,
                 year=None, month=None, week=None, hour=None, day_type=None, weather_datetime=None,
                 value=None, id=None):
        self.parent = parent
        self.gau = gau
        self.dispatch_feeder = dispatch_feeder
        self.resource_bin = resource_bin
        self.dispatch_constraint = dispatch_constraint
        self.year = year
        self.month = month
        self.week = week
        self.hour = hour
        self.day_type = day_type
        self.weather_datetime = weather_datetime
        self.value = value
        self.id = id

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (parent, gau, dispatch_feeder, resource_bin, dispatch_constraint, year, month, week, hour,
         day_type, weather_datetime, value, id) = tup

        self.set_args(scenario, parent=parent, gau=gau, dispatch_feeder=dispatch_feeder, resource_bin=resource_bin,
                  dispatch_constraint=dispatch_constraint, year=year, month=month, week=week, hour=hour,
                  day_type=day_type, weather_datetime=weather_datetime, value=value, id=id)

class california_wind_imports(DataObject):
    _instances_by_key = {}
    _key_col = "parent"
    _cols = ["parent", "gau", "dispatch_feeder", "resource_bin", "dispatch_constraint", "year",
             "month", "week", "hour", "day_type", "weather_datetime", "value", "id"]
    _table_name = "california_wind_imports"
    _data_table_name = None

    def __init__(self, parent, scenario):
        DataObject.__init__(self, parent, scenario)

        california_wind_imports._instances_by_key[self._key] = self

        self.parent = None
        self.gau = None
        self.dispatch_feeder = None
        self.resource_bin = None
        self.dispatch_constraint = None
        self.year = None
        self.month = None
        self.week = None
        self.hour = None
        self.day_type = None
        self.weather_datetime = None
        self.value = None
        self.id = None

    def set_args(self, scenario, parent=None, gau=None, dispatch_feeder=None, resource_bin=None, dispatch_constraint=None,
                 year=None, month=None, week=None, hour=None, day_type=None, weather_datetime=None,
                 value=None, id=None):
        self.parent = parent
        self.gau = gau
        self.dispatch_feeder = dispatch_feeder
        self.resource_bin = resource_bin
        self.dispatch_constraint = dispatch_constraint
        self.year = year
        self.month = month
        self.week = week
        self.hour = hour
        self.day_type = day_type
        self.weather_datetime = weather_datetime
        self.value = value
        self.id = id

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (parent, gau, dispatch_feeder, resource_bin, dispatch_constraint, year, month, week, hour,
         day_type, weather_datetime, value, id) = tup

        self.set_args(scenario, parent=parent, gau=gau, dispatch_feeder=dispatch_feeder, resource_bin=resource_bin,
                  dispatch_constraint=dispatch_constraint, year=year, month=month, week=week, hour=hour,
                  day_type=day_type, weather_datetime=weather_datetime, value=value, id=id)

class chiller_com(DataObject):
    _instances_by_key = {}
    _key_col = "parent"
    _cols = ["parent", "gau", "dispatch_feeder", "resource_bin", "dispatch_constraint", "year",
             "month", "week", "hour", "day_type", "weather_datetime", "value", "id"]
    _table_name = "chiller_com"
    _data_table_name = None

    def __init__(self, parent, scenario):
        DataObject.__init__(self, parent, scenario)

        chiller_com._instances_by_key[self._key] = self

        self.parent = None
        self.gau = None
        self.dispatch_feeder = None
        self.resource_bin = None
        self.dispatch_constraint = None
        self.year = None
        self.month = None
        self.week = None
        self.hour = None
        self.day_type = None
        self.weather_datetime = None
        self.value = None
        self.id = None

    def set_args(self, scenario, parent=None, gau=None, dispatch_feeder=None, resource_bin=None, dispatch_constraint=None,
                 year=None, month=None, week=None, hour=None, day_type=None, weather_datetime=None,
                 value=None, id=None):
        self.parent = parent
        self.gau = gau
        self.dispatch_feeder = dispatch_feeder
        self.resource_bin = resource_bin
        self.dispatch_constraint = dispatch_constraint
        self.year = year
        self.month = month
        self.week = week
        self.hour = hour
        self.day_type = day_type
        self.weather_datetime = weather_datetime
        self.value = value
        self.id = id

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (parent, gau, dispatch_feeder, resource_bin, dispatch_constraint, year, month, week, hour,
         day_type, weather_datetime, value, id) = tup

        self.set_args(scenario, parent=parent, gau=gau, dispatch_feeder=dispatch_feeder, resource_bin=resource_bin,
                  dispatch_constraint=dispatch_constraint, year=year, month=month, week=week, hour=hour,
                  day_type=day_type, weather_datetime=weather_datetime, value=value, id=id)

class clothes_drying_electric_(DataObject):
    _instances_by_key = {}
    _key_col = "parent"
    _cols = ["parent", "gau", "dispatch_feeder", "resource_bin", "dispatch_constraint", "year",
             "month", "week", "hour", "day_type", "weather_datetime", "value", "id"]
    _table_name = "clothes_drying_electric_"
    _data_table_name = None

    def __init__(self, parent, scenario):
        DataObject.__init__(self, parent, scenario)

        clothes_drying_electric_._instances_by_key[self._key] = self

        self.parent = None
        self.gau = None
        self.dispatch_feeder = None
        self.resource_bin = None
        self.dispatch_constraint = None
        self.year = None
        self.month = None
        self.week = None
        self.hour = None
        self.day_type = None
        self.weather_datetime = None
        self.value = None
        self.id = None

    def set_args(self, scenario, parent=None, gau=None, dispatch_feeder=None, resource_bin=None, dispatch_constraint=None,
                 year=None, month=None, week=None, hour=None, day_type=None, weather_datetime=None,
                 value=None, id=None):
        self.parent = parent
        self.gau = gau
        self.dispatch_feeder = dispatch_feeder
        self.resource_bin = resource_bin
        self.dispatch_constraint = dispatch_constraint
        self.year = year
        self.month = month
        self.week = week
        self.hour = hour
        self.day_type = day_type
        self.weather_datetime = weather_datetime
        self.value = value
        self.id = id

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (parent, gau, dispatch_feeder, resource_bin, dispatch_constraint, year, month, week, hour,
         day_type, weather_datetime, value, id) = tup

        self.set_args(scenario, parent=parent, gau=gau, dispatch_feeder=dispatch_feeder, resource_bin=resource_bin,
                  dispatch_constraint=dispatch_constraint, year=year, month=month, week=week, hour=hour,
                  day_type=day_type, weather_datetime=weather_datetime, value=value, id=id)

class clothes_washing(DataObject):
    _instances_by_key = {}
    _key_col = "parent"
    _cols = ["parent", "gau", "dispatch_feeder", "resource_bin", "dispatch_constraint", "year",
             "month", "week", "hour", "day_type", "weather_datetime", "value", "id"]
    _table_name = "clothes_washing"
    _data_table_name = None

    def __init__(self, parent, scenario):
        DataObject.__init__(self, parent, scenario)

        clothes_washing._instances_by_key[self._key] = self

        self.parent = None
        self.gau = None
        self.dispatch_feeder = None
        self.resource_bin = None
        self.dispatch_constraint = None
        self.year = None
        self.month = None
        self.week = None
        self.hour = None
        self.day_type = None
        self.weather_datetime = None
        self.value = None
        self.id = None

    def set_args(self, scenario, parent=None, gau=None, dispatch_feeder=None, resource_bin=None, dispatch_constraint=None,
                 year=None, month=None, week=None, hour=None, day_type=None, weather_datetime=None,
                 value=None, id=None):
        self.parent = parent
        self.gau = gau
        self.dispatch_feeder = dispatch_feeder
        self.resource_bin = resource_bin
        self.dispatch_constraint = dispatch_constraint
        self.year = year
        self.month = month
        self.week = week
        self.hour = hour
        self.day_type = day_type
        self.weather_datetime = weather_datetime
        self.value = value
        self.id = id

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (parent, gau, dispatch_feeder, resource_bin, dispatch_constraint, year, month, week, hour,
         day_type, weather_datetime, value, id) = tup

        self.set_args(scenario, parent=parent, gau=gau, dispatch_feeder=dispatch_feeder, resource_bin=resource_bin,
                  dispatch_constraint=dispatch_constraint, year=year, month=month, week=week, hour=hour,
                  day_type=day_type, weather_datetime=weather_datetime, value=value, id=id)

class direct_steam_power_tower(DataObject):
    _instances_by_key = {}
    _key_col = "parent"
    _cols = ["parent", "gau", "dispatch_feeder", "resource_bin", "dispatch_constraint", "year",
             "month", "week", "hour", "day_type", "weather_datetime", "value", "id"]
    _table_name = "direct_steam_power_tower"
    _data_table_name = None

    def __init__(self, parent, scenario):
        DataObject.__init__(self, parent, scenario)

        direct_steam_power_tower._instances_by_key[self._key] = self

        self.parent = None
        self.gau = None
        self.dispatch_feeder = None
        self.resource_bin = None
        self.dispatch_constraint = None
        self.year = None
        self.month = None
        self.week = None
        self.hour = None
        self.day_type = None
        self.weather_datetime = None
        self.value = None
        self.id = None

    def set_args(self, scenario, parent=None, gau=None, dispatch_feeder=None, resource_bin=None, dispatch_constraint=None,
                 year=None, month=None, week=None, hour=None, day_type=None, weather_datetime=None,
                 value=None, id=None):
        self.parent = parent
        self.gau = gau
        self.dispatch_feeder = dispatch_feeder
        self.resource_bin = resource_bin
        self.dispatch_constraint = dispatch_constraint
        self.year = year
        self.month = month
        self.week = week
        self.hour = hour
        self.day_type = day_type
        self.weather_datetime = weather_datetime
        self.value = value
        self.id = id

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (parent, gau, dispatch_feeder, resource_bin, dispatch_constraint, year, month, week, hour,
         day_type, weather_datetime, value, id) = tup

        self.set_args(scenario, parent=parent, gau=gau, dispatch_feeder=dispatch_feeder, resource_bin=resource_bin,
                  dispatch_constraint=dispatch_constraint, year=year, month=month, week=week, hour=hour,
                  day_type=day_type, weather_datetime=weather_datetime, value=value, id=id)

class dishwashing(DataObject):
    _instances_by_key = {}
    _key_col = "parent"
    _cols = ["parent", "gau", "dispatch_feeder", "resource_bin", "dispatch_constraint", "year",
             "month", "week", "hour", "day_type", "weather_datetime", "value", "id"]
    _table_name = "dishwashing"
    _data_table_name = None

    def __init__(self, parent, scenario):
        DataObject.__init__(self, parent, scenario)

        dishwashing._instances_by_key[self._key] = self

        self.parent = None
        self.gau = None
        self.dispatch_feeder = None
        self.resource_bin = None
        self.dispatch_constraint = None
        self.year = None
        self.month = None
        self.week = None
        self.hour = None
        self.day_type = None
        self.weather_datetime = None
        self.value = None
        self.id = None

    def set_args(self, scenario, parent=None, gau=None, dispatch_feeder=None, resource_bin=None, dispatch_constraint=None,
                 year=None, month=None, week=None, hour=None, day_type=None, weather_datetime=None,
                 value=None, id=None):
        self.parent = parent
        self.gau = gau
        self.dispatch_feeder = dispatch_feeder
        self.resource_bin = resource_bin
        self.dispatch_constraint = dispatch_constraint
        self.year = year
        self.month = month
        self.week = week
        self.hour = hour
        self.day_type = day_type
        self.weather_datetime = weather_datetime
        self.value = value
        self.id = id

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (parent, gau, dispatch_feeder, resource_bin, dispatch_constraint, year, month, week, hour,
         day_type, weather_datetime, value, id) = tup

        self.set_args(scenario, parent=parent, gau=gau, dispatch_feeder=dispatch_feeder, resource_bin=resource_bin,
                  dispatch_constraint=dispatch_constraint, year=year, month=month, week=week, hour=hour,
                  day_type=day_type, weather_datetime=weather_datetime, value=value, id=id)

class dispatchable_hydro(DataObject):
    _instances_by_key = {}
    _key_col = "parent"
    _cols = ["parent", "gau", "dispatch_feeder", "resource_bin", "dispatch_constraint", "year",
             "month", "week", "hour", "day_type", "weather_datetime", "value", "id"]
    _table_name = "dispatchable_hydro"
    _data_table_name = None

    def __init__(self, parent, scenario):
        DataObject.__init__(self, parent, scenario)

        dispatchable_hydro._instances_by_key[self._key] = self

        self.parent = None
        self.gau = None
        self.dispatch_feeder = None
        self.resource_bin = None
        self.dispatch_constraint = None
        self.year = None
        self.month = None
        self.week = None
        self.hour = None
        self.day_type = None
        self.weather_datetime = None
        self.value = None
        self.id = None

    def set_args(self, scenario, parent=None, gau=None, dispatch_feeder=None, resource_bin=None, dispatch_constraint=None,
                 year=None, month=None, week=None, hour=None, day_type=None, weather_datetime=None,
                 value=None, id=None):
        self.parent = parent
        self.gau = gau
        self.dispatch_feeder = dispatch_feeder
        self.resource_bin = resource_bin
        self.dispatch_constraint = dispatch_constraint
        self.year = year
        self.month = month
        self.week = week
        self.hour = hour
        self.day_type = day_type
        self.weather_datetime = weather_datetime
        self.value = value
        self.id = id

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (parent, gau, dispatch_feeder, resource_bin, dispatch_constraint, year, month, week, hour,
         day_type, weather_datetime, value, id) = tup

        self.set_args(scenario, parent=parent, gau=gau, dispatch_feeder=dispatch_feeder, resource_bin=resource_bin,
                  dispatch_constraint=dispatch_constraint, year=year, month=month, week=week, hour=hour,
                  day_type=day_type, weather_datetime=weather_datetime, value=value, id=id)

class dx_ac_com(DataObject):
    _instances_by_key = {}
    _key_col = "parent"
    _cols = ["parent", "gau", "dispatch_feeder", "resource_bin", "dispatch_constraint", "year",
             "month", "week", "hour", "day_type", "weather_datetime", "value", "id"]
    _table_name = "dx_ac_com"
    _data_table_name = None

    def __init__(self, parent, scenario):
        DataObject.__init__(self, parent, scenario)

        dx_ac_com._instances_by_key[self._key] = self

        self.parent = None
        self.gau = None
        self.dispatch_feeder = None
        self.resource_bin = None
        self.dispatch_constraint = None
        self.year = None
        self.month = None
        self.week = None
        self.hour = None
        self.day_type = None
        self.weather_datetime = None
        self.value = None
        self.id = None

    def set_args(self, scenario, parent=None, gau=None, dispatch_feeder=None, resource_bin=None, dispatch_constraint=None,
                 year=None, month=None, week=None, hour=None, day_type=None, weather_datetime=None,
                 value=None, id=None):
        self.parent = parent
        self.gau = gau
        self.dispatch_feeder = dispatch_feeder
        self.resource_bin = resource_bin
        self.dispatch_constraint = dispatch_constraint
        self.year = year
        self.month = month
        self.week = week
        self.hour = hour
        self.day_type = day_type
        self.weather_datetime = weather_datetime
        self.value = value
        self.id = id

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (parent, gau, dispatch_feeder, resource_bin, dispatch_constraint, year, month, week, hour,
         day_type, weather_datetime, value, id) = tup

        self.set_args(scenario, parent=parent, gau=gau, dispatch_feeder=dispatch_feeder, resource_bin=resource_bin,
                  dispatch_constraint=dispatch_constraint, year=year, month=month, week=week, hour=hour,
                  day_type=day_type, weather_datetime=weather_datetime, value=value, id=id)

class electric_furnace_res(DataObject):
    _instances_by_key = {}
    _key_col = "parent"
    _cols = ["parent", "gau", "dispatch_feeder", "resource_bin", "dispatch_constraint", "year",
             "month", "week", "hour", "day_type", "weather_datetime", "value", "id"]
    _table_name = "electric_furnace_res"
    _data_table_name = None

    def __init__(self, parent, scenario):
        DataObject.__init__(self, parent, scenario)

        electric_furnace_res._instances_by_key[self._key] = self

        self.parent = None
        self.gau = None
        self.dispatch_feeder = None
        self.resource_bin = None
        self.dispatch_constraint = None
        self.year = None
        self.month = None
        self.week = None
        self.hour = None
        self.day_type = None
        self.weather_datetime = None
        self.value = None
        self.id = None

    def set_args(self, scenario, parent=None, gau=None, dispatch_feeder=None, resource_bin=None, dispatch_constraint=None,
                 year=None, month=None, week=None, hour=None, day_type=None, weather_datetime=None,
                 value=None, id=None):
        self.parent = parent
        self.gau = gau
        self.dispatch_feeder = dispatch_feeder
        self.resource_bin = resource_bin
        self.dispatch_constraint = dispatch_constraint
        self.year = year
        self.month = month
        self.week = week
        self.hour = hour
        self.day_type = day_type
        self.weather_datetime = weather_datetime
        self.value = value
        self.id = id

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (parent, gau, dispatch_feeder, resource_bin, dispatch_constraint, year, month, week, hour,
         day_type, weather_datetime, value, id) = tup

        self.set_args(scenario, parent=parent, gau=gau, dispatch_feeder=dispatch_feeder, resource_bin=resource_bin,
                  dispatch_constraint=dispatch_constraint, year=year, month=month, week=week, hour=hour,
                  day_type=day_type, weather_datetime=weather_datetime, value=value, id=id)

class flat_demand_side(DataObject):
    _instances_by_key = {}
    _key_col = "parent"
    _cols = ["parent", "gau", "dispatch_feeder", "resource_bin", "dispatch_constraint", "year",
             "month", "week", "hour", "day_type", "weather_datetime", "value", "id"]
    _table_name = "flat_demand_side"
    _data_table_name = None

    def __init__(self, parent, scenario):
        DataObject.__init__(self, parent, scenario)

        flat_demand_side._instances_by_key[self._key] = self

        self.parent = None
        self.gau = None
        self.dispatch_feeder = None
        self.resource_bin = None
        self.dispatch_constraint = None
        self.year = None
        self.month = None
        self.week = None
        self.hour = None
        self.day_type = None
        self.weather_datetime = None
        self.value = None
        self.id = None

    def set_args(self, scenario, parent=None, gau=None, dispatch_feeder=None, resource_bin=None, dispatch_constraint=None,
                 year=None, month=None, week=None, hour=None, day_type=None, weather_datetime=None,
                 value=None, id=None):
        self.parent = parent
        self.gau = gau
        self.dispatch_feeder = dispatch_feeder
        self.resource_bin = resource_bin
        self.dispatch_constraint = dispatch_constraint
        self.year = year
        self.month = month
        self.week = week
        self.hour = hour
        self.day_type = day_type
        self.weather_datetime = weather_datetime
        self.value = value
        self.id = id

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (parent, gau, dispatch_feeder, resource_bin, dispatch_constraint, year, month, week, hour,
         day_type, weather_datetime, value, id) = tup

        self.set_args(scenario, parent=parent, gau=gau, dispatch_feeder=dispatch_feeder, resource_bin=resource_bin,
                  dispatch_constraint=dispatch_constraint, year=year, month=month, week=week, hour=hour,
                  day_type=day_type, weather_datetime=weather_datetime, value=value, id=id)

class furnace_com(DataObject):
    _instances_by_key = {}
    _key_col = "parent"
    _cols = ["parent", "gau", "dispatch_feeder", "resource_bin", "dispatch_constraint", "year",
             "month", "week", "hour", "day_type", "weather_datetime", "value", "id"]
    _table_name = "furnace_com"
    _data_table_name = None

    def __init__(self, parent, scenario):
        DataObject.__init__(self, parent, scenario)

        furnace_com._instances_by_key[self._key] = self

        self.parent = None
        self.gau = None
        self.dispatch_feeder = None
        self.resource_bin = None
        self.dispatch_constraint = None
        self.year = None
        self.month = None
        self.week = None
        self.hour = None
        self.day_type = None
        self.weather_datetime = None
        self.value = None
        self.id = None

    def set_args(self, scenario, parent=None, gau=None, dispatch_feeder=None, resource_bin=None, dispatch_constraint=None,
                 year=None, month=None, week=None, hour=None, day_type=None, weather_datetime=None,
                 value=None, id=None):
        self.parent = parent
        self.gau = gau
        self.dispatch_feeder = dispatch_feeder
        self.resource_bin = resource_bin
        self.dispatch_constraint = dispatch_constraint
        self.year = year
        self.month = month
        self.week = week
        self.hour = hour
        self.day_type = day_type
        self.weather_datetime = weather_datetime
        self.value = value
        self.id = id

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (parent, gau, dispatch_feeder, resource_bin, dispatch_constraint, year, month, week, hour,
         day_type, weather_datetime, value, id) = tup

        self.set_args(scenario, parent=parent, gau=gau, dispatch_feeder=dispatch_feeder, resource_bin=resource_bin,
                  dispatch_constraint=dispatch_constraint, year=year, month=month, week=week, hour=hour,
                  day_type=day_type, weather_datetime=weather_datetime, value=value, id=id)

class generic_csp_10hr_storage(DataObject):
    _instances_by_key = {}
    _key_col = "parent"
    _cols = ["parent", "gau", "dispatch_feeder", "resource_bin", "dispatch_constraint", "year",
             "month", "week", "hour", "day_type", "weather_datetime", "value", "id"]
    _table_name = "generic_csp_10hr_storage"
    _data_table_name = None

    def __init__(self, parent, scenario):
        DataObject.__init__(self, parent, scenario)

        generic_csp_10hr_storage._instances_by_key[self._key] = self

        self.parent = None
        self.gau = None
        self.dispatch_feeder = None
        self.resource_bin = None
        self.dispatch_constraint = None
        self.year = None
        self.month = None
        self.week = None
        self.hour = None
        self.day_type = None
        self.weather_datetime = None
        self.value = None
        self.id = None

    def set_args(self, scenario, parent=None, gau=None, dispatch_feeder=None, resource_bin=None, dispatch_constraint=None,
                 year=None, month=None, week=None, hour=None, day_type=None, weather_datetime=None,
                 value=None, id=None):
        self.parent = parent
        self.gau = gau
        self.dispatch_feeder = dispatch_feeder
        self.resource_bin = resource_bin
        self.dispatch_constraint = dispatch_constraint
        self.year = year
        self.month = month
        self.week = week
        self.hour = hour
        self.day_type = day_type
        self.weather_datetime = weather_datetime
        self.value = value
        self.id = id

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (parent, gau, dispatch_feeder, resource_bin, dispatch_constraint, year, month, week, hour,
         day_type, weather_datetime, value, id) = tup

        self.set_args(scenario, parent=parent, gau=gau, dispatch_feeder=dispatch_feeder, resource_bin=resource_bin,
                  dispatch_constraint=dispatch_constraint, year=year, month=month, week=week, hour=hour,
                  day_type=day_type, weather_datetime=weather_datetime, value=value, id=id)

class high_efficiency_central_ac_res(DataObject):
    _instances_by_key = {}
    _key_col = "parent"
    _cols = ["parent", "gau", "dispatch_feeder", "resource_bin", "dispatch_constraint", "year",
             "month", "week", "hour", "day_type", "weather_datetime", "value", "id"]
    _table_name = "high_efficiency_central_ac_res"
    _data_table_name = None

    def __init__(self, parent, scenario):
        DataObject.__init__(self, parent, scenario)

        high_efficiency_central_ac_res._instances_by_key[self._key] = self

        self.parent = None
        self.gau = None
        self.dispatch_feeder = None
        self.resource_bin = None
        self.dispatch_constraint = None
        self.year = None
        self.month = None
        self.week = None
        self.hour = None
        self.day_type = None
        self.weather_datetime = None
        self.value = None
        self.id = None

    def set_args(self, scenario, parent=None, gau=None, dispatch_feeder=None, resource_bin=None, dispatch_constraint=None,
                 year=None, month=None, week=None, hour=None, day_type=None, weather_datetime=None,
                 value=None, id=None):
        self.parent = parent
        self.gau = gau
        self.dispatch_feeder = dispatch_feeder
        self.resource_bin = resource_bin
        self.dispatch_constraint = dispatch_constraint
        self.year = year
        self.month = month
        self.week = week
        self.hour = hour
        self.day_type = day_type
        self.weather_datetime = weather_datetime
        self.value = value
        self.id = id

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (parent, gau, dispatch_feeder, resource_bin, dispatch_constraint, year, month, week, hour,
         day_type, weather_datetime, value, id) = tup

        self.set_args(scenario, parent=parent, gau=gau, dispatch_feeder=dispatch_feeder, resource_bin=resource_bin,
                  dispatch_constraint=dispatch_constraint, year=year, month=month, week=week, hour=hour,
                  day_type=day_type, weather_datetime=weather_datetime, value=value, id=id)

class high_efficiency_heat_pump_cooling_res(DataObject):
    _instances_by_key = {}
    _key_col = "parent"
    _cols = ["parent", "gau", "dispatch_feeder", "resource_bin", "dispatch_constraint", "year",
             "month", "week", "hour", "day_type", "weather_datetime", "value", "id"]
    _table_name = "high_efficiency_heat_pump_cooling_res"
    _data_table_name = None

    def __init__(self, parent, scenario):
        DataObject.__init__(self, parent, scenario)

        high_efficiency_heat_pump_cooling_res._instances_by_key[self._key] = self

        self.parent = None
        self.gau = None
        self.dispatch_feeder = None
        self.resource_bin = None
        self.dispatch_constraint = None
        self.year = None
        self.month = None
        self.week = None
        self.hour = None
        self.day_type = None
        self.weather_datetime = None
        self.value = None
        self.id = None

    def set_args(self, scenario, parent=None, gau=None, dispatch_feeder=None, resource_bin=None, dispatch_constraint=None,
                 year=None, month=None, week=None, hour=None, day_type=None, weather_datetime=None,
                 value=None, id=None):
        self.parent = parent
        self.gau = gau
        self.dispatch_feeder = dispatch_feeder
        self.resource_bin = resource_bin
        self.dispatch_constraint = dispatch_constraint
        self.year = year
        self.month = month
        self.week = week
        self.hour = hour
        self.day_type = day_type
        self.weather_datetime = weather_datetime
        self.value = value
        self.id = id

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (parent, gau, dispatch_feeder, resource_bin, dispatch_constraint, year, month, week, hour,
         day_type, weather_datetime, value, id) = tup

        self.set_args(scenario, parent=parent, gau=gau, dispatch_feeder=dispatch_feeder, resource_bin=resource_bin,
                  dispatch_constraint=dispatch_constraint, year=year, month=month, week=week, hour=hour,
                  day_type=day_type, weather_datetime=weather_datetime, value=value, id=id)

class high_efficiency_heat_pump_heating_res(DataObject):
    _instances_by_key = {}
    _key_col = "parent"
    _cols = ["parent", "gau", "dispatch_feeder", "resource_bin", "dispatch_constraint", "year",
             "month", "week", "hour", "day_type", "weather_datetime", "value", "id"]
    _table_name = "high_efficiency_heat_pump_heating_res"
    _data_table_name = None

    def __init__(self, parent, scenario):
        DataObject.__init__(self, parent, scenario)

        high_efficiency_heat_pump_heating_res._instances_by_key[self._key] = self

        self.parent = None
        self.gau = None
        self.dispatch_feeder = None
        self.resource_bin = None
        self.dispatch_constraint = None
        self.year = None
        self.month = None
        self.week = None
        self.hour = None
        self.day_type = None
        self.weather_datetime = None
        self.value = None
        self.id = None

    def set_args(self, scenario, parent=None, gau=None, dispatch_feeder=None, resource_bin=None, dispatch_constraint=None,
                 year=None, month=None, week=None, hour=None, day_type=None, weather_datetime=None,
                 value=None, id=None):
        self.parent = parent
        self.gau = gau
        self.dispatch_feeder = dispatch_feeder
        self.resource_bin = resource_bin
        self.dispatch_constraint = dispatch_constraint
        self.year = year
        self.month = month
        self.week = week
        self.hour = hour
        self.day_type = day_type
        self.weather_datetime = weather_datetime
        self.value = value
        self.id = id

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (parent, gau, dispatch_feeder, resource_bin, dispatch_constraint, year, month, week, hour,
         day_type, weather_datetime, value, id) = tup

        self.set_args(scenario, parent=parent, gau=gau, dispatch_feeder=dispatch_feeder, resource_bin=resource_bin,
                  dispatch_constraint=dispatch_constraint, year=year, month=month, week=week, hour=hour,
                  day_type=day_type, weather_datetime=weather_datetime, value=value, id=id)

class high_efficiency_room_ac_res(DataObject):
    _instances_by_key = {}
    _key_col = "parent"
    _cols = ["parent", "gau", "dispatch_feeder", "resource_bin", "dispatch_constraint", "year",
             "month", "week", "hour", "day_type", "weather_datetime", "value", "id"]
    _table_name = "high_efficiency_room_ac_res"
    _data_table_name = None

    def __init__(self, parent, scenario):
        DataObject.__init__(self, parent, scenario)

        high_efficiency_room_ac_res._instances_by_key[self._key] = self

        self.parent = None
        self.gau = None
        self.dispatch_feeder = None
        self.resource_bin = None
        self.dispatch_constraint = None
        self.year = None
        self.month = None
        self.week = None
        self.hour = None
        self.day_type = None
        self.weather_datetime = None
        self.value = None
        self.id = None

    def set_args(self, scenario, parent=None, gau=None, dispatch_feeder=None, resource_bin=None, dispatch_constraint=None,
                 year=None, month=None, week=None, hour=None, day_type=None, weather_datetime=None,
                 value=None, id=None):
        self.parent = parent
        self.gau = gau
        self.dispatch_feeder = dispatch_feeder
        self.resource_bin = resource_bin
        self.dispatch_constraint = dispatch_constraint
        self.year = year
        self.month = month
        self.week = week
        self.hour = hour
        self.day_type = day_type
        self.weather_datetime = weather_datetime
        self.value = value
        self.id = id

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (parent, gau, dispatch_feeder, resource_bin, dispatch_constraint, year, month, week, hour,
         day_type, weather_datetime, value, id) = tup

        self.set_args(scenario, parent=parent, gau=gau, dispatch_feeder=dispatch_feeder, resource_bin=resource_bin,
                  dispatch_constraint=dispatch_constraint, year=year, month=month, week=week, hour=hour,
                  day_type=day_type, weather_datetime=weather_datetime, value=value, id=id)

class lighting(DataObject):
    _instances_by_key = {}
    _key_col = "parent"
    _cols = ["parent", "gau", "dispatch_feeder", "resource_bin", "dispatch_constraint", "year",
             "month", "week", "hour", "day_type", "weather_datetime", "value", "id"]
    _table_name = "lighting"
    _data_table_name = None

    def __init__(self, parent, scenario):
        DataObject.__init__(self, parent, scenario)

        lighting._instances_by_key[self._key] = self

        self.parent = None
        self.gau = None
        self.dispatch_feeder = None
        self.resource_bin = None
        self.dispatch_constraint = None
        self.year = None
        self.month = None
        self.week = None
        self.hour = None
        self.day_type = None
        self.weather_datetime = None
        self.value = None
        self.id = None

    def set_args(self, scenario, parent=None, gau=None, dispatch_feeder=None, resource_bin=None, dispatch_constraint=None,
                 year=None, month=None, week=None, hour=None, day_type=None, weather_datetime=None,
                 value=None, id=None):
        self.parent = parent
        self.gau = gau
        self.dispatch_feeder = dispatch_feeder
        self.resource_bin = resource_bin
        self.dispatch_constraint = dispatch_constraint
        self.year = year
        self.month = month
        self.week = week
        self.hour = hour
        self.day_type = day_type
        self.weather_datetime = weather_datetime
        self.value = value
        self.id = id

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (parent, gau, dispatch_feeder, resource_bin, dispatch_constraint, year, month, week, hour,
         day_type, weather_datetime, value, id) = tup

        self.set_args(scenario, parent=parent, gau=gau, dispatch_feeder=dispatch_feeder, resource_bin=resource_bin,
                  dispatch_constraint=dispatch_constraint, year=year, month=month, week=week, hour=hour,
                  day_type=day_type, weather_datetime=weather_datetime, value=value, id=id)

class offshore(DataObject):
    _instances_by_key = {}
    _key_col = "parent"
    _cols = ["parent", "gau", "dispatch_feeder", "resource_bin", "dispatch_constraint", "year",
             "month", "week", "hour", "day_type", "weather_datetime", "value", "id"]
    _table_name = "offshore"
    _data_table_name = None

    def __init__(self, parent, scenario):
        DataObject.__init__(self, parent, scenario)

        offshore._instances_by_key[self._key] = self

        self.parent = None
        self.gau = None
        self.dispatch_feeder = None
        self.resource_bin = None
        self.dispatch_constraint = None
        self.year = None
        self.month = None
        self.week = None
        self.hour = None
        self.day_type = None
        self.weather_datetime = None
        self.value = None
        self.id = None

    def set_args(self, scenario, parent=None, gau=None, dispatch_feeder=None, resource_bin=None, dispatch_constraint=None,
                 year=None, month=None, week=None, hour=None, day_type=None, weather_datetime=None,
                 value=None, id=None):
        self.parent = parent
        self.gau = gau
        self.dispatch_feeder = dispatch_feeder
        self.resource_bin = resource_bin
        self.dispatch_constraint = dispatch_constraint
        self.year = year
        self.month = month
        self.week = week
        self.hour = hour
        self.day_type = day_type
        self.weather_datetime = weather_datetime
        self.value = value
        self.id = id

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (parent, gau, dispatch_feeder, resource_bin, dispatch_constraint, year, month, week, hour,
         day_type, weather_datetime, value, id) = tup

        self.set_args(scenario, parent=parent, gau=gau, dispatch_feeder=dispatch_feeder, resource_bin=resource_bin,
                  dispatch_constraint=dispatch_constraint, year=year, month=month, week=week, hour=hour,
                  day_type=day_type, weather_datetime=weather_datetime, value=value, id=id)

class onshore(DataObject):
    _instances_by_key = {}
    _key_col = "parent"
    _cols = ["parent", "gau", "dispatch_feeder", "resource_bin", "dispatch_constraint", "year",
             "month", "week", "hour", "day_type", "weather_datetime", "value", "id"]
    _table_name = "onshore"
    _data_table_name = None

    def __init__(self, parent, scenario):
        DataObject.__init__(self, parent, scenario)

        onshore._instances_by_key[self._key] = self

        self.parent = None
        self.gau = None
        self.dispatch_feeder = None
        self.resource_bin = None
        self.dispatch_constraint = None
        self.year = None
        self.month = None
        self.week = None
        self.hour = None
        self.day_type = None
        self.weather_datetime = None
        self.value = None
        self.id = None

    def set_args(self, scenario, parent=None, gau=None, dispatch_feeder=None, resource_bin=None, dispatch_constraint=None,
                 year=None, month=None, week=None, hour=None, day_type=None, weather_datetime=None,
                 value=None, id=None):
        self.parent = parent
        self.gau = gau
        self.dispatch_feeder = dispatch_feeder
        self.resource_bin = resource_bin
        self.dispatch_constraint = dispatch_constraint
        self.year = year
        self.month = month
        self.week = week
        self.hour = hour
        self.day_type = day_type
        self.weather_datetime = weather_datetime
        self.value = value
        self.id = id

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (parent, gau, dispatch_feeder, resource_bin, dispatch_constraint, year, month, week, hour,
         day_type, weather_datetime, value, id) = tup

        self.set_args(scenario, parent=parent, gau=gau, dispatch_feeder=dispatch_feeder, resource_bin=resource_bin,
                  dispatch_constraint=dispatch_constraint, year=year, month=month, week=week, hour=hour,
                  day_type=day_type, weather_datetime=weather_datetime, value=value, id=id)

class other_appliances(DataObject):
    _instances_by_key = {}
    _key_col = "parent"
    _cols = ["parent", "gau", "dispatch_feeder", "resource_bin", "dispatch_constraint", "year",
             "month", "week", "hour", "day_type", "weather_datetime", "value", "id"]
    _table_name = "other_appliances"
    _data_table_name = None

    def __init__(self, parent, scenario):
        DataObject.__init__(self, parent, scenario)

        other_appliances._instances_by_key[self._key] = self

        self.parent = None
        self.gau = None
        self.dispatch_feeder = None
        self.resource_bin = None
        self.dispatch_constraint = None
        self.year = None
        self.month = None
        self.week = None
        self.hour = None
        self.day_type = None
        self.weather_datetime = None
        self.value = None
        self.id = None

    def set_args(self, scenario, parent=None, gau=None, dispatch_feeder=None, resource_bin=None, dispatch_constraint=None,
                 year=None, month=None, week=None, hour=None, day_type=None, weather_datetime=None,
                 value=None, id=None):
        self.parent = parent
        self.gau = gau
        self.dispatch_feeder = dispatch_feeder
        self.resource_bin = resource_bin
        self.dispatch_constraint = dispatch_constraint
        self.year = year
        self.month = month
        self.week = week
        self.hour = hour
        self.day_type = day_type
        self.weather_datetime = weather_datetime
        self.value = value
        self.id = id

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (parent, gau, dispatch_feeder, resource_bin, dispatch_constraint, year, month, week, hour,
         day_type, weather_datetime, value, id) = tup

        self.set_args(scenario, parent=parent, gau=gau, dispatch_feeder=dispatch_feeder, resource_bin=resource_bin,
                  dispatch_constraint=dispatch_constraint, year=year, month=month, week=week, hour=hour,
                  day_type=day_type, weather_datetime=weather_datetime, value=value, id=id)

class pv_Distribution_Sited(DataObject):
    _instances_by_key = {}
    _key_col = "parent"
    _cols = ["parent", "gau", "dispatch_feeder", "resource_bin", "dispatch_constraint", "year",
             "month", "week", "hour", "day_type", "weather_datetime", "value", "id"]
    _table_name = "pv_Distribution_Sited"
    _data_table_name = None

    def __init__(self, parent, scenario):
        DataObject.__init__(self, parent, scenario)

        pv_Distribution_Sited._instances_by_key[self._key] = self

        self.parent = None
        self.gau = None
        self.dispatch_feeder = None
        self.resource_bin = None
        self.dispatch_constraint = None
        self.year = None
        self.month = None
        self.week = None
        self.hour = None
        self.day_type = None
        self.weather_datetime = None
        self.value = None
        self.id = None

    def set_args(self, scenario, parent=None, gau=None, dispatch_feeder=None, resource_bin=None, dispatch_constraint=None,
                 year=None, month=None, week=None, hour=None, day_type=None, weather_datetime=None,
                 value=None, id=None):
        self.parent = parent
        self.gau = gau
        self.dispatch_feeder = dispatch_feeder
        self.resource_bin = resource_bin
        self.dispatch_constraint = dispatch_constraint
        self.year = year
        self.month = month
        self.week = week
        self.hour = hour
        self.day_type = day_type
        self.weather_datetime = weather_datetime
        self.value = value
        self.id = id

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (parent, gau, dispatch_feeder, resource_bin, dispatch_constraint, year, month, week, hour,
         day_type, weather_datetime, value, id) = tup

        self.set_args(scenario, parent=parent, gau=gau, dispatch_feeder=dispatch_feeder, resource_bin=resource_bin,
                  dispatch_constraint=dispatch_constraint, year=year, month=month, week=week, hour=hour,
                  day_type=day_type, weather_datetime=weather_datetime, value=value, id=id)

class pv_Rooftop(DataObject):
    _instances_by_key = {}
    _key_col = "parent"
    _cols = ["parent", "gau", "dispatch_feeder", "resource_bin", "dispatch_constraint", "year",
             "month", "week", "hour", "day_type", "weather_datetime", "value", "id"]
    _table_name = "pv_Rooftop"
    _data_table_name = None

    def __init__(self, parent, scenario):
        DataObject.__init__(self, parent, scenario)

        pv_Rooftop._instances_by_key[self._key] = self

        self.parent = None
        self.gau = None
        self.dispatch_feeder = None
        self.resource_bin = None
        self.dispatch_constraint = None
        self.year = None
        self.month = None
        self.week = None
        self.hour = None
        self.day_type = None
        self.weather_datetime = None
        self.value = None
        self.id = None

    def set_args(self, scenario, parent=None, gau=None, dispatch_feeder=None, resource_bin=None, dispatch_constraint=None,
                 year=None, month=None, week=None, hour=None, day_type=None, weather_datetime=None,
                 value=None, id=None):
        self.parent = parent
        self.gau = gau
        self.dispatch_feeder = dispatch_feeder
        self.resource_bin = resource_bin
        self.dispatch_constraint = dispatch_constraint
        self.year = year
        self.month = month
        self.week = week
        self.hour = hour
        self.day_type = day_type
        self.weather_datetime = weather_datetime
        self.value = value
        self.id = id

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (parent, gau, dispatch_feeder, resource_bin, dispatch_constraint, year, month, week, hour,
         day_type, weather_datetime, value, id) = tup

        self.set_args(scenario, parent=parent, gau=gau, dispatch_feeder=dispatch_feeder, resource_bin=resource_bin,
                  dispatch_constraint=dispatch_constraint, year=year, month=month, week=week, hour=hour,
                  day_type=day_type, weather_datetime=weather_datetime, value=value, id=id)

class pv_Transmission_Sited(DataObject):
    _instances_by_key = {}
    _key_col = "parent"
    _cols = ["parent", "gau", "dispatch_feeder", "resource_bin", "dispatch_constraint", "year",
             "month", "week", "hour", "day_type", "weather_datetime", "value", "id"]
    _table_name = "pv_Transmission_Sited"
    _data_table_name = None

    def __init__(self, parent, scenario):
        DataObject.__init__(self, parent, scenario)

        pv_Transmission_Sited._instances_by_key[self._key] = self

        self.parent = None
        self.gau = None
        self.dispatch_feeder = None
        self.resource_bin = None
        self.dispatch_constraint = None
        self.year = None
        self.month = None
        self.week = None
        self.hour = None
        self.day_type = None
        self.weather_datetime = None
        self.value = None
        self.id = None

    def set_args(self, scenario, parent=None, gau=None, dispatch_feeder=None, resource_bin=None, dispatch_constraint=None,
                 year=None, month=None, week=None, hour=None, day_type=None, weather_datetime=None,
                 value=None, id=None):
        self.parent = parent
        self.gau = gau
        self.dispatch_feeder = dispatch_feeder
        self.resource_bin = resource_bin
        self.dispatch_constraint = dispatch_constraint
        self.year = year
        self.month = month
        self.week = week
        self.hour = hour
        self.day_type = day_type
        self.weather_datetime = weather_datetime
        self.value = value
        self.id = id

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (parent, gau, dispatch_feeder, resource_bin, dispatch_constraint, year, month, week, hour,
         day_type, weather_datetime, value, id) = tup

        self.set_args(scenario, parent=parent, gau=gau, dispatch_feeder=dispatch_feeder, resource_bin=resource_bin,
                  dispatch_constraint=dispatch_constraint, year=year, month=month, week=week, hour=hour,
                  day_type=day_type, weather_datetime=weather_datetime, value=value, id=id)

class reference_central_ac_res(DataObject):
    _instances_by_key = {}
    _key_col = "parent"
    _cols = ["parent", "gau", "dispatch_feeder", "resource_bin", "dispatch_constraint", "year",
             "month", "week", "hour", "day_type", "weather_datetime", "value", "id"]
    _table_name = "reference_central_ac_res"
    _data_table_name = None

    def __init__(self, parent, scenario):
        DataObject.__init__(self, parent, scenario)

        reference_central_ac_res._instances_by_key[self._key] = self

        self.parent = None
        self.gau = None
        self.dispatch_feeder = None
        self.resource_bin = None
        self.dispatch_constraint = None
        self.year = None
        self.month = None
        self.week = None
        self.hour = None
        self.day_type = None
        self.weather_datetime = None
        self.value = None
        self.id = None

    def set_args(self, scenario, parent=None, gau=None, dispatch_feeder=None, resource_bin=None, dispatch_constraint=None,
                 year=None, month=None, week=None, hour=None, day_type=None, weather_datetime=None,
                 value=None, id=None):
        self.parent = parent
        self.gau = gau
        self.dispatch_feeder = dispatch_feeder
        self.resource_bin = resource_bin
        self.dispatch_constraint = dispatch_constraint
        self.year = year
        self.month = month
        self.week = week
        self.hour = hour
        self.day_type = day_type
        self.weather_datetime = weather_datetime
        self.value = value
        self.id = id

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (parent, gau, dispatch_feeder, resource_bin, dispatch_constraint, year, month, week, hour,
         day_type, weather_datetime, value, id) = tup

        self.set_args(scenario, parent=parent, gau=gau, dispatch_feeder=dispatch_feeder, resource_bin=resource_bin,
                  dispatch_constraint=dispatch_constraint, year=year, month=month, week=week, hour=hour,
                  day_type=day_type, weather_datetime=weather_datetime, value=value, id=id)

class reference_heat_pump_cooling_res(DataObject):
    _instances_by_key = {}
    _key_col = "parent"
    _cols = ["parent", "gau", "dispatch_feeder", "resource_bin", "dispatch_constraint", "year",
             "month", "week", "hour", "day_type", "weather_datetime", "value", "id"]
    _table_name = "reference_heat_pump_cooling_res"
    _data_table_name = None

    def __init__(self, parent, scenario):
        DataObject.__init__(self, parent, scenario)

        reference_heat_pump_cooling_res._instances_by_key[self._key] = self

        self.parent = None
        self.gau = None
        self.dispatch_feeder = None
        self.resource_bin = None
        self.dispatch_constraint = None
        self.year = None
        self.month = None
        self.week = None
        self.hour = None
        self.day_type = None
        self.weather_datetime = None
        self.value = None
        self.id = None

    def set_args(self, scenario, parent=None, gau=None, dispatch_feeder=None, resource_bin=None, dispatch_constraint=None,
                 year=None, month=None, week=None, hour=None, day_type=None, weather_datetime=None,
                 value=None, id=None):
        self.parent = parent
        self.gau = gau
        self.dispatch_feeder = dispatch_feeder
        self.resource_bin = resource_bin
        self.dispatch_constraint = dispatch_constraint
        self.year = year
        self.month = month
        self.week = week
        self.hour = hour
        self.day_type = day_type
        self.weather_datetime = weather_datetime
        self.value = value
        self.id = id

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (parent, gau, dispatch_feeder, resource_bin, dispatch_constraint, year, month, week, hour,
         day_type, weather_datetime, value, id) = tup

        self.set_args(scenario, parent=parent, gau=gau, dispatch_feeder=dispatch_feeder, resource_bin=resource_bin,
                  dispatch_constraint=dispatch_constraint, year=year, month=month, week=week, hour=hour,
                  day_type=day_type, weather_datetime=weather_datetime, value=value, id=id)

class reference_heat_pump_heating_res(DataObject):
    _instances_by_key = {}
    _key_col = "parent"
    _cols = ["parent", "gau", "dispatch_feeder", "resource_bin", "dispatch_constraint", "year",
             "month", "week", "hour", "day_type", "weather_datetime", "value", "id"]
    _table_name = "reference_heat_pump_heating_res"
    _data_table_name = None

    def __init__(self, parent, scenario):
        DataObject.__init__(self, parent, scenario)

        reference_heat_pump_heating_res._instances_by_key[self._key] = self

        self.parent = None
        self.gau = None
        self.dispatch_feeder = None
        self.resource_bin = None
        self.dispatch_constraint = None
        self.year = None
        self.month = None
        self.week = None
        self.hour = None
        self.day_type = None
        self.weather_datetime = None
        self.value = None
        self.id = None

    def set_args(self, scenario, parent=None, gau=None, dispatch_feeder=None, resource_bin=None, dispatch_constraint=None,
                 year=None, month=None, week=None, hour=None, day_type=None, weather_datetime=None,
                 value=None, id=None):
        self.parent = parent
        self.gau = gau
        self.dispatch_feeder = dispatch_feeder
        self.resource_bin = resource_bin
        self.dispatch_constraint = dispatch_constraint
        self.year = year
        self.month = month
        self.week = week
        self.hour = hour
        self.day_type = day_type
        self.weather_datetime = weather_datetime
        self.value = value
        self.id = id

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (parent, gau, dispatch_feeder, resource_bin, dispatch_constraint, year, month, week, hour,
         day_type, weather_datetime, value, id) = tup

        self.set_args(scenario, parent=parent, gau=gau, dispatch_feeder=dispatch_feeder, resource_bin=resource_bin,
                  dispatch_constraint=dispatch_constraint, year=year, month=month, week=week, hour=hour,
                  day_type=day_type, weather_datetime=weather_datetime, value=value, id=id)

class reference_room_ac_res(DataObject):
    _instances_by_key = {}
    _key_col = "parent"
    _cols = ["parent", "gau", "dispatch_feeder", "resource_bin", "dispatch_constraint", "year",
             "month", "week", "hour", "day_type", "weather_datetime", "value", "id"]
    _table_name = "reference_room_ac_res"
    _data_table_name = None

    def __init__(self, parent, scenario):
        DataObject.__init__(self, parent, scenario)

        reference_room_ac_res._instances_by_key[self._key] = self

        self.parent = None
        self.gau = None
        self.dispatch_feeder = None
        self.resource_bin = None
        self.dispatch_constraint = None
        self.year = None
        self.month = None
        self.week = None
        self.hour = None
        self.day_type = None
        self.weather_datetime = None
        self.value = None
        self.id = None

    def set_args(self, scenario, parent=None, gau=None, dispatch_feeder=None, resource_bin=None, dispatch_constraint=None,
                 year=None, month=None, week=None, hour=None, day_type=None, weather_datetime=None,
                 value=None, id=None):
        self.parent = parent
        self.gau = gau
        self.dispatch_feeder = dispatch_feeder
        self.resource_bin = resource_bin
        self.dispatch_constraint = dispatch_constraint
        self.year = year
        self.month = month
        self.week = week
        self.hour = hour
        self.day_type = day_type
        self.weather_datetime = weather_datetime
        self.value = value
        self.id = id

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (parent, gau, dispatch_feeder, resource_bin, dispatch_constraint, year, month, week, hour,
         day_type, weather_datetime, value, id) = tup

        self.set_args(scenario, parent=parent, gau=gau, dispatch_feeder=dispatch_feeder, resource_bin=resource_bin,
                  dispatch_constraint=dispatch_constraint, year=year, month=month, week=week, hour=hour,
                  day_type=day_type, weather_datetime=weather_datetime, value=value, id=id)

class residential_cooking(DataObject):
    _instances_by_key = {}
    _key_col = "parent"
    _cols = ["parent", "gau", "dispatch_feeder", "resource_bin", "dispatch_constraint", "year",
             "month", "week", "hour", "day_type", "weather_datetime", "value", "id"]
    _table_name = "residential_cooking"
    _data_table_name = None

    def __init__(self, parent, scenario):
        DataObject.__init__(self, parent, scenario)

        residential_cooking._instances_by_key[self._key] = self

        self.parent = None
        self.gau = None
        self.dispatch_feeder = None
        self.resource_bin = None
        self.dispatch_constraint = None
        self.year = None
        self.month = None
        self.week = None
        self.hour = None
        self.day_type = None
        self.weather_datetime = None
        self.value = None
        self.id = None

    def set_args(self, scenario, parent=None, gau=None, dispatch_feeder=None, resource_bin=None, dispatch_constraint=None,
                 year=None, month=None, week=None, hour=None, day_type=None, weather_datetime=None,
                 value=None, id=None):
        self.parent = parent
        self.gau = gau
        self.dispatch_feeder = dispatch_feeder
        self.resource_bin = resource_bin
        self.dispatch_constraint = dispatch_constraint
        self.year = year
        self.month = month
        self.week = week
        self.hour = hour
        self.day_type = day_type
        self.weather_datetime = weather_datetime
        self.value = value
        self.id = id

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (parent, gau, dispatch_feeder, resource_bin, dispatch_constraint, year, month, week, hour,
         day_type, weather_datetime, value, id) = tup

        self.set_args(scenario, parent=parent, gau=gau, dispatch_feeder=dispatch_feeder, resource_bin=resource_bin,
                  dispatch_constraint=dispatch_constraint, year=year, month=month, week=week, hour=hour,
                  day_type=day_type, weather_datetime=weather_datetime, value=value, id=id)

class residential_freezing(DataObject):
    _instances_by_key = {}
    _key_col = "parent"
    _cols = ["parent", "gau", "dispatch_feeder", "resource_bin", "dispatch_constraint", "year",
             "month", "week", "hour", "day_type", "weather_datetime", "value", "id"]
    _table_name = "residential_freezing"
    _data_table_name = None

    def __init__(self, parent, scenario):
        DataObject.__init__(self, parent, scenario)

        residential_freezing._instances_by_key[self._key] = self

        self.parent = None
        self.gau = None
        self.dispatch_feeder = None
        self.resource_bin = None
        self.dispatch_constraint = None
        self.year = None
        self.month = None
        self.week = None
        self.hour = None
        self.day_type = None
        self.weather_datetime = None
        self.value = None
        self.id = None

    def set_args(self, scenario, parent=None, gau=None, dispatch_feeder=None, resource_bin=None, dispatch_constraint=None,
                 year=None, month=None, week=None, hour=None, day_type=None, weather_datetime=None,
                 value=None, id=None):
        self.parent = parent
        self.gau = gau
        self.dispatch_feeder = dispatch_feeder
        self.resource_bin = resource_bin
        self.dispatch_constraint = dispatch_constraint
        self.year = year
        self.month = month
        self.week = week
        self.hour = hour
        self.day_type = day_type
        self.weather_datetime = weather_datetime
        self.value = value
        self.id = id

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (parent, gau, dispatch_feeder, resource_bin, dispatch_constraint, year, month, week, hour,
         day_type, weather_datetime, value, id) = tup

        self.set_args(scenario, parent=parent, gau=gau, dispatch_feeder=dispatch_feeder, resource_bin=resource_bin,
                  dispatch_constraint=dispatch_constraint, year=year, month=month, week=week, hour=hour,
                  day_type=day_type, weather_datetime=weather_datetime, value=value, id=id)

class residential_refrigeration(DataObject):
    _instances_by_key = {}
    _key_col = "parent"
    _cols = ["parent", "gau", "dispatch_feeder", "resource_bin", "dispatch_constraint", "year",
             "month", "week", "hour", "day_type", "weather_datetime", "value", "id"]
    _table_name = "residential_refrigeration"
    _data_table_name = None

    def __init__(self, parent, scenario):
        DataObject.__init__(self, parent, scenario)

        residential_refrigeration._instances_by_key[self._key] = self

        self.parent = None
        self.gau = None
        self.dispatch_feeder = None
        self.resource_bin = None
        self.dispatch_constraint = None
        self.year = None
        self.month = None
        self.week = None
        self.hour = None
        self.day_type = None
        self.weather_datetime = None
        self.value = None
        self.id = None

    def set_args(self, scenario, parent=None, gau=None, dispatch_feeder=None, resource_bin=None, dispatch_constraint=None,
                 year=None, month=None, week=None, hour=None, day_type=None, weather_datetime=None,
                 value=None, id=None):
        self.parent = parent
        self.gau = gau
        self.dispatch_feeder = dispatch_feeder
        self.resource_bin = resource_bin
        self.dispatch_constraint = dispatch_constraint
        self.year = year
        self.month = month
        self.week = week
        self.hour = hour
        self.day_type = day_type
        self.weather_datetime = weather_datetime
        self.value = value
        self.id = id

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (parent, gau, dispatch_feeder, resource_bin, dispatch_constraint, year, month, week, hour,
         day_type, weather_datetime, value, id) = tup

        self.set_args(scenario, parent=parent, gau=gau, dispatch_feeder=dispatch_feeder, resource_bin=resource_bin,
                  dispatch_constraint=dispatch_constraint, year=year, month=month, week=week, hour=hour,
                  day_type=day_type, weather_datetime=weather_datetime, value=value, id=id)

class system_load(DataObject):
    _instances_by_key = {}
    _key_col = "parent"
    _cols = ["parent", "gau", "dispatch_feeder", "resource_bin", "dispatch_constraint", "year",
             "month", "week", "hour", "day_type", "weather_datetime", "value", "id"]
    _table_name = "system_load"
    _data_table_name = None

    def __init__(self, parent, scenario):
        DataObject.__init__(self, parent, scenario)

        system_load._instances_by_key[self._key] = self

        self.parent = None
        self.gau = None
        self.dispatch_feeder = None
        self.resource_bin = None
        self.dispatch_constraint = None
        self.year = None
        self.month = None
        self.week = None
        self.hour = None
        self.day_type = None
        self.weather_datetime = None
        self.value = None
        self.id = None

    def set_args(self, scenario, parent=None, gau=None, dispatch_feeder=None, resource_bin=None, dispatch_constraint=None,
                 year=None, month=None, week=None, hour=None, day_type=None, weather_datetime=None,
                 value=None, id=None):
        self.parent = parent
        self.gau = gau
        self.dispatch_feeder = dispatch_feeder
        self.resource_bin = resource_bin
        self.dispatch_constraint = dispatch_constraint
        self.year = year
        self.month = month
        self.week = week
        self.hour = hour
        self.day_type = day_type
        self.weather_datetime = weather_datetime
        self.value = value
        self.id = id

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (parent, gau, dispatch_feeder, resource_bin, dispatch_constraint, year, month, week, hour,
         day_type, weather_datetime, value, id) = tup

        self.set_args(scenario, parent=parent, gau=gau, dispatch_feeder=dispatch_feeder, resource_bin=resource_bin,
                  dispatch_constraint=dispatch_constraint, year=year, month=month, week=week, hour=hour,
                  day_type=day_type, weather_datetime=weather_datetime, value=value, id=id)

class water_heating_gas_NW_data_month_hour(DataObject):
    _instances_by_key = {}
    _key_col = "parent"
    _cols = ["parent", "gau", "dispatch_feeder", "resource_bin", "dispatch_constraint", "year",
             "month", "week", "hour", "day_type", "weather_datetime", "value", "id"]
    _table_name = "water_heating_gas_NW_data_month_hour"
    _data_table_name = None

    def __init__(self, parent, scenario):
        DataObject.__init__(self, parent, scenario)

        water_heating_gas_NW_data_month_hour._instances_by_key[self._key] = self

        self.parent = None
        self.gau = None
        self.dispatch_feeder = None
        self.resource_bin = None
        self.dispatch_constraint = None
        self.year = None
        self.month = None
        self.week = None
        self.hour = None
        self.day_type = None
        self.weather_datetime = None
        self.value = None
        self.id = None

    def set_args(self, scenario, parent=None, gau=None, dispatch_feeder=None, resource_bin=None, dispatch_constraint=None,
                 year=None, month=None, week=None, hour=None, day_type=None, weather_datetime=None,
                 value=None, id=None):
        self.parent = parent
        self.gau = gau
        self.dispatch_feeder = dispatch_feeder
        self.resource_bin = resource_bin
        self.dispatch_constraint = dispatch_constraint
        self.year = year
        self.month = month
        self.week = week
        self.hour = hour
        self.day_type = day_type
        self.weather_datetime = weather_datetime
        self.value = value
        self.id = id

        self.load_child_data(scenario)

    def init_from_tuple(self, tup, scenario, **kwargs):    
        (parent, gau, dispatch_feeder, resource_bin, dispatch_constraint, year, month, week, hour,
         day_type, weather_datetime, value, id) = tup

        self.set_args(scenario, parent=parent, gau=gau, dispatch_feeder=dispatch_feeder, resource_bin=resource_bin,
                  dispatch_constraint=dispatch_constraint, year=year, month=month, week=week, hour=hour,
                  day_type=day_type, weather_datetime=weather_datetime, value=value, id=id)

