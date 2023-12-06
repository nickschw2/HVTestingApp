from CapTestingApp import *
from CMFX_App import *

'''
TO-DO!!!!
Force user to take pre- and post- shot notes
Fix oscilloscope loading bar
Need to allow for plotting of more than one line on twinx
The digital filter trigger enable is not working
Add dump delay to ni_daq so that we can record for different times AND so that we can record neutrons only during shot
Add Working Gas to config
Add timeline tab
Bug where you cannot load files with different dump delays or total duration, likely because the time array is different?
'''

if __name__ == "__main__":
    if SHOT_MODE:
        app = CMFX_App()
    else:
        app = CapTestingApp()
    app.mainloop()
