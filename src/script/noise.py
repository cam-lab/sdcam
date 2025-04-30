
import os
import sys
import glob

sys.path.append( os.path.abspath( os.path.join('src', 'app'    ) ) )
sys.path.append( os.path.abspath( os.path.join('bin', 'release') ) )

import numpy as np
import sdc_lib as sdcl

T_pix = 120e-9
T_row = 81240e-9

Fs_pix   = 1/T_pix
Fs_row   = 1/T_row
Fs_frame = 23.623

#-------------------------------------------------------------------------------
#
#    Create array with amplitude spectrum for each row of the frame pixel buffer
#
#        Args:
#        ~~~~
#          Frame pixel buffer
#
#        Return:
#        ~~~~~~
#          Frequency array and amplitude spectrum list
#
def rows_ams(pbuf):
    ams = []
    height, width = pbuf.shape
    for r in range(height):
        f, a = sdcl.fft(pbuf[r], Fs_pix)
        ams.append(a)
        
    return f, np.array(ams)

#-------------------------------------------------------------------------------
#
#    Create array with amplitude spectrum for each column of the frame pixel buffer
#
#        Args:
#        ~~~~
#          Frame pixel buffer
#
#        Return:
#        ~~~~~~
#          Frequency array and amplitude spectrum list
#
def cols_ams(pbuf):
    ams = []
    height, width = pbuf.shape
    for c in range(width):
        f, a = sdcl.fft(pbuf[:, c], Fs_row)
        ams.append(a)

    return f, np.array(ams)

#-------------------------------------------------------------------------------
#
#    Create arrya with amplitude spectrum for each item in the pool of columns
#    retrieved from frame pool
#
#    Args:
#    ~~~~
#      Array of columns which are data of the same column of frames in frame pool
#
#    Return:
#    ~~~~~~
#      Frequency array and amplitude spectrum list
#
def cols_pool_ams(col_pool):
    ams = []
    pool_len, col_size = col_pool.shape
    for c in range(pool_len):
        f, a = sdcl.fft(col_pool[c], Fs_row)
        ams.append(a)

    return f, np.array(ams)

#-------------------------------------------------------------------------------
#
#    1. Create spectrums for all rows of the frame, plot the spectrums
#
#    2. Calculate average spectrum from row spectrums, plot this average spectrum
#
#    3. Add zoomed at LF verions of the above plots
#
#    Args:
#    ~~~~
#      File path:  path of the file which contains series of frames. File
#                  should be created with numpy.save() function
#
#      Frame number: index of the frame in series
#
def rows_spectrum(fpath, nframe=0):
    frames    = np.load(fpath)
    row_count = frames[0].shape[0]
    f, ams    = rows_ams(frames[nframe])
    avg_ams   = np.mean(ams, axis=0)

    fig = plt.figure(figsize=(10, 12))
    fig.suptitle('Rows Spectrum', size=16, y=0.95)
    
    #-----------------------------------------------------------------
    ax1 = fig.add_subplot(411)
    ax1.title.set_text('All frame rows spectrum')
    plt.grid(True); plt.xlabel('Frequency, Hz'); plt.ylabel('Amplitude, ADC LSB')
    for i in range(row_count):
        plt.plot(f[1:], ams[i][1:])
        
    #-----------------------------------------------------------------
    ax2 = fig.add_subplot(412, sharex=ax1)
    ax2.title.set_text('Average rows spectrum')
    plt.grid(True); plt.xlabel('Frequency, Hz'); plt.ylabel('Amplitude, ADC LSB')
    plt.plot(f[1:], avg_ams[1:])
    
    #-----------------------------------------------------------------
    ax3 = fig.add_subplot(413)
    ax3.title.set_text('All frame rows spectrum: zoom to LF')
    plt.grid(True); plt.xlabel('Frequency, Hz'); plt.ylabel('Amplitude, ADC LSB')
    points = 4
    for i in range(row_count):
        plt.plot(f[1:points], ams[i][1:points])

    #-----------------------------------------------------------------
    ax4 = fig.add_subplot(414, sharex=ax3)
    ax4.title.set_text('Average rows spectrum: zoom to LF')
    plt.grid(True); plt.xlabel('Frequency, Hz'); plt.ylabel('Amplitude, ADC LSB')
    plt.plot(f[1:points], avg_ams[1:points])

    #-----------------------------------------------------------------
    plt.subplots_adjust(left=None, bottom=None, right=None, top=None, wspace=None, hspace=0.5)

    plt.show()
    
    figfile = os.path.dirname(fpath).replace('/', '-')
    fig.savefig(f'{figfile}-row-spectrum.png')

