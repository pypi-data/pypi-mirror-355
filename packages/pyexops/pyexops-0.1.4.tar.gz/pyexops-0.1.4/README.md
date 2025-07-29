# pyExopS (Python Exoplanetary Systems Simulator)

`pyExopS` is a Python-based simulator designed to generate realistic observational data for exoplanetary systems. It aims to provide a flexible and extensible platform for studying phenomena like planetary transits, stellar activity, and various observational systematics.

## Features

-   **Realistic Star Model:** Includes quadratic limb darkening and dynamic stellar spots (umbra and penumbra).
-   **Planet Model:** Customizable orbiting planets with definable physical and orbital parameters.
-   **Advanced PSF Modeling:** Supports Gaussian, Moffat, Airy Disk, Elliptical Gaussian, and Combined Point Spread Functions to simulate realistic instrumental and atmospheric blurring.
-   **Noise Injection:** Injects Poisson (photon) noise and Gaussian (readout) noise for true-to-life data.
-   **Photometry Methods:** Implements various photometric extraction techniques:
    -   Simple Aperture Photometry (SAP)
    -   Optimal Photometry
    -   PSF Fitting Photometry
    -   Simplified Difference Imaging Photometry (DIP)
-   **Data Conditioning:** Includes a PDCSAP-like detrending algorithm to remove instrumental and astrophysical systematics from light curves while preserving transit signals.
-   **Variable Cadence:** Allows simulation of observations with non-uniform time sampling (e.g., high cadence during transit, low cadence out-of-transit).
-   **Parallel Processing:** Leverages Dask for efficient parallel computation across multicore CPUs, NVIDIA GPUs (Dask-CUDA), or distributed clusters.

## Installation

You can install `pyExopS` using pip:

```bash
pip install pyexops