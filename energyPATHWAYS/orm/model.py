# coding: utf-8
from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, Text, UniqueConstraint, text
from sqlalchemy.orm import relationship

from alchemy_util import Base, metadata, RawDataHelp

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


class BlendNodeBlendMeasurePackagesDatum(Base):
    __tablename__ = 'BlendNodeBlendMeasurePackagesData'

    package_id = Column(ForeignKey(u'BlendNodeBlendMeasurePackages.id'))
    measure_id = Column(ForeignKey(u'BlendNodeBlendMeasures.id'))
    id = Column(Integer, primary_key=True, server_default=text("nextval('\"BlendNodeBlendMeasurePackagesData_id_seq\"'::regclass)"))

    measure = relationship(u'BlendNodeBlendMeasure')
    package = relationship(u'BlendNodeBlendMeasurePackage')


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


class BlendNodeBlendMeasuresDatum(Base):
    __tablename__ = 'BlendNodeBlendMeasuresData'

    parent_id = Column(ForeignKey(u'BlendNodeBlendMeasures.id'))
    gau_id = Column(ForeignKey(u'GeographiesData.id'))
    year = Column(Integer)
    value = Column(Float)
    id = Column(Integer, primary_key=True, server_default=text("nextval('\"BlendNodeBlendMeasuresData_id_seq\"'::regclass)"))

    gau = relationship(u'GeographiesDatum')
    parent = relationship(u'BlendNodeBlendMeasure')


class BlendNodeInputsDatum(Base):
    __tablename__ = 'BlendNodeInputsData'

    blend_node_id = Column(ForeignKey(u'SupplyNodes.id'))
    supply_node_id = Column(ForeignKey(u'SupplyNodes.id'))
    id = Column(Integer, primary_key=True, server_default=text("nextval('\"BlendNodeInputsData_id_seq\"'::regclass)"))

    blend_node = relationship(u'SupplyNode', primaryjoin='BlendNodeInputsDatum.blend_node_id == SupplyNode.id')
    supply_node = relationship(u'SupplyNode', primaryjoin='BlendNodeInputsDatum.supply_node_id == SupplyNode.id')


class CleaningMethod(Base):
    __tablename__ = 'CleaningMethods'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"CleaningMethods_id_seq\"'::regclass)"))
    name = Column(Text, unique=True)


class Currency(Base):
    __tablename__ = 'Currencies'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"Currencies_id_seq\"'::regclass)"))
    name = Column(Text)


class CurrenciesConversion(Base):
    __tablename__ = 'CurrenciesConversion'

    currency_id = Column(Integer)
    currency_year_id = Column(Integer)
    value = Column(Float(53))
    id = Column(Integer, primary_key=True, server_default=text("nextval('\"CurrenciesConversion_id_seq\"'::regclass)"))


class CurrencyYear(Base):
    __tablename__ = 'CurrencyYears'

    id = Column(Integer, primary_key=True)


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
    stock_decay_function_id = Column(ForeignKey(u'StockDecayFunctions.id'))
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
    stock_decay_function = relationship(u'StockDecayFunction')
    subsector = relationship(u'DemandSubsector')


class DemandCase(Base):
    __tablename__ = 'DemandCases'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DemandCases_id_seq\"'::regclass)"))
    name = Column(Text)


class DemandCasesDatum(Base):
    __tablename__ = 'DemandCasesData'

    parent_id = Column(ForeignKey(u'DemandCases.id'))
    subsector_id = Column(ForeignKey(u'DemandSubsectors.id'))
    stock_package_id = Column(ForeignKey(u'DemandStockMeasurePackages.id'))
    service_demand_package_id = Column(ForeignKey(u'DemandSectors.id'))
    energy_efficiency_package_id = Column(ForeignKey(u'DemandEnergyEfficiencyMeasurePackages.id'))
    fuel_switching_package_id = Column(ForeignKey(u'DemandFuelSwitchingMeasurePackages.id'))
    sales_package_id = Column(ForeignKey(u'DemandSalesMeasurePackages.id'))
    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DemandCasesData_id_seq\"'::regclass)"))

    energy_efficiency_package = relationship(u'DemandEnergyEfficiencyMeasurePackage')
    fuel_switching_package = relationship(u'DemandFuelSwitchingMeasurePackage')
    parent = relationship(u'DemandCase')
    sales_package = relationship(u'DemandSalesMeasurePackage')
    service_demand_package = relationship(u'DemandSector')
    stock_package = relationship(u'DemandStockMeasurePackage')
    subsector = relationship(u'DemandSubsector')


class DemandDriver(Base):
    __tablename__ = 'DemandDrivers'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DemandDrivers_id_seq\"'::regclass)"))
    name = Column(Text)
    base_driver_id = Column(ForeignKey(u'DemandDrivers.id'))
    input_type_id = Column(ForeignKey(u'InputTypes.id'))
    unit_prefix = Column(Integer)
    unit_base = Column(Text)
    geography_id = Column(ForeignKey(u'Geographies.id'))
    other_index_1_id = Column(ForeignKey(u'OtherIndexes.id'))
    other_index_2_id = Column(ForeignKey(u'OtherIndexes.id'))
    geography_map_key_id = Column(ForeignKey(u'GeographyMapKeys.id'))
    interpolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_growth = Column(Float)

    base_driver = relationship(u'DemandDriver', remote_side=[id])
    extrapolation_method = relationship(u'CleaningMethod', primaryjoin='DemandDriver.extrapolation_method_id == CleaningMethod.id')
    geography = relationship(u'Geography')
    geography_map_key = relationship(u'GeographyMapKey')
    input_type = relationship(u'InputType')
    interpolation_method = relationship(u'CleaningMethod', primaryjoin='DemandDriver.interpolation_method_id == CleaningMethod.id')
    other_index_1 = relationship(u'OtherIndex', primaryjoin='DemandDriver.other_index_1_id == OtherIndex.id')
    other_index_2 = relationship(u'OtherIndex', primaryjoin='DemandDriver.other_index_2_id == OtherIndex.id')


class DemandDriversDatum(Base):
    __tablename__ = 'DemandDriversData'

    parent_id = Column(ForeignKey(u'DemandDrivers.id'))
    gau_id = Column(ForeignKey(u'GeographiesData.id'))
    oth_1_id = Column(ForeignKey(u'OtherIndexesData.id'))
    oth_2_id = Column(ForeignKey(u'OtherIndexesData.id'))
    year = Column(Integer)
    value = Column(Float(53))
    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DemandDriversData_id_seq\"'::regclass)"))

    gau = relationship(u'GeographiesDatum')
    oth_1 = relationship(u'OtherIndexesDatum', primaryjoin='DemandDriversDatum.oth_1_id == OtherIndexesDatum.id')
    oth_2 = relationship(u'OtherIndexesDatum', primaryjoin='DemandDriversDatum.oth_2_id == OtherIndexesDatum.id')
    parent = relationship(u'DemandDriver')


class DemandEnergyDemandsDatum(Base):
    __tablename__ = 'DemandEnergyDemandsData'

    subsector_id = Column(ForeignKey(u'DemandEnergyDemands.subsector_id'))
    gau_id = Column(ForeignKey(u'GeographiesData.id'))
    oth_1_id = Column(ForeignKey(u'OtherIndexesData.id'))
    oth_2_id = Column(ForeignKey(u'OtherIndexesData.id'))
    final_energy = Column(ForeignKey(u'FinalEnergy.id'))
    technology = Column(Integer)
    year = Column(Integer)
    value = Column(Float)
    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DemandEnergyDemandsData_id_seq\"'::regclass)"))

    FinalEnergy = relationship(u'FinalEnergy')
    gau = relationship(u'GeographiesDatum')
    oth_1 = relationship(u'OtherIndexesDatum', primaryjoin='DemandEnergyDemandsDatum.oth_1_id == OtherIndexesDatum.id')
    oth_2 = relationship(u'OtherIndexesDatum', primaryjoin='DemandEnergyDemandsDatum.oth_2_id == OtherIndexesDatum.id')
    subsector = relationship(u'DemandEnergyDemand')


class DemandEnergyEfficiencyMeasurePackage(Base):
    __tablename__ = 'DemandEnergyEfficiencyMeasurePackages'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DemandEnergyEfficiencyMeasurePackages_id_seq\"'::regclass)"))
    name = Column(Text)
    subsector_id = Column(ForeignKey(u'DemandSubsectors.id'))

    subsector = relationship(u'DemandSubsector')


class DemandEnergyEfficiencyMeasurePackagesDatum(Base):
    __tablename__ = 'DemandEnergyEfficiencyMeasurePackagesData'

    package_id = Column(ForeignKey(u'DemandEnergyEfficiencyMeasurePackages.id'))
    measure_id = Column(ForeignKey(u'DemandEnergyEfficiencyMeasures.id'))
    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DemandEnergyEfficiencyMeasurePackagesData_id_seq\"'::regclass)"))

    measure = relationship(u'DemandEnergyEfficiencyMeasure')
    package = relationship(u'DemandEnergyEfficiencyMeasurePackage')


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
    stock_decay_function_id = Column(ForeignKey(u'StockDecayFunctions.id'))
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
    stock_decay_function = relationship(u'StockDecayFunction')
    subsector = relationship(u'DemandSubsector')


class DemandEnergyEfficiencyMeasuresCost(DemandEnergyEfficiencyMeasure):
    __tablename__ = 'DemandEnergyEfficiencyMeasuresCost'

    parent_id = Column(ForeignKey(u'DemandEnergyEfficiencyMeasures.id'), primary_key=True)
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
    extrapolation_method = relationship(u'CleaningMethod', primaryjoin='DemandEnergyEfficiencyMeasuresCost.extrapolation_method_id == CleaningMethod.id')
    geography = relationship(u'Geography')
    interpolation_method = relationship(u'CleaningMethod', primaryjoin='DemandEnergyEfficiencyMeasuresCost.interpolation_method_id == CleaningMethod.id')
    other_index_1 = relationship(u'OtherIndex', primaryjoin='DemandEnergyEfficiencyMeasuresCost.other_index_1_id == OtherIndex.id')
    other_index_2 = relationship(u'OtherIndex', primaryjoin='DemandEnergyEfficiencyMeasuresCost.other_index_2_id == OtherIndex.id')


class DemandEnergyEfficiencyMeasuresCostDatum(Base):
    __tablename__ = 'DemandEnergyEfficiencyMeasuresCostData'

    parent_id = Column(ForeignKey(u'DemandEnergyEfficiencyMeasures.id'))
    gau_id = Column(ForeignKey(u'GeographiesData.id'))
    oth_1_id = Column(ForeignKey(u'OtherIndexesData.id'))
    oth_2_id = Column(ForeignKey(u'OtherIndexesData.id'))
    vintage = Column(Integer)
    value = Column(Float)
    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DemandEnergyEfficiencyMeasuresCostData_id_seq\"'::regclass)"))

    gau = relationship(u'GeographiesDatum')
    oth_1 = relationship(u'OtherIndexesDatum', primaryjoin='DemandEnergyEfficiencyMeasuresCostDatum.oth_1_id == OtherIndexesDatum.id')
    oth_2 = relationship(u'OtherIndexesDatum', primaryjoin='DemandEnergyEfficiencyMeasuresCostDatum.oth_2_id == OtherIndexesDatum.id')
    parent = relationship(u'DemandEnergyEfficiencyMeasure')


class DemandEnergyEfficiencyMeasuresDatum(Base):
    __tablename__ = 'DemandEnergyEfficiencyMeasuresData'

    parent_id = Column(ForeignKey(u'DemandEnergyEfficiencyMeasures.id'))
    final_energy = Column(ForeignKey(u'FinalEnergy.id'))
    gau_id = Column(ForeignKey(u'GeographiesData.id'))
    oth_1_id = Column(ForeignKey(u'OtherIndexesData.id'))
    oth_2_id = Column(ForeignKey(u'OtherIndexesData.id'))
    year = Column(Integer)
    value = Column(Float)
    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DemandEnergyEfficiencyMeasuresData_id_seq\"'::regclass)"))

    FinalEnergy = relationship(u'FinalEnergy')
    gau = relationship(u'GeographiesDatum')
    oth_1 = relationship(u'OtherIndexesDatum', primaryjoin='DemandEnergyEfficiencyMeasuresDatum.oth_1_id == OtherIndexesDatum.id')
    oth_2 = relationship(u'OtherIndexesDatum', primaryjoin='DemandEnergyEfficiencyMeasuresDatum.oth_2_id == OtherIndexesDatum.id')
    parent = relationship(u'DemandEnergyEfficiencyMeasure')