#-------------------------------------------------------------------------------
#
#    1. Create spectrums for all columns of the frame, plot the spectrums
#
#    2. Calculate average spectrum from column spectrums, plot this average spectrum
#
#    3. Add zoomed at LF verions of the above plots
#
#    Args:
#    ~~~~
#      File path: path of the file which contains series of frames. File
#                 should be created with numpy.save() function
#
#      Frame number: index of the frame in series
#
def cols_spectrum(fpath, nframe=0):
    frames    = np.load(fpath)
    col_count = frames[0].shape[1]
    f, ams    = cols_ams(frames[nframe])
    #avg_ams   = average(ams)
    avg_ams   = np.mean(ams, axis=0)

    fig = plt.figure(figsize=(10, 12))
    fig.suptitle('Columns Spectrum', size=16, y=0.95)

    #-----------------------------------------------------------------
    ax1 = fig.add_subplot(411)
    ax1.title.set_text('All frame columns spectrum')
    plt.grid(True); plt.xlabel('Frequency, Hz'); plt.ylabel('Amplitude, ADC LSB')
    for i in range(col_count):
        plt.plot(f[1:], ams[i][1:])

    #-----------------------------------------------------------------
    ax2 = fig.add_subplot(412, sharex=ax1)
    ax2.title.set_text('Average columns spectrum')
    plt.grid(True); plt.xlabel('Frequency, Hz'); plt.ylabel('Amplitude, ADC LSB')
    plt.plot(f[1:], avg_ams[1:])

    #-----------------------------------------------------------------
    ax3 = fig.add_subplot(413)
    ax3.title.set_text('All frame columns spectrum: zoom to LF')
    plt.grid(True); plt.xlabel('Frequency, Hz'); plt.ylabel('Amplitude, ADC LSB')
    points = 4
    for i in range(col_count):
        plt.plot(f[1:points], ams[i][1:points])

    #-----------------------------------------------------------------
    ax4 = fig.add_subplot(414, sharex=ax3)
    ax4.title.set_text('Average columns spectrum: zoom to LF')
    plt.grid(True); plt.xlabel('Frequency, Hz'); plt.ylabel('Amplitude, ADC LSB')
    plt.plot(f[1:points], avg_ams[1:points])

    #-----------------------------------------------------------------
    plt.subplots_adjust(left=None, bottom=None, right=None, top=None, wspace=None, hspace=0.5)

    plt.show()

    figfile = os.path.dirname(fpath).replace('/', '-')
    fig.savefig(f'{figfile}-col-spectrum.png')

#-------------------------------------------------------------------------------
#
#    Replace every Nth item with mean of previous and next items
#
#    Args:
#    ~~~~
#       a: array with data that is typically spectrum of composite column
#       n: the multiple of indices for replacing
#
def suppress_artefacts(a, n):
    i = np.arange(n, len(a)-1, n)

    a[i] = (a[i-1] + a[i+1])/2
    
    return a

#-------------------------------------------------------------------------------
#
#    1. Create composite long column from same or different column of frames
#       from series loaded from specified file
#
#    2. Retrieve spectrum from this long column
#
#    Args:
#    ~~~~
#      File path: path of the file which contains series of frames. File
#                 should be created with numpy.save() function
#
#      Column number: start number of the columm
#
#      Spread step:   increment value for column number. 0 means the same
#                     column for all frames
#
#    Return:
#    ~~~~~~
#      Composite long column
#      Spectrum frequency vector
#      Spectrum amplitude vector
#
#    Examples:
#    ~~~~~~~~
#      1) get spectrum for long column composed from 320th columns of the frames
#         in series
#
#          lc, f, a = long_col_ams('det/r2313b-73/f100-0.npy', 320)
#
#      2) get spectrum for long column composed from columns with indices from 200 to
#         2 multiple series frame count with index increment 2
#
#          lc, f, a = long_col_ams('det/r2313b-73/f100-0.npy', 200, 2)
#
def long_col_ams(fpath, n: int, spread_step=0, sa=False):
    fpool       = np.load(fpath)
    frame_count = fpool.shape[0]

    ams_pool = []
    lc_pool  = []
    
    #cols = fpool[:, :, 320] # retrieve 320th column and make array of the columns
    cols = []
    for i in range(frame_count):
        cols.append(fpool[i][:, n+i*spread_step])

    clist = []
    for idx, col in enumerate(cols):
        #
        # generate tail for column to fill interframe pause as random series
        # with mean and standard deviation that are average between current and
        # the next frame columns
        #
        mean_next = cols[idx+1].mean() if idx < len(cols)-1 else cols[idx].mean()
        std_next  = cols[idx+1].std()  if idx < len(cols)-1 else cols[idx].std()

        mean    = (col.mean() + mean_next)/2
        std     = (col.std()  + std_next)/2
        tail    = np.random.normal(loc=mean, scale=std, size=9).astype(np.uint16)
        
        # create result column
        ext_col = np.concatenate( (col, tail) )
        clist.append(ext_col)

    lc   = np.concatenate( clist )  # create long column
    lc   = lc - lc.min()            # remove DC component
    f, a = sdcl.fft(lc, Fs_row)     # retrieve spectrium from long column
    
    if sa:
        a = suppress_artefacts(a, frame_count)

    return lc, f, a

