*************
Release Notes
*************

Elephant 0.6.3 release notes
============================
July 22nd 2019

The release v0.6.3 is mostly about improving maintenance.

New functions
-------------
* `waveform_features` module
    * Waveform signal-to-noise ratio (https://github.com/NeuralEnsemble/elephant/pull/219).
* Added support for Butterworth `sosfiltfilt` - numerically stable (in particular, higher order) filtering (https://github.com/NeuralEnsemble/elephant/pull/234).

Buf fixes
---------
* Fixed neo version typo in requirements file (https://github.com/NeuralEnsemble/elephant/pull/218)
* Fixed broken docs (https://github.com/NeuralEnsemble/elephant/pull/230, https://github.com/NeuralEnsemble/elephant/pull/232)
* Fixed issue with 32-bit arch (https://github.com/NeuralEnsemble/elephant/pull/229)

Other changes
-------------
* Added issue templates (https://github.com/NeuralEnsemble/elephant/pull/226)
* Single VERSION file (https://github.com/NeuralEnsemble/elephant/pull/231)

Elephant 0.6.2 release notes
============================
April 23rd 2019

New functions
-------------
* `signal_processing` module
    * New functions to calculate the area under a time series and the derivative of a time series.

Other changes
-------------
* Added support to initialize binned spike train representations with a matrix
* Multiple bug fixes


Elephant 0.6.1 release notes
============================
April 1st 2019

New functions
-------------
* `signal_processing` module
    * New function to calculate the cross-correlation function for analog signals.
* `spade` module
    * Spatio-temporal spike pattern detection now includes the option to assess significance also based on time-lags of patterns, in addition to patterns size and frequency (referred to as 3D pattern spectrum).

Other changes
-------------
* This release fixes a number of compatibility issues in relation to API breaking changes in the Neo library.
* Fixed error in STTC calculation (spike time tiling coefficient)
* Minor bug fixes


Elephant 0.6.0 release notes
============================
October 12th 2018

New functions
-------------
* `cell_assembly_detection` module
    * New function to detect higher-order correlation structures such as patterns in parallel spike trains based on Russo et al, 2017.
*  **wavelet_transform()** function in `signal_prosessing.py` module
    * Function for computing wavelet transform of a given time series based on Le van Quyen et al. (2001)

Other changes
-------------
* Switched to multiple `requirements.txt` files which are directly read into the `setup.py`
* `instantaneous_rate()` accepts now list of spiketrains
* Minor bug fixes  


Elephant 0.5.0 release notes
============================
April 4nd 2018

New functions
-------------
* `change_point_detection` module:
    * New function to detect changes in the firing rate
* `spike_train_correlation` module:
    * New function to calculate the spike time tiling coefficient
* `phase_analysis` module:
    * New function to extract spike-triggered phases of an AnalogSignal
* `unitary_event_analysis` module:
    * Added new unit test to the UE function to verify the method based on data of a recent [Re]Science publication
  
Other changes
-------------
* Minor bug fixes
  
  
Elephant 0.4.3 release notes
============================
March 2nd 2018

Other changes
-------------
* Bug fixes in `spade` module:
    * Fixed an incompatibility with the latest version of an external library

  
Elephant 0.4.2 release notes
============================
March 1st 2018

New functions
-------------
* `spike_train_generation` module:
    * **inhomogeneous_poisson()** function
* Modules for Spatio Temporal Pattern Detection (SPADE) `spade_src`:
    * Module SPADE: `spade.py`
* Module `statistics.py`:
    * Added CV2 (coefficient of variation for non-stationary time series)
* Module `spike_train_correlation.py`:
    * Added normalization in **cross-correlation histogram()** (CCH)

Other changes
-------------
* Adapted the `setup.py` to automatically install the spade modules including the compiled `C` files `fim.so`
* Included testing environment for MPI in `travis.yml`
* Changed function arguments  in `current_source_density.py` to `neo.AnalogSignal` instead list of `neo.AnalogSignal` objects
* Fixes to travis and setup configuration files
* Fixed bug in ISI function `isi()`, `statistics.py` module
* Fixed bug in `dither_spikes()`, `spike_train_surrogates.py`
* Minor bug fixes
 
 
Elephant 0.4.1 release notes
============================
March 23rd 2017

Other changes
-------------
* Fix in `setup.py` to correctly import the current source density module


Elephant 0.4.0 release notes
============================
March 22nd 2017

New functions
-------------
* `spike_train_generation` module:
    * peak detection: **peak_detection()**
* Modules for Current Source Density: `current_source_density_src`
    * Module Current Source Density: `KCSD.py`
    * Module for Inverse Current Source Density: `icsd.py`

API changes
-----------
* Interoperability between Neo 0.5.0 and Elephant
    * Elephant has adapted its functions to the changes in Neo 0.5.0,
      most of the functionality behaves as before
    * See Neo documentation for recent changes: http://neo.readthedocs.io/en/latest/whatisnew.html

Other changes
-------------
* Fixes to travis and setup configuration files.
* Minor bug fixes.
* Added module `six` for Python 2.7 backwards compatibility


Elephant 0.3.0 release notes
============================
April 12st 2016

New functions
-------------
* `spike_train_correlation` module:
    * cross correlation histogram: **cross_correlation_histogram()**
* `spike_train_generation` module:
    * single interaction process (SIP): **single_interaction_process()**
    * compound Poisson process (CPP): **compound_poisson_process()**
* `signal_processing` module:
    * analytic signal: **hilbert()**
* `sta` module:
    * spike field coherence: **spike_field_coherence()**
* Module to represent kernels: `kernels` module
* Spike train metrics / dissimilarity / synchrony measures: `spike_train_dissimilarity` module
* Unitary Event (UE) analysis: `unitary_event_analysis` module
* Analysis of Sequences of Synchronous EvenTs (ASSET): `asset` module

API changes
-----------
* Function **instantaneous_rate()** now uses kernels as objects defined in the `kernels` module. The previous implementation of the function using the `make_kernel()` function is deprecated, but still temporarily available as `oldfct_instantaneous_rate()`.

Other changes
-------------
* Fixes to travis and readthedocs configuration files.


Elephant 0.2.1 release notes
============================
February 18th 2016

Other changes
-------------
Minor bug fixes.


Elephant 0.2.0 release notes
============================
September 22nd 2015

New functions
-------------
* Added covariance function **covariance()** in the `spike_train_correlation` module
* Added complexity pdf **complexity_pdf()** in the `statistics` module
* Added spike train extraction from analog signals via threshold detection the in `spike_train_generation` module
* Added **coherence()** function for analog signals in the `spectral` module
* Added **Cumulant Based Inference for higher-order of Correlation (CuBIC)** in the `cubic` module for correlation analysis of parallel recorded spike trains

API changes
-----------
* **Optimized kernel bandwidth** in `rate_estimation` function: Calculates the optimized kernel width when the paramter kernel width is specified as `auto`

Other changes
-------------
* **Optimized creation of sparse matrices**: The creation speed of the sparse matrix inside the `BinnedSpikeTrain` class is optimized
* Added **Izhikevich neuron simulator** in the `make_spike_extraction_test_data` module
* Minor improvements to the test and continous integration infrastructure
