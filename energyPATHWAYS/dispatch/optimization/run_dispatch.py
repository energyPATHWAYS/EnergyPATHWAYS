"""
The __main__ function of this script runs the allocation and dispatch optimizations.

Included here are:
Pyomo optimization function
Allocation optimization class
Dispatch optimization class
Multiprocessing functions
"""


# Third-party modules
import os
import datetime
import multiprocessing
from functools import partial
import logging
from pyomo.opt import SolverFactory

# Dispatch modules
import dispatch_problem
import year_to_period_allocation
import get_inputs
import export_results


def run_pyomo_optimization(model, data, solver_name, stdout_detail, **kwargs):
    """
    Pyomo optimization steps: create model instance from model formulation and data,
    get solver, solve instance, and load solution.
    :param model:
    :param data:
    :param solver_name:
    :param stdout_detail:
    :param kwargs:
    :return: instance
    """
    if stdout_detail:
        print "Creating model instance..."
    instance = model.create_instance(data)
    if stdout_detail:
        print "Getting solver..."
    solver = SolverFactory(solver_name)
    if stdout_detail:
        print "Solving..."
    solution = solver.solve(instance, **kwargs)
    if stdout_detail:
        print "Loading solution..."
    instance.solutions.load_from(solution)
    return instance


class PathwaysAllocation:
    """
    Data and functions for the allocation optimization.
    """
    def __init__(self, _alloc_inputs, _solver_name, _stdout_detail, _solve_kwargs, _results_directory):
        # ### Data ### #
        self.allocation_inputs = _alloc_inputs
        self.solver_name = _solver_name
        self.stdout_detail = _stdout_detail
        self.solve_kwargs = _solve_kwargs
        self.results_directory = _results_directory

    def run_year_to_month_allocation(self):
        start_time = datetime.datetime.now()
        model = year_to_period_allocation.year_to_period_allocation_formulation(self.allocation_inputs)
        results = run_pyomo_optimization(model, None, self.solver_name, self.stdout_detail, **self.solve_kwargs)
        state_of_charge = export_results.export_allocation_results(results, self.results_directory)
        print "   ...total time for allocation: " + str(datetime.datetime.now()-start_time)
        return state_of_charge


class PathwaysDispatch:
    """
    Data and functions for the dispatch optimization.
    """
    def __init__(self, _dispatch_inputs, _start_state_of_charge, _end_state_of_charge, _solver_name, _stdout_detail,
                 _solve_kwargs, _results_directory):
        # ### Data ### #
        self.dispatch_inputs = _dispatch_inputs
        self.start_state_of_charge = _start_state_of_charge
        self.end_state_of_charge = _end_state_of_charge

        # Settings, etc.
        self.solver_name = _solver_name
        self.stdout_detail = _stdout_detail
        self.solve_kwargs = _solve_kwargs
        self.results_directory = _results_directory

    def run_dispatch_optimization(self, period):
        """
        :param period:
        :return:
        """

        start_time = datetime.datetime.now()

        if self.stdout_detail:
            print "Optimizing dispatch for period " + str(period)

        # Directory structure
        # This won't be needed when inputs are loaded from memory

        if self.stdout_detail:
            print "Getting problem formulation..."
        model = dispatch_problem.dispatch_problem_formulation(self.dispatch_inputs, self.start_state_of_charge,
                                                              self.end_state_of_charge, period)

        results = run_pyomo_optimization(model, None, self.solver_name, self.stdout_detail, **self.solve_kwargs)

        if self.stdout_detail:
            print "Exporting results..."
        # TODO: currently exports results to CSVs; need to figure out what outputs are needed and how to pass them
        export_results.export_dispatch_results(results, self.results_directory, period)

        print "   ...total time for period " + str(period) + ": " + str(datetime.datetime.now()-start_time)


def run_dispatch_multi(_dispatch, period):
    """
    This function is in a sense redundant, as it simply calls the run_optimization function.
    However, it is needed outside of class to avoid pickling error while multiprocessing on Windows
    (see https://docs.python.org/2/library/multiprocessing.html#windows).
    :param _dispatch:
    :param period:
    :return:
    """
    _dispatch.run_dispatch_optimization(period)