#-------------------------------------------------------------------------------
#
#    Performs processing of data files with series of video frames and outputs
#    spectrums of composite long columns
#
#    Args:
#    ~~~~
#      File path prefix: path prefix for files that contain series of frames. Files
#                        should be created with numpy.save() function
#
#      Column number: start number of the columm
#
#      Spread step:   increment value for column number. 0 means the same
#                     column for all frames
#
#    Return:
#    ~~~~~~
#      Spectrum frequency vector
#      Spectrum amplitude vector array
#      Spectrum average amplitude vector
#
#    Examples:
#    ~~~~~~~~
#      1) get spectrum for long column composed from 320th columns of the frames
#         in series
#
#          f, ams_pool, avg_ams_320 = long_col_ams_summary('det/r2313b-73/f100', 320)
#
#      2) get spectrum for long column composed from columns with indices from 250 to
#         1 multiple series frame count with index increment 1
#
#        f, ams_pool, avg_ams_250_1 = long_col_ams_summary('det/r2313b-73/f100', 250, 1)
#
def long_col_ams_summary(fpath_prefix, n: int, spread_step=0, sa=False):
    fnlist = glob.glob(f'{fpath_prefix}*')
    fnlist.sort()
    
    ams_pool = []
    f = None
    for fname in fnlist:
        lc, f, a = long_col_ams(fname, n, spread_step, sa)
        ams_pool.append(a)
        
    ams = np.array(ams_pool)

    return f, ams, np.mean(ams, axis=0)

#-------------------------------------------------------------------------------
def plot_long_col_spectrum(fpath_prefix, n: int, spread_step=0, sa=False):

    f, ams_pool, avg_ams = long_col_ams_summary(fpath_prefix, n, spread_step, sa)

    fig = plt.figure(figsize=(10, 12))
    fig.suptitle('Long Column Spectrum', size=16, y=0.95)

    #-----------------------------------------------------------------
    ax1 = fig.add_subplot(411)
    ax1.title.set_text('All long columns spectrum')
    plt.grid(True); plt.xlabel('Frequency, Hz'); plt.ylabel('Amplitude, ADC LSB')
    for i in ams_pool:
        plt.plot(f[1:], i[1:])

    #-----------------------------------------------------------------
    ax2 = fig.add_subplot(412, sharex=ax1)
    ax2.title.set_text('Average long column spectrum')
    plt.grid(True); plt.xlabel('Frequency, Hz'); plt.ylabel('Amplitude, ADC LSB')
    plt.plot(f[1:], avg_ams[1:])

    #-----------------------------------------------------------------
    ax3 = fig.add_subplot(413)
    ax3.title.set_text('All long columns spectrum: zoom to LF')
    plt.grid(True); plt.xlabel('Frequency, Hz'); plt.ylabel('Amplitude, ADC LSB')
    points = 99
    for i in ams_pool:
        plt.plot(f[1:points], i[1:points])

    #-----------------------------------------------------------------
    ax4 = fig.add_subplot(414, sharex=ax3)
    ax4.title.set_text('Average long columns spectrum: zoom to LF')
    plt.grid(True); plt.xlabel('Frequency, Hz'); plt.ylabel('Amplitude, ADC LSB')
    plt.plot(f[1:points], avg_ams[1:points])

    #-----------------------------------------------------------------

    plt.subplots_adjust(left=None, bottom=None, right=None, top=None, wspace=None, hspace=0.5)

    plt.show()

    figfile = os.path.dirname(fpath_prefix).replace('/', '-')
    fig.savefig(f'{figfile}-long-col-spectrum.png')


#-------------------------------------------------------------------------------
def plot_long_col_avg_spectrum(fpath_prefix, n: int, spread_step=0, sa=False):

    f, ams_pool, avg_ams = long_col_ams_summary(fpath_prefix, n, spread_step, sa)

    fig = plt.figure(figsize=(10, 3))

    #-----------------------------------------------------------------
    ax = fig.add_subplot(111)
    ax.title.set_text('Average long column spectrum')
    plt.grid(True); plt.xlabel('Frequency, Hz'); plt.ylabel('Amplitude, ADC LSB')
    points = 300
    plt.plot(f[1:points], avg_ams[1:points], '.-')
    plt.plot(f[1:points], (1/f[1:points] + 0.08), '.-')
    ax.legend(['Average long column spectrum', '1/f curve'])

    #-----------------------------------------------------------------
    plt.show()