class DemandFlexibleLoadMeasurePackage(Base):
    __tablename__ = 'DemandFlexibleLoadMeasurePackages'

    id = Column(Integer, primary_key=True)
    name = Column(Text)
    subsector_id = Column(ForeignKey(u'DemandSubsectors.id'))

    subsector = relationship(u'DemandSubsector')


class DemandFlexibleLoadMeasurePackagesDatum(Base):
    __tablename__ = 'DemandFlexibleLoadMeasurePackagesData'

    measure_id = Column(ForeignKey(u'DemandFlexibleLoadMeasures.id'))
    package_id = Column(ForeignKey(u'DemandFlexibleLoadMeasurePackages.id'))
    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DemandFlexibleLoadMeasurePackagesData_id_seq\"'::regclass)"))

    measure = relationship(u'DemandFlexibleLoadMeasure')
    package = relationship(u'DemandFlexibleLoadMeasurePackage')


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


class DemandFlexibleLoadMeasuresDatum(Base):
    __tablename__ = 'DemandFlexibleLoadMeasuresData'

    parent_id = Column(ForeignKey(u'DemandFlexibleLoadMeasures.id'))
    gau_id = Column(Integer)
    oth_1_id = Column(Integer)
    year = Column(Integer)
    value = Column(Integer)
    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DemandFlexibleLoadMeasuresData_id_seq\"'::regclass)"))

    parent = relationship(u'DemandFlexibleLoadMeasure')


class DemandFuelSwitchingMeasurePackage(Base):
    __tablename__ = 'DemandFuelSwitchingMeasurePackages'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DemandFuelSwitchingMeasurePackages_id_seq\"'::regclass)"))
    name = Column(Text)
    subsector_id = Column(ForeignKey(u'DemandSubsectors.id'))

    subsector = relationship(u'DemandSubsector')


class DemandFuelSwitchingMeasurePackagesDatum(Base):
    __tablename__ = 'DemandFuelSwitchingMeasurePackagesData'

    package_id = Column(ForeignKey(u'DemandFuelSwitchingMeasurePackages.id'))
    measure_id = Column(ForeignKey(u'DemandSectors.id'))
    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DemandFuelSwitchingMeasurePackagesData_id_seq\"'::regclass)"))

    measure = relationship(u'DemandSector')
    package = relationship(u'DemandFuelSwitchingMeasurePackage')


class DemandFuelSwitchingMeasure(Base):
    __tablename__ = 'DemandFuelSwitchingMeasures'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DemandFuelSwitchingMeasures_id_seq\"'::regclass)"))
    name = Column(Text)
    subsector_id = Column(ForeignKey(u'DemandSubsectors.id'))
    final_energy_from_id = Column(ForeignKey(u'FinalEnergy.id'))
    final_energy_to_id = Column(ForeignKey(u'FinalEnergy.id'))
    stock_decay_function_id = Column(ForeignKey(u'StockDecayFunctions.id'))
    max_lifetime = Column(Float)
    min_lifetime = Column(Float)
    mean_lifetime = Column(Float)
    lifetime_variance = Column(Float)

    final_energy_from = relationship(u'FinalEnergy', primaryjoin='DemandFuelSwitchingMeasure.final_energy_from_id == FinalEnergy.id')
    final_energy_to = relationship(u'FinalEnergy', primaryjoin='DemandFuelSwitchingMeasure.final_energy_to_id == FinalEnergy.id')
    stock_decay_function = relationship(u'StockDecayFunction')
    subsector = relationship(u'DemandSubsector')


class DemandFuelSwitchingMeasuresEnergyIntensity(DemandFuelSwitchingMeasure):
    __tablename__ = 'DemandFuelSwitchingMeasuresEnergyIntensity'

    id = Column(ForeignKey(u'DemandFuelSwitchingMeasures.id'), primary_key=True)
    geography_id = Column(ForeignKey(u'Geographies.id'))
    other_index_1_id = Column(ForeignKey(u'OtherIndexes.id'))
    other_index_2_id = Column(ForeignKey(u'OtherIndexesData.id'))
    interpolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_growth = Column(Float)
    parent_id = Column(Integer)

    extrapolation_method = relationship(u'CleaningMethod', primaryjoin='DemandFuelSwitchingMeasuresEnergyIntensity.extrapolation_method_id == CleaningMethod.id')
    geography = relationship(u'Geography')
    interpolation_method = relationship(u'CleaningMethod', primaryjoin='DemandFuelSwitchingMeasuresEnergyIntensity.interpolation_method_id == CleaningMethod.id')
    other_index_1 = relationship(u'OtherIndex')
    other_index_2 = relationship(u'OtherIndexesDatum')


class DemandFuelSwitchingMeasuresCost(DemandFuelSwitchingMeasure):
    __tablename__ = 'DemandFuelSwitchingMeasuresCost'

    parent_id = Column(ForeignKey(u'DemandFuelSwitchingMeasures.id'), primary_key=True)
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
    extrapolation_method = relationship(u'CleaningMethod', primaryjoin='DemandFuelSwitchingMeasuresCost.extrapolation_method_id == CleaningMethod.id')
    geography = relationship(u'Geography')
    interpolation_method = relationship(u'CleaningMethod', primaryjoin='DemandFuelSwitchingMeasuresCost.interpolation_method_id == CleaningMethod.id')
    other_index_1 = relationship(u'OtherIndex', primaryjoin='DemandFuelSwitchingMeasuresCost.other_index_1_id == OtherIndex.id')
    other_index_2 = relationship(u'OtherIndex', primaryjoin='DemandFuelSwitchingMeasuresCost.other_index_2_id == OtherIndex.id')


class DemandFuelSwitchingMeasuresCostDatum(Base):
    __tablename__ = 'DemandFuelSwitchingMeasuresCostData'

    parent_id = Column(ForeignKey(u'DemandFuelSwitchingMeasures.id'))
    gau_id = Column(ForeignKey(u'GeographiesData.id'))
    oth_1_id = Column(ForeignKey(u'OtherIndexesData.id'))
    oth_2_id = Column(ForeignKey(u'OtherIndexesData.id'))
    vintage = Column(Integer)
    value = Column(Float)
    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DemandFuelSwitchingMeasuresCostData_id_seq\"'::regclass)"))

    gau = relationship(u'GeographiesDatum')
    oth_1 = relationship(u'OtherIndexesDatum', primaryjoin='DemandFuelSwitchingMeasuresCostDatum.oth_1_id == OtherIndexesDatum.id')
    oth_2 = relationship(u'OtherIndexesDatum', primaryjoin='DemandFuelSwitchingMeasuresCostDatum.oth_2_id == OtherIndexesDatum.id')
    parent = relationship(u'DemandFuelSwitchingMeasure')


class DemandFuelSwitchingMeasuresEnergyIntensityDatum(Base):
    __tablename__ = 'DemandFuelSwitchingMeasuresEnergyIntensityData'

    parent_id = Column(ForeignKey(u'DemandFuelSwitchingMeasures.id'))
    gau_id = Column(ForeignKey(u'GeographiesData.id'))
    oth_1_id = Column(ForeignKey(u'OtherIndexesData.id'))
    oth_2_id = Column(ForeignKey(u'OtherIndexesData.id'))
    year = Column(Integer)
    value = Column(Float)
    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DemandFuelSwitchingMeasuresEnergyIntensityData_id_seq\"'::regclass)"))

    gau = relationship(u'GeographiesDatum')
    oth_1 = relationship(u'OtherIndexesDatum', primaryjoin='DemandFuelSwitchingMeasuresEnergyIntensityDatum.oth_1_id == OtherIndexesDatum.id')
    oth_2 = relationship(u'OtherIndexesDatum', primaryjoin='DemandFuelSwitchingMeasuresEnergyIntensityDatum.oth_2_id == OtherIndexesDatum.id')
    parent = relationship(u'DemandFuelSwitchingMeasure')


class DemandFuelSwitchingMeasuresImpact(Base):
    __tablename__ = 'DemandFuelSwitchingMeasuresImpact'

    id = Column(Integer, primary_key=True)
    input_type_id = Column(ForeignKey(u'InputTypes.id'))
    unit = Column(Text)
    geography_id = Column(ForeignKey(u'Geographies.id'))
    other_index_1_id = Column(ForeignKey(u'OtherIndexes.id'))
    other_index_2_id = Column(ForeignKey(u'OtherIndexesData.id'))
    interpolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_growth = Column(Float)
    parent_id = Column(ForeignKey(u'DemandFuelSwitchingMeasures.id'))

    extrapolation_method = relationship(u'CleaningMethod', primaryjoin='DemandFuelSwitchingMeasuresImpact.extrapolation_method_id == CleaningMethod.id')
    geography = relationship(u'Geography')
    input_type = relationship(u'InputType')
    interpolation_method = relationship(u'CleaningMethod', primaryjoin='DemandFuelSwitchingMeasuresImpact.interpolation_method_id == CleaningMethod.id')
    other_index_1 = relationship(u'OtherIndex')
    other_index_2 = relationship(u'OtherIndexesDatum')
    parent = relationship(u'DemandFuelSwitchingMeasure')


class DemandFuelSwitchingMeasuresImpactDatum(Base):
    __tablename__ = 'DemandFuelSwitchingMeasuresImpactData'

    parent_id = Column(ForeignKey(u'DemandFuelSwitchingMeasures.id'))
    gau_id = Column(ForeignKey(u'GeographiesData.id'))
    oth_1_id = Column(ForeignKey(u'OtherIndexesData.id'))
    oth_2_id = Column(ForeignKey(u'OtherIndexesData.id'))
    year = Column(Integer)
    value = Column(Float)
    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DemandFuelSwitchingMeasuresImpactData_id_seq\"'::regclass)"))

    gau = relationship(u'GeographiesDatum')
    oth_1 = relationship(u'OtherIndexesDatum', primaryjoin='DemandFuelSwitchingMeasuresImpactDatum.oth_1_id == OtherIndexesDatum.id')
    oth_2 = relationship(u'OtherIndexesDatum', primaryjoin='DemandFuelSwitchingMeasuresImpactDatum.oth_2_id == OtherIndexesDatum.id')
    parent = relationship(u'DemandFuelSwitchingMeasure')


class DemandSalesDatum(Base):
    __tablename__ = 'DemandSalesData'

    subsector_id = Column(ForeignKey(u'DemandSales.subsector_id'))
    gau_id = Column(ForeignKey(u'GeographiesData.id'))
    oth_1_id = Column(ForeignKey(u'OtherIndexesData.id'))
    oth_2_id = Column(ForeignKey(u'OtherIndexesData.id'))
    technology = Column(ForeignKey(u'DemandTechs.id'))
    vintage = Column(Integer)
    value = Column(Float)
    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DemandSalesData_id_seq\"'::regclass)"))

    gau = relationship(u'GeographiesDatum')
    oth_1 = relationship(u'OtherIndexesDatum', primaryjoin='DemandSalesDatum.oth_1_id == OtherIndexesDatum.id')
    oth_2 = relationship(u'OtherIndexesDatum', primaryjoin='DemandSalesDatum.oth_2_id == OtherIndexesDatum.id')
    subsector = relationship(u'DemandSale')
    DemandTech = relationship(u'DemandTech')


class DemandSalesMeasurePackage(Base):
    __tablename__ = 'DemandSalesMeasurePackages'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DemandSalesMeasurePackages_id_seq\"'::regclass)"))
    package_name = Column(Text)
    subsector_id = Column(ForeignKey(u'DemandSubsectors.id'))

    subsector = relationship(u'DemandSubsector')


class DemandSalesMeasurePackagesDatum(Base):
    __tablename__ = 'DemandSalesMeasurePackagesData'

    package_id = Column(ForeignKey(u'DemandSalesMeasurePackages.id'))
    measure_id = Column(ForeignKey(u'DemandSalesMeasures.id'))
    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DemandSalesMeasurePackagesData_id_seq\"'::regclass)"))

    measure = relationship(u'DemandSalesMeasure')
    package = relationship(u'DemandSalesMeasurePackage')


class DemandSalesMeasure(Base):
    __tablename__ = 'DemandSalesMeasures'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DemandSalesMeasures_id_seq\"'::regclass)"))
    subsector_id = Column(ForeignKey(u'DemandSubsectors.id'))
    geography_id = Column(ForeignKey(u'Geographies.id'))
    other_index_1_id = Column(ForeignKey(u'OtherIndexes.id'))
    demand_tech_id = Column(ForeignKey(u'DemandTechs.id'))
    replaced_demand_tech_id = Column(ForeignKey(u'DemandTechs.id'))
    input_type_id = Column(ForeignKey(u'InputTypes.id'))
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
    subsector = relationship(u'DemandSubsector')


