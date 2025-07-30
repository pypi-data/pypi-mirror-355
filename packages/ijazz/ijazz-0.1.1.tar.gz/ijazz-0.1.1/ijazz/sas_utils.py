import numpy as np
import tensorflow as tf
from pathlib import Path
import json, yaml
import pandas as pd
from typing import Dict, Union, List, Tuple
import matplotlib.pyplot as plt
import cms_fstyle as cms
from cms_fstyle.fitter import FFitter
from copy import deepcopy

def ijazz_shape(categories: dict) -> List:
    """Returns the shape to be used for reshaping the tensor of parameters of the ijazz fit

    Args:
        categories (dict): categories used in the ijazz sas fit

    Returns:
        list: shape
    """
    return [len(bins)-1 for bins in categories.values()]

    
def parameters_from_json(json_file: Union[str, Path, Dict]) -> Dict:
    """Extract and re-shape the IJazZ sas results saved in a json file

    Args:
        json_file (Union[str, Path, Dict]): name of the json file where the fit results are stored

    Returns:
        dict: dictionnary with the categories used in the fit and the results of the fit
    """

    if isinstance(json_file, Dict):
        ijazz_json = json_file.copy()
    else:
        with open(json_file) as f_json:
            ijazz_json = json.load(f_json)

    categories = ijazz_json['categories']
    shape = ijazz_shape(ijazz_json['categories'])

    
    par_names = ['resp', 'reso', 'eresp', 'ereso', 'eresp_mc', 'ereso_mc'] \
                +(['reso2', 'ereso2','ereso2_mc', 'mu', 'emu', 'emu_mc', 'frac', 'efrac', 'efrac_mc'] if 'reso2' in ijazz_json.keys() else []) \
                +(['mean2G', 'std2G'] if 'mean2G' in ijazz_json.keys() else [])
    parameters = {par_name: np.array(ijazz_json.get(par_name, np.ones(shape)*np.nan)).reshape(shape) for par_name in par_names}
    parameters['eresp'] = np.where(np.isnan(parameters['eresp']), np.inf, parameters['eresp'])
    parameters['ereso'] = np.where(np.isnan(parameters['ereso']), np.inf, parameters['ereso'])
    parameters = {k: tf.convert_to_tensor(v, dtype=tf.float32) for k, v in parameters.items()}

    parameters['bins'] = [np.array(bin) for bin in categories.values()]
    parameters['bins'] = [np.where(bin <= -9999, -np.inf, bin) for bin in parameters['bins']]
    parameters['bins'] = [np.where(bin >= +9999, +np.inf, bin) for bin in parameters['bins']]
    parameters['bins'] = [tf.convert_to_tensor(bin, dtype=tf.float32) for bin in parameters['bins'] ]

    parameters['dims'] = np.array(list(categories.keys()), dtype=str)
    parameters['pt'] = np.array(ijazz_json.get('pt_mean', None))

    return parameters


