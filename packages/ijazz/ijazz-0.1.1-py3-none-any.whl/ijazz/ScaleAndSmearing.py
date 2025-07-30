import numpy as np, pandas as pd
from ijazz.RegionalFitter import RegionalFitter
import tensorflow as tf
from typing import Union, List, Dict
from pathlib import Path
import yaml, json
import argparse, sys
from ijazz.dtypes import floatzz, uintzz
from copy import deepcopy
from .sas_utils import to_correction_lib, json_safe_load, parameters_to_json, parameters_from_json, create_pt_corrector, apply_corrlib_df, compute_syst_from_jsons
from .categorize import categorize

def ijazz_sas_cmd():
    """
    entry point for the ijazz_sas command
    """
   
    parser = argparse.ArgumentParser(description=f'IJazZ Scale and Smearing fit')
    parser.add_argument('config', type=str, help='yaml config file')
    args = parser.parse_args(sys.argv[1:])

    with open(args.config, 'r') as fcfg:
        config = yaml.safe_load(fcfg)
    
    ijazz_sas(config)

def ijazz_sas(config:dict=None, do_fit=True, save_corrlib=True):
    """
    Perform the scale and smearing fit, plot the results and save the results.
    The configuration file should contain the following sections:

    - file_dt: data file (parquet format)
    - file_mc: mc file (parquet format)
    - dir_results: directory where to save the results
    - fitter: configuration for the fitter
    - sas: configuration for the scale and smearing fit
    - minimizer: configuration for the minimizer
    - syst: configuration for the systematic computation
    - corrlib: add description and version number to the correctionlib file
    - cat_latex: dictionary to convert the category name to latex
    - scale_flat_syst: flat systematic for scale
    - smear_flat_syst: flat systematic for smearing
    - dset_name: name of the dataset eg ``2023``
    - cset_name: name of the correction set eg ``EtaR9``

    See an example `sas_config.yaml <https://gitlab.cern.ch/fcouderc/ijazz_2p0/-/blob/master/config/sas_config.yaml?ref_type=heads>`_
    
    Args:
        config (dict): configuration dictionary containing the parameters for the fit
        do_fit: if True, perform the fit
        save_corrlib: if True, save the correctionlib file
    """

    files_dt = [config['file_dt']] if np.isscalar(config['file_dt']) else config['file_dt']
    files_mc = [config['file_mc']] if np.isscalar(config['file_mc']) else config['file_mc']

    dt = pd.concat([pd.read_parquet(afile).assign(ifile=ifile) for ifile, afile in enumerate(files_dt)]).reset_index(drop=True)
    mc = pd.concat([pd.read_parquet(afile).assign(ifile=ifile) for ifile, afile in enumerate(files_mc)]).reset_index(drop=True)

    dir_results = Path(config['dir_results'])
    dir_results.mkdir(parents=True, exist_ok=True)

    dset_name = config.get('dset_name', 'DSET')
    cset_name = config.get('cset_name', 'CSET')

    # -- save the raw mass for systematic computation
    mll_name = config['fitter'].get('name_mll', 'mee')
    dt[f'{mll_name}_orig'] = dt[mll_name]
    mc[f'{mll_name}_orig'] = mc[mll_name]

    config['sas']['dump_json'] = dir_results / f'SAS{dset_name}_syst-Nominal.json'
    if do_fit:
        compute_sas(dt, mc, config)

    json_file_out = dir_results / f'SAS{dset_name}_syst-Nominal.json'
    nominal_json = str(json_file_out)
    fit_2g_json = None
    import ijazz.plotting as ijp
    resp_range = (0.98, 1.03)
    reso_range = (0., 0.05)
    cat_latex = config.get('cat_latex', None)
    figs, _ = ijp.plot_results_from_json(json_file_out, resp_range=resp_range, reso_range=reso_range, 
                                         cat_latex=cat_latex, leg_fontsize='small')
    for ifig, fig in enumerate(figs):
        print(f" --> Plot nominal : {json_file_out.with_suffix(f'.fig{ifig}.jpg')}")
        fig.savefig(json_file_out.with_suffix(f'.fig{ifig}.jpg'))

    # -- plot the extra parameters if using double gaussian
    if config['fitter'].get('double_gaussian', False):
        figs, _ = ijp.plot_results_from_json2G(json_file_out, mu_range=(0.79, 1.01), reso2_range=(0.0, 0.15), frac_range=(0.79, 1.01), 
                                         cat_latex=cat_latex, leg_fontsize='small')
        for ifig, fig in enumerate(figs):
            print(f" --> Plot nominal : {json_file_out.with_suffix(f'.extra.fig{ifig}.jpg')}")
            fig.savefig(json_file_out.with_suffix(f'.extra.fig{ifig}.jpg'))
    
    if config.get('syst', False):
        syst_jsons = []

        scale_flat_syst = config.get('scale_flat_syst', 0)
        smear_flat_syst = config.get('smear_flat_syst', 0)
        config_ref = deepcopy(config)
        for syst_name, syst_cfg  in config['syst'].items():
            print(f'---------------------------------------')
            print(f'----- syst {syst_name}')
            print(f'---------------------------------------')
            dt[mll_name] = dt[f'{mll_name}_orig']
            mc[mll_name] = mc[f'{mll_name}_orig']
            print(syst_cfg)
            config = deepcopy(config_ref)
            for sub_sec, sub_cfg in syst_cfg.items():
                for k, v in sub_cfg.items():
                    config[sub_sec][k] = v
            config['sas']['correct_data'] = False
            config['sas']['correct_mc'] = False
            config['sas']['dump_json'] = dir_results / f'SAS{dset_name}_syst-{syst_name}.json'
            if do_fit:
                compute_sas(dt, mc, config)
            sas_syst = json_safe_load(config['sas']['dump_json'])

            if config['fitter'].get('double_gaussian', False):
                fit_2g_json = str(dir_results / f'SAS{dset_name}_syst-{syst_name}.json')
            else:
                syst_jsons.append(str(dir_results / f'SAS{dset_name}_syst-{syst_name}.json'))

            
    
            if config['fitter'].get('double_gaussian', False):
                # plot the scales and smearings ratio 
                figs, _ = ijp.plot_results_from_json({'nominal': nominal_json, 'syst': str(dir_results / f'SAS{dset_name}_syst-{syst_name}.json')}, 
                                        resp_range=(0.99, 1.01), reso_range=(0.5, 1.5), cat_latex=cat_latex, jsons_mode='ratio', leg_fontsize='small')
                for ifig, fig in enumerate(figs):
                    print(f" --> Plot {syst_name} : {dir_results}/SAS{dset_name}_syst-{syst_name}.2G-params.fig{ifig}.jpg")
                    fig.savefig(dir_results / f'SAS{dset_name}_syst-{syst_name}.2G-params.fig{ifig}.jpg')

                # plot the extra parameters if using double gaussian
                figs, _ = ijp.plot_results_from_json2G(parameters_from_json(sas_syst), 
                                       mu_range=(0.79, 1.01), reso2_range=(0.0, 0.15), frac_range=(0.79, 1.01), cat_latex=cat_latex, leg_fontsize='small')
                for ifig, fig in enumerate(figs):
                    print(f" --> Plot {syst_name} : {dir_results}/SAS{dset_name}_syst-{syst_name}.2G-params-extra.fig{ifig}.jpg")
                    fig.savefig(dir_results / f'SAS{dset_name}_syst-{syst_name}.2G-params-extra.fig{ifig}.jpg')
            
            else:
                #-- plot ratio of syst/nominal
                figs, _ = ijp.plot_results_from_json({'nominal': nominal_json, 'syst': str(dir_results / f'SAS{dset_name}_syst-{syst_name}.json')}, 
                                        resp_range=(0.99, 1.01), reso_range=(0.5, 1.5), cat_latex=cat_latex, jsons_mode='ratio', leg_fontsize='small')
                for ifig, fig in enumerate(figs):
                    print(f" --> Plot {syst_name} : {dir_results}/SAS{dset_name}_syst-{syst_name}.fig{ifig}.jpg")
                    fig.savefig(dir_results / f'SAS{dset_name}_syst-{syst_name}.fig{ifig}.jpg')
                
        # -- re-init config to its original value
        config = deepcopy(config_ref)

        if fit_2g_json:
            # -- compute the systematic errors from the jsons
            nominalWithSyst, fit2GWithSyst = compute_syst_from_jsons(nominal_json, syst_jsons, fit_2g=fit_2g_json, scale_flat_syst=scale_flat_syst, smear_flat_syst=smear_flat_syst)
            
            # save 2G fit with syst
            json_file_out2G = dir_results / f'SAS{dset_name}_syst-Nominal2GWithSyst.json'
            if save_corrlib:
                parameters_to_json(fit2GWithSyst, json_file_out2G)
            # save 1G fit with syst
            json_file_out = dir_results / f'SAS{dset_name}_syst-NominalWithSyst.json'
            if save_corrlib:
                parameters_to_json(nominalWithSyst, json_file_out)
            
            #-- plot 2G result with adjusted syst
            figs, _ = ijp.plot_results_from_json({'nominal':parameters_from_json(json_file_out2G), 'syst':parameters_from_json(json_file_out2G)}, jsons_mode='ratio',
                                              resp_range=(0.99, 1.01), reso_range=(0.5, 1.5), cat_latex=cat_latex, leg_fontsize='small')
            for ifig, fig in enumerate(figs):
                print(f" --> Plot Nominal 2G with Syst : {json_file_out2G.with_suffix(f'.fig{ifig}.jpg')}")
                fig.savefig(json_file_out2G.with_suffix(f'.fig{ifig}.jpg'))

    
        

            #-- plot 2G syst contribution
            # recompute mean and std of the 2G fit
            fit_2g = parameters_from_json(fit2GWithSyst)
            fit_2g['resp'] = fit_2g['mean2G']
            fit_2g['reso'] = fit_2g['std2G']

            #-- plot ratio of syst/nominal
            figs, _ = ijp.plot_results_from_json({'nominal': nominal_json, 'syst': fit_2g}, 
                                       resp_range=(0.99, 1.01), reso_range=(0.5, 1.5), cat_latex=cat_latex, jsons_mode='ratio', leg_fontsize='small')
            for ifig, fig in enumerate(figs):
                print(f" --> Plot {syst_name} : {dir_results}/SAS{dset_name}_syst-{syst_name}.fig{ifig}.jpg")
                fig.savefig(dir_results / f'SAS{dset_name}_syst-{syst_name}.fig{ifig}.jpg')

            # plot the mean difference
            figs, _ = ijp.plot_results_from_json({r'$\langle r \rangle_{1G}$':json_file_out,r'$\langle r \rangle_{2G}$':fit_2g}, jsons_mode='compare',param_to_plot='resp',resp_range=[0.995,1.01],reso_range=[0.0,0.045], cat_latex=cat_latex, hide_legend=False)
            for ifig, fig in enumerate(figs):
                print(f" --> Plot 2G syst (mean diff) : {dir_results / f'SAS{dset_name}_syst-smearing_shape-mean_diff.fig{ifig}.jpg'}")
                fig.savefig(dir_results / f'SAS{dset_name}_syst-smearing_shape-mean_diff.fig{ifig}.jpg')

            # plot the std difference
            figs, ax = ijp.plot_results_from_json({r'$\sigma_{1G}$':json_file_out,r'$\sigma_{2G}$':fit_2g}, jsons_mode='compare',param_to_plot='reso',resp_range=[0.99,1.015],reso_range=[0.0,0.045], cat_latex=cat_latex, hide_legend=False)
            for ifig, fig in enumerate(figs):
                print(f" --> Plot 2G syst (std diff) : {dir_results / f'SAS{dset_name}_syst-smearing_shape-std_diff.fig{ifig}.jpg'}")
                fig.savefig(dir_results / f'SAS{dset_name}_syst-smearing_shape-std_diff.fig{ifig}.jpg')
        else:
            # -- compute the systematic errors from the jsons
            nominalWithSyst = compute_syst_from_jsons(nominal_json, syst_jsons, scale_flat_syst=scale_flat_syst, smear_flat_syst=smear_flat_syst)
            json_file_out = dir_results / f'SAS{dset_name}_syst-NominalWithSyst.json'
            parameters_to_json(nominalWithSyst, json_file_out)

         #-- plot nominal result with adjusted syst
        figs, _ = ijp.plot_results_from_json({'nominal':parameters_from_json(json_file_out), 'syst':parameters_from_json(json_file_out)}, jsons_mode='ratio',
                                              resp_range=(0.99, 1.01), reso_range=(0.5, 1.5), cat_latex=cat_latex, leg_fontsize='small')
        for ifig, fig in enumerate(figs):
            print(f" --> Plot Nominal with Syst : {json_file_out.with_suffix(f'.fig{ifig}.jpg')}")
            fig.savefig(json_file_out.with_suffix(f'.fig{ifig}.jpg'))

    if config.get('corrlib', False) and save_corrlib:
        corrlib_file, cset_vars = to_correction_lib(json_file_out, dir_results=dir_results, dset_name=dset_name, cset_name=cset_name, 
                                                    cset_description=config['corrlib'].get('cset_description', None), 
                                                    cset_version=config['corrlib'].get('cset_version', 1))
        if fit_2g_json:
            _, _ = to_correction_lib(json_file_out2G, dir_results=dir_results, dset_name=dset_name+'2G', cset_name=cset_name, 
                                                        cset_description=config['corrlib'].get('cset_description', "SaS")+" using double gaussian smearing", 
                                                        cset_version=config['corrlib'].get('cset_version', 1))
        
        if config['corrlib'].get('smoothing', False):
            create_pt_corrector(json_file_out, dir_results=dir_results, dset_name=dset_name, cset_name=cset_name, 
                                cset_description=config['corrlib'].get('cset_description', None), 
                                cset_version=config['corrlib'].get('cset_version', 1))  

        def save_to_parquet(is_mc):
            correct = config['sas'].get('correct_mc', False) if is_mc else config['sas'].get('correct_data', False)
            if not correct:
                return
            
            df = mc if is_mc else dt
            syst_name = 'smear' if is_mc else 'scale'
            corr_name = f'EGMSmearAndSyst_{cset_name}_{dset_name}' if is_mc else f'EGMScale_{cset_name}_{dset_name}'
            print(f'Apply SAS correction (is_mc = {is_mc})')
            apply_corrlib_df(df, cset_vars, corr_name, corrlib_file, syst_name, mll_name=mll_name)

            cat_name = config['fitter'].get('name_cat', 'cat')
            col_to_drop = [col for col in df.columns if col[:len(cat_name)]==cat_name] + ['ifile'] 
            for ifile, afile in enumerate(files_mc if is_mc else files_dt):
                print(afile)
                df_fileout = Path(afile).with_suffix(f".{cset_name}Corr.parquet")
                print(f'Saving corrected dataset to {df_fileout}')
                df.query("ifile == @ifile").drop(columns=col_to_drop).to_parquet(df_fileout, engine='auto')
        save_to_parquet(is_mc=True)
        save_to_parquet(is_mc=False)      



    

