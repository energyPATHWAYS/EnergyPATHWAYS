# coding: utf-8
from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, Table, Text, UniqueConstraint, text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()
metadata = Base.metadata


class AgeGrowthOrDecayType(Base):
    __tablename__ = 'AgeGrowthOrDecayType'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"AgeGrowthOrDecayType_id_seq\"'::regclass)"))
    name = Column(Text)


class BlendNodeBlendMeasurePackage(Base):
    __tablename__ = 'BlendNodeBlendMeasurePackages'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"BlendNodeBlendMeasurePackages_id_seq\"'::regclass)"))
    name = Column(Text)
    blend_subsector_id = Column(ForeignKey(u'SupplyNodes.id'))

    blend_subsector = relationship(u'SupplyNode')


t_BlendNodeBlendMeasurePackagesData = Table(
    'BlendNodeBlendMeasurePackagesData', metadata,
    Column('package_id', ForeignKey(u'BlendNodeBlendMeasurePackages.id')),
    Column('measure_id', ForeignKey(u'BlendNodeBlendMeasures.id'))
)


class BlendNodeBlendMeasure(Base):
    __tablename__ = 'BlendNodeBlendMeasures'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"BlendNodeBlendMeasures_id_seq\"'::regclass)"))
    name = Column(Text)
    blend_node_id = Column(ForeignKey(u'SupplyNodes.id'))
    supply_node_id = Column(ForeignKey(u'SupplyNodes.id'))
    geography_id = Column(ForeignKey(u'Geographies.id'))
    other_index_1_id = Column(ForeignKey(u'OtherIndexes.id'))
    interpolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_growth = Column(Float)

    blend_node = relationship(u'SupplyNode', primaryjoin='BlendNodeBlendMeasure.blend_node_id == SupplyNode.id')
    extrapolation_method = relationship(u'CleaningMethod', primaryjoin='BlendNodeBlendMeasure.extrapolation_method_id == CleaningMethod.id')
    geography = relationship(u'Geography')
    interpolation_method = relationship(u'CleaningMethod', primaryjoin='BlendNodeBlendMeasure.interpolation_method_id == CleaningMethod.id')
    other_index_1 = relationship(u'OtherIndex')
    supply_node = relationship(u'SupplyNode', primaryjoin='BlendNodeBlendMeasure.supply_node_id == SupplyNode.id')
    packages = relationship(u'BlendNodeBlendMeasurePackage', secondary='BlendNodeBlendMeasurePackagesData')


t_BlendNodeBlendMeasuresData = Table(
    'BlendNodeBlendMeasuresData', metadata,
    Column('id', ForeignKey(u'BlendNodeBlendMeasures.id')),
    Column('gau_id', ForeignKey(u'GeographiesData.id')),
    Column('year', Integer),
    Column('value', Float)
)


t_BlendNodeInputsData = Table(
    'BlendNodeInputsData', metadata,
    Column('blend_node_id', ForeignKey(u'SupplyNodes.id')),
    Column('supply_node_id', ForeignKey(u'SupplyNodes.id'))
)


class CleaningMethod(Base):
    __tablename__ = 'CleaningMethods'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"CleaningMethods_id_seq\"'::regclass)"))
    name = Column(Text, unique=True)


class Currency(Base):
    __tablename__ = 'Currencies'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"Currencies_id_seq\"'::regclass)"))
    name = Column(Text)


t_CurrenciesConversion = Table(
    'CurrenciesConversion', metadata,
    Column('currency_id', Integer),
    Column('currency_year_id', Integer),
    Column('value', Float(53))
)


class CurrencyYear(Base):
    __tablename__ = 'CurrencyYears'

    id = Column(Integer, primary_key=True)


class DayHour(Base):
    __tablename__ = 'DayHour'

    day_hour = Column(Integer, primary_key=True, server_default=text("nextval('\"DayHour_day_hour_seq\"'::regclass)"))


class DayType(Base):
    __tablename__ = 'DayType'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DayType_id_seq\"'::regclass)"))
    name = Column(Text)


class Definition(Base):
    __tablename__ = 'Definitions'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"Definitions_id_seq\"'::regclass)"))
    name = Column(Text, unique=True)


class DemandCO2CaptureMeasure(Base):
    __tablename__ = 'DemandCO2CaptureMeasures'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DemandCO2CaptureMeasures_id_seq\"'::regclass)"))
    name = Column(Text)
    subsector_id = Column(ForeignKey(u'DemandSubsectors.id'))
    input_type_id = Column(ForeignKey(u'InputTypes.id'))
    unit = Column(Text)
    geography_id = Column(ForeignKey(u'Geographies.id'))
    other_index_1_id = Column(ForeignKey(u'OtherIndexes.id'))
    other_index_2_id = Column(ForeignKey(u'OtherIndexesData.id'))
    interpolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_growth = Column(Float)
    stock_decay_function_id = Column(ForeignKey(u'StockRolloverMethods.id'))
    min_lifetime = Column(Float)
    max_lifetime = Column(Float)
    mean_lifetime = Column(Float)
    lifetime_variance = Column(Float)

    extrapolation_method = relationship(u'CleaningMethod', primaryjoin='DemandCO2CaptureMeasure.extrapolation_method_id == CleaningMethod.id')
    geography = relationship(u'Geography')
    input_type = relationship(u'InputType')
    interpolation_method = relationship(u'CleaningMethod', primaryjoin='DemandCO2CaptureMeasure.interpolation_method_id == CleaningMethod.id')
    other_index_1 = relationship(u'OtherIndex')
    other_index_2 = relationship(u'OtherIndexesDatum')
    stock_decay_function = relationship(u'StockRolloverMethod')
    subsector = relationship(u'DemandSubsector')


class DemandCase(Base):
    __tablename__ = 'DemandCases'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DemandCases_id_seq\"'::regclass)"))
    name = Column(Text)


t_DemandCasesData = Table(
    'DemandCasesData', metadata,
    Column('id', ForeignKey(u'DemandCases.id')),
    Column('subsector_id', ForeignKey(u'DemandSubsectors.id')),
    Column('stock_package_id', ForeignKey(u'DemandStockMeasurePackages.id')),
    Column('service_demand_package_id', ForeignKey(u'DemandSectors.id')),
    Column('energy_efficiency_package_id', ForeignKey(u'DemandEnergyEfficiencyMeasurePackages.id')),
    Column('fuel_switching_package_id', ForeignKey(u'DemandFuelSwitchingMeasurePackages.id')),
    Column('sales_package_id', ForeignKey(u'DemandSalesMeasurePackages.id'))
)


class DemandDriverColumn(Base):
    __tablename__ = 'DemandDriverColumns'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DemandDriverColumns_id_seq\"'::regclass)"))
    datatable_column_name = Column(Text)


# class DemandDriver(Base):
#     __tablename__ = 'DemandDrivers'
#
#     id = Column(Integer, primary_key=True, server_default=text("nextval('\"DemandDrivers_id_seq\"'::regclass)"))
#     name = Column(Text)
#     base_driver_id = Column(ForeignKey(u'DemandDrivers.id'))
#     input_type_id = Column(ForeignKey(u'InputTypes.id'))
#     unit_prefix = Column(Integer)
#     unit_base = Column(Text)
#     geography_id = Column(ForeignKey(u'Geographies.id'))
#     other_index_1_id = Column(ForeignKey(u'OtherIndexes.id'))
#     other_index_2_id = Column(ForeignKey(u'OtherIndexes.id'))
#     geography_map_key_id = Column(ForeignKey(u'GeographyMapKeys.id'))
#     interpolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
#     extrapolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
#     extrapolation_growth = Column(Float)
#
#     base_driver = relationship(u'DemandDriver', remote_side=[id])
#     extrapolation_method = relationship(u'CleaningMethod', primaryjoin='DemandDriver.extrapolation_method_id == CleaningMethod.id')
#     geography = relationship(u'Geography')
#     geography_map_key = relationship(u'GeographyMapKey')
#     input_type = relationship(u'InputType')
#     interpolation_method = relationship(u'CleaningMethod', primaryjoin='DemandDriver.interpolation_method_id == CleaningMethod.id')
#     other_index_1 = relationship(u'OtherIndex', primaryjoin='DemandDriver.other_index_1_id == OtherIndex.id')
#     other_index_2 = relationship(u'OtherIndex', primaryjoin='DemandDriver.other_index_2_id == OtherIndex.id')


t_DemandDriversData = Table(
    'DemandDriversData', metadata,
    Column('id', ForeignKey(u'DemandDrivers.id')),
    Column('gau_id', ForeignKey(u'GeographiesData.id')),
    Column('oth_1_id', ForeignKey(u'OtherIndexesData.id')),
    Column('oth_2_id', ForeignKey(u'OtherIndexesData.id')),
    Column('year', Integer),
    Column('value', Float(53))
)


class DemandEnergyDemand(Base):
    __tablename__ = 'DemandEnergyDemands'

    subsector_id = Column(ForeignKey(u'DemandSubsectors.id'), primary_key=True)
    is_stock_dependent = Column(Boolean, server_default=text("false"))
    input_type_id = Column(ForeignKey(u'InputTypes.id'))
    unit = Column(Text)
    driver_denominator_1_id = Column(ForeignKey(u'DemandDrivers.id'))
    driver_denominator_2_id = Column(ForeignKey(u'DemandDrivers.id'))
    driver_1_id = Column(ForeignKey(u'DemandDrivers.id'))
    driver_2_id = Column(ForeignKey(u'DemandDrivers.id'))
    geography_id = Column(ForeignKey(u'Geographies.id'))
    final_energy_index = Column(Boolean)
    demand_technology_index = Column(Boolean)
    other_index_1_id = Column(ForeignKey(u'OtherIndexes.id'))
    other_index_2_id = Column(ForeignKey(u'OtherIndexes.id'))
    interpolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_growth = Column(Float)
    geography_map_key_id = Column(ForeignKey(u'GeographyMapKeys.id'))

    driver_1 = relationship(u'DemandDriver', primaryjoin='DemandEnergyDemand.driver_1_id == DemandDriver.id')
    driver_2 = relationship(u'DemandDriver', primaryjoin='DemandEnergyDemand.driver_2_id == DemandDriver.id')
    driver_denominator_1 = relationship(u'DemandDriver', primaryjoin='DemandEnergyDemand.driver_denominator_1_id == DemandDriver.id')
    driver_denominator_2 = relationship(u'DemandDriver', primaryjoin='DemandEnergyDemand.driver_denominator_2_id == DemandDriver.id')
    extrapolation_method = relationship(u'CleaningMethod', primaryjoin='DemandEnergyDemand.extrapolation_method_id == CleaningMethod.id')
    geography = relationship(u'Geography')
    geography_map_key = relationship(u'GeographyMapKey')
    input_type = relationship(u'InputType')
    interpolation_method = relationship(u'CleaningMethod', primaryjoin='DemandEnergyDemand.interpolation_method_id == CleaningMethod.id')
    other_index_1 = relationship(u'OtherIndex', primaryjoin='DemandEnergyDemand.other_index_1_id == OtherIndex.id')
    other_index_2 = relationship(u'OtherIndex', primaryjoin='DemandEnergyDemand.other_index_2_id == OtherIndex.id')
    subsector = relationship(u'DemandSubsector', uselist=False)


t_DemandEnergyDemandsData = Table(
    'DemandEnergyDemandsData', metadata,
    Column('demand_energy_demand_id', ForeignKey(u'DemandEnergyDemands.subsector_id')),
    Column('gau_id', ForeignKey(u'GeographiesData.id')),
    Column('oth_1_id', ForeignKey(u'OtherIndexesData.id')),
    Column('oth_2_id', ForeignKey(u'OtherIndexesData.id')),
    Column('final_energy', ForeignKey(u'FinalEnergy.id')),
    Column('technology', Integer),
    Column('year', Integer),
    Column('value', Float)
)


class DemandEnergyEfficiencyMeasurePackage(Base):
    __tablename__ = 'DemandEnergyEfficiencyMeasurePackages'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DemandEnergyEfficiencyMeasurePackages_id_seq\"'::regclass)"))
    name = Column(Text)
    subsector_id = Column(ForeignKey(u'DemandSubsectors.id'))

    subsector = relationship(u'DemandSubsector')


t_DemandEnergyEfficiencyMeasurePackagesData = Table(
    'DemandEnergyEfficiencyMeasurePackagesData', metadata,
    Column('package_id', ForeignKey(u'DemandEnergyEfficiencyMeasurePackages.id')),
    Column('measure_id', ForeignKey(u'DemandEnergyEfficiencyMeasures.id'))
)


class DemandEnergyEfficiencyMeasure(Base):
    __tablename__ = 'DemandEnergyEfficiencyMeasures'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DemandEnergyEfficiencyMeasures_id_seq\"'::regclass)"))
    name = Column(Text)
    subsector_id = Column(ForeignKey(u'DemandSubsectors.id'))
    input_type_id = Column(ForeignKey(u'InputTypes.id'))
    unit = Column(Text)
    geography_id = Column(ForeignKey(u'Geographies.id'))
    other_index_1_id = Column(ForeignKey(u'OtherIndexes.id'))
    other_index_2_id = Column(ForeignKey(u'OtherIndexesData.id'))
    interpolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_growth = Column(Float)
    stock_decay_function_id = Column(ForeignKey(u'StockRolloverMethods.id'))
    min_lifetime = Column(Float)
    max_lifetime = Column(Float)
    mean_lifetime = Column(Float)
    lifetime_variance = Column(Float)

    extrapolation_method = relationship(u'CleaningMethod', primaryjoin='DemandEnergyEfficiencyMeasure.extrapolation_method_id == CleaningMethod.id')
    geography = relationship(u'Geography')
    input_type = relationship(u'InputType')
    interpolation_method = relationship(u'CleaningMethod', primaryjoin='DemandEnergyEfficiencyMeasure.interpolation_method_id == CleaningMethod.id')
    other_index_1 = relationship(u'OtherIndex')
    other_index_2 = relationship(u'OtherIndexesDatum')
    stock_decay_function = relationship(u'StockRolloverMethod')
    subsector = relationship(u'DemandSubsector')
    packages = relationship(u'DemandEnergyEfficiencyMeasurePackage', secondary='DemandEnergyEfficiencyMeasurePackagesData')


t_DemandEnergyEfficiencyMeasuresCost = Table(
    'DemandEnergyEfficiencyMeasuresCost', metadata,
    Column('id', ForeignKey(u'DemandEnergyEfficiencyMeasures.id')),
    Column('currency_id', ForeignKey(u'Currencies.id')),
    Column('currency_year_id', ForeignKey(u'CurrencyYears.id')),
    Column('cost_denominator_unit', Text),
    Column('cost_of_capital', Float),
    Column('is_levelized', Boolean),
    Column('geography_id', ForeignKey(u'Geographies.id')),
    Column('other_index_1_id', ForeignKey(u'OtherIndexes.id')),
    Column('other_index_2_id', ForeignKey(u'OtherIndexes.id')),
    Column('interpolation_method_id', ForeignKey(u'CleaningMethods.id')),
    Column('extrapolation_method_id', ForeignKey(u'CleaningMethods.id')),
    Column('extrapolation_growth', Float)
)


t_DemandEnergyEfficiencyMeasuresCostData = Table(
    'DemandEnergyEfficiencyMeasuresCostData', metadata,
    Column('id', ForeignKey(u'DemandEnergyEfficiencyMeasures.id')),
    Column('gau_id', ForeignKey(u'GeographiesData.id')),
    Column('oth_1_id', ForeignKey(u'OtherIndexesData.id')),
    Column('oth_2_id', ForeignKey(u'OtherIndexesData.id')),
    Column('vintage', Integer),
    Column('value', Float)
)


t_DemandEnergyEfficiencyMeasuresData = Table(
    'DemandEnergyEfficiencyMeasuresData', metadata,
    Column('id', ForeignKey(u'DemandEnergyEfficiencyMeasures.id')),
    Column('final_energy', ForeignKey(u'FinalEnergy.id')),
    Column('gau_id', ForeignKey(u'GeographiesData.id')),
    Column('oth_1_id', ForeignKey(u'OtherIndexesData.id')),
    Column('oth_2_id', ForeignKey(u'OtherIndexesData.id')),
    Column('year', Integer),
    Column('value', Float)
)


class DemandEnergyMeasureType(Base):
    __tablename__ = 'DemandEnergyMeasureTypes'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DemandEnergyMeasureTypes_id_seq\"'::regclass)"))
    name = Column(Text)


t_DemandFlexibleLoadMeasurePackages = Table(
    'DemandFlexibleLoadMeasurePackages', metadata,
    Column('id', Integer),
    Column('name', Text),
    Column('subsector_id', ForeignKey(u'DemandSubsectors.id'))
)


