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
import numpy as np

class NI_DAQ():
    def __init__(self, dev_name, ai_channels, ao_channels, sample_rate, autoconnect=True):
        self.dev_name = dev_name
        self.ai_channels = ai_channels
        self.ao_channels = ao_channels
        self.sample_rate = sample_rate

        self.data = {name: np.array([]) for name in self.ai_channels} # analog input will be stored in this data array

        self.tasks = []

        if autoconnect:
            self.set_up_tasks()
            print('NI DAQ has been successfully initialized')


    def set_up_tasks(self):
        '''
        Creates AI and AO tasks. Builds a waveform that is played out through AO using
        regeneration. Connects AI to a callback function to handling plotting of data.
        '''

        # * Create two separate DAQmx tasks for the AI and AO
        #   C equivalent - DAQmxCreateTask
        #   http://zone.ni.com/reference/en-XX/help/370471AE-01/daqmxcfunc/daqmxcreatetask/
        # We need an extra task just for updating the labels that is running constantly
        self.h_task_ai = nidaqmx.Task('mixedai')
        self.h_task_ao = nidaqmx.Task('mixedao')
        self.tasks.append(self.h_task_ai)
        self.tasks.append(self.h_task_ao)

        # * Connect to analog input and output voltage channels on the named device
        #   C equivalent - DAQmxCreateAOVoltageChan
        #   http://zone.ni.com/reference/en-XX/help/370471AE-01/daqmxcfunc/daqmxcreateaovoltagechan/
        # https://nidaqmx-python.readthedocs.io/en/latest/ao_channel_collection.html
        for name, ai_chan in self.ai_channels.items():
            self.h_task_ai.ai_channels.add_ai_voltage_chan(f'{self.dev_name}/{ai_chan}')

        for name, ao_chan in self.ao_channels.items():
            self.h_task_ao.ao_channels.add_ao_voltage_chan(f'{self.dev_name}/{ao_chan}')

        '''
        SET UP ANALOG INPUT
        '''
        self.configure_for_reading()
        self._points_to_plot = int(self.sample_rate * 0.1) # somewhat arbritrarily, the number of points to read at once from the buffer

        # * Register a callback funtion to be run every N samples
        self.h_task_ai.register_every_n_samples_acquired_into_buffer_event(self._points_to_plot, self.read_callback)


        '''
        SET UP ANALOG OUTPUT
        '''
        # * Do allow sample regeneration: i.e. the buffer contents will play repeatedly (cyclically).
        # http://zone.ni.com/reference/en-XX/help/370471AE-01/mxcprop/attr1453/
        # For more on DAQmx write properties: http://zone.ni.com/reference/en-XX/help/370469AG-01/daqmxprop/daqmxwrite/
        # For a discussion on regeneration mode in the context of analog output tasks see:
        # https://forums.ni.com/t5/Multifunction-DAQ/Continuous-write-analog-voltage-NI-cDAQ-9178-with-callbacks/td-p/4036271
        self.h_task_ao.out_stream.regen_mode = RegenerationMode.DONT_ALLOW_REGENERATION

    def configure_for_reading(self):
        # * Configure the sampling rate and the number of samples
        #   ALSO: set source of the clock to be AO clock is where this example differs from basicAOandAI.py
        # ===> SET UP THE SHARED CLOCK: Use the AO sample clock for the AI task <===
        # The supplied sample rate for the AI task is a nominal value. It will in fact use the AO sample clock.
        #   C equivalent - DAQmxCfgSampClkTiming
        #   http://zone.ni.com/reference/en-XX/help/370471AE-01/daqmxcfunc/daqmxcfgsampclktiming/
        #   More details at: "help(task.cfg_samp_clk_timing)
        #   https://nidaqmx-python.readthedocs.io/en/latest/constants.html
        self.h_task_ai.timing.cfg_samp_clk_timing(self.sample_rate,
                                    sample_mode=AcquisitionType.CONTINUOUS)

        # * Configure the sampling rate and the number of samples
        #   C equivalent - DAQmxCfgSampClkTiming
        #   http://zone.ni.com/reference/en-XX/help/370471AE-01/daqmxcfunc/daqmxcfgsampclktiming/
        #   https://nidaqmx-python.readthedocs.io/en/latest/timing.html
        self.h_task_ao.timing.cfg_samp_clk_timing(rate = self.sample_rate,
                                    sample_mode=AcquisitionType.CONTINUOUS)

        # Configures the task to start acquiring or generating samples immediately upon starting the task.
        self.h_task_ao.triggers.start_trigger.disable_start_trig()


    def configure_for_writing(self):
        # * Configure the sampling rate and the number of samples
        #   ALSO: set source of the clock to be AO clock is where this example differs from basicAOandAI.py
        # ===> SET UP THE SHARED CLOCK: Use the AO sample clock for the AI task <===
        # The supplied sample rate for the AI task is a nominal value. It will in fact use the AO sample clock.
        #   C equivalent - DAQmxCfgSampClkTiming
        #   http://zone.ni.com/reference/en-XX/help/370471AE-01/daqmxcfunc/daqmxcfgsampclktiming/
        #   More details at: "help(task.cfg_samp_clk_timing)
        #   https://nidaqmx-python.readthedocs.io/en/latest/constants.html
        self.h_task_ai.timing.cfg_samp_clk_timing(self.sample_rate,
                                    source= f'/{self.dev_name}/ao/SampleClock',
                                    samps_per_chan=self.num_samples_per_channel,
                                    sample_mode=AcquisitionType.FINITE)

        # * Configure the sampling rate and the number of samples
        #   C equivalent - DAQmxCfgSampClkTiming
        #   http://zone.ni.com/reference/en-XX/help/370471AE-01/daqmxcfunc/daqmxcfgsampclktiming/
        #   https://nidaqmx-python.readthedocs.io/en/latest/timing.html
        self.h_task_ao.timing.cfg_samp_clk_timing(rate = self.sample_rate,
                                    sample_mode=AcquisitionType.FINITE,
                                    samps_per_chan=self.num_samples_per_channel)

        '''
        Set up the triggering
        '''
        # The AO task should start as soon as the AI task starts.
        #   More details at: "help dabs.ni.daqmx.Task.cfgDigEdgeStartTrig"
        #   DAQmxCfgDigEdgeStartTrig
        #   http://zone.ni.com/reference/en-XX/help/370471AE-01/daqmxcfunc/daqmxcfgdigedgestarttrig/
        self.h_task_ao.triggers.start_trigger.cfg_dig_edge_start_trig( f'/{self.dev_name}/ai/StartTrigger' )

        # Note that now the AO task must be started before the AI task in order for the synchronisation to work


    def write_waveform(self, waveform, force=False):
        # Wait until previous task is done, unless being forced to overwrite previous task
        # if not force:
        #     self.h_task_ao.wait_until_done()

        # pass the waveform to the analog output
        self.num_samples_per_channel = len(waveform)  # The number of samples to be stored in the buffer per channel
        print(f'Constructed a waveform of length {self.num_samples_per_channel} that will played at {self.sample_rate} samples per second')

        self.configure_for_writing()

        # * Write the waveform to the buffer with a 2 second timeout in case it fails
        #   Writes doubles using DAQmxWriteAnalogF64
        #   http://zone.ni.com/reference/en-XX/help/370471AG-01/daqmxcfunc/daqmxwriteanalogf64/
        self.h_task_ao.write(waveform, timeout=2)

    def read(self):
        points = self.h_task_ai.read(number_of_samples_per_channel=self._points_to_plot)
        values = {}
        for i, name in enumerate(self.ai_channels):
            self.data[name] = np.append(self.data[name], points[i])
            values[name] = np.abs(np.mean(points[i]))

        return values

    def read_callback(self, tTask, event_type, num_samples, callback_data):
        # Callback function that extracts data
        # This needs to be called for each timeframe to update the value of data
        self.read()
        # if self.task_complete():
        #     print('Done')
            # self.stop_acquisition()
            # self.configure_for_reading()
            # self.h_task_ai.start()
        return 0

    def task_complete(self):
        return self.h_task_ao.is_task_done()

    def start_acquisition(self):
        for task in self.tasks:
            if not self._task_created(task):
                return

        self.h_task_ao.start()
        self.h_task_ai.start() # Starting this task triggers the AO task


    def stop_acquisition(self):
        for task in self.tasks:
            if not self._task_created(task):
                continue
            else:
                task.stop()

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
        self.stop_acquisition()
        for task in self.tasks:
            task.close()
