# -*- coding: utf-8 -*-
"""
Created on Thu Oct 01 09:26:56 2015

@author: ryan
"""

import numpy as np
cimport numpy as np
cimport cython

#DTYPE = np.int
ctypedef np.int_t DTYPE_I_t
ctypedef np.float_t DTYPE_F_t

#@cython.boundscheck(False)
cdef class Rollover(object):
#    cdef object vintaged_markov_matrix
#    cdef np.ndarray[DTYPE_F_t, ndim=3] vintaged_markov_matrix
    #cdef public double x, y, z, vx, vy, vz, m
    def __init__(self, vintaged_markov_matrix, initial_markov_matrix, num_years, num_vintages, num_techs, initial_stock=None, sales_share=None, stock_changes=None, specified_stock=None, specified_retirements=None):
        if np.any(np.isnan(vintaged_markov_matrix)) or np.any(np.isnan(initial_markov_matrix)):
            raise ValueError('Markov Matrix cannot contain NaN')
        
        #necessary inputs
        cdef np.ndarray[DTYPE_F_t, ndim=3] temp = vintaged_markov_matrix
        self.vintaged_markov_matrix = temp #vintaged_markov_matrix
        cdef np.ndarray[DTYPE_F_t, ndim=3] self.initial_markov_matrix = initial_markov_matrix
        cdef int self.num_years, cdef int self.num_vintages, cdef int self.num_techs = num_years, num_vintages, num_techs
        
        #optional
        if (sales_share is None) and (self.num_techs>1):
            raise ValueError("With more than one technology, sales share must be specified")
        cdef np.ndarray[DTYPE_F_t, ndim=3] self.sales_share = np.ones((self.num_years, 1, 1)) if sales_share is None else sales_share
        cdef np.ndarray[DTYPE_F_t] self.initial_stock = np.zeros(self.num_techs) if initial_stock is None else initial_stock
        cdef np.ndarray[DTYPE_F_t] self.stock_changes = np.zeros(self.num_years) if stock_changes is None else stock_changes.flatten()
        cdef np.ndarray[DTYPE_F_t] self.specified_retirements = np.zeros(self.num_years) if specified_retirements is None else specified_retirements
        if specified_stock is None:
            cdef np.ndarray[DTYPE_F_t, ndim=2] self.specified_stock = np.empty((self.num_years, self.num_techs))
            self.specified_stock.fill(np.nan)
        else:
            cdef np.ndarray[DTYPE_F_t, ndim=2] self.specified_stock = specified_stock
        
        cdef np.ndarray[DTYPE_I_t] self.all_techs = np.arange(self.num_techs, dtype=int)
        cdef np.ndarray[DTYPE_F_t, ndim=3] self.stock = np.zeros((self.num_techs, self.num_vintages + 1, self.num_years))
        cdef np.ndarray[DTYPE_F_t, ndim=2] self.rolloff_record = np.zeros((self.num_years, self.num_techs))
        cdef np.ndarray[DTYPE_F_t, ndim=2] self.natural_rolloff = np.zeros((self.num_years, self.num_techs))
        cdef np.ndarray[DTYPE_F_t, ndim=2] self.sales_record = np.zeros((self.num_vintages, self.num_techs))
        cdef np.ndarray[DTYPE_F_t] self.prinxy = np.zeros(self.num_techs)
        
        cdef int self.i
        cdef np.ndarray[DTYPE_F_t] self.specified_sales
        cdef double self.sum_specified_sales
        cdef np.ndarray[DTYPE_F_t] self.rolloff
        cdef double self.rolloff_summed
        cdef np.ndarray[DTYPE_F_t] self.sales_by_tech
        cdef np.ndarray[DTYPE_I_t] self.solvable
        cdef np.ndarray[DTYPE_I_t] self.specified
        cdef np.ndarray[DTYPE_F_t] self.prior_year_stock
        cdef np.ndarray[DTYPE_F_t, ndim=3] self.stock_new
        cdef np.ndarray[DTYPE_F_t, ndim=3] self.stock_replacement
        cdef np.ndarray[DTYPE_F_t, ndim=2] self.new_sales_fraction
        cdef np.ndarray[DTYPE_F_t, ndim=2] self.new_sales
        cdef np.ndarray[DTYPE_F_t, ndim=2] self.early_retirements
        cdef np.ndarray[DTYPE_F_t, ndim=2] self.replacement_sales

    def calc_initial_stock_rolloff(self, np.ndarray[DTYPE_I_t] prinxy, str mode='rolloff'):
        i = self.i #make an int
        if mode=='rolloff':
            return (self.initial_stock if i==0 else self.stock[:, 0, i-1]) * (1 - self.initial_markov_matrix[self.all_techs, i, prinxy])
        elif mode=='remaining':
            return (self.initial_stock if i==0 else self.stock[:, 0, i-1]) * self.initial_markov_matrix[self.all_techs, i, prinxy]
    
    def calc_vintaged_stock_rolloff(self, np.ndarray[DTYPE_I_t] prinxy, str mode='rolloff'):
        i = self.i #make an int
        if mode=='rolloff':
            return self.stock[:, 1:i+1, i-1] * (0 if i==0 else (1 - self.vintaged_markov_matrix[self.all_techs, i-1::-1, prinxy]))
        elif mode=='remaining':
            return self.stock[:, 1:i+1, i-1] * (0 if i==0 else self.vintaged_markov_matrix[self.all_techs, i-1::-1, prinxy])
    
    def sum_vintaged_stock_rolloff(self, np.ndarray[DTYPE_I_t] prinxy):
        return 0 if self.i==0 else np.sum(self.calc_vintaged_stock_rolloff(prinxy), axis=1)
    
    def sum_rolloff(self, np.ndarray[DTYPE_I_t] prinxy):
        return self.calc_initial_stock_rolloff(prinxy) + self.sum_vintaged_stock_rolloff(prinxy)
    
    def calc_stock_rolloff(self, np.ndarray[DTYPE_F_t] prinxy):
        cdef np.ndarray[DTYPE_I_t] f_prinxy, cdef np.ndarray[DTYPE_I_t] c_prinxy = np.array(np.floor(prinxy), dtype=int), np.array(np.ceil(prinxy), dtype=int)
        if np.all(f_prinxy==c_prinxy):
            return self.sum_rolloff(np.array(prinxy, dtype=int))
        else:
            cdef double f_rolloff = self.sum_rolloff(f_prinxy)
            cdef double c_rolloff = self.sum_rolloff(c_prinxy)
            return f_rolloff + (prinxy-f_prinxy)*(c_rolloff-f_rolloff)
       
    def update_prinxy(self, double incremental_retirement, np.ndarray[DTYPE_I_t] retireable):
        """ A positive incremental retirement means that retirements are increasing
        """
        if incremental_retirement==0 or sum(self.prior_year_stock[retireable])==0:
            return
        
        if incremental_retirement>sum(self.prior_year_stock[retireable]):
            raise ValueError('specified incremental stock retirements are greater than retireable stock size')
            #self.prinxy[retireable] = self.num_years-1
                
        cdef double starting_rolloff = np.sum(self.calc_stock_rolloff(self.prinxy))
        cdef double old_rolloff, cdef double new_rolloff = starting_rolloff, starting_rolloff
        cdef np.ndarray[DTYPE_F_t] temp_prinxy = np.copy(self.prinxy)
        
        cdef int inc = 1 if incremental_retirement>0 else -1
        temp_prinxy[retireable] = np.floor(temp_prinxy[retireable]) if incremental_retirement>0 else np.ceil(temp_prinxy[retireable])
        while inc*incremental_retirement > inc*(new_rolloff - starting_rolloff):
            if (np.all(temp_prinxy[retireable]==0) and inc==-1) or (np.all(temp_prinxy[retireable]==self.num_years-1) and inc==1):
                return temp_prinxy
            temp_prinxy[retireable] = np.clip(temp_prinxy[retireable]+inc, 0, self.num_years-1)
            old_rolloff, new_rolloff = new_rolloff, np.sum(self.calc_stock_rolloff(temp_prinxy))
        temp_prinxy[retireable] -= inc*(1 - (incremental_retirement + starting_rolloff - old_rolloff)/(new_rolloff - old_rolloff))
        self.prinxy = temp_prinxy

    def calc_remaining_stock_initial(self):
        cdef np.ndarray[DTYPE_I_t] f_prinxy, cdef np.ndarray[DTYPE_I_t] c_prinxy = np.array(np.floor(self.prinxy), dtype=int), np.array(np.ceil(self.prinxy), dtype=int)
        if np.all(f_prinxy==c_prinxy):
            return self.calc_initial_stock_rolloff(np.array(self.prinxy, dtype=int), mode='remaining')
        else:
            cdef np.ndarray[DTYPE_F_t] f_rolloff = self.calc_initial_stock_rolloff(f_prinxy, mode='remaining')
            cdef np.ndarray[DTYPE_F_t] c_rolloff = self.calc_initial_stock_rolloff(c_prinxy, mode='remaining')
        return f_rolloff + (self.prinxy-f_prinxy)*(c_rolloff-f_rolloff)
    
    def calc_remaining_stock_vintaged(self):
        cdef np.ndarray[DTYPE_I_t] f_prinxy, cdef np.ndarray[DTYPE_I_t] c_prinxy = np.array(np.floor(self.prinxy), dtype=int), np.array(np.ceil(self.prinxy), dtype=int)
        if np.all(f_prinxy==c_prinxy):
            return self.calc_vintaged_stock_rolloff(np.array(self.prinxy, dtype=int), mode='remaining')
        else:
            cdef np.ndarray[DTYPE_F_t, ndim=2] f_rolloff = self.calc_vintaged_stock_rolloff(f_prinxy, mode='remaining')
            cdef np.ndarray[DTYPE_F_t, ndim=2] c_rolloff = self.calc_vintaged_stock_rolloff(c_prinxy, mode='remaining')
        return f_rolloff + ((self.prinxy-f_prinxy)*(c_rolloff-f_rolloff).T).T

    def update_stock(self):
        i = self.i #make an int
        self.stock[:, 0, i] = self.calc_remaining_stock_initial()
        self.stock[:, 1:i+1, i] = self.calc_remaining_stock_vintaged()
        self.stock[:, i+1, i] = self.sales_by_tech

    def account_for_specified_stock(self):
        i = self.i #make an int
        if not len(self.specified) or np.sum(self.prior_year_stock)==0:
            self.specified_sales = self.specified_stock[i]
            self.sum_specified_sales = np.sum(self.specified_sales[self.specified])
        else:
            # if you have specified sales, it supersedes natural sales (most of the time it is zero)
            self.specified_sales = self.specified_stock[i] - (self.prior_year_stock - self.rolloff)
            # a negative specified sale means you need to do early retirement
            self.sum_specified_sales = np.sum(self.specified_sales[self.specified])
            if self.sum_specified_sales > np.sum(self.prior_year_stock) + self.stock_changes[i]:
                raise RuntimeError('Specified stock in a given year is greater than the total stock')
            
            # if specified sales are negative, we need to accelerate retirement for that technology
            if np.any(self.specified_sales<0):
                for neg_index in np.nonzero(self.specified_sales<0)[0]:
                    self.update_prinxy(-self.specified_sales[neg_index], np.array([neg_index], dtype=int))
                    self.specified_sales[neg_index] = 0
                self.sum_specified_sales = np.sum(self.specified_sales[self.specified])
                # Because of the retirements, we have a new natural rolloff number
                self.update_rolloff()
            
            # We need additional early retirement to make room for specified_sales
            if round(self.sum_specified_sales, 7) > round(self.rolloff_summed + self.stock_changes[i], 7):
                cdef double incremental_retirement = self.sum_specified_sales - (self.rolloff_summed + self.stock_changes[i])
                self.update_prinxy(incremental_retirement, self.solvable)
                # Because of the retirements, we have a new natural rolloff number
                self.update_rolloff()

    def account_for_specified_retirements(self):
        i = self.i #make an int
        if (np.sum(self.prior_year_stock)>0) and (self.specified_retirements is not None) and (self.specified_retirements[i]>0):
            self.update_prinxy(self.specified_retirements[i], self.all_techs)

    def account_for_stock_shrinkage(self):
        i = self.i #make an int
        if round(self.stock_changes[i], 7) < round(self.sum_specified_sales - self.rolloff_summed, 7):
            cdef double incremental_retirement = (self.sum_specified_sales - self.rolloff_summed) - self.stock_changes[i]
            self.update_prinxy(incremental_retirement, self.solvable)
            self.update_rolloff()

    def update_rolloff(self):
        self.rolloff = self.calc_stock_rolloff(self.prinxy)
        self.rolloff_summed = np.sum(self.rolloff)

    def set_final_sales(self):
        i = self.i #make an int
        #calculate final sales
        if np.sum(self.prior_year_stock):
            self.sales_by_tech = np.dot(self.sales_share[i], self.rolloff) #natural sales
        else:
            self.sales_by_tech = np.mean(np.linalg.matrix_power(self.sales_share[i], 100), axis=1) * self.stock_changes[i]
            
        if len(self.specified):
            self.sales_by_tech[self.specified] = self.specified_sales[self.specified]
        
        if np.sum(self.sales_by_tech[self.solvable]):
            self.sales_by_tech[self.solvable] *= ((self.stock_changes[i] + self.rolloff_summed) - self.sum_specified_sales) / np.sum(self.sales_by_tech[self.solvable])
        
    def run(self):
        for self.i in range(self.num_years):
            i = self.i #make an int
            self.prinxy = np.zeros(self.num_techs) #probability of retiring in next x years
            
            self.solvable = np.nonzero(np.isnan(self.specified_stock[i]))[0]
            self.specified = np.nonzero(~np.isnan(self.specified_stock[i]))[0]
            
            #Get prior year's stock
            self.prior_year_stock = self.initial_stock if i==0 else np.sum(self.stock[:, :i+1, i-1], axis=1)

            #Get natural retirements
            self.natural_rolloff[i] = self.calc_stock_rolloff(self.prinxy)
            
            # specified early retirements are done first
            self.account_for_specified_retirements()
    
            #Get natural rolloff (with specified early retirements)
            self.update_rolloff()
            
            #We have specified stock
            self.account_for_specified_stock()
            
            #if stock change is less than specified sales minus rolloff, we need additional retirements
            self.account_for_stock_shrinkage()
            
            self.set_final_sales()
            
            self.update_stock()
            self.sales_record[i] = self.sales_by_tech
            self.rolloff_record[i] = self.rolloff

        self.early_retirements = self.rolloff_record - self.natural_rolloff
        self.new_sales = np.clip(self.sales_record - self.natural_rolloff, a_min=0, a_max=self.sales_record)
        self.replacement_sales = np.clip(self.natural_rolloff, a_min=0, a_max=self.sales_record)

        self.new_sales_fraction = self.new_sales/self.sales_record
        self.new_sales_fraction[np.isnan(self.new_sales_fraction)] = 0
        
        self.stock_new = np.zeros((self.num_techs, self.num_vintages + 1, self.num_years))
        self.stock_new[:, 1:, :] = np.transpose(np.transpose(self.stock[:, 1:, :], [2, 1, 0])*self.new_sales_fraction, [2, 1, 0])
        self.stock_new[:, 0, :] *= np.transpose(np.transpose(self.stock[:, 0, :])*self.new_sales_fraction[0])
        
        self.stock_replacement = np.zeros((self.num_techs, self.num_vintages + 1, self.num_years))
        self.stock_replacement[:, 1:, :] = np.transpose(np.transpose(self.stock[:, 1:, :], [2, 1, 0])*(1-self.new_sales_fraction), [2, 1, 0])
        self.stock_replacement[:, 0, :] *= np.transpose(np.transpose(self.stock[:, 0, :])*(1-self.new_sales_fraction[0]))

    def return_formatted_outputs(self):
        cdef tuple shape1 = (self.num_techs * (self.num_vintages + 1), self.num_years)
        cdef tuple shape2 = (self.num_techs * self.num_years)
        # stock
        # stock new
        # stock replacement
        # natural rolloff
        # early retirements
        # total sales
        # new sales
        # replacement sales
        return (np.reshape(self.stock, shape1),
                np.reshape(self.stock_new, shape1),
                np.reshape(self.stock_replacement, shape1),
                np.reshape(self.natural_rolloff, shape2),
                np.reshape(self.early_retirements, shape2),
                np.reshape(self.sales_record, shape2),
                np.reshape(self.new_sales, shape2),
                np.reshape(self.replacement_sales, shape2))
                





