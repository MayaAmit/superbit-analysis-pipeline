import numpy as np
from numpy.polynomial import Polynomial
import fitsio
from astropy.table import Table
import os
from argparse import ArgumentParser
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.colors import Normalize
from scipy.interpolate import interpn

from superbit_lensing import utils
from superbit_lensing.match import MatchedTruthCatalog

import pudb

parser = ArgumentParser()

parser.add_argument('shear_file', type=str,
                    help='Shear catalog filename')
parser.add_argument('truth_file', type=str,
                    help='Truth catalog filename')
parser.add_argument('-run_name', type=str, default=None,
                    help='Name of simulation run')
parser.add_argument('-outdir', type=str, default='',
                    help='Output directory for plots')
parser.add_argument('--show', action='store_true', default=False,
                    help='Turn on to display plots')
parser.add_argument('--vb', action='store_true', default=False,
                    help='Turn on for verbose prints')

def get_image_shape():
    '''Returns the SB single-epoch image shape (9568, 6380)'''

    return (9568, 6380)

def cut_cat_by_radius(cat, radius, xtag='x_image', ytag='y_image'):
    assert radius > 0
    Nx, Ny = get_image_shape()
    xcen, ycen = Nx // 2, Ny // 2
    assert xcen > 0
    assert ycen > 0

    obj_radius = np.sqrt((cat[xtag]-xcen)**2 + (cat[ytag]-ycen)**2)

    return cat[obj_radius < radius]

def plot_true_shear_dist(match, size=(8,8), outfile=None, show=None,
                         run_name=None, radial_cut=None, fontsize=14):

    true = match.true

    if radial_cut is not None:
        true = cut_cat_by_radius(true, radial_cut)

    # fig, axes = plt.subplots(nrows=1, ncols=2, figsize=size)

    plt.rcParams.update({'font.size': fontsize})

    bins = np.linspace(-.2, .2, 100)

    plt.hist(true['nfw_g1'], bins=bins, histtype='step', lw=2, label='g1', alpha=0.8)
    plt.hist(true['nfw_g2'], bins=bins, histtype='step', lw=2, label='g2', alpha=0.8)
    plt.axvline(0, lw=2, ls='--', c='k')

    plt.legend()
    plt.xlabel(r'True $\gamma$')
    plt.ylabel('Counts')
    plt.yscale('log')
    plt.title(f'{run_name} True Shear')

    plt.gcf().set_size_inches(size)

    if outfile is not None:
        plt.savefig(outfile, bbox_inches='tight', dpi=300)

    if show is True:
        plt.show()
    else:
        plt.close()

    return

def plot_responses_by_class(match, size=(8,8), outfile=None, show=False,
                         run_name=None, radial_cut=None, fontsize=14):
    '''
    Plot the distribution of shear responses for both stars
    and galaxies
    '''

    shear = match.meas

    if radial_cut is not None:
        shear = cut_cat_by_radius(shear, radial_cut)

    is_star = np.where(shear['redshift'] == 0)

    objs = {
        'star': shear[is_star],
        'gal': shear[not is_star],
        'foreground': shear[(not is_star) and
                            (shear['nfw_g1'] == 0) and
                            (shear['nfw_g2'] == 0)],
        'background': shear[(not is_star) and
                            (shear['nfw_g1'] != 0) or
                            (shear['nfw_g2'] != 0)]
    }

    plt.rcParams.update({'font.size': fontsize})
    bins = np.linspace(-3, 3, 100)

    R = np.mean([shear['r11'], shear['r22']], axis=0)
    plt.hist(
        R, bins=bins, histtype='step', alpha=0.8, label='All', lw=2
        )

    plt.axvline(0, lw=2, c='k', ls='--')

    for obj, cat in objs.items():
        R = np.mean([cat['r11'], cat['r22']], axis=0)

        plt.hist(
            R, bins=bins, histtype='step', alpha=0.8, label=obj, lw=2
            )

    if run_name is None:
        p = ''
    else:
        p = f'{run_name} '

    plt.legend()
    plt.xlabel('Response')
    plt.ylabel('Counts')
    plt.title(f'{p}Object Responses')

    plt.gcf().set_size_inches(size)

    if outfile is not None:
        plt.savefig(outfile, bbox_inches='tight', dpi=300)

    if show is True:
        plt.show()
    else:
        plt.close()

    return

