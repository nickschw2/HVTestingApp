import nidaqmx
import numpy as np
from constants import *
from nidaqmx.constants import AcquisitionType
from nidaqmx.stream_readers import AnalogMultiChannelReader

# Mostly from https://github.com/toastytato/DAQ_Interface
# Could also take from https://github.com/tenss/Python_DAQmx_examples

class NISystem:
    def __init__(self):
        self.sys = nidaqmx.system.System.local()
        self.driverVersion = sys.driver_version
        self.devices = sys.devices

    def getTerminals(self):
        terminals = {}
        for device in self.devices:
            tDevice = self.devices[device.name]
            terminals[device.name] = tDevice.terminals

# Thread for capturing input signal through DAQ
class NIRead:

    def __init__(self, sample_rate, sample_size, channels, type='analog' dev_name='PXI1Slot2'):

        self.reader = None
        self.is_running = False
        self.is_paused = False
        self.input_channels = channels
        self.daq_in_name = dev_name
        self.type = type

        self.sample_rate = sample_rate
        self.sample_size = sample_size
        # actual data received from the DAQ
        self.input = np.empty(shape=(len(inputPinDefaults), self.sample_size))


    # called on start()
    def run(self):
        self.is_running = True
        self.create_task()

        while self.is_running:
            if not self.is_paused:
                try:
                    self.reader.read_many_sample(data=self.input, number_of_samples_per_channel=self.sample_size)

                except Exception as e:
                    print("Error with read_many_sample")
                    print(e)
                    break

        self.task.close()

    def create_task(self):
        print("reader input channels:", self.input_channels)
        try:
            self.task = nidaqmx.Task("Analog Input Task")
        except OSError:
            print("DAQ is not connected, task could not be created")
            return

        try:
            if self.type = 'analog':
                for channel in self.input_channels:
                    channel_name = self.daq_in_name + "/ai" + str(channel)
                    self.task.ai_channels.add_ai_voltage_chan(channel_name)
                    print(channel_name)
            elif self.type = 'digital':
                for channel in self.input_channels:
                    channel_name = self.daq_in_name + "/ai" + str(channel)
                    self.task.ai_channels.add_ai_voltage_chan(channel_name)
                    print(channel_name)
            else:
                raise ValueError
        except Exception:
            print("DAQ is not connected, channel could not be added")
            return
        except ValueError:
            print('Please choose from analog or digital for the type')
            return

        self.task.timing.cfg_samp_clk_timing(rate=self.sample_rate, sample_mode=AcquisitionType.CONTINUOUS)
        self.task.start()

        self.reader = AnalogMultiChannelReader(self.task.in_stream)

    def restart(self):
        self.is_paused = True
        self.task.close()
        self.create_task()
        self.is_paused = False

class NIWrite(SignalGeneratorBase):
    def __init__(
        self,
        voltages,
        frequencies,
        shifts,
        output_states,
        sample_rate,
        sample_size,
        channels,
        dev_name="Dev1",
    ):
        super().__init__(
            voltages,
            frequencies,
            shifts,
            output_states,
            sample_rate,
            sample_size,
        )

        self.output_channels = channels
        self.daq_out_name = dev_name

    # create the NI task for writing to DAQ
    def create_task(self):
        try:
            self.task = nidaqmx.Task()
        except OSError:
            print("DAQ is not connected, task could not be created")
            return

        for ch in self.output_channels:
            channel_name = self.daq_out_name + "/ao" + str(ch)
            self.task.ao_channels.add_ao_voltage_chan(channel_name)

        signals_in_buffer = 4
        buffer_length = self.sample_size * signals_in_buffer
        self.task.timing.cfg_samp_clk_timing(
            rate=self.sample_rate,
            samps_per_chan=buffer_length,
            sample_mode=AcquisitionType.CONTINUOUS,
        )

        self.task.out_stream.regen_mode = RegenerationMode.DONT_ALLOW_REGENERATION
        # apparently the samps_per_chan doesn't do much for buffer size
        self.task.out_stream.output_buf_size = buffer_length

        print("Regeneration mode is set to: " + str(self.task.out_stream.regen_mode))

        print("Voltage is: ", self.voltages, " -- Frequency is: ", self.frequencies)

        self.writer = AnalogMultiChannelWriter(self.task.out_stream)

        # fill the buffer
        self.callback()
        self.callback()

    def callback(self):
        super().callback()
        self.writer.write_many_sample(self.output_waveform)

    def resume(self):
        self.callback()  # extra callback to fill DAQ buffer
        super().resume()  # start timer
        self.task.start()  # start task

    # TODO: bug with this not setting output to 0 when DAQ is hooked up
    def pause(self):
        super().pause()
        self.task.stop()

    def end(self):
        super().end()
        self.task.close()

