from ijazz.ScaleAndSmearing import IJazZSAS
from ijazz.sas_utils import parameters_from_json
import matplotlib.pyplot as plt
import tensorflow as tf
from matplotlib.pyplot import Figure, Axes
import cms_fstyle as cms
import numpy as np
import pandas as pd
from typing import Union, List, Dict, Tuple
from pathlib import Path
import copy


def ijazz_plot_results():
    """entry point for the ijazz_plot command
    """
    import argparse, sys, json
    parser = argparse.ArgumentParser(description=f'IJazZ json result plotter')
    parser.add_argument('json_file', type=str, help='json file with the fit results')
    parser.add_argument('--resp', type=float, nargs='+', default=(), help='response y range')
    parser.add_argument('--reso', type=float, nargs='+', default=(), help='resolution y range')
    parser.add_argument('-x', '--x_range', type=float, nargs='+', default=(), help='x range')
    parser.add_argument('--latex', type=str, default=None, help='json file with latex categories')
    parser.add_argument('-o', '--out', type=str, default=None, help='name of the output file')
    parser.add_argument('-d', '--dims', type=str, nargs='+', default=None, help='dimensions to plot')
    parser.add_argument('--ncol', type=int, default=1, help='number of columns for legend')
    parser.add_argument('--leg_fontsize', type=str, default='medium', help='fontsize for legend')
    parser.add_argument('--leg_title_fontsize', type=str, default='large', help='title fontsize for legend')
    parser.add_argument('-H','--hide', action='store_true', help='hide legend')

    args = parser.parse_args(sys.argv[1:])
    print(args)

    cat_latex = None
    if args.latex:
        with open(args.latex, 'r') as flatex:
            cat_latex=json.load(flatex)
        
    figs, ax = plot_results_from_json(args.json_file, dims=args.dims, x_range=args.x_range, resp_range=args.resp, reso_range=args.reso, cat_latex=cat_latex,
                                      hide_legend=args.hide, leg_ncol=args.ncol, leg_fontsize=args.leg_fontsize, leg_title_fontsize=args.leg_title_fontsize)
    plt.show()
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        print(f' --> Save plots to {out}')
        for ifig, fig in enumerate(figs):
            fig.savefig(out.with_suffix(f'.fig{ifig}' + out.suffix))


