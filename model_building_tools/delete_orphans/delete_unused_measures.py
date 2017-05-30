# This script deletes all measures from the database that are not used by any scenario file in the working path.
# Cascading delete constraints in the database will delete the measures' associated data when the measure is deleted.
# All '*.json' files in the specified directory are assumed to be scenario files.
#
# Basic usage is:
#
# python delete_unused_measures.py -p ../../model_runs/us_model_example/
#
# If you'd like to do a dry run to see what will be deleted before actually deleting, use the '-d' option:
#
# python delete_unused_measures.py -d -p ../../model_runs/us_model_example/
#
# All of the SQL that is run is identical in either case, but with the dry run the transaction is rolled back
# at the end rather than committed.

import click
import os
import logging
import energyPATHWAYS.config as cfg
from glob import glob
from energyPATHWAYS.scenario_loader import Scenario


@click.command()
@click.option('-d', '--dry-run/--no-dry-run', default=False,
              help='Rollback the transaction at the end so no rows are actually deleted.')
@click.option('-p', '--path', type=click.Path(exists=True),
              help='Working directory for energyPATHWAYS config file and scenarios.')
@click.option('-c', '--config', default='config.INI', help='File name for the energyPATHWAYS configuration file.')
def delete_unused_measures(dry_run, path, config):
    cfg.initialize_config(path, config, 'delete_orphans_log.txt')

    scenario_files = glob(os.path.join(cfg.workingdir, '*.json'))

    if not scenario_files:
        raise IOError("No scenario json files found in {}".format(path))

    used_measure_ids = {category: set() for category in Scenario.MEASURE_CATEGORIES}

    for scenario_file in scenario_files:
        scenario = Scenario(scenario_file)
        for category, measure_ids in scenario.all_measure_ids_by_category().iteritems():
            used_measure_ids[category].update(measure_ids)

    for category, measure_ids in used_measure_ids.iteritems():
        where = ''
        if measure_ids:
            where = ' WHERE id NOT IN ({})'.format(', '.join(str(measure_id) for measure_id in measure_ids))
        query = 'DELETE FROM "{}"{};'.format(category, where)
        logging.info("Executing `{}`".format(query))
        cfg.cur.execute(query)

    if dry_run:
        logging.info("Rolling back (dry run was requested)")
        cfg.con.rollback()
    else:
        logging.info("Committing")
        cfg.con.commit()

if __name__ == '__main__':
    delete_unused_measures()
