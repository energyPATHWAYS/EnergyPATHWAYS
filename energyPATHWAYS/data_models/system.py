from data_source import Base
from sqlalchemy import Column, Integer, Text, Float, ForeignKey, PrimaryKeyConstraint, text


class AgeGrowthOrDecayType(Base):
    __tablename__ = 'AgeGrowthOrDecayType'

    id = Column(Integer, primary_key=True) #, server_default=text("nextval('\"AgeGrowthOrDecayType_id_seq\"'::regclass)"))
    name = Column(Text, unique=True)


class CleaningMethod(Base):
    __tablename__ = 'CleaningMethods'

    id = Column(Integer, primary_key=True) #, server_default=text("nextval('\"CleaningMethods_id_seq\"'::regclass)"))
    name = Column(Text, unique=True)


class Currency(Base):
    __tablename__ = 'Currencies'

    id = Column(Integer, primary_key=True) #, server_default=text("nextval('\"Currencies_id_seq\"'::regclass)")
    name = Column(Text, unique=True)


class CurrencyConversion(Base):
    __tablename__ = 'CurrenciesConversion'

    currency_id = Column(ForeignKey(Currency.id), primary_key=True)
    # See http://docs.sqlalchemy.org/en/latest/changelog/migration_11.html#the-autoincrement-directive-is-no-longer-implicitly-enabled-for-a-composite-primary-key-column
    # for why this autoincrement=False is required in SQLAlchemy 1.0 (it's not reqired for the previous field
    # because it's a foreign key
    currency_year = Column(Integer, primary_key=True, autoincrement=False)
    value = Column(Float(53))


class Definition(Base):
    __tablename__ = 'Definitions'

    id = Column(Integer, primary_key=True) #, server_default=text("nextval('\"Definitions_id_seq\"'::regclass)")
    name = Column(Text, unique=True)


class DemandSector(Base):
    __tablename__ = 'DemandSectors'

    id = Column(Integer, primary_key=True) #, server_default=text("nextval('\"DemandSectors_id_seq\"'::regclass)")
    name = Column(Text, unique=True)


class DemandStockUnitType(Base):
    __tablename__ = 'DemandStockUnitTypes'

    id = Column(Integer, primary_key=True) #, server_default = text("nextval('\"DemandStockUnitTypes_id_seq\"'::regclass)")
    name = Column(Text, unique=True)


class DemandTechUnitType(Base):
    __tablename__ = 'DemandTechUnitTypes'

    id = Column(Integer, primary_key=True) #, server_default = text("nextval('\"DemandTechUnitTypes_id_seq\"'::regclass)")
    name = Column(Text, unique=True)


class EfficiencyType(Base):
    __tablename__ = 'EfficiencyTypes'

    id = Column(Integer, primary_key=True) #, server_default=text("nextval('\"EfficiencyTypes_id_seq\"'::regclass)")
    name = Column(Text, unique=True)


class GreenhouseGasEmissionsType(Base):
    __tablename__ = 'GreenhouseGasEmissionsType'

    id = Column(Integer, primary_key=True) #, server_default=text("nextval('\"GreenhouseGasEmissionsType_id_seq\"'::regclass)")
    name = Column(Text, unique=True)


class GreenhouseGas(Base):
    __tablename__ = 'GreenhouseGases'

    id = Column(Integer, primary_key=True) #, server_default=text("nextval('\"GreenhouseGases_id_seq\"'::regclass)")
    name = Column(Text, unique=True)
    long_name = Column(Text, unique=True)


class InflationConversion(Base):
    __tablename__ = 'InflationConversion'

    currency_id = Column(ForeignKey(Currency.id), primary_key=True)
    # See http://docs.sqlalchemy.org/en/latest/changelog/migration_11.html#the-autoincrement-directive-is-no-longer-implicitly-enabled-for-a-composite-primary-key-column
    # for why this autoincrement=False is required in SQLAlchemy 1.0 (it's not reqired for the previous field
    # because it's a foreign key
    currency_year = Column(Integer, primary_key=True, autoincrement=False)
    value = Column(Float(53))


class InputType(Base):
    __tablename__ = 'InputTypes'

    id = Column(Integer, primary_key=True) #, server_default=text("nextval('\"InputTypes_id_seq\"'::regclass)"))
    name = Column(Text, unique=True)


class OptPeriod(Base):
    __tablename__ = 'OptPeriods'

    id = Column(Integer, primary_key=True) #, server_default=text("nextval('\"OptPeriods_id_seq\"'::regclass)")
    hours = Column(Integer, unique=True)

class ShapesType(Base):
    __tablename__ = 'ShapesTypes'

    id = Column(Integer, primary_key=True) #, server_default=text("nextval('\"ShapesTypes_id_seq\"'::regclass)")
    name = Column(Text, unique=True)


class ShapesUnit(Base):
    __tablename__ = 'ShapesUnits'

    id = Column(Integer, primary_key=True) #, server_default=text("nextval('\"ShapesUnits_id_seq\"'::regclass)")
    name = Column(Text, unique=True)


class StockDecayFunction(Base):
    __tablename__ = 'StockDecayFunctions'

    id = Column(Integer, primary_key=True) #, server_default=text("nextval('\"StockDecayFunctions_id_seq\"'::regclass)")
    name = Column(Text, unique=True)


class SupplyCostType(Base):
    __tablename__ = 'SupplyCostTypes'

    id = Column(Integer, primary_key=True) #, server_default=text("nextval('\"SupplyCostTypes_id_seq\"'::regclass)")
    name = Column(Text, unique=True)


class SupplyType(Base):
    __tablename__ = 'SupplyTypes'

    id = Column(Integer, primary_key=True) #, server_default=text("nextval('\"SupplyTypes_id_seq\"'::regclass)")
    name = Column(Text, unique=True)