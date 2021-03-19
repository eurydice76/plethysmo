import collections
import logging
import re
import time

import pyedflib as edf

import pandas as pd

import numpy as np

from scipy.signal import find_peaks

from plethysmo.kernel.parameters import PARAMETERS
from plethysmo.kernel.roi import ROI
from plethysmo.utils.signal import current_volume, expiratory_time, inspiratory_time, period_frequency


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
        # mini = self._signal.min()
        # maxi = self._signal.max()
        # self._signal -= mini
        # self._signal /= (maxi-mini)
        # self._signal -= 0.5
        # self._signal *= 2.0

        # Rebuild the time axis from the period
        n_points = len(self._signal)
        self._times = np.arange(0,n_points*self._dt,self._dt)
        
        # The list of valid intervals (tuples of of the form (start,end))
        self._valid_intervals = collections.OrderedDict()

        # The ROIs used to set up the intervals
        self._rois = collections.OrderedDict()

        # The time zones for which the data will not be parsed when searching for valid intervals
        self._excluded_zones = collections.OrderedDict()

    def add_roi(self, name, roi):
        """Add a new ROI the the ROIs container.

        Args:
            name (str): the name of the ROI
            roi (plethysmo.kernel.roi.ROI): the ROI
        """

        if name in self._rois:
            logging.info('A ROI with name {} already exists.')
            return

        if not isinstance(roi, ROI):
            logging.info('Invalid type for roi argument.')
            return

        self._rois[name] = roi

        self._valid_intervals[name] = []

    def add_excluded_zone(self, name, roi):
        """Add a new ROI the excluded zones container.

        Args:
            name (str): the name of the ROI
            roi (plethysmo.kernel.roi.ROI): the ROI
        """

        if name in self._excluded_zones:
            logging.info('A ROI with name {} already exists.')
            return

        if not isinstance(roi, ROI):
            logging.info('Invalid type for roi argument.')
            return

        self._excluded_zones[name] = roi

    def compute_statistics(self):
        """Compute some statistics on this reader.
        """

        statistics = collections.OrderedDict()

        for roi, intervals in self._valid_intervals.items():

            times = []
            for start, end in intervals:
                t_start = time.strftime('%H:%M:%S',time.gmtime(start*self._dt))
                t_end = time.strftime('%H:%M:%S',time.gmtime(end*self._dt))
                times.append('{} --- {}'.format(t_start,t_end))

            valid_times = []

            data = []

            for j, (start,end) in enumerate(intervals):

                row = []

                # Compute the integral
                windowed_interval = self._signal[start:end]

                # Compute the period of the signal
                period, frequency = period_frequency(windowed_interval, self._dt)

                # Skip the entry for which the frequency is over a given threshold
                if frequency > PARAMETERS['frequency threshold']:
                    continue

                row.append(period)
                row.append(frequency)

                # Compute the inspiratory time as the average of the time intervals where the signal is negative
                insp_time = inspiratory_time(windowed_interval,self._dt)
                row.append(insp_time)

                # Compute the expiratory time as the average of the time intervals where the signal is positive
                exp_time = expiratory_time(windowed_interval,self._dt)
                row.append(exp_time)

                # Compute the current volume as the minimum of the integrals of the negative parts of the signal
                cv = current_volume(windowed_interval, self._dt)
                row.append(cv)

                # Compute the volume minute which is defined as the product between the volume courand and the frequency (in min^-1)
                volmin = cv*frequency
                row.append(volmin)

                # Compute the pif 
                peak_indexes, _ = find_peaks(-windowed_interval, prominence=PARAMETERS['signal prominence'])
                pif = np.average([v for v in windowed_interval[peak_indexes] if v < 0.0]) if peak_indexes.size else np.nan
                row.append(pif)

                # Compute the pef 
                peak_indexes, _ = find_peaks(windowed_interval, prominence=PARAMETERS['signal prominence'])
                pef = np.average([v for v in windowed_interval[peak_indexes] if v > 0.0]) if peak_indexes.size else np.nan
                row.append(pef)
                
                # The amplitude is computed as the difference between the pef and the pif
                row.append(pef - pif)

                valid_times.append(times[j])

                data.append(row)

            statistics[roi] = pd.DataFrame(data,index=valid_times,columns = ['period','frequence','temps inspiratoire','temps expiratoire','volume courant','volume minute','pif','pef','amplitude'])

            statistics[roi] = statistics[roi].round(3)

        return statistics

    def delete_excluded_zone(self, name):
        """Delete a ROI from the excluded zones container.

        Args:
            name (str): the ROI name
        """

        if name not in self._excluded_zones:
            return

        del self._excluded_zones[name]

    def delete_roi(self, name):
        """Delete a ROI from the ROIs container.

        Args:
            name (str): the ROI name
        """

        if name not in self._rois:
            return

        del self._rois[name]

        del self._valid_intervals[name]

    @property
    def dt(self):
        """Getter for _dt attribute.
        """

        return self._dt

    @property
    def filename(self):
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

        # Loop over the ROI ans search for valid intervals inside
        for name, roi in self._rois.items():

            self._valid_intervals[name] = []

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
                            if (end - start)*self._dt > PARAMETERS['signal duration']:
                                self._valid_intervals[name].append((start,end))
                            break
                        # Case where the signal is between the thresholds: checked that its length is over the signal duration parameter
                        else:
                            # If this is the case, the interval is closed and kept
                            if (comp1 - start)*self._dt > PARAMETERS['signal duration']:
                                end = comp1
                                self._valid_intervals[name].append((start,end))
                                break

                        comp1 += 1
                    comp = comp1
                else:
                    comp += 1

        # Loop over the intervals found so far and check that none of them fall within an excluded zone. If this is the case, the interval is not kept.
        for name, intervals in self._valid_intervals.items():
            valid_intervals = []
            for start, end in intervals:

                # Loop over the excluded zones
                for roi in self._excluded_zones.values():
                    start_roi, _ = roi.lower_corner
                    # The roi unit is converted from time to index
                    start_roi = int(start_roi/self._dt)
                    start_roi = max(start_roi,0)

                    end_roi, _ = roi.upper_corner
                    # The roi unit is converted from time to index
                    end_roi = int(end_roi/self._dt)
                    end_roi = min(end_roi,len(self._signal)-1)
                    
                    # Check for intersection between the interval and the exluded zone
                    if (end >= start_roi and start <= end_roi):
                        break

                else:
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
                        if duration >= PARAMETERS['signal separation']:
                            temp.append(next_interval)
                            comp = comp1
                            break
                        comp1 += 1
                    else:
                        comp += 1
                
                valid_intervals = temp

            self._valid_intervals[name] = valid_intervals

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
