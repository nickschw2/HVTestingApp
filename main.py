from CapTestingApp import *
from CMFX_App import *

'''
TO-DO!!!!
Keep recording charging until the last safety switch has closed
put plotting and saving on a separate thread so computer doesn't freeze
Put the digital switches on the ni daq to call continuously
figure out why the software timing is so jank (like time.sleep is sleeping for longer than expected)
Post shot notes seem to not be recording in master
Set possible configuration to number of pulses (add kwarg to daq init for n_pulses=None)
Wrap the text in the notes
Force user to take pre- and post- shot notes
'''

if __name__ == "__main__":
    if SHOT_MODE:
        app = CMFX_App()
    else:
        app = CapTestingApp()
    app.mainloop()
