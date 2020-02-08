
import os
import pdb
import pandas as pd
from energyPATHWAYS.time_series import TimeSeries
from energyPATHWAYS.util import df_slice, level_specific_indexer

ep_emissions_input = r'C:\Users\ryandrewjones\Dropbox (EER)\Science Paper 2019\results\EP\combined_outputs\c_emissions.csv'
rio_emissions_input = r'C:\Users\ryandrewjones\Dropbox (EER)\Science Paper 2019\results\RIO\_aggregate_outputs\total_emissions.csv'

ep_emissions = pd.read_csv(ep_emissions_input, delimiter=',')
ep_emissions = ep_emissions.set_index([col for col in ep_emissions.columns if col not in ['MEGATONNE']]).sort_index()
years = list(ep_emissions.index.get_level_values('YEAR').unique())

rio_emissions = pd.read_csv(rio_emissions_input, delimiter=',')
rio_emissions['run name'] = [name.upper() for name in rio_emissions['run name'].values]
rio_emissions = rio_emissions.set_index([col for col in rio_emissions.columns if col not in ['value']]).sort_index()
rio_emissions = rio_emissions.xs('total emissions', level='output')

rio_emissions.index.get_level_values('product fuel').unique()
ignore_products = ['carbon sequestration_1', 'carbon sequestration_10', 'carbon sequestration_11', 'carbon sequestration_2', 'carbon sequestration_3', 'carbon sequestration_4', 'carbon sequestration_5',
                    'carbon sequestration_6', 'carbon sequestration_7', 'carbon sequestration_8', 'carbon sequestration_9','industrial co2', 'product and bunkering co2']
keep_products = list(set(rio_emissions.index.get_level_values('product fuel').unique()) - set(ignore_products))
rio_emissions = df_slice(rio_emissions, keep_products, 'product fuel')
rio_emissions = rio_emissions.groupby(level=['run name', 'year']).sum()
rio_emissions /= 1000. # make it megatons
rio_emissions_years = rio_emissions.index.get_level_values('year').unique()
rio_emissions = TimeSeries.clean(rio_emissions, newindex=years, time_index_name='year', interpolation_method='linear_interpolation')
rio_emissions_scenarios = rio_emissions.index.get_level_values('run name').unique()

#filter years
# ep_emissions = df_slice(ep_emissions, rio_emissions_years, 'YEAR', reset_index=True)

ep_final_energy_no_scale = ['product and bunkering co2', 'industrial co2', 'industrial captured co2', 'export Carbon Sequestration']
assert set(ep_final_energy_no_scale).issubset(ep_emissions.index.get_level_values('FINAL_ENERGY').unique())
final_energy_yes_scale = list(set(ep_emissions.index.get_level_values('FINAL_ENERGY').unique()) - set(ep_final_energy_no_scale))

def scale(df):
    year = df.index.get_level_values('YEAR').unique()[0]
    scenario = df.index.get_level_values('SCENARIO').unique()[0]
    if scenario not in rio_emissions_scenarios:
        print year, scenario, "RIO scenario not found"
        return df
    target_emissions = rio_emissions.loc[scenario, year]['value']

    df_scale = df.loc[level_specific_indexer(df, ['EXPORT/DOMESTIC', 'FINAL_ENERGY'], [['DOMESTIC'], final_energy_yes_scale]),]
    ep_current_emissions = df_scale.sum()['MEGATONNE']
    scaler = target_emissions / ep_current_emissions
    print year, scenario, scaler
    df_scale *= scaler

    piece2 = df.loc[level_specific_indexer(df, ['EXPORT/DOMESTIC', 'FINAL_ENERGY'], [['EXPORT'], final_energy_yes_scale]),]
    piece3 = df.loc[level_specific_indexer(df, 'FINAL_ENERGY', [ep_final_energy_no_scale]),]

    assert len(df_scale) + len(piece2) + len(piece3) == len(df)

    df_return = pd.concat([df_scale.reset_index(), piece2.reset_index(), piece3.reset_index()]).set_index(df.index.names).sort_index()
    return df_return

ep_emissions = ep_emissions.groupby(level=['TIMESTAMP', 'SCENARIO', 'YEAR']).apply(scale)
# interpolate between all years
# ep_emissions = TimeSeries.clean(ep_emissions, newindex=years, time_index_name='YEAR', interpolation_method='linear_interpolation')

print 'saving scaled emissions'
ep_emissions.to_csv(r'C:\Users\ryandrewjones\Dropbox (EER)\Science Paper 2019\results\EP\combined_outputs\c_emissions_scaled.csv')
