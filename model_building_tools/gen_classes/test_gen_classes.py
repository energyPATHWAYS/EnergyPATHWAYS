from __future__ import print_function
from energyPATHWAYS.database import Database
from schema import BlendNodeBlendMeasures, BlendNodeBlendMeasuresData

import pandas as pd
pd.set_option('display.width', 200)

db = Database.get_database(dbname='170817_US', user='rjp', cache_data=True)
obj = BlendNodeBlendMeasures.from_db(1)
print(obj)
print('')

obj = BlendNodeBlendMeasures.from_db(2)
print(obj)
print('')

obj = BlendNodeBlendMeasuresData.from_db(11963)
print(obj)
