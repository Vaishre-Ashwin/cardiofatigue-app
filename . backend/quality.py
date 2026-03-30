# quality.py

import numpy as np
from scipy.signal import find_peaks


def compute_snr(signal):
    """
    Estimate Signal-to-Noise Ratio (SNR)
    """
    signal = np.array(signal)

    signal_power = np.mean(signal ** 2)
    noise_power = np.var(signal - np.mean(signal))

    if noise_power == 0:
        return 0

    return signal_power / noise_power


def check_signal_quality(signal):
    """
    Advanced PPG signal quality assessment

    Returns:
    - quality_score (0 to 100)
    - is_valid (True / False)
    """

    if signal is None or len(signal) < 50:
        return 0, False

    signal = np.array(signal)

    score = 0

    # 🔹 1. Variability check
    std_dev = np.std(signal)
    if std_dev > 0.02:
        score += 20

    # 🔹 2. Peak detection (heartbeat presence)
    peaks, _ = find_peaks(signal, distance=10)

    if len(peaks) > 5:
        score += 20

    # 🔹 3. Peak consistency (interval regularity)
    if len(peaks) > 2:
        intervals = np.diff(peaks)
        interval_std = np.std(intervals)

        if interval_std < 20:
            score += 20

    # 🔹 4. Signal-to-noise ratio
    snr = compute_snr(signal)

    if snr > 1:
        score += 20

    # 🔹 5. Amplitude check
    amplitude = np.max(signal) - np.min(signal)

    if amplitude > 0.1:
        score += 20

    # 🔹 Final decision
    is_valid = score >= 50

    return score, is_valid
