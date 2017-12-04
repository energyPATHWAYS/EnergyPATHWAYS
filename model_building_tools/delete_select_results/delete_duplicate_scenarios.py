import csv
import click
import os
import sys

def list_the_scenarios(path):
    with open(path, 'rb') as in_file:
        csvreader = csv.reader(in_file, delimiter=',')
        header = csvreader.next()
        i_timestamp = header.index('TIMESTAMP')
        i_scenario = header.index('SCENARIO')
        scenarios = set()
        totallinecount = 0
        for row in csvreader:
            scenarios.add((row[i_scenario], row[i_timestamp]))
            totallinecount += 1
    return sorted(scenarios), totallinecount

results_folders = ['demand_outputs', 'supply_outputs', 'dispatch_outputs', 'combined_outputs']

@click.command()
@click.option('-d', '--workingdir', type=click.Path(exists=True), help='Path where the results are located')
@click.option('-n', '--keep_newest/--keep_oldest', default=True, help='Keep the scenarios with the newest timestamps')
@click.option('-o', '--keep_oldest/--no_keep_oldest', default=False, help='Keep the scenarios with the oldest timestamps')
@click.option('--rollback/--no_rollback', default=False)
def delete_results(workingdir, keep_newest, keep_oldest, rollback):
    assert not ((keep_newest and keep_oldest) or (not keep_newest and not keep_oldest)), 'must choose to either keep the oldest timestamps or newest timestamps for a scenario'
    for folder in results_folders:
        path = os.path.join(workingdir, folder)
        for file in os.listdir(path):
            if file[-4:]!='.csv' or file[0]=='_' or file=='s_io.csv':
                continue
            print '{}'.format(file)

            scenario_stamps, totallinecount = list_the_scenarios(os.path.join(path, file))
            scenario_stamps = scenario_stamps[-1::-1] if keep_newest else scenario_stamps
            scenario_to_keep = {}
            for scenario, stamp in scenario_stamps:
                if scenario not in scenario_to_keep:
                    scenario_to_keep[scenario] = stamp

            removelinecount = 0
            if len(scenario_stamps) > len(scenario_to_keep):
                write_name = '_' + file
                out_file = open(os.path.join(path, write_name), 'wb')
                csvwriter = csv.writer(out_file, delimiter=',')

                with open(os.path.join(path, file), 'rb') as in_file:
                    csvreader = csv.reader(in_file, delimiter=',')
                    header = csvreader.next()
                    csvwriter.writerow(header)
                    i_timestamp = header.index('TIMESTAMP')
                    i_scenario = header.index('SCENARIO')
                    for row in csvreader:
                        if row[i_timestamp] == scenario_to_keep[row[i_scenario]]:
                            csvwriter.writerow(row)
                        else:
                            removelinecount += 1

                out_file.close()
                if rollback:
                    os.remove(os.path.join(path, '_' + file))
                else:
                    os.remove(os.path.join(path, file))
                    os.rename(os.path.join(path, '_' + file), os.path.join(path, file))

            print '    removed {} lines of {} total lines ({}%)'.format(removelinecount, totallinecount, round(removelinecount/float(totallinecount))*100)



if __name__ == '__main__':
    delete_results()