#-------------------------------------------------------------------------------
def plot_long_col_avg_spectrums(fpath_prefix, n: int, spread_step=0, sa=False):

    f0, ams_pool0, avg_ams0 = long_col_ams_summary(fpath_prefix[0], n, spread_step, sa)
    f1, ams_pool1, avg_ams1 = long_col_ams_summary(fpath_prefix[1], n, spread_step, sa)

    fig = plt.figure(figsize=(10, 6))

    #-----------------------------------------------------------------
    ax0 = fig.add_subplot(211)
    ax0.title.set_text('Average long column spectrum')
    plt.grid(True); plt.xlabel('Frequency, Hz'); plt.ylabel('Amplitude, ADC LSB')

    plt.plot(f0[1:], avg_ams0[1:])
    plt.plot(f1[1:], avg_ams1[1:])
    ax0.legend(['r2313b-70', 'r2313b-73'])

    ax1 = fig.add_subplot(212)
    ax1.title.set_text('Average long column spectrum: zoom to LF')
    plt.grid(True); plt.xlabel('Frequency, Hz'); plt.ylabel('Amplitude, ADC LSB')
    points = 99
    plt.plot(f0[1:points], avg_ams0[1:points])
    plt.plot(f1[1:points], avg_ams1[1:points])
    ax1.legend(['r2313b-70', 'r2313b-73'])

    #-----------------------------------------------------------------
    plt.subplots_adjust(left=None, bottom=None, right=None, top=None, wspace=None, hspace=0.5)
    plt.show()

#-------------------------------------------------------------------------------
#
#    Create array with average amplitude spectrum obtained from spectrums of all
#    pixels in time domain: spectrum for each pixel calculated from pixel values
#    that retrieved from certain pixel position over all frames in series
#
#        Args:
#        ~~~~
#          Path to file with frame series
#
#        Return:
#        ~~~~~~
#          Frequency array and average amplitude spectrum
#
def pix_mean_ams(fpath):
    fpool       = np.load(fpath)
    frame_count = fpool.shape[0]
    row_count   = fpool[0].shape[0]
    col_count   = fpool[0].shape[1]

    ams = []
    for r in range(row_count):
        for c in range(col_count):
            pix  = fpool[:, r, c]
            f, a = sdcl.fft(pix, Fs_frame)
            ams.append(a)

    return f, np.mean(np.array(ams), axis=0)

#-------------------------------------------------------------------------------
#
#    Plot pixel average spectrum
#
#      Args:
#      ~~~~
#        Prefix of the path to files with frame series
#
#      Example:
#      ~~~~~~~
#        plot_pix_mean_ams('../det/r2313b-70/f100')
#
def plot_pix_mean_ams(fpath_prefix):
    f, a = pix_mean_ams_summary(fpath_prefix)
    plot_mean_ams_summary(f, a, fpath_prefix)

#---------------------------------------------------------------------
def pix_mean_ams_summary(fpath_prefix):
    fnlist = glob.glob(f'{fpath_prefix}*')
    fnlist.sort()

    ams_pool = []
    f = None
    for fname in fnlist:
        f, a = pix_mean_ams(fname)
        ams_pool.append(a)

    ams = np.array(ams_pool)
    
    return f, ams

def plot_pix_mean_ams_summary(f, ams, fpath_prefix):
    
    lc_f, lc_ams_pool, lc_avg_ams = long_col_ams_summary(fpath_prefix, 220, spread_step=2, sa=True)

    #-----------------------------------------------------------------
    fig = plt.figure(figsize=(10, 6))

    #-----------------------------------------------------------------
    ax0 = fig.add_subplot(211)
    ax0.title.set_text('Average pixel spectrums for all series')
    plt.grid(True); plt.xlabel('Frequency, Hz'); plt.ylabel('Amplitude, ADC LSB')

    for a in ams:
        plt.plot(f[1:], a[1:])
        
    ax1 = fig.add_subplot(212)
    ax1.title.set_text('Average over all series pixel spectrum vs long column spectrum')
    plt.grid(True); plt.xlabel('Frequency, Hz'); plt.ylabel('Amplitude, ADC LSB')
    plt.plot(f[1:], np.mean(ams, axis=0)[1:])
    points = 50
    plt.plot(lc_f[1:points], lc_avg_ams[1:points])
    
    ax1.legend(['Pixel spectrum', 'Long column spectrum'])
    
    plt.subplots_adjust(left=None, bottom=None, right=None, top=None, wspace=None, hspace=0.5)
    plt.show()

#-------------------------------------------------------------------------------

