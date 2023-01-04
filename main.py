from CapTestingApp import *
from CMFX_App import *

'''
TO-DO!!!!
Keep recording charging until the last safety switch has closed
put plotting and saving on a separate thread so computer doesn't freeze
figure out why the software timing is so jank (like time.sleep is sleeping for longer than expected)
Post shot notes seem to not be recording in master
Force user to take pre- and post- shot notes
Clear notes on reset press
Reset y axis on reset press
Weird scaling on x axis for charging plot
Fix oscilloscope loading bar
When reset, the results plot shows up immediately
'''

if __name__ == "__main__":
    if SHOT_MODE:
        app = CMFX_App()
    else:
        app = CapTestingApp()
    app.mainloop()