def plot_shear_responses(match, size=(8,8), outfile=None, show=False,
                         run_name=None, radial_cut=None, fontsize=14,
                         label=None, close=True):
    '''
    Plot the distribution of shear responses for both stars
    and galaxies
    '''

    shear = match.meas

    if radial_cut is not None:
        shear = cut_cat_by_radius(shear, radial_cut)

    R = {'r11':None, 'r12': None, 'r21':None, 'r22': None}

    plt.rcParams.update({'font.size': fontsize})

    bins = np.linspace(-3, 3, 100)

    for key in R.keys():
        R[key] = shear[key]
        plt.hist(
            R[key], bins=bins, histtype='step', alpha=0.8, label=key, lw=2
            )

    plt.axvline(0, lw=2, c='k', ls='--')

    if run_name is None:
        p = ''
    else:
        p = f'{run_name} '

    plt.legend()
    plt.xlabel('Response')
    plt.ylabel('Counts')
    plt.title(f'{p}Object Responses')

    plt.gcf().set_size_inches(size)

    if outfile is not None:
        plt.savefig(outfile, bbox_inches='tight', dpi=300)

    if show is True:
        plt.show()

    if close is True:
        plt.close()

    return

def density_scatter(x, y, ax=None, fig=None, sort=True, bins=20, s=2,
                    **kwargs):
    '''
    Scatter plot colored by 2d histogram
    '''

    if ax is None:
        fig , ax = plt.subplots()
    else:
        if fig is None:
            raise Exception('Must pass both fig and ax if you pass one!')
    data, x_e, y_e = np.histogram2d(x, y, bins=bins, density=True )
    z = interpn(
        (0.5*(x_e[1:] + x_e[:-1]) , 0.5*(y_e[1:]+y_e[:-1])), data, np.vstack([x,y]).T,
        method='splinef2d', bounds_error=False
        )

    # To be sure to plot all data
    z[np.where(np.isnan(z))] = 0.0

    # Sort the points by density, so that the densest points are plotted last
    if sort:
        idx = z.argsort()
        x, y, z = x[idx], y[idx], z[idx]

    ax.scatter( x, y, c=z, s=s, **kwargs)

    norm = Normalize(vmin=np.min(z), vmax=np.max(z))
    cbar = fig.colorbar(cm.ScalarMappable(norm=norm), ax=ax)
    cbar.ax.set_ylabel('Density')

    return ax