class DemandSalesMeasuresDatum(Base):
    __tablename__ = 'DemandSalesMeasuresData'

    parent_id = Column(ForeignKey(u'DemandSalesMeasures.id'))
    gau_id = Column(ForeignKey(u'GeographiesData.id'))
    oth_1_id = Column(ForeignKey(u'OtherIndexesData.id'))
    vintage = Column(Integer)
    value = Column(Float)
    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DemandSalesMeasuresData_id_seq\"'::regclass)"))

    gau = relationship(u'GeographiesDatum')
    oth_1 = relationship(u'OtherIndexesDatum')
    parent = relationship(u'DemandSalesMeasure')


class DemandSector(Base):
    __tablename__ = 'DemandSectors'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DemandSectors_id_seq\"'::regclass)"))
    name = Column(Text, unique=True)
    shape_id = Column(Integer)
    max_lead_hours = Column(Integer)
    max_lag_hours = Column(Integer)


class DemandServiceDemandMeasurePackage(Base):
    __tablename__ = 'DemandServiceDemandMeasurePackages'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DemandServiceDemandMeasurePackages_id_seq\"'::regclass)"))
    name = Column(Text)
    subsector_id = Column(ForeignKey(u'DemandSubsectors.id'))

    subsector = relationship(u'DemandSubsector')


class DemandServiceDemandMeasurePackagesDatum(Base):
    __tablename__ = 'DemandServiceDemandMeasurePackagesData'

    package_id = Column(ForeignKey(u'DemandServiceDemandMeasurePackages.id'))
    measure_id = Column(ForeignKey(u'DemandServiceDemandMeasures.id'))
    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DemandServiceDemandMeasurePackagesData_id_seq\"'::regclass)"))

    measure = relationship(u'DemandServiceDemandMeasure')
    package = relationship(u'DemandServiceDemandMeasurePackage')


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
    stock_decay_function_id = Column(ForeignKey(u'StockDecayFunctions.id'))
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
    stock_decay_function = relationship(u'StockDecayFunction')
    subsector = relationship(u'DemandSubsector')


class DemandServiceDemandMeasuresCost(DemandServiceDemandMeasure):
    __tablename__ = 'DemandServiceDemandMeasuresCost'

    parent_id = Column(ForeignKey(u'DemandServiceDemandMeasures.id'), primary_key=True)
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
    extrapolation_method = relationship(u'CleaningMethod', primaryjoin='DemandServiceDemandMeasuresCost.extrapolation_method_id == CleaningMethod.id')
    geography = relationship(u'Geography')
    interpolation_method = relationship(u'CleaningMethod', primaryjoin='DemandServiceDemandMeasuresCost.interpolation_method_id == CleaningMethod.id')
    other_index_1 = relationship(u'OtherIndex', primaryjoin='DemandServiceDemandMeasuresCost.other_index_1_id == OtherIndex.id')
    other_index_2 = relationship(u'OtherIndex', primaryjoin='DemandServiceDemandMeasuresCost.other_index_2_id == OtherIndex.id')


class DemandServiceDemandMeasuresCostDatum(Base):
    __tablename__ = 'DemandServiceDemandMeasuresCostData'

    id = Column(Integer, primary_key=True)
    gau_id = Column(ForeignKey(u'GeographiesData.id'))
    oth_1_id = Column(ForeignKey(u'OtherIndexesData.id'))
    oth_2_id = Column(ForeignKey(u'OtherIndexesData.id'))
    vintage = Column(Integer)
    value = Column(Float)
    parent_id = Column(ForeignKey(u'DemandServiceDemandMeasures.id'))

    gau = relationship(u'GeographiesDatum')
    oth_1 = relationship(u'OtherIndexesDatum', primaryjoin='DemandServiceDemandMeasuresCostDatum.oth_1_id == OtherIndexesDatum.id')
    oth_2 = relationship(u'OtherIndexesDatum', primaryjoin='DemandServiceDemandMeasuresCostDatum.oth_2_id == OtherIndexesDatum.id')
    parent = relationship(u'DemandServiceDemandMeasure')


class DemandServiceDemandMeasuresDatum(Base):
    __tablename__ = 'DemandServiceDemandMeasuresData'

    parent_id = Column(ForeignKey(u'DemandServiceDemandMeasures.id'))
    gau_id = Column(ForeignKey(u'GeographiesData.id'))
    oth_1_id = Column(ForeignKey(u'OtherIndexesData.id'))
    oth_2_id = Column(ForeignKey(u'OtherIndexesData.id'))
    year = Column(Integer)
    value = Column(Float)
    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DemandServiceDemandMeasuresData_id_seq\"'::regclass)"))

    gau = relationship(u'GeographiesDatum')
    oth_1 = relationship(u'OtherIndexesDatum', primaryjoin='DemandServiceDemandMeasuresDatum.oth_1_id == OtherIndexesDatum.id')
    oth_2 = relationship(u'OtherIndexesDatum', primaryjoin='DemandServiceDemandMeasuresDatum.oth_2_id == OtherIndexesDatum.id')
    parent = relationship(u'DemandServiceDemandMeasure')


class DemandServiceDemandsDatum(Base):
    __tablename__ = 'DemandServiceDemandsData'

    subsector_id = Column(ForeignKey(u'DemandServiceDemands.subsector_id'))
    gau_id = Column(ForeignKey(u'GeographiesData.id'))
    final_energy = Column(ForeignKey(u'FinalEnergy.id'))
    technology = Column(ForeignKey(u'DemandTechs.id'))
    oth_1_id = Column(ForeignKey(u'OtherIndexesData.id'))
    oth_2_id = Column(ForeignKey(u'OtherIndexesData.id'))
    year = Column(Integer)
    value = Column(Float)
    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DemandServiceDemandsData_id_seq\"'::regclass)"))

    FinalEnergy = relationship(u'FinalEnergy')
    gau = relationship(u'GeographiesDatum')
    oth_1 = relationship(u'OtherIndexesDatum', primaryjoin='DemandServiceDemandsDatum.oth_1_id == OtherIndexesDatum.id')
    oth_2 = relationship(u'OtherIndexesDatum', primaryjoin='DemandServiceDemandsDatum.oth_2_id == OtherIndexesDatum.id')
    subsector = relationship(u'DemandServiceDemand')
    DemandTech = relationship(u'DemandTech')


class DemandServiceEfficiencyDatum(Base):
    __tablename__ = 'DemandServiceEfficiencyData'

    subsector_id = Column(ForeignKey(u'DemandSubsectors.id'))
    final_energy = Column(ForeignKey(u'FinalEnergy.id'))
    gau_id = Column(ForeignKey(u'GeographiesData.id'))
    oth_1_id = Column(ForeignKey(u'OtherIndexesData.id'))
    oth_2_id = Column(ForeignKey(u'OtherIndexesData.id'))
    year = Column(Integer)
    value = Column(Float)
    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DemandServiceEfficiencyData_id_seq\"'::regclass)"))

    FinalEnergy = relationship(u'FinalEnergy')
    gau = relationship(u'GeographiesDatum')
    oth_1 = relationship(u'OtherIndexesDatum', primaryjoin='DemandServiceEfficiencyDatum.oth_1_id == OtherIndexesDatum.id')
    oth_2 = relationship(u'OtherIndexesDatum', primaryjoin='DemandServiceEfficiencyDatum.oth_2_id == OtherIndexesDatum.id')
    subsector = relationship(u'DemandSubsector')


class DemandServiceLink(Base):
    __tablename__ = 'DemandServiceLink'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DemandServiceLink_id_seq\"'::regclass)"))
    subsector_id = Column(ForeignKey(u'DemandSubsectors.id'))
    linked_subsector_id = Column(ForeignKey(u'DemandSubsectors.id'))
    service_demand_share = Column(Float)
    year = Column(Integer)

    linked_subsector = relationship(u'DemandSubsector', primaryjoin='DemandServiceLink.linked_subsector_id == DemandSubsector.id')
    subsector = relationship(u'DemandSubsector', primaryjoin='DemandServiceLink.subsector_id == DemandSubsector.id')


class DemandStockDatum(Base):
    __tablename__ = 'DemandStockData'

    subsector_id = Column(ForeignKey(u'DemandStock.subsector_id', ondelete=u'CASCADE'))
    gau_id = Column(ForeignKey(u'GeographiesData.id'))
    oth_1_id = Column(ForeignKey(u'OtherIndexesData.id'))
    oth_2_id = Column(ForeignKey(u'OtherIndexesData.id'))
    technology = Column(ForeignKey(u'DemandTechs.id'))
    year = Column(Integer)
    value = Column(Float)
    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DemandStockData_id_seq\"'::regclass)"))

    gau = relationship(u'GeographiesDatum')
    oth_1 = relationship(u'OtherIndexesDatum', primaryjoin='DemandStockDatum.oth_1_id == OtherIndexesDatum.id')
    oth_2 = relationship(u'OtherIndexesDatum', primaryjoin='DemandStockDatum.oth_2_id == OtherIndexesDatum.id')
    subsector = relationship(u'DemandStock')
    DemandTech = relationship(u'DemandTech')


class DemandStockMeasurePackage(Base):
    __tablename__ = 'DemandStockMeasurePackages'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DemandStockMeasurePackages_id_seq\"'::regclass)"))
    name = Column(Text)
    subsector_id = Column(ForeignKey(u'DemandSubsectors.id'))

    subsector = relationship(u'DemandSubsector')


class DemandStockMeasurePackagesDatum(Base):
    __tablename__ = 'DemandStockMeasurePackagesData'

    package_id = Column(ForeignKey(u'DemandSalesMeasurePackages.id'))
    measure_id = Column(ForeignKey(u'DemandStockMeasurePackages.id'))
    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DemandStockMeasurePackagesData_id_seq\"'::regclass)"))

    measure = relationship(u'DemandStockMeasurePackage')
    package = relationship(u'DemandSalesMeasurePackage')


class DemandStockMeasure(Base):
    __tablename__ = 'DemandStockMeasures'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DemandStockMeasures_id_seq\"'::regclass)"))
    subsector_id = Column(ForeignKey(u'DemandSubsectors.id'))
    geography_id = Column(ForeignKey(u'Geographies.id'))
    other_index_1_id = Column(ForeignKey(u'OtherIndexes.id'))
    demand_tech_id = Column(ForeignKey(u'DemandSectors.id'))
    interpolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_growth = Column(Float)

    demand_tech = relationship(u'DemandSector')
    extrapolation_method = relationship(u'CleaningMethod', primaryjoin='DemandStockMeasure.extrapolation_method_id == CleaningMethod.id')
    geography = relationship(u'Geography')
    interpolation_method = relationship(u'CleaningMethod', primaryjoin='DemandStockMeasure.interpolation_method_id == CleaningMethod.id')
    other_index_1 = relationship(u'OtherIndex')
    subsector = relationship(u'DemandSubsector')


class DemandStockMeasuresDatum(Base):
    __tablename__ = 'DemandStockMeasuresData'

    parent_id = Column(ForeignKey(u'DemandStockMeasures.id'))
    gau_id = Column(ForeignKey(u'GeographiesData.id'))
    oth_1_id = Column(ForeignKey(u'OtherIndexesData.id'))
    vintage = Column(Integer)
    value = Column(Float)
    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DemandStockMeasuresData_id_seq\"'::regclass)"))

    gau = relationship(u'GeographiesDatum')
    oth_1 = relationship(u'OtherIndexesDatum')
    parent = relationship(u'DemandStockMeasure')


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


class DemandEnergyDemand(DemandSubsector):
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


class DemandServiceEfficiency(DemandSubsector):
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


class DemandStock(DemandSubsector):
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


class DemandSale(DemandSubsector):
    __tablename__ = 'DemandSales'

    subsector_id = Column(ForeignKey(u'DemandSubsectors.id'), primary_key=True)
    geography_id = Column(ForeignKey(u'Geographies.id'))
    other_index_1_id = Column(ForeignKey(u'OtherIndexes.id'))
    other_index_2_id = Column(ForeignKey(u'OtherIndexes.id'))
    input_type_id = Column(ForeignKey(u'InputTypes.id'))
    interpolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_growth = Column(Float)

    extrapolation_method = relationship(u'CleaningMethod', primaryjoin='DemandSale.extrapolation_method_id == CleaningMethod.id')
    geography = relationship(u'Geography')
    input_type = relationship(u'InputType')
    interpolation_method = relationship(u'CleaningMethod', primaryjoin='DemandSale.interpolation_method_id == CleaningMethod.id')
    other_index_1 = relationship(u'OtherIndex', primaryjoin='DemandSale.other_index_1_id == OtherIndex.id')
    other_index_2 = relationship(u'OtherIndex', primaryjoin='DemandSale.other_index_2_id == OtherIndex.id')


