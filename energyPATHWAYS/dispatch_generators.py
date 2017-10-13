
import util
import numpy as np
import copy
import pandas as pd
import logging
from sklearn.cluster import KMeans
import pdb
import dispatch_maintenance

def cluster_generators(n_clusters, pmax, marginal_cost, FORs, MORs, must_run, pad_stack=False, zero_mc_4_must_run=False):
    """ Cluster generators is a function that takes a generator stack and clusters them by marginal_cost and must run status.

    clustering is done with sklearn KMeans

    Args:
        n_clusters (int): controls the number of output generators (must between 1 and the number of generators)
        pmax (1d array): pmax of each generator
        marginal_cost (1d array): the full marginal marginal cost for each generator
        FORs (1d array): forced outage rates by generator
        MORs (1d array): maintenance rates by generator
        must_run (bool 1d array): boolean array indicating whether each generator is must run
        pad_stack (bool): if true, the highest cost dispatchable generator has it's capacity increased
        zero_mc_4_must_run (bool): if true, must run generators are returned with zero marginal cost

    Returns:
        clustered: a dictionary with generator clusters
    """
    ind = np.nonzero(pmax)
    pmax = pmax[ind]
    marginal_cost = marginal_cost[ind]
    FORs = FORs[ind]
    MORs = MORs[ind]
    must_run = must_run[ind]
    assert n_clusters>= 1
    assert n_clusters <= len(pmax)
    new_mc = copy.deepcopy(marginal_cost)  # copy mc before changing it
    if zero_mc_4_must_run:
        new_mc[np.nonzero(must_run)] = 0
    # clustering is done here
    cluster = KMeans(n_clusters=n_clusters, precompute_distances='auto', random_state=1)
    factor = (max(marginal_cost) - min(marginal_cost)) * 10
    fit = cluster.fit_predict(np.vstack((must_run * factor, new_mc)).T)
    num_clusters_found = max(fit) + 1
    n_clusters = min(n_clusters, num_clusters_found)

    # helper functions for results
    group_sum = lambda c, a: sum(a[fit == c])
    group_wgtav = lambda c, a, b: 0 if group_sum(c, a) == 0 else np.dot(a[fit == c], b[fit == c]) / group_sum(c, a)

    combined_rate = _get_combined_outage_rate(FORs, MORs)
    derated_pmax = pmax * (1 - combined_rate)

    clustered = {}
    clustered['marginal_cost'] = np.array([group_wgtav(c, derated_pmax, new_mc) for c in range(n_clusters)])
    order = np.argsort(clustered['marginal_cost'])  # order the result by marginal cost
    clustered['marginal_cost'] = clustered['marginal_cost'][order]
    clustered['derated_pmax'] = np.array([group_sum(c, derated_pmax) for c in range(n_clusters)])[order]
    clustered['pmax'] = np.array([group_sum(c, pmax) for c in range(n_clusters)])[order]
    clustered['FORs'] = np.array([group_wgtav(c, pmax, FORs) for c in range(n_clusters)])[order]
    clustered['MORs'] = np.array([group_wgtav(c, pmax, MORs) for c in range(n_clusters)])[order]
    clustered['must_run'] = np.array([round(group_wgtav(c, pmax, must_run)) for c in range(n_clusters)], dtype=int)[
        order]

    # check the result
    #        np.testing.assert_almost_equal(sum(clustered['pmax'][np.where(clustered['must_run']==0)]), sum(pmax[np.where(must_run==0)]))

    # if we are padding the stack, add a generator at the end of the stack that is high cost
    if pad_stack:
        for name in ['FORs', 'MORs', 'must_run']:
            clustered[name] = np.concatenate((clustered[name], [clustered[name][-1]]))
        for name in ['derated_pmax', 'pmax']:
            clustered[name] = np.concatenate((clustered[name], [sum(clustered[name])]))
        clustered['marginal_cost'] = np.concatenate((clustered['marginal_cost'], [10 * clustered['marginal_cost'][-1]]))

    return clustered

##################################################################
##################################################################
## GENERATOR DISPATCH (LOOKUP HEURISTIC)
##################################################################
def _get_combined_outage_rate(FORs, MORs):
    return MORs + (1 - MORs) * FORs


