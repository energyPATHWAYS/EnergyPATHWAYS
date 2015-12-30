# -*- coding: utf-8 -*-
"""
Created on Thu Aug 06 13:07:14 2015

@author: Ryan Jones
"""


class DemandTechnology:
    def __init__(self, drivers, ID, **kwargs):
        self.ID = ID
        self.drivers = drivers
        for col, att in util.object_att_from_table('DemandTechs', ID):
            setattr(self, col, att)
        self.stocks = {}

    def add_stock(self, GAU=None, DAU=None):
        if (GAU, DAU) in self.stocks:
            # ToDo note that a technology was added twice
            return
        self.stocks[GAU, DAU] = DemandStock()

    def tech_efficiency(self, ID, efficiency, start=None, end=None):
        """
            returns function parameters based on identification of efficiency type - main or aux
            """
        vintage_start = int(cfgfile.get('vintage', 'start_year'))
        vintage_end = int(cfgfile.get('vintage', 'end_year'))
        vintages = np.arange(vintage_start, vintage_end + 1)
        model_start_year = int(cfgfile.get('case', 'model_start_year'))
        model_end_year = int(cfgfile.get('case', 'model_end_year'))
        years = np.arange(model_start_year, model_end_year + 1)
        # years = np.arange (start, end)
        # vintages = np.arange (start, end)
        stock = self.stock
        if efficiency == "main":
            efficiency_key = 'main_energy_efficiency'
            ref_ID = stock.techs[ID].reference_main_efficiency_id
            decay = 'main_energy_efficiency_decay'
        else:
            efficiency_key = 'aux_energy_efficiency'
            ref_ID = stock.techs[ID].reference_aux_efficiency_id
            decay = 'aux_energy_efficiency_decay'
        eff_def = stock.techs[ID].efficiency_definition
        if eff_def == "absolute":
            ref_ID = ID
        else:
            ref_eff_def = stock.techs[ref_ID].efficiency_definition
            if ref_eff_def == "relative":
                error_text = "reference technology for technology %s not defined in absolute terms" % ID
                raise ValueError(error_text)
            else:
                pass
        # units to convert efficiency values to
        sd_unit_type = self.service_demand.unit_type
        sd_unit = self.service_demand.unit_base
        energy_unit = cfgfile.get('case', 'energy_unit')
        # converts efficiency values of technologies that are defined in
        # absolute terms ex. miles/gallon for subsectors with inputs defined
        # in energy service terms ex. kilometers to consistent efficiency
        # units of energy_unit/service_demand_unit ex. gigajoule/kilometer
        if eff_def == 'absolute' and sd_unit_type == 'service':
            eff = util.efficiency_convert(getattr(stock.techs[ID], efficiency_key),
                                          stock.techs[ID].efficiency_numerator_unit,
                                          stock.techs[ID].efficiency_denominator_unit,
                                          energy_unit, sd_unit)
            eff = TimeSeries.clean(eff, extrapolation_method="nearest", newindex=vintages)
            clean_eff_numerator_unit = energy_unit
            clean_eff_denominator_unit = sd_unit
        # no conversion is used if the service_demand unit is energy, as
        # the efficiency values will be normalized in later calculations
        elif eff_def == 'absolute' and sd_unit_type == 'energy':
            eff = getattr(stock.techs[ID], efficiency_key)
            eff = TimeSeries.clean(eff, extrapolation_method="nearest", newindex=vintages)
            clean_eff_numerator_unit = stock.techs[ID].efficiency_numerator_unit
            clean_eff_denominator_unit = stock.techs[ID].efficiency_denominator_unit
        # converts efficiency values for reference technologies
        # that are defined in absolute terms ex. miles/gallon for
        # subsectors with inputs defined in energy service terms ex.
        # kilometers to consistent efficiency units of
        # energy_unit/service_demand_unit ex. gigajoule/kilometer
        elif eff_def == "relative" and sd_unit_type == 'service':
            ref_eff = util.efficiency_convert(
                getattr(stock.techs[ref_ID], efficiency_key),
                stock.techs[ref_ID].efficiency_numerator_unit,
                stock.techs[ref_ID].efficiency_denominator_unit, energy_unit,
                sd_unit)
            ref_eff = TimeSeries.clean(ref_eff, extrapolation_method="nearest", newindex=vintages)
            eff = getattr(stock.techs[ID], efficiency_key)
            eff = TimeSeries.clean(eff, extrapolation_method="nearest", newindex=vintages)
            eff *= ref_eff
            clean_eff_numerator_unit = energy_unit
            clean_eff_denominator_unit = sd_unit
        # no conversion is used if the service_demand unit is energy, as
        # the efficiency values will be normalized in later calculations.
        # efficiency values are multiplied by reference technology efficiencies
        else:
            ref_eff = getattr(stock.techs[ref_ID], efficiency_key)
            ref_eff = TimeSeries.clean(ref_eff, extrapolation_method="nearest", newindex=vintages)
            eff = getattr(stock.techs[ID], efficiency_key)
            eff = TimeSeries.clean(eff, extrapolation_method="nearest",
                                   newindex=vintages)
            eff *= ref_eff
            clean_eff_numerator_unit = stock.techs[ref_ID].efficiency_numerator_unit
            clean_eff_denominator_unit = stock.techs[ref_ID].efficiency_denominator_unit
        decay_df = stockrollover.vintage_age(years, vintages)
        decay_df *= stockrollover.vintage_exist(years, vintages)
        if eff_def == "absolute":
            decay_df = 1 - (decay_df * getattr(stock.techs[ID], decay))
        else:
            decay_df = 1 - (decay_df * getattr(stock.techs[ref_ID], decay))
        eff = eff.transpose()

        eff = (decay_df.values * eff.values, years, vintages)
        setattr(stock.techs[ID], 'clean_%s_efficiency' % efficiency, eff)
        setattr(stock.techs[ID], 'clean_%s_efficiency_numerator_unit' % efficiency, clean_eff_numerator_unit)
        setattr(stock.techs[ID], 'clean_%s_efficiency_denominator_unit' % efficiency, clean_eff_denominator_unit)

    def stock_efficiency(self):
        sd_unit_type = self.service_demand.unit_type
        if sd_unit_type == 'energy':
            # ==============================================================================
            # in order to calculate a normalized efficiency for a stock, which is
            # used when the service demand is defined in energy terms, all
            #             absolute efficiency values must be in the same units. This code converts
            #             all efficiency values to the same units.
            # ==============================================================================
            primary_key = self.stock.techs[min(self.stock.techs.keys())]
            setattr(self.stock, 'primary_efficiency_ID', primary_key)
            setattr(self.stock, 'primary_efficiency_numerator_unit',
                    stock.techs[primary_key].clean_main_efficiency_numerator_unit)
            setattr(self.stock, 'primary_efficiency_denominator_unit',
                    stock.techs[primary_key].clean_main_efficiency_denominator_unit)
            for key in self.stock.techs:
                for eff_type in ['main', 'aux']:
                    data = getattr(self.stock.techs[key],
                                   'clean_%s_efficiency' % eff_type)
                    unit_from_denominator = getattr(self.stock.techs[key],
                                                    'clean_%s_efficiency_denominator_unit' % eff_type)
                    unit_from_numerator = getattr(self.stock.techs[key],
                                                  'clean_%s_efficiency_numerator_unit' % eff_type)
                    unit_to_denominator = getattr(self.stock, 'primary_efficiency_denominator_unit')
                    unit_to_numerator = getattr(self.stock, 'primary_efficiency_numerator_unit')
                    eff = util.efficiency_convert(data, unit_from_numerator, unit_from_denominator, unit_to_numerator,
                                                  unit_to_denominator)