t_DemandFlexibleLoadMeasurePackagesData = Table(
    'DemandFlexibleLoadMeasurePackagesData', metadata,
    Column('measure_id', Integer),
    Column('package_id', Integer)
)


class DemandFlexibleLoadMeasure(Base):
    __tablename__ = 'DemandFlexibleLoadMeasures'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DemandFlexibleLoadMeasures_id_seq\"'::regclass)"))
    subsector_id = Column(ForeignKey(u'DemandSubsectors.id'))
    geography_id = Column(ForeignKey(u'Geographies.id'))
    other_index_1_id = Column(ForeignKey(u'OtherIndexes.id'))
    interpolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_growth = Column(Float)

    extrapolation_method = relationship(u'CleaningMethod', primaryjoin='DemandFlexibleLoadMeasure.extrapolation_method_id == CleaningMethod.id')
    geography = relationship(u'Geography')
    interpolation_method = relationship(u'CleaningMethod', primaryjoin='DemandFlexibleLoadMeasure.interpolation_method_id == CleaningMethod.id')
    other_index_1 = relationship(u'OtherIndex')
    subsector = relationship(u'DemandSubsector')


t_DemandFlexibleLoadMeasuresData = Table(
    'DemandFlexibleLoadMeasuresData', metadata,
    Column('measure_id', Integer),
    Column('gau_id', Integer),
    Column('oth_1_id', Integer),
    Column('year', Integer),
    Column('value', Integer)
)


class DemandFuelSwitchingMeasurePackage(Base):
    __tablename__ = 'DemandFuelSwitchingMeasurePackages'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DemandFuelSwitchingMeasurePackages_id_seq\"'::regclass)"))
    name = Column(Text)
    subsector_id = Column(ForeignKey(u'DemandSubsectors.id'))

    subsector = relationship(u'DemandSubsector')


t_DemandFuelSwitchingMeasurePackagesData = Table(
    'DemandFuelSwitchingMeasurePackagesData', metadata,
    Column('package_id', ForeignKey(u'DemandFuelSwitchingMeasurePackages.id')),
    Column('measure_id', ForeignKey(u'DemandSectors.id'))
)


class DemandFuelSwitchingMeasure(Base):
    __tablename__ = 'DemandFuelSwitchingMeasures'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DemandFuelSwitchingMeasures_id_seq\"'::regclass)"))
    name = Column(Text)
    subsector_id = Column(ForeignKey(u'DemandSubsectors.id'))
    final_energy_from_id = Column(ForeignKey(u'FinalEnergy.id'))
    final_energy_to_id = Column(ForeignKey(u'FinalEnergy.id'))
    stock_decay_function_id = Column(ForeignKey(u'StockRolloverMethods.id'))
    max_lifetime = Column(Float)
    min_lifetime = Column(Float)
    mean_lifetime = Column(Float)
    lifetime_variance = Column(Float)

    final_energy_from = relationship(u'FinalEnergy', primaryjoin='DemandFuelSwitchingMeasure.final_energy_from_id == FinalEnergy.id')
    final_energy_to = relationship(u'FinalEnergy', primaryjoin='DemandFuelSwitchingMeasure.final_energy_to_id == FinalEnergy.id')
    stock_decay_function = relationship(u'StockRolloverMethod')
    subsector = relationship(u'DemandSubsector')


t_DemandFuelSwitchingMeasuresCost = Table(
    'DemandFuelSwitchingMeasuresCost', metadata,
    Column('id', ForeignKey(u'DemandFuelSwitchingMeasures.id')),
    Column('currency_id', ForeignKey(u'Currencies.id')),
    Column('currency_year_id', ForeignKey(u'CurrencyYears.id')),
    Column('cost_denominator_unit', Text),
    Column('cost_of_capital', Float),
    Column('is_levelized', Boolean),
    Column('geography_id', ForeignKey(u'Geographies.id')),
    Column('other_index_1_id', ForeignKey(u'OtherIndexes.id')),
    Column('other_index_2_id', ForeignKey(u'OtherIndexes.id')),
    Column('interpolation_method_id', ForeignKey(u'CleaningMethods.id')),
    Column('extrapolation_method_id', ForeignKey(u'CleaningMethods.id')),
    Column('extrapolation_growth', Float)
)


t_DemandFuelSwitchingMeasuresCostData = Table(
    'DemandFuelSwitchingMeasuresCostData', metadata,
    Column('id', ForeignKey(u'DemandFuelSwitchingMeasures.id')),
    Column('gau_id', ForeignKey(u'GeographiesData.id')),
    Column('oth_1_id', ForeignKey(u'OtherIndexesData.id')),
    Column('oth_2_id', ForeignKey(u'OtherIndexesData.id')),
    Column('vintage', Integer),
    Column('value', Float)
)


class DemandFuelSwitchingMeasuresEnergyIntensity(Base):
    __tablename__ = 'DemandFuelSwitchingMeasuresEnergyIntensity'

    id = Column(ForeignKey(u'DemandFuelSwitchingMeasures.id'), primary_key=True)
    geography_id = Column(ForeignKey(u'Geographies.id'))
    other_index_1_id = Column(ForeignKey(u'OtherIndexes.id'))
    other_index_2_id = Column(ForeignKey(u'OtherIndexesData.id'))
    interpolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_growth = Column(Float)

    extrapolation_method = relationship(u'CleaningMethod', primaryjoin='DemandFuelSwitchingMeasuresEnergyIntensity.extrapolation_method_id == CleaningMethod.id')
    geography = relationship(u'Geography')
    DemandFuelSwitchingMeasure = relationship(u'DemandFuelSwitchingMeasure', uselist=False)
    interpolation_method = relationship(u'CleaningMethod', primaryjoin='DemandFuelSwitchingMeasuresEnergyIntensity.interpolation_method_id == CleaningMethod.id')
    other_index_1 = relationship(u'OtherIndex')
    other_index_2 = relationship(u'OtherIndexesDatum')


t_DemandFuelSwitchingMeasuresEnergyIntensityData = Table(
    'DemandFuelSwitchingMeasuresEnergyIntensityData', metadata,
    Column('id', ForeignKey(u'DemandFuelSwitchingMeasures.id')),
    Column('gau_id', ForeignKey(u'GeographiesData.id')),
    Column('oth_1_id', ForeignKey(u'OtherIndexesData.id')),
    Column('oth_2_id', ForeignKey(u'OtherIndexesData.id')),
    Column('year', Integer),
    Column('value', Float)
)


class DemandFuelSwitchingMeasuresImpact(Base):
    __tablename__ = 'DemandFuelSwitchingMeasuresImpact'

    id = Column(ForeignKey(u'DemandFuelSwitchingMeasures.id'), primary_key=True)
    input_type_id = Column(ForeignKey(u'InputTypes.id'))
    unit = Column(Text)
    geography_id = Column(ForeignKey(u'Geographies.id'))
    other_index_1_id = Column(ForeignKey(u'OtherIndexes.id'))
    other_index_2_id = Column(ForeignKey(u'OtherIndexesData.id'))
    interpolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_growth = Column(Float)

    extrapolation_method = relationship(u'CleaningMethod', primaryjoin='DemandFuelSwitchingMeasuresImpact.extrapolation_method_id == CleaningMethod.id')
    geography = relationship(u'Geography')
    DemandFuelSwitchingMeasure = relationship(u'DemandFuelSwitchingMeasure', uselist=False)
    input_type = relationship(u'InputType')
    interpolation_method = relationship(u'CleaningMethod', primaryjoin='DemandFuelSwitchingMeasuresImpact.interpolation_method_id == CleaningMethod.id')
    other_index_1 = relationship(u'OtherIndex')
    other_index_2 = relationship(u'OtherIndexesDatum')


t_DemandFuelSwitchingMeasuresImpactData = Table(
    'DemandFuelSwitchingMeasuresImpactData', metadata,
    Column('id', ForeignKey(u'DemandFuelSwitchingMeasures.id')),
    Column('gau_id', ForeignKey(u'GeographiesData.id')),
    Column('oth_1_id', ForeignKey(u'OtherIndexesData.id')),
    Column('oth_2_id', ForeignKey(u'OtherIndexesData.id')),
    Column('year', Integer),
    Column('value', Float)
)


class DemandSale(Base):
    __tablename__ = 'DemandSales'

    subsector_id = Column(ForeignKey(u'DemandSubsectors.id'), primary_key=True)
    geography_id = Column(ForeignKey(u'Geographies.id'))
    other_index_1_id = Column(ForeignKey(u'OtherIndexes.id'))
    other_index_2_id = Column(ForeignKey(u'OtherIndexes.id'))
    input_type_id = Column(ForeignKey(u'InputTypes.id'))
    stock_rollover_method_id = Column(ForeignKey(u'StockRolloverMethods.id'))
    interpolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_growth = Column(Float)

    extrapolation_method = relationship(u'CleaningMethod', primaryjoin='DemandSale.extrapolation_method_id == CleaningMethod.id')
    geography = relationship(u'Geography')
    input_type = relationship(u'InputType')
    interpolation_method = relationship(u'CleaningMethod', primaryjoin='DemandSale.interpolation_method_id == CleaningMethod.id')
    other_index_1 = relationship(u'OtherIndex', primaryjoin='DemandSale.other_index_1_id == OtherIndex.id')
    other_index_2 = relationship(u'OtherIndex', primaryjoin='DemandSale.other_index_2_id == OtherIndex.id')
    stock_rollover_method = relationship(u'StockRolloverMethod')
    subsector = relationship(u'DemandSubsector', uselist=False)


t_DemandSalesData = Table(
    'DemandSalesData', metadata,
    Column('subsector_id', ForeignKey(u'DemandSales.subsector_id')),
    Column('gau_id', ForeignKey(u'GeographiesData.id')),
    Column('oth_1_id', ForeignKey(u'OtherIndexesData.id')),
    Column('oth_2_id', ForeignKey(u'OtherIndexesData.id')),
    Column('technology', ForeignKey(u'DemandTechs.id')),
    Column('vintage', Integer),
    Column('value', Float)
)


class DemandSalesMeasurePackage(Base):
    __tablename__ = 'DemandSalesMeasurePackages'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DemandSalesMeasurePackages_id_seq\"'::regclass)"))
    package_name = Column(Text)
    subsector_id = Column(ForeignKey(u'DemandSubsectors.id'))

    subsector = relationship(u'DemandSubsector')


t_DemandSalesMeasurePackagesData = Table(
    'DemandSalesMeasurePackagesData', metadata,
    Column('package_id', ForeignKey(u'DemandSalesMeasurePackages.id')),
    Column('measure_id', ForeignKey(u'DemandSalesMeasures.id'))
)


class DemandSalesMeasure(Base):
    __tablename__ = 'DemandSalesMeasures'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DemandSalesMeasures_id_seq\"'::regclass)"))
    subsector_id = Column(ForeignKey(u'DemandSubsectors.id'))
    geography_id = Column(ForeignKey(u'Geographies.id'))
    other_index_1_id = Column(ForeignKey(u'OtherIndexes.id'))
    demand_tech_id = Column(ForeignKey(u'DemandTechs.id'))
    replaced_demand_tech_id = Column(ForeignKey(u'DemandTechs.id'))
    input_type_id = Column(ForeignKey(u'InputTypes.id'))
    stock_rollover_method_id = Column(ForeignKey(u'StockRolloverMethods.id'))
    interpolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_growth = Column(Float)

    demand_tech = relationship(u'DemandTech', primaryjoin='DemandSalesMeasure.demand_tech_id == DemandTech.id')
    extrapolation_method = relationship(u'CleaningMethod', primaryjoin='DemandSalesMeasure.extrapolation_method_id == CleaningMethod.id')
    geography = relationship(u'Geography')
    input_type = relationship(u'InputType')
    interpolation_method = relationship(u'CleaningMethod', primaryjoin='DemandSalesMeasure.interpolation_method_id == CleaningMethod.id')
    other_index_1 = relationship(u'OtherIndex')
    replaced_demand_tech = relationship(u'DemandTech', primaryjoin='DemandSalesMeasure.replaced_demand_tech_id == DemandTech.id')
    stock_rollover_method = relationship(u'StockRolloverMethod')
    subsector = relationship(u'DemandSubsector')
    packages = relationship(u'DemandSalesMeasurePackage', secondary='DemandSalesMeasurePackagesData')


t_DemandSalesMeasuresData = Table(
    'DemandSalesMeasuresData', metadata,
    Column('id', ForeignKey(u'DemandSalesMeasures.id')),
    Column('gau_id', ForeignKey(u'GeographiesData.id')),
    Column('oth_1_id', ForeignKey(u'OtherIndexesData.id')),
    Column('vintage', Integer),
    Column('value', Float)
)


class DemandSector(Base):
    __tablename__ = 'DemandSectors'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DemandSectors_id_seq\"'::regclass)"))
    name = Column(Text, unique=True)

    packages = relationship(u'DemandFuelSwitchingMeasurePackage', secondary='DemandFuelSwitchingMeasurePackagesData')


class DemandServiceDemandMeasureCost(Base):
    __tablename__ = 'DemandServiceDemandMeasureCost'

    id = Column(ForeignKey(u'DemandServiceDemandMeasures.id'), primary_key=True)
    currency_id = Column(ForeignKey(u'Currencies.id'))
    currency_year_id = Column(ForeignKey(u'CurrencyYears.id'))
    cost_denominator_unit = Column(Text)
    cost_of_capital = Column(Float)
    is_levelized = Column(Boolean)
    geography_id = Column(ForeignKey(u'Geographies.id'))
    other_index_1_id = Column(ForeignKey(u'OtherIndexes.id'))
    other_index_2_id = Column(ForeignKey(u'OtherIndexes.id'))
    interpolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_growth = Column(Float)

    currency = relationship(u'Currency')
    currency_year = relationship(u'CurrencyYear')
    extrapolation_method = relationship(u'CleaningMethod', primaryjoin='DemandServiceDemandMeasureCost.extrapolation_method_id == CleaningMethod.id')
    geography = relationship(u'Geography')
    DemandServiceDemandMeasure = relationship(u'DemandServiceDemandMeasure', uselist=False)
    interpolation_method = relationship(u'CleaningMethod', primaryjoin='DemandServiceDemandMeasureCost.interpolation_method_id == CleaningMethod.id')
    other_index_1 = relationship(u'OtherIndex', primaryjoin='DemandServiceDemandMeasureCost.other_index_1_id == OtherIndex.id')
    other_index_2 = relationship(u'OtherIndex', primaryjoin='DemandServiceDemandMeasureCost.other_index_2_id == OtherIndex.id')


class DemandServiceDemandMeasurePackage(Base):
    __tablename__ = 'DemandServiceDemandMeasurePackages'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DemandServiceDemandMeasurePackages_id_seq\"'::regclass)"))
    name = Column(Text)
    subsector_id = Column(ForeignKey(u'DemandSubsectors.id'))

    subsector = relationship(u'DemandSubsector')


t_DemandServiceDemandMeasurePackagesData = Table(
    'DemandServiceDemandMeasurePackagesData', metadata,
    Column('package_id', ForeignKey(u'DemandServiceDemandMeasurePackages.id')),
    Column('measure_id', ForeignKey(u'DemandServiceDemandMeasures.id'))
)


class DemandServiceDemandMeasure(Base):
    __tablename__ = 'DemandServiceDemandMeasures'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DemandServiceDemandMeasures_id_seq\"'::regclass)"))
    name = Column(Text)
    subsector_id = Column(ForeignKey(u'DemandSubsectors.id'))
    input_type_id = Column(ForeignKey(u'InputTypes.id'))
    unit = Column(Text)
    geography_id = Column(ForeignKey(u'Geographies.id'))
    other_index_1_id = Column(ForeignKey(u'OtherIndexes.id'))
    other_index_2_id = Column(ForeignKey(u'OtherIndexesData.id'))
    interpolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_growth = Column(Float)
    stock_decay_function_id = Column(ForeignKey(u'StockRolloverMethods.id'))
    min_lifetime = Column(Float)
    max_lifetime = Column(Float)
    mean_lifetime = Column(Float)
    lifetime_variance = Column(Float)

    extrapolation_method = relationship(u'CleaningMethod', primaryjoin='DemandServiceDemandMeasure.extrapolation_method_id == CleaningMethod.id')
    geography = relationship(u'Geography')
    input_type = relationship(u'InputType')
    interpolation_method = relationship(u'CleaningMethod', primaryjoin='DemandServiceDemandMeasure.interpolation_method_id == CleaningMethod.id')
    other_index_1 = relationship(u'OtherIndex')
    other_index_2 = relationship(u'OtherIndexesDatum')
    stock_decay_function = relationship(u'StockRolloverMethod')
    subsector = relationship(u'DemandSubsector')
    packages = relationship(u'DemandServiceDemandMeasurePackage', secondary='DemandServiceDemandMeasurePackagesData')