def process_handler(_periods, n_processes):
    """
    Process periods in parallel.
    NOTE: On Windows, this function must be run using if__name__ == ' __main__' to avoid a RuntimeError
    (see https://docs.python.org/2/library/multiprocessing.html#windows).
    :param _periods:
    :param n_processes:
    :return:
    """
    pool = multiprocessing.Pool(processes=n_processes)

    # TODO: maybe change to pool.map() if at some point we need to run map_async(...).get() (two are equivalent)
    # Other option is to use imap,
    # which will return the results as soon as they are ready rather than wait for all workers to finish,
    # but that probably doesn't help us, as wee need to pass on everything at once
    # http://stackoverflow.com/questions/26520781/multiprocessing-pool-whats-the-difference-between-map-async-and-imap
    # TODO: experiment with chunksize option
    pool.map_async(run_dispatch_multi, _periods)
    pool.close()
    pool.join()


def multiprocessing_debug_info():
    """
    Run this to see what multiprocessing is doing.
    :return:
    """
    multiprocessing.log_to_stderr().setLevel(logging.DEBUG)


if __name__ == "__main__":
    _start_time = datetime.datetime.now()
    print "Running dispatch..."
    multiprocessing.freeze_support()  # can be omitted if we won't be producing a Windows executable

    # ############# SETTINGS ############# #
    # Currently using all available CPUs in multiprocessing function below
    available_cpus = multiprocessing.cpu_count()

    # Solver info
    solver_name = "glpk"
    solver_settings = None

    # Pyomo solve keyword arguments
    # Set 'keepfiles' to True if you want the problem and solution files
    # Set 'tee' to True if you want to stream the solver output
    solve_kwargs = {"keepfiles": False, "tee": False}

    # How much to print to standard output; set to 1 for more detailed output, 0 for limited detail
    stdout_detail = 0

    # The directory structure will have to change, but I'm not sure how yet
    current_directory = os.getcwd()
    results_directory = current_directory + "/results"
    inputs_directory = current_directory + "/test_inputs"

    # Make results directory if it doesn't exist
    if not os.path.exists(results_directory):
            os.mkdir(results_directory)

    # ################### OPTIMIZATIONS ##################### #

    # ### Create allocation instance and run optimization ### #

    # This currently exports results to the dispatch optimization inputs directory (that part won't be needed)
    # It also returns the needed params for the main dispatch optimization
    allocation = PathwaysAllocation(_alloc_inputs=get_inputs.alloc_inputs_init(inputs_directory),
                                    _solver_name=solver_name, _stdout_detail=stdout_detail, _solve_kwargs=solve_kwargs,
                                    _results_directory=inputs_directory)

    print "...running large storage allocation..."
    state_of_charge = allocation.run_year_to_month_allocation()
    alloc_start_state_of_charge, alloc_end_state_of_charge = state_of_charge[0], state_of_charge[1]

    # # ### Instantiate hourly dispatch class and run optimization ### #
    pathways_dispatch = PathwaysDispatch(_dispatch_inputs=get_inputs.dispatch_inputs_init(inputs_directory),
                                         _start_state_of_charge=alloc_start_state_of_charge,
                                         _end_state_of_charge=alloc_end_state_of_charge,
                                         _solver_name=solver_name, _stdout_detail=stdout_detail,
                                         _solve_kwargs=solve_kwargs,
                                         _results_directory=results_directory)
    periods = pathways_dispatch.dispatch_inputs.periods

    print "...running main dispatch optimization..."
    # Run periods in parallel
    pool = multiprocessing.Pool(processes=available_cpus)
    partial_opt = partial(run_dispatch_multi, pathways_dispatch)

    # TODO: maybe change to pool.map() if at some point we need to run map_async(...).get() (two are equivalent)
    # Other option is to use imap,
    # which will return the results as soon as they are ready rather than wait for all workers to finish,
    # but that probably doesn't help us, as wee need to pass on everything at once
    # http://stackoverflow.com/questions/26520781/multiprocessing-pool-whats-the-difference-between-map-async-and-imap
    # TODO: experiment with chunksize option
    pool.map_async(partial_opt, periods)
    pool.close()
    pool.join()

    # # Run periods in sequence
    # for p in periods:
    #     run_dispatch_multi(pathways_dispatch, p)

    print "Done. Total time for dispatch: " + str(datetime.datetime.now()-_start_time)

