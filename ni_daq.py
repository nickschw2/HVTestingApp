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

        self.data = {ai_chan: np.array([]) for ai_chan in self.ai_channels} # analog input will be stored in this data array

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
        self.h_task_ao = nidaqmx.Task('mixedao')
        self.h_task_ai = nidaqmx.Task('mixedai')
        self.tasks.append(self.h_task_ao)
        self.tasks.append(self.h_task_ai)

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

        # * Configure the sampling rate and the number of samples
        #   ALSO: set source of the clock to be AO clock is where this example differs from basicAOandAI.py
        # ===> SET UP THE SHARED CLOCK: Use the AO sample clock for the AI task <===
        # The supplied sample rate for the AI task is a nominal value. It will in fact use the AO sample clock.
        #   C equivalent - DAQmxCfgSampClkTiming
        #   http://zone.ni.com/reference/en-XX/help/370471AE-01/daqmxcfunc/daqmxcfgsampclktiming/
        #   More details at: "help(task.cfg_samp_clk_timing)
        #   https://nidaqmx-python.readthedocs.io/en/latest/constants.html
        self._points_to_plot = 1
        self.h_task_ai.timing.cfg_samp_clk_timing(self.sample_rate,
                                    source= f'/{self.dev_name}/ao/SampleClock',
                                    samps_per_chan=self._points_to_plot,
                                    sample_mode=AcquisitionType.CONTINUOUS)



        # * Register a callback funtion to be run every N samples
        self.h_task_ai.register_every_n_samples_acquired_into_buffer_event(self._points_to_plot, self.read)


        '''
        SET UP ANALOG OUTPUT
        '''

        # * Configure the sampling rate and the number of samples
        #   C equivalent - DAQmxCfgSampClkTiming
        #   http://zone.ni.com/reference/en-XX/help/370471AE-01/daqmxcfunc/daqmxcfgsampclktiming/
        #   https://nidaqmx-python.readthedocs.io/en/latest/timing.html
        self.h_task_ao.timing.cfg_samp_clk_timing(rate = self.sample_rate)


        # * Do allow sample regeneration: i.e. the buffer contents will play repeatedly (cyclically).
        # http://zone.ni.com/reference/en-XX/help/370471AE-01/mxcprop/attr1453/
        # For more on DAQmx write properties: http://zone.ni.com/reference/en-XX/help/370469AG-01/daqmxprop/daqmxwrite/
        # For a discussion on regeneration mode in the context of analog output tasks see:
        # https://forums.ni.com/t5/Multifunction-DAQ/Continuous-write-analog-voltage-NI-cDAQ-9178-with-callbacks/td-p/4036271
        # self.h_task_ao.out_stream.regen_mode = RegenerationMode.ALLOW_REGENERATION



        # * Set the size of the output buffer
        #   C equivalent - DAQmxCfgOutputBuffer
        #   http://zone.ni.com/reference/en-XX/help/370471AG-01/daqmxcfunc/daqmxcfgoutputbuffer/
        #self.h_task.cfgOutputBuffer(num_samples_per_channel);

        '''
        Set up the triggering
        '''
        # The AO task should start as soon as the AI task starts.
        #   More details at: "help dabs.ni.daqmx.Task.cfgDigEdgeStartTrig"
        #   DAQmxCfgDigEdgeStartTrig
        #   http://zone.ni.com/reference/en-XX/help/370471AE-01/daqmxcfunc/daqmxcfgdigedgestarttrig/
        self.h_task_ao.triggers.start_trigger.cfg_dig_edge_start_trig( f'/{self.dev_name}/ai/StartTrigger' )

        # Note that now the AO task must be started before the AI task in order for the synchronisation to work

    def write_waveform(self, waveform):
        # pass the waveform to the analog output
        self.num_samples_per_channel = len(self.waveform)  # The number of samples to be stored in the buffer per channel
        print(f'Constructed a waveform of length {self.num_samples_per_channel} that will played at {self.sample_rate} samples per second')

        # * Write the waveform to the buffer with a 2 second timeout in case it fails
        #   Writes doubles using DAQmxWriteAnalogF64
        #   http://zone.ni.com/reference/en-XX/help/370471AG-01/daqmxcfunc/daqmxwriteanalogf64/
        self.h_task_ao.write(self.waveform, timeout=2)

    def read(self):
        # Callback function that extracts data
        points = self.h_task_ai.read(number_of_samples_per_channel=self._points_to_plot)
        values = {}
        for i, ai_chan in enumerate(ai_channels):
            self.data[ai_chan] = np.append(self.data[ai_chan], points[i])
            values[ai_chan] = np.mean(points[i])
        print(self.data)
        return values


    def start_acquisition(self):
        if not self._task_created():
            return

        self.h_task_ao.start()
        self.h_task_ai.start() # Starting this task triggers the AO task


    def stop_acquisition(self):
        if not self._task_created():
            return

        self.h_task_ai.stop()
        self.h_task_ao.stop()

    # House-keeping methods follow
    def _task_created(self):
        '''
        Return True if a task has been created
        '''

        if isinstance(self.h_task_ao,nidaqmx.task.Task) or isinstance(self.h_task_ai,nidaqmx.task.Task):
            return True
        else:
            print('No tasks created: run the set_up_tasks method')
            return False

    def close(self):
        self.stop_acquisition()
        for task in self.tasks:
            task.close()

if __name__ == '__main__':
    print('\nRunning demo for AOandAI_sharedClock\n\n')
    MIXED = AOandAI_sharedClock()
    MIXED.set_up_tasks()
    # MIXED.setup_plot()
    MIXED.start_acquisition()
    input('press return to stop')
    MIXED.stop_acquisition()
    MIXED.h_task_ai.close()
    MIXED.h_task_ao.close()
    plt.plot(MIXED.data)
    plt.show()
