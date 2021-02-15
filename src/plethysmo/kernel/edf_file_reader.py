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

        # The time zone for which the data will not be parsed when searching for valid intervals
        self._exclusion_zones = []

        # The minimum duration for a valid interval (in seconds)
        self._signal_duration = 5

        # The separation between two valid intervals (in seconds)
        self._signal_separation =  15

        # The minimum value under which the signal is not valid anymore
        self._threshold_min = -0.10

        # The maximum value over which the signal is not valid anymore
        self._threshold_max =  0.10
        
        # The list of valid intervals (tuples of of the form (start,end))
        self._valid_intervals = []

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
    def exclusion_zones(self):
        """Getter for _exclusion_zones attribute.
        """

        return self._exclusion_zones

    @exclusion_zones.setter
    def exclusion_zones(self, exclusion_zones):
        """Getter for _exclusion_zones attribute.
        """

        self._exclusion_zones = exclusion_zones

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
        params['threshold min'] = self._threshold_min
        params['threshold max'] = self._threshold_max
        params['signal duration'] = self._signal_duration
        params['signal separation'] = self._signal_separation
        params['exclusion zones'] = ','.join(['{}:{}'.format(start,end) for start,end in self._exclusion_zones])

        return params

    @parameters.setter
    def parameters(self, params):
        """Set the parameters for searching for valid intervals.

        Args:
            params (dict): the parameters
        """

        try:
            self._threshold_min = float(params.get('threshold min',-0.8))
            self._threshold_max = float(params.get('threshold max',0.8))
            self._signal_duration = float(params.get('signal duration',5))
            self._signal_separation = float(params.get('signal separation',15))
            exclusion_zones = params.get('exclusion zones','').strip()
            self._exclusion_zones = re.findall(r'(\d+):(\d+)(?:,|$)',exclusion_zones)
        except ValueError as e:
            raise EDFFileReaderError from e


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
    def threshold_max(self):
        """Getter for _threshold_max attribute.
        """

        return self._threshold_max

    @threshold_max.setter
    def threshold_max(self, threshold_max):
        """Getter for _threshold_max attribute.
        """

        self._threshold_max = threshold_max

    @property
    def threshold_min(self):
        """Getter for _threshold_min attribute.
        """

        return self._threshold_min

    @threshold_min.setter
    def threshold_min(self, threshold_min):
        """Getter for _threshold_min attribute.
        """

        self._threshold_min = threshold_min

    @property
    def times(self):
        """Getter for _times attribute.
        """

        return self._times

    def update_valid_intervals(self):
        """Update the valid intervals.
        """

        signal_length = len(self._signal)

        comp = 0

        intervals = []

        while comp < signal_length:

            s = self._signal[comp]

            if s >= self._threshold_min and s <= self._threshold_max:
                start = comp
                comp1 = start
                while comp1 < signal_length:
                    s1 = self._signal[comp1]
                    if s1 < self._threshold_min or s1 > self._threshold_max:
                        end = comp1
                        intervals.append((start,end))
                        break
                    comp1 += 1
                comp = comp1
            else:
                comp += 1

        valid_intervals = []
        for start, end in intervals:
            excluded_interval = False
            for start_excluded_zone, end_excluded_zone in self._exclusion_zones:
                if (end >= start_excluded_zone and start <= end_excluded_zone):
                    excluded_interval = True

            if excluded_interval:
                continue

            duration = (end - start)*self._dt
            if duration <= self._signal_duration:
                continue

            valid_intervals.append((start,end))

        n_intervals = len(valid_intervals)

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