class DemandServiceDemand(DemandSubsector):
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


class DemandTechsInstallationCost(DemandTech):
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
    extrapolation_method = relationship(u'CleaningMethod', primaryjoin='DemandTechsInstallationCost.extrapolation_method_id == CleaningMethod.id')
    geography = relationship(u'Geography')
    interpolation_method = relationship(u'CleaningMethod', primaryjoin='DemandTechsInstallationCost.interpolation_method_id == CleaningMethod.id')
    other_index_1 = relationship(u'OtherIndex', primaryjoin='DemandTechsInstallationCost.other_index_1_id == OtherIndex.id')
    other_index_2 = relationship(u'OtherIndex', primaryjoin='DemandTechsInstallationCost.other_index_2_id == OtherIndex.id')


class DemandTechsParasiticEnergy(DemandTech):
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
    extrapolation_method = relationship(u'CleaningMethod', primaryjoin='DemandTechsParasiticEnergy.extrapolation_method_id == CleaningMethod.id')
    geography = relationship(u'Geography')
    interpolation_method = relationship(u'CleaningMethod', primaryjoin='DemandTechsParasiticEnergy.interpolation_method_id == CleaningMethod.id')
    other_index_1 = relationship(u'OtherIndex', primaryjoin='DemandTechsParasiticEnergy.other_index_1_id == OtherIndex.id')
    other_index_2 = relationship(u'OtherIndex', primaryjoin='DemandTechsParasiticEnergy.other_index_2_id == OtherIndex.id')


class DemandTechsMainEfficiency(DemandTech):
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
    extrapolation_method = relationship(u'CleaningMethod', primaryjoin='DemandTechsMainEfficiency.extrapolation_method_id == CleaningMethod.id')
    final_energy = relationship(u'FinalEnergy')
    geography = relationship(u'Geography')
    interpolation_method = relationship(u'CleaningMethod', primaryjoin='DemandTechsMainEfficiency.interpolation_method_id == CleaningMethod.id')
    other_index_1 = relationship(u'OtherIndex', primaryjoin='DemandTechsMainEfficiency.other_index_1_id == OtherIndex.id')
    other_index_2 = relationship(u'OtherIndex', primaryjoin='DemandTechsMainEfficiency.other_index_2_id == OtherIndex.id')
    reference_tech = relationship(u'DemandTechsMainEfficiency', remote_side=[demand_tech_id])


class DemandTechsFuelSwitchCost(DemandTech):
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
    extrapolation_method = relationship(u'CleaningMethod', primaryjoin='DemandTechsFuelSwitchCost.extrapolation_method_id == CleaningMethod.id')
    geography = relationship(u'Geography')
    interpolation_method = relationship(u'CleaningMethod', primaryjoin='DemandTechsFuelSwitchCost.interpolation_method_id == CleaningMethod.id')
    other_index_1 = relationship(u'OtherIndex', primaryjoin='DemandTechsFuelSwitchCost.other_index_1_id == OtherIndex.id')
    other_index_2 = relationship(u'OtherIndex', primaryjoin='DemandTechsFuelSwitchCost.other_index_2_id == OtherIndex.id')
    reference_tech = relationship(u'DemandTechsFuelSwitchCost', remote_side=[demand_tech_id])


class DemandTechsAuxEfficiency(DemandTech):
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
    extrapolation_method = relationship(u'CleaningMethod', primaryjoin='DemandTechsAuxEfficiency.extrapolation_method_id == CleaningMethod.id')
    final_energy = relationship(u'FinalEnergy')
    geography = relationship(u'Geography')
    interpolation_method = relationship(u'CleaningMethod', primaryjoin='DemandTechsAuxEfficiency.interpolation_method_id == CleaningMethod.id')
    other_index_1 = relationship(u'OtherIndex', primaryjoin='DemandTechsAuxEfficiency.other_index_1_id == OtherIndex.id')
    other_index_2 = relationship(u'OtherIndex', primaryjoin='DemandTechsAuxEfficiency.other_index_2_id == OtherIndex.id')


class DemandTechsFixedMaintenanceCost(DemandTech):
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
    extrapolation_method = relationship(u'CleaningMethod', primaryjoin='DemandTechsFixedMaintenanceCost.extrapolation_method_id == CleaningMethod.id')
    geography = relationship(u'Geography')
    interpolation_method = relationship(u'CleaningMethod', primaryjoin='DemandTechsFixedMaintenanceCost.interpolation_method_id == CleaningMethod.id')
    other_index_1 = relationship(u'OtherIndex', primaryjoin='DemandTechsFixedMaintenanceCost.other_index_1_id == OtherIndex.id')
    other_index_2 = relationship(u'OtherIndex', primaryjoin='DemandTechsFixedMaintenanceCost.other_index_2_id == OtherIndex.id')
    reference_tech = relationship(u'DemandTechsFixedMaintenanceCost', remote_side=[demand_tech_id])


class DemandTechsCapitalCost(DemandTech):
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
    extrapolation_method = relationship(u'CleaningMethod', primaryjoin='DemandTechsCapitalCost.extrapolation_method_id == CleaningMethod.id')
    geography = relationship(u'Geography')
    interpolation_method = relationship(u'CleaningMethod', primaryjoin='DemandTechsCapitalCost.interpolation_method_id == CleaningMethod.id')
    other_index_1 = relationship(u'OtherIndex', primaryjoin='DemandTechsCapitalCost.other_index_1_id == OtherIndex.id')
    other_index_2 = relationship(u'OtherIndex', primaryjoin='DemandTechsCapitalCost.other_index_2_id == OtherIndex.id')
    reference_tech = relationship(u'DemandTechsCapitalCost', remote_side=[demand_tech_id])


class DemandTechsServiceDemandModifier(DemandTech):
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
    extrapolation_method = relationship(u'CleaningMethod', primaryjoin='DemandTechsServiceDemandModifier.extrapolation_method_id == CleaningMethod.id')
    geography = relationship(u'Geography')
    interpolation_method = relationship(u'CleaningMethod', primaryjoin='DemandTechsServiceDemandModifier.interpolation_method_id == CleaningMethod.id')
    other_index_1 = relationship(u'OtherIndex', primaryjoin='DemandTechsServiceDemandModifier.other_index_1_id == OtherIndex.id')
    other_index_2 = relationship(u'OtherIndex', primaryjoin='DemandTechsServiceDemandModifier.other_index_2_id == OtherIndex.id')


class DemandTechsAuxEfficiencyDatum(Base):
    __tablename__ = 'DemandTechsAuxEfficiencyData'

    demand_tech_id = Column(ForeignKey(u'DemandTechs.id'))
    gau_id = Column(ForeignKey(u'GeographiesData.id'))
    oth_1_id = Column(ForeignKey(u'OtherIndexesData.id'))
    oth_2_id = Column(ForeignKey(u'OtherIndexesData.id'))
    vintage = Column(Integer)
    value = Column(Float)
    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DemandTechsAuxEfficiencyData_id_seq\"'::regclass)"))

    demand_tech = relationship(u'DemandTech')
    gau = relationship(u'GeographiesDatum')
    oth_1 = relationship(u'OtherIndexesDatum', primaryjoin='DemandTechsAuxEfficiencyDatum.oth_1_id == OtherIndexesDatum.id')
    oth_2 = relationship(u'OtherIndexesDatum', primaryjoin='DemandTechsAuxEfficiencyDatum.oth_2_id == OtherIndexesDatum.id')


class DemandTechsCapitalCostNewDatum(Base):
    __tablename__ = 'DemandTechsCapitalCostNewData'

    demand_tech_id = Column(ForeignKey(u'DemandTechs.id'))
    gau_id = Column(ForeignKey(u'GeographiesData.id'))
    oth_1_id = Column(ForeignKey(u'OtherIndexesData.id'))
    oth_2_id = Column(ForeignKey(u'OtherIndexesData.id'))
    vintage = Column(Integer)
    value = Column(Float)
    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DemandTechsCapitalCostNewData_id_seq\"'::regclass)"))

    demand_tech = relationship(u'DemandTech')
    gau = relationship(u'GeographiesDatum')
    oth_1 = relationship(u'OtherIndexesDatum', primaryjoin='DemandTechsCapitalCostNewDatum.oth_1_id == OtherIndexesDatum.id')
    oth_2 = relationship(u'OtherIndexesDatum', primaryjoin='DemandTechsCapitalCostNewDatum.oth_2_id == OtherIndexesDatum.id')


class DemandTechsCapitalCostReplacementDatum(Base):
    __tablename__ = 'DemandTechsCapitalCostReplacementData'

    demand_tech_id = Column(ForeignKey(u'DemandTechs.id'))
    gau_id = Column(ForeignKey(u'GeographiesData.id'))
    oth_1_id = Column(ForeignKey(u'OtherIndexesData.id'))
    oth_2_id = Column(ForeignKey(u'OtherIndexesData.id'))
    vintage = Column(Integer)
    value = Column(Float)
    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DemandTechsCapitalCostReplacementData_id_seq\"'::regclass)"))

    demand_tech = relationship(u'DemandTech')
    gau = relationship(u'GeographiesDatum')
    oth_1 = relationship(u'OtherIndexesDatum', primaryjoin='DemandTechsCapitalCostReplacementDatum.oth_1_id == OtherIndexesDatum.id')
    oth_2 = relationship(u'OtherIndexesDatum', primaryjoin='DemandTechsCapitalCostReplacementDatum.oth_2_id == OtherIndexesDatum.id')


class DemandTechsFixedMaintenanceCostDatum(Base):
    __tablename__ = 'DemandTechsFixedMaintenanceCostData'

    demand_tech_id = Column(ForeignKey(u'DemandTechs.id'))
    gau_id = Column(ForeignKey(u'GeographiesData.id'))
    oth_1_id = Column(ForeignKey(u'OtherIndexesData.id'))
    oth_2_id = Column(ForeignKey(u'OtherIndexesData.id'))
    vintage = Column(Integer)
    value = Column(Float)
    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DemandTechsFixedMaintenanceCostData_id_seq\"'::regclass)"))

    demand_tech = relationship(u'DemandTech')
    gau = relationship(u'GeographiesDatum')
    oth_1 = relationship(u'OtherIndexesDatum', primaryjoin='DemandTechsFixedMaintenanceCostDatum.oth_1_id == OtherIndexesDatum.id')
    oth_2 = relationship(u'OtherIndexesDatum', primaryjoin='DemandTechsFixedMaintenanceCostDatum.oth_2_id == OtherIndexesDatum.id')


class DemandTechsFuelSwitchCostDatum(Base):
    __tablename__ = 'DemandTechsFuelSwitchCostData'

    demand_tech_id = Column(ForeignKey(u'DemandTechs.id'))
    gau_id = Column(ForeignKey(u'GeographiesData.id'))
    oth_1_id = Column(ForeignKey(u'OtherIndexesData.id'))
    oth_2_id = Column(ForeignKey(u'OtherIndexesData.id'))
    vintage = Column(Integer)
    value = Column(Float)
    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DemandTechsFuelSwitchCostData_id_seq\"'::regclass)"))

    demand_tech = relationship(u'DemandTech')
    gau = relationship(u'GeographiesDatum')
    oth_1 = relationship(u'OtherIndexesDatum', primaryjoin='DemandTechsFuelSwitchCostDatum.oth_1_id == OtherIndexesDatum.id')
    oth_2 = relationship(u'OtherIndexesDatum', primaryjoin='DemandTechsFuelSwitchCostDatum.oth_2_id == OtherIndexesDatum.id')


class DemandTechsInstallationCostNewDatum(Base):
    __tablename__ = 'DemandTechsInstallationCostNewData'

    demand_tech_id = Column(ForeignKey(u'DemandTechs.id'))
    gau_id = Column(ForeignKey(u'GeographiesData.id'))
    oth_1_id = Column(ForeignKey(u'OtherIndexesData.id'))
    oth_2_id = Column(ForeignKey(u'OtherIndexesData.id'))
    vintage = Column(Integer)
    value = Column(Float)
    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DemandTechsInstallationCostNewData_id_seq\"'::regclass)"))

    demand_tech = relationship(u'DemandTech')
    gau = relationship(u'GeographiesDatum')
    oth_1 = relationship(u'OtherIndexesDatum', primaryjoin='DemandTechsInstallationCostNewDatum.oth_1_id == OtherIndexesDatum.id')
    oth_2 = relationship(u'OtherIndexesDatum', primaryjoin='DemandTechsInstallationCostNewDatum.oth_2_id == OtherIndexesDatum.id')


