CREATE TABLE migrated."CleaningMethods" (
	id INTEGER NOT NULL, 
	name TEXT, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);

CREATE TABLE migrated."Geographies" (
	id INTEGER NOT NULL, 
	name TEXT, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);

CREATE TABLE migrated."GeographyMapKeys" (
	id INTEGER NOT NULL, 
	name TEXT, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);

CREATE TABLE migrated."InputTypes" (
	id INTEGER NOT NULL, 
	name TEXT, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);

CREATE TABLE migrated."OtherIndexes" (
	id INTEGER NOT NULL, 
	name TEXT, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);

CREATE TABLE migrated."DemandDrivers" (
	id INTEGER NOT NULL, 
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

CREATE TABLE migrated."DemandDriversData" (
	id INTEGER NOT NULL, 
	parent_id INTEGER, 
	gau_id INTEGER, 
	oth_1_id INTEGER, 
	oth_2_id INTEGER, 
	year INTEGER, 
	value FLOAT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(parent_id) REFERENCES migrated."DemandDrivers" (id)
);

