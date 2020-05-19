import os

import h5py
import numpy as np
import pylab as plt
from matplotlib import gridspec
from scipy.signal import detrend


def figsize(scale, width_by_height_ratio):
    """
    Create figure size either a full page or a half page figure

    Args:

        scale (float): 0.5 for half page figure, 1 for full page

        width_by_height_ratio (float): ratio of width to height for the figure

    Returns: list of width and height

    """
    fig_width_pt = 513.17  # 469.755                  # Get this from LaTeX using \the\textwidth
    inches_per_pt = 1.0 / 72.27  # Convert pt to inch
    golden_mean = (np.sqrt(5.0) - 1.0) / 2.0  # Aesthetic ratio (you could change this)
    fig_width = fig_width_pt * inches_per_pt * scale  # width in inches
    fig_height = fig_width * golden_mean  # height in inches
    fig_size = [fig_width, width_by_height_ratio * fig_height]
    return fig_size


def get_params(scale=0.5, width_by_height_ratio=1):
    """
    Create a dictionary for pretty plotting

    Args:

        scale (float): 0.5 for half page figure, 1 for full page

        width_by_height_ratio (float): ratio of width to height for the figure

    Returns: dictionary of parameters

    """
    params = {'backend': 'pdf',
              'axes.labelsize': 10,
              'lines.markersize': 4,
              'font.size': 10,
              'xtick.major.size': 6,
              'xtick.minor.size': 3,
              'ytick.major.size': 6,
              'ytick.minor.size': 3,
              'xtick.major.width': 0.5,
              'ytick.major.width': 0.5,
              'xtick.minor.width': 0.5,
              'ytick.minor.width': 0.5,
              'lines.markeredgewidth': 1,
              'axes.linewidth': 1.2,
              'legend.fontsize': 7,
              'xtick.labelsize': 10,
              'ytick.labelsize': 10,
              'savefig.dpi': 200,
              'path.simplify': True,
              'font.family': 'serif',
              'font.serif': 'Times',
              'text.latex.preamble': [r'\usepackage{amsmath}', r'\usepackage{amsbsy}',
                                      r'\DeclareMathAlphabet{\mathcal}{OMS}{cmsy}{m}{n}'],
              'figure.figsize': figsize(scale, width_by_height_ratio)}
    return params


def plot_h5(h5_file, save=True, detrend_ft=True, publication=False):
    """
    Plot the h5 candidates

    Args:

        h5_file (str): Name of the h5 file

        save (bool): Save the file as a png

        detrend_ft (bool): detrend the frequency time plot

        publication (bool): make publication quality plot

    Returns: None

    """
    with h5py.File(h5_file, 'r') as f:
        dm_time = np.array(f['data_dm_time'])
        if detrend_ft:
            freq_time = detrend(np.array(f['data_freq_time'])[:, ::-1].T)
        else:
            freq_time = np.array(f['data_freq_time'])[:, ::-1].T
        dm_time[dm_time != dm_time] = 0
        freq_time[freq_time != freq_time] = 0
        freq_time -= np.median(freq_time)
        freq_time /= np.std(freq_time)
        fch1, foff, nchan, dm, cand_id, tsamp, dm_opt, snr, snr_opt, width = f.attrs['fch1'], \
                                                                             f.attrs['foff'], f.attrs['nchans'], \
                                                                             f.attrs['dm'], f.attrs['cand_id'], \
                                                                             f.attrs['tsamp'], f.attrs['dm_opt'], \
                                                                             f.attrs['snr'], f.attrs['snr_opt'], \
                                                                             f.attrs['width']
        if width > 1:
            ts = np.linspace(-128, 128, 256) * tsamp * width * 1000 / 2
        else:
            ts = np.linspace(-128, 128, 256) * tsamp * 1000

        plt.clf()

        if publication:
            fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(5, 7), sharex='col')

        else:
            fig = plt.figure(figsize=(15, 10))
            gs = gridspec.GridSpec(3, 2, width_ratios=[4, 1], height_ratios=[1, 1, 1])
            ax1 = plt.subplot(gs[0, 0])
            ax2 = plt.subplot(gs[1, 0])
            ax3 = plt.subplot(gs[2, 0])
            ax4 = plt.subplot(gs[:, 1])
            to_print = []
            for key in f.attrs.keys():
                if 'filelist' in key:
                    pass
                elif 'filename' in key:
                    to_print.append(f'filename : {os.path.basename(f.attrs[key])}\n')
                    to_print.append(f'filepath : {os.path.dirname(f.attrs[key])}\n')
                else:
                    to_print.append(f'{key} : {f.attrs[key]}\n')
            str_print = ''.join(to_print)
            ax4.text(0.2, 0, str_print, fontsize=14, ha='left', va='bottom', wrap=True)
            ax4.axis('off')

        ax1.plot(ts, freq_time.sum(0), 'k-')
        ax1.set_ylabel('Flux (Arb. Units)')
        ax2.imshow(freq_time, aspect='auto', extent=[ts[0], ts[-1], fch1, fch1 + (nchan * foff)], interpolation='none')
        ax2.set_ylabel('Frequency (MHz)')
        ax3.imshow(dm_time, aspect='auto', extent=[ts[0], ts[-1], 2 * dm, 0], interpolation='none')
        ax3.set_ylabel(r'DM (pc cm$^{-3}$)')
        ax3.set_xlabel('Time (ms)')

        plt.tight_layout()
        if save:
            plt.savefig(h5_file[:-3] + '.png', bbox_inches='tight')
        else:
            plt.close()

        return None