class DemandTechsInstallationCostReplacementDatum(Base):
    __tablename__ = 'DemandTechsInstallationCostReplacementData'

    demand_tech_id = Column(ForeignKey(u'DemandTechs.id'))
    gau_id = Column(ForeignKey(u'GeographiesData.id'))
    oth_1_id = Column(ForeignKey(u'OtherIndexesData.id'))
    oth_2_id = Column(ForeignKey(u'OtherIndexesData.id'))
    vintage = Column(Integer)
    value = Column(Float)
    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DemandTechsInstallationCostReplacementData_id_seq\"'::regclass)"))

    demand_tech = relationship(u'DemandTech')
    gau = relationship(u'GeographiesDatum')
    oth_1 = relationship(u'OtherIndexesDatum', primaryjoin='DemandTechsInstallationCostReplacementDatum.oth_1_id == OtherIndexesDatum.id')
    oth_2 = relationship(u'OtherIndexesDatum', primaryjoin='DemandTechsInstallationCostReplacementDatum.oth_2_id == OtherIndexesDatum.id')


class DemandTechsMainEfficiencyDatum(Base):
    __tablename__ = 'DemandTechsMainEfficiencyData'

    demand_tech_id = Column(ForeignKey(u'DemandTechs.id'))
    gau_id = Column(ForeignKey(u'GeographiesData.id'))
    oth_1_id = Column(ForeignKey(u'OtherIndexesData.id'))
    oth_2_id = Column(ForeignKey(u'OtherIndexesData.id'))
    vintage = Column(Integer)
    value = Column(Float)
    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DemandTechsMainEfficiencyData_id_seq\"'::regclass)"))

    demand_tech = relationship(u'DemandTech')
    gau = relationship(u'GeographiesDatum')
    oth_1 = relationship(u'OtherIndexesDatum', primaryjoin='DemandTechsMainEfficiencyDatum.oth_1_id == OtherIndexesDatum.id')
    oth_2 = relationship(u'OtherIndexesDatum', primaryjoin='DemandTechsMainEfficiencyDatum.oth_2_id == OtherIndexesDatum.id')


class DemandTechsParasiticEnergyDatum(Base):
    __tablename__ = 'DemandTechsParasiticEnergyData'

    demand_tech_id = Column(ForeignKey(u'DemandTechs.id'))
    gau_id = Column(ForeignKey(u'GeographiesData.id'))
    oth_1_id = Column(ForeignKey(u'OtherIndexesData.id'))
    oth_2_id = Column(ForeignKey(u'OtherIndexesData.id'))
    final_energy = Column(ForeignKey(u'FinalEnergy.id'))
    vintage = Column(Integer)
    value = Column(Float)
    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DemandTechsParasiticEnergyData_id_seq\"'::regclass)"))

    demand_tech = relationship(u'DemandTech')
    FinalEnergy = relationship(u'FinalEnergy')
    gau = relationship(u'GeographiesDatum')
    oth_1 = relationship(u'OtherIndexesDatum', primaryjoin='DemandTechsParasiticEnergyDatum.oth_1_id == OtherIndexesDatum.id')
    oth_2 = relationship(u'OtherIndexesDatum', primaryjoin='DemandTechsParasiticEnergyDatum.oth_2_id == OtherIndexesDatum.id')


class DemandTechsServiceDemandModifierDatum(Base):
    __tablename__ = 'DemandTechsServiceDemandModifierData'

    demand_tech_id = Column(ForeignKey(u'DemandTechs.id'))
    gau_id = Column(ForeignKey(u'GeographiesData.id'))
    oth_1_id = Column(ForeignKey(u'OtherIndexesData.id'))
    oth_2_id = Column(ForeignKey(u'OtherIndexesData.id'))
    vintage = Column(Integer)
    value = Column(Float)
    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DemandTechsServiceDemandModifierData_id_seq\"'::regclass)"))

    demand_tech = relationship(u'DemandTech')
    gau = relationship(u'GeographiesDatum')
    oth_1 = relationship(u'OtherIndexesDatum', primaryjoin='DemandTechsServiceDemandModifierDatum.oth_1_id == OtherIndexesDatum.id')
    oth_2 = relationship(u'OtherIndexesDatum', primaryjoin='DemandTechsServiceDemandModifierDatum.oth_2_id == OtherIndexesDatum.id')


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


class DemandTechsServiceLinkDatum(Base):
    __tablename__ = 'DemandTechsServiceLinkData'

    parent_id = Column(ForeignKey(u'DemandTechsServiceLink.id'))
    gau_id = Column(ForeignKey(u'GeographiesData.id'))
    oth_1_id = Column(ForeignKey(u'OtherIndexesData.id'))
    oth_2_id = Column(ForeignKey(u'OtherIndexesData.id'))
    vintage = Column(Integer)
    value = Column(Float)
    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DemandTechsServiceLinkData_id_seq\"'::regclass)"))

    gau = relationship(u'GeographiesDatum')
    oth_1 = relationship(u'OtherIndexesDatum', primaryjoin='DemandTechsServiceLinkDatum.oth_1_id == OtherIndexesDatum.id')
    oth_2 = relationship(u'OtherIndexesDatum', primaryjoin='DemandTechsServiceLinkDatum.oth_2_id == OtherIndexesDatum.id')
    parent = relationship(u'DemandTechsServiceLink')


class DispatchConfig(Base):
    __tablename__ = 'DispatchConfig'

    id = Column(Integer, primary_key=True)
    geography_id = Column(ForeignKey(u'Geographies.id'))
    opt_hours = Column(Integer)
    flex_load_constraints_offset = Column(Integer)
    large_storage_duration = Column(Integer)
    thermal_dispatch_node_id = Column(ForeignKey(u'SupplyNodes.id'))
    distribution_node_id = Column(ForeignKey(u'SupplyNodes.id'))
    transmission_node_id = Column(ForeignKey(u'SupplyNodes.id'))
    distribution_grid_node_id = Column(Integer)

    distribution_node = relationship(u'SupplyNode', primaryjoin='DispatchConfig.distribution_node_id == SupplyNode.id')
    geography = relationship(u'Geography')
    thermal_dispatch_node = relationship(u'SupplyNode', primaryjoin='DispatchConfig.thermal_dispatch_node_id == SupplyNode.id')
    transmission_node = relationship(u'SupplyNode', primaryjoin='DispatchConfig.transmission_node_id == SupplyNode.id')


class DispatchConstraintType(Base):
    __tablename__ = 'DispatchConstraintTypes'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DispatchConstraintTypes_id_seq\"'::regclass)"))
    name = Column(Text)


class DispatchFeeder(Base):
    __tablename__ = 'DispatchFeeders'

    id = Column(Integer, primary_key=True)
    name = Column(Text, unique=True)


class DispatchFeedersAllocation(Base):
    __tablename__ = 'DispatchFeedersAllocation'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DispatchFeedersAllocation_id_seq\"'::regclass)"))
    geography_id = Column(Integer)
    geography_map_key_id = Column(Integer)
    input_type_id = Column(Integer)
    interpolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))

    extrapolation_method = relationship(u'CleaningMethod', primaryjoin='DispatchFeedersAllocation.extrapolation_method_id == CleaningMethod.id')
    interpolation_method = relationship(u'CleaningMethod', primaryjoin='DispatchFeedersAllocation.interpolation_method_id == CleaningMethod.id')


class DispatchFeedersAllocationDatum(Base):
    __tablename__ = 'DispatchFeedersAllocationData'

    parent_id = Column(Integer)
    gau_id = Column(Integer)
    dispatch_feeder = Column(Integer)
    demand_sector = Column(Integer)
    year = Column(Integer)
    value = Column(Float(53))
    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DispatchFeedersAllocationData_id_seq\"'::regclass)"))


class DispatchNodeDatum(Base):
    __tablename__ = 'DispatchNodeData'

    supply_node_id = Column(ForeignKey(u'DispatchNodeConfig.supply_node_id'))
    gau_id = Column(ForeignKey(u'GeographiesData.id'))
    week = Column(Integer)
    day = Column(Integer)
    month = Column(Integer)
    p_max = Column(Float(53))
    p_min = Column(Float(53))
    energy_budget = Column(Float(53))
    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DispatchNodeData_id_seq\"'::regclass)"))

    gau = relationship(u'GeographiesDatum')
    supply_node = relationship(u'DispatchNodeConfig')


class DispatchWindow(Base):
    __tablename__ = 'DispatchWindows'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"DispatchWindows_id_seq\"'::regclass)"))
    name = Column(Text, unique=True)


class EfficiencyType(Base):
    __tablename__ = 'EfficiencyTypes'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"EfficiencyTypes_id_seq\"'::regclass)"))
    name = Column(Text)


class FinalEnergy(Base):
    __tablename__ = 'FinalEnergy'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"FinalEnergy_id_seq\"'::regclass)"))
    name = Column(Text)
    shape_id = Column(ForeignKey(u'Shapes.id'))

    shape = relationship(u'Shape')


class FlexibleLoadShiftType(Base):
    __tablename__ = 'FlexibleLoadShiftTypes'

    id = Column(Integer, primary_key=True)
    name = Column(Text)


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


class GeographyIntersection(Base):
    __tablename__ = 'GeographyIntersection'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"GeographyIntersection_id_seq\"'::regclass)"))


class GeographyIntersectionDatum(Base):
    __tablename__ = 'GeographyIntersectionData'
    __table_args__ = (
        UniqueConstraint('intersection_id', 'gau_id'),
    )

    intersection_id = Column(ForeignKey(u'GeographyIntersection.id'))
    gau_id = Column(ForeignKey(u'GeographiesData.id'))
    id = Column(Integer, primary_key=True, server_default=text("nextval('\"GeographyIntersectionData_id_seq\"'::regclass)"))

    gau = relationship(u'GeographiesDatum')
    intersection = relationship(u'GeographyIntersection')


class GeographyMap(Base):
    __tablename__ = 'GeographyMap'
    __table_args__ = (
        UniqueConstraint('intersection_id', 'geography_map_key_id'),
    )

    intersection_id = Column(ForeignKey(u'GeographyIntersection.id'))
    geography_map_key_id = Column(ForeignKey(u'GeographyMapKeys.id'))
    value = Column(Float(53))
    id = Column(Integer, primary_key=True, server_default=text("nextval('\"GeographyMap_id_seq\"'::regclass)"))

    geography_map_key = relationship(u'GeographyMapKey')
    intersection = relationship(u'GeographyIntersection')


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


class ImportCostDatum(Base):
    __tablename__ = 'ImportCostData'

    import_node_id = Column(ForeignKey(u'ImportCost.import_node_id'))
    gau_id = Column(ForeignKey(u'GeographiesData.id'))
    demand_sector_id = Column(ForeignKey(u'DemandSectors.id'))
    year = Column(Integer)
    value = Column(Float(53))
    id = Column(Integer, primary_key=True, server_default=text("nextval('\"ImportCostData_id_seq\"'::regclass)"))

    demand_sector = relationship(u'DemandSector')
    gau = relationship(u'GeographiesDatum')
    import_node = relationship(u'ImportCost')


class IndexLevel(Base):
    __tablename__ = 'IndexLevels'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"IndexLevels_id_seq\"'::regclass)"))
    index_level = Column(Text)
    data_column_name = Column(Text)


class InflationConversion(Base):
    __tablename__ = 'InflationConversion'

    currency_year_id = Column(ForeignKey(u'CurrencyYears.id'))
    currency_id = Column(ForeignKey(u'Currencies.id'))
    value = Column(Float(53))
    id = Column(Integer, primary_key=True, server_default=text("nextval('\"InflationConversion_id_seq\"'::regclass)"))

    currency = relationship(u'Currency')
    currency_year = relationship(u'CurrencyYear')


class InputType(Base):
    __tablename__ = 'InputTypes'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"InputTypes_id_seq\"'::regclass)"))
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


class PrimaryCostDatum(Base):
    __tablename__ = 'PrimaryCostData'

    primary_node_id = Column(ForeignKey(u'SupplyNodes.id'))
    gau_id = Column(ForeignKey(u'GeographiesData.id'))
    demand_sector_id = Column(ForeignKey(u'DemandSectors.id'))
    oth_1_id = Column(ForeignKey(u'OtherIndexesData.id'))
    resource_bins = Column(Integer)
    year = Column(Integer)
    value = Column(Float(53))
    id = Column(Integer, primary_key=True, server_default=text("nextval('\"PrimaryCostData_id_seq\"'::regclass)"))

    demand_sector = relationship(u'DemandSector')
    gau = relationship(u'GeographiesDatum')
    oth_1 = relationship(u'OtherIndexesDatum')
    primary_node = relationship(u'SupplyNode')


