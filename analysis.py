from constants import *
from config import *
import numpy as np
from scipy import signal, integrate

class Analysis():
    def __init__(self, time, timeUnit, voltage, current):
        self.time = time
        self.timeUnit = timeUnit
        self.set_time()

        # Send voltage and current through filter
        self.voltage = self.lowPassFilter(voltage, cutoff_freq)
        self.current = self.lowPassFilter(current, cutoff_freq)

        self.get_velocity()

    def set_time(self):
        # Get time in seconds
        if self.timeUnit == 'us':
            self.time_sec = self.time / 1e6
        elif self.timeUnit == 'ms':
            self.time_sec = self.time / 1e3

    def lowPassFilter(self, data, cutoff_freq):
        order = 10 # magnitude of dropoff in frequency response above cutoff
        sos = signal.butter(order, cutoff_freq, btype='lowpass', output='sos', fs=samp_freq)
        return signal.sosfilt(sos, data)
    
    def get_velocity(self):
        # Electric field (V / m)
        self.E = self.voltage / plasma_radius_outer
        
        # Rotational velocity (m / s)
        self.velocity = self.E / B0

    def get_diamagneticDensity(self, data):
        # Filter and integrate
        filtered = self.lowPassFilter(data, cutoff_freq)
        integrated = integrate.cumulative_trapezoid(filtered, x=self.time_sec, initial=0)

        # Remove DC bias
        fitCutoffIndex = np.where(self.time_sec >= 0)[0][0]
        fitParams = np.polyfit(self.time_sec[:fitCutoffIndex], integrated[:fitCutoffIndex], 1)
        fit = np.poly1d(fitParams)
        offset = integrated - fit(self.time_sec)

        # Change in magnetic field (T)
        deltaB = offset / (N_turns * np.pi * chamber_radius**2)

        # density = B0 * plasma_radius_outer * deltaB / (mu0 * m_i * self.velocity**2 * d_r)
        density = 2 * B0**3 * deltaB * np.log(plasma_radius_outer / plasma_radius_inner) * (plasma_radius_outer - plasma_radius_inner)**2 / (mu0 * m_i * self.voltage**2)

        return density
