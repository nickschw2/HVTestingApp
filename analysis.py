from constants import *
from config import *
import numpy as np
from scipy import signal, integrate, optimize

class Analysis():
    def __init__(self, time, timeUnit, voltage, current, dumpDelay, ignitronDelay, polarity):
        self.time = time
        self.timeUnit = timeUnit
        self.dumpDelay = dumpDelay / 1000 # In ms by default, convert to s
        self.ignitronDelay = ignitronDelay / 1000 # In ms by default, convert to s
        self.set_time()
        self.voltage = voltage
        self.current = current
        self.polarity = polarity

        # Send voltage and current through filter
        self.voltage_filtered = self.lowPassFilter(voltage)
        self.current_filtered = self.lowPassFilter(current)

        try:
            self.get_decay_time()
            self.get_stored_energy()
            self.get_capacitance()
            self.get_mom_conf_time()
            self.get_velocity()
            self.success = True
        except Exception as e:
            print(e)
            self.success = False

    def set_time(self):
        # Get time in seconds
        if self.timeUnit == 'us':
            self.time_sec = self.time / 1e6
        elif self.timeUnit == 'ms':
            self.time_sec = self.time / 1e3
        else:
            self.time_sec = self.time

        self.frequency = 1 / (self.time_sec[1] - self.time_sec[0]) # [Hz]

    def lowPassFilter(self, data, cutoff_freq=1000):
        order = 10 # magnitude of dropoff in frequency response above cutoff
        sos = signal.butter(order, cutoff_freq, btype='lowpass', output='sos', fs=samp_freq)
        return signal.sosfilt(sos, data)
    
    def get_decay_time(self):
        # Find the point just before the dump. Used to calculate resistance of the plasma at the moment of dump
        self.voltage_drop_index = np.where(self.time_sec > self.dumpDelay + self.ignitronDelay)[0][0]

        # Separate out the dump trace
        dump_window = 0.2 # [s]
        dump_indices = (self.time_sec >= self.dumpDelay + self.ignitronDelay) & (self.time_sec <= self.dumpDelay + self.ignitronDelay + dump_window)
        self.dump_time = self.time_sec[dump_indices]
        self.dump_current = self.current_filtered[dump_indices]
        self.dump_voltage = self.voltage_filtered[dump_indices]

        # Peak finder to find the peak current during the dump
        # The bias determines if the current is positive during the discharge, if so the dump current will be in the opposite direction
        # If the bias is positive, the dump current will be negative and we need to flip the sign to find the 'peak'
        if self.polarity == 'Positive':
            self.peaks, _ = signal.find_peaks(-self.dump_current, height=1, prominence=1)
            m_guess_factor = -1
        elif self.polarity == 'Negative':
            self.peaks, _ = signal.find_peaks(self.dump_current, height=1, prominence=1)
            m_guess_factor = 1
        else:
            print('Polarity is not correct')

        self.peak = self.peaks[0]
        self.exp_time = self.dump_time[self.peak:]
        self.exp_current = self.dump_current[self.peak:]
        self.exp_voltage = self.dump_voltage[self.peak:]

        # Resistance is calculated right before the dump
        self.voltage_at_dump = self.voltage_filtered[self.voltage_drop_index] # [V]
        self.current_at_dump = self.current_filtered[self.voltage_drop_index] # [A]
        self.resistance_at_dump = np.abs(self.voltage_at_dump / self.current_at_dump) # [Ohms]
        
        # Initial guess is 1 A peak magnitude, 40 ms dump time, and decays to zero
        p0 = (m_guess_factor * 1, 0.04, 0)
        params, cv = optimize.curve_fit(self.exp_decay, self.exp_time, self.exp_current, p0)
        self.m, self.decayTime, self.b = params

    def exp_decay(self, x, m, tau, b):
        return m * np.exp(-x / tau) + b
    
    def get_stored_energy(self):
        if not hasattr(self, 'tau'):
            self.get_decay_time()

        self.stored_energy = np.abs(integrate.trapezoid(self.exp_current * self.exp_voltage, self.exp_time))

    def get_capacitance(self):
        if not hasattr(self, 'stored_energy'):
            self.get_stored_energy()

        # self.capacitance = self.tau / 1000 / (self.resistance_at_dump * 1000) # [F]

        # 1/2 CV^2 = int(I * V)
        self.capacitance = 2 * self.stored_energy / self.voltage_at_dump**2 # [F]

    def get_mom_conf_time(self):
        if not hasattr(self, 'capacitance'):
            self.get_capacitance()

        self.tau_M = self.capacitance * self.resistance_at_dump

    # def get_density(self, length, inner_radius, outer_radius, B_0, species):
    #     if not hasattr(self, 'capacitance'):
    #         self.get_capacitance()

    #     if species == 'hydrogen':
    #         m_i = m_p
    #     elif species == 'deuterium':
    #         m_i = 2 * m_p

    #     # 1/2 CV^2 = 1/2 n m_i v^2 V_p
    #     self.RC_density = self.capacitance * B_0**2 * (outer_radius - inner_radius) / (np.pi * m_i * (outer_radius + inner_radius) * length)
    
    def get_velocity(self):
        # Electric field (V / m)
        self.E = self.voltage / plasma_radius_outer
        
        # Rotational velocity (m / s)
        self.velocity = self.E / B0

        # Get velocity at the dump
        self.dumpVelocity = self.voltage_at_dump / ((plasma_radius_outer - plasma_radius_inner) * B0)

    def get_diamagneticDensity(self, data):
        # Filter and integrate
        filtered = self.lowPassFilter(data)
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
