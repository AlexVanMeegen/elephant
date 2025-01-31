# -*- coding: utf-8 -*-
"""
This modules provides functions to calculate correlations between spike trains.

:copyright: Copyright 2015-2016 by the Elephant team, see `doc/authors.rst`.
:license: Modified BSD, see LICENSE.txt for details.
"""
from __future__ import division
import numpy as np
import neo
import quantities as pq
import warnings


def covariance(binned_sts, binary=False):
    '''
    Calculate the NxN matrix of pairwise covariances between all combinations
    of N binned spike trains.

    For each pair of spike trains :math:`(i,j)`, the covariance :math:`C[i,j]`
    is obtained by binning :math:`i` and :math:`j` at the desired bin size. Let
    :math:`b_i` and :math:`b_j` denote the binned spike trains and :math:`m_i`
    and :math:`m_j` their respective averages. Then

    .. math::
         C[i,j] = <b_i-m_i, b_j-m_j> / (l-1)

    where <..,.> is the scalar product of two vectors and :math:`l` is the
    number of bins.

    For an input of n spike trains, an n x n matrix is returned containing the
    covariances for each combination of input spike trains.

    If binary is True, the binned spike trains are clipped to 0 or 1 before
    computing the covariance, so that the binned vectors :math:`b_i` and
    :math:`b_j` are binary.

    Parameters
    ----------
    binned_sts : elephant.conversion.BinnedSpikeTrain
        A binned spike train containing the spike trains to be evaluated.
    binary : bool, optional
        If True, the spikes of a particular spike train falling in the same bin
        are counted as 1, resulting in binary binned vectors :math:`b_i`. If
        False, the binned vectors :math:`b_i` contain the spike counts per bin.
        Default: False

    Returns
    -------
    C : ndarrray
        The square matrix of covariances. The element :math:`C[i,j]=C[j,i]` is
        the covariance between binned_sts[i] and binned_sts[j].

    Examples
    --------
    Generate two Poisson spike trains

    >>> from elephant.spike_train_generation import homogeneous_poisson_process
    >>> st1 = homogeneous_poisson_process(
            rate=10.0*Hz, t_start=0.0*s, t_stop=10.0*s)
    >>> st2 = homogeneous_poisson_process(
            rate=10.0*Hz, t_start=0.0*s, t_stop=10.0*s)

    Calculate the covariance matrix.

    >>> from elephant.conversion import BinnedSpikeTrain
    >>> cov_matrix = covariance(BinnedSpikeTrain([st1, st2], binsize=5*ms))

    The covariance between the spike trains is stored in cc_matrix[0,1] (or
    cov_matrix[1,0]).

    Notes
    -----
    * The spike trains in the binned structure are assumed to all cover the
      complete time span of binned_sts [t_start,t_stop).
    '''
    return __calculate_correlation_or_covariance(
        binned_sts, binary, corrcoef_norm=False)


def corrcoef(binned_sts, binary=False):
    '''
    Calculate the NxN matrix of pairwise Pearson's correlation coefficients
    between all combinations of N binned spike trains.

    For each pair of spike trains :math:`(i,j)`, the correlation coefficient
    :math:`C[i,j]` is obtained by binning :math:`i` and :math:`j` at the
    desired bin size. Let :math:`b_i` and :math:`b_j` denote the binned spike
    trains and :math:`m_i` and :math:`m_j` their respective averages. Then

    .. math::
         C[i,j] = <b_i-m_i, b_j-m_j> /
                      \sqrt{<b_i-m_i, b_i-m_i>*<b_j-m_j,b_j-m_j>}

    where <..,.> is the scalar product of two vectors.

    For an input of n spike trains, an n x n matrix is returned.
    Each entry in the matrix is a real number ranging between -1 (perfectly
    anti-correlated spike trains) and +1 (perfectly correlated spike trains).
    However, if k-th spike train is empty, k-th row and k-th column of the
    returned matrix are set to NaN.

    If binary is True, the binned spike trains are clipped to 0 or 1 before
    computing the correlation coefficients, so that the binned vectors
    :math:`b_i` and :math:`b_j` are binary.

    Parameters
    ----------
    binned_sts : elephant.conversion.BinnedSpikeTrain
        A binned spike train containing the spike trains to be evaluated.
    binary : bool, optional
        If True, two spikes of a particular spike train falling in the same bin
        are counted as 1, resulting in binary binned vectors :math:`b_i`. If
        False, the binned vectors :math:`b_i` contain the spike counts per bin.
        Default: False

    Returns
    -------
    C : ndarrray
        The square matrix of correlation coefficients. The element
        :math:`C[i,j]=C[j,i]` is the Pearson's correlation coefficient between
        binned_sts[i] and binned_sts[j]. If binned_sts contains only one
        SpikeTrain, C=1.0.

    Examples
    --------
    Generate two Poisson spike trains

    >>> from elephant.spike_train_generation import homogeneous_poisson_process
    >>> from quantities import s, Hz
    >>> import neo
    >>> st1 = homogeneous_poisson_process(
            rate=10.0*Hz, t_start=0.0*s, t_stop=10.0*s)
    >>> st2 = homogeneous_poisson_process(
            rate=10.0*Hz, t_start=0.0*s, t_stop=10.0*s)

    Calculate the correlation matrix.

    >>> from elephant.conversion import BinnedSpikeTrain
    >>> cc_matrix = corrcoef(BinnedSpikeTrain([st1, st2], binsize=5*ms))

    The correlation coefficient between the spike trains is stored in
    cc_matrix[0,1] (or cc_matrix[1,0]).



    Notes
    -----
    * The spike trains in the binned structure are assumed to all cover the
      complete time span of binned_sts [t_start,t_stop).
    '''

    return __calculate_correlation_or_covariance(
        binned_sts, binary, corrcoef_norm=True)


