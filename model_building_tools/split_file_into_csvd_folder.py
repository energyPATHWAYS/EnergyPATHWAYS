


import os
import pdb
import csv
import random
import pandas as pd
import numpy as np


path = r'C:\github\EP_US_db\database'
file_name = 'SupplyStock.csv.gz'

key_col = 'supply_node'

output_folder_name = file_name.split('.')[0] + '.csvd'

if not os.path.exists(os.path.join(path, output_folder_name)):
    os.makedirs(os.path.join(path, output_folder_name))

values = pd.read_csv(os.path.join(path, file_name), compression='gzip')

for name, group in values.groupby(key_col):
    gau_groups = group.groupby('gau').sum()['value']
    non_zero_gaus = gau_groups.index[np.nonzero(gau_groups.values)[0]]
    group = group[group['gau'].isin(non_zero_gaus)]
    group.to_csv(os.path.join(path, output_folder_name, name.rstrip().lstrip()+'.csv.gz'), compression='gzip', index=False)