def plot_shear_calibration(match, size=(16,6), outfile=None, show=False,
                           run_name=None, gridsize=50, fontsize=14,
                           radial_cut=None, limits=None, **kwargs):
    '''
    Plot the shear calibration (multiplicative & additive)
    for both stars and galxies
    '''

    truth = match.true
    shear = match.meas

    if radial_cut is not None:
        truth = cut_cat_by_radius(truth, radial_cut)
        shear = cut_cat_by_radius(shear, radial_cut)

    gtrue = {}
    gtrue['g1'] = truth['nfw_g1']
    gtrue['g2'] = truth['nfw_g2']

    gmeas= {}
    gmeas['g1'] = shear['g1_Rinv']
    gmeas['g2'] = shear['g2_Rinv']

    plt.rcParams.update({'font.size': fontsize})

    k = 1
    plt.close()
    fig, axes = plt.subplots(nrows=1, ncols=2)
    for i in range(2):
        # plt.hexbin(g1_true, g1_meas, gridsize=gridsize)
        # plt.axhline(0, lw=2, c='k', ls='--')
        # ax = plt.gca()
        ax = axes[i]
        x, y = gtrue[f'g{k}'], gmeas[f'g{k}']
        density_scatter(x, y, ax=ax, fig=fig, **kwargs)

        # Get linear fit to scatter points
        # m, b = np.polyfit(x, y, 1)
        b, m = Polynomial.fit(x, y, 1)

        # Compute m, b directly
        mean_gtrue = np.mean(gtrue[f'g{k}'])
        mean_gmeas = np.mean(gmeas[f'g{k}'])
        # mean_Rinv = 1. / (np.mean(shear['r11']) + np.mean(shear['r22']))

        # TODO: update for additive bias
        m_est = (mean_gmeas / mean_gtrue) - 1.

        if limits is None:
            xlim = ax.get_xlim()
            ylim = ax.get_ylim()
            lims = [
                np.min([ax.get_xlim(), ax.get_ylim()]),  # min of both axes
                np.max([ax.get_xlim(), ax.get_ylim()]),  # max of both axes
            ]
        else:
            lims = [
                np.min(limits),
                np.max(limits)
            ]
            xlim = limits[0]
            ylim = limits[1]

        # ax.plot([np.min(x), np.max(x)], [np.min(y), np.max(y)], 'k-')
        ax.plot(lims, np.poly1d((m,b))(lims), lw=2, ls='--', c='r', label=f'm={m:.3f}; b={b:.3f}')
        ax.plot(lims, lims, 'k-', label='x=y')
        ax.legend(fontsize=12)
        ax.set_xlim(xlim)
        ax.set_ylim(ylim)
        ax.set_xlabel(rf'True $\gamma_{k}$')
        ax.set_ylabel(rf'Meas $\gamma_{k}$' + ' ($\gamma^i / <R^i>$)')
        # ax.set_title(f'<g{k}_meas> ~ (1 + {m_est:.4f}) * <g{k}_true>')
        k += 1

    plt.gcf().set_size_inches(size)

    if run_name is None:
        p = ''
    else:
        p = f'{run_name} '
    plt.suptitle(f'{p}Shear Bias')

    if outfile is not None:
        plt.savefig(outfile, bbox_inches='tight', dpi=300)

    if show is True:
        plt.show()
    else:
        plt.close()

    return

def compute_shear_bias(sample, component):
    '''
    Compute multiplicative & added shear bias for sample
    and component 'g1' or 'g2'

    returns: (m, m_err, c, c_err)
    '''

    assert (component == 'g1') or (component == 'g2')
    g = component

    true = sample[f'nfw_{g}']
    meas = sample[f'{g}_Rinv']

    c, m = Polynomial.fit(true, meas, 1)

    # TODO: actually compute errors
    m_err, c_err = 0., 0.

    return (m, m_err, c, c_err)

def plot_bias_by_col(match, col, bins, outfile=None, show=False, run_name=None,
                     size=(10,14)):

    shear = match.meas

    N = len(bins) - 1
    g1_m = np.zeros(N)
    g1_c = np.zeros(N)
    g1_m_err = np.zeros(N)
    g1_c_err = np.zeros(N)
    g2_m = np.zeros(N)
    g2_c = np.zeros(N)
    g2_m_err = np.zeros(N)
    g2_c_err = np.zeros(N)

    k = 0
    for b1, b2 in zip(bins, bins[1:]):
        sample = shear[(shear[col] >= b1) & (shear[col] < b2)]

        g1_bias = compute_shear_bias(sample, 'g1')
        g1_m[k], g1_m_err[k] = g1_bias[0]-1., g1_bias[1]
        g1_c[k], g1_c_err[k] = g1_bias[2], g1_bias[3]

        g2_bias = compute_shear_bias(sample, 'g2')
        g2_m[k], g2_m_err[k] = g2_bias[0]-1., g2_bias[1]
        g2_c[k], g2_c_err[k] = g2_bias[2], g2_bias[3]
        k += 1

    xx = np.mean([bins[0:-1], bins[1:]], axis=0)

    fig, axes = plt.subplots(nrows=2, ncols=1, sharex=True)

    axes[0].errorbar(xx, 10*g1_m, 10*g1_m_err, label='g1')
    axes[0].errorbar(xx, 10*g2_m, 10*g2_m_err, label='g2')
    axes[0].axhline(0, lw=2, ls='--', c='k')
    axes[0].set_ylabel(r'm [$10^{-1}$]')
    axes[0].legend()

    axes[1].errorbar(xx, 100*g1_c, 100*g1_c_err, label='g1')
    axes[1].errorbar(xx, 100*g2_c, 100*g2_c_err, label='g2')
    axes[1].axhline(0, lw=2, ls='--', c='k')
    axes[1].set_xlabel(col)
    axes[1].set_ylabel('c [$10^{-2}$]')
    axes[1].legend()

    fig.set_size_inches(size)
    fig.subplots_adjust(hspace=0.1)

    if run_name is None:
        p = ''
    else:
        p = f'{run_name} '
    plt.suptitle(f'{p}Shear Bias', y=0.9)

    if outfile is not None:
        plt.savefig(outfile, bbox_inches='tight', dpi=300)

    if show is True:
        plt.show()
    else:
        plt.close()

    return

