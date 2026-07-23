#!/usr/bin/env python3
"""Distributional, temporal, spectral, and spatial residual diagnostics."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import signal, stats


def standardize_channels(windows: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Standardize ``(windows, time, channels)`` values per channel."""
    values = np.asarray(windows, dtype=np.float64)
    if values.ndim != 3:
        raise ValueError("windows must have shape (windows, time, channels)")
    flattened = values.reshape(-1, values.shape[-1])
    means = flattened.mean(axis=0)
    scales = flattened.std(axis=0)
    if np.any(~np.isfinite(scales)) or np.any(scales <= 0):
        raise ValueError("every channel must have finite, nonzero variance")
    return (values - means[None, None, :]) / scales[None, None, :], means, scales


def temporal_autocorrelation(standardized: np.ndarray, max_lag: int) -> np.ndarray:
    """Estimate per-channel autocorrelation within disjoint windows."""
    values = np.asarray(standardized, dtype=np.float64)
    if values.ndim != 3:
        raise ValueError("standardized values must be three-dimensional")
    if max_lag < 1 or max_lag >= values.shape[1]:
        raise ValueError("max_lag must be between 1 and window_length - 1")
    autocorrelation = np.ones((values.shape[-1], max_lag + 1), dtype=np.float64)
    for lag in range(1, max_lag + 1):
        left = values[:, :-lag, :]
        right = values[:, lag:, :]
        numerator = np.einsum("wtc,wtc->c", left, right)
        denominator = np.sqrt(
            np.einsum("wtc,wtc->c", left, left)
            * np.einsum("wtc,wtc->c", right, right)
        )
        autocorrelation[:, lag] = np.divide(
            numerator,
            denominator,
            out=np.zeros_like(numerator),
            where=denominator > 0,
        )
    return autocorrelation


def ljung_box_pvalues(autocorrelation: np.ndarray, observations: int) -> np.ndarray:
    """Return the standard large-sample Ljung-Box p-value per channel."""
    values = np.asarray(autocorrelation, dtype=np.float64)
    if values.ndim != 2 or values.shape[1] < 2:
        raise ValueError("autocorrelation must contain lag zero and positive lags")
    lags = np.arange(1, values.shape[1], dtype=np.float64)
    if observations <= int(lags[-1]):
        raise ValueError("observations must exceed max_lag")
    statistic = observations * (observations + 2) * np.sum(
        values[:, 1:] ** 2 / (observations - lags)[None, :], axis=1
    )
    return stats.chi2.sf(statistic, df=len(lags))


def spatial_correlation(standardized: np.ndarray) -> np.ndarray:
    """Return the zero-lag channel correlation matrix."""
    values = np.asarray(standardized, dtype=np.float64)
    if values.ndim != 3:
        raise ValueError("standardized values must be three-dimensional")
    flattened = values.reshape(-1, values.shape[-1])
    return np.corrcoef(flattened, rowvar=False)


def welch_power(
    segments: np.ndarray,
    sampling_frequency: float,
    nperseg: int = 1024,
) -> tuple[np.ndarray, np.ndarray]:
    """Return segment-averaged Welch power as ``(frequency, channel)``."""
    values = np.asarray(segments, dtype=np.float64)
    if values.ndim != 3:
        raise ValueError("segments must have shape (segments, time, channels)")
    if sampling_frequency <= 0:
        raise ValueError("sampling_frequency must be positive")
    nperseg = min(int(nperseg), values.shape[1])
    frequencies, power = signal.welch(
        values,
        fs=sampling_frequency,
        axis=1,
        nperseg=nperseg,
        detrend="constant",
        scaling="density",
    )
    return frequencies, power.mean(axis=0)


def spectral_flatness(
    frequencies: np.ndarray,
    power: np.ndarray,
    lower_hz: float = 300.0,
    upper_hz: float = 7_500.0,
) -> np.ndarray:
    """Compute geometric-to-arithmetic mean power in the requested band."""
    frequencies = np.asarray(frequencies, dtype=np.float64)
    power = np.asarray(power, dtype=np.float64)
    keep = (frequencies >= lower_hz) & (frequencies <= upper_hz)
    if not np.any(keep):
        raise ValueError("requested spectral band contains no frequencies")
    selected = np.maximum(power[keep], np.finfo(np.float64).tiny)
    return np.exp(np.mean(np.log(selected), axis=0)) / np.mean(selected, axis=0)


