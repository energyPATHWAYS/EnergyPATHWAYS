import sys
import logging
import datetime
import click
from flask import Flask
import multiprocessing
import time
import psutil
import sqlalchemy
import subprocess
import models

# create the application object
app = Flask(__name__)
app.config.from_pyfile('config.py')
models.db.init_app(app)

# set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(filename='../../us_model_example/queue_monitor_%s.log' %
                             datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f%z'),
                    level=logging.INFO,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

@click.command()
@click.option('-f', '--poll-frequency', default=60,
              help="Number of seconds to wait between queue checks. Note that the actual interval between the start "
                   "of one check and the next will be slightly longer than this because of the time taken to actually "
                   "check the queue. Default 60.")
@click.option('-w', '--max-workers', default=4,
              help="Maximum number of simultaneous scenario runs. Defaults to one.")
def start_queue_monitor(poll_frequency, max_workers):
    qm = QueueMonitor(poll_frequency, max_workers)
    qm.start()

class QueueMonitor:
    ACTIVE_STATUS_IDS = [models.ScenarioRunStatus.LAUNCHED_ID, models.ScenarioRunStatus.RUNNING_ID]

    def __init__(self, poll_frequency, max_workers):
        self.poll_frequency = poll_frequency
        self.max_workers = max_workers
        logger.info('Starting queue monitor polling every %i seconds with %i workers' %
                    (self.poll_frequency, self.max_workers))

    def start(self):
        while True:
            logger.debug('Checking queue')
            self.check_queue()
            logger.debug('Sleeping for %i seconds' % (self.poll_frequency,))
            time.sleep(self.poll_frequency)

    def check_queue(self):
        with app.app_context():
            self.check_for_lost_runs()
            self.utilize_available_workers()

    def active_runs(self):
        return models.ScenarioRun.query.filter(models.ScenarioRun.status_id.in_(self.ACTIVE_STATUS_IDS))

    def check_for_lost_runs(self):
        logger.debug("Checking for lost runs")

        # Find the ids of any runs that claim to be running but whose pids are no longer active.
        # Note that this will also treat any ScenarioRuns having a NULL pid as lost, which is appropriate.
        # (The run should have had its pid set when it was launched; if it didn't something's gone wrong.)
        lost_run_ids = []
        for run in self.active_runs():
            if not psutil.pid_exists(run.pid):
                lost_run_ids.append(run.id)
            elif run.status_id == models.ScenarioRunStatus.LAUNCHED_ID:
                # This isn't *necessarily* a problem, but it suggests that something went wrong with the model run
                # process (even though it's still running) because that process should have had time to update the
                # status to "Running" rather than "Launched" by the time we're doing the next queue check.
                logger.warning("ScenarioRun %i is still in the 'Launched' state even though it has a running process"
                               % (run.id,))

        # Mark the runs with the lost pids as "Lost" rather than running.
        # Note that we re-check here that any ScenarioRuns being updated are still in the running state at the moment
        # of the update in order to avoid a race condition where we found that the process was gone above, but it was
        # actually because the run had successfully completed in the middle of our loop.
        # The synchronize_session=False means that we won't try to update the run objects in memory to reflect this
        # update. This was necessary to work around an error and is fine because the session is immediately
        # committed which expires the memory contents anyway.
        if lost_run_ids:
            logger.warning("Cleaning up lost run(s): " + ', '.join(str(i) for i in lost_run_ids))
            models.db.session.query(models.ScenarioRun).filter(sqlalchemy.and_(
                models.ScenarioRun.status_id.in_(self.ACTIVE_STATUS_IDS),
                models.ScenarioRun.id.in_(lost_run_ids)
            )).update({'status_id': models.ScenarioRunStatus.LOST_ID, 'end_time': sqlalchemy.func.now()},
                      synchronize_session=False)
            models.db.session.commit()
        else:
            logger.debug("No lost runs found")

    def utilize_available_workers(self):
        active_run_count = self.active_runs().count()
        available_slots = self.max_workers - active_run_count
        logger.debug("%i scenarios currently running; launching up to %i new runs" %
                     (active_run_count, available_slots))
        self.start_new_runs(available_slots)

    def start_new_runs(self, num_runs):
        if num_runs <= 0:
            return

        runs_to_start = models.ScenarioRun.query.filter_by(status_id=models.ScenarioRunStatus.QUEUED_ID)\
                                                .order_by(models.ScenarioRun.ready_time)\
                                                .limit(num_runs)

        if runs_to_start.count() == 0:
            logger.debug('Did not find any queued runs to start')

        for run in runs_to_start:
            # Note that we are launching this scenario run
            logger.info("Launching ScenarioRun %i" % (run.id,))
            run.status_id = models.ScenarioRunStatus.LAUNCHED_ID
            run.start_time = datetime.datetime.now()
            models.db.session.commit()
            # Actually run the scenario
            proc = subprocess.Popen(['energyPATHWAYS', '-a',
                                     '-p', '../../us_model_example',
                                     '-s', str(run.scenario_id),
                                     '--no_save_models'])
            # Record the pid
            logger.info("ScenarioRun %i got pid %i" % (run.id, proc.pid))
            run.pid = proc.pid
            models.db.session.commit()

if __name__ == '__main__':
    start_queue_monitor()
