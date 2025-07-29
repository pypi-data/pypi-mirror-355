"""
This module provides simple visualization functions for displaying data in a notebook or saving plots.
It includes utilities for drawing histograms, heatmaps, line graphs, and histograms with Gaussian fits.
The module leverages Matplotlib and Seaborn for creating visualizations.
"""
from typing import Optional

import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

from . import fitting


def draw_hist(
    data: np.ndarray,
    file_name: str = "histogram",
    save_to: Optional[str] = None,
    log: bool = False,
    **kwargs,
) -> None:
    """
    Draw a histogram of the data. If a folder is provided, the plot is saved.
    Args:
        data: np.array in any shape
        file_name: str (optional) default is "histogram"
        save_to: str (optional) default is None
        log: bool (optional) default
        **kwargs: (optional) passed to plt.hist
    """
    plt.clf()
    plt.hist(data.ravel(), **kwargs)
    if log:
        plt.yscale("log")
    if save_to is not None:
        plt.savefig(save_to + file_name + ".png")
        plt.close()
    else:
        plt.show()


def draw_heatmap(
    data: np.ndarray,
    file_name: str = "heatmap",
    save_to: Optional[str] = None,
    **kwargs,
) -> None:
    """
    Draw a heatmap of the data. If a folder is provided, the plot is saved.
    Args:
        data: np.array in 2 dimensions
        file_name
        save_to
        **kwargs: is passed to plt.hist
    """
    if data.ndim != 2:
        raise ValueError("Input data is not a 2D array.")
    plt.clf()
    cmap = kwargs.get("cmap", "coolwarm")
    sns.heatmap(data, cmap=cmap, **kwargs)
    if save_to is not None:
        plt.savefig(save_to + file_name + ".png")
        plt.close()
    else:
        plt.show()


def draw_graph(data: np.ndarray, file_name: str = "graph", save_to: Optional[str] = None, **kwargs) -> None:
    """
    Draw a graph of the data. If a folder is provided, the plot is saved.
    """
    plt.clf()
    plt.plot(data.ravel(), **kwargs)
    if save_to is not None:
        plt.savefig(save_to + file_name + ".png")
        plt.close()
    else:
        plt.show()


def draw_hist_and_gauss_fit(
    data: np.ndarray,
    bins: int,
    amplitude: float,
    mean: float,
    sigma: float,
    file_name: Optional[str] = None,
    save_to: Optional[str] = None,
) -> None:
    """
    Draw a histogram of the data and a gaussian fit
    """
    plt.clf()
    _, hist_bins = np.histogram(data, bins, range=(np.nanmin(data), np.nanmax(data)), density=True)
    bin_centers = (hist_bins[:-1] + hist_bins[1:]) / 2
    plt.hist(data, bins=hist_bins.tolist(), density=True, alpha=0.5)
    plt.plot(bin_centers, fitting.gaussian(bin_centers, amplitude, mean, sigma), "r-")
    plt.title(f"Fitted parameters:\nMean: {mean:.2f}\nSigma: {sigma:.2f}")
    plt.xlabel("Value")
    plt.ylabel("Frequency")
    if save_to is not None:
        if file_name is None:
            file_name = "hist_and_fit"
        plt.savefig(save_to + "/" + file_name + ".png")
        plt.close()
    else:
        plt.show()
