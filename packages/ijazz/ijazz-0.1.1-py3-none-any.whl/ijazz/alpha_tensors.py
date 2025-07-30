__doc__ = """This Modules computes the alpha matrix which allows to smear with a gaussion function an histogram
The input histogram is of dimension d_mc (MC reference) and the smeared 
one of dimension d_dt (smeared to the dataspace).
Author: fabrice.couderc@cea.fr"""

import tensorflow as tf
import numpy as np
from ijazz.dtypes import floatzz


def alpha_evt(d_min, d_max, bin_m, r_ll, s_ll):
    """
    Compute the probability migration from due to a Gaussian over-smearing.
    Per-event variation of the alpha matrix (dim(d_min) = dim(d_max) = dim(rll) = dim(sll)).
    Note the computation is done with a normalisation to the fitting region (win_z)

    Args:
        - d_min: minimum value of the mass point for data (we return a bined probability)
        - d_max: maximum value of the mass point for data (we return a bined probability)
        - bin_m: MC binning in Mee
        - r_ll: Gaussian mean (relative, gaussian mean will be mu x r_ll)
        - s_ll: Gaussian resolution(relative as well)
    Returns a 2D tensor (dim(bining_mc), dim(r_ll))
    dim(r_ll) should be the number of events or categories

    NB: this can be used to compute the integral of pi !
    """
    d_min = tf.cast(d_min, floatzz)
    d_max = tf.cast(d_max, floatzz)
    sqrt2 = tf.cast(tf.sqrt(2.0), floatzz)
    r_loc = tf.cast(tf.reshape(r_ll, (+1, -1)), floatzz)
    s_loc = tf.cast(tf.reshape(s_ll, (+1, -1)), floatzz)

    mee = tf.reshape(0.5 * (bin_m[1:] + bin_m[:-1]), (-1, +1))  # reshape for a 3D tensor
    a_ij = tf.math.erf((tf.reshape(d_max, (+1, -1))/r_loc - mee) / (sqrt2 * mee * s_loc)) - \
           tf.math.erf((tf.reshape(d_min, (+1, -1))/r_loc - mee) / (sqrt2 * mee * s_loc))
    return 0.5 * a_ij


def alpha_2d(bin_d, bin_m, r_ll, s_ll):
    """
    Compute the probability migration from due to a Gaussian over-smearing.
    Note the computation is done with a normalisation to the fitting region

    Args:
        - bin_d: data binning in Mee
        - bin_m: MC binning in Mee
        - r_ll: Gaussian mean (relative, gaussian mean, scalar number)
        - s_ll: Gaussian resolution(relative as well, , scalar number)
    Returns a 2D tensor (dim(bining_data), dim(bining_mc))
    """
    return tf.squeeze(alpha_3d(np.array([bin_d]).T, np.array([bin_m]).T, r_ll=[r_ll], s_ll=[s_ll]), [2])


def alpha_3d(b_ic, b_jc, r_ll, s_ll):
    """
    Compute the probability migration from due to a Gaussian over-smearing.
    Note the computation is done with a normalisation to the fitting region

    Args:
        - b_ic: data binning in Mee (2D)
        - b_jc: MC binning in Mee (2D)
        - r_ll: Gaussian mean (relative, gaussian mean will be mu x r_ll)
        - s_ll: Gaussian resolution(relative as well)
    Returns a 3D tensor (dim(bining_data), dim(bining_mc), dim(r_ll))
    dim(r_ll) should be the number of events or categories
    """
    sqrt2 = tf.sqrt(2.)

    r_loc = tf.expand_dims(tf.expand_dims(r_ll, axis=0), axis=0)
    s_loc = tf.expand_dims(tf.expand_dims(s_ll, axis=0), axis=0)

    m_ijc = tf.expand_dims(0.5 * (b_jc[1:,] + b_jc[:-1,]), axis=0)
    b_ijc = tf.expand_dims(b_ic, axis=1)

    a_ijc = tf.math.erf((b_ijc[1:]/r_loc  - m_ijc) / (sqrt2 * m_ijc * s_loc)) - \
            tf.math.erf((b_ijc[:-1]/r_loc - m_ijc) / (sqrt2 * m_ijc * s_loc))
    
    return 0.5 * a_ijc


def alpha_3d_2g(b_ic, b_jc, rll_sll1, rll_sll2, rll_sll3, rll_sll4):
    """
    Compute the probability migration from due to a Gaussian over-smearing.
    Note the computation is done with a normalisation to the fitting region
    
    Args:
        - b_ic: data binning in Mee (2D)
        - b_jc: MC binning in Mee (2D)
        - r_ll: Gaussian mean (relative, gaussian mean will be mu x r_ll)
        - s_ll: Gaussian resolution(relative as well)
    Returns a 3D tensor (dim(bining_data), dim(bining_mc), dim(r_ll))
    dim(r_ll) should be the number of events or categories
    """
    sqrt2 = tf.sqrt(2.)

    m_ijc = tf.expand_dims(0.5 * (b_jc[1:,] + b_jc[:-1,]), axis=0)
    b_ijc = tf.expand_dims(b_ic, axis=1)

    a_ijc_total = tf.zeros_like(m_ijc)

    # loop over the 4 gaussians
    for (f_ll, r_ll, s_ll) in [rll_sll1, rll_sll2, rll_sll3, rll_sll4]:
        r_loc = tf.expand_dims(tf.expand_dims(r_ll, axis=0), axis=0)
        s_loc = tf.expand_dims(tf.expand_dims(s_ll, axis=0), axis=0)

        a_ijc = 0.5 * f_ll *(tf.math.erf((b_ijc[1:]/r_loc  - m_ijc) / (sqrt2 * m_ijc * s_loc)) - \
                tf.math.erf((b_ijc[:-1]/r_loc - m_ijc) / (sqrt2 * m_ijc * s_loc)))
        a_ijc_total += a_ijc
    
    
    return a_ijc_total