class DemandStock(Stock):
    """
    Demand-side equipment stock.

    Attributes
    ----------
    final_energy_list : list
        ex. {"electricity", "pipeline gas"}
        List of final_energy types demanded by techs in the stock.
    stocksubsector: instance of class StockSubsector
    """


# def __init__(self):
# self.service_demand = ServiceDemand()
#
# def add_service_demand(self):
#        self.service_demand = ServiceDemand()
#
#    def cf_to_unit(self, unit, service_demand_unit):
#        """converts capacity factor stock units to energy output units based on service demand unit"""
#
#    def tech_lookup(self, unit, stocksubsector):
#        """return dictionary techs from tech database based on a lookup of unit and stockSubsector."""
#
#    def final_energy_list(self, techs):
#        """return all final energy types from attributes of tech dictionary"""
#
#    def add_demand_techs(self, demand_tech_id):
#        if demand_tech_id in self.techs:
#            return
#        self.techs[demand_tech_id] = technology.DemandTech(demand_tech_id)


class Stock(DataMapFunctions):
    """
    """

    def __init__(self, drivers, ID, technology_id=None, **kwargs):
        self.ID = ID
        self.sql_ID_table = cfgfile.get('db_table_name', 'DemandStock')
        self.sql_data_table = cfgfile.get('db_table_name', 'DemandStockData')
        self.technology_id = technology_id
        self.drivers = drivers
        self.mapped = False
        for col, att in util.object_att_from_table(self.sql_ID_table, ID):
            setattr(self, col, att)
        DataMapFunctions.__init__(self)
        self.read_timeseries_data()

    #        self.project('DemandStock', 'service_demand_dependent')

    #
    @staticmethod
    def stock_new(var, **kwargs):
        print kwargs['asdf']


# def stock_growth(self):
#        """combines driver and intensity attributes into a stock growth projection"""
#
#    def rollover(self):
#        """used to perform stock rollover calculations and produce stock compositions matrices of stock units by tech"""
#
#    def stock_normal(self):
#        """normalizes the stock for weighted average calculations"""
#
#    def stock_additions(self):
#        """calculates annual stock additions as a function of new and replace on burnout  by available tech"""
#
#    def stock_additions_early(self):
#        """calculates annual stock additions as a function of early replacement by available tech"""
#
#    def stock_replacement_early(self):
#        """calculates annual stock replacements by year and replaced vintage"""
#
#    def stock_output(self, output_type):
#        """calculates stock output by selected output type: physical units, efficiency, etc."""
#
#        pass

















