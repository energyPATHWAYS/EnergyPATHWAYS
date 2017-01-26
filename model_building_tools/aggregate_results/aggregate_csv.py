# -*- coding: utf-8 -*-
"""
Created on Fri May 27 10:01:27 2016

@author: ryandrewjones
"""

import os
import csv
import shutil

def checkexistormakedir(path):
    '''Checks to see if a directory exists, and creates it if not
    '''
    if not os.path.exists(path):
        os.makedirs(path)

def traverse_files(input_directory, output_directory):
    checkexistormakedir(output_directory)
    for f in os.listdir(input_directory):
        if f.endswith('csv'):
            append_write(os.path.join(input_directory, f), os.path.join(output_directory, f))
        else:
            traverse_files(os.path.join(input_directory, f), os.path.join(output_directory, f))

def append_write(write_from, write_to):
    write_to_already_exists = os.path.isfile(write_to)
    with open(write_from, 'rb') as infile:
        csvreader = csv.reader(infile, delimiter=',')
        if write_to_already_exists:
            # get rid of the header row in this case
            csvreader.next()
        with open(write_to, 'ab') as outfile:
            csvwriter = csv.writer(outfile, delimiter=',')
            for row in csvreader:
                csvwriter.writerow(row)


starting_directory = os.getcwd()

input_folder = 'inputs'
output_folder = 'outputs'

# remove old results
if os.path.exists(os.path.join(starting_directory, output_folder)):
    shutil.rmtree(os.path.join(starting_directory, output_folder))

# aggregate new results
for folder in os.listdir(os.path.join(starting_directory, input_folder)):
    traverse_files(input_directory=os.path.join(starting_directory, input_folder, folder),
                   output_directory=os.path.join(starting_directory, output_folder))