def _get_marginal_cost_order(marginal_cost, must_run=None):
    if must_run is None:
        must_run = np.zeros_like(marginal_cost)
    must_run_index, dispat_index = np.nonzero(must_run)[0], np.nonzero(must_run == 0)[0]
    sorted_cost = np.argsort(marginal_cost)
    marginal_cost_order = np.concatenate(([mc for mc in sorted_cost if mc in must_run_index],
                                          [mc for mc in sorted_cost if mc in dispat_index])).astype(int)
    return marginal_cost_order


def solve_gen_dispatch(load, pmax, marginal_cost, FORs, MORs, must_run, gen_categories=None):
    marginal_cost_order = _get_marginal_cost_order(marginal_cost, must_run)

    combined_rate = _get_combined_outage_rate(FORs, MORs)
    derated_capacity = pmax * (1 - combined_rate)

    sorted_pmax = derated_capacity[marginal_cost_order]
    sorted_marginal_cost = marginal_cost[marginal_cost_order]
    cum_pmax = np.cumsum(sorted_pmax)

    must_run_sum = sum((pmax * (1 - combined_rate))[np.nonzero(must_run)])
    load_w_must_run = np.clip(load, a_min=must_run_sum, a_max=None)

    dispatch = np.zeros((len(derated_capacity), len(load)))
    market_prices = []
    for h, look in enumerate(load_w_must_run):
        height = np.where(cum_pmax < look)[0]
        dispatch[height, h] = sorted_pmax[height]
        if len(height) and len(height) != len(pmax):
            marg = height[-1] + 1
            dispatch[marg, h] = look - cum_pmax[height[-1]]
            market_prices.append(sorted_marginal_cost[marg])
        else:
            dispatch[0, h] = look
            market_prices.append(sorted_marginal_cost[0])
    dispatch = dispatch[np.argsort(marginal_cost_order)]

    dispatch_by_generator = dispatch.sum(axis=1)
    production_cost = (marginal_cost * dispatch.T).sum(axis=1)
    gen_dispatch_shape = dispatch.sum(axis=0)
    dispatch_by_category = pd.DataFrame(dispatch, index=gen_categories).groupby(level=0).sum().T

    return market_prices, production_cost, dispatch_by_generator, gen_dispatch_shape, dispatch_by_category


def _format_gen_dispatch_inputs(num_groups, pmaxs, marginal_costs, FOR=None, MOR=None, must_runs=None,
                                capacity_weights=None):
    zero_clip = lambda x: np.clip(x, 0, None)
    pmaxs, marginal_costs, FOR, MOR = zero_clip(pmaxs), zero_clip(marginal_costs), zero_clip(FOR), zero_clip(MOR)
    marginal_costs = np.tile(marginal_costs, (num_groups, 1)) if len(marginal_costs.shape) == 1 else marginal_costs
    pmaxs = np.tile(pmaxs, (num_groups, 1)) if len(pmaxs.shape) == 1 else pmaxs
    FOR = np.zeros_like(pmaxs) if FOR is None else (np.tile(FOR, (num_groups, 1)) if len(FOR.shape) == 1 else FOR)
    MOR = np.zeros_like(pmaxs) if MOR is None else (np.tile(MOR, (num_groups, 1)) if len(MOR.shape) == 1 else MOR)
    must_runs = np.ones_like(pmaxs, dtype=bool) if must_runs is None else np.array(
        np.tile(must_runs, (num_groups, 1)) if len(must_runs.shape) == 1 else must_runs, dtype=bool)
    capacity_weights = np.full(pmaxs.shape[1], 1 / float(len(pmaxs.T)),
                               dtype=float) if capacity_weights is None else np.array(capacity_weights, dtype=float)
    return marginal_costs, pmaxs, FOR, MOR, must_runs, capacity_weights