t_DemandServiceDemandMeasuresCostData = Table(
    'DemandServiceDemandMeasuresCostData', metadata,
    Column('id', ForeignKey(u'DemandServiceDemandMeasures.id')),
    Column('gau_id', ForeignKey(u'GeographiesData.id')),
    Column('oth_1_id', ForeignKey(u'OtherIndexesData.id')),
    Column('oth_2_id', ForeignKey(u'OtherIndexesData.id')),
    Column('vintage', Integer),
    Column('value', Float)
)


t_DemandServiceDemandMeasuresData = Table(
    'DemandServiceDemandMeasuresData', metadata,
    Column('id', ForeignKey(u'DemandServiceDemandMeasures.id')),
    Column('gau_id', ForeignKey(u'GeographiesData.id')),
    Column('oth_1_id', ForeignKey(u'OtherIndexesData.id')),
    Column('oth_2_id', ForeignKey(u'OtherIndexesData.id')),
    Column('year', Integer),
    Column('value', Float)
)


class DemandServiceDemandUnitType(Base):
    __tablename__ = 'DemandServiceDemandUnitTypes'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DemandServiceDemandUnitTypes_id_seq\"'::regclass)"))
    name = Column(Text, unique=True)


class DemandServiceDemand(Base):
    __tablename__ = 'DemandServiceDemands'

    subsector_id = Column(ForeignKey(u'DemandSubsectors.id'), primary_key=True)
    is_stock_dependent = Column(Boolean, server_default=text("false"))
    input_type_id = Column(ForeignKey(u'InputTypes.id'))
    unit = Column(Text)
    driver_denominator_1_id = Column(ForeignKey(u'DemandDrivers.id'))
    driver_denominator_2_id = Column(ForeignKey(u'DemandDrivers.id'))
    driver_1_id = Column(ForeignKey(u'DemandDrivers.id'))
    driver_2_id = Column(ForeignKey(u'DemandDrivers.id'))
    geography_id = Column(ForeignKey(u'Geographies.id'))
    final_energy_index = Column(Boolean)
    demand_technology_index = Column(Boolean)
    other_index_1_id = Column(ForeignKey(u'OtherIndexes.id'))
    other_index_2_id = Column(ForeignKey(u'OtherIndexes.id'))
    interpolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_growth = Column(Float)
    geography_map_key_id = Column(ForeignKey(u'GeographyMapKeys.id'))

    driver_1 = relationship(u'DemandDriver', primaryjoin='DemandServiceDemand.driver_1_id == DemandDriver.id')
    driver_2 = relationship(u'DemandDriver', primaryjoin='DemandServiceDemand.driver_2_id == DemandDriver.id')
    driver_denominator_1 = relationship(u'DemandDriver', primaryjoin='DemandServiceDemand.driver_denominator_1_id == DemandDriver.id')
    driver_denominator_2 = relationship(u'DemandDriver', primaryjoin='DemandServiceDemand.driver_denominator_2_id == DemandDriver.id')
    extrapolation_method = relationship(u'CleaningMethod', primaryjoin='DemandServiceDemand.extrapolation_method_id == CleaningMethod.id')
    geography = relationship(u'Geography')
    geography_map_key = relationship(u'GeographyMapKey')
    input_type = relationship(u'InputType')
    interpolation_method = relationship(u'CleaningMethod', primaryjoin='DemandServiceDemand.interpolation_method_id == CleaningMethod.id')
    other_index_1 = relationship(u'OtherIndex', primaryjoin='DemandServiceDemand.other_index_1_id == OtherIndex.id')
    other_index_2 = relationship(u'OtherIndex', primaryjoin='DemandServiceDemand.other_index_2_id == OtherIndex.id')
    subsector = relationship(u'DemandSubsector', uselist=False)


t_DemandServiceDemandsData = Table(
    'DemandServiceDemandsData', metadata,
    Column('demand_service_demand_id', ForeignKey(u'DemandServiceDemands.subsector_id')),
    Column('gau_id', ForeignKey(u'GeographiesData.id')),
    Column('final_energy', ForeignKey(u'FinalEnergy.id')),
    Column('technology', ForeignKey(u'DemandTechs.id')),
    Column('oth_1_id', ForeignKey(u'OtherIndexesData.id')),
    Column('oth_2_id', ForeignKey(u'OtherIndexesData.id')),
    Column('year', Integer),
    Column('value', Float)
)


class DemandServiceEfficiency(Base):
    __tablename__ = 'DemandServiceEfficiency'

    subsector_id = Column(ForeignKey(u'DemandSubsectors.id'), primary_key=True)
    energy_unit = Column(Text)
    denominator_unit = Column(Text)
    geography_id = Column(ForeignKey(u'Geographies.id'))
    other_index_1_id = Column(ForeignKey(u'OtherIndexes.id'))
    other_index_2_id = Column(ForeignKey(u'OtherIndexes.id'))
    interpolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_growth = Column(Float)
    geography_map_key_id = Column(ForeignKey(u'GeographyMapKeys.id'))

    extrapolation_method = relationship(u'CleaningMethod', primaryjoin='DemandServiceEfficiency.extrapolation_method_id == CleaningMethod.id')
    geography = relationship(u'Geography')
    geography_map_key = relationship(u'GeographyMapKey')
    interpolation_method = relationship(u'CleaningMethod', primaryjoin='DemandServiceEfficiency.interpolation_method_id == CleaningMethod.id')
    other_index_1 = relationship(u'OtherIndex', primaryjoin='DemandServiceEfficiency.other_index_1_id == OtherIndex.id')
    other_index_2 = relationship(u'OtherIndex', primaryjoin='DemandServiceEfficiency.other_index_2_id == OtherIndex.id')
    subsector = relationship(u'DemandSubsector', uselist=False)


t_DemandServiceEfficiencyData = Table(
    'DemandServiceEfficiencyData', metadata,
    Column('subsector_id', ForeignKey(u'DemandSubsectors.id')),
    Column('final_energy', ForeignKey(u'FinalEnergy.id')),
    Column('gau_id', ForeignKey(u'GeographiesData.id')),
    Column('oth_1_id', ForeignKey(u'OtherIndexesData.id')),
    Column('oth_2_id', ForeignKey(u'OtherIndexesData.id')),
    Column('year', Integer),
    Column('value', Float)
)


class DemandServiceLink(Base):
    __tablename__ = 'DemandServiceLink'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DemandServiceLink_id_seq\"'::regclass)"))
    subsector_id = Column(ForeignKey(u'DemandSubsectors.id'))
    linked_subsector_id = Column(ForeignKey(u'DemandSubsectors.id'))
    service_demand_share = Column(Float)
    year = Column(Integer)

    linked_subsector = relationship(u'DemandSubsector', primaryjoin='DemandServiceLink.linked_subsector_id == DemandSubsector.id')
    subsector = relationship(u'DemandSubsector', primaryjoin='DemandServiceLink.subsector_id == DemandSubsector.id')


class DemandStock(Base):
    __tablename__ = 'DemandStock'

    subsector_id = Column(ForeignKey(u'DemandSubsectors.id'), primary_key=True)
    is_service_demand_dependent = Column(Boolean, server_default=text("false"))
    driver_denominator_1_id = Column(ForeignKey(u'DemandDrivers.id'))
    driver_denominator_2_id = Column(ForeignKey(u'DemandDrivers.id'))
    driver_1_id = Column(ForeignKey(u'DemandDrivers.id'))
    driver_2_id = Column(ForeignKey(u'DemandDrivers.id'))
    geography_id = Column(ForeignKey(u'Geographies.id'))
    other_index_1_id = Column(ForeignKey(u'OtherIndexes.id'))
    other_index_2_id = Column(ForeignKey(u'OtherIndexes.id'))
    geography_map_key_id = Column(ForeignKey(u'GeographyMapKeys.id'))
    input_type_id = Column(ForeignKey(u'InputTypes.id'))
    demand_stock_unit_type_id = Column(ForeignKey(u'DemandStockUnitTypes.id'))
    unit = Column(Text)
    time_unit = Column(Text)
    interpolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_growth = Column(Float)

    demand_stock_unit_type = relationship(u'DemandStockUnitType')
    driver_1 = relationship(u'DemandDriver', primaryjoin='DemandStock.driver_1_id == DemandDriver.id')
    driver_2 = relationship(u'DemandDriver', primaryjoin='DemandStock.driver_2_id == DemandDriver.id')
    driver_denominator_1 = relationship(u'DemandDriver', primaryjoin='DemandStock.driver_denominator_1_id == DemandDriver.id')
    driver_denominator_2 = relationship(u'DemandDriver', primaryjoin='DemandStock.driver_denominator_2_id == DemandDriver.id')
    extrapolation_method = relationship(u'CleaningMethod', primaryjoin='DemandStock.extrapolation_method_id == CleaningMethod.id')
    geography = relationship(u'Geography')
    geography_map_key = relationship(u'GeographyMapKey')
    input_type = relationship(u'InputType')
    interpolation_method = relationship(u'CleaningMethod', primaryjoin='DemandStock.interpolation_method_id == CleaningMethod.id')
    other_index_1 = relationship(u'OtherIndex', primaryjoin='DemandStock.other_index_1_id == OtherIndex.id')
    other_index_2 = relationship(u'OtherIndex', primaryjoin='DemandStock.other_index_2_id == OtherIndex.id')
    subsector = relationship(u'DemandSubsector', uselist=False)


t_DemandStockData = Table(
    'DemandStockData', metadata,
    Column('subsector_id', ForeignKey(u'DemandStock.subsector_id', ondelete=u'CASCADE')),
    Column('gau_id', ForeignKey(u'GeographiesData.id')),
    Column('oth_1_id', ForeignKey(u'OtherIndexesData.id')),
    Column('oth_2_id', ForeignKey(u'OtherIndexesData.id')),
    Column('technology', ForeignKey(u'DemandTechs.id')),
    Column('year', Integer),
    Column('value', Float)
)


class DemandStockMeasurePackage(Base):
    __tablename__ = 'DemandStockMeasurePackages'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DemandStockMeasurePackages_id_seq\"'::regclass)"))
    name = Column(Text)
    subsector_id = Column(ForeignKey(u'DemandSubsectors.id'))

    subsector = relationship(u'DemandSubsector')
    packages = relationship(u'DemandSalesMeasurePackage', secondary='DemandStockMeasurePackagesData')


t_DemandStockMeasurePackagesData = Table(
    'DemandStockMeasurePackagesData', metadata,
    Column('package_id', ForeignKey(u'DemandSalesMeasurePackages.id')),
    Column('measure_id', ForeignKey(u'DemandStockMeasurePackages.id'))
)


class DemandStockMeasure(Base):
    __tablename__ = 'DemandStockMeasures'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DemandStockMeasures_id_seq\"'::regclass)"))
    subsector_id = Column(ForeignKey(u'DemandSubsectors.id'))
    geography_id = Column(ForeignKey(u'Geographies.id'))
    other_index_1_id = Column(ForeignKey(u'OtherIndexes.id'))
    demand_tech_id = Column(ForeignKey(u'DemandSectors.id'))
    replaced_demand_tech_id = Column(ForeignKey(u'DemandSectors.id'))
    input_type_id = Column(ForeignKey(u'InputTypes.id'))
    stock_rollover_method_id = Column(ForeignKey(u'StockRolloverMethods.id'))
    interpolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_growth = Column(Float)

    demand_tech = relationship(u'DemandSector', primaryjoin='DemandStockMeasure.demand_tech_id == DemandSector.id')
    extrapolation_method = relationship(u'CleaningMethod', primaryjoin='DemandStockMeasure.extrapolation_method_id == CleaningMethod.id')
    geography = relationship(u'Geography')
    input_type = relationship(u'InputType')
    interpolation_method = relationship(u'CleaningMethod', primaryjoin='DemandStockMeasure.interpolation_method_id == CleaningMethod.id')
    other_index_1 = relationship(u'OtherIndex')
    replaced_demand_tech = relationship(u'DemandSector', primaryjoin='DemandStockMeasure.replaced_demand_tech_id == DemandSector.id')
    stock_rollover_method = relationship(u'StockRolloverMethod')
    subsector = relationship(u'DemandSubsector')


t_DemandStockMeasuresData = Table(
    'DemandStockMeasuresData', metadata,
    Column('id', ForeignKey(u'DemandStockMeasures.id')),
    Column('gau_id', ForeignKey(u'GeographiesData.id')),
    Column('oth_1_id', ForeignKey(u'OtherIndexesData.id')),
    Column('vintage', Integer),
    Column('value', Float)
)


class DemandStockUnitType(Base):
    __tablename__ = 'DemandStockUnitTypes'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DemandStockUnitTypes_id_seq\"'::regclass)"))
    name = Column(Text, unique=True)


class DemandSubsector(Base):
    __tablename__ = 'DemandSubsectors'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DemandSubsectors_id_seq\"'::regclass)"))
    sector_id = Column(ForeignKey(u'DemandSectors.id'))
    name = Column(Text)
    cost_of_capital = Column(Float)
    is_active = Column(Boolean, server_default=text("false"))
    shape_id = Column(ForeignKey(u'Shapes.id'))
    max_lead_hours = Column(Integer)
    max_lag_hours = Column(Integer)

    sector = relationship(u'DemandSector')
    shape = relationship(u'Shape')


class DemandTechEfficiencyType(Base):
    __tablename__ = 'DemandTechEfficiencyTypes'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DemandTechEfficiencyTypes_id_seq\"'::regclass)"))
    name = Column(Text)


class DemandTechUnitType(Base):
    __tablename__ = 'DemandTechUnitTypes'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DemandTechUnitTypes_id_seq\"'::regclass)"))
    name = Column(Text)


class DemandTech(Base):
    __tablename__ = 'DemandTechs'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DemandTechs_id_seq\"'::regclass)"))
    linked_id = Column(ForeignKey(u'DemandTechs.id'))
    stock_link_ratio = Column(Float)
    subsector_id = Column(ForeignKey(u'DemandSubsectors.id'))
    name = Column(Text)
    min_lifetime = Column(Float)
    max_lifetime = Column(Float)
    source = Column(Text)
    additional_description = Column(Text)
    demand_tech_unit_type_id = Column(ForeignKey(u'DemandTechUnitTypes.id'))
    unit = Column(Text)
    time_unit = Column(Text)
    cost_of_capital = Column(Float)
    stock_decay_function_id = Column(ForeignKey(u'StockDecayFunctions.id'))
    mean_lifetime = Column(Float)
    lifetime_variance = Column(Float)
    shape_id = Column(ForeignKey(u'Shapes.id'))
    max_lead_hours = Column(Integer)
    max_lag_hours = Column(Integer)

    demand_tech_unit_type = relationship(u'DemandTechUnitType')
    linked = relationship(u'DemandTech', remote_side=[id])
    shape = relationship(u'Shape')
    stock_decay_function = relationship(u'StockDecayFunction')
    subsector = relationship(u'DemandSubsector')


class DemandTechsAuxEfficiency(Base):
    __tablename__ = 'DemandTechsAuxEfficiency'

    demand_tech_id = Column(ForeignKey(u'DemandTechs.id'), primary_key=True)
    definition_id = Column(ForeignKey(u'Definitions.id'))
    reference_tech_id = Column(Integer)
    geography_id = Column(ForeignKey(u'Geographies.id'))
    other_index_1_id = Column(ForeignKey(u'OtherIndexes.id'))
    other_index_2_id = Column(ForeignKey(u'OtherIndexes.id'))
    final_energy_id = Column(ForeignKey(u'FinalEnergy.id'))
    demand_tech_efficiency_types_id = Column(ForeignKey(u'DemandTechEfficiencyTypes.id'))
    is_numerator_service = Column(Boolean)
    numerator_unit = Column(Text)
    denominator_unit = Column(Text)
    interpolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_growth = Column(Float)
    age_growth_or_decay_type_id = Column(ForeignKey(u'AgeGrowthOrDecayType.id'))
    age_growth_or_decay = Column(Float)
    shape_id = Column(Integer)

    age_growth_or_decay_type = relationship(u'AgeGrowthOrDecayType')
    definition = relationship(u'Definition')
    demand_tech_efficiency_types = relationship(u'DemandTechEfficiencyType')
    demand_tech = relationship(u'DemandTech', uselist=False)
    extrapolation_method = relationship(u'CleaningMethod', primaryjoin='DemandTechsAuxEfficiency.extrapolation_method_id == CleaningMethod.id')
    final_energy = relationship(u'FinalEnergy')
    geography = relationship(u'Geography')
    interpolation_method = relationship(u'CleaningMethod', primaryjoin='DemandTechsAuxEfficiency.interpolation_method_id == CleaningMethod.id')
    other_index_1 = relationship(u'OtherIndex', primaryjoin='DemandTechsAuxEfficiency.other_index_1_id == OtherIndex.id')
    other_index_2 = relationship(u'OtherIndex', primaryjoin='DemandTechsAuxEfficiency.other_index_2_id == OtherIndex.id')


