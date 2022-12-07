'''
 Demonstration of simultaneous analog input and output
 pynidaqmx.mixed.AOandAI_sharedClock.py
 Description:
  This example demonstrates how to continuously run data acquisition (AI)
  and signal generation (AO) at the same time and have the tasks synchronized
  with one another. Note that a single DAQmx task can support only one type of channel:
  http://digital.ni.com/public.nsf/allkb/4D2E6ABCF652542186256F04004FDAC3
  So we need to make one task for AI, one for AO, and start them synchronously with an
  internal trigger.
  In this example the AI and AO share a clock. They both start at the same time and
  acquire data at exactly the same rate.
'''

import nidaqmx
from nidaqmx.constants import (AcquisitionType,RegenerationMode)
from nidaqmx.stream_readers import (
    AnalogSingleChannelReader, AnalogMultiChannelReader)
from nidaqmx.stream_writers import (
    AnalogSingleChannelWriter, AnalogMultiChannelWriter)
import numpy as np
from config import *

class NI_DAQ():
    def __init__(self, systemStatus_name, discharge_name, sample_rate, systemStatus_channels={}, charge_ao_channels={}, diagnostics={}, autostart=True):
        self.systemStatus_name = systemStatus_name
        self.discharge_name = discharge_name
        self.systemStatus_channels = systemStatus_channels
        self.charge_ao_channels = charge_ao_channels
        self.diagnostics = diagnostics
        self.sample_rate = sample_rate

        self.data = {name: np.array([]) for name in self.systemStatus_channels} # analog input will be stored in this data array

        self.tasks = []
        self.closed = False

        self.set_up_tasks()
        print('NI DAQ has been successfully initialized')

        if autostart:
            self.start_acquisition()

    def set_up_tasks(self):
        '''
        Creates AI and AO tasks. Builds a waveform that is played out through AO using
        regeneration. Connects AI to a callback function to handling plotting of data.
        '''

        # * Create two separate DAQmx tasks for the AI and AO
        #   C equivalent - DAQmxCreateTask
        #   http://zone.ni.com/reference/en-XX/help/370471AE-01/daqmxcfunc/daqmxcreatetask/
        # We need an extra task just for updating the labels that is running constantly
        self.task_systemStatus = nidaqmx.Task()
        self.task_charge_ao = nidaqmx.Task()
        self.task_diagnostics = nidaqmx.Task()
        
        self.tasks.append(self.task_systemStatus)
        self.tasks.append(self.task_charge_ao)
        self.tasks.append(self.task_diagnostics)

        # * Connect to analog input and output voltage channels on the named device
        #   C equivalent - DAQmxCreateAOVoltageChan
        #   http://zone.ni.com/reference/en-XX/help/370471AE-01/daqmxcfunc/daqmxcreateaovoltagechan/
        # https://nidaqmx-python.readthedocs.io/en/latest/ao_channel_collection.html
        for ai_chan in self.systemStatus_channels.values():
            self.task_systemStatus.ai_channels.add_ai_voltage_chan(f'{self.systemStatus_name}/{ai_chan}', min_val=0.0, max_val=10.0)

        for ao_chan in self.charge_ao_channels.values():
            self.task_charge_ao.ao_channels.add_ao_voltage_chan(f'{self.discharge_name}/{ao_chan}', min_val=0.0, max_val=10.0)

        for diagnostic in self.diagnostics.values():
            self.task_diagnostics.ai_channels.add_ai_voltage_chan(f'{self.discharge_name}/{diagnostic}', min_val=-10.0, max_val=10.0)

        '''
        SET UP ANALOG INPUT
        '''
        if len(self.systemStatus_channels) != 0:
            self._points_to_plot = int(self.sample_rate * 0.1) # somewhat arbritrarily, the number of points to read at once from the buffer
            self.task_systemStatus.timing.cfg_samp_clk_timing(self.sample_rate,
                                    sample_mode=AcquisitionType.CONTINUOUS,
                                    samps_per_chan=self._points_to_plot)

        # * Register a callback funtion to be run every N samples and when the AO task is done
            self.task_systemStatus.register_every_n_samples_acquired_into_buffer_event(self._points_to_plot, self.read_callback)

        '''
        SET UP COUNTER OUTPUT
        '''
        if SHOT_MODE:
            self.h_task_co = nidaqmx.Task()
            self.tasks.append(self.h_task_co)

            freq = 10000
            duty_cycle = 0.5
            self.h_task_co.co_channels.add_co_pulse_chan_freq(f'{self.discharge_name}/ctr0', freq=freq, duty_cycle=duty_cycle)
            self.h_task_co.channels.co_pulse_term = f'/{self.discharge_name}/PFI0'

            n_pulses = 1
            self.h_task_co.timing.cfg_implicit_timing(sample_mode=AcquisitionType.FINITE, samps_per_chan=n_pulses)
            self.h_task_co.triggers.start_trigger.cfg_dig_edge_start_trig(f'/{self.discharge_name}/PFI1', trigger_edge=nidaqmx.constants.Edge.RISING)

    def write_value(self, value):
        self.task_charge_ao.write(value, timeout=2)

    def read(self):
        points = self.task_systemStatus.read(number_of_samples_per_channel=self._points_to_plot)
        values = {}
        for i, name in enumerate(self.systemStatus_channels):
            self.data[name] = np.append(self.data[name], points[i])
            values[name] = np.mean(points[i])

        return values

    def read_callback(self, tTask, event_type, num_samples, callback_data):
        self.read()
        return 0

    def start_acquisition(self):
        for task in self.tasks:
            if not self._task_created(task):
                return
            else:
                task.start()

    def stop_acquisition(self):
        for task in self.tasks:
            if not self._task_created(task):
                continue
            else:
                task.stop()

    def reset_data(self):
        self.data = {name: np.array([]) for name in self.systemStatus_channels} # analog input will be stored in this data array

    # House-keeping methods follow
    def _task_created(self, task):
        '''
        Return True if a task has been created
        '''

        if isinstance(task, nidaqmx.task.Task):
            return True
        else:
            print('No tasks created: run the set_up_tasks method')
            return False

    def close(self):
        if not self.closed:
            self.stop_acquisition()
            for task in self.tasks:
                task.close()
            self.closed = True