class IJazZSAS:
    def __init__(self, dt: pd.DataFrame, mc: pd.DataFrame, config: dict, categories: dict=None) -> None:
        """This class performs the scale and smearing fit for leptons in different categories.
        The input dataframe should have as columns contain the categorisation variables.
        The naming convention is "var1" (resp. "var2") for the value of the variable var for lepton 1 (resp. 2)
        WARNING: If pt is used for categorisation the naming convention is "pt", so please rename if necessary
        For categorisation with "pt" bining it is more reliable to do the fit based on a categorisation on the relative pt.
        This will be automatically done unless turned off (use_r_pt=False).

        Args:
            dt (pd.DataFrame): dataframe containing the data events
            mc (pd.DataFrame): dataframe containing the mc events
            config (dict): dictionary containing the config of the RegionalFitter and its minimize function. An example yaml is given in the repertory configs/ 
            categories (dict): dictionary for categorisation, e.g. {'pt': [25, 50, 100], 'abs_eta': [0, 1, 2]}. Defaults to None (can be specified in the config dict)

        NB: the config dictionnary can be saved under a yaml file (prefered), opened and passed to the fitter.
        It **MUST** have three section: "sas", "fitter", "minimizer"
        """
        try:
            config["sas"]
        except KeyError:
            raise KeyError('The sas section is not present in the configuration dict')
        
        try:
            config["fitter"]
        except KeyError:
            raise KeyError('The fitter section is not present in the configuration dict')

        try:
            config["minimizer"]
        except KeyError:
            raise KeyError('The minimizer section is not present in the configuration dict')

        if categories is None:
            # - this will crask if no categories section but this is expected.
            categories = config['sas']['categories']

        self.categories_def = categories
        self.cfg = config
        self.double_gaussian = config['fitter'].get('double_gaussian', False)
        print(f"Double gaussian fit: {self.double_gaussian}")

        use_rpt = config['sas'].get('use_rpt', True)
        self.mll_name = config['fitter'].get('name_mll', 'mee')
        self.pt_name = config['sas'].get('name_pt_var', 'pt')
        self.cat_name = config['fitter'].get('name_cat', 'cat')
        cut = config['sas'].get('cut', None)
        cut = '' if cut is None else cut

        if categories.get(self.pt_name, None):
            pt_bins = categories[self.pt_name]
            cut_pt = f"{self.pt_name}1 >= {pt_bins[0]} and {self.pt_name}2 >= {pt_bins[0]}" + " and " + \
                f"{self.pt_name}1 < {pt_bins[-1]} and {self.pt_name}2 < {pt_bins[-1]}"
            cut = cut_pt if cut == "" else f'{cut} and {cut_pt}'
        self.cut = cut
        print(f"Applying selection: {cut}")

        # -- if one of the categories is pt or et, categorize first vs pT/mee
        self.has_pt = False
        if use_rpt:
            self.categories = {'r_pt'  if key == self.pt_name else key : np.array(values)/91.2 
                                if key == self.pt_name else np.array(values) for key, values in categories.items()}
            if self.pt_name in list(categories.keys()):
                self.has_pt = True
                for df in [dt, mc]:
                    for i_ele in [1, 2]:
                        df[f'r_pt{i_ele}'] = df[f'{self.pt_name}{i_ele}'] / df[self.mll_name]
        else:
            self.categories = categories
        
        # can have different MC/data categories when recasting w/r to pT
        self.categories_mc = self.categories.copy() 
        self.categories_dt = self.categories.copy() 

        for df in [dt, mc]:
            self.lepton_reg = categorize(df, self.categories, cut=self.cut, prefix=self.cat_name)

        self.dt = dt
        self.mc = mc

        self.fitter = None
        self.resp = None
        self.reso = None
        self.resp_corr = None     # -- response after data scale correction
        self.reso_uncorr = None   # -- resolution before data scale correction
        self.eresp = None
        self.ereso = None
        self.eresp_mc = None
        self.ereso_mc = None
        self.pt_mean = None

    def fit(self, optimizer=tf.keras.optimizers.Adam) -> np.ndarray:
        """Actually performs the fit

        Args:
            optimizer (class): tensorflow compatible optimizer for instance tf.keras.optimizers.Adam (this is not the optimizer the the class)
            learning_rate (float, optional): learning rate to pass to the optimizer. Defaults to 0.01.
            dnll_tol (float, optional): delta likelihood tolerance to stop the fit. Defaults to 0.01.
            max_epochs (int, optional): maximum number of iteration. Defaults to 1000.
            init_rand (bool, optional): random starting poin. Defaults to False.
            batch_size (int, optional): can perform the fit in batch size (usefull for large number of parameters). Defaults to -1.
            device (str, optional): _description_. Defaults to 'CPU'.
            batch_training (bool, optional): use the batch training mode. Defaults to False.
            hess (str, optional): computation of the hession (None, 'numerical', or 'analytical'), it can take a while. Defaults to 'numerical'.
            cats (_type_, optional): subset of categories to perform the fit. Defaults to slice(None).

        Returns:
            np.ndarray: array of the value of the -2 * log likelihood during the fit
        """
        learning_rate = self.cfg['sas'].get('learning_rate', 1e-3)
        print("======== FIT (first fit, binings including pt require a second one)")
        fitter = RegionalFitter(self.dt, self.mc, n_par=self.lepton_reg.size, **self.cfg['fitter'])
        nlls = fitter.minimize(optimizer(learning_rate=learning_rate), **self.cfg['minimizer'])       
        self.resp = fitter.resp.numpy().astype(np.float32).copy()
        self.reso = np.abs(fitter.reso.numpy().astype(np.float32).copy())
        self.eresp = np.zeros(self.resp.shape, dtype=np.float32)
        self.ereso = np.zeros(self.reso.shape, dtype=np.float32)
        self.eresp_mc = np.ones(self.resp.shape, dtype=np.float32)*np.nan
        self.ereso_mc = np.ones(self.reso.shape, dtype=np.float32)*np.nan

        if self.double_gaussian:
            self.reso2 = np.abs(fitter.reso2.numpy().astype(np.float32).copy())
            self.mu = fitter.mu.numpy().astype(np.float32).copy()
            self.frac = fitter.frac.numpy().astype(np.float32).copy()
            self.ereso2 = np.zeros(self.reso2.shape, dtype=np.float32)
            self.emu = np.zeros(self.mu.shape, dtype=np.float32)
            self.efrac = np.zeros(self.frac.shape, dtype=np.float32)
            self.ereso2_mc = np.ones(self.reso2.shape, dtype=np.float32)*np.nan
            self.emu_mc = np.ones(self.mu.shape, dtype=np.float32)*np.nan
            self.efrac_mc = np.ones(self.frac.shape, dtype=np.float32)*np.nan

        if self.has_pt:
            print("======== FIT with scale correction for pT bining")
            self.recast_pt_bins(prefix='cat_corr')
            self.correct_data(self.resp, prefix='cat_corr')
            fitter = RegionalFitter(self.dt, self.mc, n_par=self.lepton_reg.size, **self.cfg['fitter'])
            nlls = fitter.minimize(optimizer(learning_rate=learning_rate), **self.cfg['minimizer'])
            self.reso_uncorr = self.reso.copy()
            self.resp_uncorr = self.resp.copy()
            self.resp = self.resp * fitter.resp.numpy()
            self.reso = np.abs(fitter.reso.numpy().copy())

            if self.double_gaussian:
                self.reso2_uncorr = self.reso2.copy()
                self.mu_uncorr = self.mu.copy()
                self.frac_uncorr = self.frac.copy()
                self.reso2 = np.abs(fitter.reso2.numpy().copy())
                self.mu = fitter.mu.numpy().copy()
                self.frac = fitter.frac.numpy().copy()

            # -- uncorrect the data
            self.dt[self.mll_name] = self.dt[f'{self.mll_name}_raw']
            for i_ele in [1, 2]:
                self.dt[f'{self.pt_name}{i_ele}'] = self.dt[f'pt_raw{i_ele}']
            self.dt.drop(columns=[f'{self.mll_name}_raw', 'pt_raw1', 'pt_raw2'], inplace=True)

        self.fitter = fitter  # -- keep the fitter
        return nlls

    def calc_err_stat(self, force=False):
        hess = self.cfg['sas'].get('hess', False)
        if hess:
            numerical = True if hess == 'numerical' else False
            print(f"======== HESSIAN COMPUTATION: numerical {numerical}")
            self.fitter.covariance(numerical=numerical, force=force, batch_size=-1)
            self.eresp = self.fitter.eresp
            self.ereso = self.fitter.ereso
            if self.double_gaussian:
                self.ereso2 = self.fitter.ereso2
                self.emu = self.fitter.emu
                self.efrac = self.fitter.efrac
        else:
            print("NB: HESSIAN computation was not requested")

    def calc_err_mc(self):
        """compute the error due to MC statistical fluctuations, this may take a while
        """
        if self.cfg['sas'].get('err_mc', True):
            print(f"======== MC UNCERTAINTY COMPUTATION")
            self.fitter.calc_err_mc()
            self.eresp_mc = self.fitter.eresp_mc.copy()
            self.ereso_mc = self.fitter.ereso_mc.copy()
            self.eresp = np.sqrt(self.eresp**2 + self.eresp_mc**2)
            self.ereso = np.sqrt(self.ereso**2 + self.ereso_mc**2)
            if self.double_gaussian:
                self.ereso2_mc = self.fitter.ereso2_mc.copy()
                self.emu_mc = self.fitter.emu_mc.copy()
                self.efrac_mc = self.fitter.efrac_mc.copy()
                self.ereso2 = np.sqrt(self.ereso2**2 + self.ereso2_mc**2)
                self.emu = np.sqrt(self.emu**2 + self.emu_mc**2)
                self.efrac = np.sqrt(self.efrac**2 + self.efrac_mc**2)
        else:
            print("NB: no MC uncertainties were required")

    def correct_data(self, response: np.ndarray, prefix:str=None):
        """correct the data dataframe after the fit

        Args:
            response (np.ndarray): array with the responses to apply for correction
            prefix (str, optional): prefix used for naming the categorisation. Defaults to None.
        """
        if prefix is None:
            prefix = self.cfg['fitter']['name_cat']
        self.dt[f'{self.mll_name}_raw'] = self.dt[self.mll_name]
        for i_ele in [1, 2]:
            self.dt[f'pt_raw{i_ele}'] = self.dt[f'{self.pt_name}{i_ele}']
            idx = self.dt[f'{prefix}{i_ele}'] >= 0
            scale = response[self.dt.loc[idx, f'{prefix}{i_ele}']]
            self.dt.loc[idx, f'{self.pt_name}{i_ele}'] /= scale
            self.dt.loc[idx, self.mll_name] /= np.sqrt(scale)

    def correct_mc(self, resolution: np.ndarray, prefix:str=None):
        """correct the mc dataframe

        Args:
            resolution (np.ndarray): array with the relative resolution to smear the MC
            prefix (str, optional): prefix used for naming the categorisation. Defaults to None.
        """
        if prefix is None:
            prefix = self.cfg['fitter']['name_cat']

        

        def rbinorm(n, mu, sigma1, sigma2, frac):
            # Generate samples from each normal distribution
            scales = np.array([mu*np.random.normal(1, sigma2, n), np.random.normal(1, sigma1, n)])
            binom = np.random.binomial(1, frac, n)
            return scales[binom, np.arange(n)]

        self.mc[f'{self.mll_name}_raw'] = self.mc[self.mll_name]
        for i_ele in [1, 2]:
            self.mc[f'pt_raw{i_ele}'] = self.mc[f'{self.pt_name}{i_ele}']
            idx = self.mc[f'{prefix}{i_ele}'] >= 0
            if self.cfg['fitter'].get('double_gaussian', False):
                # smear = rbinorm(len(idx), self.mu[self.mc.loc[idx, f'{prefix}{i_ele}']], resolution[self.mc.loc[idx, f'{prefix}{i_ele}']], self.reso2[self.mc.loc[idx, f'{prefix}{i_ele}']], self.frac[self.mc.loc[idx, f'{prefix}{i_ele}']])
                smear = rbinorm(len(idx), self.mu[0], resolution[self.mc.loc[idx, f'{prefix}{i_ele}']], self.reso2[self.mc.loc[idx, f'{prefix}{i_ele}']], self.frac[0])
            else:
                smear = np.random.normal(1, resolution[self.mc.loc[idx, f'{prefix}{i_ele}']]).astype(np.float32)
            self.mc.loc[idx, f'{self.pt_name}{i_ele}'] *= smear
            self.mc.loc[idx, self.mll_name] *= np.sqrt(smear)
    
    def recast_pt_bins(self, prefix='cat'):
        """when doing a fit that contains pt bining with the option use_r_pt, one has to recast the relative pt in real pt value (in GeV)

        Args:
            prefix (str, optional): prefix used for naming the categorisation. Defaults to 'cat'.
        """
        if not self.has_pt:
            return 

        prefix_ref = self.cfg['fitter'].get('name_cat', 'cat')

        pt_bins = []
        for idf, df in enumerate([self.dt, self.mc]):
            df_cat_pt = pd.concat( [df[[f'{prefix_ref}_r_pt{ilep}', f'{self.pt_name}{ilep}' , f'{prefix_ref}{ilep}']]\
                .rename(columns={f'{prefix_ref}_r_pt{ilep}': f'{prefix_ref}_r_pt', 
                                 f'{self.pt_name}{ilep}': self.pt_name, 
                                 f'{prefix_ref}{ilep}': prefix_ref}) for ilep in [1, 2]] )
            pt_mean = df_cat_pt.query('cat >= 0').groupby(f'{prefix_ref}_r_pt')[self.pt_name].mean().to_numpy()
            pt_bins_def = self.categories_def[self.pt_name]
            pt_bins = np.concatenate([[pt_bins_def[0]], (pt_mean[:-1]+pt_mean[1:])*0.5, [pt_bins_def[-1]]])
            categories = {key: pt_bins if key == self.pt_name else np.array(values) for key, values in self.categories_def.items()}
            if idf == 0:
                self.categories_dt = categories.copy()
            else:
                self.categories_mc = categories.copy()
            self.lepton_reg = categorize(df, categories, prefix=prefix, cut=self.cut)
            if idf == 0:
                self.pt_mean = pt_mean

    def dump_json(self, outfile: Union[Path, str]=None):
        """Dump the resulst to a json file

        Args:
            outfile (Union[Path, str], optional): output file name. Defaults to None.
        """
        if outfile is None:
            return
        categories = self.categories_dt if self.has_pt else self.categories
        if self.double_gaussian:
            def reshape(param):
                if param.shape[0] == 1:
                    return np.ones((self.fitter.n_par,), dtype=np.float64)*param
                else:
                    return param
            parameters_to_json({"categories": categories, "resp": self.resp, "reso": self.reso, "reso2": reshape(self.reso2), "mu": reshape(self.mu), "frac": reshape(self.frac),
                                "eresp": self.eresp, "ereso": self.ereso, "ereso2": reshape(self.ereso2), "emu": reshape(self.emu), "efrac": reshape(self.efrac),
                                "eresp_mc": self.eresp_mc, "ereso_mc": self.ereso_mc, "ereso2_mc": reshape(self.ereso2_mc), "emu_mc": reshape(self.emu_mc), "efrac_mc": reshape(self.efrac_mc), "pt_mean": self.pt_mean}, outfile)
        else:
            parameters_to_json({"categories": categories, "resp": self.resp, "reso": self.reso,
                                "eresp": self.eresp, "ereso": self.ereso,
                                "eresp_mc": self.eresp_mc, "ereso_mc": self.ereso_mc, "pt_mean": self.pt_mean}, outfile)