def __calculate_correlation_or_covariance(binned_sts, binary, corrcoef_norm):
    '''
    Helper function for covariance() and corrcoef() that performs the complete
    calculation for either the covariance (corrcoef_norm=False) or correlation
    coefficient (corrcoef_norm=True). Both calculations differ only by the
    denominator.

    Parameters
    ----------
    binned_sts : elephant.conversion.BinnedSpikeTrain
        See covariance() or corrcoef(), respectively.
    binary : bool
        See covariance() or corrcoef(), respectively.
    corrcoef_norm : bool
        Use normalization factor for the correlation coefficient rather than
        for the covariance.
    '''
    num_neurons = binned_sts.matrix_rows

    # Pre-allocate correlation matrix
    C = np.zeros((num_neurons, num_neurons))

    # Retrieve unclipped matrix
    spmat = binned_sts.to_sparse_array()

    # Check for empty spike trains
    row_counts = spmat.getnnz(1)
    if row_counts.min() == 0:
        warnings.warn(
            'Detected empty spike trains (rows) in the argument binned_sts.')

    # For each row, extract the nonzero column indices and the corresponding
    # data in the matrix (for performance reasons)
    bin_idx_unique = []
    bin_counts_unique = []
    if binary:
        for s in spmat:
            bin_idx_unique.append(s.nonzero()[1])
    else:
        for s in spmat:
            bin_counts_unique.append(s.data)

    # All combinations of spike trains
    for i in range(num_neurons):
        for j in range(i, num_neurons):
            if row_counts[j] == 0:
                C[j, :] = np.NaN
                C[:, j] = np.NaN
                break
            # Enumerator:
            # $$ <b_i-m_i, b_j-m_j>
            #      = <b_i, b_j> + l*m_i*m_j - <b_i, M_j> - <b_j, M_i>
            #      =:    ij     + l*m_i*m_j - n_i * m_j  - n_j * m_i
            #      =     ij     - n_i*n_j/l                         $$
            # where $n_i$ is the spike count of spike train $i$,
            # $l$ is the number of bins used (i.e., length of $b_i$ or $b_j$),
            # and $M_i$ is a vector [m_i, m_i,..., m_i].
            if binary:
                # Intersect indices to identify number of coincident spikes in
                # i and j (more efficient than directly using the dot product)
                ij = len(np.intersect1d(
                    bin_idx_unique[i], bin_idx_unique[j], assume_unique=True))

                # Number of spikes in i and j
                n_i = len(bin_idx_unique[i])
                n_j = len(bin_idx_unique[j])
            else:
                # Calculate dot product b_i*b_j between unclipped matrices
                ij = spmat[i].dot(spmat[j].transpose()).toarray()[0][0]

                # Number of spikes in i and j
                n_i = np.sum(bin_counts_unique[i])
                n_j = np.sum(bin_counts_unique[j])

            enumerator = ij - n_i * n_j / binned_sts.num_bins

            # Denominator:
            if corrcoef_norm:
                # Correlation coefficient

                # Note:
                # $$ <b_i-m_i, b_i-m_i>
                #      = <b_i, b_i> + m_i^2 - 2 <b_i, M_i>
                #      =:    ii     + m_i^2 - 2 n_i * m_i
                #      =     ii     - n_i^2 /               $$
                if binary:
                    # Here, b_i*b_i is just the number of filled bins (since
                    # each filled bin of a clipped spike train has value equal
                    # to 1)
                    ii = len(bin_idx_unique[i])
                    jj = len(bin_idx_unique[j])
                else:
                    # directly calculate the dot product based on the counts of
                    # all filled entries (more efficient than using the dot
                    # product of the rows of the sparse matrix)
                    ii = np.dot(bin_counts_unique[i], bin_counts_unique[i])
                    jj = np.dot(bin_counts_unique[j], bin_counts_unique[j])

                denominator = np.sqrt(
                    (ii - (n_i ** 2) / binned_sts.num_bins) *
                    (jj - (n_j ** 2) / binned_sts.num_bins))
            else:
                # Covariance

                # $$ l-1 $$
                denominator = (binned_sts.num_bins - 1)

            # Fill entry of correlation matrix
            C[i, j] = C[j, i] = enumerator / denominator
    return np.squeeze(C)