def parameters_to_json(params:Dict, outfile: Union[str, Path]) -> None:
    """Dump the parameters dictionnary to a json file

    Args:
        params (Dict): input dictionnary
        outfile (Union[str, Path]): output file
    """
    print(f'Dump results to json file: {outfile}')
    categories = params['categories']
    categories_serialized = {}
    for k, v in categories.items():
        v = np.where(np.array(v) == +np.inf, +9999, np.array(v))
        v = np.where(np.array(v) == -np.inf, -9999, np.array(v))
        categories_serialized[k] = v.tolist()
    categories_serialized

    with open(outfile, "w")  as fjson:
        eresp = np.where(np.isnan(np.array(params['eresp'])), 0, np.array(params['eresp']))
        ereso = np.where(np.isnan(np.array(params['ereso'])), 0, np.array(params['ereso']))
        eresp_mc = np.where(np.isnan(np.array(params['eresp_mc'])), 0, np.array(params['eresp_mc']))
        ereso_mc = np.where(np.isnan(np.array(params['ereso_mc'])), 0, np.array(params['ereso_mc']))

        pt_mean = None if params.get('pt_mean', None) is None else params['pt_mean'].tolist()

        if "reso2" in params.keys():
            emu = np.where(np.isnan(np.array(params['emu'])), 1, np.array(params['emu']))
            ereso2 = np.where(np.isnan(np.array(params['ereso2'])), 1, np.array(params['ereso2']))
            efrac = np.where(np.isnan(np.array(params['efrac'])), 1, np.array(params['efrac']))
            emu_mc = np.where(np.isnan(np.array(params['emu_mc'])), 1, np.array(params['emu_mc']))
            ereso2_mc = np.where(np.isnan(np.array(params['ereso2_mc'])), 1, np.array(params['ereso2_mc']))
            efrac_mc = np.where(np.isnan(np.array(params['efrac_mc'])), 1, np.array(params['efrac_mc']))
            json.dump({"categories": categories_serialized,
                "resp": np.array(params['resp']).tolist(), "reso": np.array(params['reso']).tolist(),
                "reso2": np.array(params['reso2']).tolist(), "mu": np.array(params['mu']).tolist(), "frac" : np.array(params['frac']).tolist(),
                "eresp": eresp.tolist(), "ereso": ereso.tolist(),
                "ereso2": ereso2.tolist(), "emu": emu.tolist(), "efrac" : efrac.tolist(),
                "eresp_mc": eresp_mc.tolist(), "ereso_mc": ereso_mc.tolist(),
                "ereso2_mc": ereso2_mc.tolist(), "emu_mc": emu_mc.tolist(), "efrac_mc" : efrac_mc.tolist(),
                "pt_mean": pt_mean} | ({"mean2G": np.array(params['mean2G']).tolist(), "std2G": np.array(params['std2G']).tolist()} if "mean2G" in params.keys() else {}),
                fjson, indent=4)
        else:
            json.dump({"categories": categories_serialized,
                "resp": np.array(params['resp']).tolist(), "reso": np.array(params['reso']).tolist(),
                "eresp": eresp.tolist(), "ereso": ereso.tolist(),
                "eresp_mc": eresp_mc.tolist(), "ereso_mc": ereso_mc.tolist(),
                "pt_mean": pt_mean},
                fjson, indent=4)


def json_safe_load(json_name, mc_errors=False):
    with open(json_name, 'r') as fjson:
        sas = json.load(fjson)
    for k in ['resp', 'reso', 'eresp', 'ereso', 'pt_mean'] + \
            (['eresp_mc', 'ereso_mc'] if mc_errors else []) + \
            (['reso2', 'ereso2', 'mu', 'emu', 'frac', 'efrac'] if 'reso2' in sas.keys() else []) + \
            (['ereso2_mc', 'emu_mc', 'efrac_mc'] if ('reso2' in sas.keys()) and mc_errors else []):
        sas[k] = np.array(sas[k])
    return sas

