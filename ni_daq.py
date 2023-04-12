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
from nidaqmx.constants import (AcquisitionType, Edge, TriggerType, Level, LineGrouping, Signal)
from nidaqmx.stream_readers import (AnalogMultiChannelReader)
import numpy as np
from config import *

class NI_DAQ():
    def __init__(self, systemStatus_sample_rate, systemStatus_name, output_name,
                 diagnostics_name, diagnostics2_name=None, systemStatus_channels={},
                 charge_ao_channels={}, diagnostics={}, diagnostics2={},
                 n_pulses=None, autostart=True):
        
        self.systemStatus_name = systemStatus_name
        self.output_name = output_name
        self.diagnostics_name = diagnostics_name
        self.diagnostics2_name = diagnostics2_name
        self.systemStatus_channels = systemStatus_channels
        self.charge_ao_channels = charge_ao_channels
        self.diagnostics = diagnostics
        self.diagnostics2 = diagnostics2
        self.systemStatus_sample_rate = systemStatus_sample_rate
        self.n_pulses = n_pulses

        self.systemStatusData = {name: np.array([]) for name in self.systemStatus_channels} # analog input will be stored in this data array

        self.tasks = []
        self.closed = False

        self.dumpDelay = default_dumpDelay

        self.status_task_names = ['task_systemStatus', 'task_charge_ao']
        self.switch_task_names = ['task_switch_trigger', 'task_switch']
        self.dump_task_names = ['task_dump_trigger', 'task_dump']
        self.trigger_task_names = ['task_diagnostics', 'task_co']
        
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
        self.add_tasks(self.status_task_names)

        # * Connect to analog input and output voltage channels on the named device
        #   C equivalent - DAQmxCreateAOVoltageChan
        #   http://zone.ni.com/reference/en-XX/help/370471AE-01/daqmxcfunc/daqmxcreateaovoltagechan/
        # https://nidaqmx-python.readthedocs.io/en/latest/ao_channel_collection.html
        for name, ai_chan in self.systemStatus_channels.items():
            self.task_systemStatus.ai_channels.add_ai_voltage_chan(f'{self.systemStatus_name}/{ai_chan}', 
                                                                   min_val=0.0, max_val=10.0,
                                                                   name_to_assign_to_channel=name)

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
        self.remove_tasks(self.trigger_task_names + self.dump_task_names)

        # Create tasks and add them to task list
        self.add_tasks(self.trigger_task_names + self.dump_task_names)
                                                 
        '''
        COUNTER TASK
        '''
        freq = 1 / pulse_period
        duty_cycle = pulse_width / pulse_period
        # Normally send as many pulses as possible
        if self.n_pulses == None:
            self.n_pulses = int(duration / pulse_period)
        self.task_co.co_channels.add_co_pulse_chan_freq(f'{self.output_name}/ctr0', freq=freq, duty_cycle=duty_cycle, initial_delay=spectrometer_delay)
        self.task_co.channels.co_pulse_term = f'/{self.output_name}/PFI0'
        self.task_co.timing.cfg_implicit_timing(sample_mode=AcquisitionType.FINITE, samps_per_chan=self.n_pulses)        
        self.task_co.triggers.start_trigger.cfg_dig_edge_start_trig(f'/{self.diagnostics_name}/PFI0', trigger_edge=Edge.RISING)

        '''
        DIGITAL OUTPUT TASKS
        '''
        #### Open dump switch initially ####
        # We need to open the dump switch initially with a single pulse, because we don't know how long the charging process will take
        # Our old PXI model (6133 or 6225) doesn't have the ability to generate a do trigger
        # So we create a dummy ai task and use the ai Sample Clock, then trigger the ai task
        self.task_dump_trigger.ai_channels.add_ai_voltage_chan(f'{self.output_name}/ai0')
        self.task_dump_trigger.timing.cfg_samp_clk_timing(rate=switch_samp_freq, source='OnboardClock', sample_mode=AcquisitionType.CONTINUOUS)

        # We trigger the dump switch to open with a separate digital signal to this PFI line
        self.task_dump_trigger.triggers.start_trigger.cfg_dig_edge_start_trig(trigger_source=f'/{self.output_name}/PFI1', trigger_edge=Edge.RISING)

        # Set up the do task to open the dump switch when it is triggered
        # We only need to write a single true value to the channel
        self.task_dump.do_channels.add_do_chan(f'{self.output_name}/{digitalOutName}/{do_defaults["Dump Switch"]}')
        self.task_dump.timing.cfg_samp_clk_timing(rate=switch_samp_freq, source=f'/{self.output_name}/ai/SampleClock', active_edge=Edge.RISING, sample_mode=AcquisitionType.FINITE, samps_per_chan=1)
        self.task_dump.write(True, auto_start=False)

        # When the switch has been opened, setup the triggering for switching the load and dump
        self.task_dump.register_done_event(self.set_switch_trigger)

        '''
        DIAGNOSTICS TASK
        '''
        for name, diagnostic in self.diagnostics.items():
            self.task_diagnostics.ai_channels.add_ai_voltage_chan(f'{self.diagnostics_name}/{diagnostic}',
                                                                  min_val=-10.0, max_val=10.0,
                                                                  name_to_assign_to_channel=name)
            
        if self.diagnostics2_name != None:
            for name, diagnostic in self.diagnostics2.items():
                self.task_diagnostics.ai_channels.add_ai_voltage_chan(f'{self.diagnostics2_name}/{diagnostic}',
                                                                    min_val=-10.0, max_val=10.0,
                                                                    name_to_assign_to_channel=name)

        # Create time array for discharge
        n_channels = len(self.diagnostics) + len(self.diagnostics2)
        pretrigger_fraction = 0.1
        posttrigger_samples = int(samp_freq * duration) + 1 # Add one to include t=0
        pretrigger_samples = int(posttrigger_samples * pretrigger_fraction) 
        pretrigger_duration = duration * pretrigger_fraction
        discharge_samps_per_chan = pretrigger_samples + posttrigger_samples
        self.dischargeTime = np.linspace(-pretrigger_duration, duration, discharge_samps_per_chan)
        if (max(np.abs(self.dischargeTime)) < 1e-3):
            self.dischargeTime *= 1e6
            self.tUnit = 'us'
        elif (max(np.abs(self.dischargeTime)) < 1):
            self.dischargeTime *= 1e3
            self.tUnit = 'ms'
        else:
            self.tUnit = 's'

        self.dischargeData = np.zeros((n_channels, discharge_samps_per_chan))

        self.task_diagnostics.timing.cfg_samp_clk_timing(samp_freq, sample_mode=AcquisitionType.FINITE, samps_per_chan=discharge_samps_per_chan)

        # Add analog signal trigger
        self.task_diagnostics.triggers.reference_trigger.cfg_dig_edge_ref_trig(f'/{self.diagnostics_name}/PFI0', pretrigger_samples=pretrigger_samples)
        
        # Specify a minimum pulse width (in sec) to avoid false trigger
        # self.task_diagnostics.triggers.reference_trigger.anlg_edge_dig_fltr_enable = True
        # self.task_diagnostics.triggers.reference_trigger.anlg_edge_dig_fltr_min_pulse_width = 0.01

        # self.task_diagnostics.register_signal_event(Signal.SAMPLE_COMPLETE, self.read_discharge)

        self.discharge_reader = AnalogMultiChannelReader(self.task_diagnostics.in_stream)

        self.dischargeTriggered = False

        '''START TASKS'''
        for task in self.trigger_task_names + self.dump_task_names:
            task = getattr(self, task)
            if len(task.channel_names) != 0:
                task.start()

    def set_switch_trigger(self, task_handle, status, callback_data):
        # Remove the old dump switch tasks
        self.remove_tasks(self.dump_task_names)

        # Create tasks and add them to task list
        for task in self.switch_task_names:
            setattr(self, task, nidaqmx.Task())
            self.tasks.append(getattr(self, task))

        # Our old PXI model (6133 or 6225) doesn't have the ability to generate a do trigger
        # So we create a dummy ai task and use the ai Sample Clock, then trigger the ai task
        self.task_switch_trigger.ai_channels.add_ai_voltage_chan(f'{self.output_name}/ai0')
        self.task_switch_trigger.timing.cfg_samp_clk_timing(rate=switch_samp_freq, source='OnboardClock', sample_mode=AcquisitionType.CONTINUOUS)

        # Trigger the signal generation with the pulse generator to this PFI channel
        self.task_switch_trigger.triggers.start_trigger.cfg_dig_edge_start_trig(trigger_source=f'/{self.diagnostics_name}/PFI0', trigger_edge=Edge.RISING)

        # Setup pause trigger
        # self.task_switch_trigger.triggers.pause_trigger.trig_type = TriggerType.DIGITAL_LEVEL
        # self.task_switch_trigger.triggers.pause_trigger.dig_lvl_src = f'/{self.output_name}/PFI2'
        # self.task_switch_trigger.triggers.pause_trigger.dig_lvl_when = Level.HIGH

        # Add digital output to switch lines
        self.task_switch.do_channels.add_do_chan(f'{self.output_name}/{digitalOutName}/{do_defaults["Load Switch"]}')
        self.task_switch.do_channels.add_do_chan(f'{self.output_name}/{digitalOutName}/{do_defaults["Dump Switch"]}')

        # Switch timing
        n_load_samples = int(switch_samp_freq * (gasPuffWaitTime + self.dumpDelay + switchWaitTime))
        n_dump_samples = int(switch_samp_freq * (gasPuffWaitTime + self.dumpDelay))

        # Construct digital arrays to pass to the do channels
        load_list = [True] * n_load_samples
        dump_list = [True] * n_dump_samples
        
        # The last element of the array has to be false so the switch is in the normal state
        load_list[-1] = False
        # The length of the arrays must be the same
        dump_list += [False] * (n_load_samples - n_dump_samples)

        # Configure timing to a finite generation
        self.task_switch.timing.cfg_samp_clk_timing(rate=switch_samp_freq, source=f'/{self.output_name}/ai/SampleClock', active_edge=Edge.RISING, sample_mode=AcquisitionType.FINITE, samps_per_chan=n_load_samples)

        self.task_switch.write([load_list, dump_list], auto_start=False)

        # When the switch operation has completed, remove tasks
        self.task_switch.register_done_event(self.remove_switch_tasks)

        '''START TASKS'''
        for task in self.switch_task_names:
            task = getattr(self, task)
            task.start()

        return 0

    def set_dumpDelay(self, dumpDelay):
        self.dumpDelay = dumpDelay
        print(f'Set dump delay to {self.dumpDelay} s')

    def remove_switch_tasks(self, task_handle, status, callback_data):
        self.remove_tasks(self.switch_task_names)
        return 0

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
    
    def remove_tasks(self, task_names):
        for task_name in task_names:
            if hasattr(self, task_name):
                task = getattr(self, task_name)
                if task in self.tasks:
                    self.tasks.remove(task)
                    task.stop()
                    task.close()

    def add_tasks(self, task_names):
        for task in task_names:
            setattr(self, task, nidaqmx.Task())
            self.tasks.append(getattr(self, task))

    def start_acquisition(self):
        for task in self.tasks:
            if not self._task_created(task):
                return
            else:
                if len(task.channel_names) != 0 and task.is_task_done():
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