class SignalGeneratorBase:
    """
    Used as debug signal generator to create a waveform while debugging to create waveforms
    without initializing NI method that can raise errors
    """

    def __init__(
        self, voltages, frequencies, shifts, output_states, sample_rate, sample_size
    ):

        self.is_running = False

        self.num_channels = len(CHANNEL_NAMES_OUT)
        self.wave_gen = [WaveGenerator() for i in range(self.num_channels)]

        self.voltages = voltages
        self.frequencies = frequencies
        self.shifts = shifts
        self.output_states = output_states

        # TODO: change ability to dynamically change sample rate/size in UI settings
        self.sample_rate = sample_rate  # resolution (signals/second)
        self.sample_size = sample_size  # buffer size sent on each callback

        self.timer = QtCore.QTimer()
        self.timer.setTimerType(QtCore.Qt.PreciseTimer)

        self.timer.timeout.connect(self.callback)

    # makes sure all waveforms start at the same place so phase shifts work as intended for multi-channel processes
    def realign_channel_phases(self):
        for i in range(self.num_channels):
            self.wave_gen[i].reset_counter()

    def on_offsets_received(self, data):
        self.offsets = data

    # callback for the Debug sig_gen to create signal and send to data reader
    def callback(self):
        for i in range(self.num_channels):
            if self.output_states[i]:
                self.output_waveform[i] = self.wave_gen[i].generate_wave(
                    self.voltages[i],
                    self.frequencies[i],
                    self.shifts[i],
                    self.sample_rate,
                    self.sample_size,
                )
            else:
                self.output_waveform[i] = np.zeros(self.sample_size)

        # use as debug simulated input signal
        self.incoming_data.emit(self.output_waveform)

    def resume(self):
        print("Signal resumed")
        self.is_running = True
        self.output_states = [True for x in range(self.num_channels)]
        self.signal_time = 1000 * (self.sample_size / self.sample_rate)
        self.callback()
        self.timer.start(self.signal_time)

    def pause(self):
        print("Signal paused")
        self.is_running = False
        self.output_states = [False for x in range(self.num_channels)]
        # clear the buffer with new data
        self.callback()
        self.callback()
        self.timer.stop()

    def end(self):
        self.is_running = False
        self.timer.stop()

# creates the sine wave to output
class WaveGenerator:
    def __init__(self):
        self.reset = False
        self.counter = 0
        self.last_freq = 0
        self.output_times = []

    def reset_counter(self):
        self.reset = True

    def generate_wave(self, voltage, frequency, shift, sample_rate, samples_per_chunk):
        """
        :param voltage: RMS voltage, which will be converted to amplitude in signal
        :param frequency: Determines if AC or DC. Frequency of signal in Hz if not 0, creates DC signal if frequency is 0
        :param shift: The phase shift in degrees
        :param sample_rate: # of data points per second
        :param samples_per_chunk: # of data points that will be written in this output buffer
        :return: np.array with waveform of input params
        """

        # return DC voltage if frequency is 0
        if frequency == 0:
            return np.full(shape=samples_per_chunk, fill_value=voltage)

        # determine if it needs to shift frequency based on which part of the waveform it's on
        if self.last_freq != frequency or self.reset:
            self.reset = False
            self.counter = 0
            self.last_freq = frequency
        else:
            self.counter += 1

        amplitude = np.sqrt(2) * voltage  # get peak-peak voltage from RMS voltage
        # waves_per_sec = frequency
        rad_per_sec = 2 * np.pi * frequency
        chunks_per_sec = sample_rate / samples_per_chunk
        sec_per_chunk = 1 / chunks_per_sec
        waves_per_chunk = frequency / chunks_per_sec

        # phase shift based on parameter
        phase_shift = 2 * np.pi * shift / 360

        # shift the frequency if starting in the middle of a wave
        start_fraction = waves_per_chunk % 1
        freq_shifter = self.counter * 2 * np.pi * start_fraction

        self.output_times = np.linspace(
            start=0, stop=sec_per_chunk, num=samples_per_chunk
        )
        output_waveform = amplitude * np.sin(
            self.output_times * rad_per_sec + freq_shifter - phase_shift
        )

        return output_waveform
