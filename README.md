High Voltage Capacitor Testing Application

This application is used in the 

Only runs on windows or linux because you can only get NIDAQMX on windows or linux
Packages needed to install: matplotlib, pandas, numpy, nidaqmx
External software needed: NIDAQMX, sun-valley-ttk-theme
Please follow the given steps in order to correctly execute this program.\n
1. Login with username and password and press 'Login' button.\n
2. Press the 'Save Location' button and select the folder where you would like to save results. N.B. that you
are allowed to change the save location throughout use of this program.\n
3. Enter the serial number of the specific capacitor being tested in the correct format.\n
4. Enter the desired charge (in kilovolts).\n
5. Enter the desired hold time (in seconds).\n
6. Press the 'Okay' button in the top right. You should briefly see a message that these values have been 'Set!' and
can now begin the checklist.\n
7. Press 'Begin Checklist' button which will create a pop-up window that contains a series of steps.
These steps must be completed and checked before every test run. Once they are all checked, the user will
then have the ability to begin the test.\n
8. Press 'Charge' button to begin charging the capacitor. The graph on the left displays the charging state over time.
Current and voltage are measured in two places -- the power supply and the load. During charging, there should be no
current or voltage across the load as long as the load switch is open. If there is any current or voltage detected across
the load, the power supply switch will open in order to protect it. A popup window will appear indicating this fault
and asking the user if they would like to perform an 'Emergency Off' operation. This will shut off power to the switches
ensuring that any stored charge is dumped across the resistor.\n
9. Once the charge level has reached the desired charge, the power supply switch will open, disconnecting it from the
capacitor. The capacitor will hold charge at this level for the desired hold time and then discharge into the load. If
the desired voltage is not reached, the user will have to manually press the 'Discharge' button to trigger a discharge.\n
10. Once a discharge is triggered, the graph on the right will display the static discharge current and voltage provided
by the oscilloscope.\n
11. All of this data is automatically written to a save file with a unique identifier for each test run.\n
12. By pressing 'Reset' the user will clear all the fields and may begin another test.