"""Tools for Electrical Power Quality Analysis.


>>> wf = range(-10, 20)
>>> stats = power_quality_stats(wf)
>>> stats['total_power']
135
>>> stats['mean_power']
4.5



"""

import numpy as np


def power_quality_stats(wf):
    """Compute power quality statistics from a waveform."""
    return {
        'total_power': sum(wf),
        'mean_power': np.mean(wf),
        'std_power': np.std(wf),
        'max_power': np.max(wf),
        'min_power': np.min(wf),
        'median_power': np.median(wf),
        'p10_power': np.percentile(wf, 10),
        'p90_power': np.percentile(wf, 90),
        'p25_power': np.percentile(wf, 25),
        'p75_power': np.percentile(wf, 75),
        'p5_power': np.percentile(wf, 5),
        'p95_power': np.percentile(wf, 95),
    }