def _get_stock_changes(load_groups, pmaxs, FOR, MOR, capacity_weights, reserves, thermal_capacity_multiplier):
    combined_rates = [_get_combined_outage_rate(FOR[i], MOR[i]) for i in range(len(load_groups))]
    max_by_load_group = np.array([max(group) * (1 + reserves) for group in load_groups])
    cap_by_load_group = np.array([sum(pmaxs[i] * thermal_capacity_multiplier[i] * (1 - combined_rates[i])) for i in
                                  range(len(max_by_load_group))])
    shortage_by_group = max_by_load_group - cap_by_load_group
    order = [i for i in np.argsort(shortage_by_group)[-1::-1] if shortage_by_group[i] > 0]

    stock_changes = np.zeros(len(capacity_weights))
    for i in order:
        derated_capacity = sum((pmaxs[i] + stock_changes) * (1 - combined_rates[i]))
        residual_for_load_balance = max_by_load_group[i] - derated_capacity
        # we need more capacity
        if residual_for_load_balance > 0:
            if all(combined_rates[i][capacity_weights != 0] > .5):
                logging.warning('All generators queued for capacity expansion have outage rates higher than 50%, this can cause issues')
            ncwi = np.nonzero((capacity_weights!=0) & (combined_rates[i]<1))[0]
            normed_capacity_weights = capacity_weights[ncwi] / sum(capacity_weights[ncwi])
            stock_changes[ncwi] += normed_capacity_weights * residual_for_load_balance / (1 - combined_rates[i][ncwi])
    cap_by_load_group = np.array([sum((pmaxs[i] + stock_changes) * (1 - combined_rates[i])) for i in range(len(max_by_load_group))])
    final_shortage_by_group = max_by_load_group - cap_by_load_group
    if not all(np.round(final_shortage_by_group, 7) <= 0):
        logging.error('_get_stock_changes did not build enough capacity')
    return stock_changes


def generator_stack_dispatch(load, pmaxs, marginal_costs, dispatch_periods=None, FOR=None, MOR=None, must_runs=None,
                             capacity_weights=None, gen_categories=None, return_dispatch_by_category=False,
                             reserves=.07, thermal_capacity_multiplier=None):
    """ Dispatch generators to a net load signal
    Args:
        load: net load shape (ndarray[h])
        pmaxs: max capacity (ndarray[d, n])
        marginal_costs: marginal generator operating cost (ndarray[d, n])
        dispatch_periods: identifiers for each load hour (ndarray[d]) defaults to None
        FOR: generator forced outage rates (ndarray[d, n]) defaults to zero for each generator
        MOR: maintenance outage rates (ndarray[d, n]) defaults to zero for each generator
        must_run: generator must run status (ndarray[d, n]) defaults to False for each generator
        periods_per_year: number of periods per year, used to calculate capacity factors, default is 8760
    Returns:
        dispatch_results: dictionary
         --market_price: hourly market price over the dispatch (ndarray[h])
         --production_cost: hourly production cost over the dispatch (ndarray[h])
         --gen_cf: generator capacity factors over the dispatch period (ndarray[n])
    """
    count = lambda x: len(x.T) if x.ndim > 1 else len(x)
    if count(pmaxs) != count(marginal_costs):
        raise ValueError('Number of generator pmaxs must equal number of marginal_costs')

    if capacity_weights is not None and capacity_weights.ndim > 1:
        raise ValueError('capacity weights should not vary across dispatch periods')

    load_groups = (load,) if dispatch_periods is None else np.array_split(load,
                                                                          np.where(np.diff(dispatch_periods) != 0)[
                                                                              0] + 1)
    num_groups = len(load_groups)

    marginal_costs, pmaxs, FOR, MOR, must_runs, capacity_weights = _format_gen_dispatch_inputs(num_groups,
                                                                                                        pmaxs,
                                                                                                        marginal_costs,
                                                                                                        FOR, MOR,
                                                                                                        must_runs,
                                                                                                        capacity_weights)

    market_prices, production_costs, gen_dispatch_shape, dispatch_by_category_df = [], [], [], []
    gen_energies = np.zeros(pmaxs.shape[1])

    stock_changes = _get_stock_changes(load_groups, pmaxs, FOR, MOR, capacity_weights, reserves,
                                                thermal_capacity_multiplier)

    for i, load_group in enumerate(load_groups):
        market_price, production_cost, gen_energy, shape, dispatch_by_category = solve_gen_dispatch(
            load_group, pmaxs[i] + stock_changes, marginal_costs[i], FOR[i], MOR[i], must_runs[i], gen_categories)
        market_prices += list(market_price)
        production_costs += list(production_cost)
        gen_dispatch_shape += list(shape)
        gen_energies += gen_energy
        dispatch_by_category_df.append(dispatch_by_category)

    if return_dispatch_by_category:
        dispatch_by_category_df = pd.concat(dispatch_by_category_df).reset_index(drop=True)
    else:
        dispatch_by_category_df = None

    gen_cf = gen_energies / np.max((pmaxs + stock_changes), axis=0) / float(len(load))
    gen_cf[np.nonzero(np.max((pmaxs + stock_changes), axis=0) == 0)] = 0
    dispatch_results = dict(zip(
        ['market_price', 'production_cost', 'generation', 'gen_cf', 'gen_dispatch_shape', 'stock_changes',
         'dispatch_by_category'],
        [market_prices, production_costs, gen_energies, gen_cf, gen_dispatch_shape, stock_changes,
         dispatch_by_category_df]))

    for key, value in dispatch_results.items():
        if key == 'dispatch_by_category' and return_dispatch_by_category == False:
            continue
        if np.any(~np.isfinite(value)):
            raise ValueError("non finite numbers found in the {} results".format(key))

    return dispatch_results

