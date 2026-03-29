import numpy as np
from scipy.signal import butter, filtfilt, find_peaks

def bandpass_filter(signal, fs=30, low=0.5, high=4.0, order=3):
    signal = np.asarray(signal, dtype=float)
    if len(signal) < 10:
        return signal
    nyq = 0.5 * fs
    lowcut = low / nyq
    highcut = high / nyq
    b, a = butter(order, [lowcut, highcut], btype="band")
    return filtfilt(b, a, signal)

def estimate_signal_quality(ppg_values):
    arr = np.asarray(ppg_values, dtype=float)
    if len(arr) < 10:
        return 0.0
    variability = np.std(arr)
    noise = np.mean(np.abs(np.diff(arr))) + 1e-6
    score = variability / noise
    return float(max(0.0, min(1.0, score / 10.0)))

def extract_ppg_features(ppg_values, fs=30):
    arr = np.asarray(ppg_values, dtype=float)
    if len(arr) < 10:
        return {
            "ppg_mean": 0.0,
            "ppg_std": 0.0,
            "hr_est": 0.0,
            "peak_count": 0,
            "ppg_quality_score": 0.0
        }

    filtered = bandpass_filter(arr, fs=fs)
    peaks, _ = find_peaks(filtered, distance=max(1, fs // 2))

    duration_sec = len(filtered) / fs
    hr_est = (len(peaks) / duration_sec) * 60 if duration_sec > 0 else 0.0

    return {
        "ppg_mean": float(np.mean(filtered)),
        "ppg_std": float(np.std(filtered)),
        "hr_est": float(hr_est),
        "peak_count": int(len(peaks)),
        "ppg_quality_score": round(estimate_signal_quality(filtered), 3)
    }