def cross_correlation_histogram(
        binned_st1, binned_st2, window='full', border_correction=False,
        binary=False, kernel=None, method='speed', cross_corr_coef=False):
    """
    Computes the cross-correlation histogram (CCH) between two binned spike
    trains binned_st1 and binned_st2.

    Parameters
    ----------
    binned_st1, binned_st2 : BinnedSpikeTrain
        Binned spike trains to cross-correlate. The two spike trains must have
        same t_start and t_stop
    window : string or list of integer (optional)
        ‘full’: This returns the crosscorrelation at each point of overlap,
        with an output shape of (N+M-1,). At the end-points of the
        cross-correlogram, the signals do not overlap completely, and
        boundary effects may be seen.
        ‘valid’: Mode valid returns output of length max(M, N) - min(M, N) + 1.
        The cross-correlation product is only given for points where the
        signals overlap completely.
        Values outside the signal boundary have no effect.
        list of integer (window[0]=minimum lag, window[1]=maximum lag): The
        entries of window are two integers representing the left and
        right extremes (expressed as number of bins) where the
        crosscorrelation is computed
        Default: 'full'
    border_correction : bool (optional)
        whether to correct for the border effect. If True, the value of the
        CCH at bin b (for b=-H,-H+1, ...,H, where H is the CCH half-length)
        is multiplied by the correction factor:
                            (H+1)/(H+1-|b|),
        which linearly corrects for loss of bins at the edges.
        Default: False
    binary : bool (optional)
        whether to binary spikes from the same spike train falling in the
        same bin. If True, such spikes are considered as a single spike;
        otherwise they are considered as different spikes.
        Default: False.
    kernel : array or None (optional)
        A one dimensional array containing an optional smoothing kernel applied
        to the resulting CCH. The length N of the kernel indicates the
        smoothing window. The smoothing window cannot be larger than the
        maximum lag of the CCH. The kernel is normalized to unit area before
        being applied to the resulting CCH. Popular choices for the kernel are
          * normalized boxcar kernel: numpy.ones(N)
          * hamming: numpy.hamming(N)
          * hanning: numpy.hanning(N)
          * bartlett: numpy.bartlett(N)
        If None is specified, the CCH is not smoothed.
        Default: None
    method : string (optional)
        Defines the algorithm to use. "speed" uses numpy.correlate to calculate
        the correlation between two binned spike trains using a non-sparse data
        representation. Due to various optimizations, it is the fastest
        realization. In contrast, the option "memory" uses an own
        implementation to calculate the correlation based on sparse matrices,
        which is more memory efficient but slower than the "speed" option.
        Default: "speed"
    cross_corr_coef : bool (optional)
        Normalizes the CCH to obtain the cross-correlation  coefficient
        function ranging from -1 to 1 according to Equation (5.10) in
        "Analysis of parallel spike trains", 2010, Gruen & Rotter, Vol 7

    Returns
    -------
    cch : AnalogSignal
        Containing the cross-correlation histogram between binned_st1 and
        binned_st2.

        The central bin of the histogram represents correlation at zero
        delay. Offset bins correspond to correlations at a delay equivalent
        to the difference between the spike times of binned_st1 and those of
        binned_st2: an entry at positive lags corresponds to a spike in
        binned_st2 following a spike in binned_st1 bins to the right, and an
        entry at negative lags corresponds to a spike in binned_st1 following
        a spike in binned_st2.

        To illustrate this definition, consider the two spike trains:
        binned_st1: 0 0 0 0 1 0 0 0 0 0 0
        binned_st2: 0 0 0 0 0 0 0 1 0 0 0
        Here, the CCH will have an entry of 1 at lag h=+3.

        Consistent with the definition of AnalogSignals, the time axis
        represents the left bin borders of each histogram bin. For example,
        the time axis might be:
        np.array([-2.5 -1.5 -0.5 0.5 1.5]) * ms
    bin_ids : ndarray of int
        Contains the IDs of the individual histogram bins, where the central
        bin has ID 0, bins the left have negative IDs and bins to the right
        have positive IDs, e.g.,:
        np.array([-3, -2, -1, 0, 1, 2, 3])

    Example
    -------
        Plot the cross-correlation histogram between two Poisson spike trains
        >>> import elephant
        >>> import matplotlib.pyplot as plt
        >>> import quantities as pq

        >>> binned_st1 = elephant.conversion.BinnedSpikeTrain(
                elephant.spike_train_generation.homogeneous_poisson_process(
                    10. * pq.Hz, t_start=0 * pq.ms, t_stop=5000 * pq.ms),
                binsize=5. * pq.ms)
        >>> binned_st2 = elephant.conversion.BinnedSpikeTrain(
                elephant.spike_train_generation.homogeneous_poisson_process(
                    10. * pq.Hz, t_start=0 * pq.ms, t_stop=5000 * pq.ms),
                binsize=5. * pq.ms)

        >>> cc_hist = \
            elephant.spike_train_correlation.cross_correlation_histogram(
                binned_st1, binned_st2, window=[-30,30],
                border_correction=False,
                binary=False, kernel=None, method='memory')

        >>> plt.bar(
                left=cc_hist[0].times.magnitude,
                height=cc_hist[0][:, 0].magnitude,
                width=cc_hist[0].sampling_period.magnitude)
        >>> plt.xlabel('time (' + str(cc_hist[0].times.units) + ')')
        >>> plt.ylabel('cross-correlation histogram')
        >>> plt.axis('tight')
        >>> plt.show()

    Alias
    -----
    cch
    """

    def _cross_corr_coef(cch_result, binned_st1, binned_st2):
        # Normalizes the CCH to obtain the cross-correlation
        # coefficient function ranging from -1 to 1
        N = max(binned_st1.num_bins, binned_st2.num_bins)
        Nx = len(binned_st1.spike_indices[0])
        Ny = len(binned_st2.spike_indices[0])
        spmat = [binned_st1.to_sparse_array(), binned_st2.to_sparse_array()]
        bin_counts_unique = []
        for s in spmat:
            bin_counts_unique.append(s.data)
        ii = np.dot(bin_counts_unique[0], bin_counts_unique[0])
        jj = np.dot(bin_counts_unique[1], bin_counts_unique[1])
        rho_xy = (cch_result - Nx * Ny / N) / \
            np.sqrt((ii - Nx**2. / N) * (jj - Ny**2. / N))
        return rho_xy

    def _border_correction(counts, max_num_bins, l, r):
        # Correct the values taking into account lacking contributes
        # at the edges
        correction = float(max_num_bins + 1) / np.array(
            max_num_bins + 1 - abs(
                np.arange(l, r + 1)), float)
        return counts * correction

    def _kernel_smoothing(counts, kern, l, r):
        # Define the kern for smoothing as an ndarray
        if hasattr(kern, '__iter__'):
            if len(kern) > np.abs(l) + np.abs(r) + 1:
                raise ValueError(
                    'The length of the kernel cannot be larger than the '
                    'length %d of the resulting CCH.' % (
                        np.abs(l) + np.abs(r) + 1))
            kern = np.array(kern, dtype=float)
            kern = 1. * kern / sum(kern)
        # Check kern parameter
        else:
            raise ValueError('Invalid smoothing kernel.')

        # Smooth the cross-correlation histogram with the kern
        return np.convolve(counts, kern, mode='same')

    def _cch_memory(binned_st1, binned_st2, left_edge, right_edge,
                    border_corr, binary, kern):

        # Retrieve unclipped matrix
        st1_spmat = binned_st1.to_sparse_array()
        st2_spmat = binned_st2.to_sparse_array()

        # For each row, extract the nonzero column indices
        # and the corresponding # data in the matrix (for performance reasons)
        st1_bin_idx_unique = st1_spmat.nonzero()[1]
        st2_bin_idx_unique = st2_spmat.nonzero()[1]

        # Case with binary entries
        if binary:
            st1_bin_counts_unique = np.array(st1_spmat.data > 0, dtype=int)
            st2_bin_counts_unique = np.array(st2_spmat.data > 0, dtype=int)
        # Case with all values
        else:
            st1_bin_counts_unique = st1_spmat.data
            st2_bin_counts_unique = st2_spmat.data

        # Initialize the counts to an array of zeroes,
        # and the bin IDs to integers
        # spanning the time axis
        counts = np.zeros(np.abs(left_edge) + np.abs(right_edge) + 1)
        bin_ids = np.arange(left_edge, right_edge + 1)
        # Compute the CCH at lags in left_edge,...,right_edge only
        for idx, i in enumerate(st1_bin_idx_unique):
            il = np.searchsorted(st2_bin_idx_unique, left_edge + i)
            ir = np.searchsorted(st2_bin_idx_unique,
                                 right_edge + i, side='right')
            timediff = st2_bin_idx_unique[il:ir] - i
            assert ((timediff >= left_edge) & (
                timediff <= right_edge)).all(), 'Not all the '
            'entries of cch lie in the window'
            counts[timediff + np.abs(left_edge)] += (
                    st1_bin_counts_unique[idx] * st2_bin_counts_unique[il:ir])
            st2_bin_idx_unique = st2_bin_idx_unique[il:]
            st2_bin_counts_unique = st2_bin_counts_unique[il:]
        # Border correction
        if border_corr is True:
            counts = _border_correction(
                counts, max_num_bins, left_edge, right_edge)
        if kern is not None:
            # Smoothing
            counts = _kernel_smoothing(counts, kern, left_edge, right_edge)
        # Transform the array count into an AnalogSignal
        cch_result = neo.AnalogSignal(
            signal=counts.reshape(counts.size, 1),
            units=pq.dimensionless,
            t_start=(bin_ids[0] - 0.5) * binned_st1.binsize,
            sampling_period=binned_st1.binsize)
        # Return only the hist_bins bins and counts before and after the
        # central one
        return cch_result, bin_ids

    def _cch_speed(binned_st1, binned_st2, left_edge, right_edge, cch_mode,
                   border_corr, binary, kern):

        # Retrieve the array of the binne spike train
        st1_arr = binned_st1.to_array()[0, :]
        st2_arr = binned_st2.to_array()[0, :]

        # Convert the to binary version
        if binary:
            st1_arr = np.array(st1_arr > 0, dtype=int)
            st2_arr = np.array(st2_arr > 0, dtype=int)
        if cch_mode == 'pad':
            # Zero padding to stay between left_edge and right_edge
            st1_arr = np.pad(st1_arr,
                             (int(np.abs(np.min([left_edge, 0]))), np.max(
                                 [right_edge, 0])),
                             mode='constant')
            cch_mode = 'valid'
        # Cross correlate the spike trains
        counts = np.correlate(st2_arr, st1_arr, mode=cch_mode)
        bin_ids = np.r_[left_edge:right_edge + 1]
        # Border correction
        if border_corr is True:
            counts = _border_correction(
                counts, max_num_bins, left_edge, right_edge)
        if kern is not None:
            # Smoothing
            counts = _kernel_smoothing(counts, kern, left_edge, right_edge)
        # Transform the array count into an AnalogSignal
        cch_result = neo.AnalogSignal(
            signal=counts.reshape(counts.size, 1),
            units=pq.dimensionless,
            t_start=(bin_ids[0] - 0.5) * binned_st1.binsize,
            sampling_period=binned_st1.binsize)
        # Return only the hist_bins bins and counts before and after the
        # central one
        return cch_result, bin_ids

    # Check that the spike trains are binned with the same temporal
    # resolution
    if not binned_st1.matrix_rows == 1:
        raise AssertionError("Spike train must be one dimensional")
    if not binned_st2.matrix_rows == 1:
        raise AssertionError("Spike train must be one dimensional")
    if not binned_st1.binsize == binned_st2.binsize:
        raise AssertionError("Bin sizes must be equal")

    # Check t_start and t_stop identical (to drop once that the
    # pad functionality wil be available in the BinnedSpikeTrain classe)
    if not binned_st1.t_start == binned_st2.t_start:
        raise AssertionError("Spike train must have same t start")
    if not binned_st1.t_stop == binned_st2.t_stop:
        raise AssertionError("Spike train must have same t stop")

    # The maximum number of of bins
    max_num_bins = max(binned_st1.num_bins, binned_st2.num_bins)

    # Set the time window in which is computed the cch
    # Window parameter given in number of bins (integer)
    if isinstance(window[0], int) and isinstance(window[1], int):
        # Check the window parameter values
        if window[0] >= window[1] or window[0] <= -max_num_bins \
                or window[1] >= max_num_bins:
            raise ValueError(
                "The window exceeds the length of the spike trains")
        # Assign left and right edges of the cch
        left_edge, right_edge = window[0], window[1]
        # The mode in which to compute the cch for the speed implementation
        cch_mode = 'pad'
    # Case without explicit window parameter
    elif window == 'full':
        # cch computed for all the possible entries
        # Assign left and right edges of the cch
        right_edge = binned_st2.num_bins - 1
        left_edge = - binned_st1.num_bins + 1
        cch_mode = window
        # cch compute only for the entries that completely overlap
    elif window == 'valid':
        # cch computed only for valid entries
        # Assign left and right edges of the cch
        right_edge = max(binned_st2.num_bins - binned_st1.num_bins, 0)
        left_edge = min(binned_st2.num_bins - binned_st1.num_bins, 0)
        cch_mode = window
    # Check the mode parameter
    else:
        raise KeyError("Invalid window parameter")

    if method == "memory":
        cch_result, bin_ids = _cch_memory(
            binned_st1, binned_st2, left_edge, right_edge, border_correction,
            binary, kernel)
    elif method == "speed":
        cch_result, bin_ids = _cch_speed(
            binned_st1, binned_st2, left_edge, right_edge, cch_mode,
            border_correction, binary, kernel)

    if cross_corr_coef:
        cch_result = _cross_corr_coef(cch_result, binned_st1, binned_st2)

    return cch_result, bin_ids


