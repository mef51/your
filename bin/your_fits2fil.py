#!/usr/bin/env python
# coding: utf-8

# In[1]:


import argparse
import glob
import logging
import os
from datetime import datetime


# In[2]:


import numpy as np
import tqdm
import glob


# In[3]:


from your import Your
from your.pysigproc import SigprocFile


# In[4]:


logger = logging.getLogger(__name__)


# In[5]:


def make_sigproc_obj(filfile, y, nchans, chan_freq):
    '''
    Use Your class object of the lower band to make Sigproc
    class object with the relevant parameters
    :param filfile: Name of the Filterbank file
    :param y: Your object for the PSRFITS files
    '''
    logger.debug(f'Generating Sigproc object')
    fil_obj = SigprocFile()

    logger.debug(f'Setting attributes of Sigproc object from Your object.')
    fil_obj.rawdatafile = filfile
    fil_obj.source_name = y.your_header.source_name

    # Verify the following parameters
    fil_obj.machine_id = 0  # use "Fake" for now
    fil_obj.barycentric = 0  # by default the data isn't barycentered
    fil_obj.pulsarcentric = 0
    fil_obj.telescope_id = 6  # use only GBT for now
    fil_obj.data_type = 0

    fil_obj.nchans = nchans
    fil_obj.foff = y.your_header.foff
    fil_obj.fch1 = chan_freq[1]
    fil_obj.nbeams = 1
    fil_obj.ibeam = 0
    fil_obj.nbits = y.your_header.nbits
    fil_obj.tsamp = y.your_header.tsamp
    fil_obj.tstart = y.your_header.tstart
    fil_obj.nifs = 1  # Only use Intensity values
    
    from astropy.coordinates import SkyCoord
    loc = SkyCoord(y.your_header.ra_deg, y.your_header.dec_deg, unit='deg')
    ra_hms = loc.ra.hms
    dec_dms = loc.dec.dms
    
    fil_obj.src_raj = float(f'{int(ra_hms[0]):02d}{np.abs(int(ra_hms[1])):02d}{np.abs(ra_hms[2]):07.4f}')
    fil_obj.src_dej = float(f'{int(dec_dms[0]):02d}{np.abs(int(dec_dms[1])):02d}{np.abs(dec_dms[2]):07.4f}')
    
    fil_obj.az_start = -1
    fil_obj.za_start = -1
    return fil_obj


# In[6]:


def write_fil(data, y, nchans =None, chan_freq=None, filename=None, outdir=None):
    '''
    Write Filterbank file given the Your object
    :param y: Your object for the PSRFITS files
    :param nonzerodata: Non-Zero Data from the PSRFITS files
    :param filename: Output name of the Filterbank file
    :param outdir: Output directory for the Filterbank file
    '''

    original_dir, orig_basename = os.path.split(y.your_header.filename)
    if not filename:
        filename = '_'.join(orig_basename.split('.')[0].split('_')[:-1]) + '.fil'

    if not outdir:
        outdir = original_dir

    filfile = outdir + '/' + filename

    # Add checks for an existing fil file
    logger.info(f'Trying to write data to filterbank file: {filfile}')
    try:
        if os.stat(filfile).st_size > 8192:  # check and replace with the size of header
            logger.info(f'Writing {data.shape[0]} spectra to file: {filfile}')
            SigprocFile.append_spectra(data, filfile)

        else:
            fil_obj = make_sigproc_obj(filfile, y,nchans,chan_freq)
            fil_obj.write_header(filfile)
            logger.info(f'Writing {data.shape[0]} spectra to file: {filfile}')
            fil_obj.append_spectra(data, filfile)

    except FileNotFoundError:
        fil_obj = make_sigproc_obj(filfile, y, nchans,chan_freq)
        fil_obj.write_header(filfile)
        logger.info(f'Writing {data.shape[0]} spectra to file: {filfile}')
        fil_obj.append_spectra(data, filfile)
    logger.info(f'Successfully written data to Filterbank file: {filfile}')


# In[7]:


def convert(f,c=None, outdir=None, filfile=None):
    '''
    reads data from one or more PSRFITS files
    and writes out a Filterbank File.
    :param f: List of PSRFITS files
    :param outdir: Output directory for Filterbank file
    :param filfile: Name of the Filterbank file to write to
    '''
    y = Your(f)
    fits_header = vars(y.your_header)
    if c:
        min_c = int(np.min(c))
        max_c = int(np.max(c))
    else:
        min_c = 0
        max_c = len(y.chan_freqs)
        
    chan_freq = y.chan_freqs[min_c:max_c]
    nchans = len(chan_freq)

    # Calculate loop of spectra
    interval = 4096 * 24
    if y.your_header.native_nspectra > interval:
        nloops = 1 + y.your_header.native_nspectra // interval
    else:
        nloops = 1
    nstarts = np.arange(0, interval * nloops, interval, dtype=int)
    nsamps = np.full(nloops, interval)
    if y.your_header.native_nspectra % interval != 0:
        nsamps[-1] = y.your_header.native_nspectra % interval

    # Read data
    for nstart, nsamp in tqdm.tqdm(zip(nstarts, nsamps), total=len(nstarts)):
        logger.debug(f'Reading spectra {nstart}-{nstart + nsamp} in file {y.filename}')
        data = y.get_data(nstart, nsamp).astype(y.your_header.dtype)
        data = data[:,min_c:max_c]
       
        logger.info(f'Writing data from spectra {nstart}-{nstart + nsamp}in the frequency channel range {min_c}-{max_c} to filterbank')
        write_fil(data, y, nchans = nchans, chan_freq = chan_freq, outdir=outdir, filename=filfile)
        logger.debug(f'Successfully written data from spectra {nstart}-{nstart + nsamp} in the frequency channel range {min_c}-{max_c} to filterbank')

    logging.debug(f'Read all the necessary spectra')


# In[8]:


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Convert files from PSRFITS format to a single file in Filterbank format.",formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-v', '--verbose', help='Be verbose', action='store_true')
    parser.add_argument('-f', '--files',
                        help='Paths of PSRFITS files to be converted to a single file in Filterbank format. Surround with quotes, and either use wildcards or separate with spaces',
                        required=True, type=str)
    parser.add_argument('-c', '--chans', help='Required channels (eg -c 0 4096)', required=False, type=int, nargs=2, default=None)
    parser.add_argument('-o', '--outdir', type=str, help='Output directory for Filterbank file', default='.',
                        required=False)
    parser.add_argument('-fil', '--fil_name', type=str, help='Output name of the Filterbank file', default=None,
                        required=False)
    values = parser.parse_args()

    logging_format = '%(asctime)s - %(funcName)s -%(name)s - %(levelname)s - %(message)s'
    log_filename = values.outdir + '/' + datetime.utcnow().strftime('fits2fil_%Y_%m_%d_%H_%M_%S_%f.log')

    if values.verbose:
        logging.basicConfig(filename=log_filename, level=logging.DEBUG, format=logging_format)
    else:
        logging.basicConfig(filename=log_filename, level=logging.INFO, format=logging_format)

    logging.info("Input Arguments:-")
    for arg, value in sorted(vars(values).items()):
        logging.info("Argument %s: %r", arg, value)

    if len(values.files.split(' ')) > 1:
        files = values.files.split(' ')
    else:
        files = glob.glob(values.files)
        

    convert(files, values.chans, values.outdir, values.fil_name)


# In[ ]:




