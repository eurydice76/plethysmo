import numpy as np

from scipy.signal import find_peaks

def period_frequency(signal, dt):

    # Compute the period using maximum of autocorrelation
    # See here for info https://stackoverflow.com/questions/59265603/how-to-find-period-of-signal-autocorrelation-vs-fast-fourier-transform-vs-power
    acf = np.correlate(signal, signal, 'full')[-len(signal):]
        # Find the second-order differences
    inflection = np.diff(np.sign(np.diff(acf)))
    # Find where they are negative --> maximum
    peaks = (inflection < 0).nonzero()[0] + 1
    if peaks.size == 0:
        period = np.nan
    else:
        # Convert from index to time unit
        period = peaks[acf[peaks].argmax()]*dt

    frequency = 1.0/period

    # The frequency is converted in minute^-1
    frequency *= 60.0

    return (period, frequency)

def current_volume(signal, dt):

    # Retrieve the negative areas of the windowed interval
    comp = 0
    negative_intervals = []
    while comp < len(signal):
        v = signal[comp]
        if v < 0.0:
            comp1 = comp
            while comp1 < len(signal):
                v1 = signal[comp1]
                if v1 >= 0.0:
                    negative_intervals.append((comp, comp1))
                    comp = comp1
                    break
                comp1 += 1
        comp += 1

    if not negative_intervals:
        return np.nan
        
    current_volume = min([np.sum(signal[start:end]) for start,end in negative_intervals])*dt

    return current_volume

def expiratory_time(signal, dt):

    # Retrieve the positive areas of the windowed interval
    comp = 0
    positive_intervals = []
    while comp < len(signal):
        v = signal[comp]
        if v > 0.0:
            comp1 = comp
            while comp1 < len(signal):
                v1 = signal[comp1]
                if v1 <= 0.0:
                    positive_intervals.append((comp, comp1))
                    comp = comp1
                    break
                comp1 += 1
        comp += 1

    # The expiratory time is computed as the average of the interval length where the signal is positive
    time = np.average([(end - start)*dt for start,end in positive_intervals])

    # The expiratory time is converted in ms
    time *= 1.0e3

    return time

def inspiratory_time(signal, dt):

    # Retrieve the negative areas of the windowed interval
    comp = 0
    negative_intervals = []
    while comp < len(signal):
        v = signal[comp]
        if v < 0.0:
            comp1 = comp
            while comp1 < len(signal):
                v1 = signal[comp1]
                if v1 >= 0.0:
                    negative_intervals.append((comp, comp1))
                    comp = comp1
                    break
                comp1 += 1
        comp += 1

    # The inspiratory time is computed as the average of the interval length where the signal is negative
    time = np.average([(end - start)*dt for start,end in negative_intervals])

    # The inspiratory time is converted in ms
    time *= 1.0e3

    return time
