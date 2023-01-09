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
from nidaqmx.constants import (AcquisitionType, Edge, TerminalConfiguration)
from nidaqmx.stream_readers import (AnalogMultiChannelReader)
import numpy as np
from config import *

class NI_DAQ():
    def __init__(self, systemStatus_name, output_name, discharge_name, systemStatus_sample_rate, systemStatus_channels={}, charge_ao_channels={}, diagnostics={}, n_pulses=None, autostart=True):
        self.systemStatus_name = systemStatus_name
        self.output_name = output_name
        self.discharge_name = discharge_name
        self.systemStatus_channels = systemStatus_channels
        self.charge_ao_channels = charge_ao_channels
        self.diagnostics = diagnostics
        self.systemStatus_sample_rate = systemStatus_sample_rate
        self.n_pulses = n_pulses

        self.systemStatusData = {name: np.array([]) for name in self.systemStatus_channels} # analog input will be stored in this data array

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

        self.tasks.append(self.task_systemStatus)
        self.tasks.append(self.task_charge_ao)

        # * Connect to analog input and output voltage channels on the named device
        #   C equivalent - DAQmxCreateAOVoltageChan
        #   http://zone.ni.com/reference/en-XX/help/370471AE-01/daqmxcfunc/daqmxcreateaovoltagechan/
        # https://nidaqmx-python.readthedocs.io/en/latest/ao_channel_collection.html
        for name, ai_chan in self.systemStatus_channels.items():
            self.task_systemStatus.ai_channels.add_ai_voltage_chan(f'{self.systemStatus_name}/{ai_chan}', 
                                                                   min_val=0.0, max_val=10.0,
                                                                   name_to_assign_to_channel=name,
                                                                   terminal_config=TerminalConfiguration.DIFF)

        for name, ao_chan in self.charge_ao_channels.items():
            self.task_charge_ao.ao_channels.add_ao_voltage_chan(f'{self.output_name}/{ao_chan}',
                                                                min_val=0.0, max_val=10.0,
                                                                name_to_assign_to_channel=name)

        '''
        SET UP ANALOG INPUT
        '''
        if len(self.systemStatus_channels) != 0:
            self._points_to_plot = int(self.systemStatus_sample_rate * 0.1) # somewhat arbritrarily, the number of points to read at once from the buffer
            self.task_systemStatus.timing.cfg_samp_clk_timing(self.systemStatus_sample_rate,
                                    sample_mode=AcquisitionType.CONTINUOUS,
                                    samps_per_chan=self._points_to_plot)

        # * Register a callback funtion to be run every N samples and when the AO task is done
            self.task_systemStatus.register_every_n_samples_acquired_into_buffer_event(self._points_to_plot, self.read_callback)

        '''
        SET UP DISCHARGE TRIGGER
        '''
        self.reset_discharge_trigger()

    def reset_discharge_trigger(self):
        # Remove and close prior versions of trigger tasks
        if hasattr(self, 'task_diagnostics'):
            self.tasks.remove(self.task_diagnostics)
            self.task_diagnostics.stop()
            self.task_diagnostics.close()

        if hasattr(self, 'task_co'):
            self.tasks.remove(self.task_co)
            self.task_co.stop()
            self.task_co.close()

        '''
        SET UP DISCHARGE AND COUNTER TASKS
        '''
        self.task_diagnostics = nidaqmx.Task()
        self.tasks.append(self.task_diagnostics)

        for name, diagnostic in self.diagnostics.items():
            self.task_diagnostics.ai_channels.add_ai_voltage_chan(f'{self.discharge_name}/{diagnostic}',
                                                                  min_val=-1.0, max_val=1.0,
                                                                  name_to_assign_to_channel=name,
                                                                  terminal_config=TerminalConfiguration.DIFF)

        self.task_co = nidaqmx.Task()
        self.tasks.append(self.task_co)

        freq = 1 / pulse_period
        duty_cycle = pulse_width / pulse_period
        # Normally send as many pulses as possible
        if self.n_pulses == None:
            self.n_pulses = int(duration / pulse_period)
        self.task_co.co_channels.add_co_pulse_chan_freq(f'{self.output_name}/ctr0', freq=freq, duty_cycle=duty_cycle, initial_delay=spectrometer_delay)
        self.task_co.channels.co_pulse_term = f'/{self.output_name}/PFI0'
        self.task_co.timing.cfg_implicit_timing(sample_mode=AcquisitionType.FINITE, samps_per_chan=self.n_pulses)        
        self.task_co.triggers.start_trigger.cfg_dig_edge_start_trig(f'/{self.output_name}/PFI1', trigger_edge=Edge.RISING)

        # Create time array for discharge
        n_channels = len(self.diagnostics)
        pretrigger_fraction = 0.1
        posttrigger_samples = int(maxDiagnosticsFreq * duration) + 1 # Add one to include t=0
        pretrigger_samples = int(posttrigger_samples * pretrigger_fraction) 
        pretrigger_duration = duration * pretrigger_fraction
        discharge_samps_per_chan = pretrigger_samples + posttrigger_samples
        self.dischargeTime = np.linspace(-pretrigger_duration, duration, discharge_samps_per_chan)
        if (max(np.abs(self.dischargeTime)) < 1e-3):
            self.dischargeTime = self.dischargeTime * 1e6
            self.tUnit = 'us'
        elif (max(np.abs(self.dischargeTime)) < 1):
            self.dischargeTime = self.dischargeTime * 1e3
            self.tUnit = 'ms'
        else:
            self.tUnit = 's'


        self.dischargeData = np.zeros((n_channels, discharge_samps_per_chan))

        self.task_diagnostics.timing.cfg_samp_clk_timing(maxDiagnosticsFreq, sample_mode=AcquisitionType.FINITE, samps_per_chan=discharge_samps_per_chan)
        self.task_diagnostics.triggers.reference_trigger.cfg_dig_edge_ref_trig(f'/{self.output_name}/PFI1', pretrigger_samples=pretrigger_samples, trigger_edge=Edge.RISING)
        # self.task_diagnostics.register_signal_event(Signal.SAMPLE_COMPLETE, self.read_discharge)

        self.discharge_reader = AnalogMultiChannelReader(self.task_diagnostics.in_stream)

        self.dischargeTriggered = False

        self.task_diagnostics.start()
        self.task_co.start()

    def write_value(self, value):
        self.task_charge_ao.write(value, timeout=2)

    def read(self):
        points = self.task_systemStatus.read(number_of_samples_per_channel=self._points_to_plot)
        values = {}
        for i, name in enumerate(self.systemStatus_channels):
            self.systemStatusData[name] = np.append(self.systemStatusData[name], points[i])
            values[name] = np.mean(points[i])

        return values

    def read_callback(self, tTask, event_type, num_samples, callback_data):
        self.read()
        return 0

    def read_discharge(self):
        if not self.dischargeTriggered:
            print('DAQ has been triggered')
            # Read all discharge data and wait for acquisition to finish
            self.dischargeTriggered = True
            self.discharge_reader.read_many_sample(self.dischargeData)

        return 0

    def start_acquisition(self):
        for task in self.tasks:
            if not self._task_created(task):
                return
            else:
                if task.is_task_done():
                    task.start()

    def stop_acquisition(self):
        for task in self.tasks:
            if not self._task_created(task):
                continue
            else:
                task.stop()

    def reset_systemStatus(self):
        self.systemStatusData = {name: np.array([]) for name in self.systemStatus_channels} # analog input will be stored in this data array

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