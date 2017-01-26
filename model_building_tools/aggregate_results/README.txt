This script will combine CSV outputs from different EnergyPATHWAYS runs

Instructions:
(1) Put results from different runs in a folder called "inputs". Each set of results should be in a separate folder. For example:
	/aggregate results/inputs/run1/**bunch of sub folders and CSVs**
	/aggregate results/inputs/run2/**bunch of sub folders and CSVs**
(2) Run the script

Notes:
(1) The script works recursively to match the inputs structure, but in order to work correctly, each set of inputs should have the same folder structure and file names
(2) The script assumes that you have some identifiying column in each of the outputs CSVs that will be distinguishing. Thus, the script does not append anything to the columns or otherwise change the outputs.
(3) All old results are automatically deleted when you run the script