def match_cats(truth_file, shear_file, **kwargs):
    return MatchedTruthCatalog(truth_file, shear_file, **kwargs)

def main(args):

    shear_file = args.shear_file
    truth_file = args.truth_file
    run_name = args.run_name
    outdir = args.outdir
    show = args.show
    vb = args.vb

    if run_name is not None:
        p = f'{run_name}-'
    else:
        p = ''

    if outdir is not None:
        utils.make_dir(outdir)

    match = match_cats(
        truth_file, shear_file
        , meas_ratag='ra_mcal', meas_dectag='dec_mcal'
        )
    print(f'Match cat has {match.Nobjs} objs')

    outfile = os.path.join(outdir, f'{p}true-g-dist.png')
    plot_true_shear_dist(
        match, outfile=outfile, show=show, run_name=run_name
                         )

    outfile = os.path.join(outdir, f'{p}shear-responses.png')
    plot_shear_responses(
        match, outfile=outfile, show=show, run_name=run_name
                         )

    outfile = os.path.join(outdir, f'{p}shear-calibration.png')
    plot_shear_calibration(
        match, outfile=outfile, show=show, run_name=run_name
        )

    outfile = os.path.join(outdir, f'{p}shear-calibration-zoom.png')
    plot_shear_calibration(
        match, outfile=outfile, show=show, run_name=run_name,
        limits=[[-.1, .1], [-.5, .5]], s=3
        )

    #-----------------------------------------------------------------
    # Now repeat w/ radial cut to force square in image
    # single images have dimensions (9568, 6380)
    radial_cut = 6380 // 2 # pixels
    outfile = os.path.join(outdir, f'{p}true-g-dist-rcut.png')
    plot_true_shear_dist(
        match, outfile=outfile, show=show, run_name=run_name,
        radial_cut=radial_cut
                         )

    outfile = os.path.join(outdir, f'{p}shear-responses-rcut.png')
    plot_shear_responses(
        match, outfile=outfile, show=show, run_name=run_name,
        radial_cut=radial_cut
                         )

    outfile = os.path.join(outdir, f'{p}shear-calibration-rcut.png')
    plot_shear_calibration(
        match, outfile=outfile, show=show, run_name=run_name,
        radial_cut=radial_cut
        )

    outfile = os.path.join(outdir, f'{p}shear-calibration-zoom-rcut.png')
    plot_shear_calibration(
        match, outfile=outfile, show=show, run_name=run_name,
        limits=[[-.1, .1], [-.5, .5]], s=3,
        radial_cut=radial_cut
        )

    #-----------------------------------------------------------------
    # Now replicate some of the plots in mcal2

    outfile = os.path.join(outdir, f'{p}obj-responses.png')
    plot_responses_by_class(
        match, outfile=outfile, show=show, run_name=run_name,
        )

    outfile = os.path.join(outdir, f'{p}bias-by-s2n.png')
    bins = np.linspace(10, 20, 11)
    print(bins)
    plot_bias_by_col(
        match, 's2n_r_noshear', bins, outfile=outfile, show=show, run_name=run_name,
        )

    return 0

if __name__ == '__main__':
    args = parser.parse_args()
    rc = main(args)

    if rc == 0:
        print('\nTests have completed without errors')
    else:
        print(f'\nTests failed with rc={rc}')

