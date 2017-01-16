# -*- coding: utf-8 -*-
__author__ = 'Ben, Ryan, Michael'

import numpy as np
from collections import defaultdict
import pandas as pd
import energyPATHWAYS
import unittest
import ipdb

class TestRollover(unittest.TestCase):
    def setUp(self):
        start_year = 2000
        end_year = 2050
        years = range(start_year, end_year+1)
        self.num_years = end_year-start_year+1 # number of years to run in the stock rollover
        self.num_vintages = end_year-start_year+1 # it might be that this is unneeeded and should just be set to self.num_years
        
        self.num_techs = 1 # number of technologies in a subsector (can be 1 and often is)
        tech_ids = [0]
        steps_per_year = 1
        
        # start a record for a single technology
        tech = energyPATHWAYS.shared_classes.StockItem()
        tech.mean_lifetime = 10 # years
        tech.lifetime_variance = 4 # years
        # Other ways to define lifetime are min_lifetime and max_lifetime
        tech.stock_decay_function = 'weibull' # other options here ('linear' or 'exponential')
        tech.spy = steps_per_year
        tech.years = years
                
        tech.set_survival_parameters()
        tech.set_survival_vintaged()
        tech.set_decay_vintaged()
        tech.set_survival_initial_stock()
        tech.set_decay_initial_stock()
        
        # wrap the technologies together
        technologies = dict(zip(tech_ids, [tech]))
        
        # at this point we have all the survival functions, but we don't yet have the markov matrix
        
        functions = defaultdict(list)
        for fun in ['survival_vintaged', 'survival_initial_stock', 'decay_vintaged', 'decay_initial_stock']:
            for tech_id in tech_ids:
                technology = technologies[tech_id]
                functions[fun].append(getattr(technology, fun))
            functions[fun] = pd.DataFrame(np.array(functions[fun]).T, columns=tech_ids)
        
        
        vintaged_markov = energyPATHWAYS.util.create_markov_vector(functions['decay_vintaged'].values, functions['survival_vintaged'].values)
        self.vintaged_markov_matrix = energyPATHWAYS.util.create_markov_matrix(vintaged_markov, self.num_techs, self.num_years, steps_per_year)
        
        initial_markov = energyPATHWAYS.util.create_markov_vector(functions['decay_initial_stock'].values, functions['survival_initial_stock'].values)
        self.initial_markov_matrix = energyPATHWAYS.util.create_markov_matrix(initial_markov, self.num_techs, self.num_years, steps_per_year)
        
        # now we have the markov matrix and we are ready to do stock rollover

    def tearDown(self):
        self.num_years = None
        self.num_vintages = None
        self.num_techs = None
        self.vintaged_markov_matrix = None
        self.initial_markov_matrix = None

    # helper method to succinctly set up a rollover, run it, and return outputs
    def outputs_for(self, *args, **kwargs):
        rollover = energyPATHWAYS.rollover.Rollover(*args, **kwargs)
        rollover.run()
        return rollover.return_formatted_outputs()

    def test_basic_stock_changes(self):
        # just some example inputs
        initial_stock = 10000
        change_per_year = 500
        stock_changes = np.array([change_per_year]*self.num_years) # must be a numpy array
        
        # set of rollover object
        rollover = energyPATHWAYS.rollover.Rollover(self.vintaged_markov_matrix, self.initial_markov_matrix, self.num_years, self.num_vintages, self.num_techs,
                                                    initial_stock=initial_stock, stock_changes=stock_changes)
        
        # run the rollover
        rollover.run()
        
        # grab the outputs
        stock_total, stock_new, stock_replacement, retirements, retirements_natural, retirements_early, sales_record, sales_new, sales_replacement = rollover.return_formatted_outputs()
        #ipdb.set_trace()
        self.assertAlmostEqual(stock_total[:, -1].sum(), initial_stock + change_per_year * self.num_years)

    @unittest.skip("currently rollover returns zeros if output is requested prematurely; should raise an error since this is unlikely to be what the user wants")
    def test_premature_output_request(self):
        rollover = energyPATHWAYS.rollover.Rollover(self.vintaged_markov_matrix, self.initial_markov_matrix, self.num_years, self.num_vintages, self.num_techs)

        # Ask for outputs before the rollover has run()
        with self.assertRaises(RuntimeError):
            rollover.return_formatted_outputs()

    def test_basic_specified_stock(self):
        constant_stock = 1000
        specified_stock = np.array([constant_stock]*self.num_years)

        output = self.outputs_for(self.vintaged_markov_matrix, self.initial_markov_matrix, self.num_years, self.num_vintages, self.num_techs,
                                  specified_stock=specified_stock)

        self.assertAlmostEqual(output[0][:, -1].sum(), constant_stock)

    # The next few tests see which inputs "win" when there's a conflict. Arguably in some of these cases the response
    # should be to raise an exception rather than have some input silently disregarded, but we'll start by
    # characterizing the current behavior.

    # specified_stock "wins" and overrides the initial_stock
    def test_specified_stock_initial_stock_conflict(self):
        initial_stock = 10000
        constant_stock = 1000
        specified_stock = np.array([constant_stock]*self.num_years)

        output = self.outputs_for(self.vintaged_markov_matrix, self.initial_markov_matrix, self.num_years, self.num_vintages, self.num_techs,
                                  initial_stock=initial_stock, specified_stock=specified_stock)

        # check that the first and last year's total stock is equal to the constant stock
        self.assertAlmostEqual(output[0][:, 0].sum(), constant_stock)
        self.assertAlmostEqual(output[0][:, -1].sum(), constant_stock)

    # specified_stock "wins" and overrides the stock_changes
    def test_specified_stock_stock_change_conflict(self):
        constant_stock = 10000
        specified_stock = np.array([constant_stock]*self.num_years)
        change_per_year = 500
        stock_changes = np.array([change_per_year]*self.num_years)

        output = self.outputs_for(self.vintaged_markov_matrix, self.initial_markov_matrix, self.num_years, self.num_vintages, self.num_techs,
                                  stock_changes=stock_changes, specified_stock=specified_stock)

        # check that the first and last year's total stock is equal to the constant stock
        self.assertAlmostEqual(output[0][:, 0].sum(), constant_stock)
        self.assertAlmostEqual(output[0][:, -1].sum(), constant_stock)

    # specified_sales "wins" and overrides stock_changes
    # I believe the result we see is a combination of specified sales and natural rolloff, but this should be confirmed
    def test_specified_sales_stock_change_conflict(self):
        sales_per_year = 100
        specified_sales = np.array([sales_per_year]*self.num_years)
        change_per_year = 500
        stock_changes = np.array([change_per_year]*self.num_years)

        output = self.outputs_for(self.vintaged_markov_matrix, self.initial_markov_matrix, self.num_years, self.num_vintages, self.num_techs,
                                  stock_changes=stock_changes, specified_sales=specified_sales)

        self.assertAlmostEqual(output[0][:, 0].sum(), sales_per_year)
        self.assertAlmostEqual(output[0][:, -1].sum(), 1050, places=5)

    # this one does raise an exception noting that the specified sales and specified stock conflict
    def test_specified_sales_specified_stock_conflict(self):
        sales_per_year = 100
        specified_sales = np.array([sales_per_year]*self.num_years)
        constant_stock = 10000
        specified_stock = np.array([constant_stock]*self.num_years)

        rollover = energyPATHWAYS.rollover.Rollover(self.vintaged_markov_matrix, self.initial_markov_matrix, self.num_years, self.num_vintages, self.num_techs,
                                                    specified_stock=specified_stock, specified_sales=specified_sales)

        with self.assertRaises(RuntimeError):
            rollover.run()