t_DemandTechsAuxEfficiencyData = Table(
    'DemandTechsAuxEfficiencyData', metadata,
    Column('demand_tech_id', ForeignKey(u'DemandTechs.id')),
    Column('gau_id', ForeignKey(u'GeographiesData.id')),
    Column('oth_1_id', ForeignKey(u'OtherIndexesData.id')),
    Column('oth_2_id', ForeignKey(u'OtherIndexesData.id')),
    Column('vintage', Integer),
    Column('value', Float)
)


class DemandTechsCapitalCost(Base):
    __tablename__ = 'DemandTechsCapitalCost'

    demand_tech_id = Column(ForeignKey(u'DemandTechs.id'), primary_key=True)
    definition_id = Column(ForeignKey(u'Definitions.id'))
    reference_tech_id = Column(ForeignKey(u'DemandTechsCapitalCost.demand_tech_id'))
    geography_id = Column(ForeignKey(u'Geographies.id'))
    other_index_1_id = Column(ForeignKey(u'OtherIndexes.id'))
    other_index_2_id = Column(ForeignKey(u'OtherIndexes.id'))
    currency_id = Column(ForeignKey(u'Currencies.id'))
    currency_year_id = Column(Integer)
    is_levelized = Column(Boolean, server_default=text("false"))
    interpolation_method_id = Column(ForeignKey(u'CleaningMethods.id'), server_default=text("1"))
    extrapolation_method_id = Column(ForeignKey(u'CleaningMethods.id'), server_default=text("4"))
    extrapolation_growth = Column(Float)

    currency = relationship(u'Currency')
    definition = relationship(u'Definition')
    demand_tech = relationship(u'DemandTech', uselist=False)
    extrapolation_method = relationship(u'CleaningMethod', primaryjoin='DemandTechsCapitalCost.extrapolation_method_id == CleaningMethod.id')
    geography = relationship(u'Geography')
    interpolation_method = relationship(u'CleaningMethod', primaryjoin='DemandTechsCapitalCost.interpolation_method_id == CleaningMethod.id')
    other_index_1 = relationship(u'OtherIndex', primaryjoin='DemandTechsCapitalCost.other_index_1_id == OtherIndex.id')
    other_index_2 = relationship(u'OtherIndex', primaryjoin='DemandTechsCapitalCost.other_index_2_id == OtherIndex.id')
    reference_tech = relationship(u'DemandTechsCapitalCost', remote_side=[demand_tech_id])


t_DemandTechsCapitalCostNewData = Table(
    'DemandTechsCapitalCostNewData', metadata,
    Column('demand_tech_id', ForeignKey(u'DemandTechs.id')),
    Column('gau_id', ForeignKey(u'GeographiesData.id')),
    Column('oth_1_id', ForeignKey(u'OtherIndexesData.id')),
    Column('oth_2_id', ForeignKey(u'OtherIndexesData.id')),
    Column('vintage', Integer),
    Column('value', Float)
)


t_DemandTechsCapitalCostReplacementData = Table(
    'DemandTechsCapitalCostReplacementData', metadata,
    Column('demand_tech_id', ForeignKey(u'DemandTechs.id')),
    Column('gau_id', ForeignKey(u'GeographiesData.id')),
    Column('oth_1_id', ForeignKey(u'OtherIndexesData.id')),
    Column('oth_2_id', ForeignKey(u'OtherIndexesData.id')),
    Column('vintage', Integer),
    Column('value', Float)
)


class DemandTechsFixedMaintenanceCost(Base):
    __tablename__ = 'DemandTechsFixedMaintenanceCost'

    demand_tech_id = Column(ForeignKey(u'DemandTechs.id'), primary_key=True)
    definition_id = Column(ForeignKey(u'Definitions.id'))
    reference_tech_id = Column(ForeignKey(u'DemandTechsFixedMaintenanceCost.demand_tech_id'))
    geography_id = Column(ForeignKey(u'Geographies.id'))
    other_index_1_id = Column(ForeignKey(u'OtherIndexes.id'))
    other_index_2_id = Column(ForeignKey(u'OtherIndexes.id'))
    currency_id = Column(ForeignKey(u'Currencies.id'))
    currency_year_id = Column(ForeignKey(u'CurrencyYears.id'))
    interpolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_growth = Column(Float)
    age_growth_or_decay_type_id = Column(ForeignKey(u'AgeGrowthOrDecayType.id'))
    age_growth_or_decay = Column(Float)
    additional_description = Column(Text)

    age_growth_or_decay_type = relationship(u'AgeGrowthOrDecayType')
    currency = relationship(u'Currency')
    currency_year = relationship(u'CurrencyYear')
    definition = relationship(u'Definition')
    demand_tech = relationship(u'DemandTech', uselist=False)
    extrapolation_method = relationship(u'CleaningMethod', primaryjoin='DemandTechsFixedMaintenanceCost.extrapolation_method_id == CleaningMethod.id')
    geography = relationship(u'Geography')
    interpolation_method = relationship(u'CleaningMethod', primaryjoin='DemandTechsFixedMaintenanceCost.interpolation_method_id == CleaningMethod.id')
    other_index_1 = relationship(u'OtherIndex', primaryjoin='DemandTechsFixedMaintenanceCost.other_index_1_id == OtherIndex.id')
    other_index_2 = relationship(u'OtherIndex', primaryjoin='DemandTechsFixedMaintenanceCost.other_index_2_id == OtherIndex.id')
    reference_tech = relationship(u'DemandTechsFixedMaintenanceCost', remote_side=[demand_tech_id])


t_DemandTechsFixedMaintenanceCostData = Table(
    'DemandTechsFixedMaintenanceCostData', metadata,
    Column('demand_tech_id', ForeignKey(u'DemandTechs.id')),
    Column('gau_id', ForeignKey(u'GeographiesData.id')),
    Column('oth_1_id', ForeignKey(u'OtherIndexesData.id')),
    Column('oth_2_id', ForeignKey(u'OtherIndexesData.id')),
    Column('vintage', Integer),
    Column('value', Float)
)


class DemandTechsFuelSwitchCost(Base):
    __tablename__ = 'DemandTechsFuelSwitchCost'

    demand_tech_id = Column(ForeignKey(u'DemandTechs.id'), primary_key=True)
    definition_id = Column(ForeignKey(u'Definitions.id'))
    reference_tech_id = Column(ForeignKey(u'DemandTechsFuelSwitchCost.demand_tech_id'))
    geography_id = Column(ForeignKey(u'Geographies.id'))
    other_index_1_id = Column(ForeignKey(u'OtherIndexes.id'))
    other_index_2_id = Column(ForeignKey(u'OtherIndexes.id'))
    currency_id = Column(ForeignKey(u'Currencies.id'))
    currency_year_id = Column(ForeignKey(u'CurrencyYears.id'))
    is_levelized = Column(Boolean, server_default=text("false"))
    interpolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_growth = Column(Float)

    currency = relationship(u'Currency')
    currency_year = relationship(u'CurrencyYear')
    definition = relationship(u'Definition')
    demand_tech = relationship(u'DemandTech', uselist=False)
    extrapolation_method = relationship(u'CleaningMethod', primaryjoin='DemandTechsFuelSwitchCost.extrapolation_method_id == CleaningMethod.id')
    geography = relationship(u'Geography')
    interpolation_method = relationship(u'CleaningMethod', primaryjoin='DemandTechsFuelSwitchCost.interpolation_method_id == CleaningMethod.id')
    other_index_1 = relationship(u'OtherIndex', primaryjoin='DemandTechsFuelSwitchCost.other_index_1_id == OtherIndex.id')
    other_index_2 = relationship(u'OtherIndex', primaryjoin='DemandTechsFuelSwitchCost.other_index_2_id == OtherIndex.id')
    reference_tech = relationship(u'DemandTechsFuelSwitchCost', remote_side=[demand_tech_id])


t_DemandTechsFuelSwitchCostData = Table(
    'DemandTechsFuelSwitchCostData', metadata,
    Column('demand_tech_id', ForeignKey(u'DemandTechs.id')),
    Column('gau_id', ForeignKey(u'GeographiesData.id')),
    Column('oth_1_id', ForeignKey(u'OtherIndexesData.id')),
    Column('oth_2_id', ForeignKey(u'OtherIndexesData.id')),
    Column('vintage', Integer),
    Column('value', Float)
)


class DemandTechsInstallationCost(Base):
    __tablename__ = 'DemandTechsInstallationCost'

    demand_tech_id = Column(ForeignKey(u'DemandTechs.id'), primary_key=True)
    definition_id = Column(ForeignKey(u'Definitions.id'))
    reference_tech_id = Column(Integer)
    geography_id = Column(ForeignKey(u'Geographies.id'))
    other_index_1_id = Column(ForeignKey(u'OtherIndexes.id'))
    other_index_2_id = Column(ForeignKey(u'OtherIndexes.id'))
    currency_id = Column(ForeignKey(u'Currencies.id'))
    currency_year_id = Column(ForeignKey(u'CurrencyYears.id'))
    is_levelized = Column(Boolean, server_default=text("false"))
    interpolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_growth = Column(Float)

    currency = relationship(u'Currency')
    currency_year = relationship(u'CurrencyYear')
    definition = relationship(u'Definition')
    demand_tech = relationship(u'DemandTech', uselist=False)
    extrapolation_method = relationship(u'CleaningMethod', primaryjoin='DemandTechsInstallationCost.extrapolation_method_id == CleaningMethod.id')
    geography = relationship(u'Geography')
    interpolation_method = relationship(u'CleaningMethod', primaryjoin='DemandTechsInstallationCost.interpolation_method_id == CleaningMethod.id')
    other_index_1 = relationship(u'OtherIndex', primaryjoin='DemandTechsInstallationCost.other_index_1_id == OtherIndex.id')
    other_index_2 = relationship(u'OtherIndex', primaryjoin='DemandTechsInstallationCost.other_index_2_id == OtherIndex.id')


t_DemandTechsInstallationCostNewData = Table(
    'DemandTechsInstallationCostNewData', metadata,
    Column('demand_tech_id', ForeignKey(u'DemandTechs.id')),
    Column('gau_id', ForeignKey(u'GeographiesData.id')),
    Column('oth_1_id', ForeignKey(u'OtherIndexesData.id')),
    Column('oth_2_id', ForeignKey(u'OtherIndexesData.id')),
    Column('vintage', Integer),
    Column('value', Float)
)


t_DemandTechsInstallationCostReplacementData = Table(
    'DemandTechsInstallationCostReplacementData', metadata,
    Column('demand_tech_id', ForeignKey(u'DemandTechs.id')),
    Column('gau_id', ForeignKey(u'GeographiesData.id')),
    Column('oth_1_id', ForeignKey(u'OtherIndexesData.id')),
    Column('oth_2_id', ForeignKey(u'OtherIndexesData.id')),
    Column('vintage', Integer),
    Column('value', Float)
)


class DemandTechsMainEfficiency(Base):
    __tablename__ = 'DemandTechsMainEfficiency'

    demand_tech_id = Column(ForeignKey(u'DemandTechs.id'), primary_key=True)
    definition_id = Column(ForeignKey(u'Definitions.id'))
    reference_tech_id = Column(ForeignKey(u'DemandTechsMainEfficiency.demand_tech_id'))
    geography_id = Column(ForeignKey(u'Geographies.id'))
    other_index_1_id = Column(ForeignKey(u'OtherIndexes.id'))
    other_index_2_id = Column(ForeignKey(u'OtherIndexes.id'))
    final_energy_id = Column(ForeignKey(u'FinalEnergy.id'))
    utility_factor = Column(Float)
    demand_tech_efficiency_types = Column(ForeignKey(u'DemandTechEfficiencyTypes.id'))
    is_numerator_service = Column(Boolean)
    numerator_unit = Column(Text)
    denominator_unit = Column(Text)
    interpolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_growth = Column(Float)
    age_growth_or_decay_type_id = Column(ForeignKey(u'AgeGrowthOrDecayType.id'))
    age_growth_or_decay = Column(Float)
    shape_id = Column(Integer)

    age_growth_or_decay_type = relationship(u'AgeGrowthOrDecayType')
    definition = relationship(u'Definition')
    DemandTechEfficiencyType = relationship(u'DemandTechEfficiencyType')
    demand_tech = relationship(u'DemandTech', uselist=False)
    extrapolation_method = relationship(u'CleaningMethod', primaryjoin='DemandTechsMainEfficiency.extrapolation_method_id == CleaningMethod.id')
    final_energy = relationship(u'FinalEnergy')
    geography = relationship(u'Geography')
    interpolation_method = relationship(u'CleaningMethod', primaryjoin='DemandTechsMainEfficiency.interpolation_method_id == CleaningMethod.id')
    other_index_1 = relationship(u'OtherIndex', primaryjoin='DemandTechsMainEfficiency.other_index_1_id == OtherIndex.id')
    other_index_2 = relationship(u'OtherIndex', primaryjoin='DemandTechsMainEfficiency.other_index_2_id == OtherIndex.id')
    reference_tech = relationship(u'DemandTechsMainEfficiency', remote_side=[demand_tech_id])


t_DemandTechsMainEfficiencyData = Table(
    'DemandTechsMainEfficiencyData', metadata,
    Column('demand_tech_id', ForeignKey(u'DemandTechs.id')),
    Column('gau_id', ForeignKey(u'GeographiesData.id')),
    Column('oth_1_id', ForeignKey(u'OtherIndexesData.id')),
    Column('oth_2_id', ForeignKey(u'OtherIndexesData.id')),
    Column('vintage', Integer),
    Column('value', Float)
)


class DemandTechsParasiticEnergy(Base):
    __tablename__ = 'DemandTechsParasiticEnergy'

    demand_tech_id = Column(ForeignKey(u'DemandTechs.id'), primary_key=True)
    definition_id = Column(ForeignKey(u'Definitions.id'))
    reference_tech_id = Column(Integer)
    geography_id = Column(ForeignKey(u'Geographies.id'))
    other_index_1_id = Column(ForeignKey(u'OtherIndexes.id'))
    other_index_2_id = Column(ForeignKey(u'OtherIndexes.id'))
    energy_unit = Column(Text)
    time_unit = Column(Text)
    interpolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_growth = Column(Float)
    age_growth_or_decay_type_id = Column(ForeignKey(u'AgeGrowthOrDecayType.id'))
    age_growth_or_decay = Column(Float)

    age_growth_or_decay_type = relationship(u'AgeGrowthOrDecayType')
    definition = relationship(u'Definition')
    demand_tech = relationship(u'DemandTech', uselist=False)
    extrapolation_method = relationship(u'CleaningMethod', primaryjoin='DemandTechsParasiticEnergy.extrapolation_method_id == CleaningMethod.id')
    geography = relationship(u'Geography')
    interpolation_method = relationship(u'CleaningMethod', primaryjoin='DemandTechsParasiticEnergy.interpolation_method_id == CleaningMethod.id')
    other_index_1 = relationship(u'OtherIndex', primaryjoin='DemandTechsParasiticEnergy.other_index_1_id == OtherIndex.id')
    other_index_2 = relationship(u'OtherIndex', primaryjoin='DemandTechsParasiticEnergy.other_index_2_id == OtherIndex.id')


t_DemandTechsParasiticEnergyData = Table(
    'DemandTechsParasiticEnergyData', metadata,
    Column('demand_tech_id', ForeignKey(u'DemandTechs.id')),
    Column('gau_id', ForeignKey(u'GeographiesData.id')),
    Column('oth_1_id', ForeignKey(u'OtherIndexesData.id')),
    Column('oth_2_id', ForeignKey(u'OtherIndexesData.id')),
    Column('final_energy', ForeignKey(u'FinalEnergy.id')),
    Column('vintage', Integer),
    Column('value', Float)
)


