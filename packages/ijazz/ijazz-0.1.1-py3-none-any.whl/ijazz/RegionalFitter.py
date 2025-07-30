import numpy as np
import pandas as pd
import tensorflow as tf
import matplotlib.pyplot as plt
from ijazz.dtypes import floatzz, uintzz
from ijazz.alpha_tensors import alpha_3d, alpha_3d_2g
import scipy.optimize as scipyfitter
from tqdm import tqdm
import tensorflow.experimental.numpy as tnp
tnp.experimental_enable_numpy_behavior()
import copy
import fast_histogram as fh



class RegionalFitter:
    def __init__(self, dt: pd.DataFrame, mc:pd.DataFrame, n_par:int=-1,
                 name_cat='cat', name_mll='mee', name_weights: str=None,
                 min_nevt_region_dt=10,  min_nevt_region_mc=100,
                 win_z_dt=(70, 110),
                 win_z_mc=(50, 130),
                 bin_width_dt='Q',
                 bin_width_mc=0.1,
                 double_gaussian=False,
                 single_parameters=[],
                 error_parameters=['resp', 'reso'],
                 fast_hist=False):
        """The RegionalFitter performs the scale and smearing fit using tensorflow technology.

        Args:
            dt (pd.DataFrame): dataframe containing the data (index must be unique)
            mc (pd.DataFrame): dataframe containing the data (index must be unique)
            n_par (int): number of parameters (auto-detection: if no events some parameters might be missed). Default to -1 (auto-detection)
            name_cat (str, optional): name of the categorisation var for each ele. Defaults to 'cat'.
            name_mll (str, optional): name of the dilepton mass. Defaults to 'mee'.
            name_weights (str, optional): name of the column containing the MC weights. Defaults to None.
            min_nevt_region_dt (int, optional): minimum number of data events per category. Defaults to 10.
            min_nevt_region_mc (int, optional): minimum number of mc events per category (this matters). Defaults to 100.
            win_z_dt (tuple, optional): mass range of the dilepton mass to fit. Defaults to (50, 130).
            win_z_mc (tuple, optional): larger mass range to consider MC events. Defaults to (70, 110).
            bin_width_dt (str, optional): size of the bin width to be used in the dilepton mass (can be quantile). Defaults to 'Q'.
            bin_width_mc (float, optional): size of the bin to bin the original mc distribution (should be small). Defaults to 0.1.
            double_gaussian (bool, optional): use a double gaussian for the smearing. Defaults to False.
            single_parameters (list, optional): list of parameters that are not regional. Defaults to [].
            error_parameters (list, optional): list of parameters to be used in the error computation. Defaults to ['resp', 'reso'].
            fast_hist (bool, optional): use the fast histogram package. Defaults to False.
        """

        if not (dt.index.is_unique and mc.index.is_unique):
            raise Exception('RegionalFitter requies input dataframe to have an index with unique values')

        self.bin_width_dt = bin_width_dt
        self.name_cat = name_cat
        self.name_mll = name_mll
        self.win_z_dt = win_z_dt

        # constrain the mass to be in the window
        dt = dt[(dt[name_mll]>=win_z_dt[0]) & (dt[name_mll]<=win_z_dt[1]) & (dt[f'{name_cat}1'] >=0) & (dt[f'{name_cat}2'] >=0)]
        mc = mc[(mc[name_mll]>=win_z_mc[0]) & (mc[name_mll]<=win_z_mc[1]) & (mc[f'{name_cat}1'] >=0) & (mc[f'{name_cat}2'] >=0)]

        # error related parameters
        self.idx_pars = None
        self.eresp = None
        self.ereso = None
        self.corr = None
        self.err = None
        self.cov = None
        self.hess = None

        self.double_gaussian = double_gaussian
        self.single_parameters = single_parameters
        self.error_parameters = error_parameters

        self.n_par = n_par
        if n_par <= 0:
            # extract the parameters numbering scheme (concatenate in case the 2 electrons do not share the same categories)
            pars_dt = np.unique(np.concatenate([dt[f'{name_cat}1'].unique(), dt[f'{name_cat}2'].unique()])) 
            pars_mc = np.unique(np.concatenate([mc[f'{name_cat}1'].unique(), mc[f'{name_cat}2'].unique()]))
            self.n_par = np.intersect1d(pars_dt, pars_mc).max() + 1

        # -- something needed to see if the intersection is smaller than each parameter lists
        # - create the resp and reso variables to be fitted
        self.resp = tf.Variable(initial_value=np.random.normal(1.00, 0.020, self.n_par),
                                name='resp', trainable=True, dtype=floatzz)
        self.reso = tf.Variable(initial_value=np.random.normal(0.01, 0.001, self.n_par),
                                name='reso', trainable=True, dtype=floatzz)
        if double_gaussian:
            # Constraint to ensure values remain between 0.8 and 1
            constraint = lambda z: tf.clip_by_value(z, 0.8, 1)
            constraint_reso = lambda z: tf.clip_by_value(z, 0.0, 0.08)

            self.reso2 = tf.Variable(initial_value=np.random.normal(0.02, 0.001, 1 if 'reso2' in single_parameters else self.n_par),
                                    name='reso2', trainable=True, dtype=floatzz, constraint=constraint_reso)
            self.mu = tf.Variable(initial_value=np.random.normal(0.98, 0.020, 1 if 'mu' in single_parameters else self.n_par),
                                    name='mu', trainable=True, dtype=floatzz, constraint=constraint)
            self.frac = tf.Variable(initial_value=np.random.normal(0.98, 0.01, 1 if 'frac' in single_parameters else self.n_par),
                                    name='frac', trainable=True, dtype=floatzz, constraint=constraint)
            
            # -- variables used in the gradient
            self.trainable_variables = [self.resp, self.reso, self.reso2] + ([self.mu] if self.mu.trainable else []) + ([self.frac] if self.frac.trainable else [])
        
        else:
            self.trainable_variables = [self.resp, self.reso]

        # -- set of variables to be used in the error computation
        self.error_variables = [var for var in self.trainable_variables if var.name[:-2] in error_parameters]


        self.eresp = np.ones(self.resp.shape[0]) * np.nan
        self.ereso = np.ones(self.reso.shape[0]) * np.nan
        self.eresp_mc = np.ones(self.resp.shape[0]) * np.nan
        self.ereso_mc = np.ones(self.reso.shape[0]) * np.nan

        if double_gaussian:
            self.ereso2 = np.ones(self.reso2.shape[0]) * np.nan
            self.emu = np.ones(self.mu.shape[0]) * np.nan
            self.efrac = np.ones(self.frac.shape[0]) * np.nan
            self.ereso2_mc = np.ones(self.reso2.shape[0]) * np.nan
            self.emu_mc = np.ones(self.mu.shape[0]) * np.nan
            self.efrac_mc = np.ones(self.frac.shape[0]) * np.nan

        # -- regions numbering
        self.regions = np.arange(self.n_par ** 2).reshape(self.n_par, self.n_par)

        # -- re-order min and max to create the region (correction and smearing are abelian)
        keep_reg = [pd.DataFrame()] * 2  # - regions to be kept
        self.idt = 0
        self.imc = 1
        counts_per_reg = [pd.DataFrame()] * 2

        df_region = [None] * 2
        min_evt = [min_nevt_region_dt, min_nevt_region_mc] 

        for idf, df in enumerate([dt, mc]):
            df_region[idf] = pd.DataFrame({'imin': df[[f'{name_cat}1', f'{name_cat}2']].min(axis=1), 
                                           'imax': df[[f'{name_cat}1', f'{name_cat}2']].max(axis=1)},
                                            index = df.index)
            i_reg_max = df_region[idf] ['imax'].max()
            df_region[idf]['ireg'] = df_region[idf] ['imin']*i_reg_max + df_region[idf]['imax']
            counts_per_reg[idf] = df_region[idf]['ireg'].value_counts().sort_index()
            keep_reg[idf] = counts_per_reg[idf][counts_per_reg[idf] > min_evt[idf]]
        keep_region = keep_reg[0].index.intersection(keep_reg[1].index)

        # -- regional indexing
        self.regional_electron_indices = df_region[0].groupby('ireg').mean().astype(np.int32)\
            .loc[keep_region].rename(columns={'imin': 0, 'imax': 1})
        self.regional_electron_indices['n_dt'] = counts_per_reg[self.idt].loc[keep_region]
        self.regional_electron_indices['n_mc'] = counts_per_reg[self.imc].loc[keep_region]

        self.n_reg = len(keep_region)
        print(f"Number of regions saved : {self.n_reg}, max : {self.n_par*(self.n_par+1)/2:.0f} ")


        # -- create histograms
        # - create the MC binning with a constant width (user input)
        n_bins_mc = int(np.floor((win_z_mc[1]-win_z_mc[0])/bin_width_mc))
        self.bins_mc = tf.cast(tf.linspace(*win_z_mc, n_bins_mc+1, name='bins_mc'), floatzz)
        self.bins_mean_mc = []
        self.bins_mid_mc = np.array([0.5 * (self.bins_mc[1:] + self.bins_mc[:-1])] * self.n_reg)
        
        self.bins_dt = []
        self.bins_width = []

        hs_dt = []
        hs_mc = []
        hs_mc_w2 = []
        hs_mc_bin_dt = []
        
        n_bin_dt_max = int((win_z_dt[1] - win_z_dt[0])/0.5)

        for ireg in tqdm(keep_region, desc="Create regions"):

            dt_reg = dt.loc[df_region[0]['ireg'] == ireg, :]
            mc_reg = mc.loc[df_region[1]['ireg'] == ireg, :]

            mc_mee = mc_reg[name_mll]
            dt_mee = dt_reg[name_mll]

            # - create mc hist and save the sum_i wi^2 when there are weights
            if name_weights:
                mc_weights = mc_reg[name_weights]
                if fast_hist:
                    hs_mc.append(fh.histogram1d(mc_mee, range=win_z_mc, bins=n_bins_mc, weights=mc_weights))
                    # print(len(hs_mc[-1]))   
                    hs_mc_w2.append(fh.histogram1d(mc_mee, range=win_z_mc, bins=n_bins_mc, weights=mc_weights**2))
                else:
                    hs_mc.append(np.histogram(mc_mee, bins=self.bins_mc, weights=mc_weights)[0])
                    hs_mc_w2.append(np.histogram(mc_mee, bins=self.bins_mc, weights=mc_weights**2)[0])
            else:
                mc_weights = None
                if fast_hist:
                    hs_mc.append(fh.histogram1d(mc_mee, range=win_z_mc, bins=n_bins_mc))
                else:
                    hs_mc.append(np.histogram(mc_mee, bins=self.bins_mc, weights=mc_weights)[0])
                hs_mc_w2.append(hs_mc[-1])
            # hs_mc[-1] = np.abs(hs_mc[-1])  # when prob < 0, use abs(prob) to avoid weird behaviour
            hs_mc[-1][hs_mc[-1]<0] = 0  # when prob < 0, put bins to 0 to avoid weird behaviour
            
            # - create Data hist
            # create data binning with different possibility
            if bin_width_dt == "Q": # quantile binning
                # -- the quantile bining should be related to the MC, not to data (just move the mean to data)
                dm = dt_mee.mean() - mc_mee.mean()
                mc_mee_q = mc_reg.query(f"{win_z_dt[0]} < ({name_mll} + {dm}) < {win_z_dt[1]}")[name_mll]
                n_bins = max(5, min(n_bin_dt_max, int(np.power(len(mc_mee_q), 1/3)))) 
                bins = np.quantile(mc_mee_q + dm, np.linspace(0, 1, n_bins+1)) 
                # print(bins)
                # bins[0], bins[-1] = win_z_dt
            
            elif bin_width_dt: # constant bin width
                n_bins = int(np.floor((win_z_dt[1]-win_z_dt[0])/bin_width_dt)+1)
                bins = tf.cast(tf.linspace(*win_z_dt, n_bins, name=f'bins_dt_{ireg}'), floatzz)
            else: # data bining tuned depending on event count using Freedman–Diaconis rule
                irq = np.subtract(*np.percentile(dt_mee, [75, 25]))
                bin_width = max(2 * irq / np.power(len(mc_mee),1/3),0.5)
                n_bins = int(np.floor((win_z_dt[1]-win_z_dt[0])/bin_width)+1)
                bin_width = (win_z_dt[1]-win_z_dt[0])/(n_bins-1)
                bins = tf.cast(tf.linspace(*win_z_dt, n_bins, name=f'bins_dt_{ireg}'), floatzz)
                
            hs_dt.append(np.histogram(dt_mee, bins=bins)[0])
            hs_mc_bin_dt.append(np.histogram(mc_mee, bins=bins, weights=mc_weights)[0])
            self.bins_dt.append(bins)
        
        try:
            pad_sequences = tf.keras.utils.pad_sequences
        except AttributeError:
            pad_sequences = tf.keras.preprocessing.sequence.pad_sequences

        # hs = [np.array(pad_sequences(hs_dt, padding='post', dtype=np.float64)).T, np.array(tf.cast(hs_mc, dtype=floatzz)).T]
        # # padding the dt hist with the max of the window, this ensure a_ij=0 for those elements 
        # bins = [pad_sequences(self.bins_dt, padding='post',value=win_z_dt[1],dtype=float), np.array([self.bins_mc]*len(self.bins_dt))]

        # mask to avoid pi = 0 in log: FC use tf boolean mask (avoid tricks)
        # this also allows to mask pis < 0 (for instance with < 0 weights)
        pi_mask = pad_sequences(hs_dt, value=1e14, padding='post', dtype=float)
        pi_mask[pi_mask<1e13] = True
        pi_mask[pi_mask>1e13] = False
        self.pi_mask = pi_mask.astype(bool).T

        # -- also remove potentially negative pis when the MC integral < 0 (with negative weights)
        n_mc = np.array([h_mc.sum() for h_mc in hs_mc])
        self.pi_mask[:, n_mc <= 0] = False

        # -- renaming of the variables to make them more clear 
        self.n_ic = tf.constant(np.array(pad_sequences(hs_dt, padding='post', dtype=np.float64)).T, dtype=floatzz)  # - histo data
        self.m_jc = tf.constant(np.array(tf.cast(hs_mc, dtype=floatzz)).T, dtype=floatzz)  # - hist MC
        self.m_ic = tf.constant(np.array(pad_sequences(hs_mc_bin_dt, padding='post',dtype=float)).T)  # - hist MC width data bining
        self.b_ic = tf.constant(pad_sequences(self.bins_dt, padding='post',value=win_z_dt[1],dtype=float).T, dtype=floatzz)   # - bining dt
        self.b_jc = tf.constant(np.array([self.bins_mc]*len(self.bins_dt)).T, dtype=floatzz)   # - bining mc
        self.s2_m_jc = tf.constant(np.array(tf.cast(hs_mc_w2, floatzz)).T) # - error on the h mc
        self.pi_mask = tf.constant(self.pi_mask, dtype=tf.bool) # - mask 

        # -- re-index the region so it corresponds to the index of tensors
        self.regional_electron_indices = self.regional_electron_indices.reset_index(drop=True)

    def rll_sll(self, cats=slice(None)):
        """Compute the dilepton rll and sll for each gaussian. In the case of double gaussian, we end up with 4 gaussians.

        Args:
            cats (slice, optional): categories where to compute the rll and sll. Defaults to slice(None).

        Returns:
            tuple: tuple of rll and sll for each gaussian
        """
        iele = self.regional_electron_indices
        r_l = [tnp.asarray(self.resp)[iele[ie].to_numpy()] for ie in [0, 1]]
        s_l = [tnp.asarray(self.reso)[iele[ie].to_numpy()] for ie in [0, 1]]
        r_ll = tf.sqrt(r_l[0][cats] * r_l[1][cats])
        s_ll = tf.maximum(0.5 * tf.sqrt(s_l[0][cats] ** 2 + s_l[1][cats] ** 2), 1e-3)

        if self.double_gaussian:
            s2_l = [tnp.asarray(self.reso2)[iele[ie].to_numpy()] for ie in [0, 1]]
            if 'mu' in self.single_parameters:
                m_l = [tnp.asarray(self.mu) for ie in [0, 1]]
            else:
                m_l = [tnp.asarray(self.mu)[iele[ie].to_numpy()] for ie in [0, 1]]
            if 'frac' in self.single_parameters:
                f_l = [tnp.asarray(self.frac) for ie in [0, 1]]
            else:
                f_l = [tnp.asarray(self.frac)[iele[ie].to_numpy()] for ie in [0, 1]]
            
            s_12_21 = tf.maximum(0.5 * tf.sqrt(s2_l[0][cats] ** 2 + s_l[1][cats] ** 2), 1e-3)
            s_11_22 = tf.maximum(0.5 * tf.sqrt(s_l[0][cats] ** 2 + s2_l[1][cats] ** 2), 1e-3)
            s_12_22 = tf.maximum(0.5 * tf.sqrt(s2_l[0][cats] ** 2 + s2_l[1][cats] ** 2), 1e-3)

            def idx(param_name):
                return 0 if param_name in self.single_parameters else cats

            return (f_l[0][idx('frac')]*f_l[1][idx('frac')], r_ll, s_ll), \
                    ((1-f_l[0][idx('frac')])*f_l[1][idx('frac')], r_ll*tf.sqrt(m_l[0][idx('mu')]), s_12_21), \
                    (f_l[0][idx('frac')]*(1-f_l[1][idx('frac')]), r_ll*tf.sqrt(m_l[1][idx('mu')]), s_11_22), \
                    ((1-f_l[0][idx('frac')])*(1-f_l[1][idx('frac')]), r_ll*tf.sqrt(m_l[0][idx('mu')]*m_l[1][idx('mu')]), s_12_22)
        else:
            return (1., r_ll, s_ll), (0., r_ll, s_ll), (0., r_ll, s_ll), (0., r_ll, s_ll)
        
    def pi(self, cats: slice=slice(None), rll_sll: tuple=None):
        """Compute the probabilities of being in the bin i (after smearing) in each categories

        Args:
            cats (slice, optional): categories where to compute the pis. Defaults to slice(None).
            rll_sll (tuple, optional): tuple with the rll and sll for each gaussian. Defaults to None.

        Returns:
            np.array: 2D array of probabilities per category
        """
        if rll_sll is None:
            rll_sll1, rll_sll2, rll_sll3, rll_sll4 = self.rll_sll(cats)
        else :
            rll_sll1, rll_sll2, rll_sll3, rll_sll4 = rll_sll
        a_ijc = alpha_3d_2g(self.b_ic[:, cats], self.b_jc[:, cats], rll_sll1, rll_sll2, rll_sll3, rll_sll4)
        p_ic = tf.linalg.diag_part(tf.tensordot(a_ijc, self.m_jc[:, cats], axes=[[1], [0]]))
        p_c = tf.reduce_sum(p_ic, axis=0)
        return p_ic / p_c

    def nll_cat(self, cats:slice=slice(None)):
        """Compute the negative log likelihood (multinomial law)

        Args:
            cats (slice, optional): categories where to compute the nll. Defaults to slice(None).

        Returns:
            tf.float64: nll
        """
        p_ic = tf.boolean_mask(self.pi(cats=cats), self.pi_mask[:, cats])
        n_ic = tf.boolean_mask(self.n_ic[:, cats], self.pi_mask[:, cats])
        return -tf.reduce_sum(n_ic * tf.math.log(p_ic))

    # -- next line are just to confirm tensorflow computation for dnll
    # def nll2_cat(self, cats=slice(None)):
    #     rll, sll = self.rll_sll(cats)
    #     a_ijc = alpha_3d(self.bins[0][cats], self.bins[1][cats], rll, sll)
    #     n_ic = self.hs[self.idt][:, cats]
    #     m_jc = self.hs[self.imc][:, cats]
    #     p_ic = tf.linalg.diag_part(tf.tensordot(a_ijc, m_jc, axes=[[1], [0]]))
    #     n_c = tf.reduce_sum(self.hs[self.idt][:, cats], axis=0)
    #     p_c = tf.reduce_sum(p_ic, axis=0)
    #     mask = self.pi_mask[:, cats]
    #     return -(tf.reduce_sum(tf.boolean_mask(n_ic, mask) * tf.math.log(tf.boolean_mask(p_ic, mask))) -
    #              tf.reduce_sum(n_c * tf.math.log(p_c)))

    @tf.function
    def dnll_dmjc(self, cats):
        """Compute the gradient of the negative log likelihood with respect to the MC histogram.

        Args:
            cats (slice): categories where to compute the gradient.

        Returns:
            tf.float64: gradient of the nll with respect to the MC histogram.
        """
        rll_sll1, rll_sll2, rll_sll3, rll_sll4 = self.rll_sll(cats)
        a_ijc = alpha_3d_2g(self.b_ic[:, cats], self.b_jc[:, cats], rll_sll1, rll_sll2, rll_sll3, rll_sll4)
        p_ic = tf.linalg.diag_part(tf.tensordot(a_ijc, self.m_jc[:, cats], axes=[[1], [0]]))
        n_c = tf.reduce_sum(self.n_ic[:, cats], axis=0)
        p_c = tf.reduce_sum(p_ic, axis=0)
        mask = self.pi_mask[:, cats]
        return -(tf.linalg.diag_part(tf.tensordot(a_ijc, self.n_ic[:, cats]/(p_ic + ~mask), axes=[[0], [0]])) - 
                 n_c/p_c * tf.reduce_sum(a_ijc, axis=0))

    def nll_batch(self, **kwargs):
        return self.batcher(self.nll_cat, **kwargs)

    def batcher(self, afunc, batch_size=-1, shuffle=False, cats=slice(None)):
        """Compute the likelihood in batch and then sum-up the result.

        Args:
            batch_size (int): size of the batch.
            shuffle (bool): shuffle the events before (this is useless in this case but kept for timing tests).

        Returns:
            tf.float64: the summed likelihood.
        """
        nll = tf.cast(0., floatzz)
        if batch_size > 0:
            # shuffle events and split in batches
            batches = np.split(self.regional_electron_indices.iloc[cats].index if not shuffle else
                               self.regional_electron_indices.iloc[cats].sample(frac=1).index,
                               np.arange(0, len(self.regional_electron_indices.iloc[cats]), batch_size)[1:])
        else :
            batches = [cats]

        for batch in batches:
            nll += afunc(batch.sort_values() if batch_size > 0 else batch)
        return nll

    def train_epoch(self, optimizer, batch_size=-1, batch_training=True, cats=slice(None)):
        """Train a single epoch for the model.

        Args:
            optimizer (tf.keras.optimizers.Optimizer): The Keras optimizer used to apply gradients.
            batch_size (int, optional): The size of the batch for negative log-likelihood (NLL) computation. 
                Defaults to -1, which means no batching.
            batch_training (bool, optional): If True, updates parameters at each batch for faster training. 
                Defaults to True.
            cats (slice, optional): A slice object to select specific categories of data. Defaults to slice(None).
            
        Returns:
            tf.Tensor: The total negative log-likelihood (NLL) for the epoch.
        """
        if batch_size > 0:
            # shuffle events and split in batches
            batches = np.split(self.regional_electron_indices.iloc[cats].sample(frac=1).index,
                                np.arange(0, len(self.regional_electron_indices.iloc[cats]), batch_size)[1:])
        
        if batch_training:
            nll_epoch = tf.cast(0., floatzz)
            for batch in batches:
                with tf.GradientTape(persistent=False) as gtape:
                    nll = self.nll_cat(batch.sort_values() if batch_size > 0 else batch)
                gradients = gtape.gradient(nll, self.trainable_variables)
                optimizer.apply_gradients(zip(gradients, self.trainable_variables))
                nll_epoch += nll
        else:
            with tf.GradientTape(persistent=False) as gtape:
                nll_epoch = self.nll_cat(cats)                    
            gradients = gtape.gradient(nll_epoch, self.trainable_variables)
            optimizer.apply_gradients(zip(gradients, self.trainable_variables))

        return nll_epoch

    def minimize(self, optimizer, dnll_tol=0.1, max_epochs=1000, minimizer='Adam',
                 init_rand=False, nepoch_print=10,
                 init_resp=None, init_reso=None,
                 device='CPU', batch_size=-1, batch_training=True, cats=slice(None)):
        """
        Minimizes the negative log-likelihood using a TensorFlow optimizer.

        Args:
            optimizer (tf.keras.optimizers.Optimizer): TensorFlow optimizer to apply gradients.
            dnll_tol (float): Tolerance for the change in -2logL to determine convergence.
            max_epochs (int): Maximum number of epochs for optimization.
            minimizer (str): Optimization method, either 'Adam' or a SciPy minimizer (e.g., 'TNC').
            init_rand (bool): If True, initializes variables randomly.
            nepoch_print (int): Frequency of printing progress (every `nepoch_print` epochs).
            device (str): Device to use for computation ('CPU' or 'GPU').
            batch_size (int): Size of the batch for likelihood computation.
            batch_training (bool): If True, updates parameters at each batch for faster training.

        Returns:
            List[float]: List of negative log-likelihood values for each epoch.
        """

        if minimizer == 'Adam':
            nlls = self.minimize_tf(optimizer, dnll_tol=dnll_tol, max_epochs=max_epochs, 
                                    init_rand=init_rand, init_resp=init_resp, init_reso=init_reso,
                                    nepoch_print=nepoch_print, device=device, 
                                    batch_size=batch_size, batch_training=batch_training, cats=cats)
        else:
            nlls = self.minimize_sp(dnll_tol=dnll_tol, minimizer=minimizer, device=device,
                                    init_rand=init_rand, init_resp=init_resp, init_reso=init_reso,
                                    batch_size=batch_size, cats=cats) 

        return nlls

    def minimize_tf(self, optimizer, dnll_tol=0.1, max_epochs=1000,
                 init_rand=False, nepoch_print=10,
                 init_resp=None, init_reso=None,
                 device='CPU', batch_size=-1, batch_training=True, cats=slice(None)):
        """
        Minimizes the negative log-likelihood using a TensorFlow optimizer.

        Args:
            optimizer (tf.keras.optimizers.Optimizer): TensorFlow optimizer to apply gradients.
            dnll_tol (float): Tolerance for the change in -2logL to determine convergence.
            max_epochs (int): Maximum number of epochs for optimization.
            init_rand (bool): If True, initializes variables randomly.
            nepoch_print (int): Frequency of printing progress (every `nepoch_print` epochs).
            device (str): Device to use for computation ('CPU' or 'GPU').
            batch_size (int): Size of the batch for likelihood computation.
            batch_training (bool): If True, updates parameters at each batch for faster training.
            cats (slice): A slice object to select specific categories of data.

        Returns:
            np.ndarray: Array of negative log-likelihood values for each epoch.
        """

        if init_rand:
            self.resp.assign(np.random.normal(1.00, 0.02, self.n_par))
            self.reso.assign(np.random.normal(0.015, 0.002, self.n_par))
        elif init_resp is not None and init_reso is not None:
            self.resp.assign(init_resp)
            self.reso.assign(init_reso)
        else:
            self.resp.assign(tf.ones(self.n_par, dtype=floatzz) * 1.00)
            self.reso.assign(tf.ones(self.n_par, dtype=floatzz) * 0.02)
            if self.double_gaussian:
                self.reso2.assign(tf.ones(1 if 'reso2' in self.single_parameters else self.n_par, dtype=floatzz) * 0.04)
                self.mu.assign(tf.ones(1 if 'mu' in self.single_parameters else self.n_par, dtype=floatzz) * 0.95)
                self.frac.assign(tf.ones(1 if 'frac' in self.single_parameters else self.n_par, dtype=floatzz) * 0.95)

        nlls = [1e10]
        n_epoch = 0

        def stop_condition():
            dnll = 2 * dnll_tol if n_epoch < 2 else nlls[-1] - nlls[-2]
            return (abs(dnll) < dnll_tol) and (n_epoch > 5) and (abs(nlls[-1] - nlls[-4]) < dnll_tol) or np.isnan(nlls[-1])

        with tf.device('/device:' + device + ':0'):
            while not stop_condition() and n_epoch < max_epochs:
                if n_epoch >= 2 and abs(nlls[-1] - nlls[-2]) < 1000:
                    # -- switch batch training when close to convergence
                    batch_training = False
                nlls.append(self.train_epoch(optimizer, batch_size=batch_size, batch_training=batch_training, cats=cats))
                if nepoch_print > 0 and n_epoch % nepoch_print == 0:
                    print(f'epoch: {n_epoch:>5d}, nll = {nlls[-1]:.2f}')
                    # if self.double_gaussian:
                    #     print(self.reso2.numpy(), self.mu.numpy(), self.frac.numpy())
                n_epoch += 1
            if n_epoch == max_epochs:
                print('WARNING! Max epochs reached, the minimization may not have converged')
        print(f' --> FN (TensorFlow minimizer): {nlls[-1]:.4f}')
        return np.array(nlls[1:])

    def minimize_sp(self, dnll_tol=0.1, minimizer='TNC',
                 init_rand=False, 
                 init_resp=None, init_reso=None,
                 device='CPU', batch_size=-1, cats=slice(None)):
        """
        Minimizes the negative log-likelihood using a SciPy optimizer.

        Args:
            dnll_tol (float): Tolerance for the change in -2logL to determine convergence.
            minimizer (str): SciPy minimizer method (e.g., 'TNC', 'L-BFGS-B').
            init_rand (bool): If True, initializes variables randomly.
            init_resp (np.ndarray, optional): Initial values for the response parameters. Defaults to None.
            init_reso (np.ndarray, optional): Initial values for the resolution parameters. Defaults to None.
            device (str): Device to use for computation ('CPU' or 'GPU').
            batch_size (int): Size of the batch for likelihood computation.
            cats (slice): A slice object to select specific categories of data.

        Returns:
            np.ndarray: Array containing the final negative log-likelihood value.
        """
        if init_rand:
            self.resp.assign(np.random.normal(1.00, 0.02, self.n_par))
            self.reso.assign(np.random.normal(0.015, 0.002, self.n_par))
        elif init_resp is not None and init_reso is not None:
            self.resp.assign(init_resp)
            self.reso.assign(init_reso)
        else:
            self.resp.assign(tf.ones(self.n_par, dtype=floatzz) * 1.00)
            self.reso.assign(tf.ones(self.n_par, dtype=floatzz) * 0.02)

        p0 = tf.concat(self.trainable_variables, axis=0)
        def get_nll(par):
            for var, value in zip(self.trainable_variables, tf.split(par, [VAR.shape[0] for VAR in self.trainable_variables])):
                var.assign(value)
            return self.nll_batch(batch_size=batch_size, cats=cats)
        
        def get_dnll(par):
            for var, value in zip(self.trainable_variables, tf.split(par, [VAR.shape[0] for VAR in self.trainable_variables])):
                var.assign(value)
            with tf.GradientTape(persistent=False) as gtape:
                nll = self.nll_batch(batch_size=batch_size, cats=cats)
            grad = gtape.gradient(nll, self.trainable_variables)
            return tf.concat([tf.convert_to_tensor(grad[i]) for i in range(len(self.trainable_variables))], axis=0)

        with tf.device('/device:' + device + ':0'):
            result = scipyfitter.minimize(get_nll, p0, jac=get_dnll, method=minimizer, options={'ftol': dnll_tol})
        fval = result.fun
        print(result)
        for var, value in zip(self.trainable_variables, tf.split(result.x, [VAR.shape[0] for VAR in self.trainable_variables])):
            var.assign(value)
        return np.array([fval])
    
    def get_index(self, e1=None, e2=None, c=None):
        """
        Get indices based on electron or pair categories.

        Args:
            e1 (list, optional): List of electron indices to match.
            e2 (list, optional): List of electron indices to match. If both `e1` and `e2` 
            are provided, pairs of indices will be matched.
            c (list[tuple], optional): List of electron index pairs to match.

        Returns:
            pd.Index: Unique indices matching the categories. Returns all indices if no categories.

        Notes:
            - If both `e1` and `e2` are provided, all combinations of pairs, including reversed, are considered.
            - Assumes `self.regional_electron_indices` is a pandas DataFrame.
        """

        if e1:
            if e2:
                pairs = [(i, j) for i in e1 for j in e2] + [(i, j) for i in e2 for j in e1]
                idx = np.unique(np.where(self.regional_electron_indices.set_index([0,1]).index.isin(pairs)))
            else :
                idx = np.unique(np.where(self.regional_electron_indices.isin(e1))[0])
        elif e2:
            idx = np.unique(np.where(self.regional_electron_indices.isin(e2))[0])
        elif c:
            idx = []
            id = self.regional_electron_indices
            for pair in c :
                idx += id.index[((id[0] == pair[0]) & (id[1] == pair[1])) | 
                                ((id[0] == pair[1]) & (id[1] == pair[0]))].to_list()
        else:
            idx = range(self.n_ic.shape[1])
        return pd.Index(idx)

    def plot_region_fits(self, cols=5, show_mc=False, n_plots=None, e1=None, e2=None, cats=None, rll_sll=None):
        """
        Plot the data and fit for each region.

        Args:
            cols (int): Number of columns in the plot.
            show_mc (bool): If True, show the Monte Carlo uncorrected.
            n_plots (int): Number of plots to show.
            e1 (list): List of electron indices to match.
            e2 (list): List of electron indices to match. If both `e1` and `e2` 
            are provided, pairs of indices will be matched.
            cats (list[tuple]): List of electron index pairs to match.
            rll_sll (tuple): Tuple with the rll and sll for each gaussian.

        Returns:
            tuple: Tuple containing the figure and axes objects.
        """       
        if n_plots and (e1 is None) and (e2 is None) and (cats is None):
            idx = pd.Index(range(min(n_plots, self.n_ic.shape[1])))
        elif isinstance(cats,slice):
            idx = self.regional_electron_indices[cats].index
        elif cats is not None :
            idx = cats
        else :
            idx = self.get_index(e1, e2)

        n_plots = len(idx)
        cols = min(cols,n_plots)
        rows = int(np.ceil(n_plots/cols))
        fig, ax = plt.subplots(nrows=rows, ncols=cols, figsize=(5*cols,5*rows), squeeze=False)
        ax = ax.flatten()

        if show_mc:
            m_ic = self.m_ic[:, idx]
            p_ic_mc = m_ic / tf.reduce_sum(m_ic, axis=0)

        p_ic = self.pi(idx,rll_sll)
        for i, id in enumerate(idx):
            corr = 1 if self.bin_width_dt != "Q" else self.b_ic[1:, id] - self.b_ic[:-1, id]
            n_ic = self.n_ic[:, id]
            xval = (self.b_ic[1:, id] + self.b_ic[:-1, id])*0.5
            xerr = (self.b_ic[1:, id] - self.b_ic[:-1, id])*0.5
            if show_mc:
                ax[i].stairs( np.array(p_ic_mc[:, id])*tf.reduce_sum(n_ic)/corr, edges=self.b_ic[:, id],label='mc')
            ax[i].errorbar(xval, n_ic / corr,yerr=tf.sqrt(n_ic)/corr,xerr=xerr,fmt='ko',label='dt')
            ax[i].stairs(p_ic[:, id] * tf.reduce_sum(n_ic)/corr,edges=self.b_ic[:, id],label='fit')
            idx_e1, idx_e2, _, _ = self.regional_electron_indices.iloc[id]

            ax[i].set_title(f"Category {id} ({idx_e1},{idx_e2})")
            ax[i].set_xlim(self.win_z_dt)
            if self.bin_width_dt == "Q":
                ax[i].set_ylabel(f"Events per GeV")
            else :
                ax[i].set_ylabel(f"Events per {self.bin_width_dt:.2f} GeV")
            ax[i].set_xlabel(r"$M_{ee}$ (GeV)")
            ax[i].legend()

        return fig, ax

    def get_hessian(self, afunc, numerical=True, **kwargs):
        """Compute the hessain of a function numerically or analytically

        Args:
            afunc (function): function to get hessian of
            numerical (bool, optional): type of computation. Defaults to True.
        
        Returns:
            np.array: hessian matrix
        """
        if numerical:
            epsilon = kwargs.pop('epsilon', 1e-4)
            p0 = [var.numpy().copy() for var in self.error_variables]
            hess_blocks = [[None for _ in range(len(self.error_variables))] for _ in range(len(self.error_variables))]
            for i, var1 in enumerate(self.error_variables):
                for j, var2 in enumerate(self.error_variables):
                    if j < i:
                        continue
                    hess = np.zeros((var1.shape[0], var2.shape[0]))
                    for ir, r in enumerate(p0[i]):
                        # print(ir)
                        p = copy.deepcopy(p0)
                        p[i][ir] = p0[i][ir] + epsilon
                        for var, value in zip(self.error_variables, p):
                            var.assign(value)
                        with tf.GradientTape(persistent=True) as gtape:
                            nll = afunc(**kwargs)
                        # print(gtape.gradient(nll, var2))
                        grad_plus = tf.convert_to_tensor(gtape.gradient(nll, var2))
                        p[i][ir] = p0[i][ir] - epsilon
                        var1.assign(p[i])
                        with tf.GradientTape(persistent=True) as gtape:
                            nll = afunc(**kwargs)
                        grad_minus = tf.convert_to_tensor(gtape.gradient(nll, var2))
                        hess[ir, :] = (grad_plus - grad_minus) / (2*epsilon)
                        # print(ir,(grad_plus - grad_minus) / (2*epsilon))
                    hess_blocks[i][j] = hess
                    
            
            
            for i in range(len(self.error_variables)):
                for j in range(len(self.error_variables)):
                    if j < i:
                        continue
                    hess_blocks[j][i] = hess_blocks[i][j].T
            hess = np.block(hess_blocks)
        else:
            with tf.GradientTape(persistent=True) as gtape1:
                with tf.GradientTape(persistent=True) as gtape2:
                    nll = afunc(**kwargs)
                grad = gtape2.gradient(nll, gtape2.watched_variables())
            hess_r = gtape1.jacobian(grad[0], gtape1.watched_variables())
            hess_s = gtape1.jacobian(grad[1], gtape1.watched_variables())
            hess = tf.concat([tf.concat(hess_r, axis=1),
                              tf.concat(hess_s, axis=1)], axis=0).numpy()
        return hess
        
    def covariance(self, numerical=True, force=False, **kwargs):
        """
        Computes and stores the Hessian, covariance, and correlation matrices.

        Args:
            numerical (bool, optional): Whether to compute the Hessian numerically. Defaults to True.
            force (bool, optional): If True, recompute all matrices even if they already exist. Defaults to False.
            **kwargs: Additional parameters for the `nll_batch` function (e.g., batch_size).

        Returns:
            None
        """
        if self.hess is None or force:
            self.hess = self.get_hessian(self.nll_batch, numerical=numerical, **kwargs)

        # - select only parameters which are actually fitted (for others hess = 0 so non-invertible matrix)
        idx_pars = np.where(np.diag(self.hess) > 1)[0]
        self.idx_pars = idx_pars
        if idx_pars.shape[0] < sum(var.shape[0] for var in self.error_variables):
            self.hess = self.hess[idx_pars][:, idx_pars]

        self.cov = np.linalg.inv(self.hess)
        self.err = np.sqrt(np.diag(self.cov))
        self.corr = self.cov / np.reshape(self.err, (-1, 1)) / np.reshape(self.err, (1, -1))
       
        offset = 0
        for var in self.error_variables:
            var_size = var.shape[0]
            is_var_par = (idx_pars >= offset) & (idx_pars < offset + var_size)
            var_err = self.err[is_var_par]
            if var.name[:-2] == 'resp':
                self.eresp[idx_pars[is_var_par] - offset] = var_err
            elif var.name[:-2] == 'reso':
                self.ereso[idx_pars[is_var_par] - offset] = var_err
            elif var.name[:-2] == 'reso2':
                self.ereso2[idx_pars[is_var_par] - offset] = var_err
            elif var.name[:-2] == 'mu':
                self.emu[idx_pars[is_var_par] - offset] = var_err
            elif var.name[:-2] == 'frac':
                self.efrac[idx_pars[is_var_par] - offset] = var_err
            offset += var_size

    def calc_err_mc(self) -> None:
        """Compute the uncertainty due to MC limited statistic

        Returns:
            None: store the error in dedicated variables in the fitter
        """

        # the computation is given by 
        # dtheta = | - Hess^-1 x d2nll/dthetadmjc | where hess is the hessian w/r to dtheta
        
        nb_j = self.m_jc.shape[0]  # - number of bins for the MC
        nb_c = self.m_jc.shape[1]  # - number of categories

        s2_jc = np.empty((nb_j*nb_c,))
        d2nll_dvarsdm = [np.empty((s2_jc.shape[0], var.shape[0])) for var in self.error_variables]

        # # -- flatten the second derivative matrix and compute by category to avoid memory destruction
        @tf.function
        def d2nll_dtheta_dmjc(icat):
            with tf.GradientTape(persistent=True) as gtape:
                dnll = tf.reshape(self.dnll_dmjc(icat), [-1])
            return [gtape.jacobian(dnll, var) for var in self.error_variables]
        
        for icat in tqdm(tf.range(nb_c), desc="Calc d2nll"):
            tf_icat = tf.constant(icat, shape=(1,))
            g_vars = d2nll_dtheta_dmjc(tf_icat)
            for i, g_var in enumerate(g_vars):
                d2nll_dvarsdm[i][icat*nb_j:(icat+1)*nb_j, :] = g_var
            s2_jc[icat*nb_j:(icat+1)*nb_j] = self.s2_m_jc[:, icat]

        dtheta2_mc_pjc = tf.tensordot(self.cov, np.concatenate(d2nll_dvarsdm, axis=1)\
            [:, self.idx_pars], axes=[1, 1])**2
        dtheta = tf.sqrt(tf.tensordot(dtheta2_mc_pjc, s2_jc, axes=[[1], [0]])).numpy()

        offset = 0
        for var in self.error_variables:
            var_size = var.shape[0]
            is_var_par = (self.idx_pars >= offset) & (self.idx_pars < offset + var_size)
            var_err = dtheta[is_var_par]
            if var.name[:-2] == 'resp':
                self.eresp_mc[self.idx_pars[is_var_par] - offset] = var_err
            elif var.name[:-2] == 'reso':
                self.ereso_mc[self.idx_pars[is_var_par] - offset] = var_err
            elif var.name[:-2] == 'reso2':
                self.ereso2_mc[self.idx_pars[is_var_par] - offset] = var_err
            elif var.name[:-2] == 'mu':
                self.emu_mc[self.idx_pars[is_var_par] - offset] = var_err
            elif var.name[:-2] == 'frac':
                self.efrac_mc[self.idx_pars[is_var_par] - offset] = var_err
            offset += var_size
