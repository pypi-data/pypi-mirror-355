"""module description"""

import os
from datetime import datetime

import numpy as np

from . import utils
from . import analysis as an
from . import params
from . import fitting as fit
from . import file_io as io
from . import bin_to_h5

from .logger import global_logger

_logger = global_logger


class Analysis:
    """
    A base class for performing data analysis on HDF5 files.

    This class initializes the analysis environment by loading parameters from a
    configuration file, extracting metadata from the input HDF5 file, and creating
    an output HDF5 file for storing analysis results. It provides a foundation for
    specific analysis workflows by managing parameters, logging, and file handling.
    """

    def __init__(self, prm_file: str) -> None:
        self.prm_file = prm_file
        self.params = params.Params(prm_file)
        _logger.info("APANTIAS Instance initialized with parameter file: %s", prm_file)
        self.params.print_contents()

        # load values of parameter file
        self.params_dict = self.params.get_dict()
        self.results_dir = self.params_dict["results_dir"]
        self.data_h5 = self.params_dict["data_h5_file"]
        self.darkframe_dset = self.params_dict["darkframe_dset"]
        self.available_cpus = utils.get_cpu_count()
        self.available_ram_gb = utils.get_avail_ram_gb()
        self.custom_attributes = self.params_dict["custom_attributes"]
        self.nframes_eval = self.params_dict["nframes_eval"]
        self.thres_bad_slopes = self.params_dict["thres_bad_slopes"]
        self.thres_event_prim = self.params_dict["thres_event_prim"]
        self.thres_event_sec = self.params_dict["thres_event_sec"]
        self.ext_offsetmap = self.params_dict["ext_offsetmap"]
        self.ext_noisemap = self.params_dict["ext_noisemap"]

        _logger.info(f"CPUs available: {self.available_cpus}")
        _logger.info(f"RAM available: {self.available_ram_gb} GB")
        _logger.info("")

        # get parameters from data_h5 file
        self.total_frames, self.column_size, self.row_size, self.nreps = io._get_params_from_data_file(self.data_h5)

        # create analysis h5 file
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        bin_filename = os.path.basename(self.data_h5)[:-3]
        self.out_h5_name = f"{timestamp}_{bin_filename}.h5"
        self.out_h5 = os.path.join(self.results_dir, self.out_h5_name)
        io._create_analysis_file(
            self.results_dir, self.out_h5_name, self.params_dict, self.custom_attributes, self.data_h5
        )
        _logger.info("Created analysis h5 file: %s/%s", self.results_dir, self.out_h5_name)
        vds_list = io._get_all_datasets(self.data_h5)
        bin_to_h5._create_vds(self.out_h5, vds_list)
        _logger.info("Virtual datasets created in group '0_raw_data'")


class Default(Analysis):
    """ "
    A default implementation of the Analysis class for processing HDF5 data.

    This class extends the base Analysis class and provides a specific workflow for
    analyzing HDF5 data. It performs tasks such as calculating bad slopes, removing
    outliers, subtracting offsets, and generating event maps. The results are stored
    in an output HDF5 file, organized into different groups for clean and structured
    analysis.

    Key Features:
        - Fits Gaussian distributions to pixel data to identify bad slopes.
        - Removes bad slopes and outliers from the data.
        - Subtracts offsets and calculates cleaned pixel data.
        - Generates event maps based on primary and secondary thresholds.
        - Fits double Gaussian distributions to calculate gain parameters.

    Attributes:
        Inherits all attributes from the Analysis class.

    Methods:
        calculate():
            Executes the default analysis workflow, including bad slope detection,
            outlier removal, offset subtraction, event map generation, and gain fitting.
    """

    def __init__(self, prm_file: str) -> None:
        super().__init__(prm_file)
        _logger.info("Default analysis initialized")

    def calculate(self):
        """Function description"""
        _logger.info("Start calculating bad slopes map")
        slopes = io.get_data_from_file(self.data_h5, "preproc_slope_nreps")
        fitted = utils.apply_pixelwise(slopes, fit.fit_gauss_to_hist)
        _logger.info("Finished fitting")
        lower_bound = fitted[1, :, :] - self.thres_bad_slopes * np.abs(fitted[2, :, :])
        upper_bound = fitted[1, :, :] + self.thres_bad_slopes * np.abs(fitted[2, :, :])
        failed_fits_mask = np.isnan(fitted[1, :, :]) | np.isnan(fitted[2, :, :])
        bad_slopes_mask = (slopes < lower_bound) | (slopes > upper_bound)
        bad_pixels_mask = bad_slopes_mask | failed_fits_mask
        io.add_array(self.out_h5, fitted, "1_clean/slope_fit_parameters")
        io.add_array(self.out_h5, bad_pixels_mask, "1_clean/bad_slopes_mask")
        io.add_array(self.out_h5, np.sum(bad_pixels_mask, axis=0), "1_clean/bad_slopes_count")
        failed_fits = np.sum(np.isnan(fitted[:, :, 1]))
        if failed_fits > 0:
            _logger.warning(
                "Failed fits: %d (%.2f%%)", failed_fits, (failed_fits / (self.column_size * self.row_size) * 100)
            )
        data = io.get_data_from_file(self.data_h5, "preproc_mean_nreps")
        io.add_array(self.out_h5, data, "1_clean/preproc_pixel_data")  # rename this
        _logger.info("Removing bad slopes")
        data[bad_pixels_mask] = np.nan
        sum_bad_slopes = np.sum(bad_pixels_mask)
        _logger.warning(
            "Signals removed due to bad slopes: %d (%.2f%%)",
            sum_bad_slopes,
            (sum_bad_slopes / (bad_pixels_mask.size) * 100),
        )
        _logger.info("Removing outliers")
        fitted = utils.apply_pixelwise(data, fit.fit_gauss_to_hist)
        lower_bound = fitted[1, :, :] - 5 * np.abs(fitted[2, :, :])
        outlier_mask = data < lower_bound
        data[outlier_mask] = np.nan
        io.add_array(self.out_h5, data, "1_clean/cleaned_pixel_data")
        io.add_array(self.out_h5, outlier_mask, "1_clean/outlier_mask")
        sum_outliers = np.sum(outlier_mask)
        _logger.warning(
            "Signals removed due to outliers: %d (%.2f%%)", sum_outliers, (sum_outliers / (outlier_mask.size) * 100)
        )
        _logger.info("Fitting pixelwise")
        fitted = utils.apply_pixelwise(data, fit.fit_gauss_to_hist)
        io.add_array(self.out_h5, fitted, "2_offnoi/fit_parameters")
        offset = fitted[1]
        noise = fitted[2]
        _logger.info("Subtracting second offset")
        data -= offset[np.newaxis, :, :]
        io.add_array(self.out_h5, data, "2_offnoi/pixel_data")
        # _logger.info("Start Calculating event_map")
        # structure = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]])
        # event_map = an.group_pixels(data, self.thres_event_prim, self.thres_event_sec, noise, structure)
        # event_counts = event_map > 0
        # event_counts_sum = np.sum(event_counts, axis=0)
        # io.add_array(self.out_h5, event_map, "3_filter/event_map")
        # io.add_array(self.out_h5, event_counts, "3_filter/event_counts")
        # io.add_array(self.out_h5, event_counts_sum, "3_filter/event_counts_sum")
        _logger.info("Start Fitting Gain")
        fitted = utils.apply_pixelwise(data, fit.fit_2_gauss_to_hist)
        io.add_array(self.out_h5, fitted, "4_gain/fit_parameters")
        _logger.info("Analysis finished")