class Scenario(Base):
    __tablename__ = 'Scenarios'

    id = Column(Integer, primary_key=True)
    name = Column(Text)
    demand_case = Column(Text)
    supply_case = Column(Text)
    is_active = Column(Boolean)


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


class ShapesDatum(Base):
    __tablename__ = 'ShapesData'

    parent_id = Column(Integer)
    gau_id = Column(ForeignKey(u'GeographiesData.id'))
    dispatch_feeder = Column(ForeignKey(u'DispatchFeeders.id'))
    timeshift_type = Column(ForeignKey(u'FlexibleLoadShiftTypes.id'))
    resource_bin = Column(Integer)
    dispatch_constraint_id = Column(Integer)
    year = Column(Integer)
    month = Column(Integer)
    week = Column(Integer)
    hour = Column(Integer)
    day_type_id = Column(ForeignKey(u'DayType.id'))
    weather_datetime = Column(Text)
    value = Column(Float)
    id = Column(Integer, primary_key=True, server_default=text("nextval('\"ShapesData_id_seq\"'::regclass)"))

    day_type = relationship(u'DayType')
    DispatchFeeder = relationship(u'DispatchFeeder')
    gau = relationship(u'GeographiesDatum')
    FlexibleLoadShiftType = relationship(u'FlexibleLoadShiftType')


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


class StorageTechsEnergyCapitalCostNewDatum(Base):
    __tablename__ = 'StorageTechsEnergyCapitalCostNewData'

    supply_tech_id = Column(ForeignKey(u'SupplyTechs.id'))
    gau_id = Column(ForeignKey(u'GeographiesData.id'))
    oth_1_id = Column(ForeignKey(u'OtherIndexesData.id'))
    oth_2_id = Column(ForeignKey(u'OtherIndexesData.id'))
    vintage = Column(Integer)
    value = Column(Float)
    id = Column(Integer, primary_key=True, server_default=text("nextval('\"StorageTechsEnergyCapitalCostNewData_id_seq\"'::regclass)"))

    gau = relationship(u'GeographiesDatum')
    oth_1 = relationship(u'OtherIndexesDatum', primaryjoin='StorageTechsEnergyCapitalCostNewDatum.oth_1_id == OtherIndexesDatum.id')
    oth_2 = relationship(u'OtherIndexesDatum', primaryjoin='StorageTechsEnergyCapitalCostNewDatum.oth_2_id == OtherIndexesDatum.id')
    supply_tech = relationship(u'SupplyTech')


class StorageTechsEnergyCapitalCostReplacementDatum(Base):
    __tablename__ = 'StorageTechsEnergyCapitalCostReplacementData'

    supply_tech_id = Column(ForeignKey(u'SupplyTechs.id'))
    gau_id = Column(ForeignKey(u'GeographiesData.id'))
    oth_1_id = Column(ForeignKey(u'OtherIndexesData.id'))
    oth_2_id = Column(ForeignKey(u'OtherIndexesData.id'))
    vintage = Column(Integer)
    value = Column(Float)
    id = Column(Integer, primary_key=True, server_default=text("nextval('\"StorageTechsEnergyCapitalCostReplacementData_id_seq\"'::regclass)"))

    gau = relationship(u'GeographiesDatum')
    oth_1 = relationship(u'OtherIndexesDatum', primaryjoin='StorageTechsEnergyCapitalCostReplacementDatum.oth_1_id == OtherIndexesDatum.id')
    oth_2 = relationship(u'OtherIndexesDatum', primaryjoin='StorageTechsEnergyCapitalCostReplacementDatum.oth_2_id == OtherIndexesDatum.id')
    supply_tech = relationship(u'SupplyTech')


class SupplyCapacityFactorDatum(Base):
    __tablename__ = 'SupplyCapacityFactorData'

    supply_node_id = Column(ForeignKey(u'SupplyCapacityFactor.supply_node_id'))
    gau_id = Column(ForeignKey(u'GeographiesData.id'))
    demand_sector = Column(Integer)
    resource_bins = Column(Integer)
    year = Column(Integer)
    value = Column(Float(53))
    id = Column(Integer, primary_key=True, server_default=text("nextval('\"SupplyCapacityFactorData_id_seq\"'::regclass)"))

    gau = relationship(u'GeographiesDatum')
    supply_node = relationship(u'SupplyCapacityFactor')


class SupplyCase(Base):
    __tablename__ = 'SupplyCases'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"SupplyCases_id_seq\"'::regclass)"))
    name = Column(Text)


class SupplyCasesDatum(Base):
    __tablename__ = 'SupplyCasesData'

    parent_id = Column(ForeignKey(u'SupplyCases.id'))
    supply_node_id = Column(ForeignKey(u'SupplyNodes.id'))
    blend_package_id = Column(ForeignKey(u'BlendNodeBlendMeasurePackages.id'))
    export_package_id = Column(ForeignKey(u'SupplyExportMeasurePackages.id'))
    stock_package_id = Column(ForeignKey(u'SupplyStockMeasurePackages.id'))
    sales_package_id = Column(ForeignKey(u'SupplySalesMeasurePackages.id'))
    sales_share_package_id = Column(ForeignKey(u'SupplySalesShareMeasurePackages.id'))
    id = Column(Integer, primary_key=True, server_default=text("nextval('\"SupplyCasesData_id_seq\"'::regclass)"))

    blend_package = relationship(u'BlendNodeBlendMeasurePackage')
    export_package = relationship(u'SupplyExportMeasurePackage')
    parent = relationship(u'SupplyCase')
    sales_package = relationship(u'SupplySalesMeasurePackage')
    sales_share_package = relationship(u'SupplySalesShareMeasurePackage')
    stock_package = relationship(u'SupplyStockMeasurePackage')
    supply_node = relationship(u'SupplyNode')


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


class SupplyCostDatum(Base):
    __tablename__ = 'SupplyCostData'

    parent_id = Column(ForeignKey(u'SupplyCost.id'))
    gau_id = Column(ForeignKey(u'GeographiesData.id'))
    demand_sector_id = Column(ForeignKey(u'DemandSectors.id'))
    resource_bins = Column(Integer)
    year = Column(Integer)
    value = Column(Float(53))
    id = Column(Integer, primary_key=True, server_default=text("nextval('\"SupplyCostData_id_seq\"'::regclass)"))

    demand_sector = relationship(u'DemandSector')
    gau = relationship(u'GeographiesDatum')
    parent = relationship(u'SupplyCost')


class SupplyCostType(Base):
    __tablename__ = 'SupplyCostTypes'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"SupplyCostTypes_id_seq\"'::regclass)"))
    name = Column(Text)


class SupplyEfficiencyDatum(Base):
    __tablename__ = 'SupplyEfficiencyData'

    parent_id = Column(ForeignKey(u'SupplyEfficiency.id'))
    gau_id = Column(ForeignKey(u'GeographiesData.id'))
    efficiency_type_id = Column(ForeignKey(u'EfficiencyTypes.id'))
    demand_sector_id = Column(ForeignKey(u'DemandSectors.id'))
    supply_node_id = Column(ForeignKey(u'SupplyNodes.id'))
    resource_bins = Column(Integer)
    year = Column(Integer)
    value = Column(Float(53))
    id = Column(Integer, primary_key=True, server_default=text("nextval('\"SupplyEfficiencyData_id_seq\"'::regclass)"))

    demand_sector = relationship(u'DemandSector')
    efficiency_type = relationship(u'EfficiencyType')
    gau = relationship(u'GeographiesDatum')
    parent = relationship(u'SupplyEfficiency')
    supply_node = relationship(u'SupplyNode')


class SupplyEmissionsDatum(Base):
    __tablename__ = 'SupplyEmissionsData'

    supply_node_id = Column(ForeignKey(u'SupplyNodes.id'))
    gau_id = Column(ForeignKey(u'GeographiesData.id'))
    demand_sector_id = Column(ForeignKey(u'DemandSectors.id'))
    oth_1_id = Column(ForeignKey(u'OtherIndexes.id'))
    ghg_type_id = Column(ForeignKey(u'GreenhouseGasEmissionsType.id'))
    ghg_id = Column(ForeignKey(u'GreenhouseGases.id'))
    year = Column(Integer)
    value = Column(Float(53))
    id = Column(Integer, primary_key=True, server_default=text("nextval('\"PrimaryEmissionsData_id_seq\"'::regclass)"))

    demand_sector = relationship(u'DemandSector')
    gau = relationship(u'GeographiesDatum')
    ghg = relationship(u'GreenhouseGase')
    ghg_type = relationship(u'GreenhouseGasEmissionsType')
    oth_1 = relationship(u'OtherIndex')
    supply_node = relationship(u'SupplyNode')


class SupplyExportDatum(Base):
    __tablename__ = 'SupplyExportData'

    supply_node_id = Column(ForeignKey(u'SupplyExport.supply_node_id', onupdate=u'CASCADE'))
    gau_id = Column(ForeignKey(u'GeographiesData.id'))
    oth_1_id = Column(ForeignKey(u'OtherIndexes.id'))
    resource_bins = Column(Integer)
    year = Column(Integer)
    value = Column(Float(53))
    id = Column(Integer, primary_key=True, server_default=text("nextval('\"SupplyExportData_id_seq\"'::regclass)"))

    gau = relationship(u'GeographiesDatum')
    oth_1 = relationship(u'OtherIndex')
    supply_node = relationship(u'SupplyExport')


class SupplyExportMeasurePackage(Base):
    __tablename__ = 'SupplyExportMeasurePackages'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"SupplyExportMeasurePackages_id_seq\"'::regclass)"))
    name = Column(Text)
    supply_node_id = Column(ForeignKey(u'SupplyNodes.id'))

    supply_node = relationship(u'SupplyNode')


class SupplyExportMeasurePackagesDatum(Base):
    __tablename__ = 'SupplyExportMeasurePackagesData'

    package_id = Column(ForeignKey(u'SupplyExportMeasurePackages.id'))
    measure_id = Column(ForeignKey(u'SupplyExportMeasures.id'))
    id = Column(Integer, primary_key=True, server_default=text("nextval('\"SupplyExportMeasurePackagesData_id_seq\"'::regclass)"))

    measure = relationship(u'SupplyExportMeasure')
    package = relationship(u'SupplyExportMeasurePackage')


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


class SupplyExportMeasuresDatum(Base):
    __tablename__ = 'SupplyExportMeasuresData'

    parent_id = Column(ForeignKey(u'SupplyExportMeasures.id'))
    gau_id = Column(ForeignKey(u'GeographiesData.id'))
    oth_1_id = Column(ForeignKey(u'OtherIndexesData.id'))
    year = Column(Integer)
    value = Column(Float)
    id = Column(Integer, primary_key=True, server_default=text("nextval('\"SupplyExportMeasuresData_id_seq\"'::regclass)"))

    gau = relationship(u'GeographiesDatum')
    oth_1 = relationship(u'OtherIndexesDatum')
    parent = relationship(u'SupplyExportMeasure')


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
    is_flexible = Column(Integer)
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


class SupplySale(SupplyNode):
    __tablename__ = 'SupplySales'

    supply_node_id = Column(ForeignKey(u'SupplyNodes.id'), primary_key=True)
    geography_id = Column(ForeignKey(u'Geographies.id'))
    capacity_or_energy_unit = Column(Text)
    time_unit = Column(Text)
    interpolation_method = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_method = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_growth = Column(Float)

    CleaningMethod = relationship(u'CleaningMethod', primaryjoin='SupplySale.extrapolation_method == CleaningMethod.id')
    geography = relationship(u'Geography')
    CleaningMethod1 = relationship(u'CleaningMethod', primaryjoin='SupplySale.interpolation_method == CleaningMethod.id')


class SupplyEfficiency(SupplyNode):
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
    interpolation_method = relationship(u'CleaningMethod', primaryjoin='SupplyEfficiency.interpolation_method_id == CleaningMethod.id')


class DispatchNodeConfig(SupplyNode):
    __tablename__ = 'DispatchNodeConfig'

    supply_node_id = Column(ForeignKey(u'SupplyNodes.id'), primary_key=True)
    dispatch_order = Column(Integer, unique=True)
    dispatch_window_id = Column(ForeignKey(u'DispatchWindows.id'))
    geography_id = Column(ForeignKey(u'Geographies.id'))

    dispatch_window = relationship(u'DispatchWindow')
    geography = relationship(u'Geography')


class PrimaryCost(SupplyNode):
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