class DemandTechsServiceDemandModifier(Base):
    __tablename__ = 'DemandTechsServiceDemandModifier'

    demand_tech_id = Column(ForeignKey(u'DemandTechs.id'), primary_key=True)
    geography_id = Column(ForeignKey(u'Geographies.id'))
    other_index_1_id = Column(ForeignKey(u'OtherIndexes.id'))
    other_index_2_id = Column(ForeignKey(u'OtherIndexes.id'))
    interpolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_growth = Column(Float)
    age_growth_or_decay_type_id = Column(ForeignKey(u'AgeGrowthOrDecayType.id'))
    age_growth_or_decay = Column(Float)

    age_growth_or_decay_type = relationship(u'AgeGrowthOrDecayType')
    demand_tech = relationship(u'DemandTech', uselist=False)
    extrapolation_method = relationship(u'CleaningMethod', primaryjoin='DemandTechsServiceDemandModifier.extrapolation_method_id == CleaningMethod.id')
    geography = relationship(u'Geography')
    interpolation_method = relationship(u'CleaningMethod', primaryjoin='DemandTechsServiceDemandModifier.interpolation_method_id == CleaningMethod.id')
    other_index_1 = relationship(u'OtherIndex', primaryjoin='DemandTechsServiceDemandModifier.other_index_1_id == OtherIndex.id')
    other_index_2 = relationship(u'OtherIndex', primaryjoin='DemandTechsServiceDemandModifier.other_index_2_id == OtherIndex.id')


t_DemandTechsServiceDemandModifierData = Table(
    'DemandTechsServiceDemandModifierData', metadata,
    Column('demand_tech_id', ForeignKey(u'DemandTechs.id')),
    Column('gau_id', ForeignKey(u'GeographiesData.id')),
    Column('oth_1_id', ForeignKey(u'OtherIndexesData.id')),
    Column('oth_2_id', ForeignKey(u'OtherIndexesData.id')),
    Column('vintage', Integer),
    Column('value', Float)
)


class DemandTechsServiceLink(Base):
    __tablename__ = 'DemandTechsServiceLink'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DemandTechsServiceLink_id_seq\"'::regclass)"))
    service_link_id = Column(ForeignKey(u'DemandServiceLink.id'))
    demand_tech_id = Column(ForeignKey(u'DemandTechs.id'))
    definition_id = Column(ForeignKey(u'Definitions.id'))
    reference_id = Column(Integer)
    geography_id = Column(ForeignKey(u'Geographies.id'))
    other_index_1_id = Column(ForeignKey(u'OtherIndexes.id'))
    other_index_2_id = Column(ForeignKey(u'OtherIndexes.id'))
    interpolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_growth = Column(Float)
    age_growth_or_decay_type_id = Column(ForeignKey(u'AgeGrowthOrDecayType.id'))
    age_growth_or_decay = Column(Float)

    age_growth_or_decay_type = relationship(u'AgeGrowthOrDecayType')
    definition = relationship(u'Definition')
    demand_tech = relationship(u'DemandTech')
    extrapolation_method = relationship(u'CleaningMethod', primaryjoin='DemandTechsServiceLink.extrapolation_method_id == CleaningMethod.id')
    geography = relationship(u'Geography')
    interpolation_method = relationship(u'CleaningMethod', primaryjoin='DemandTechsServiceLink.interpolation_method_id == CleaningMethod.id')
    other_index_1 = relationship(u'OtherIndex', primaryjoin='DemandTechsServiceLink.other_index_1_id == OtherIndex.id')
    other_index_2 = relationship(u'OtherIndex', primaryjoin='DemandTechsServiceLink.other_index_2_id == OtherIndex.id')
    service_link = relationship(u'DemandServiceLink')


t_DemandTechsServiceLinkData = Table(
    'DemandTechsServiceLinkData', metadata,
    Column('id', ForeignKey(u'DemandTechsServiceLink.id')),
    Column('gau_id', ForeignKey(u'GeographiesData.id')),
    Column('oth_1_id', ForeignKey(u'OtherIndexesData.id')),
    Column('oth_2_id', ForeignKey(u'OtherIndexesData.id')),
    Column('vintage', Integer),
    Column('value', Float)
)


class DemandUnitDenominator(Base):
    __tablename__ = 'DemandUnitDenominators'

    denominator_id = Column(Integer, primary_key=True, server_default=text("nextval('\"DemandUnitDenominators_denominator_id_seq\"'::regclass)"))
    datatable_column_name = Column(Text)


t_DispatchConfig = Table(
    'DispatchConfig', metadata,
    Column('id', Integer),
    Column('geography_id', ForeignKey(u'Geographies.id')),
    Column('opt_hours', Integer),
    Column('flex_load_constraints_offset', Integer),
    Column('large_storage_duration', Integer),
    Column('thermal_dispatch_node_id', ForeignKey(u'SupplyNodes.id')),
    Column('distribution_node_id', ForeignKey(u'SupplyNodes.id')),
    Column('transmission_node_id', ForeignKey(u'SupplyNodes.id'))
)


class DispatchFeeder(Base):
    __tablename__ = 'DispatchFeeders'

    id = Column(Integer)
    feeder_id = Column(Integer, primary_key=True, server_default=text("nextval('\"DispatchFeeders_feeder_id_seq\"'::regclass)"))
    name = Column(Text, unique=True)


t_DispatchFeedersData = Table(
    'DispatchFeedersData', metadata,
    Column('id', Integer),
    Column('dispatch_feeder', ForeignKey(u'DispatchFeeders.feeder_id')),
    Column('demand_sector', ForeignKey(u'DemandSectors.id')),
    Column('year', Integer),
    Column('value', Float)
)


class DispatchNodeConfig(Base):
    __tablename__ = 'DispatchNodeConfig'

    supply_node_id = Column(ForeignKey(u'SupplyNodes.id'), primary_key=True)
    dispatch_order = Column(Integer, unique=True)
    dispatch_window_id = Column(ForeignKey(u'DispatchWindows.id'))
    geography_id = Column(ForeignKey(u'Geographies.id'))

    dispatch_window = relationship(u'DispatchWindow')
    geography = relationship(u'Geography')
    supply_node = relationship(u'SupplyNode', uselist=False)


t_DispatchNodeData = Table(
    'DispatchNodeData', metadata,
    Column('supply_node_id', ForeignKey(u'DispatchNodeConfig.supply_node_id')),
    Column('gau_id', ForeignKey(u'GeographiesData.id')),
    Column('week', Integer),
    Column('day', Integer),
    Column('month', Integer),
    Column('p_max', Float(53)),
    Column('p_min', Float(53)),
    Column('energy_budget', Float(53))
)


class DispatchWindow(Base):
    __tablename__ = 'DispatchWindows'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DispatchWindows_id_seq\"'::regclass)"))
    name = Column(Text, unique=True)


class EfficiencyType(Base):
    __tablename__ = 'EfficiencyTypes'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"EfficiencyTypes_id_seq\"'::regclass)"))
    name = Column(Text)


t_EnergySystemScenarioData = Table(
    'EnergySystemScenarioData', metadata,
    Column('id', ForeignKey(u'EnergySystemScenarios.id')),
    Column('demand_case_id', ForeignKey(u'DemandCases.id')),
    Column('supply_case_id', ForeignKey(u'SupplyCases.id'))
)


class EnergySystemScenario(Base):
    __tablename__ = 'EnergySystemScenarios'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"EnergySystemScenarios_id_seq\"'::regclass)"))
    name = Column(Text)


class FinalEnergy(Base):
    __tablename__ = 'FinalEnergy'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"FinalEnergy_id_seq\"'::regclass)"))
    name = Column(Text)
    shape_id = Column(ForeignKey(u'Shapes.id'))

    shape = relationship(u'Shape')


class FlexibleLoadMeasure(Base):
    __tablename__ = 'FlexibleLoadMeasures'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"FlexibleLoadMeasures_id_seq\"'::regclass)"))
    subsector_id = Column(ForeignKey(u'DemandSubsectors.id'))

    subsector = relationship(u'DemandSubsector')


class Geography(Base):
    __tablename__ = 'Geographies'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"Geographies_id_seq\"'::regclass)"))
    name = Column(Text, unique=True)


class GeographiesDatum(Base):
    __tablename__ = 'GeographiesData'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"GeographiesData_id_seq\"'::regclass)"))
    name = Column(Text)
    geography_id = Column(ForeignKey(u'Geographies.id'))

    geography = relationship(u'Geography')
    intersections = relationship(u'GeographyIntersection', secondary='GeographyIntersectionData')


class GeographyIntersection(Base):
    __tablename__ = 'GeographyIntersection'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"GeographyIntersection_id_seq\"'::regclass)"))


t_GeographyIntersectionData = Table(
    'GeographyIntersectionData', metadata,
    Column('intersection_id', ForeignKey(u'GeographyIntersection.id')),
    Column('gau_id', ForeignKey(u'GeographiesData.id')),
    UniqueConstraint('intersection_id', 'gau_id')
)


t_GeographyMap = Table(
    'GeographyMap', metadata,
    Column('intersection_id', ForeignKey(u'GeographyIntersection.id')),
    Column('geography_map_key_id', ForeignKey(u'GeographyMapKeys.id')),
    Column('value', Float(53)),
    UniqueConstraint('intersection_id', 'geography_map_key_id')
)


class GeographyMapKey(Base):
    __tablename__ = 'GeographyMapKeys'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"GeographyMapKeys_id_seq\"'::regclass)"))
    name = Column(Text, unique=True)


class GreenhouseGasEmissionsType(Base):
    __tablename__ = 'GreenhouseGasEmissionsType'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"GreenhouseGasEmissionsType_id_seq\"'::regclass)"))
    name = Column(Text, unique=True)


class GreenhouseGase(Base):
    __tablename__ = 'GreenhouseGases'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"GreenhouseGases_id_seq\"'::regclass)"))
    name = Column(Text)
    long_name = Column(Text)


class IDMap(Base):
    __tablename__ = 'IDMap'

    identifier_id = Column(Text, primary_key=True)
    ref_table = Column(Text)


class ImportCost(Base):
    __tablename__ = 'ImportCost'

    import_node_id = Column(ForeignKey(u'SupplyNodes.id'), primary_key=True)
    source = Column(Text)
    notes = Column(Text)
    geography_id = Column(ForeignKey(u'Geographies.id'))
    currency_id = Column(ForeignKey(u'Currencies.id'))
    currency_year_id = Column(ForeignKey(u'CurrencyYears.id'))
    denominator_unit = Column(Text)
    interpolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_growth = Column(Float)

    currency = relationship(u'Currency')
    currency_year = relationship(u'CurrencyYear')
    extrapolation_method = relationship(u'CleaningMethod', primaryjoin='ImportCost.extrapolation_method_id == CleaningMethod.id')
    geography = relationship(u'Geography')
    import_node = relationship(u'SupplyNode', uselist=False)
    interpolation_method = relationship(u'CleaningMethod', primaryjoin='ImportCost.interpolation_method_id == CleaningMethod.id')


t_ImportCostData = Table(
    'ImportCostData', metadata,
    Column('import_node_id', ForeignKey(u'ImportCost.import_node_id')),
    Column('gau_id', ForeignKey(u'GeographiesData.id')),
    Column('demand_sector_id', ForeignKey(u'DemandSectors.id')),
    Column('year', Integer),
    Column('value', Float(53))
)


class ImportEmission(Base):
    __tablename__ = 'ImportEmissions'

    import_node_id = Column(ForeignKey(u'SupplyNodes.id'), primary_key=True)
    source = Column(Text)
    notes = Column(Text)
    geography_id = Column(ForeignKey(u'Geographies.id'))
    other_index_1_id = Column(ForeignKey(u'OtherIndexes.id'))
    mass_unit = Column(Text)
    energy_unit = Column(Text)
    is_incremental = Column(Boolean)
    interpolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_growth = Column(Float)

    extrapolation_method = relationship(u'CleaningMethod', primaryjoin='ImportEmission.extrapolation_method_id == CleaningMethod.id')
    geography = relationship(u'Geography')
    import_node = relationship(u'SupplyNode', uselist=False)
    interpolation_method = relationship(u'CleaningMethod', primaryjoin='ImportEmission.interpolation_method_id == CleaningMethod.id')
    other_index_1 = relationship(u'OtherIndex')


t_ImportEmissionsData = Table(
    'ImportEmissionsData', metadata,
    Column('import_node_id', ForeignKey(u'SupplyNodes.id')),
    Column('gau_id', ForeignKey(u'GeographiesData.id')),
    Column('demand_sector_id', ForeignKey(u'DemandSectors.id')),
    Column('oth_1_id', ForeignKey(u'OtherIndexesData.id')),
    Column('ghg_type_id', ForeignKey(u'GreenhouseGasEmissionsType.id')),
    Column('ghg_id', ForeignKey(u'GreenhouseGases.id')),
    Column('year', Integer),
    Column('value', Float(53))
)


class IndexLevel(Base):
    __tablename__ = 'IndexLevels'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"IndexLevels_id_seq\"'::regclass)"))
    index_level = Column(Text)
    data_column_name = Column(Text)


t_InflationConversion = Table(
    'InflationConversion', metadata,
    Column('currency_year_id', ForeignKey(u'CurrencyYears.id')),
    Column('currency_id', ForeignKey(u'Currencies.id')),
    Column('value', Float(53))
)


class InputType(Base):
    __tablename__ = 'InputTypes'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"InputTypes_id_seq\"'::regclass)"))
    name = Column(Text, unique=True)


class Month(Base):
    __tablename__ = 'Month'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"Month_id_seq\"'::regclass)"))
    name = Column(Text, unique=True)


class OptPeriod(Base):
    __tablename__ = 'OptPeriods'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"OptPeriods_id_seq\"'::regclass)"))
    hours = Column(Integer, unique=True)


class OtherIndex(Base):
    __tablename__ = 'OtherIndexes'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"OtherIndexes_id_seq\"'::regclass)"))
    name = Column(Text)


class OtherIndexesDatum(Base):
    __tablename__ = 'OtherIndexesData'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"OtherIndexesData_id_seq\"'::regclass)"))
    name = Column(Text)
    other_index_id = Column(ForeignKey(u'OtherIndexes.id'))

    other_index = relationship(u'OtherIndex')


class PrimaryCost(Base):
    __tablename__ = 'PrimaryCost'

    primary_node_id = Column(ForeignKey(u'SupplyNodes.id'), primary_key=True)
    geography_id = Column(ForeignKey(u'Geographies.id'))
    other_index_1_id = Column(ForeignKey(u'OtherIndexes.id'))
    currency_id = Column(ForeignKey(u'Currencies.id'))
    currency_year_id = Column(ForeignKey(u'CurrencyYears.id'))
    denominator_unit = Column(Text)
    interpolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_growth = Column(Float)

    currency = relationship(u'Currency')
    currency_year = relationship(u'CurrencyYear')
    extrapolation_method = relationship(u'CleaningMethod', primaryjoin='PrimaryCost.extrapolation_method_id == CleaningMethod.id')
    geography = relationship(u'Geography')
    interpolation_method = relationship(u'CleaningMethod', primaryjoin='PrimaryCost.interpolation_method_id == CleaningMethod.id')
    other_index_1 = relationship(u'OtherIndex')
    primary_node = relationship(u'SupplyNode', uselist=False)


t_PrimaryCostData = Table(
    'PrimaryCostData', metadata,
    Column('primary_node_id', ForeignKey(u'SupplyNodes.id')),
    Column('gau_id', ForeignKey(u'GeographiesData.id')),
    Column('demand_sector_id', ForeignKey(u'DemandSectors.id')),
    Column('oth_1_id', ForeignKey(u'OtherIndexesData.id')),
    Column('resource_bins', Integer),
    Column('year', Integer),
    Column('value', Float(53))
)


class PrimaryEmission(Base):
    __tablename__ = 'PrimaryEmissions'

    primary_node_id = Column(ForeignKey(u'SupplyNodes.id'), primary_key=True)
    geography_id = Column(ForeignKey(u'Geographies.id'))
    other_index_1_id = Column(Integer)
    mass_unit = Column(Text)
    denominator_unit = Column(Text)
    interpolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_growth = Column(Float)
    source = Column(Text)
    notes = Column(Text)

    extrapolation_method = relationship(u'CleaningMethod', primaryjoin='PrimaryEmission.extrapolation_method_id == CleaningMethod.id')
    geography = relationship(u'Geography')
    interpolation_method = relationship(u'CleaningMethod', primaryjoin='PrimaryEmission.interpolation_method_id == CleaningMethod.id')
    primary_node = relationship(u'SupplyNode', uselist=False)


t_PrimaryEmissionsData = Table(
    'PrimaryEmissionsData', metadata,
    Column('primary_node_id', ForeignKey(u'SupplyNodes.id')),
    Column('gau_id', ForeignKey(u'GeographiesData.id')),
    Column('demand_sector_id', ForeignKey(u'DemandSectors.id')),
    Column('oth_1_id', ForeignKey(u'OtherIndexes.id')),
    Column('ghg_type_id', ForeignKey(u'GreenhouseGasEmissionsType.id')),
    Column('ghg_id', ForeignKey(u'GreenhouseGases.id')),
    Column('year', Integer),
    Column('value', Float(53))
)