def fdr_rejections(pvalues: np.ndarray, alpha: float = 0.05) -> np.ndarray:
    """Benjamini-Hochberg rejection mask."""
    values = np.asarray(pvalues, dtype=np.float64)
    if values.ndim != 1 or np.any(~np.isfinite(values)):
        raise ValueError("pvalues must be a finite one-dimensional array")
    order = np.argsort(values)
    ordered = values[order]
    thresholds = alpha * np.arange(1, len(values) + 1) / len(values)
    passing = np.flatnonzero(ordered <= thresholds)
    rejected = np.zeros(len(values), dtype=bool)
    if passing.size:
        rejected[order[: passing[-1] + 1]] = True
    return rejected


def analyze_domain(
    windows: np.ndarray,
    spectral_segments: np.ndarray,
    sampling_frequency: float,
    max_lag: int = 30,
) -> tuple[pd.DataFrame, dict[str, np.ndarray]]:
    """Compute per-channel tests plus arrays needed by the local renderer."""
    standardized, means, standard_deviations = standardize_channels(windows)
    flattened = standardized.reshape(-1, standardized.shape[-1])
    skewness = stats.skew(flattened, axis=0, bias=False)
    excess_kurtosis = stats.kurtosis(flattened, axis=0, fisher=True, bias=False)
    jarque_bera = stats.jarque_bera(flattened, axis=0)
    autocorrelation = temporal_autocorrelation(standardized, max_lag=max_lag)
    temporal_pvalues = ljung_box_pvalues(autocorrelation, observations=flattened.shape[0])
    correlations = spatial_correlation(standardized)
    frequencies, power = welch_power(spectral_segments, sampling_frequency)
    flatness = spectral_flatness(frequencies, power)
    probabilities = np.linspace(0.001, 0.999, 199)
    empirical_quantiles = np.quantile(flattened, probabilities, axis=0)
    normal_quantiles = stats.norm.ppf(probabilities)
    quantile_rmse = np.sqrt(
        np.mean((empirical_quantiles - normal_quantiles[:, None]) ** 2, axis=0)
    )
    histogram_edges = np.linspace(-8.0, 8.0, 321)
    histogram_density, _ = np.histogram(
        flattened.ravel(), bins=histogram_edges, density=True
    )

    channel_table = pd.DataFrame(
        {
            "channel_index": np.arange(flattened.shape[1]),
            "mean": means,
            "std": standard_deviations,
            "skewness": skewness,
            "excess_kurtosis": excess_kurtosis,
            "normal_quantile_rmse": quantile_rmse,
            "fraction_abs_gt_3": np.mean(np.abs(flattened) > 3, axis=0),
            "fraction_abs_gt_5": np.mean(np.abs(flattened) > 5, axis=0),
            "jarque_bera_statistic": jarque_bera.statistic,
            "jarque_bera_pvalue": jarque_bera.pvalue,
            "jarque_bera_fdr_reject": fdr_rejections(jarque_bera.pvalue),
            "mean_abs_autocorrelation": np.mean(np.abs(autocorrelation[:, 1:]), axis=1),
            "max_abs_autocorrelation": np.max(np.abs(autocorrelation[:, 1:]), axis=1),
            "ljung_box_pvalue": temporal_pvalues,
            "ljung_box_fdr_reject": fdr_rejections(temporal_pvalues),
            "spectral_flatness": flatness,
        }
    )
    arrays = {
        "autocorrelation": autocorrelation,
        "spatial_correlation": correlations,
        "frequencies_hz": frequencies,
        "power": power,
        "normal_quantiles": normal_quantiles,
        "empirical_quantiles": empirical_quantiles,
        "histogram_edges": histogram_edges,
        "histogram_density": histogram_density,
    }
    return channel_table, arrays