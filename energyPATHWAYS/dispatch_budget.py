
import util
import numpy as np 
from scipy import optimize
import logging
import pdb 

##################################################################
##################################################################
## POWER TO GAS, ELECTROLYSIS AND HYDRO DISPATCH
##################################################################
def residual_energy(load_cutoff, load, energy_budget, pmin=0, pmax=None):
    """
    energy_budget > 0 is generation (hydro)
    energy_budget < 0 is load (P2G)
    """
    dct = (1 if energy_budget> 0 else -1)
    return np.sum(np.clip(dct * load[dct * load > dct * (load_cutoff + pmin)] - dct * load_cutoff, a_min=pmin,
                          a_max=pmax) - pmin) + len(load) * pmin - dct * energy_budget


def dispatch_shape(load, load_cutoff, dct, pmin=0, pmax=None):
    """
    dct = 1 is generation (hydro)
    dct = -1 is load (P2G)
    """
    dispatch = np.zeros_like(load) - dct * pmin
    dispatch[dct * load > dct * (load_cutoff + pmin)] -= dct * (
    np.clip(dct * load[dct * load > dct * (load_cutoff + pmin)] - dct * load_cutoff, a_min=pmin, a_max=pmax) - pmin)
    return dispatch * -dct  # always positive


def solve_for_load_cutoff(load, energy_budget, pmin=0, pmax=None):
    lowest = min(load) - pmax - 1
    highest = max(load) + pmax + 1
    load_cutoff = optimize.bisect(residual_energy, lowest, highest, args=(load, energy_budget, pmin, pmax))
    if lowest == highest:
        return lowest
    return load_cutoff


def solve_for_dispatch_shape(load, energy_budget, pmin=0, pmax=None):
    if abs(energy_budget) < pmin * len(load):
        logging.debug('During dispatch to energy budget, the pmin is too large for the given energy budget')
        return np.ones_like(load) * energy_budget / len(load)

    if pmax is not None and abs(energy_budget) > pmax * len(load):
        logging.debug('During dispatch to energy budget, the pmax is too small for the given energy budget')
        return np.ones_like(load) * pmax

    load_cutoff = solve_for_load_cutoff(load, energy_budget, pmin, pmax)
    return dispatch_shape(load, load_cutoff, (1 if energy_budget > 0 else -1), pmin, pmax)


def dispatch_to_energy_budget(load, energy_budgets, dispatch_periods=None, pmins=0, pmaxs=None):
    """ Dispatch to energy budget produces a dispatch shape for a load or generating energy budget

    Common uses would be hydro, power2gas, and hydrogen electrolysis

    energy_budget > 0 is generation (hydro)
    energy_budget < 0 is load (P2G)

    Args:
        load: net load shape (ndarray)
        energy_budgets: availabile energy (float or ndarray)
        dispatch_periods: identifiers for each load hour (ndarray) defaults to None
        pmins: min power for the dispatch (float or ndarray) defaults to zero
        pmaxs: max power for the dispatch (float or ndarray) defaults to None

    Returns:
        dispatch: (ndarray)

    This function solves based on a huristic, which returns the same solution as optimization

    Note that every change in dispatch period results in a new dispatch group, for instance,
     range(12) + range(12) will result in 24 dispatch groups, not 12, as might be expected.
    """
    if dispatch_periods is not None and len(dispatch_periods) != len(load):
        raise ValueError('Dispatch period identifiers must match the length of the load data')

    # spit the load into dispatch groups
    load_groups = (load,) if dispatch_periods is None else np.array_split(load,
                                                                          np.where(np.diff(dispatch_periods) != 0)[
                                                                              0] + 1)
    energy_budgets = util.ensure_iterable_and_not_string(energy_budgets)
    pmins, pmaxs = util.ensure_iterable_and_not_string(pmins), util.ensure_iterable_and_not_string(pmaxs)

    if len(energy_budgets) != len(load_groups):
        raise ValueError('Number of energy_budgets must match the number of dispatch periods')

    if len(pmins) != len(load_groups):
        if len(pmins) == 1:
            # expand to match the number of load groups
            pmins *= len(load_groups)
        else:
            raise ValueError('Number of pmin values must match the number of dispatch periods')

    if len(pmaxs) != len(load_groups):
        if len(pmaxs) == 1:
            # expand to match the number of load groups
            pmaxs *= len(load_groups)
        else:
            raise ValueError('Number of pmax values must match the number of dispatch periods')

    # call solve for dispatch on each group and concatenate
    return np.concatenate([solve_for_dispatch_shape(load_group, energy_budget, pmin, pmax)
                           for load_group, energy_budget, pmin, pmax in zip(load_groups, energy_budgets, pmins, pmaxs)])