class PrimaryPotentialConversion(Base):
    __tablename__ = 'PrimaryPotentialConversion'

    primary_node_id = Column(ForeignKey(u'SupplyNodes.id'), primary_key=True)
    geography_id = Column(ForeignKey(u'Geographies.id'))
    other_index_1_id = Column(ForeignKey(u'OtherIndexes.id'))
    energy_unit_numerator = Column(Text)
    resource_unit_denominator = Column(Text)
    interpolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_growth = Column(Float)

    extrapolation_method = relationship(u'CleaningMethod', primaryjoin='PrimaryPotentialConversion.extrapolation_method_id == CleaningMethod.id')
    geography = relationship(u'Geography')
    interpolation_method = relationship(u'CleaningMethod', primaryjoin='PrimaryPotentialConversion.interpolation_method_id == CleaningMethod.id')
    other_index_1 = relationship(u'OtherIndex')
    primary_node = relationship(u'SupplyNode', uselist=False)


t_PrimaryPotentialConversionData = Table(
    'PrimaryPotentialConversionData', metadata,
    Column('primary_node_id', ForeignKey(u'PrimaryPotentialConversion.primary_node_id')),
    Column('gau_id', ForeignKey(u'GeographiesData.id')),
    Column('oth_1_id', ForeignKey(u'OtherIndexesData.id')),
    Column('resource_bins', Integer),
    Column('year', Integer),
    Column('value', Float(53))
)


class Shape(Base):
    __tablename__ = 'Shapes'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"Shapes_id_seq\"'::regclass)"))
    name = Column(Text)
    shape_type_id = Column(ForeignKey(u'ShapesTypes.id'))
    shape_unit_type_id = Column(ForeignKey(u'ShapesUnits.id'))
    time_zone_id = Column(ForeignKey(u'TimeZones.id'))
    geography_id = Column(ForeignKey(u'Geographies.id'))
    other_index_1_id = Column(ForeignKey(u'OtherIndexes.id'))
    other_index_2_id = Column(ForeignKey(u'OtherIndexes.id'))
    geography_map_key_id = Column(ForeignKey(u'GeographyMapKeys.id'))
    interpolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))

    extrapolation_method = relationship(u'CleaningMethod', primaryjoin='Shape.extrapolation_method_id == CleaningMethod.id')
    geography = relationship(u'Geography')
    geography_map_key = relationship(u'GeographyMapKey')
    interpolation_method = relationship(u'CleaningMethod', primaryjoin='Shape.interpolation_method_id == CleaningMethod.id')
    other_index_1 = relationship(u'OtherIndex', primaryjoin='Shape.other_index_1_id == OtherIndex.id')
    other_index_2 = relationship(u'OtherIndex', primaryjoin='Shape.other_index_2_id == OtherIndex.id')
    shape_type = relationship(u'ShapesType')
    shape_unit_type = relationship(u'ShapesUnit')
    time_zone = relationship(u'TimeZone')


t_ShapesData = Table(
    'ShapesData', metadata,
    Column('id', ForeignKey(u'Shapes.id')),
    Column('gau_id', ForeignKey(u'GeographiesData.id')),
    Column('oth_1_id', ForeignKey(u'OtherIndexesData.id')),
    Column('oth_2_id', ForeignKey(u'OtherIndexesData.id')),
    Column('month', ForeignKey(u'Month.id')),
    Column('hour', ForeignKey(u'DayHour.day_hour')),
    Column('day_type_id', ForeignKey(u'DayType.id')),
    Column('weather_datetime', Text),
    Column('value', Float(53))
)


class ShapesType(Base):
    __tablename__ = 'ShapesTypes'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"ShapesTypes_id_seq\"'::regclass)"))
    name = Column(Text)


class ShapesUnit(Base):
    __tablename__ = 'ShapesUnits'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"ShapesUnits_id_seq\"'::regclass)"))
    name = Column(Text)


class StockDecayFunction(Base):
    __tablename__ = 'StockDecayFunctions'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"StockDecayFunctions_id_seq\"'::regclass)"))
    name = Column(Text)


class StockRolloverMethod(Base):
    __tablename__ = 'StockRolloverMethods'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"StockRolloverMethods_id_seq\"'::regclass)"))
    name = Column(Text, unique=True)


class StorageTechsCapacityCapitalCost(Base):
    __tablename__ = 'StorageTechsCapacityCapitalCost'

    storage_tech_id = Column(ForeignKey(u'SupplyTechs.id'), primary_key=True)
    definition_id = Column(ForeignKey(u'Definitions.id'))
    reference_tech_id = Column(ForeignKey(u'StorageTechsCapacityCapitalCost.storage_tech_id'))
    currency_id = Column(ForeignKey(u'Currencies.id'))
    geography_id = Column(ForeignKey(u'Geographies.id'))
    currency_year_id = Column(ForeignKey(u'CurrencyYears.id'))
    capacity_unit = Column(Text)
    is_levelized = Column(Boolean)
    cost_of_capital = Column(Float(53))
    interpolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))

    currency = relationship(u'Currency')
    currency_year = relationship(u'CurrencyYear')
    definition = relationship(u'Definition')
    extrapolation_method = relationship(u'CleaningMethod', primaryjoin='StorageTechsCapacityCapitalCost.extrapolation_method_id == CleaningMethod.id')
    geography = relationship(u'Geography')
    interpolation_method = relationship(u'CleaningMethod', primaryjoin='StorageTechsCapacityCapitalCost.interpolation_method_id == CleaningMethod.id')
    reference_tech = relationship(u'StorageTechsCapacityCapitalCost', remote_side=[storage_tech_id])
    storage_tech = relationship(u'SupplyTech', uselist=False)


class StorageTechsCapacityCapitalCostNewDatum(Base):
    __tablename__ = 'StorageTechsCapacityCapitalCostNewData'

    storage_tech_id = Column(ForeignKey(u'SupplyTechs.id'), primary_key=True)
    gau_id = Column(ForeignKey(u'GeographiesData.id'))
    oth_1_id = Column(ForeignKey(u'OtherIndexesData.id'))
    oth_2_id = Column(ForeignKey(u'OtherIndexesData.id'))
    vintage = Column(Integer)
    value = Column(Float)

    gau = relationship(u'GeographiesDatum')
    oth_1 = relationship(u'OtherIndexesDatum', primaryjoin='StorageTechsCapacityCapitalCostNewDatum.oth_1_id == OtherIndexesDatum.id')
    oth_2 = relationship(u'OtherIndexesDatum', primaryjoin='StorageTechsCapacityCapitalCostNewDatum.oth_2_id == OtherIndexesDatum.id')
    storage_tech = relationship(u'SupplyTech', uselist=False)


class StorageTechsCapacityCapitalCostReplacementDatum(Base):
    __tablename__ = 'StorageTechsCapacityCapitalCostReplacementData'

    storage_tech_id = Column(ForeignKey(u'SupplyTechs.id'), primary_key=True)
    gau_id = Column(ForeignKey(u'GeographiesData.id'))
    oth_1_id = Column(ForeignKey(u'OtherIndexesData.id'))
    oth_2_id = Column(ForeignKey(u'OtherIndexesData.id'))
    vintage = Column(Integer)
    value = Column(Float)

    gau = relationship(u'GeographiesDatum')
    oth_1 = relationship(u'OtherIndexesDatum', primaryjoin='StorageTechsCapacityCapitalCostReplacementDatum.oth_1_id == OtherIndexesDatum.id')
    oth_2 = relationship(u'OtherIndexesDatum', primaryjoin='StorageTechsCapacityCapitalCostReplacementDatum.oth_2_id == OtherIndexesDatum.id')
    storage_tech = relationship(u'SupplyTech', uselist=False)


class StorageTechsEnergyCapitalCost(Base):
    __tablename__ = 'StorageTechsEnergyCapitalCost'

    storage_tech_id = Column(ForeignKey(u'SupplyTechs.id'), primary_key=True)
    tech_name = Column(Text, unique=True)
    definition_id = Column(ForeignKey(u'Definitions.id'))
    reference_tech_id = Column(ForeignKey(u'StorageTechsEnergyCapitalCost.storage_tech_id'))
    currency_id = Column(ForeignKey(u'Currencies.id'))
    geography_id = Column(ForeignKey(u'Geographies.id'))
    currency_year_id = Column(ForeignKey(u'CurrencyYears.id'))
    energy_unit = Column(Text)
    is_levelized = Column(Boolean)
    cost_of_capital = Column(Float(53))
    interpolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))

    currency = relationship(u'Currency')
    currency_year = relationship(u'CurrencyYear')
    definition = relationship(u'Definition')
    extrapolation_method = relationship(u'CleaningMethod', primaryjoin='StorageTechsEnergyCapitalCost.extrapolation_method_id == CleaningMethod.id')
    geography = relationship(u'Geography')
    interpolation_method = relationship(u'CleaningMethod', primaryjoin='StorageTechsEnergyCapitalCost.interpolation_method_id == CleaningMethod.id')
    reference_tech = relationship(u'StorageTechsEnergyCapitalCost', remote_side=[storage_tech_id])
    storage_tech = relationship(u'SupplyTech', uselist=False)


t_StorageTechsEnergyCapitalCostNewData = Table(
    'StorageTechsEnergyCapitalCostNewData', metadata,
    Column('storage_tech_id', ForeignKey(u'SupplyTechs.id')),
    Column('gau_id', ForeignKey(u'GeographiesData.id')),
    Column('oth_1_id', ForeignKey(u'OtherIndexesData.id')),
    Column('oth_2_id', ForeignKey(u'OtherIndexesData.id')),
    Column('vintage', Integer),
    Column('value', Float)
)


t_StorageTechsEnergyCapitalCostReplacementData = Table(
    'StorageTechsEnergyCapitalCostReplacementData', metadata,
    Column('storage_tech_id', ForeignKey(u'SupplyTechs.id')),
    Column('gau_id', ForeignKey(u'GeographiesData.id')),
    Column('oth_1_id', ForeignKey(u'OtherIndexesData.id')),
    Column('oth_2_id', ForeignKey(u'OtherIndexesData.id')),
    Column('vintage', Integer),
    Column('value', Float)
)


class SupplyCapacityFactor(Base):
    __tablename__ = 'SupplyCapacityFactor'

    supply_node_id = Column(ForeignKey(u'SupplyNodes.id'), primary_key=True)
    geography_id = Column(ForeignKey(u'Geographies.id'))
    unit = Column(Text)
    interpolation_method = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_method = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_growth = Column(Float)

    CleaningMethod = relationship(u'CleaningMethod', primaryjoin='SupplyCapacityFactor.extrapolation_method == CleaningMethod.id')
    geography = relationship(u'Geography')
    CleaningMethod1 = relationship(u'CleaningMethod', primaryjoin='SupplyCapacityFactor.interpolation_method == CleaningMethod.id')
    supply_node = relationship(u'SupplyNode', uselist=False)


t_SupplyCapacityFactorData = Table(
    'SupplyCapacityFactorData', metadata,
    Column('supply_node_id', ForeignKey(u'SupplyCapacityFactor.supply_node_id')),
    Column('gau_id', ForeignKey(u'GeographiesData.id')),
    Column('demand_sector_id', Integer),
    Column('resource_bins', Integer),
    Column('year', Integer),
    Column('value', Float(53))
)


class SupplyCase(Base):
    __tablename__ = 'SupplyCases'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"SupplyCases_id_seq\"'::regclass)"))
    name = Column(Text)


t_SupplyCasesData = Table(
    'SupplyCasesData', metadata,
    Column('id', ForeignKey(u'SupplyCases.id')),
    Column('supply_node_id', ForeignKey(u'SupplyNodes.id')),
    Column('blend_package_id', ForeignKey(u'BlendNodeBlendMeasurePackages.id')),
    Column('export_package_id', ForeignKey(u'SupplyExportMeasurePackages.id')),
    Column('stock_package_id', ForeignKey(u'SupplyStockMeasurePackages.id')),
    Column('sales_package_id', ForeignKey(u'SupplySalesMeasurePackages.id')),
    Column('sales_share_package_id', ForeignKey(u'SupplySalesShareMeasurePackages.id'))
)


class SupplyCost(Base):
    __tablename__ = 'SupplyCost'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"SupplyCost_id_seq\"'::regclass)"))
    name = Column(Text)
    source = Column(Text)
    additional_notes = Column(Text)
    supply_node_id = Column(ForeignKey(u'SupplyNodes.id'))
    geography_id = Column(ForeignKey(u'Geographies.id'))
    supply_cost_type_id = Column(ForeignKey(u'SupplyCostTypes.id'))
    currency_id = Column(ForeignKey(u'Currencies.id'))
    currency_year_id = Column(ForeignKey(u'CurrencyYears.id'))
    energy_or_capacity_unit = Column(Text)
    time_unit = Column(Text)
    is_capital_cost = Column(Boolean, server_default=text("false"))
    cost_of_capital = Column(Float)
    book_life = Column(Integer)
    throughput_correlation = Column(Float(53))
    interpolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_growth = Column(Float)

    currency = relationship(u'Currency')
    currency_year = relationship(u'CurrencyYear')
    extrapolation_method = relationship(u'CleaningMethod', primaryjoin='SupplyCost.extrapolation_method_id == CleaningMethod.id')
    geography = relationship(u'Geography')
    interpolation_method = relationship(u'CleaningMethod', primaryjoin='SupplyCost.interpolation_method_id == CleaningMethod.id')
    supply_cost_type = relationship(u'SupplyCostType')
    supply_node = relationship(u'SupplyNode')


t_SupplyCostData = Table(
    'SupplyCostData', metadata,
    Column('id', ForeignKey(u'SupplyCost.id')),
    Column('gau_id', ForeignKey(u'GeographiesData.id')),
    Column('demand_sector_id', ForeignKey(u'DemandSectors.id')),
    Column('resource_bins', Integer),
    Column('year', Integer),
    Column('value', Float(53))
)


class SupplyCostType(Base):
    __tablename__ = 'SupplyCostTypes'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"SupplyCostTypes_id_seq\"'::regclass)"))
    name = Column(Text)


class SupplyEfficiency(Base):
    __tablename__ = 'SupplyEfficiency'

    id = Column(ForeignKey(u'SupplyNodes.id'), primary_key=True)
    geography_id = Column(ForeignKey(u'Geographies.id'))
    source = Column(Text)
    notes = Column(Text)
    input_unit = Column(Text)
    output_unit = Column(Text)
    interpolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_growth = Column(Float)

    extrapolation_method = relationship(u'CleaningMethod', primaryjoin='SupplyEfficiency.extrapolation_method_id == CleaningMethod.id')
    geography = relationship(u'Geography')
    SupplyNode = relationship(u'SupplyNode', uselist=False)
    interpolation_method = relationship(u'CleaningMethod', primaryjoin='SupplyEfficiency.interpolation_method_id == CleaningMethod.id')


t_SupplyEfficiencyData = Table(
    'SupplyEfficiencyData', metadata,
    Column('id', ForeignKey(u'SupplyEfficiency.id')),
    Column('gau_id', ForeignKey(u'GeographiesData.id')),
    Column('efficiency_type_id', ForeignKey(u'EfficiencyTypes.id')),
    Column('demand_sector_id', ForeignKey(u'DemandSectors.id')),
    Column('supply_node_id', ForeignKey(u'SupplyNodes.id')),
    Column('resource_bins', Integer),
    Column('year', Integer),
    Column('value', Float(53))
)


class SupplyExport(Base):
    __tablename__ = 'SupplyExport'

    supply_node_id = Column(ForeignKey(u'SupplyNodes.id'), primary_key=True)
    geography_id = Column(ForeignKey(u'Geographies.id'))
    oth_index_1_id = Column(ForeignKey(u'OtherIndexes.id'))
    unit = Column(Text)
    interpolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_growth = Column(Float)

    extrapolation_method = relationship(u'CleaningMethod', primaryjoin='SupplyExport.extrapolation_method_id == CleaningMethod.id')
    geography = relationship(u'Geography')
    interpolation_method = relationship(u'CleaningMethod', primaryjoin='SupplyExport.interpolation_method_id == CleaningMethod.id')
    oth_index_1 = relationship(u'OtherIndex')
    supply_node = relationship(u'SupplyNode', uselist=False)