def increase_pmax_with_capacity_weights(pmaxs, capacity_weights, scale_amount=0.03):
    """
    This function is necessary because without some token capacity for generators we may build, the model will not schedule maintenance properly
    """
    has_capacity_weight = np.nonzero(capacity_weights)[0]
    has_zero_pmax = np.nonzero(pmaxs==0)[0]
    capacity_weight_no_capacity = np.intersect1d(has_capacity_weight, has_zero_pmax)
    capacity_to_add = pmaxs.sum() * scale_amount
    pmaxs2 = copy.deepcopy(pmaxs)
    pmaxs2[capacity_weight_no_capacity] += capacity_to_add / len(capacity_weight_no_capacity)
    return pmaxs2

def run_thermal_dispatch(params):
    dispatch_geography = params[0]
    thermal_dispatch_df = params[1]
    columns = params[1].columns #save for later since we are doing a squeeze
    thermal_dispatch_df = thermal_dispatch_df.squeeze().unstack('IO')
    dispatch_geography_index = params[2]
    load = util.df_slice(params[3], dispatch_geography, dispatch_geography_index)

    return_dispatch_by_category = params[4]
    reserves = params[5]
    months = load.index.get_level_values('weather_datetime').month
    weeks = load.index.get_level_values('weather_datetime').week
    load = load.values.flatten()
    pmaxs = thermal_dispatch_df['capacity'].values
    marginal_costs = thermal_dispatch_df['cost'].values
    MOR = thermal_dispatch_df['maintenance_outage_rate'].values
    FOR = thermal_dispatch_df['forced_outage_rate'].values
    must_runs = thermal_dispatch_df['must_run'].values
    capacity_weights = thermal_dispatch_df['capacity_weights'].values
    thermal_capacity_multiplier = thermal_dispatch_df['thermal_capacity_multiplier'].values
    # grabs the technology from the label
    gen_categories = [int(s.split(', ')[1].rstrip('L')) for s in thermal_dispatch_df.index.get_level_values('thermal_generators')]

    pmaxs2 = increase_pmax_with_capacity_weights(pmaxs, capacity_weights)
    maintenance_rates = dispatch_maintenance.schedule_generator_maintenance(load=load, pmaxs=pmaxs2, annual_maintenance_rates=MOR, dispatch_periods=weeks, marginal_costs=marginal_costs)
    dispatch_results = generator_stack_dispatch(load=load, pmaxs=pmaxs, marginal_costs=marginal_costs, MOR=maintenance_rates,
                                                                    FOR=FOR, must_runs=must_runs, dispatch_periods=weeks, capacity_weights=capacity_weights,
                                                                    gen_categories=gen_categories, return_dispatch_by_category=return_dispatch_by_category,
                                                                    reserves=reserves, thermal_capacity_multiplier=thermal_capacity_multiplier)

    for output in ['gen_cf', 'generation', 'stock_changes']:
        thermal_dispatch_df[output] = dispatch_results[output]

    thermal_dispatch_df = thermal_dispatch_df.stack('IO').to_frame()
    thermal_dispatch_df.columns = columns

    return (thermal_dispatch_df, dispatch_results)