def compute_sas(dt, mc, cfg, categories=None) -> IJazZSAS:
    """Wrapper to compute the scale and smearing parameters

    Args:
        dt (pd.DataFrame): input dataframe for data
        mc (pd.DataFrame): input dataframe for mc
        cfg (Union[str, Path]): config file to control the sas fit
        categories (dict, optional): categories to do the fit (can be specified in config). Defaults to None.

    Returns:
        IJazZSAS: return the ScaleAndSmearing fitter
    """
    sas = IJazZSAS(dt, mc, config=cfg, categories=categories)
    sas.fit()
    sas.calc_err_stat()
    sas.calc_err_mc()
    sas.dump_json(cfg['sas'].get('dump_json', None))
    # if cfg['sas'].get('correct_data', False):
    #     sas.recast_pt_bins()
    #     sas.correct_data(sas.resp)
    # if cfg['sas'].get('correct_mc', False):
    #     sas.correct_mc(sas.reso)
    return sas


class IJazZEnergyCorrector:
    def __init__(self, dt: pd.DataFrame, mc: pd.DataFrame, json_file: Union[str, Path, Dict], mll_name, pt_name) -> None:
        if not isinstance(json_file, Dict):
            with open(json_file) as f_json:
                json_file = json.load(f_json)

        self.categories = json_file['categories']
        self.resp = np.array(json_file['resp'], dtype=np.float32).flatten()
        self.reso = np.array(json_file['reso'], dtype=np.float32).flatten()
        self.eresp = np.array(json_file['eresp'], dtype=np.float32).flatten()
        self.ereso = np.array(json_file['ereso'], dtype=np.float32).flatten()

        self.mll_name = mll_name
        self.pt_name = pt_name
        self.prefix = "LepCatCorr"
        for df in [dt, mc]:
            self.lepton_cat = categorize(df, self.categories, prefix=self.prefix)
        self.mc = mc
        self.dt = dt

    def reset_data(self):
        self.dt[self.mll_name] = self.dt[f'{self.mll_name}_raw']

    def reset_mc(self):
        self.mc[self.mll_name] = self.mc[f'{self.mll_name}_raw']

    def correct_data(self):
        self.dt[f'{self.mll_name}_raw'] = self.dt[self.mll_name]
        for i_ele in [1, 2]:
            self.dt[f'pt_raw{i_ele}'] = self.dt[f'{self.pt_name}{i_ele}']
            idx = self.dt[f'{self.prefix}{i_ele}'] >= 0
            scale = self.resp[self.dt.loc[idx, f'{self.prefix}{i_ele}']]
            self.dt.loc[idx, f'{self.pt_name}{i_ele}'] /= scale
            self.dt.loc[idx, self.mll_name] /= np.sqrt(scale)
    
    def correct_mc(self, do_syst=False):
        self.mc[f'{self.mll_name}_raw'] = self.mc[self.mll_name]
        for i_ele in [1, 2]:
            self.mc[f'pt_raw{i_ele}'] = self.mc[f'{self.pt_name}{i_ele}']
            idx = self.mc[f'{self.prefix}{i_ele}'] >= 0
            smear = np.random.normal(1, self.reso[self.mc.loc[idx, f'{self.prefix}{i_ele}']]).astype(np.float32)
            self.mc.loc[idx, f'{self.pt_name}{i_ele}'] *= smear
            self.mc.loc[idx, self.mll_name] *= np.sqrt(smear)

        if do_syst:
            self.mc[f'{self.mll_name}_scaleUp'] = self.mc[self.mll_name]
            self.mc[f'{self.mll_name}_scaleDo'] = self.mc[self.mll_name]
            for i_ele in [1, 2]:
                idx = self.mc[f'{self.prefix}{i_ele}'] >= 0
                eresp = self.eresp[self.mc.loc[idx, f'{self.prefix}{i_ele}']]
                self.mc.loc[idx, f'{self.mll_name}_scaleUp'] /= np.sqrt(1. + eresp)
                self.mc.loc[idx, f'{self.mll_name}_scaleDo'] /= np.sqrt(1. - eresp)

            self.mc[f'{self.mll_name}_smearUp'] = self.mc[f'{self.mll_name}_raw']
            self.mc[f'{self.mll_name}_smearDo'] = self.mc[f'{self.mll_name}_raw']
            for i_ele in [1, 2]:
                idx = self.mc[f'{self.prefix}{i_ele}'] >= 0
                reso = self.reso[self.mc.loc[idx, f'{self.prefix}{i_ele}']]
                ereso = self.ereso[self.mc.loc[idx, f'{self.prefix}{i_ele}']]
                smear_up = np.random.normal(1, (reso+ereso)[self.mc.loc[idx, f'{self.prefix}{i_ele}']]).astype(np.float32)
                smear_do = np.random.normal(1, (reso-ereso)[self.mc.loc[idx, f'{self.prefix}{i_ele}']]).astype(np.float32)

                self.mc.loc[idx, f'{self.mll_name}_smearUp'] *= np.sqrt(smear_up)
                self.mc.loc[idx, f'{self.mll_name}_smearDo'] *= np.sqrt(smear_do)
