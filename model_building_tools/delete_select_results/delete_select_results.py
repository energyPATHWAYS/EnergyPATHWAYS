import csv
import click
import os
import sys

def list_the_scenarios(workingdir):
    folder = 'combined_outputs'
    path = os.path.join(workingdir, folder)
    file = 'c_emissions.csv'
    with open(os.path.join(path, file), 'rb') as in_file:
        csvreader = csv.reader(in_file, delimiter=',')
        header = csvreader.next()
        i_timestamp = header.index('TIMESTAMP')
        i_scenario = header.index('SCENARIO')
        scenarios = []
        for row in csvreader:
            scenarios.append((row[i_scenario], row[i_timestamp]))
    scenarios = set(scenarios)
    print 'Scenario list:'
    for scenario in scenarios:
        print '    "{}", "{}"'.format(scenario[0], scenario[1])

results_folders = ['demand_outputs', 'supply_outputs', 'dispatch_outputs', 'combined_outputs']

@click.command()
@click.option('-d', '--workingdir', type=click.Path(exists=True), help='Path where the results are located')
@click.option('-t', '--timestamp', type=str, help='time stamp to delete')
@click.option('-s', '--scenario', type=str, help='scenario to delete')
@click.option('-ls', '--list_scenarios/--no_list_scenarios', default=False)
@click.option('--rollback/--no_rollback', default=False)
def delete_results(workingdir, timestamp, scenario, list_scenarios, rollback):
    if list_scenarios:
        list_the_scenarios(workingdir)
        sys.exit()
    for folder in results_folders:
        path = os.path.join(workingdir, folder)
        for file in os.listdir(path):
            if file[-4:]!='.csv' or file[0]=='_' or file=='s_io.csv':
                continue
            write_name = '_' + file
            out_file = open(os.path.join(path, write_name), 'wb')
            csvwriter = csv.writer(out_file, delimiter=',')
            removelinecount, totallinecount = 0, 0
            with open(os.path.join(path, file), 'rb') as in_file:
                csvreader = csv.reader(in_file, delimiter=',')
                header = csvreader.next()
                csvwriter.writerow(header)
                i_timestamp = header.index('TIMESTAMP')
                i_scenario = header.index('SCENARIO')
                for row in csvreader:
                    totallinecount += 1
                    c_s = True if scenario is not None and row[i_scenario]==scenario else False
                    t_s = True if timestamp is not None and row[i_timestamp]==timestamp else False
                    if (c_s and t_s) or (c_s and timestamp is None) or (t_s and scenario is None):
                        removelinecount += 1
                        continue
                    else:
                        csvwriter.writerow(row)
            print 'Removed {} lines of {} total lines ({}%) from file {}'.format(removelinecount, totallinecount, round(removelinecount/float(totallinecount),2), file)
            out_file.close()
            if rollback:
                os.remove(os.path.join(path, '_' + file))
            else:
                os.remove(os.path.join(path, file))
                os.rename(os.path.join(path, '_' + file), os.path.join(path, file))


if __name__ == '__main__':
    delete_results()