def to_correction_lib(sas: Union[Dict, str, Path], dir_results:Union[Path, str]='./tmp/', dset_name='DSET', 
                      cset_name='CSET', cset_description:str=None, cset_version=1, 
                      cat_latex=None) -> Tuple[str, List[str]]:
    """Create a correction lib files based 

    Args:
        sas (Dict, ): dictionnary with scales and smearings
        dir_results (Path, optional): directory. Defaults to Path('./tmp/').
        dset_name (str, optional): dataset nickname. Defaults to 'DSET'.
        cset_name (str, optional): correction saet name. Defaults to 'CSET'.
        cset_description (str, optional): description of the correction set. Defaults to None.
        cset_version (int, optional): correction set version. Defaults to 1.
        cat_latex (Dict, optional): dictionnary with a description of variables in categories. Defaults to None.
    """
    import correctionlib.schemav2 as cs
    import rich
    if not isinstance(sas, Dict):
        sas = json_safe_load(sas)

    dir_results = Path(dir_results)
    print(f'---------------------------------------')
    print(f'---- Create correction lib')
    print(f'---------------------------------------')
    if cat_latex is None:
        cat_latex = {key: key for key in sas['categories']}

    def create_correction(cset_name, out_name, measures):
        def create_bin_corr(s_name):
            # flow = cs.Binning(['error'] + ['clamp'] * len(sas['categories']))
            # flow = {'syst': 'error'} | {k: 'clamp' for k in sas['categories'].keys()}
            
            flow = 'clamp'
            return cs.MultiBinning( nodetype='multibinning',
                                inputs=list(sas['categories'].keys()),
                                edges=list(sas['categories'].values()),
                                content=measures[s_name],
                                flow=flow)

        return cs.Correction(name = cset_name, 
                                version = cset_version,
                                description=cset_description,
                                inputs = [cs.Variable(name="syst", type="string", description="Systematic type")] +
                                         [cs.Variable(name=dim, type='real', description=cat_latex[dim]) for dim in sas['categories']],
                                output = cs.Variable(name=out_name, type="real", description=f"EM {out_name} value"),
                                data = cs.Category(nodetype='category',
                                                   input='syst',
                                                   content=[cs.CategoryItem(key=k,value=create_bin_corr(k)) for k in measures.keys()]
                                                  )
                                )
        
    esr_rel = sas['eresp']/sas['resp']
    scales = {'scale': 1./sas['resp'], 'escale': esr_rel/sas['resp'], 'scale_up': 1./sas['resp']*(1 + esr_rel), 'scale_down': 1./sas['resp']*(1-esr_rel)}
    smears = {'smear': sas['reso'], 'esmear': sas['ereso'], 'smear_up': sas['reso']+sas['ereso'], 'smear_down': sas['reso']-sas['ereso'],
              'escale': esr_rel, 'scale_up': 1 + esr_rel, 'scale_down': 1 - esr_rel }
    if 'reso2' in sas.keys():
        smears |= {'reso2': sas['reso2'], 'ereso2': sas['ereso2'], 'reso2_up': sas['reso2']+sas['ereso2'], 'reso2_down': sas['reso2']-sas['ereso2'],
                  'mu': sas['mu'],  'emu': sas['emu'], "mu_up": sas['mu']+sas['emu'], "mu_down": sas['mu']-sas['emu'],
                  'frac': sas['frac'],'efrac': sas['efrac'], 'frac_up': sas['frac']+sas['efrac'], 'frac_down': sas['frac']-sas['efrac']}
                  
    c_scale = create_correction(f'EGMScale_{cset_name}_{dset_name}'       , 'scale', scales) # only scales to apply to data
    c_smear = create_correction(f'EGMSmearAndSyst_{cset_name}_{dset_name}', 'smear', smears) # MC parameters
    
    rich.print(c_scale)
    rich.print(c_smear)
    cset = cs.CorrectionSet(schema_version=2,
                            description=cset_description,
                            corrections=[c_scale, c_smear]
                            )
    dir_results.mkdir(exist_ok=True)
    file_out = dir_results / f"EGMScalesSmearing_{dset_name}.v{cset_version}.json"
    print(f"Writing out correction lib file: {file_out}.gz")
    import gzip
    with gzip.open(f"{file_out}.gz", "wt") as fout:
        fout.write(cset.model_dump_json(indent=1,exclude_unset=True))
    return f"{file_out}.gz", list(sas['categories'].keys()),

def compute_syst_from_jsons(nominal:Union[Dict, str, Path], syst_jsons:List[Union[Dict, str, Path]], fit_2g:Union[Dict, str, Path]=None,
                            scale_flat_syst:float=0.0, smear_flat_syst:float=0.0) -> Tuple[str, List[str]]:
    """Compute the systematic uncertainties from the json files

    Args:
        nominal (Union[Dict, str, Path]): nominal json file
        syst_jsons (List[Union[Dict, str, Path]]): list of json files with systematic variations
        fit_2g (Union[Dict, str, Path], optional): json file with the parameters of the double gaussian fit. Defaults to None.
        scale_flat_syst (float, optional): flat scale systematic uncertainty. Defaults to 0.0.
        smear_flat_syst (float, optional): flat smear systematic uncertainty. Defaults to 0.0.
    
    Returns:
    """ 
    if not isinstance(nominal, Dict):
        nominal = json_safe_load(nominal, mc_errors=True) 
    else:
        raise ValueError('Missing nominal json file')
    
    eresp = nominal['eresp']**2
    ereso = nominal['ereso']**2

    eresp += scale_flat_syst**2
    ereso += smear_flat_syst**2

    for syst in syst_jsons:
        if not isinstance(syst, Dict):
            syst = json_safe_load(syst)
        eresp += (syst['resp']-nominal['resp'])**2
        ereso += (syst['reso']-nominal['reso'])**2

    

    if fit_2g:
        if not isinstance(fit_2g, Dict):
            fit_2g = json_safe_load(fit_2g)
        import copy
        nominal_eresp = copy.deepcopy(eresp)
        nominal_ereso = copy.deepcopy(ereso)
        r = fit_2g['resp']
        s1 = fit_2g['reso']
        s2 = fit_2g['reso2']
        mu = fit_2g['mu']
        f = fit_2g['frac']

        fit_2g['mean2G'] = (f + (1-f)*mu)*r
        fit_2g['std2G'] = np.sqrt(f*s1**2 + (1-f)*(mu**2)*(s2**2) + f*(1-f)*((mu-1)**2)) * r

        eresp += (nominal['resp'] - fit_2g['mean2G'])**2
        ereso += (nominal['reso'] - fit_2g['std2G'])**2

        fit_2g['eresp'] = np.sqrt(nominal_eresp)
        fit_2g['ereso'] = np.sqrt(nominal_ereso)

        fit_2g['eresp_mc'] = nominal['eresp_mc']
        fit_2g['ereso_mc'] = nominal['ereso_mc']

    nominal['eresp'] = np.sqrt(eresp)
    nominal['ereso'] = np.sqrt(ereso)

    if fit_2g:
        return nominal, fit_2g
    else:
        return nominal 
   

