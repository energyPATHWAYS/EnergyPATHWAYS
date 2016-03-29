# -*- coding: utf-8 -*-
"""
Created on Mon Mar 28 18:00:33 2016

@author: Ben
"""
import dispatch_problem_PATHWAYS

def run_dispatch_optimization(dispatch_class, start_state_of_charge, end_state_of_charge, period):
        """
        :param period:
        :return:
        """

        if dispatch_class.stdout_detail:
            print "Optimizing dispatch for period " + str(period)

        # Directory structure
        # This won't be needed when inputs are loaded from memory

        if dispatch_class.stdout_detail:
            print "Getting problem formulation..."
        model = dispatch_problem_PATHWAYS.dispatch_problem_formulation(dispatch_class, start_state_of_charge,
                                                              end_state_of_charge, period)
        
        results = dispatch_class.run_pyomo(model,None)
        return results