t_SupplyExportData = Table(
    'SupplyExportData', metadata,
    Column('supply_node_id', ForeignKey(u'SupplyExport.supply_node_id')),
    Column('gau_id', ForeignKey(u'GeographiesData.id')),
    Column('oth_1_id', ForeignKey(u'OtherIndexes.id')),
    Column('resource_bins', Integer),
    Column('year', Integer),
    Column('value', Float(53))
)


class SupplyExportMeasurePackage(Base):
    __tablename__ = 'SupplyExportMeasurePackages'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"SupplyExportMeasurePackages_id_seq\"'::regclass)"))
    name = Column(Text)
    supply_node_id = Column(ForeignKey(u'SupplyNodes.id'))

    supply_node = relationship(u'SupplyNode')


t_SupplyExportMeasurePackagesData = Table(
    'SupplyExportMeasurePackagesData', metadata,
    Column('package_id', ForeignKey(u'SupplyExportMeasurePackages.id')),
    Column('measure_id', ForeignKey(u'SupplyExportMeasures.id'))
)


class SupplyExportMeasure(Base):
    __tablename__ = 'SupplyExportMeasures'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"SupplyExportMeasures_id_seq\"'::regclass)"))
    supply_node_id = Column(ForeignKey(u'SupplyNodes.id'))
    name = Column(Text)
    geography_id = Column(ForeignKey(u'Geographies.id'))
    other_index_1_id = Column(ForeignKey(u'OtherIndexes.id'))
    interpolation_method = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_method = Column(ForeignKey(u'CleaningMethods.id'))
    unit = Column(Integer)

    CleaningMethod = relationship(u'CleaningMethod', primaryjoin='SupplyExportMeasure.extrapolation_method == CleaningMethod.id')
    geography = relationship(u'Geography')
    CleaningMethod1 = relationship(u'CleaningMethod', primaryjoin='SupplyExportMeasure.interpolation_method == CleaningMethod.id')
    other_index_1 = relationship(u'OtherIndex')
    supply_node = relationship(u'SupplyNode')
    packages = relationship(u'SupplyExportMeasurePackage', secondary='SupplyExportMeasurePackagesData')


t_SupplyExportMeasuresData = Table(
    'SupplyExportMeasuresData', metadata,
    Column('id', ForeignKey(u'SupplyExportMeasures.id')),
    Column('gau_id', ForeignKey(u'GeographiesData.id')),
    Column('oth_1_id', ForeignKey(u'OtherIndexesData.id')),
    Column('year', Integer),
    Column('value', Float)
)


class SupplyNode(Base):
    __tablename__ = 'SupplyNodes'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"SupplyNodes_id_seq\"'::regclass)"))
    name = Column(Text)
    supply_type_id = Column(ForeignKey(u'SupplyTypes.id'))
    tradable_geography_id = Column(ForeignKey(u'Geographies.id'))
    is_active = Column(Boolean)
    final_energy_link = Column(ForeignKey(u'FinalEnergy.id'))
    is_curtailable = Column(Integer)
    is_exportable = Column(Integer)
    is_dispatchable = Column(Integer)
    residual_supply_node_id = Column(ForeignKey(u'SupplyNodes.id'))
    mean_lifetime = Column(Float)
    lifetime_variance = Column(Float)
    max_lifetime = Column(Float)
    min_lifetime = Column(Float)
    stock_decay_function_id = Column(ForeignKey(u'StockDecayFunctions.id'))
    cost_of_capital = Column(Float)
    book_life = Column(Integer)
    geography_map_key_id = Column(ForeignKey(u'Geographies.id'))
    shape_id = Column(ForeignKey(u'Shapes.id'))
    max_lag_hours = Column(Integer)
    max_lead_hours = Column(Integer)

    FinalEnergy = relationship(u'FinalEnergy')
    geography_map_key = relationship(u'Geography', primaryjoin='SupplyNode.geography_map_key_id == Geography.id')
    residual_supply_node = relationship(u'SupplyNode', remote_side=[id])
    shape = relationship(u'Shape')
    stock_decay_function = relationship(u'StockDecayFunction')
    supply_type = relationship(u'SupplyType')
    tradable_geography = relationship(u'Geography', primaryjoin='SupplyNode.tradable_geography_id == Geography.id')
    supply_nodes = relationship(
        u'SupplyNode',
        secondary='BlendNodeInputsData',
        primaryjoin=u'SupplyNode.id == BlendNodeInputsData.c.blend_node_id',
        secondaryjoin=u'SupplyNode.id == BlendNodeInputsData.c.supply_node_id'
    )


class SupplyPotential(Base):
    __tablename__ = 'SupplyPotential'

    supply_node_id = Column(ForeignKey(u'SupplyNodes.id'), primary_key=True)
    geography_id = Column(ForeignKey(u'Geographies.id'))
    other_index_1_id = Column(ForeignKey(u'OtherIndexes.id'))
    unit = Column(Text)
    time_unit = Column(Integer)
    interpolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_method_growth = Column(Float)
    extrapolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))

    extrapolation_method = relationship(u'CleaningMethod', primaryjoin='SupplyPotential.extrapolation_method_id == CleaningMethod.id')
    geography = relationship(u'Geography')
    interpolation_method = relationship(u'CleaningMethod', primaryjoin='SupplyPotential.interpolation_method_id == CleaningMethod.id')
    other_index_1 = relationship(u'OtherIndex')
    supply_node = relationship(u'SupplyNode', uselist=False)


t_SupplyPotentialData = Table(
    'SupplyPotentialData', metadata,
    Column('supply_node_id', ForeignKey(u'SupplyPotential.supply_node_id')),
    Column('gau_id', ForeignKey(u'GeographiesData.id')),
    Column('demand_sector', ForeignKey(u'DemandSectors.id')),
    Column('oth_1_id', ForeignKey(u'OtherIndexesData.id')),
    Column('resource_bins', Integer),
    Column('year', Integer),
    Column('value', Float(53))
)


class SupplySale(Base):
    __tablename__ = 'SupplySales'

    supply_node_id = Column(ForeignKey(u'SupplyNodes.id'), primary_key=True)
    geography_id = Column(ForeignKey(u'Geographies.id'))
    capacity_or_energy_unit = Column(Text)
    time_unit = Column(Text)
    stock_rollover_method_id = Column(ForeignKey(u'StockRolloverMethods.id'))
    interpolation_method = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_method = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_growth = Column(Float)

    CleaningMethod = relationship(u'CleaningMethod', primaryjoin='SupplySale.extrapolation_method == CleaningMethod.id')
    geography = relationship(u'Geography')
    CleaningMethod1 = relationship(u'CleaningMethod', primaryjoin='SupplySale.interpolation_method == CleaningMethod.id')
    stock_rollover_method = relationship(u'StockRolloverMethod')
    supply_node = relationship(u'SupplyNode', uselist=False)


t_SupplySalesData = Table(
    'SupplySalesData', metadata,
    Column('supply_node_id', ForeignKey(u'SupplySales.supply_node_id')),
    Column('gau_id', ForeignKey(u'GeographiesData.id')),
    Column('demand_sector', ForeignKey(u'DemandSectors.id')),
    Column('supply_technology', ForeignKey(u'SupplyTechs.id')),
    Column('vintage', Integer),
    Column('value', Float(53))
)


class SupplySalesMeasurePackage(Base):
    __tablename__ = 'SupplySalesMeasurePackages'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"SupplySalesMeasurePackages_id_seq\"'::regclass)"))
    name = Column(Text)
    supply_node_id = Column(ForeignKey(u'SupplyNodes.id'))

    supply_node = relationship(u'SupplyNode')


t_SupplySalesMeasurePackagesData = Table(
    'SupplySalesMeasurePackagesData', metadata,
    Column('package_id', ForeignKey(u'SupplySalesMeasurePackages.id')),
    Column('measure_id', ForeignKey(u'SupplyTechs.id'))
)


class SupplySalesMeasure(Base):
    __tablename__ = 'SupplySalesMeasures'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"SupplySalesMeasures_id_seq\"'::regclass)"))
    name = Column(Text)
    supply_technology_id = Column(ForeignKey(u'SupplyTechs.id'))
    supply_node_id = Column(ForeignKey(u'SupplyNodes.id'))
    geography_id = Column(ForeignKey(u'Geographies.id'))
    other_index_1_id = Column(ForeignKey(u'OtherIndexes.id'))
    capacity_or_energy_unit = Column(Text)
    time_unit = Column(Text)
    stock_rollover_method_id = Column(ForeignKey(u'StockRolloverMethods.id'))
    interpolation_method = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_method = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_growth = Column(Float)

    CleaningMethod = relationship(u'CleaningMethod', primaryjoin='SupplySalesMeasure.extrapolation_method == CleaningMethod.id')
    geography = relationship(u'Geography')
    CleaningMethod1 = relationship(u'CleaningMethod', primaryjoin='SupplySalesMeasure.interpolation_method == CleaningMethod.id')
    other_index_1 = relationship(u'OtherIndex')
    stock_rollover_method = relationship(u'StockRolloverMethod')
    supply_node = relationship(u'SupplyNode')
    supply_technology = relationship(u'SupplyTech')


t_SupplySalesMeasuresData = Table(
    'SupplySalesMeasuresData', metadata,
    Column('id', ForeignKey(u'SupplySalesMeasures.id')),
    Column('gau_id', ForeignKey(u'GeographiesData.id')),
    Column('oth_1_id', ForeignKey(u'OtherIndexes.id')),
    Column('demand_sector_id', ForeignKey(u'DemandSectors.id')),
    Column('resource_bins', Integer),
    Column('vintage', Integer),
    Column('value', Float(53))
)


class SupplySalesShare(Base):
    __tablename__ = 'SupplySalesShare'

    supply_node_id = Column(ForeignKey(u'SupplyNodes.id'), primary_key=True)
    geography_id = Column(ForeignKey(u'Geographies.id'))
    interpolation_method = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_method = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_growth = Column(Float)

    CleaningMethod = relationship(u'CleaningMethod', primaryjoin='SupplySalesShare.extrapolation_method == CleaningMethod.id')
    geography = relationship(u'Geography')
    CleaningMethod1 = relationship(u'CleaningMethod', primaryjoin='SupplySalesShare.interpolation_method == CleaningMethod.id')
    supply_node = relationship(u'SupplyNode', uselist=False)


t_SupplySalesShareData = Table(
    'SupplySalesShareData', metadata,
    Column('supply_node_id', ForeignKey(u'SupplyNodes.id')),
    Column('gau_id', ForeignKey(u'GeographiesData.id')),
    Column('demand_sector', ForeignKey(u'DemandSectors.id')),
    Column('supply_technology', ForeignKey(u'SupplyTechs.id')),
    Column('vintage', Integer),
    Column('value', Float(53))
)


class SupplySalesShareMeasurePackage(Base):
    __tablename__ = 'SupplySalesShareMeasurePackages'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"SupplySalesShareMeasurePackages_id_seq\"'::regclass)"))
    name = Column(Text)
    supply_node_id = Column(ForeignKey(u'SupplyNodes.id'))

    supply_node = relationship(u'SupplyNode')


t_SupplySalesShareMeasurePackagesData = Table(
    'SupplySalesShareMeasurePackagesData', metadata,
    Column('package_id', ForeignKey(u'SupplySalesShareMeasurePackages.id')),
    Column('measure_id', ForeignKey(u'SupplySalesShareMeasures.id'))
)


class SupplySalesShareMeasure(Base):
    __tablename__ = 'SupplySalesShareMeasures'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"SupplySalesShareMeasures_id_seq\"'::regclass)"))
    name = Column(Text)
    supply_node_id = Column(ForeignKey(u'SupplyNodes.id'))
    supply_technology_id = Column(ForeignKey(u'SupplyTechs.id'))
    replaced_supply_technology_id = Column(ForeignKey(u'SupplyTechs.id'))
    geography_id = Column(ForeignKey(u'Geographies.id'))
    capacity_or_energy_unit = Column(Text)
    time_unit = Column(Text)
    stock_rollover_method_id = Column(ForeignKey(u'StockRolloverMethods.id'))
    interpolation_method = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_method = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_growth = Column(Float)

    CleaningMethod = relationship(u'CleaningMethod', primaryjoin='SupplySalesShareMeasure.extrapolation_method == CleaningMethod.id')
    geography = relationship(u'Geography')
    CleaningMethod1 = relationship(u'CleaningMethod', primaryjoin='SupplySalesShareMeasure.interpolation_method == CleaningMethod.id')
    replaced_supply_technology = relationship(u'SupplyTech', primaryjoin='SupplySalesShareMeasure.replaced_supply_technology_id == SupplyTech.id')
    stock_rollover_method = relationship(u'StockRolloverMethod')
    supply_node = relationship(u'SupplyNode')
    supply_technology = relationship(u'SupplyTech', primaryjoin='SupplySalesShareMeasure.supply_technology_id == SupplyTech.id')
    packages = relationship(u'SupplySalesShareMeasurePackage', secondary='SupplySalesShareMeasurePackagesData')


t_SupplySalesShareMeasuresData = Table(
    'SupplySalesShareMeasuresData', metadata,
    Column('id', ForeignKey(u'SupplySalesShareMeasures.id')),
    Column('gau_id', ForeignKey(u'GeographiesData.id')),
    Column('demand_sector_id', ForeignKey(u'DemandSectors.id')),
    Column('vintage', Integer),
    Column('value', Float(53))
)


class SupplyStock(Base):
    __tablename__ = 'SupplyStock'

    supply_node_id = Column(ForeignKey(u'SupplyNodes.id'), primary_key=True)
    geography_id = Column(ForeignKey(u'Geographies.id'))
    capacity_or_energy_unit = Column(Text)
    time_unit = Column(Text)
    interpolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_growth = Column(Float)
    geography_map_key_id = Column(ForeignKey(u'Geographies.id'))

    extrapolation_method = relationship(u'CleaningMethod', primaryjoin='SupplyStock.extrapolation_method_id == CleaningMethod.id')
    geography = relationship(u'Geography', primaryjoin='SupplyStock.geography_id == Geography.id')
    geography_map_key = relationship(u'Geography', primaryjoin='SupplyStock.geography_map_key_id == Geography.id')
    interpolation_method = relationship(u'CleaningMethod', primaryjoin='SupplyStock.interpolation_method_id == CleaningMethod.id')
    supply_node = relationship(u'SupplyNode', uselist=False)


t_SupplyStockData = Table(
    'SupplyStockData', metadata,
    Column('supply_node_id', ForeignKey(u'SupplyNodes.id')),
    Column('gau_id', ForeignKey(u'GeographiesData.id')),
    Column('demand_sector', ForeignKey(u'DemandSectors.id')),
    Column('supply_technology', ForeignKey(u'SupplyTechs.id')),
    Column('resource_bins', Integer),
    Column('year', Integer),
    Column('value', Float(53))
)


class SupplyStockMeasurePackage(Base):
    __tablename__ = 'SupplyStockMeasurePackages'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"SupplyStockMeasurePackages_id_seq\"'::regclass)"))
    name = Column(Text)
    supply_node_id = Column(ForeignKey(u'SupplyNodes.id'))

    supply_node = relationship(u'SupplyNode')


t_SupplyStockMeasurePackagesData = Table(
    'SupplyStockMeasurePackagesData', metadata,
    Column('package_id', ForeignKey(u'SupplyStockMeasurePackages.id')),
    Column('measure_id', ForeignKey(u'SupplyStockMeasures.id'))
)


class SupplyStockMeasure(Base):
    __tablename__ = 'SupplyStockMeasures'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"SupplyStockMeasures_id_seq\"'::regclass)"))
    name = Column(Text)
    supply_technology_id = Column(ForeignKey(u'SupplyTechs.id'))
    supply_node_id = Column(ForeignKey(u'SupplyNodes.id'))
    geography_id = Column(ForeignKey(u'Geographies.id'))
    other_index_1_id = Column(ForeignKey(u'OtherIndexes.id'))
    capacity_or_energy_unit = Column(Text)
    time_unit = Column(Text)
    stock_rollover_method_id = Column(ForeignKey(u'StockRolloverMethods.id'))
    interpolation_method = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_method = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_growth = Column(Float)

    CleaningMethod = relationship(u'CleaningMethod', primaryjoin='SupplyStockMeasure.extrapolation_method == CleaningMethod.id')
    geography = relationship(u'Geography')
    CleaningMethod1 = relationship(u'CleaningMethod', primaryjoin='SupplyStockMeasure.interpolation_method == CleaningMethod.id')
    other_index_1 = relationship(u'OtherIndex')
    stock_rollover_method = relationship(u'StockRolloverMethod')
    supply_node = relationship(u'SupplyNode')
    supply_technology = relationship(u'SupplyTech')
    packages = relationship(u'SupplyStockMeasurePackage', secondary='SupplyStockMeasurePackagesData')