def apply_corrlib_df(df: pd.DataFrame, cset_vars:List[str], cset_name:str, cset_file:str, syst_name:str, mll_name='mass', ptl_name='pt'):
    """Apply the correction lib to a pandas dataframe

    Args:
        df (pd.DataFrame): dataframe with the variables to correct
        cset_vars (List[str]): list of the variables used in the correction
        cset_name (str): name of the correction set
        cset_file (str): name of the correction file
        syst_name (str): type of correction to apply: scale or smear
        mll_name (str, optional): dilepton mass variable name. Defaults to 'mass'.
        ptl_name (str, optional): lepton tranverse momentum variable name. Defaults to 'pt'.
    """
    import correctionlib
    cset = correctionlib.CorrectionSet.from_file(cset_file)
    try:
        corr = cset[cset_name]
    except IndexError:
        corr = cset.compound[cset_name]

    lep_names = [f'{name}1' for name in cset_vars]
    lep_names = [name.split('1')[0] for name in df.columns.intersection(lep_names)]
    for i_ele in [1, 2]:
        lep_vars = [df[f'{var}{i_ele}' if var in lep_names else var] for var in cset_vars]

        scales = corr.evaluate(*([syst_name] + lep_vars))
        if syst_name == 'smear':
            try:
                scales *= corr.evaluate(*(['stdnormal'] + lep_vars))
                print('Smearing using the included random number generator')
            except:
                scales = np.random.normal(1, scales)
                print('Smearing using the numpy random')

        df[mll_name] *= np.sqrt(scales)
        df[f'{ptl_name}{i_ele}'] *= scales


# ------------------------------------------------------------------------------------------
# -- Potentially fit the results of the SAS when they are computed vs pT
# -- This is done to avoid spikes in the pT spectrum (+ smoothen the result)
# ------------------------------------------------------------------------------------------
class FuncStr:
    def __init__(self, expression: str):
        """This class generates a numpy verctorized function based on a string expression
            Parameters for fits are possible with [], e.g. par0 == [0]
        Args:
            expression (str): analytical expression of the form "np.sqrt([1]*x + [0])

        Raises:
            SyntaxError: checkout that the syntax is correct (only [] for now)
        """
        if expression.count("[") != expression.count("]"):
            raise SyntaxError("Missing a stating or closing braket")
        self.n_par = 1 + expression.count("[")
        self.expression = expression

    def replace_par(self, *par):
        expression = self.expression
        for p_name, p_val in zip([f"[{ip}]" for ip in range(self.n_par-1)], par):
            expression = expression.replace(p_name, f'{p_val:.10f}')
        return expression

    def tformula(self, *par) -> str:
        """Return a ROOT type TFormula replacing parameters with inputs pars

        Returns:
            str: TFormula expression
        """
        expression = self.expression
        for p_name, p_val in zip([f"[{ip}]" for ip in range(self.n_par-1)], par):
            expression = expression.replace(p_name, f'{p_val:.10f}')
        expression = expression.replace('np.', '')
        expression = expression.replace('power', 'pow')
        return expression
    
    def __call__(self, x, *par):
        return np.frompyfunc(lambda x, *par: eval(self.replace_par(*par)), self.n_par, 1)(x, *par)


resp_exp = "[0] * np.power(min(x, 160)/45., [1]) + [2]"  # fix corr for pT > 160 GeV
reso_exp = "np.sqrt(np.abs(np.power([0], 2) + [1]/min(x, 160)))"   # fix corr for pT > 160 GeV

pt_fit_resp = FuncStr(resp_exp)
pt_fit_reso = FuncStr(reso_exp)

p0_resp = [-0.02, -1., 1.0]
pr_resp = [[-0.9, 0.5], [-5, 5], [0.5, 1.5]]
p0_reso = [0.01, 0.0]
pr_reso = [[1e-3, 0.1], [-0.05, 0.05]]


