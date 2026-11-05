"""Mergeable SB3 running moments for telemetry, never policy normalization."""
import numpy as np
from stable_baselines3.common.running_mean_std import RunningMeanStd


def merge(previous, values):
    rms=RunningMeanStd(epsilon=0)
    if previous:
        rms.mean=np.asarray(previous['mean']);rms.var=np.asarray(previous['variance']);rms.count=previous['count']
    data=np.asarray(values,dtype=float)
    if data.size:
        if not np.isfinite(data).all():raise ValueError('nonfinite telemetry')
        rms.update(data.reshape(-1))
    return dict(mean=float(rms.mean),variance=float(rms.var),count=float(rms.count))
