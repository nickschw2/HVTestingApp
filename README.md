High Voltage Capacitor Testing Application

This application is used in the [CMFX](https://ireap.umd.edu/research/centrifugal-mirror-fusion-experiment) experiment at the University of Maryland. The wiring diagram for this experiment is as show in Figure 1.

![testing_diagram drawio](https://user-images.githubusercontent.com/73498784/150697927-674cf9c2-f089-4d98-a357-511fd6936872.png)
**Figure 1**

Because of the dependency on [National Instruments DAQmx drivers](https://www.ni.com/en-us/support/downloads/drivers/download.ni-daqmx.html#428058) (which must be installed for interfacing with an NI DAQ), the program can only run on Windows or Linux OS.

The application is written in Python's default GUI language, [tkinter](https://docs.python.org/3/library/tkinter.html) (manual [here](https://www.tcl.tk/man/tcl8.5/contents.html)). The python package dependencies can be installed with pip or some other package manager: matplotlib, pandas, numpy, nidaqmx.

An advanced GUI style is provided by [sun-valley-ttk-theme](https://github.com/rdbende/Sun-Valley-ttk-theme), which should be installed in the parent directory.

The high-level goal of the application is to remotely charge and discharge high-voltage capacitors. An electrical diagram in Figure 1 defines the setup. An operator in the control room sends/receives signals to/from an NI DAQ. There are two modes: (1) the default, discharge mode, where the HV power supply switch is open (NO) and the load switch is closed (NC) and (2) the charging mode, where the HV power supply switch is closed and the load switch is open. Additionally, the diagram is separated in two regions -- low and high voltage components. On the low voltage level, a power supply provides a low-voltage analog input to a high-voltage power supply, of which the voltage and current is monitored by an oscilloscope. Additionally, two solid state DC-AC relays can be triggered with a +5V digital signal from the NI DAQ, which then close/open the power supply and load switch. Once the capacitor has been charged, the switches turn to discharge mode and the voltage is discharged into a load resistor. Here, the current and voltage is measured and transferred through an oscilloscope to the DAQ.

A screenshot of the application is provided in Fig. 2.
![application](https://user-images.githubusercontent.com/73498784/150697889-81495a59-9dab-487a-b136-ff51a5e9d1f3.PNG)
**Figure 2**

The operation of the application is as follows:

Please follow the given steps in order to correctly execute this program.\n
1. On startup, the user is prompted to login. Login with username and password and press 'Login' button. If the login is incorrect you will be directed to try again or contact Nick Schwartz (nickschw@umd.edu).
2. The user is then prompted to choose a 'Save Location.' This is where all the results will be automatically saved. Additionally, the user can load prior runs through File -> Open. Please note that the user is allowed to change the save location throughout use of the application through File -> Save.
3. Lastly, the user is finally prompted to select the pin locations on the NI DAQ for certain inputs/outputs for the system. Again, these pins can be changed through File -> Set Pins.
4. Next the user will enter the capacitor and run information:
  - Enter the serial number of the specific capacitor being tested in the correct format (3 letters followed by 3 numbers).
  - Enter the desired charge (in kilovolts). If the entered value is larger than the maximum charge value for a given capacitor type, the user will be prompted with an error message.
  - Enter the desired hold time (in seconds)
5. Press the 'Okay' button in the top right. A popup window will confirm that the user input values have been set.
6. At this point, one of the buttons in the Operate portion of the GUI will become active: Begin Checklist. The user must run through this checklist before every charge/discharge operation. Once all of the steps are ticked and the user presses the 'Okay' button, the Charge and Discharge buttons will become active.
7. Press 'Charge' button to begin charging the capacitor. The graph on the left displays the charging state over time. Current and voltage are measured in two places -- the power supply and the load. During charging, there should be no current or voltage across the load as long as the load switch is open. If there is any current or voltage detected across the load, the power supply switch will open in order to protect it. A popup window will appear indicating this fault and asking the user if they would like to perform an 'Emergency Off' operation. This will shut off power to the switches ensuring that any stored charge is dumped across the resistor.
8. Once the charge level has reached the desired charge, the power supply switch will open, isolating the capacitor. The capacitor will hold charge at this level for the desired hold time and then discharge into the load. If the desired voltage is not reached or the user has the desire to discharge early, the user will have to manually press the 'Discharge' button to trigger a discharge.
9. Once a discharge has ended, the oscilloscope reads the current and voltage through the load and this data appears on the discharge graph.
10. All of this data is automatically written to a save file with a unique identifier for each test run.
11. By pressing 'Reset' the user will clear all the fields and may begin another test.
