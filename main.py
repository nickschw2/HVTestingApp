from CapTestingApp import *
from CMFX_App import *

'''
TO-DO!!!!
Fix oscilloscope loading bar
Need to allow for plotting of more than one line on twinx
The digital filter trigger enable is not working
Bug where you cannot load files with different dump delays or total duration, likely because the time array is different?
'''

if __name__ == "__main__":
    if SHOT_MODE:
        app = CMFX_App()
    else:
        app = CapTestingApp()
    app.mainloop()
