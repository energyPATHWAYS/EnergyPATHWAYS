
import os
import pdb
import pandas as pd
import csv

read_directory = 'E:\ep_runs\UCS\RIO2EP\combined_outputs'

for file in os.listdir(read_directory):
    if file[-4:]!='.csv' or file[-12:]=='filtered.csv':
        continue

    new_file = open(os.path.join(read_directory, file[:-4]+'_filtered.csv'), 'wb')
    csv_writer = csv.writer(new_file, delimiter=',')

    with open(os.path.join(read_directory, file), 'rb') as readfile:
        csv_reader = csv.reader(readfile, delimiter=',')
        header = csv_reader.next()
        year_index = header.index('YEAR')
        csv_writer.writerow(header)
        for row in csv_reader:
            if int(row[year_index]) % 5 == 0:
                csv_writer.writerow(row)

    new_file.close()
