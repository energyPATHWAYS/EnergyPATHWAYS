CREATE TABLE migrated."AgeGrowthOrDecayType" (
	id SERIAL NOT NULL, 
	name TEXT, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);

CREATE TABLE migrated."CleaningMethods" (
	id SERIAL NOT NULL, 
	name TEXT, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);

CREATE TABLE migrated."Currencies" (
	id SERIAL NOT NULL, 
	name TEXT, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);

CREATE TABLE migrated."Definitions" (
	id SERIAL NOT NULL, 
	name TEXT, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);

CREATE TABLE migrated."DemandSectors" (
	id SERIAL NOT NULL, 
	name TEXT, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);

CREATE TABLE migrated."DemandStockUnitTypes" (
	id SERIAL NOT NULL, 
	name TEXT, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);

CREATE TABLE migrated."DemandTechUnitTypes" (
	id SERIAL NOT NULL, 
	name TEXT, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);

CREATE TABLE migrated."EfficiencyTypes" (
	id SERIAL NOT NULL, 
	name TEXT, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);

CREATE TABLE migrated."Geographies" (
	id SERIAL NOT NULL, 
	name TEXT, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);

CREATE TABLE migrated."GeographyMapKeys" (
	id SERIAL NOT NULL, 
	name TEXT, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);

CREATE TABLE migrated."GreenhouseGasEmissionsType" (
	id SERIAL NOT NULL, 
	name TEXT, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);

CREATE TABLE migrated."GreenhouseGases" (
	id SERIAL NOT NULL, 
	name TEXT, 
	long_name TEXT, 
	PRIMARY KEY (id), 
	UNIQUE (name), 
	UNIQUE (long_name)
);

CREATE TABLE migrated."InputTypes" (
	id SERIAL NOT NULL, 
	name TEXT, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);

CREATE TABLE migrated."OptPeriods" (
	id SERIAL NOT NULL, 
	hours INTEGER, 
	PRIMARY KEY (id), 
	UNIQUE (hours)
);

CREATE TABLE migrated."OtherIndexes" (
	id SERIAL NOT NULL, 
	name TEXT, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);

CREATE TABLE migrated."ShapesTypes" (
	id SERIAL NOT NULL, 
	name TEXT, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);

CREATE TABLE migrated."ShapesUnits" (
	id SERIAL NOT NULL, 
	name TEXT, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);

CREATE TABLE migrated."StockDecayFunctions" (
	id SERIAL NOT NULL, 
	name TEXT, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);

CREATE TABLE migrated."SupplyCostTypes" (
	id SERIAL NOT NULL, 
	name TEXT, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);

CREATE TABLE migrated."SupplyTypes" (
	id SERIAL NOT NULL, 
	name TEXT, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);

CREATE TABLE migrated."CurrenciesConversion" (
	currency_id INTEGER NOT NULL, 
	currency_year INTEGER NOT NULL, 
	value FLOAT(53), 
	PRIMARY KEY (currency_id, currency_year), 
	FOREIGN KEY(currency_id) REFERENCES migrated."Currencies" (id)
);

CREATE TABLE migrated."DemandDrivers" (
	id SERIAL NOT NULL, 
	name TEXT, 
	base_driver_id INTEGER, 
	input_type_id INTEGER, 
	unit_prefix INTEGER, 
	unit_base TEXT, 
	geography_id INTEGER, 
	other_index_1_id INTEGER, 
	other_index_2_id INTEGER, 
	geography_map_key_id INTEGER, 
	interpolation_method_id INTEGER, 
	extrapolation_method_id INTEGER, 
	extrapolation_growth FLOAT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(base_driver_id) REFERENCES migrated."DemandDrivers" (id), 
	FOREIGN KEY(input_type_id) REFERENCES migrated."InputTypes" (id), 
	FOREIGN KEY(geography_id) REFERENCES migrated."Geographies" (id), 
	FOREIGN KEY(other_index_1_id) REFERENCES migrated."OtherIndexes" (id), 
	FOREIGN KEY(other_index_2_id) REFERENCES migrated."OtherIndexes" (id), 
	FOREIGN KEY(geography_map_key_id) REFERENCES migrated."GeographyMapKeys" (id), 
	FOREIGN KEY(interpolation_method_id) REFERENCES migrated."CleaningMethods" (id), 
	FOREIGN KEY(extrapolation_method_id) REFERENCES migrated."CleaningMethods" (id)
);

CREATE TABLE migrated."InflationConversion" (
	currency_id INTEGER NOT NULL, 
	currency_year INTEGER NOT NULL, 
	value FLOAT(53), 
	PRIMARY KEY (currency_id, currency_year), 
	FOREIGN KEY(currency_id) REFERENCES migrated."Currencies" (id)
);

CREATE TABLE migrated."DemandDriversData" (
	id SERIAL NOT NULL, 
	parent_id INTEGER, 
	gau_id INTEGER, 
	oth_1_id INTEGER, 
	oth_2_id INTEGER, 
	year INTEGER, 
	value FLOAT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(parent_id) REFERENCES migrated."DemandDrivers" (id)
);

