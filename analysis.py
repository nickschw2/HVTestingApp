from constants import *
from config import *
import numpy as np
from scipy import signal, integrate

class Analysis():
    def __init__(self, time, timeUnit):
        self.time = time
        self.timeUnit = timeUnit

    def lowPassFilter(self, data, cutoff_freq):
        order = 10 # magnitude of dropoff in frequency response above cutoff
        sos = signal.butter(order, cutoff_freq, btype='lowpass', output='sos', fs=sample_freq)
        return signal.sosfilt(sos, data)

    def analyzeDiamagnetic(self, data):
        # Filter and integrate
        filtered = self.lowPassFilter(data, cutoff_freq)
        integrated = integrate.cumulative_trapezoid(filtered, x=self.time, initial=0)

        # Remove DC bias
        fitCutoffIndex = np.where(self.time >= 0)[0][0]
        fitParams = np.polyfit(self.time[:fitCutoffIndex], integrated[:fitCutoffIndex], 1)
        fit = np.poly1d(fitParams)
        offset = integrated - fit(self.time)

        density = offset * 2

        return density
