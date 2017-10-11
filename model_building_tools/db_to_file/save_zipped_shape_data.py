from __future__ import print_function
import pandas as pd
import gzip

#
# To dump from postgres to csv do this in psql:
#
#   \copy "ShapesData" to 'ShapesData.csv' csv header
#

filename = 'ShapesData.csv.gz'
with gzip.open(filename, 'rb') as f:
    df = pd.read_csv(f, index_col=None)

for id in df.parent_id.unique():
    filename = '%d.csv.gz' % id
    slice = df.query('parent_id == %d' % id)
    data = slice.to_csv(None)
    print("Writing %s" % filename)
    with gzip.open(filename, 'wb') as f:
        f.write(data)