class SupplyEmission(SupplyNode):
    __tablename__ = 'SupplyEmissions'

    supply_node_id = Column(ForeignKey(u'SupplyNodes.id'), primary_key=True)
    geography_id = Column(ForeignKey(u'Geographies.id'))
    other_index_1_id = Column(Integer)
    mass_unit = Column(Text)
    denominator_unit = Column(Text)
    interpolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_growth = Column(Float)
    source = Column(Text)
    notes = Column(Text)

    extrapolation_method = relationship(u'CleaningMethod', primaryjoin='SupplyEmission.extrapolation_method_id == CleaningMethod.id')
    geography = relationship(u'Geography')
    interpolation_method = relationship(u'CleaningMethod', primaryjoin='SupplyEmission.interpolation_method_id == CleaningMethod.id')


class SupplySalesShare(SupplyNode):
    __tablename__ = 'SupplySalesShare'

    supply_node_id = Column(ForeignKey(u'SupplyNodes.id'), primary_key=True)
    geography_id = Column(ForeignKey(u'Geographies.id'))
    interpolation_method = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_method = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_growth = Column(Float)

    CleaningMethod = relationship(u'CleaningMethod', primaryjoin='SupplySalesShare.extrapolation_method == CleaningMethod.id')
    geography = relationship(u'Geography')
    CleaningMethod1 = relationship(u'CleaningMethod', primaryjoin='SupplySalesShare.interpolation_method == CleaningMethod.id')


class SupplyExport(SupplyNode):
    __tablename__ = 'SupplyExport'

    supply_node_id = Column(ForeignKey(u'SupplyNodes.id', onupdate=u'CASCADE'), primary_key=True)
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


class ImportCost(SupplyNode):
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
    interpolation_method = relationship(u'CleaningMethod', primaryjoin='ImportCost.interpolation_method_id == CleaningMethod.id')


class SupplyCapacityFactor(SupplyNode):
    __tablename__ = 'SupplyCapacityFactor'

    supply_node_id = Column(ForeignKey(u'SupplyNodes.id'), primary_key=True)
    geography_id = Column(ForeignKey(u'Geographies.id'))
    unit = Column(Text)
    interpolation_method = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_method = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_growth = Column(Float)
    age_growth_or_decay_type_id = Column(Integer)
    age_growth_or_decay = Column(Float)

    CleaningMethod = relationship(u'CleaningMethod', primaryjoin='SupplyCapacityFactor.extrapolation_method == CleaningMethod.id')
    geography = relationship(u'Geography')
    CleaningMethod1 = relationship(u'CleaningMethod', primaryjoin='SupplyCapacityFactor.interpolation_method == CleaningMethod.id')


class SupplyPotentialConversion(SupplyNode):
    __tablename__ = 'SupplyPotentialConversion'

    supply_node_id = Column(ForeignKey(u'SupplyNodes.id'), primary_key=True)
    geography_id = Column(ForeignKey(u'Geographies.id'))
    other_index_1_id = Column(ForeignKey(u'OtherIndexes.id'))
    energy_unit_numerator = Column(Text)
    resource_unit_denominator = Column(Text)
    interpolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_method_id = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_growth = Column(Float)

    extrapolation_method = relationship(u'CleaningMethod', primaryjoin='SupplyPotentialConversion.extrapolation_method_id == CleaningMethod.id')
    geography = relationship(u'Geography')
    interpolation_method = relationship(u'CleaningMethod', primaryjoin='SupplyPotentialConversion.interpolation_method_id == CleaningMethod.id')
    other_index_1 = relationship(u'OtherIndex')


class SupplyPotential(SupplyNode):
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


class SupplyStock(SupplyNode):
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


class SupplyPotentialConversionDatum(Base):
    __tablename__ = 'SupplyPotentialConversionData'

    supply_node_id = Column(ForeignKey(u'SupplyPotentialConversion.supply_node_id'))
    gau_id = Column(ForeignKey(u'GeographiesData.id'))
    oth_1_id = Column(ForeignKey(u'OtherIndexesData.id'))
    resource_bins = Column(Integer)
    year = Column(Integer)
    value = Column(Float(53))
    id = Column(Integer, primary_key=True, server_default=text("nextval('\"PrimaryPotentialConversionData_id_seq\"'::regclass)"))

    gau = relationship(u'GeographiesDatum')
    oth_1 = relationship(u'OtherIndexesDatum')
    supply_node = relationship(u'SupplyPotentialConversion')


class SupplyPotentialDatum(Base):
    __tablename__ = 'SupplyPotentialData'

    supply_node_id = Column(ForeignKey(u'SupplyPotential.supply_node_id'))
    gau_id = Column(ForeignKey(u'GeographiesData.id'))
    demand_sector = Column(ForeignKey(u'DemandSectors.id'))
    oth_1_id = Column(ForeignKey(u'OtherIndexesData.id'))
    resource_bins = Column(Integer)
    year = Column(Integer)
    value = Column(Float(53))
    id = Column(Integer, primary_key=True, server_default=text("nextval('\"SupplyPotentialData_id_seq\"'::regclass)"))

    DemandSector = relationship(u'DemandSector')
    gau = relationship(u'GeographiesDatum')
    oth_1 = relationship(u'OtherIndexesDatum')
    supply_node = relationship(u'SupplyPotential')


class SupplySalesDatum(Base):
    __tablename__ = 'SupplySalesData'

    supply_node_id = Column(ForeignKey(u'SupplySales.supply_node_id'))
    gau_id = Column(ForeignKey(u'GeographiesData.id'))
    demand_sector = Column(ForeignKey(u'DemandSectors.id'))
    supply_technology = Column(ForeignKey(u'SupplyTechs.id'))
    vintage = Column(Integer)
    value = Column(Float(53))
    id = Column(Integer, primary_key=True, server_default=text("nextval('\"SupplySalesData_id_seq\"'::regclass)"))

    DemandSector = relationship(u'DemandSector')
    gau = relationship(u'GeographiesDatum')
    supply_node = relationship(u'SupplySale')
    SupplyTech = relationship(u'SupplyTech')


class SupplySalesMeasurePackage(Base):
    __tablename__ = 'SupplySalesMeasurePackages'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"SupplySalesMeasurePackages_id_seq\"'::regclass)"))
    name = Column(Text)
    supply_node_id = Column(ForeignKey(u'SupplyNodes.id'))

    supply_node = relationship(u'SupplyNode')


class SupplySalesMeasurePackagesDatum(Base):
    __tablename__ = 'SupplySalesMeasurePackagesData'

    package_id = Column(ForeignKey(u'SupplySalesMeasurePackages.id'))
    measure_id = Column(ForeignKey(u'SupplyTechs.id'))
    id = Column(Integer, primary_key=True, server_default=text("nextval('\"SupplySalesMeasurePackagesData_id_seq\"'::regclass)"))

    measure = relationship(u'SupplyTech')
    package = relationship(u'SupplySalesMeasurePackage')


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
    interpolation_method = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_method = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_growth = Column(Float)

    CleaningMethod = relationship(u'CleaningMethod', primaryjoin='SupplySalesMeasure.extrapolation_method == CleaningMethod.id')
    geography = relationship(u'Geography')
    CleaningMethod1 = relationship(u'CleaningMethod', primaryjoin='SupplySalesMeasure.interpolation_method == CleaningMethod.id')
    other_index_1 = relationship(u'OtherIndex')
    supply_node = relationship(u'SupplyNode')
    supply_technology = relationship(u'SupplyTech')


class SupplySalesMeasuresDatum(Base):
    __tablename__ = 'SupplySalesMeasuresData'

    parent_id = Column(ForeignKey(u'SupplySalesMeasures.id'))
    gau_id = Column(ForeignKey(u'GeographiesData.id'))
    oth_1_id = Column(ForeignKey(u'OtherIndexes.id'))
    demand_sector_id = Column(ForeignKey(u'DemandSectors.id'))
    resource_bins = Column(Integer)
    vintage = Column(Integer)
    value = Column(Float(53))
    id = Column(Integer, primary_key=True, server_default=text("nextval('\"SupplySalesMeasuresData_id_seq\"'::regclass)"))

    demand_sector = relationship(u'DemandSector')
    gau = relationship(u'GeographiesDatum')
    oth_1 = relationship(u'OtherIndex')
    parent = relationship(u'SupplySalesMeasure')


class SupplySalesShareDatum(Base):
    __tablename__ = 'SupplySalesShareData'

    supply_node_id = Column(ForeignKey(u'SupplyNodes.id'))
    gau_id = Column(ForeignKey(u'GeographiesData.id'))
    demand_sector = Column(ForeignKey(u'DemandSectors.id'))
    supply_technology = Column(ForeignKey(u'SupplyTechs.id'))
    vintage = Column(Integer)
    value = Column(Float(53))
    id = Column(Integer, primary_key=True, server_default=text("nextval('\"SupplySalesShareData_id_seq\"'::regclass)"))

    DemandSector = relationship(u'DemandSector')
    gau = relationship(u'GeographiesDatum')
    supply_node = relationship(u'SupplyNode')
    SupplyTech = relationship(u'SupplyTech')


class SupplySalesShareMeasurePackage(Base):
    __tablename__ = 'SupplySalesShareMeasurePackages'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"SupplySalesShareMeasurePackages_id_seq\"'::regclass)"))
    name = Column(Text)
    supply_node_id = Column(ForeignKey(u'SupplyNodes.id'))

    supply_node = relationship(u'SupplyNode')


class SupplySalesShareMeasurePackagesDatum(Base):
    __tablename__ = 'SupplySalesShareMeasurePackagesData'

    package_id = Column(ForeignKey(u'SupplySalesShareMeasurePackages.id'))
    measure_id = Column(ForeignKey(u'SupplySalesShareMeasures.id'))
    id = Column(Integer, primary_key=True, server_default=text("nextval('\"SupplySalesShareMeasurePackagesData_id_seq\"'::regclass)"))

    measure = relationship(u'SupplySalesShareMeasure')
    package = relationship(u'SupplySalesShareMeasurePackage')


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
    interpolation_method = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_method = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_growth = Column(Float)

    CleaningMethod = relationship(u'CleaningMethod', primaryjoin='SupplySalesShareMeasure.extrapolation_method == CleaningMethod.id')
    geography = relationship(u'Geography')
    CleaningMethod1 = relationship(u'CleaningMethod', primaryjoin='SupplySalesShareMeasure.interpolation_method == CleaningMethod.id')
    replaced_supply_technology = relationship(u'SupplyTech', primaryjoin='SupplySalesShareMeasure.replaced_supply_technology_id == SupplyTech.id')
    supply_node = relationship(u'SupplyNode')
    supply_technology = relationship(u'SupplyTech', primaryjoin='SupplySalesShareMeasure.supply_technology_id == SupplyTech.id')


class SupplySalesShareMeasuresDatum(Base):
    __tablename__ = 'SupplySalesShareMeasuresData'

    parent_id = Column(ForeignKey(u'SupplySalesShareMeasures.id'))
    gau_id = Column(ForeignKey(u'GeographiesData.id'))
    demand_sector_id = Column(ForeignKey(u'DemandSectors.id'))
    vintage = Column(Integer)
    value = Column(Float(53))
    id = Column(Integer, primary_key=True, server_default=text("nextval('\"SupplySalesShareMeasuresData_id_seq\"'::regclass)"))

    demand_sector = relationship(u'DemandSector')
    gau = relationship(u'GeographiesDatum')
    parent = relationship(u'SupplySalesShareMeasure')


class SupplyStockDatum(Base):
    __tablename__ = 'SupplyStockData'

    supply_node_id = Column(ForeignKey(u'SupplyNodes.id'))
    gau_id = Column(ForeignKey(u'GeographiesData.id'))
    demand_sector = Column(ForeignKey(u'DemandSectors.id'))
    supply_technology = Column(ForeignKey(u'SupplyTechs.id'))
    resource_bins = Column(Integer)
    year = Column(Integer)
    value = Column(Float(53))
    id = Column(Integer, primary_key=True, server_default=text("nextval('\"SupplyStockData_id_seq\"'::regclass)"))

    DemandSector = relationship(u'DemandSector')
    gau = relationship(u'GeographiesDatum')
    supply_node = relationship(u'SupplyNode')
    SupplyTech = relationship(u'SupplyTech')


class SupplyStockMeasurePackage(Base):
    __tablename__ = 'SupplyStockMeasurePackages'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"SupplyStockMeasurePackages_id_seq\"'::regclass)"))
    name = Column(Text)
    supply_node_id = Column(ForeignKey(u'SupplyNodes.id'))

    supply_node = relationship(u'SupplyNode')