t_SupplyStockMeasuresData = Table(
    'SupplyStockMeasuresData', metadata,
    Column('id', ForeignKey(u'SupplyStockMeasures.id')),
    Column('gau_id', ForeignKey(u'GeographiesData.id')),
    Column('oth_1_id', ForeignKey(u'OtherIndexes.id')),
    Column('demand_sector_id', ForeignKey(u'DemandSectors.id')),
    Column('year', Integer),
    Column('value', Float(53))
)


class SupplyTech(Base):
    __tablename__ = 'SupplyTechs'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"SupplyTechs_id_seq\"'::regclass)"))
    name = Column(Text, unique=True)
    supply_node_id = Column(ForeignKey(u'SupplyNodes.id'))
    source = Column(Text)
    additional_description = Column(Text)
    stock_decay_function_id = Column(ForeignKey(u'StockDecayFunctions.id'))
    book_life = Column(Integer)
    mean_lifetime = Column(Float)
    lifetime_variance = Column(Float)
    min_lifetime = Column(Float)
    max_lifetime = Column(Float)
    discharge_duration = Column(Float)
    cost_of_capital = Column(Float)
    shape_id = Column(ForeignKey(u'Shapes.id'))
    max_lag_hours = Column(Integer)
    max_lead_hours = Column(Integer)

    shape = relationship(u'Shape')
    stock_decay_function = relationship(u'StockDecayFunction')
    supply_node = relationship(u'SupplyNode')
    packages = relationship(u'SupplySalesMeasurePackage', secondary='SupplySalesMeasurePackagesData')


class SupplyTechsCO2Capture(Base):
    __tablename__ = 'SupplyTechsCO2Capture'

    supply_tech_id = Column(ForeignKey(u'SupplyTechs.id'), primary_key=True)
    definition_id = Column(ForeignKey(u'Definitions.id'))
    geography_id = Column(ForeignKey(u'GeographiesData.id'))
    reference_tech_id = Column(ForeignKey(u'SupplyTechsCO2Capture.supply_tech_id'))
    interpolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_growth = Column(Float)
    age_growth_or_decay_type_id = Column(ForeignKey(u'AgeGrowthOrDecayType.id'))
    age_growth_or_decay = Column(Float)

    age_growth_or_decay_type = relationship(u'AgeGrowthOrDecayType')
    definition = relationship(u'Definition')
    extrapolation_method = relationship(u'CleaningMethod', primaryjoin='SupplyTechsCO2Capture.extrapolation_method_id == CleaningMethod.id')
    geography = relationship(u'GeographiesDatum')
    interpolation_method = relationship(u'CleaningMethod', primaryjoin='SupplyTechsCO2Capture.interpolation_method_id == CleaningMethod.id')
    reference_tech = relationship(u'SupplyTechsCO2Capture', remote_side=[supply_tech_id])
    supply_tech = relationship(u'SupplyTech', uselist=False)


class SupplyTechsCO2CaptureDatum(Base):
    __tablename__ = 'SupplyTechsCO2CaptureData'

    supply_tech_id = Column(ForeignKey(u'SupplyTechs.id'), primary_key=True)
    gau_id = Column(ForeignKey(u'GeographiesData.id'))
    resource_bin = Column(Integer)
    vintage = Column(Integer)
    value = Column(Float(53))

    gau = relationship(u'GeographiesDatum')
    supply_tech = relationship(u'SupplyTech', uselist=False)


class SupplyTechsCapacityFactor(Base):
    __tablename__ = 'SupplyTechsCapacityFactor'

    supply_tech_id = Column(ForeignKey(u'SupplyTechs.id'), primary_key=True)
    geography_id = Column(ForeignKey(u'Geographies.id'))
    reference_tech_id = Column(ForeignKey(u'SupplyTechsCapacityFactor.supply_tech_id'))
    definition_id = Column(ForeignKey(u'Definitions.id'))
    interpolation_method = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_method = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_growth = Column(Float)
    age_growth_or_decay_type_id = Column(ForeignKey(u'AgeGrowthOrDecayType.id'))
    age_growth_or_decay = Column(Float)

    age_growth_or_decay_type = relationship(u'AgeGrowthOrDecayType')
    definition = relationship(u'Definition')
    CleaningMethod = relationship(u'CleaningMethod', primaryjoin='SupplyTechsCapacityFactor.extrapolation_method == CleaningMethod.id')
    geography = relationship(u'Geography')
    CleaningMethod1 = relationship(u'CleaningMethod', primaryjoin='SupplyTechsCapacityFactor.interpolation_method == CleaningMethod.id')
    reference_tech = relationship(u'SupplyTechsCapacityFactor', remote_side=[supply_tech_id])
    supply_tech = relationship(u'SupplyTech', uselist=False)


t_SupplyTechsCapacityFactorData = Table(
    'SupplyTechsCapacityFactorData', metadata,
    Column('supply_tech_id', ForeignKey(u'SupplyTechs.id')),
    Column('gau_id', ForeignKey(u'GeographiesData.id')),
    Column('oth_1_id', ForeignKey(u'OtherIndexes.id')),
    Column('resource_bins', Integer),
    Column('year', Integer),
    Column('value', Float(53))
)


class SupplyTechsCapitalCost(Base):
    __tablename__ = 'SupplyTechsCapitalCost'

    supply_tech_id = Column(ForeignKey(u'SupplyTechs.id'), primary_key=True)
    definition_id = Column(ForeignKey(u'Definitions.id'))
    reference_tech_id = Column(ForeignKey(u'SupplyTechsCapitalCost.supply_tech_id'))
    geography_id = Column(ForeignKey(u'Geographies.id'))
    currency_id = Column(ForeignKey(u'Currencies.id'))
    currency_year_id = Column(ForeignKey(u'CurrencyYears.id'))
    capacity_or_energy_unit = Column(Text)
    time_unit = Column(Text)
    is_levelized = Column(Boolean)
    interpolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_growth = Column(Float)
    source = Column(Text)
    notes = Column(Text)

    currency = relationship(u'Currency')
    currency_year = relationship(u'CurrencyYear')
    definition = relationship(u'Definition')
    extrapolation_method = relationship(u'CleaningMethod', primaryjoin='SupplyTechsCapitalCost.extrapolation_method_id == CleaningMethod.id')
    geography = relationship(u'Geography')
    interpolation_method = relationship(u'CleaningMethod', primaryjoin='SupplyTechsCapitalCost.interpolation_method_id == CleaningMethod.id')
    reference_tech = relationship(u'SupplyTechsCapitalCost', remote_side=[supply_tech_id])
    supply_tech = relationship(u'SupplyTech', uselist=False)


t_SupplyTechsCapitalCostNewData = Table(
    'SupplyTechsCapitalCostNewData', metadata,
    Column('supply_tech_id', ForeignKey(u'SupplyTechs.id')),
    Column('gau_id', ForeignKey(u'GeographiesData.id')),
    Column('demand_sector_id', ForeignKey(u'DemandSectors.id')),
    Column('resource_bin', Integer),
    Column('vintage', Integer),
    Column('value', Float(53))
)


t_SupplyTechsCapitalCostReplacementData = Table(
    'SupplyTechsCapitalCostReplacementData', metadata,
    Column('supply_tech_id', ForeignKey(u'SupplyTechs.id')),
    Column('gau_id', ForeignKey(u'GeographiesData.id')),
    Column('demand_sector_id', ForeignKey(u'DemandSectors.id')),
    Column('resource_bin', Integer),
    Column('vintage', Integer),
    Column('value', Float(53))
)


class SupplyTechsEfficiency(Base):
    __tablename__ = 'SupplyTechsEfficiency'

    supply_tech_id = Column(ForeignKey(u'SupplyTechs.id'), primary_key=True)
    geography_id = Column(ForeignKey(u'GeographiesData.id'))
    definition_id = Column(ForeignKey(u'Definitions.id'))
    reference_tech_id = Column(ForeignKey(u'SupplyTechsEfficiency.supply_tech_id'))
    input_unit = Column(Text)
    output_unit = Column(Text)
    interpolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_growth = Column(Float)
    age_growth_or_decay_type_id = Column(ForeignKey(u'AgeGrowthOrDecayType.id'))
    age_growth_or_decay = Column(Float)
    source = Column(Text)
    notes = Column(Text)

    age_growth_or_decay_type = relationship(u'AgeGrowthOrDecayType')
    definition = relationship(u'Definition')
    extrapolation_method = relationship(u'CleaningMethod', primaryjoin='SupplyTechsEfficiency.extrapolation_method_id == CleaningMethod.id')
    geography = relationship(u'GeographiesDatum')
    interpolation_method = relationship(u'CleaningMethod', primaryjoin='SupplyTechsEfficiency.interpolation_method_id == CleaningMethod.id')
    reference_tech = relationship(u'SupplyTechsEfficiency', remote_side=[supply_tech_id])
    supply_tech = relationship(u'SupplyTech', uselist=False)


t_SupplyTechsEfficiencyData = Table(
    'SupplyTechsEfficiencyData', metadata,
    Column('supply_tech_id', ForeignKey(u'SupplyTechs.id')),
    Column('supply_node_id', ForeignKey(u'SupplyNodes.id')),
    Column('efficiency_type_id', ForeignKey(u'EfficiencyTypes.id')),
    Column('gau_id', ForeignKey(u'GeographiesData.id')),
    Column('demand_sector_id', ForeignKey(u'DemandSectors.id')),
    Column('resource_bin', Integer),
    Column('vintage', Integer),
    Column('value', Float(53))
)


class SupplyTechsFixedMaintenanceCost(Base):
    __tablename__ = 'SupplyTechsFixedMaintenanceCost'

    supply_tech_id = Column(ForeignKey(u'SupplyTechs.id'), primary_key=True)
    definition_id = Column(ForeignKey(u'Definitions.id'))
    reference_tech_id = Column(ForeignKey(u'SupplyTechsFixedMaintenanceCost.supply_tech_id'))
    geography_id = Column(ForeignKey(u'Geographies.id'))
    currency_id = Column(ForeignKey(u'Currencies.id'))
    currency_year_id = Column(ForeignKey(u'CurrencyYears.id'))
    capacity_or_energy_unit = Column(Text)
    time_unit = Column(Text)
    interpolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_growth = Column(Float)
    age_growth_or_decay_type_id = Column(ForeignKey(u'AgeGrowthOrDecayType.id'))
    age_growth_or_decay = Column(Float)
    source = Column(Text)
    notes = Column(Text)

    age_growth_or_decay_type = relationship(u'AgeGrowthOrDecayType')
    currency = relationship(u'Currency')
    currency_year = relationship(u'CurrencyYear')
    definition = relationship(u'Definition')
    extrapolation_method = relationship(u'CleaningMethod', primaryjoin='SupplyTechsFixedMaintenanceCost.extrapolation_method_id == CleaningMethod.id')
    geography = relationship(u'Geography')
    interpolation_method = relationship(u'CleaningMethod', primaryjoin='SupplyTechsFixedMaintenanceCost.interpolation_method_id == CleaningMethod.id')
    reference_tech = relationship(u'SupplyTechsFixedMaintenanceCost', remote_side=[supply_tech_id])
    supply_tech = relationship(u'SupplyTech', uselist=False)


t_SupplyTechsFixedMaintenanceCostData = Table(
    'SupplyTechsFixedMaintenanceCostData', metadata,
    Column('supply_tech_id', ForeignKey(u'SupplyTechs.id')),
    Column('gau_id', ForeignKey(u'GeographiesData.id')),
    Column('demand_sector_id', ForeignKey(u'DemandSectors.id')),
    Column('resource_bin', Integer),
    Column('vintage', Integer),
    Column('value', Float)
)


class SupplyTechsInstallationCost(Base):
    __tablename__ = 'SupplyTechsInstallationCost'

    supply_tech_id = Column(ForeignKey(u'SupplyTechs.id'), primary_key=True)
    definition_id = Column(ForeignKey(u'Definitions.id'))
    geography_id = Column(ForeignKey(u'Geographies.id'))
    reference_tech_id = Column(ForeignKey(u'SupplyTechsInstallationCost.supply_tech_id'))
    currency_id = Column(ForeignKey(u'Currencies.id'))
    currency_year_id = Column(ForeignKey(u'CurrencyYears.id'))
    capacity_or_energy_unit = Column(Text)
    time_unit = Column(Text)
    is_levelized = Column(Boolean, server_default=text("false"))
    interpolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_growth = Column(Float)
    source = Column(Text)
    notes = Column(Text)

    currency = relationship(u'Currency')
    currency_year = relationship(u'CurrencyYear')
    definition = relationship(u'Definition')
    extrapolation_method = relationship(u'CleaningMethod', primaryjoin='SupplyTechsInstallationCost.extrapolation_method_id == CleaningMethod.id')
    geography = relationship(u'Geography')
    interpolation_method = relationship(u'CleaningMethod', primaryjoin='SupplyTechsInstallationCost.interpolation_method_id == CleaningMethod.id')
    reference_tech = relationship(u'SupplyTechsInstallationCost', remote_side=[supply_tech_id])
    supply_tech = relationship(u'SupplyTech', uselist=False)


t_SupplyTechsInstallationCostNewData = Table(
    'SupplyTechsInstallationCostNewData', metadata,
    Column('supply_tech_id', ForeignKey(u'SupplyTechs.id')),
    Column('gau_id', ForeignKey(u'GeographiesData.id')),
    Column('demand_sector_id', ForeignKey(u'DemandSectors.id')),
    Column('resource_bin', Integer),
    Column('vintage', Integer),
    Column('value', Float(53))
)


t_SupplyTechsInstallationCostReplacementData = Table(
    'SupplyTechsInstallationCostReplacementData', metadata,
    Column('supply_tech_id', ForeignKey(u'SupplyTechs.id')),
    Column('gau_id', ForeignKey(u'GeographiesData.id')),
    Column('demand_sector_id', ForeignKey(u'DemandSectors.id')),
    Column('resource_bin', Integer),
    Column('vintage', Integer),
    Column('value', Float(53))
)


class SupplyTechsVariableMaintenanceCost(Base):
    __tablename__ = 'SupplyTechsVariableMaintenanceCost'

    supply_tech_id = Column(ForeignKey(u'SupplyTechs.id'), primary_key=True)
    definition_id = Column(ForeignKey(u'Definitions.id'))
    reference_tech_id = Column(ForeignKey(u'SupplyTechsVariableMaintenanceCost.supply_tech_id'))
    currency_id = Column(ForeignKey(u'Currencies.id'))
    geography_id = Column(ForeignKey(u'GeographiesData.id'))
    currency_year_id = Column(ForeignKey(u'CurrencyYears.id'))
    energy_unit = Column(Text)
    interpolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_growth = Column(Float)
    age_growth_or_decay_type_id = Column(ForeignKey(u'AgeGrowthOrDecayType.id'))
    age_growth_or_decay = Column(Float)
    source = Column(Text)
    notes = Column(Text)

    age_growth_or_decay_type = relationship(u'AgeGrowthOrDecayType')
    currency = relationship(u'Currency')
    currency_year = relationship(u'CurrencyYear')
    definition = relationship(u'Definition')
    extrapolation_method = relationship(u'CleaningMethod', primaryjoin='SupplyTechsVariableMaintenanceCost.extrapolation_method_id == CleaningMethod.id')
    geography = relationship(u'GeographiesDatum')
    interpolation_method = relationship(u'CleaningMethod', primaryjoin='SupplyTechsVariableMaintenanceCost.interpolation_method_id == CleaningMethod.id')
    reference_tech = relationship(u'SupplyTechsVariableMaintenanceCost', remote_side=[supply_tech_id])
    supply_tech = relationship(u'SupplyTech', uselist=False)


t_SupplyTechsVariableMaintenanceCostData = Table(
    'SupplyTechsVariableMaintenanceCostData', metadata,
    Column('supply_tech_id', ForeignKey(u'SupplyTechs.id')),
    Column('gau_id', ForeignKey(u'GeographiesData.id')),
    Column('demand_sector_id', ForeignKey(u'DemandSectors.id')),
    Column('resource_bin', Integer),
    Column('vintage', Integer),
    Column('value', Float(53))
)


class SupplyType(Base):
    __tablename__ = 'SupplyTypes'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"SupplyTypes_id_seq\"'::regclass)"))
    name = Column(Text, unique=True)


class TimeZone(Base):
    __tablename__ = 'TimeZones'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"TimeZones_id_seq\"'::regclass)"))
    name = Column(Text)
    utc_shift = Column(Float(53))


class YearHour(Base):
    __tablename__ = 'YearHour'

    year_hour = Column(Integer, primary_key=True, server_default=text("nextval('\"YearHour_year_hour_seq\"'::regclass)"))
