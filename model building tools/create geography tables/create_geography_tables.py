# -*- coding: utf-8 -*-
"""
Created on Sat Apr 16 15:02:05 2016

@author: Ryan Jones

"""

import os
import csv
import pandas as pd

directory = os.getcwd()

# from the database
Geographies            = pd.read_csv(os.path.join(directory, 'inputs', 'Geographies.csv'))
GeographiesData        = pd.read_csv(os.path.join(directory, 'inputs', 'GeographiesData.csv'))
GeographyMapKeys       = pd.read_csv(os.path.join(directory, 'inputs', 'GeographyMapKeys.csv'))

# "human legible" formatting
GeographiesSpatialJoin = pd.read_csv(os.path.join(directory, 'inputs', 'GeographiesSpatialJoin.csv'))

# Parse inputs and set up mapping
id_to_gau = dict(Geographies.values)
gau_to_id = {v: k for k, v in id_to_gau.iteritems()}

gaus = [id_to_gau[id] for id in GeographiesData['geography_id'].values]
GeographiesDataDict = dict(zip(zip(gaus, GeographiesData['name']), GeographiesData['id'].values))
MapKeysDict = dict(zip(GeographyMapKeys['name'], GeographyMapKeys['id']))

SpatialJoinColumns = GeographiesSpatialJoin.columns
gau_columns = [c for c in SpatialJoinColumns if c in gau_to_id]
map_key_columns = [c for c in SpatialJoinColumns if c in GeographyMapKeys['name'].values]

##########
# tables to produce
##########
# GeographyIntersection
# GeographyIntersectionData
# GeographyMap
##########

GeographyIntersection = [['id']]+[[i] for i in range(1, len(GeographiesSpatialJoin)+1)]
GeographyIntersectionData = []
GeographyMap = []

# Iterate through each row of the spatial join table
for row in GeographiesSpatialJoin.iterrows():
    intersection_id = row[0]+1
    # iterate down the columns in each row
    for col in row[1].iteritems():
        if col[0] in gau_columns:
            print GeographiesDataDict[col]
            GeographyIntersectionData.append([intersection_id, GeographiesDataDict[col]])
        elif col[0] in map_key_columns:
            GeographyMap.append([intersection_id, MapKeysDict[col[0]], col[1]])
        else:
            raise ValueError('column {} not found in Geographies'.format(col[0]))

# add id column to the results
GeographyIntersectionData = [row+[i+1] for i, row in enumerate(GeographyIntersectionData)]
GeographyMap = [row+[i+1] for i, row in enumerate(GeographyMap)]

# add a header to the results
GeographyIntersectionData = [['intersection_id', 'gau_id', 'id']]+GeographyIntersectionData
GeographyMap = [['intersection_id', 'geography_map_key_id', 'value', 'id']]+GeographyMap

# write the results to the outputs folder
def csv_write(path, data):
    with open(path, 'wb') as outfile:
        csvwriter = csv.writer(outfile)
        for row in data:
            csvwriter.writerow(row)

csv_write(os.path.join(directory, 'outputs', 'GeographyIntersection.csv'), GeographyIntersection)
csv_write(os.path.join(directory, 'outputs', 'GeographyIntersectionData.csv'), GeographyIntersectionData)
csv_write(os.path.join(directory, 'outputs', 'GeographyMap.csv'), GeographyMap)