def plot_results_from_json(json_file: Union[str, Path, Dict], dims: List=None, x_range=(), x_unit='', 
              cat_latex:Dict=None, resp_range=(), reso_range=(), hide_legend=False, 
              jsons_mode='', param_to_plot=None, **kwargs) -> Tuple[List[Figure], Axes]:
    """Create a list of Axes to plot the results in the json file.
    the dimensions to plot can be specified, additional dimension are averaged over.
    Up to 3 dimensions can be plotted.

    Args:
        json_file (Union[str, Path, Dict]): json file containing the results of the IJazZ SAS fit or Dict from the json file
        dims (List, optional): name dimensions to plot (as in the categories). Defaults to None.
        x_range (tuple, optional): range of the main variable (dimension 0). Defaults to ().
        x_unit (str, optional): usint of the main varaible. Defaults to ''.
        cat_latex (Dict, optional): dictionnary mapping var name (from categories) into a latex name. Defaults to None.
        resp_range (tuple, optional): y-range of the resp axis. Defaults to ().
        reso_range (tuple, optional): y-range if the reso axis. Defaults to ().
        leg_ncol (int, optional): number of columns in the legend. Defaults to 1.
        hide_legend (bool, optional): hide the legend. Defaults to False.
        jsons_mode (str, optional): select plotting mode between 'compare' and 'ratio'. Defaults to ''.
        param_to_plot (str, optional): parameter to plot (resp or reso) if compare_jsons. Defaults to None.

    Returns:
        Tuple[Figure, Axes]: Figure and Axes of the plot.
    """
    # -- get the parameters
    if compare_jsons:= jsons_mode == 'compare':
        params_dict = {}
        for key, values in json_file.items():
            params_dict[key] = values if isinstance(values, Dict) else parameters_from_json(values)
        # params = params_dict[key]
        json_names = list(params_dict.keys())
        params_list = list(params_dict.values())
        params = params_list[0]

    elif jsons_mode == 'ratio':
        json_nominal = json_file.get('nominal')
        json_syst = json_file.get('syst')
        if json_nominal is None or json_syst is None:
            raise KeyError('the json file must contain a nominal and syst key')

        params_nominal = json_nominal if isinstance(json_nominal, Dict) else parameters_from_json(json_nominal)
        params_syst = json_syst if isinstance(json_syst, Dict) else parameters_from_json(json_syst)
        params = copy.deepcopy(params_syst)
        # params = params_nominal
        # params['resp'] = params_syst['resp'][2:,:,:] / params_nominal['resp']
        # params['eresp'] = params_syst['eresp'][2:,:,:] / params_nominal['resp']
        # params['eresp_mc'] = params_syst['eresp_mc'][2:,:,:] / params_nominal['resp']
        # params['reso'] = params_syst['reso'][2:,:,:] / params_nominal['reso']
        # params['ereso'] = params_syst['ereso'][2:,:,:] / params_nominal['reso']
        # params['ereso_mc'] = params_syst['ereso_mc'][2:,:,:] / params_nominal['reso']
        
        params['resp'] = params_syst['resp'] / params_nominal['resp']
        params['eresp'] = params_syst['eresp'] / params_nominal['resp']
        params['eresp_mc'] = params_syst['eresp_mc'] / params_nominal['resp']
        params['reso'] = params_syst['reso'] / params_nominal['reso']
        params['ereso'] = params_syst['ereso'] / params_nominal['reso']
        params['ereso_mc'] = params_syst['ereso_mc'] / params_nominal['reso']
        

    else:
        params = json_file if isinstance(json_file, Dict) else parameters_from_json(json_file)

    if not cat_latex:
        # -- define cat_latex if not given
        cat_latex = {key: key for key in params['dims']}

    if dims is None:
        # -- keep all dims by default
        dims = [key for key in params['dims']]
    
    for dim in dims:
        if dim not in cat_latex:
            cat_latex[dim] = dim

    if len(dims) > 3:
        # -- keep only the 3 first dimensions
        dims = dims[:3]

    dims_to_keep = [np.where(params['dims'] == d)[0][0] for d in dims]
    dims_to_average = [id for id, d in enumerate(params['dims']) if not d in dims]
    perm = dims_to_keep + dims_to_average
    dims_to_average = np.arange(len(dims_to_keep), len(perm))

    def reshape_param(param, par_name):
        par = tf.transpose(param[par_name], perm=perm)
        epar = tf.transpose(param[f'e{par_name}'], perm=perm)
        epar_mc = tf.transpose(param[f'e{par_name}_mc'], perm=perm)
        # avoid 0 division
        epar = tf.where(epar == 0, 1, epar)
        epar_mc = tf.where(epar_mc == 0, 1, epar_mc)

        par = tf.reduce_sum((par/ epar**2), axis=dims_to_average) / tf.reduce_sum((1 / epar**2), axis=dims_to_average)
        epar = tf.sqrt(1./ tf.reduce_sum((1 / epar**2), axis=dims_to_average))
        epar_mc = tf.sqrt(1./ tf.reduce_sum((1 / epar_mc**2), axis=dims_to_average))
        # put back errors to 0
        epar = tf.where(epar == 1, 0, epar)
        epar_mc = tf.where(epar_mc == 1, 0, epar_mc)
        shape = list(tf.shape(par).numpy()) + [1] * (3-tf.rank(par).numpy())
        return tf.reshape(par, shape), tf.reshape(epar, shape), tf.reshape(epar_mc, shape)

    if compare_jsons:

        resps, eresps, eresp_mcs = zip(*(reshape_param(param, 'resp') for param in params_list))
        resos, eresos, ereso_mcs = zip(*(reshape_param(param, 'reso') for param in params_list))
        resp, reso = np.stack(resps, axis=1), np.stack(resos, axis=1)
        eresp, ereso = np.stack(eresps, axis=1), np.stack(eresos, axis=1)
        eresp_mc, ereso_mc = np.stack(eresp_mcs, axis=1), np.stack(ereso_mcs, axis=1)
        
    
        if len(dims) < 3:
            resp = np.squeeze(resp, axis=-1)
            reso = np.squeeze(reso, axis=-1)
            eresp = np.squeeze(eresp, axis=-1)
            ereso = np.squeeze(ereso, axis=-1)
            eresp_mc = np.squeeze(eresp_mc, axis=-1)
            ereso_mc = np.squeeze(ereso_mc, axis=-1)
        
    else:
        resp, eresp, eresp_mc = reshape_param(params,'resp')
        reso, ereso, ereso_mc = reshape_param(params,'reso')

    # -- dim 0
    xbin = params['bins'][dims_to_keep[0]]
    xbin = tf.where(xbin == +np.inf, x_range[1] if len(x_range) > 1 else xbin[-2]*1.5, xbin)
    xbin = tf.where(xbin == -np.inf, x_range[0] if len(x_range) > 0 else xbin[1]/1.5, xbin)
    xval = 0.5*(xbin[1:] + xbin[:-1])
    xerr = 0.5*(xbin[1:] - xbin[:-1])
    var_ref = cat_latex[dims[0]] + x_unit

    # -- higher dimensions
    var1, var2 = None, None
    bin1, bin2 = [], []
    n_dim2 = 1
    if compare_jsons:
        json_names 
        if len(dims) > 1:
            var1 = cat_latex[dims[1]] 
            bin1 = params['bins'][dims_to_keep[1]]
            n_dim2 = len(bin1) - 1          

        if len(dims) > 2:
            var2 = cat_latex[dims[2]] 
            bin2 = params['bins'][dims_to_keep[2]]
            n_dim2 = len(bin2) - 1

            if len(params['bins'][dims_to_keep[1]]) - 1 >2:
                print('WARNING: too many bins for the 2th dimension, only the first 2 will be considered')
            
    else:
        if len(dims) > 1:
            var1 = cat_latex[dims[1]] 
            bin1 = params['bins'][dims_to_keep[1]]

        if len(dims) > 2:
            var2 = cat_latex[dims[2]] 
            bin2 = params['bins'][dims_to_keep[2]]
            n_dim2 = len(bin2) - 1

    # -- only maximum of 2 line per figure
    figs = []
    axes = []
    for ifig in range(n_dim2 // 2):
        fig, ax = plt.subplots(2, 2, figsize=(12, 4.5*2), squeeze=False)
        figs.append(fig)
        axes.append(ax)
    for ifig in range(n_dim2 % 2):
        fig, ax = plt.subplots(1, 2, figsize=(12, 4.5), squeeze=False)
        figs.append(fig)
        axes.append(ax)
    ax = np.concatenate(axes, axis=0)

    for i2 in range(resp.shape[-1]):
        leg_titles = []
        for i1 in range(len(params_list) if compare_jsons else resp.shape[-2]):
            label = f"${bin1[i1]:>5.4g} \leq${var1}$< {bin1[i1+1]:<5.4g}$" if var1 and not (compare_jsons) else json_names[i1] if compare_jsons else "fit" 
            leg_title = '' if not var2 else f"${bin2[i2]:>5.4g} \leq${var2}$< {bin2[i2+1]:<5.4g}$" 
            if compare_jsons and len(dims) != 1:
                leg_title += f"\n${bin1[min(i1,resp.shape[-2]-1) if len(dims)>2 else i2]:>5.4g} \leq${var1}$< {bin1[min(i1,resp.shape[-2]-1)+1 if len(dims)>2 else i2+1]:<5.4g}$"
                leg_titles.append(leg_title)

            def get_resp_reso(resp, reso, corr='resp'):
                if corr == 'resp':
                    corr2 = 'reso' if compare_jsons and param_to_plot == 'reso' else 'resp'
                else:
                    corr2 = 'resp' if compare_jsons and param_to_plot == 'resp' else 'reso'
                respo = resp if corr2 == 'resp' else reso 
                # print(corr, respo is reso)
                if compare_jsons and len(dims) > 2:
                    # print('hello')
                    if corr == 'resp':
                        return respo[:, i1, 0, i2]
                    else:
                        return respo[:, i1, 1, i2]
                else:
                    return respo[:, i1, i2]
            # -- response plot
            axis = ax[i2, 0]
            axis.errorbar(xval, get_resp_reso(resp, reso, corr='resp'), xerr=xerr, yerr=get_resp_reso(eresp, ereso, corr='resp'), ls='', marker='.', label=label, capsize=2)
            axis.bar(xval, 2*get_resp_reso(eresp_mc, ereso_mc, corr='resp'), bottom=get_resp_reso(resp, reso, corr='resp') - get_resp_reso(eresp_mc, ereso_mc, corr='resp'), 
                    width=1.5*xerr, alpha=0.7, color=axis.lines[-1].get_color())
            cms.polish_axis(axis, x_range=x_range, x_title=var_ref, y_title='reso.' if compare_jsons and param_to_plot == 'reso' else 'resp.', y_range=reso_range if compare_jsons and param_to_plot == 'reso' else resp_range, 
                            leg_title=leg_titles[0] if compare_jsons and len(dims)>2 else leg_title, **kwargs) 
            if param_to_plot is None or param_to_plot=='resp':
                axis.axhline(1, ls='--', color='gray')

            if hide_legend:
                axis.legend().set_visible(False) 

            # -- resolution plot
            axis = ax[i2, 1]
            axis.errorbar(xval, get_resp_reso(resp, reso, corr='reso'), xerr=xerr, yerr=get_resp_reso(eresp, ereso, corr='reso'), ls='', marker='.', label=label, capsize=2)
            axis.bar(xval, 2*get_resp_reso(eresp_mc, ereso_mc, corr='reso'), bottom=get_resp_reso(resp, reso, corr='reso') - get_resp_reso(eresp_mc, ereso_mc, corr='reso'), 
                    width=1.5*xerr, alpha=0.7, color=axis.lines[-1].get_color())
            cms.polish_axis(axis, x_range=x_range, x_title=var_ref, y_title='resp.' if compare_jsons and param_to_plot == 'resp' else 'reso.', y_range=resp_range if compare_jsons and param_to_plot == 'resp' else reso_range, 
                            leg_title=leg_titles[-1] if compare_jsons and len(dims)>2 else leg_title, **kwargs)
            if compare_jsons and param_to_plot=='resp' or jsons_mode == 'ratio':
                axis.axhline(1, ls='--', color='gray')
            if hide_legend:
                axis.legend().set_visible(False) 
            

    return figs, ax


def plot_results_from_json2G(json_file: Union[str, Path, Dict], dims: List=None, x_range=(), x_unit='', 
              cat_latex:Dict=None, mu_range=(0.78,1.02), reso2_range=(-0.001,0.10), frac_range=(0.78,1.02), **kwargs) -> Tuple[List[Figure], Axes]:
    """Create a list of Axes to plot the results in the json file.
    the dimensions to plot can be specified, additional dimension are averaged over.
    Up to 3 dimensions can be plotted.

    Args:
        json_file (Union[str, Path, Dict]): json file containing the results of the IJazZ SAS fit or Dict from the json file
        dims (List, optional): name dimensions to plot (as in the categories). Defaults to None.
        x_range (tuple, optional): range of the main variable (dimension 0). Defaults to ().
        x_unit (str, optional): usint of the main varaible. Defaults to ''.
        cat_latex (Dict, optional): dictionnary mapping var name (from categories) into a latex name. Defaults to None.
        resp_range (tuple, optional): y-range of the resp axis. Defaults to ().
        reso_range (tuple, optional): y-range if the reso axis. Defaults to ().
        leg_ncol (int, optional): number of columns in the legend. Defaults to 1.

    Returns:
        Tuple[Figure, Axes]: Figure and Axes of the plot.
    """
    # -- get the parameters
    params = json_file if isinstance(json_file, Dict) else parameters_from_json(json_file)

    if not cat_latex:
        # -- define cat_latex if not given
        cat_latex = {key: key for key in params['dims']}

    if dims is None:
        # -- keep all dims by default
        dims = [key for key in params['dims']]

    if len(dims) > 3:
        # -- keep only the 3 first dimensions
        dims = dims[:3]

    dims_to_keep = [np.where(params['dims'] == d)[0][0] for d in dims]
    dims_to_average = [id for id, d in enumerate(params['dims']) if not d in dims]
    perm = dims_to_keep + dims_to_average
    dims_to_average = np.arange(len(dims_to_keep), len(perm))

    def reshape_param(par_name):
        par = tf.transpose(params[par_name], perm=perm)
        
        epar = tf.transpose(params[f'e{par_name}'], perm=perm)
        epar_mc = tf.transpose(params[f'e{par_name}_mc'], perm=perm)

        # par = tf.reduce_sum((par/ epar**2), axis=dims_to_average) / tf.reduce_sum((1 / epar**2), axis=dims_to_average)
        # epar = tf.sqrt(1./ tf.reduce_sum((1 / epar**2), axis=dims_to_average))
        # epar_mc = tf.sqrt(1./ tf.reduce_sum((1 / epar_mc**2), axis=dims_to_average))

        shape = list(tf.shape(par).numpy()) + [1] * (3-tf.rank(par).numpy())
        return tf.reshape(par, shape), tf.reshape(epar, shape), tf.reshape(epar_mc, shape)

    mu, emu, emu_mc = reshape_param('mu')
    reso2, ereso2, ereso2_mc = reshape_param('reso2')
    frac, efrac, efrac_mc = reshape_param('frac')

    if emu.mean() == 1.0:
        emu -= 1.0
    if emu_mc.mean() == 1.0:
        emu_mc -= 1.0
    if ereso2.mean() == 1.0:
        ereso2 -= 1.0
    if ereso2_mc.mean() == 1.0:
        ereso2_mc -= 1.0
    if efrac.mean() == 1.0:
        efrac -= 1.0
    if efrac_mc.mean() == 1.0:
        efrac_mc -= 1.0


    # -- dim 0
    xbin = params['bins'][dims_to_keep[0]]
    xbin = tf.where(xbin == +np.inf, x_range[1] if len(x_range) > 1 else xbin[-2]*1.5, xbin)
    xbin = tf.where(xbin == -np.inf, x_range[0] if len(x_range) > 0 else xbin[1]/1.5, xbin)
    xval = 0.5*(xbin[1:] + xbin[:-1])
    xerr = 0.5*(xbin[1:] - xbin[:-1])
    var_ref = cat_latex[dims[0]] + x_unit

    # -- higher dimensions
    var1, var2 = None, None
    bin1, bin2 = [], []
    n_dim2 = 1
    if len(dims) > 1:
        var1 = cat_latex[dims[1]] 
        bin1 = params['bins'][dims_to_keep[1]]

    if len(dims) > 2:
        var2 = cat_latex[dims[2]] 
        bin2 = params['bins'][dims_to_keep[2]]
        n_dim2 = len(bin2) - 1

    # -- only maximum of 2 line per figure
    figs = []
    axes = []
    for ifig in range(n_dim2 // 2):
        fig, ax = plt.subplots(2, 3, figsize=(18, 4.5*2), squeeze=False)
        figs.append(fig)
        axes.append(ax)
    for ifig in range(n_dim2 % 2):
        fig, ax = plt.subplots(1, 3, figsize=(18, 4.5), squeeze=False)
        figs.append(fig)
        axes.append(ax)
    ax = np.concatenate(axes, axis=0)

    for i1 in range(mu.shape[-2]):
        for i2 in range(mu.shape[-1]):
            label = "fit" if not var1 else f"${bin1[i1]:>5.4g} \leq${var1}$< {bin1[i1+1]:<5.4g}$"
            leg_title = '' if not var2 else f"${bin2[i2]:>5.4g} \leq${var2}$< {bin2[i2+1]:<5.4g}$"

            # -- mu plot
            axis = ax[i2, 0]
            axis.errorbar(xval, mu[:, i1 ,i2], xerr=xerr, yerr=emu[:, i1, i2], ls='', marker='.', label=label, capsize=2)
            axis.bar(xval, 2*emu_mc[:, i1, i2], bottom=mu[:, i1, i2] - emu_mc[:, i1, i2], 
                    width=1.5*xerr, alpha=0.7, color=axis.lines[-1].get_color())
            cms.polish_axis(axis, x_range=x_range, x_title=var_ref, y_title='mu', y_range=mu_range, 
                            leg_title=leg_title, **kwargs) 
            axis.axhline(1, ls='--', color='gray')

            # -- resolution plot
            axis = ax[i2, 1]
            axis.errorbar(xval, reso2[:, i1 ,i2], xerr=xerr, yerr=ereso2[:, i1, i2], ls='', marker='.', label=label, capsize=2)
            axis.bar(xval, 2*ereso2_mc[:, i1, i2], bottom=reso2[:, i1, i2] - ereso2_mc[:, i1, i2], 
                    width=1.5*xerr, alpha=0.7, color=axis.lines[-1].get_color())
            cms.polish_axis(axis, x_range=x_range, x_title=var_ref, y_title='reso2.', y_range=reso2_range, 
                            leg_title=leg_title, **kwargs) 
            
            # -- frac plot
            axis = ax[i2, 2]
            axis.errorbar(xval, frac[:, i1 ,i2], xerr=xerr, yerr=efrac[:, i1, i2], ls='', marker='.', label=label, capsize=2)
            axis.bar(xval, 2*efrac_mc[:, i1, i2], bottom=frac[:, i1, i2] - efrac_mc[:, i1, i2], 
                    width=1.5*xerr, alpha=0.7, color=axis.lines[-1].get_color())
            cms.polish_axis(axis, x_range=x_range, x_title=var_ref, y_title='frac.', y_range=frac_range, 
                            leg_title=leg_title, **kwargs) 

    return figs, ax


def plot_syst_from_jsons(nominal:Union[Dict, str, Path], syst_jsons:List[Union[Dict, str, Path]], fit_2g:Union[Dict, str, Path]=None,
                         nominal_syst:Union[Dict, str, Path]=None, scale_flat_syst:float=0.0, smear_flat_syst:float=0.0, **kwargs) -> Tuple[str, List[str]]:
    """Plot the contribution of each systematic uncertainties  from the json files

    Args:
        nominal (Union[Dict, str, Path]): nominal json file
        syst_jsons (List[Union[Dict, str, Path]]): list of json files with systematic variations
        fit_2g (Union[Dict, str, Path], optional): json file with the parameters of the double gaussian fit. Defaults to None.
        scale_flat_syst (float, optional): flat scale systematic uncertainty. Defaults to 0.0.
        smear_flat_syst (float, optional): flat smear systematic uncertainty. Defaults to 0.0.
    
    Returns:
    """ 
    if not isinstance(nominal, Dict):
        nominal = parameters_from_json(nominal) 
    else:
        raise ValueError('Missing nominal json file')
    
    jsons_dict = {}
    import copy
    
    params = copy.deepcopy(nominal)
    params['resp'] = nominal['eresp']
    params['reso'] = nominal['ereso']
    params['eresp'] = np.zeros_like(nominal['eresp'])
    params['ereso'] = np.zeros_like(nominal['ereso'])
    params['eresp_mc'] = np.zeros_like(nominal['eresp'])
    params['ereso_mc'] = np.zeros_like(nominal['ereso'])

    eresp = nominal['eresp']**2
    ereso = nominal['ereso']**2

    jsons_dict['e_fitter'] = params

    params = copy.deepcopy(nominal)
    params['resp'] = nominal['eresp_mc']
    params['reso'] = nominal['ereso_mc']
    params['eresp'] = np.zeros_like(nominal['eresp'])
    params['ereso'] = np.zeros_like(nominal['ereso'])
    params['eresp_mc'] = np.zeros_like(nominal['eresp'])
    params['ereso_mc'] = np.zeros_like(nominal['ereso'])

    jsons_dict['e_fitter_mc'] = params

    flat_syst = copy.deepcopy(nominal)
    flat_syst['resp'] = np.ones_like(nominal['resp']) * scale_flat_syst
    flat_syst['reso'] = np.ones_like(nominal['reso']) * smear_flat_syst
    eresp += scale_flat_syst**2
    ereso += smear_flat_syst**2
    flat_syst['eresp'] = np.zeros_like(nominal['eresp'])
    flat_syst['ereso'] = np.zeros_like(nominal['ereso'])
    flat_syst['eresp_mc'] = np.zeros_like(nominal['eresp'])
    flat_syst['ereso_mc'] = np.zeros_like(nominal['ereso'])

    jsons_dict['flat_syst'] = flat_syst


    # return plot_results_from_json(jsons_dict, **kwargs)
    

    for syst_name, syst in syst_jsons.items():
        if not isinstance(syst, Dict):
            syst = parameters_from_json(syst)
        eresp_syst = np.abs(syst['resp']-nominal['resp'])
        ereso_syst = np.abs(syst['reso']-nominal['reso'])

        eresp += eresp_syst**2
        ereso += ereso_syst**2

        params = copy.deepcopy(nominal)
        params['resp'] = eresp_syst
        params['reso'] = ereso_syst
        params['eresp'] = np.zeros_like(nominal['eresp'])
        params['ereso'] = np.zeros_like(nominal['ereso'])
        params['eresp_mc'] = np.zeros_like(nominal['eresp'])
        params['ereso_mc'] = np.zeros_like(nominal['ereso'])

        jsons_dict[syst_name] = params


    if fit_2g:
        if not isinstance(fit_2g, Dict):
            fit_2g = parameters_from_json(fit_2g)

        r = fit_2g['resp']
        s1 = fit_2g['reso']
        s2 = fit_2g['reso2']
        mu = fit_2g['mu']
        f = fit_2g['frac']

        r2g = (f + (1-f)*mu)*r
        s2g = np.sqrt(f*s1**2 + (1-f)*(mu**2)*(s2**2) + f*(1-f)*((mu-1)**2)) * r

        eresp_2g = np.abs(nominal['resp'] - r2g)
        ereso_2g = np.abs(nominal['reso'] - s2g)

        eresp += (eresp_2g)**2
        ereso += (ereso_2g)**2

        params = copy.deepcopy(nominal)
        params['resp'] = eresp_2g
        params['reso'] = ereso_2g
        params['eresp'] = np.zeros_like(nominal['eresp'])
        params['ereso'] = np.zeros_like(nominal['ereso'])
        params['eresp_mc'] = np.zeros_like(nominal['eresp'])
        params['ereso_mc'] = np.zeros_like(nominal['ereso'])

        jsons_dict['2G'] = params

    

    params = copy.deepcopy(nominal)
    params['resp'] = np.sqrt(eresp)
    params['reso'] = np.sqrt(ereso)
    params['eresp'] = np.zeros_like(nominal['eresp'])
    params['ereso'] = np.zeros_like(nominal['ereso'])
    params['eresp_mc'] = np.zeros_like(nominal['eresp'])
    params['ereso_mc'] = np.zeros_like(nominal['ereso'])

    jsons_dict['total'] = params

    if nominal_syst:
        if not isinstance(nominal_syst, Dict):
            nominal_syst = parameters_from_json(nominal_syst)
        
        params = copy.deepcopy(nominal)
        params['resp'] = nominal_syst['eresp']
        params['reso'] = nominal_syst['ereso']
        params['eresp'] = np.zeros_like(nominal['eresp'])
        params['ereso'] = np.zeros_like(nominal['ereso'])
        params['eresp_mc'] = np.zeros_like(nominal['eresp'])
        params['ereso_mc'] = np.zeros_like(nominal['ereso'])

        jsons_dict['check'] = params

    return plot_results_from_json(jsons_dict, **kwargs)

def plot_sas_fit_results(sas: IJazZSAS, cat_latex={}, x_range=None, 
                         resp_range=(0.95, 1.05), reso_range=(0, 0.05), add_injected=False,
                         use_pt_cat=False,
                         resp_range_ratio=(0.999, 1.001), reso_range_ratio=(0.80, 1.20),
                         pt_scale_std = 1.0) -> Tuple[Figure, Axes]:
    """Plot the result of the scale and smearing fit 

    Args:
        sas (IJazZSAS): object containing the fit result of the scale and smearing (as well as the data , mc samples)
        cat_latex (dict, optional): dict containing for each variable used for categorisation a latex plotting symbol (e.g. {'pt': 'p_T'}). Defaults to {}.
        x_range (tuple, optional): x axis range (can be auto). Defaults to None.
        resp_range (tuple, optional): y axis range for response. Defaults to (0.95, 1.05).
        reso_range (tuple, optional): y axis range for resolution. Defaults to (0, 0.05).
        add_injected (bool, optional): When a resolution was injected for test, plot the value (variable sas per lepton must exist filled with the injected s&s). Defaults to False.
        use_pt_cat (bool, optional): Use the pt categorisation axis (when fitting with relative pt, allows to plot back w/r to pt). Defaults to False.
        resp_range_ratio (tuple, optional): y axis range for response ratio. Defaults to (0.999, 1.001).
        reso_range_ratio (tuple, optional): y axis range for resolution ratio. Defaults to (0.80, 1.20).
        pt_scale_std (float, optional): ?. Defaults to 1.0.

    Returns:
        tuple[plt.Figure, plt.Axes]: matplotlib figure, axes with the result
    """
    # -- define cat_latex if not given
    if not cat_latex:
        cat_latex = {key: key for key in sas.categories.keys()}

    # -- up to 3 dimensions
    n_dim1 = sas.lepton_reg.shape[1] if len(sas.lepton_reg.shape) > 1 else 1
    n_dim2 = sas.lepton_reg.shape[2] if len(sas.lepton_reg.shape) > 2 else 1

    if add_injected:
        fig, ax = plt.subplots(2, 2, sharex=True, height_ratios=(4, 1), figsize=(12, 7))
    else:
        fig, ax = plt.subplots(n_dim2, 2, figsize=(12, 4.5*n_dim2))

    def tune_dimension(arr, ashape):
        if len(ashape) == 1:
            return  np.array([[arr.reshape(ashape)]]).T
        elif len(ashape) == 2:
            return  np.array([arr.reshape(ashape).T]).T
        return arr.reshape(ashape)

    lepton_cat = tune_dimension(sas.lepton_reg, sas.lepton_reg.shape)
    resp = tune_dimension(sas.resp, sas.lepton_reg.shape)
    reso = tune_dimension(sas.reso, sas.lepton_reg.shape)
    eresp = None
    ereso = None
    if sas.eresp is not None:
        eresp = tune_dimension(sas.eresp, sas.lepton_reg.shape)
        ereso = tune_dimension(sas.ereso, sas.lepton_reg.shape)
    
    eresp_mc = None
    ereso_mc = None
    if sas.eresp_mc is not None:
        eresp_mc = tune_dimension(sas.eresp_mc, sas.lepton_reg.shape)
        ereso_mc = tune_dimension(sas.ereso_mc, sas.lepton_reg.shape)

    leg_ncol = 1
    injected = None
    name_cat = sas.cfg['fitter'].get('name_cat', 'cat')
    name_pt = sas.cfg['sas'].get('name_pt_var', 'pt')
    if add_injected and 'sas1' in sas.dt.columns:
        injected = sas.dt.groupby(f'{name_cat}2')['sas2'].agg({'mean', 'std'})\
            .reindex(range(len(sas.resp)))  # -- add missing cat if necessary
        injected['std'] = injected['std'] / injected['mean']
        leg_ncol = 2


    # -- dimension 0
    categories = sas.categories.copy()
    var_ref = list(categories.keys())[0]
    bin_ref = np.array(categories.pop(var_ref), dtype=np.float32)
    if use_pt_cat and var_ref == f'r_pt':
        df_cat = pd.concat( [sas.dt[[f'{name_cat}_r_pt{ilep}', f'{name_pt}{ilep}' , f'{name_cat}{ilep}']]\
            .rename(columns={f'{name_cat}_r_pt{ilep}': f'{name_cat}_r_pt', 
                                f'{name_pt}{ilep}': name_pt, 
                                f'{name_cat}{ilep}': name_cat}) for ilep in [1, 2]])
        df_cat = df_cat.query(f'{name_cat}_r_pt >= 0').groupby(f'{name_cat}_r_pt')[name_pt].agg({'mean', 'std'})\
            .reindex(range(resp.shape[0]))  # -- add missing cat if necessary
        df_cat['std'] *= pt_scale_std  # -- for pt re-casting do not use the full std
        var_ref = f"$p_T$  (GeV)"
    else:
        df_cat = pd.concat([sas.dt[[f'{name_cat}_{var_ref}{ilep}', f'{var_ref}{ilep}']]\
            .rename(columns={f'{name_cat}_{var_ref}{ilep}': f'{name_cat}_{var_ref}', 
                            f'{var_ref}{ilep}': f'{var_ref}'}) for ilep in [1, 2]])
        df_cat = df_cat.query(f'{name_cat}_{var_ref} >= 0').groupby(f'{name_cat}_{var_ref}')[var_ref].agg({'mean', 'std'})\
            .reindex(range(resp.shape[0]))  # -- add missing cat if necessary
        var_ref = f"${cat_latex[var_ref]}$"
    xval = df_cat['mean'].values
    xerr = df_cat['std'].values
    if not x_range:
        x_range = (bin_ref[0], min(bin_ref[-1], xval[-1] + 5*xerr[-1]))  

    # -- dimension 1
    var1 = None
    if n_dim1 > 1:
        var1 = list(categories.keys())[0]
        bin1 = np.array(categories.pop(var1), dtype=np.float32)
        var1 = cat_latex[var1]

    # -- dimension 2
    var2 = None
    if n_dim2 > 1:
        var2 = list(categories.keys())[0]
        bin2 = np.array(categories.pop(var2), dtype=np.float32)
        var2 = cat_latex[var2]

    for i1 in range(n_dim1):
        for i2 in range(n_dim2):
            label = "fit" if not var1 else f"$ {bin1[i1]:>5.4g} \leq {var1} < {bin1[i1+1]:<5.4g}$"
            leg_title = '' if not var2 else f"$ {bin2[i2]:>5.4g} \leq {var2} < {bin2[i2+1]:<5.4g}$"

            # -- plot the response   
            if injected is not None:
                axis = ax[0, 0]
            else:
                axis = ax[0] if n_dim2 == 1 else ax[i2, 0] 
            axis.errorbar(xval, resp[:, i1 ,i2], xerr=xerr, yerr=eresp[:, i1, i2], ls='', marker='.', label=label, capsize=2)
            if eresp_mc is not None:
                axis.bar(xval, 2*eresp_mc[:, i1, i2], bottom=resp[:, i1, i2] - eresp_mc[:, i1, i2], 
                         width=1.5*xerr, alpha=0.7, color=axis.lines[-1].get_color())
            if injected is not None: 
                axis.plot(xval, injected.loc[lepton_cat[:, i1, i2], 'mean'], color=axis.lines[-1].get_color(), ls='--', label='injected')
                ax[1, 0].errorbar(xval, resp[:, i1 ,i2] / injected.loc[lepton_cat[:, i1, i2], 'mean'], xerr=xerr, 
                                  yerr=eresp[:, i1, i2]/ injected.loc[lepton_cat[:, i1, i2], 'mean'], ls='', marker='.', capsize=2)
                cms.polish_axis(y_title='resp.', y_range=resp_range, ax=axis, leg_title=leg_title, leg_ncol=leg_ncol)
            else:
                cms.polish_axis(x_range=x_range, x_title=var_ref, y_title='resp.', y_range=resp_range, ax=axis, leg_title=leg_title, leg_ncol=leg_ncol) 
            axis.axhline(1, ls='--', color='gray')
    
            # -- plot the resolution
            if injected is not None:
                axis = ax[0, 1]
            else:
                axis = ax[1] if n_dim2 == 1 else ax[i2, 1] 
            axis.errorbar(xval, reso[:, i1 ,i2], xerr=xerr, yerr=ereso[:, i1, i2], ls='', marker='.', label=label, capsize=2)
            if ereso_mc is not None:
                axis.bar(xval, 2*ereso_mc[:, i1, i2], bottom=reso[:, i1, i2] - ereso_mc[:, i1, i2], 
                         width=1.5*xerr, alpha=0.7, color=axis.lines[-1].get_color())
            if injected is not None: 
                axis.plot(xval, injected.loc[lepton_cat[:, i1, i2], 'std'], color=axis.lines[-1].get_color(), ls='--', label='injected')
                ax[1, 1].errorbar(xval, reso[:, i1 ,i2] / injected.loc[lepton_cat[:, i1, i2], 'std'], xerr=xerr, 
                                  yerr=ereso[:, i1, i2]/ injected.loc[lepton_cat[:, i1, i2], 'std'], ls='', marker='.', capsize=2)
            if injected is not None:
                cms.polish_axis(y_title='reso.', y_range=reso_range, ax=axis, leg_title=leg_title, leg_ncol=leg_ncol)
                cms.polish_axis(x_title=var_ref, x_range=x_range, y_title='fit / inj.', y_range=resp_range_ratio, ax=ax[1, 0])
                cms.polish_axis(x_title=var_ref, x_range=x_range, y_title='fit / inj.', y_range=reso_range_ratio, ax=ax[1, 1])
                ax[1, 0].axhline(1, ls='-', color='black')
                ax[1, 1].axhline(1, ls='-', color='black')
            else:
                cms.polish_axis(x_range=x_range, x_title=var_ref, y_title='reso.', 
                                y_range=reso_range, ax=axis, leg_title=leg_title, leg_ncol=leg_ncol)
    return fig, ax
  