# Alias for common abbreviation
cch = cross_correlation_histogram


def spike_time_tiling_coefficient(spiketrain_1, spiketrain_2, dt=0.005 * pq.s):
    """
    Calculates the Spike Time Tiling Coefficient (STTC) as described in
    (Cutts & Eglen, 2014) following Cutts' implementation in C.
    The STTC is a pairwise measure of correlation between spike trains.
    It has been proposed as a replacement for the correlation index as it
    presents several advantages (e.g. it's not confounded by firing rate,
    appropriately distinguishes lack of correlation from anti-correlation,
    periods of silence don't add to the correlation and it's sensitive to
    firing patterns).

    The STTC is calculated as follows:

    .. math::
        STTC = 1/2((PA - TB)/(1 - PA*TB) + (PB - TA)/(1 - PB*TA))

    Where `PA` is the proportion of spikes from train 1 that lie within
    `[-dt, +dt]` of any spike of train 2 divided by the total number of spikes
    in train 1, `PB` is the same proportion for the spikes in train 2;
    `TA` is the proportion of total recording time within `[-dt, +dt]` of any
    spike in train 1, TB is the same proportion for train 2.
    For :math:`TA = PB = 1`and for :math:`TB = PA = 1`
    the resulting :math:`0/0` is replaced with :math:`1`,
    since every spike from the train with :math:`T = 1` is within
    `[-dt, +dt]` of a spike of the other train.

    This is a Python implementation compatible with the elephant library of
    the original code by C. Cutts written in C and avaiable at:
    (https://github.com/CCutts/Detecting_pairwise_correlations_in_spike_trains/blob/master/spike_time_tiling_coefficient.c)

    Parameters
    ----------
    spiketrain_1, spiketrain_2: neo.Spiketrain objects to cross-correlate.
        Must have the same t_start and t_stop.
    dt: Python Quantity.
        The synchronicity window is used for both: the quantification of the
        proportion of total recording time that lies [-dt, +dt] of each spike
        in each train and the proportion of spikes in `spiketrain_1` that lies
        `[-dt, +dt]` of any spike in `spiketrain_2`.
        Default : 0.005 * pq.s

    Returns
    -------
    index:  float
        The spike time tiling coefficient (STTC). Returns np.nan if any spike
        train is empty.

    References
    ----------
    Cutts, C. S., & Eglen, S. J. (2014). Detecting Pairwise Correlations in
    Spike Trains: An Objective Comparison of Methods and Application to the
    Study of Retinal Waves. Journal of Neuroscience, 34(43), 14288–14303.
    """

    def run_P(spiketrain_1, spiketrain_2):
        """
        Check every spike in train 1 to see if there's a spike in train 2
        within dt
        """
        N2 = len(spiketrain_2)

        # Search spikes of spiketrain_1 in spiketrain_2
        # ind will contain index of
        ind = np.searchsorted(spiketrain_2.times, spiketrain_1.times)

        # To prevent IndexErrors
        # If a spike of spiketrain_1 is after the last spike of spiketrain_2,
        # the index is N2, however spiketrain_2[N2] raises an IndexError.
        # By shifting this index, the spike of spiketrain_1 will be compared
        # to the last 2 spikes of spiketrain_2 (negligible overhead).
        # Note: Not necessary for index 0 that will be shifted to -1,
        # because spiketrain_2[-1] is valid (additional negligible comparison)
        ind[ind == N2] = N2 - 1

        # Compare to nearest spike in spiketrain_2 BEFORE spike in spiketrain_1
        close_left = np.abs(
            spiketrain_2.times[ind - 1] - spiketrain_1.times) <= dt
        # Compare to nearest spike in spiketrain_2 AFTER (or simultaneous)
        # spike in spiketrain_2
        close_right = np.abs(
            spiketrain_2.times[ind] - spiketrain_1.times) <= dt

        # spiketrain_2 spikes that are in [-dt, dt] range of spiketrain_1
        # spikes are counted only ONCE (as per original implementation)
        close = close_left + close_right

        # Count how many spikes in spiketrain_1 have a "partner" in
        # spiketrain_2
        return np.count_nonzero(close)

    def run_T(spiketrain):
        """
        Calculate the proportion of the total recording time 'tiled' by spikes.
        """
        N = len(spiketrain)
        time_A = 2 * N * dt  # maximum possible time

        if N == 1:  # for just one spike in train
            if spiketrain[0] - spiketrain.t_start < dt:
                time_A += -dt + spiketrain[0] - spiketrain.t_start
            if spiketrain[0] + dt > spiketrain.t_stop:
                time_A += -dt - spiketrain[0] + spiketrain.t_stop
        else:  # if more than one spike in train
            # Vectorized loop of spike time differences
            diff = np.diff(spiketrain)
            diff_overlap = diff[diff < 2 * dt]
            # Subtract overlap
            time_A += -2 * dt * len(diff_overlap) + np.sum(diff_overlap)

            # check if spikes are within dt of the start and/or end
            # if so subtract overlap of first and/or last spike
            if (spiketrain[0] - spiketrain.t_start) < dt:
                time_A += spiketrain[0] - dt - spiketrain.t_start

            if (spiketrain.t_stop - spiketrain[N - 1]) < dt:
                time_A += -spiketrain[-1] - dt + spiketrain.t_stop

        T = time_A / (spiketrain.t_stop - spiketrain.t_start)
        return T.simplified.item()  # enforce simplification, strip units

    N1 = len(spiketrain_1)
    N2 = len(spiketrain_2)

    if N1 == 0 or N2 == 0:
        index = np.nan
    else:
        TA = run_T(spiketrain_1)
        TB = run_T(spiketrain_2)
        PA = run_P(spiketrain_1, spiketrain_2)
        PA = PA / N1
        PB = run_P(spiketrain_2, spiketrain_1)
        PB = PB / N2
        # check if the P and T values are 1 to avoid division by zero
        # This only happens for TA = PB = 1 and/or TB = PA = 1,
        # which leads to 0/0 in the calculation of the index.
        # In those cases, every spike in the train with P = 1
        # is within dt of a spike in the other train,
        # so we set the respective (partial) index to 1.
        if PA * TB == 1:
            if PB * TA == 1:
                index = 1.
            else:
                index = 0.5 + 0.5 * (PB - TA) / (1 - PB * TA)
        elif PB * TA == 1:
            index = 0.5 + 0.5 * (PA - TB) / (1 - PA * TB)
        else:
            index = 0.5 * (PA - TB) / (1 - PA * TB) + 0.5 * (PB - TA) / (
                    1 - PB * TA)
    return index


sttc = spike_time_tiling_coefficient