def do_pt_fit(axval, avar, eavar, func:FuncStr, p0, p_range, 
           do_plot=False, min_pt=25, max_pt = 160, width_pt=0.5):
    
    minimizer="BFGS"

    fit_result = [None] * avar.shape[-1]
    if do_plot:
        n_row = int(np.ceil(avar.shape[-1]/3.))
        fig, ax = plt.subplots(3, n_row, figsize=(9, 3*n_row) )
        ax = ax.flatten()
    
    fine_pt_bining = np.linspace(min_pt, max_pt, int((max_pt-min_pt)/width_pt) + 1 )
    xxval = (fine_pt_bining[1:] + fine_pt_bining[:-1])*0.5
    y_fine = []
    for i_dim in np.arange(avar.shape[-1]):
        fitter = FFitter(p0=p0, p_range=p_range, minimizer=minimizer)
        par, epar = fitter.fit(axval, avar[:, i_dim], eavar[:, i_dim], func)
        if par is None:
            fitter = FFitter(p0=p0, p_range=p_range, minimizer='Nelder-Mead')
            par1, epar1 = fitter.fit(axval, avar[:, i_dim], eavar[:, i_dim], func) 
            print(" * refit1", par1)
            fitter = FFitter(p0=par1, p_range=p_range, minimizer=minimizer)
            par, epar = fitter.fit(axval, avar[:, i_dim], eavar[:, i_dim], func) 
            print(" * refit2", par)
            if par is None:
                par, epar = (par1, epar1)
        y_fine.append(func(xxval, *par))
        if do_plot:
            plt.sca(ax[i_dim])
            cms.draw(axval, avar[:, i_dim], yerr=eavar[:, i_dim], option ='E')
            ax[i_dim].plot(xxval, y_fine[-1], color=ax[i_dim].lines[-1].get_color(), ls='--')
        fit_result[i_dim] = func.tformula(*par)

    return fit_result 


def pt_smoothing(json_file:Union[str, Path, Dict], dim_to_fit='pt', do_plot=False) -> Tuple[Dict, Dict]:
    """Function to fit the pT-dependent sas to make them smooth

    Args:
        json_file (Union[str, Path]): name of the json file containing the result of the sas fit
        dim_to_fit (str, optional): name of the pt dimension. Defaults to 'pt'.

    Returns:
        Dict: new sas dictionnary
    """
    params = parameters_from_json(json_file)
    if params.get('pt', None) is not None:
        xval = params['pt']
    else:
        return {}
        
    fit_vres = {}
    fit_eres = {}
    for sas_type in ['resp', 'reso']:
        var, evar, evar_mc = params[sas_type], params[f'e{sas_type}'], params[f'e{sas_type}_mc']
        
        # -- find the dimension with pt
        idim_pt = np.where(params['dims'] == dim_to_fit)[0][-1]
        d_perm = [idim_pt] + [idim for idim, d in enumerate(params['dims']) if d != dim_to_fit]
        var = tf.transpose(var, perm=d_perm).reshape(var.shape[idim_pt], -1)
        evar = tf.transpose(evar, perm=d_perm).reshape(evar.shape[idim_pt], -1)
        evar_mc = tf.transpose(evar_mc, perm=d_perm).reshape(evar.shape[idim_pt], -1)

        p0 = p0_resp if sas_type == 'resp' else p0_reso
        pr = pr_resp if sas_type == 'resp' else pr_reso
        pt_fit = pt_fit_resp if sas_type == 'resp' else pt_fit_reso

        var = var.numpy()
        evar = evar.numpy()
        var_up = var + evar
        if sas_type == 'resp':
            var = 1 / var
            var_up = 1 / (var - evar)
        res = do_pt_fit(xval, var, evar, pt_fit, p0, pr, do_plot=do_plot)
        res_up = do_pt_fit(xval, var_up, evar, pt_fit, p0, pr)
        fit_vres[sas_type] = res
        fit_eres[sas_type] = res_up

    eresp_abs = f'abs({fit_vres["resp"]} - {fit_vres["resp"]})'
    ereso_abs = f'abs({fit_vres["reso"]} - {fit_vres["reso"]})'
    eresp_rel = f'abs({fit_vres["resp"]}/{fit_vres["resp"]} - 1)'

    fit_res_dt = {'scale': fit_vres['resp'], 'escale': eresp_abs}
    fit_res_mc = {'smear': fit_vres['reso'], 'escale': eresp_rel, 'esmear': ereso_abs}
    return fit_res_dt,  fit_res_mc


