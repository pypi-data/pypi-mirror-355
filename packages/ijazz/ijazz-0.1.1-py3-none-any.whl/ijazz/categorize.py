import numpy as np
import pandas as pd

def categorize(df: pd.DataFrame, category_dict: dict, cut="", prefix='cat', var_prefixes=None, var_suffixes=['1','2']) -> np.ndarray:
    """Create the categories for both lepton based on a dataframe containing the categorisation variable per lepton
    under the form var1, var2 for lepton 1 and lepton 2, the name of the variables to categorize upon are specified in the 
    the category dictionnary along with the corresponding bining.

    Args:
        df (pd.DataFrame): input dataframe containing the variable to categorize
        category_dict (dict): dictionary for categorisation, e.g. {'pt': [25, 50, 100], 'abs_eta': [0, 1, 2]}
        cut (str, optional): cut to be use if df.eval(cut) to apply a selection. Defaults to "".
        prefix (str, optional): prefix used for the categorisation. Defaults to 'cat'.

    Returns:
        np.ndarray: array with the category numbers that have been created
    """
 
    n_cat_bins = [len(bin)-1 for bin in category_dict.values()]
    categories = np.arange(np.prod(n_cat_bins)).reshape(*n_cat_bins)
    selection = True
    idx = slice(0, None) if cut == "" else df.eval(cut)
    if var_prefixes is None:
        var_prefixes = ['','']
    else:
        var_suffixes = ['','']
    for name, bins in category_dict.items():
        for ele_suffix, ele_prefix in zip(var_suffixes, var_prefixes):
            df[f'{prefix}_{ele_prefix}{name}{ele_suffix}'] = np.int32(-1)
            df.loc[idx, f'{prefix}_{ele_prefix}{name}{ele_suffix}'] = (np.digitize(df.loc[idx, f"{ele_prefix}{name}{ele_suffix}"], bins) - 1).astype(np.int32)
            selection &= (df[f'{prefix}_{ele_prefix}{name}{ele_suffix}'] >= 0) & (df[f'{prefix}_{ele_prefix}{name}{ele_suffix}'] < len(bins) - 1)

    for i_ele, (ele_suffix, ele_prefix) in enumerate(zip(var_suffixes, var_prefixes)):
        i_ele += 1
        df[f'{prefix}{i_ele}'] = -1
        df.loc[selection, f'{prefix}{i_ele}'] = categories[tuple([df.loc[selection, f"{prefix}_{ele_prefix}{name}{ele_suffix}"] for name in category_dict.keys()])]
        df[f'{prefix}{i_ele}'] = df[f'{prefix}{i_ele}'].astype(np.int32)
    return categories