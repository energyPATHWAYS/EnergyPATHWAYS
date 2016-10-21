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

@click.command()
@click.option('-f', '--poll-frequency', default=60,
              help="Number of seconds to wait between queue checks. Note that the actual interval between the start "
                   "of one check and the next will be slightly longer than this because of the time taken to actually "
                   "check the queue. Default 60.")
@click.option('-w', '--max-workers', default=multiprocessing.cpu_count(),
              help="Maximum number of simultaneous scenario runs. Defaults to the number of cores available.")
def start_queue_monitor(poll_frequency, max_workers):
    print max_workers
    qm = QueueMonitor(poll_frequency, max_workers)
    qm.start()

class QueueMonitor:
    def __init__(self, poll_frequency, max_workers):
        self.poll_frequency = poll_frequency
        self.max_workers = max_workers

    def start(self):
        while True:
            self.check_queue()
            time.sleep(self.poll_frequency)

    def check_queue(self):
        with app.app_context():
            self.check_for_lost_runs()
            self.check_for_queued_runs()

    def check_for_lost_runs(self):
        running_status_id = models.ScenarioRunStatus.RUNNING_ID
        active_runs = models.ScenarioRun.query.filter_by(status_id=running_status_id)

        # Find the ids of any runs that claim to be running but whose pids are no longer active.
        # Note that this will also treat any ScenarioRuns having a NULL pid as lost, which is appropriate.
        # (The run should have had its pid set when it was marked as running; if it didn't something's gone wrong.)
        lost_run_ids = []
        for run in active_runs:
            if not psutil.pid_exists(run.pid):
                lost_run_ids.append(run.id)

        # Mark the runs with the lost pids as "lost" rather than running.
        # Note that we re-check here that any ScenarioRuns being updated are still in the running state at the moment
        # of the update in order to avoid a race condition where we found that the process was gone above, but it was
        # actually because the run had successfully completed in the middle of our loop.
        # The synchronize_session=False means that we won't try to update the run objects in memory to reflect this
        # update. This was necessary to work around an error and is fine because the session is immediately
        # committed which expires the memory contents anyway.
        if lost_run_ids:
            models.db.session.query(models.ScenarioRun).filter(sqlalchemy.and_(
                models.ScenarioRun.status_id == running_status_id,
                models.ScenarioRun.id.in_(lost_run_ids)
            )).update({'status_id': models.ScenarioRunStatus.LOST_ID, 'end_time': sqlalchemy.func.now()},
                      synchronize_session=False)
            models.db.session.commit()

    def check_for_queued_runs(self):
        # Note that this is making the assumption that the model run process has had time to update the status_id
        # of any recently started runs in the time that passes between queue checks. This should be a safe assumption
        # since it's pretty much the first thing that the model runner does, but if that update was somehow delayed,
        # we could wind up starting more than one process for the same run, with bad consequences for database
        # integrity. Probably adding a "Handed off" status would be cleaner.
        # You might think we could solve the problem by setting the status to "running" in this script rather than
        # in the model running process, but that creates a race condition where the model running process could
        # immediately log a termination due to error (status_id 4) which we then overwrite from this process with
        # a status_id 2. Since the process would be terminated due to an exception, we would then mark it as "lost"
        # (status_id 6) on the next pass, which isn't terrible but we'd lose some information in having the status
        # be 6 rather than 4.
        active_run_count = models.ScenarioRun.query.filter_by(status_id=models.ScenarioRunStatus.RUNNING_ID).count()
        self.start_new_runs(self.max_workers - active_run_count)

    def start_new_runs(self, num_runs):
        if num_runs <= 0:
            return

        runs_to_start = models.ScenarioRun.query.filter_by(status_id=models.ScenarioRunStatus.QUEUED_ID)\
                                                .order_by(models.ScenarioRun.ready_time)\
                                                .limit(num_runs)

        for run in runs_to_start:
            # Actually run the scenario
            subprocess.Popen(['energyPATHWAYS', '-a',
                              '-p', '../../us_model_example',
                              '-s', str(run.scenario_id)])

if __name__ == '__main__':
    start_queue_monitor()