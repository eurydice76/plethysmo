import collections
import re

import pyedflib as edf

import numpy as np

class EDFFileReaderError(Exception):
    """Error handler for EDFFileReader related exceptions.
    """

class EDFFileReader:
    """This class implements a reader for EDF file which contains plethysmography data.
    """

    def __init__(self, edf_filename):
        """Constructor
        """

        self._edf_filename = edf_filename

        try:
            self._edf_file = edf.EdfReader(edf_filename)
        except OSError as e:
            raise EDFFileReaderError from e
        else:
            # Fetch the sample frequency from the edf file
            self._sample_frequency = self._edf_file.getSampleFrequency(0)
            self._dt = 1.0/self._sample_frequency

        # Read the signal
        self._signal = self._edf_file.readSignal(0)

        # Autoscale the signal such as its limits become [-1,1]
        mini = self._signal.min()
        maxi = self._signal.max()
        self._signal -= mini
        self._signal /= (maxi-mini)
        self._signal -= 0.5
        self._signal *= 2.0

        # Rebuild the time axis from the period
        n_points = len(self._signal)
        self._times = np.arange(0,n_points*self._dt,self._dt)

        # The minimum duration for a valid interval (in seconds)
        self._signal_duration = 5.0

        # The separation between two valid intervals (in seconds)
        self._signal_separation = 15.0
        
        # The list of valid intervals (tuples of of the form (start,end))
        self._valid_intervals = []

        # The list of ROIs used to set up the intervals
        self._rois = []

        # The time zones for which the data will not be parsed when searching for valid intervals
        self._excluded_zones = []

    @property
    def dt(self):
        """Getter for _dt attribute.
        """

        return self._dt

    @property
    def edf_filename(self):
        """Getter for _edf_filename attribute.
        """

        return self._edf_filename

    @property
    def excluded_zones(self):
        """Getter for _excluded_zones attribute.
        """

        return self._excluded_zones

    @excluded_zones.setter
    def excluded_zones(self, excluded_zones):
        """Getter for _excluded_zones attribute.
        """

        self._excluded_zones = excluded_zones

    def get_filtered_signal(self, fmin, fmax):
        """Get the signal filtred using a pass-band filter.

        Args:
            fmin (double): the frequence min
            fmax (double): the frequence max
        """

        freqs = np.fft.fftfreq(len(self._times),d=self._dt)

        spectrum = np.fft.fft(self._signal)
        spectrum[abs(freqs) < fmin] = 0
        spectrum[abs(freqs) > fmax] = 0
        filtered_signal = np.fft.ifft(spectrum)

        return filtered_signal.real

    @property
    def frequencies(self):
        """Return the frequencies.

        Return:
            numpy.array: the frequencies
        """

        frequencies = np.fft.fftfreq(len(self._times),d=self._dt)

        return frequencies

    @property
    def metadata(self):
        """Return the formated header of the edf file.
        """

        header = self._edf_file.getHeader()

        if header['startdate']:
            header['startdate'] = header['startdate'].strftime('%Y/%m/%d - %H:%M:%S')

        if header['birthdate']:
            header['birthdate'] = header['birthdate'].strftime('%Y/%m/%d - %H:%M:%S')

        return '\n'.join([": ".join([k,v]) for k,v in header.items()])

    @property
    def parameters(self):
        """Return the parameters for searching for valid intervals.

        Return:
            dict: the parameters
        """

        params = collections.OrderedDict()
        params['signal duration'] = self._signal_duration
        params['signal separation'] = self._signal_separation

        return params

    @parameters.setter
    def parameters(self, params):
        """Set the parameters for searching for valid intervals.

        Args:
            params (dict): the parameters
        """

        try:
            self._signal_duration = float(params.get('signal duration',5))
            self._signal_separation = float(params.get('signal separation',15))
        except ValueError as e:
            raise EDFFileReaderError from e

    def reset_valid_intervals(self):
        """Reset the list of valid intervals.
        """

        self._valid_intervals = []

    @property
    def rois(self):
        """Getter for _rois attribute.
        """

        return self._rois

    @property
    def signal(self):
        """Getter for _signal attribute.
        """

        return self._signal

    @property
    def signal_duration(self):
        """Getter for _signal_duration attribute.
        """

        return self._signal_duration

    @signal_duration.setter
    def signal_duration(self, signal_duration):
        """Getter for _signal_duration attribute.
        """

        self._signal_duration = signal_duration

    @property
    def signal_separation(self):
        """Getter for _signal_separation attribute.
        """

        return self._signal_separation

    @signal_separation.setter
    def signal_separation(self, signal_separation):
        """Getter for _signal_separation attribute.
        """

        self._signal_separation = signal_separation

    @property
    def spectrum(self):
        """Return the real part of the spectrum.
        """

        return np.fft.fft(self._signal).real

    @property
    def times(self):
        """Getter for _times attribute.
        """

        return self._times

    def update_valid_intervals(self):
        """Update the valid intervals.
        """

        intervals = []

        # Loop over the ROI ans search for valid intervals inside
        for roi in self._rois:

            start_roi, threshold_min = roi.lower_corner
            # The roi unit is converted from time to index
            start_roi = int(start_roi/self._dt)
            start_roi = max(start_roi,0)

            end_roi, threshold_max = roi.upper_corner
            # The roi unit is converted from time to index
            end_roi = int(end_roi/self._dt)
            end_roi = min(end_roi,len(self._signal)-1)

            # Start the search from the beginning of the ROI
            comp = start_roi
            
            while comp < end_roi:

                s = self._signal[comp]

                # Case where the signal is between the threshold: start a second loop to find how many points are successively within between the threshold
                if s >= threshold_min and s <= threshold_max:
                    start = comp
                    comp1 = start
                    # Loop until the end of the ROI
                    while comp1 < end_roi:
                        s1 = self._signal[comp1]
                        # Case where the signal is out of the thresholds: the interval is closed and checked that its length is over the signal duration parameter
                        if s1 < threshold_min or s1 > threshold_max:
                            end = comp1
                            # Case where the signal is over the signal duration parameter: the interval is closed and kept
                            if (end - start)*self._dt > self._signal_duration:
                                intervals.append((start,end))
                            break
                        # Case where the signal is between the thresholds: checked that its length is over the signal duration parameter
                        else:
                            # If this is the case, the interval is closed and kept
                            if (comp1 - start)*self._dt > self._signal_duration:
                                end = comp1
                                intervals.append((start,end))
                                break

                        comp1 += 1
                    comp = comp1
                else:
                    comp += 1

        # Loop over the interval found so far and check that none of them fall within an excluded zone. If this is the case, the interval is not kept.
        valid_intervals = []
        for start, end in intervals:
            excluded_interval = False
            for roi in self._excluded_zones:

                start_roi, _ = roi.lower_corner
                # The roi unit is converted from time to index
                start_roi = int(start_roi/self._dt)
                start_roi = max(start_roi,0)

                end_roi, _ = roi.upper_corner
                # The roi unit is converted from time to index
                end_roi = int(end_roi/self._dt)
                end_roi = min(end_roi,len(self._signal)-1)
                
                if (end >= start_roi and start <= end_roi):
                    excluded_interval = True

            if excluded_interval:
                continue

            valid_intervals.append((start,end))

        n_intervals = len(valid_intervals)

        # Loop over the intervals found so far, and keep only those distant from more than the signal separation parameter
        if n_intervals >= 2:

            comp = 0
            temp = [valid_intervals[0]]
            while comp < n_intervals- 1:
                current_interval = valid_intervals[comp]
                comp1 = comp + 1
                while comp1 < n_intervals:
                    next_interval = valid_intervals[comp1]
                    duration = (next_interval[0] - current_interval[1])*self._dt
                    if duration >= self._signal_separation:
                        temp.append(next_interval)
                        comp = comp1
                        break
                    comp1 += 1
                else:
                    comp += 1
            
            valid_intervals = temp

        self._valid_intervals = valid_intervals

        return self._valid_intervals

    @property
    def valid_intervals(self):
        """Getter for _valid_intervals attribute.
        """

        return self._valid_intervals

if __name__ == '__main__':
    
    import sys

    edf_filename = sys.argv[1]

    reader = EDFFileReader(edf_filename)

    reader.update_valid_intervals()

    print(reader.metadata)

    print(reader.get_filtered_signal(2.0,6.0))
