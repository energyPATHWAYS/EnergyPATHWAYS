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

CREATE TABLE migrated."DayTypes" (
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

CREATE TABLE migrated."DispatchConstraintTypes" (
	id SERIAL NOT NULL, 
	name TEXT, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);

CREATE TABLE migrated."DispatchFeeders" (
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

CREATE TABLE migrated."FlexibleLoadShiftTypes" (
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

CREATE TABLE migrated."TimeZones" (
	id SERIAL NOT NULL, 
	name TEXT, 
	utc_shift FLOAT(53), 
	PRIMARY KEY (id), 
	UNIQUE (name)
);

CREATE TABLE migrated."CurrenciesConversion" (
	id SERIAL NOT NULL, 
	currency_id INTEGER, 
	currency_year INTEGER, 
	value FLOAT(53), 
	PRIMARY KEY (id), 
	UNIQUE (currency_id, currency_year), 
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

CREATE TABLE migrated."GeographiesData" (
	id SERIAL NOT NULL, 
	name TEXT, 
	geography_id INTEGER, 
	PRIMARY KEY (id), 
	UNIQUE (geography_id, name), 
	FOREIGN KEY(geography_id) REFERENCES migrated."Geographies" (id)
);

CREATE TABLE migrated."InflationConversion" (
	id SERIAL NOT NULL, 
	currency_id INTEGER, 
	currency_year INTEGER, 
	value FLOAT(53), 
	PRIMARY KEY (id), 
	UNIQUE (currency_id, currency_year), 
	FOREIGN KEY(currency_id) REFERENCES migrated."Currencies" (id)
);

CREATE TABLE migrated."OtherIndexesData" (
	id SERIAL NOT NULL, 
	other_index_id INTEGER, 
	name TEXT, 
	PRIMARY KEY (id), 
	UNIQUE (other_index_id, name), 
	FOREIGN KEY(other_index_id) REFERENCES migrated."OtherIndexes" (id)
);

CREATE TABLE migrated."Shapes" (
	id SERIAL NOT NULL, 
	name TEXT, 
	shape_type_id INTEGER, 
	shape_unit_type_id INTEGER, 
	time_zone_id INTEGER, 
	geography_id INTEGER, 
	other_index_1_id INTEGER, 
	other_index_2_id INTEGER, 
	geography_map_key_id INTEGER, 
	interpolation_method_id INTEGER, 
	extrapolation_method_id INTEGER, 
	PRIMARY KEY (id), 
	UNIQUE (name), 
	FOREIGN KEY(shape_type_id) REFERENCES migrated."ShapesTypes" (id), 
	FOREIGN KEY(shape_unit_type_id) REFERENCES migrated."ShapesUnits" (id), 
	FOREIGN KEY(time_zone_id) REFERENCES migrated."TimeZones" (id), 
	FOREIGN KEY(geography_id) REFERENCES migrated."Geographies" (id), 
	FOREIGN KEY(other_index_1_id) REFERENCES migrated."OtherIndexes" (id), 
	FOREIGN KEY(other_index_2_id) REFERENCES migrated."OtherIndexes" (id), 
	FOREIGN KEY(geography_map_key_id) REFERENCES migrated."GeographyMapKeys" (id), 
	FOREIGN KEY(interpolation_method_id) REFERENCES migrated."CleaningMethods" (id), 
	FOREIGN KEY(extrapolation_method_id) REFERENCES migrated."CleaningMethods" (id)
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
	UNIQUE (parent_id, gau_id, oth_1_id, oth_2_id, year), 
	FOREIGN KEY(parent_id) REFERENCES migrated."DemandDrivers" (id), 
	FOREIGN KEY(gau_id) REFERENCES migrated."GeographiesData" (id), 
	FOREIGN KEY(oth_1_id) REFERENCES migrated."OtherIndexesData" (id), 
	FOREIGN KEY(oth_2_id) REFERENCES migrated."OtherIndexesData" (id)
);

CREATE TABLE migrated."DemandSectors" (
	id SERIAL NOT NULL, 
	name TEXT, 
	shape_id INTEGER, 
	max_lead_hours INTEGER, 
	max_lag_hours INTEGER, 
	PRIMARY KEY (id), 
	UNIQUE (name), 
	FOREIGN KEY(shape_id) REFERENCES migrated."Shapes" (id)
);

CREATE TABLE migrated."ShapesData" (
	id SERIAL NOT NULL, 
	parent_id INTEGER, 
	gau_id INTEGER, 
	dispatch_feeder_id INTEGER, 
	timeshift_type_id INTEGER, 
	resource_bin INTEGER, 
	dispatch_constraint_type_id INTEGER, 
	year INTEGER, 
	month INTEGER, 
	week INTEGER, 
	hour INTEGER, 
	day_type_id INTEGER, 
	weather_datetime TIMESTAMP WITHOUT TIME ZONE, 
	value FLOAT, 
	PRIMARY KEY (id), 
	UNIQUE (parent_id, gau_id, dispatch_feeder_id, timeshift_type_id, resource_bin), 
	FOREIGN KEY(parent_id) REFERENCES migrated."Shapes" (id), 
	FOREIGN KEY(gau_id) REFERENCES migrated."GeographiesData" (id), 
	FOREIGN KEY(dispatch_feeder_id) REFERENCES migrated."DispatchFeeders" (id), 
	FOREIGN KEY(timeshift_type_id) REFERENCES migrated."FlexibleLoadShiftTypes" (id), 
	FOREIGN KEY(dispatch_constraint_type_id) REFERENCES migrated."DispatchConstraintTypes" (id), 
	FOREIGN KEY(day_type_id) REFERENCES migrated."DayTypes" (id)
);