def create_pt_corrector(sas: Union[Dict, str, Path], dir_results:Union[Path, str]='./tmp/', dset_name='DSET', cset_name='CSET',
                        cset_description:str=None, cset_version=1, cat_latex=None, pt_name='pt'):
    """Create a correction lib files based 

    Args:
        sas (Dict, ): dictionnary with scales and smearings
        dir_results (Path, optional): directory. Defaults to Path('./tmp/').
        dset_name (str, optional): dataset nickname. Defaults to 'DSET'.
        cset_name (str, optional): correction saet name. Defaults to 'CSET'.
        cset_description (str, optional): description of the correction set. Defaults to None.
        cset_version (int, optional): correction set version. Defaults to 1.
        cat_latex (Dict, optional): dictionnary with a description of variables in categories. Defaults to None.
    """
    import correctionlib.schemav2 as cs
    import rich
    print(f'--------------------------------------------')
    print(f'---- Create correction lib with PT SMOOTHING')
    print(f'--------------------------------------------')
    # -- do fits
    fit_dt, fit_mc = pt_smoothing(sas)

    if not isinstance(sas, Dict):
        sas = json_safe_load(sas)
    
    if cat_latex is None:
        cat_latex = {key: key for key in sas['categories']}
    dir_results = Path(dir_results)

    categories = sas['categories'].copy()
    categories.pop(pt_name)
    edges = list(categories.values())
    n_val = np.prod([len(e)-1 for e in edges])

    def get_correction(sas_type, fit_results):
        input_cats = [cs.Variable(name=dim, type='real', description=cat_latex[dim]) for dim in  categories.keys()]
        
        def get_pt_corr(expression, flow='clamp'):
            content=[cs.Formula(nodetype="formula", variables=[pt_name], parser="TFormula", expression=expression[ibin]) for ibin in range(n_val)]
            return cs.MultiBinning(nodetype='multibinning',
                                   inputs=list(categories.keys()),
                                   edges=edges,
                                   content=content,
                                   flow=flow)  
            
        cset = cs.Correction(name=f"EGMScale_{cset_name}_{dset_name}" if sas_type == 'scale' else f"EGMSmearAndSyst_{cset_name}_{dset_name}" ,
                            version = cset_version,
                            description=cset_description,
                            inputs = [cs.Variable(name="syst", type="string", description="Systematic type"),
                                      cs.Variable(name=pt_name, type="real", description="p_T in GeV")] + input_cats ,
                            output = cs.Variable(name=sas_type, type="real", description=f"EM {sas_type} value"),
                            data = cs.Category(nodetype='category',
                                               input='syst',
                                               content=[cs.CategoryItem(key=k,value=get_pt_corr(v)) for k, v in fit_results.items()],
                                               default=get_pt_corr(fit_results[sas_type]))
                            )
        return cset

    c_scale = get_correction('scale', fit_dt)
    c_smear = get_correction('smear', fit_mc)
    rich.print(c_scale)
    rich.print(c_smear)
    
    cset = cs.CorrectionSet(schema_version=2,
                            description=cset_description,
                            corrections=[c_scale, c_smear]
                            )
    dir_results.mkdir(exist_ok=True)
    file_out = dir_results / f"EGMScalesSmearing_{dset_name}_SMOOTH.v{cset_version}.json"
    print(f"Writing out correction lib file: {file_out}.gz")
    import gzip
    with gzip.open(f"{file_out}.gz", "wt") as fout:
        fout.write(cset.model_dump_json(indent=1,exclude_unset=True))
    return c_scale


def ijazz_sas_smoothing():
    """entry point for the ijazz_sas_smoothing command
    """
    import argparse
    import sys
    parser = argparse.ArgumentParser(description=f'IJazZ Scale and Smearing fit')
    parser.add_argument('json_file', type=str, help='name of json file')
    parser.add_argument('--dset', type=str, default='DSET', help="name of the dataset")
    parser.add_argument('--cset', type=str, default='CSET', help="name of the correction set")
    parser.add_argument('--description', type=str, default=None, help="cset description")
    parser.add_argument('-v', '--vers', type=int, default=1, help="cset version")
    parser.add_argument('-o', '--outdir', type=str, default="./", help="output directory")
    args = parser.parse_args(sys.argv[1:])

    create_pt_corrector(args.json_file, dir_results=args.outdir, dset_name=args.dset, cset_name=args.cset,
                        cset_description=args.description, cset_version=args.vers) 




