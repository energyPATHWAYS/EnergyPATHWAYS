from data_source import Base
from sqlalchemy import Column, Integer, Text, Float, ForeignKey, UniqueConstraint, text


class AgeGrowthOrDecayType(Base):
    __tablename__ = 'AgeGrowthOrDecayType'

    id = Column(Integer, primary_key=True)
    name = Column(Text, unique=True)


class CleaningMethod(Base):
    __tablename__ = 'CleaningMethods'

    id = Column(Integer, primary_key=True)
    name = Column(Text, unique=True)


class Currency(Base):
    __tablename__ = 'Currencies'

    id = Column(Integer, primary_key=True)
    name = Column(Text, unique=True)


class CurrencyConversion(Base):
    __tablename__ = 'CurrenciesConversion'

    id = Column(Integer, primary_key=True)
    currency_id = Column(ForeignKey(Currency.id))
    currency_year = Column(Integer)
    value = Column(Float(53))

    UniqueConstraint(currency_id, currency_year)


class DayType(Base):
    __tablename__ = 'DayTypes'

    id = Column(Integer, primary_key=True)
    name = Column(Text, unique=True)


class Definition(Base):
    __tablename__ = 'Definitions'

    id = Column(Integer, primary_key=True)
    name = Column(Text, unique=True)


class DemandStockUnitType(Base):
    __tablename__ = 'DemandStockUnitTypes'

    id = Column(Integer, primary_key=True)
    name = Column(Text, unique=True)


class DemandTechUnitType(Base):
    __tablename__ = 'DemandTechUnitTypes'

    id = Column(Integer, primary_key=True)
    name = Column(Text, unique=True)


class DispatchConstraintType(Base):
    __tablename__ = 'DispatchConstraintTypes'

    id = Column(Integer, primary_key=True)
    name = Column(Text, unique=True)


class EfficiencyType(Base):
    __tablename__ = 'EfficiencyTypes'

    id = Column(Integer, primary_key=True)
    name = Column(Text, unique=True)


class FlexibleLoadShiftType(Base):
    __tablename__ = 'FlexibleLoadShiftTypes'

    id = Column(Integer, primary_key=True)
    name = Column(Text, unique=True)


class GreenhouseGasEmissionsType(Base):
    __tablename__ = 'GreenhouseGasEmissionsType'

    id = Column(Integer, primary_key=True)
    name = Column(Text, unique=True)


class GreenhouseGas(Base):
    __tablename__ = 'GreenhouseGases'

    id = Column(Integer, primary_key=True)
    name = Column(Text, unique=True)
    long_name = Column(Text, unique=True)


class InflationConversion(Base):
    __tablename__ = 'InflationConversion'

    id = Column(Integer, primary_key=True)
    currency_id = Column(ForeignKey(Currency.id))
    currency_year = Column(Integer)
    value = Column(Float(53))

    UniqueConstraint(currency_id, currency_year)


class InputType(Base):
    __tablename__ = 'InputTypes'

    id = Column(Integer, primary_key=True)
    name = Column(Text, unique=True)


class OptPeriod(Base):
    __tablename__ = 'OptPeriods'

    id = Column(Integer, primary_key=True)
    hours = Column(Integer, unique=True)

class ShapesType(Base):
    __tablename__ = 'ShapesTypes'

    id = Column(Integer, primary_key=True)
    name = Column(Text, unique=True)


class ShapesUnit(Base):
    __tablename__ = 'ShapesUnits'

    id = Column(Integer, primary_key=True)
    name = Column(Text, unique=True)


class StockDecayFunction(Base):
    __tablename__ = 'StockDecayFunctions'

    id = Column(Integer, primary_key=True)
    name = Column(Text, unique=True)


class SupplyCostType(Base):
    __tablename__ = 'SupplyCostTypes'

    id = Column(Integer, primary_key=True)
    name = Column(Text, unique=True)


class SupplyType(Base):
    __tablename__ = 'SupplyTypes'

    id = Column(Integer, primary_key=True)
    name = Column(Text, unique=True)


class TimeZone(Base):
    __tablename__ = 'TimeZones'

    id = Column(Integer, primary_key=True)
    name = Column(Text, unique=True)
    utc_shift = Column(Float(53))