class SupplyStockMeasurePackagesDatum(Base):
    __tablename__ = 'SupplyStockMeasurePackagesData'

    package_id = Column(ForeignKey(u'SupplyStockMeasurePackages.id'))
    measure_id = Column(ForeignKey(u'SupplyStockMeasures.id'))
    id = Column(Integer, primary_key=True, server_default=text("nextval('\"SupplyStockMeasurePackagesData_id_seq\"'::regclass)"))

    measure = relationship(u'SupplyStockMeasure')
    package = relationship(u'SupplyStockMeasurePackage')


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
    interpolation_method = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_method = Column(ForeignKey(u'CleaningMethods.id'))
    extrapolation_growth = Column(Float)

    CleaningMethod = relationship(u'CleaningMethod', primaryjoin='SupplyStockMeasure.extrapolation_method == CleaningMethod.id')
    geography = relationship(u'Geography')
    CleaningMethod1 = relationship(u'CleaningMethod', primaryjoin='SupplyStockMeasure.interpolation_method == CleaningMethod.id')
    other_index_1 = relationship(u'OtherIndex')
    supply_node = relationship(u'SupplyNode')
    supply_technology = relationship(u'SupplyTech')


class SupplyStockMeasuresDatum(Base):
    __tablename__ = 'SupplyStockMeasuresData'

    parent_id = Column(ForeignKey(u'SupplyStockMeasures.id'))
    gau_id = Column(ForeignKey(u'GeographiesData.id'))
    oth_1_id = Column(ForeignKey(u'OtherIndexes.id'))
    demand_sector_id = Column(ForeignKey(u'DemandSectors.id'))
    year = Column(Integer)
    value = Column(Float(53))
    id = Column(Integer, primary_key=True, server_default=text("nextval('\"SupplyStockMeasuresData_id_seq\"'::regclass)"))

    demand_sector = relationship(u'DemandSector')
    gau = relationship(u'GeographiesDatum')
    oth_1 = relationship(u'OtherIndex')
    parent = relationship(u'SupplyStockMeasure')


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


class SupplyTechsFixedMaintenanceCost(SupplyTech):
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


class SupplyTechsInstallationCost(SupplyTech):
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


class StorageTechsCapacityCapitalCost(SupplyTech):
    __tablename__ = 'StorageTechsCapacityCapitalCost'

    supply_tech_id = Column(ForeignKey(u'SupplyTechs.id'), primary_key=True)
    definition_id = Column(ForeignKey(u'Definitions.id'))
    reference_tech_id = Column(ForeignKey(u'StorageTechsCapacityCapitalCost.supply_tech_id'))
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
    reference_tech = relationship(u'StorageTechsCapacityCapitalCost', remote_side=[supply_tech_id])


class StorageTechsCapacityCapitalCostNewDatum(SupplyTech):
    __tablename__ = 'StorageTechsCapacityCapitalCostNewData'

    supply_tech_id = Column(ForeignKey(u'SupplyTechs.id'), primary_key=True)
    gau_id = Column(ForeignKey(u'GeographiesData.id'))
    oth_1_id = Column(ForeignKey(u'OtherIndexesData.id'))
    oth_2_id = Column(ForeignKey(u'OtherIndexesData.id'))
    vintage = Column(Integer)
    value = Column(Float)

    gau = relationship(u'GeographiesDatum')
    oth_1 = relationship(u'OtherIndexesDatum', primaryjoin='StorageTechsCapacityCapitalCostNewDatum.oth_1_id == OtherIndexesDatum.id')
    oth_2 = relationship(u'OtherIndexesDatum', primaryjoin='StorageTechsCapacityCapitalCostNewDatum.oth_2_id == OtherIndexesDatum.id')


class SupplyTechsCO2Capture(SupplyTech):
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


class SupplyTechsCapitalCost(SupplyTech):
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


class SupplyTechsVariableMaintenanceCost(SupplyTech):
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


class SupplyTechsCO2CaptureDatum(SupplyTech):
    __tablename__ = 'SupplyTechsCO2CaptureData'

    supply_tech_id = Column(ForeignKey(u'SupplyTechs.id'), primary_key=True)
    gau_id = Column(ForeignKey(u'GeographiesData.id'))
    resource_bin = Column(Integer)
    vintage = Column(Integer)
    value = Column(Float(53))

    gau = relationship(u'GeographiesDatum')


class SupplyTechsCapacityFactor(SupplyTech):
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


class StorageTechsCapacityCapitalCostReplacementDatum(SupplyTech):
    __tablename__ = 'StorageTechsCapacityCapitalCostReplacementData'

    supply_tech_id = Column(ForeignKey(u'SupplyTechs.id'), primary_key=True)
    gau_id = Column(ForeignKey(u'GeographiesData.id'))
    oth_1_id = Column(ForeignKey(u'OtherIndexesData.id'))
    oth_2_id = Column(ForeignKey(u'OtherIndexesData.id'))
    vintage = Column(Integer)
    value = Column(Float)

    gau = relationship(u'GeographiesDatum')
    oth_1 = relationship(u'OtherIndexesDatum', primaryjoin='StorageTechsCapacityCapitalCostReplacementDatum.oth_1_id == OtherIndexesDatum.id')
    oth_2 = relationship(u'OtherIndexesDatum', primaryjoin='StorageTechsCapacityCapitalCostReplacementDatum.oth_2_id == OtherIndexesDatum.id')


class StorageTechsEnergyCapitalCost(SupplyTech):
    __tablename__ = 'StorageTechsEnergyCapitalCost'

    supply_tech_id = Column(ForeignKey(u'SupplyTechs.id'), primary_key=True)
    tech_name = Column(Text, unique=True)
    definition_id = Column(ForeignKey(u'Definitions.id'))
    reference_tech_id = Column(ForeignKey(u'StorageTechsEnergyCapitalCost.supply_tech_id'))
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
    reference_tech = relationship(u'StorageTechsEnergyCapitalCost', remote_side=[supply_tech_id])


class SupplyTechsEfficiency(SupplyTech):
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


class SupplyTechsCapacityFactorDatum(Base):
    __tablename__ = 'SupplyTechsCapacityFactorData'

    supply_tech_id = Column(ForeignKey(u'SupplyTechs.id'))
    gau_id = Column(ForeignKey(u'GeographiesData.id'))
    oth_1_id = Column(ForeignKey(u'OtherIndexes.id'))
    resource_bins = Column(Integer)
    vintage = Column(Integer)
    value = Column(Float(53))
    id = Column(Integer, primary_key=True, server_default=text("nextval('\"SupplyTechsCapacityFactorData_id_seq\"'::regclass)"))

    gau = relationship(u'GeographiesDatum')
    oth_1 = relationship(u'OtherIndex')
    supply_tech = relationship(u'SupplyTech')


class SupplyTechsCapitalCostNewDatum(Base):
    __tablename__ = 'SupplyTechsCapitalCostNewData'

    supply_tech_id = Column(ForeignKey(u'SupplyTechs.id'))
    gau_id = Column(ForeignKey(u'GeographiesData.id'))
    demand_sector_id = Column(ForeignKey(u'DemandSectors.id'))
    resource_bin = Column(Integer)
    vintage = Column(Integer)
    value = Column(Float(53))
    id = Column(Integer, primary_key=True, server_default=text("nextval('\"SupplyTechsCapitalCostNewData_id_seq\"'::regclass)"))

    demand_sector = relationship(u'DemandSector')
    gau = relationship(u'GeographiesDatum')
    supply_tech = relationship(u'SupplyTech')


class SupplyTechsCapitalCostReplacementDatum(Base):
    __tablename__ = 'SupplyTechsCapitalCostReplacementData'

    supply_tech_id = Column(ForeignKey(u'SupplyTechs.id'))
    gau_id = Column(ForeignKey(u'GeographiesData.id'))
    demand_sector_id = Column(ForeignKey(u'DemandSectors.id'))
    resource_bin = Column(Integer)
    vintage = Column(Integer)
    value = Column(Float(53))
    id = Column(Integer, primary_key=True, server_default=text("nextval('\"SupplyTechsCapitalCostReplacementData_id_seq\"'::regclass)"))

    demand_sector = relationship(u'DemandSector')
    gau = relationship(u'GeographiesDatum')
    supply_tech = relationship(u'SupplyTech')


class SupplyTechsEfficiencyDatum(Base):
    __tablename__ = 'SupplyTechsEfficiencyData'

    supply_tech_id = Column(ForeignKey(u'SupplyTechs.id'))
    supply_node_id = Column(ForeignKey(u'SupplyNodes.id'))
    efficiency_type_id = Column(ForeignKey(u'EfficiencyTypes.id'))
    gau_id = Column(ForeignKey(u'GeographiesData.id'))
    demand_sector_id = Column(ForeignKey(u'DemandSectors.id'))
    resource_bin = Column(Integer)
    vintage = Column(Integer)
    value = Column(Float(53))
    id = Column(Integer, primary_key=True, server_default=text("nextval('\"SupplyTechsEfficiencyData_id_seq\"'::regclass)"))

    demand_sector = relationship(u'DemandSector')
    efficiency_type = relationship(u'EfficiencyType')
    gau = relationship(u'GeographiesDatum')
    supply_node = relationship(u'SupplyNode')
    supply_tech = relationship(u'SupplyTech')


class SupplyTechsFixedMaintenanceCostDatum(Base):
    __tablename__ = 'SupplyTechsFixedMaintenanceCostData'

    supply_tech_id = Column(ForeignKey(u'SupplyTechs.id'))
    gau_id = Column(ForeignKey(u'GeographiesData.id'))
    demand_sector_id = Column(ForeignKey(u'DemandSectors.id'))
    resource_bin = Column(Integer)
    vintage = Column(Integer)
    value = Column(Float)
    id = Column(Integer, primary_key=True, server_default=text("nextval('\"SupplyTechsFixedMaintenanceCostData_id_seq\"'::regclass)"))

    demand_sector = relationship(u'DemandSector')
    gau = relationship(u'GeographiesDatum')
    supply_tech = relationship(u'SupplyTech')


class SupplyTechsInstallationCostNewDatum(Base):
    __tablename__ = 'SupplyTechsInstallationCostNewData'

    supply_tech_id = Column(ForeignKey(u'SupplyTechs.id'))
    gau_id = Column(ForeignKey(u'GeographiesData.id'))
    demand_sector_id = Column(ForeignKey(u'DemandSectors.id'))
    resource_bin = Column(Integer)
    vintage = Column(Integer)
    value = Column(Float(53))
    id = Column(Integer, primary_key=True, server_default=text("nextval('\"SupplyTechsInstallationCostNewData_id_seq\"'::regclass)"))

    demand_sector = relationship(u'DemandSector')
    gau = relationship(u'GeographiesDatum')
    supply_tech = relationship(u'SupplyTech')


class SupplyTechsInstallationCostReplacementDatum(Base):
    __tablename__ = 'SupplyTechsInstallationCostReplacementData'

    supply_tech_id = Column(ForeignKey(u'SupplyTechs.id'))
    gau_id = Column(ForeignKey(u'GeographiesData.id'))
    demand_sector_id = Column(ForeignKey(u'DemandSectors.id'))
    resource_bin = Column(Integer)
    vintage = Column(Integer)
    value = Column(Float(53))
    id = Column(Integer, primary_key=True, server_default=text("nextval('\"SupplyTechsInstallationCostReplacementData_id_seq\"'::regclass)"))

    demand_sector = relationship(u'DemandSector')
    gau = relationship(u'GeographiesDatum')
    supply_tech = relationship(u'SupplyTech')


class SupplyTechsVariableMaintenanceCostDatum(Base):
    __tablename__ = 'SupplyTechsVariableMaintenanceCostData'

    supply_tech_id = Column(ForeignKey(u'SupplyTechs.id'))
    gau_id = Column(ForeignKey(u'GeographiesData.id'))
    demand_sector_id = Column(ForeignKey(u'DemandSectors.id'))
    resource_bin = Column(Integer)
    vintage = Column(Integer)
    value = Column(Float(53))
    id = Column(Integer, primary_key=True, server_default=text("nextval('\"SupplyTechsVariableMaintenanceCostData_id_seq\"'::regclass)"))

    demand_sector = relationship(u'DemandSector')
    gau = relationship(u'GeographiesDatum')
    supply_tech = relationship(u'SupplyTech')


class SupplyType(Base):
    __tablename__ = 'SupplyTypes'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"SupplyTypes_id_seq\"'::regclass)"))
    name = Column(Text, unique=True)


class TimeZone(Base):
    __tablename__ = 'TimeZones'

    id = Column(Integer, primary_key=True, server_default=text("nextval('\"TimeZones_id_seq\"'::regclass)"))
    name = Column(Text)
    utc_shift = Column(Float(53))
