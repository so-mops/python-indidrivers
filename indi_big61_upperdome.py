#!/usr/bin/env python3
from os import stat
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd().parent))

from mtnpy import Kuiper

from pyindi.device import *

MYDEVICE = 'Upperdome'
# Groups: Status, Commands, Engineering
STATUS_GROUP = 'Status'
MAIN_CONTROL_GROUP = 'Main Control'
ENGINEERING_GROUP = 'Engineering'

telescope = Kuiper()

status_group_l = [
    'Idle',
    'Domeslit Opening',
    'Upper Windscreen Opening',
    'Lower Windscreen Opening', 
    'Lower Windscreen Closing',
    'Upper Windscreen Closing', 
    'Domeslit Closing', 
    'Fault'
]
status_group_t = [
    'Domeslit State',
    'UpperWS State',
    'LowerWS State',
    'Local Mode SW',
    'Upperdome Faulted'
]
engineering_group_t = [
    'Upperdome State Integer',
    'Upperdome IO Byte',
    'Upperdome Fault Byte',
    'Domeslit Opened LimitSW',
    'Domeslit Closed LimitSW',
    'UpperWS Opened LimitSW',
    'UpperWS Closed LimitSW',
    'LowerWS Opened LimitSW',
    'LowerWS Closed LimitSW',
    'Domeslit Faulted',
    'UpperWS Faulted',
    'LowerWS Faulted',
]

class Device(device):
    def ISGetProperties(self, device=None):
        """Property Definiations are generated
        by initProperties and buildSkeleton. No
        need to do it here. """
        
        commands_s = [
            ISwitch(
                "open_all",  # Name (for internal use)
                ISState.OFF, # INDI State (ISState.ON:ISState.OFF)
                "Open All"   # Label (for display)
            ),
            ISwitch("close_all", ISState.OFF, "Close All"),
            ISwitch('stop', ISState.OFF, 'Stop')
        ]
        commands_sp = ISwitchVector(
            commands_s,        # The switches in the vector group
            MYDEVICE,          # The device it belongs to
            "commands",        # The name
            IPState.IDLE,      # INDI state for leds (IDLE:OK:BUSY:ALERT)
            ISRule.ATMOST1,    # INDI switch rule (ATMOST1:ONEOFMANY:NOFMANY)
            IPerm.RW,          # Type of property (RW:W:R)
            0,                 # Timeout
            "Commands",        # The label (for display)
            MAIN_CONTROL_GROUP # Group to attach to
        )
        self.IDDef(commands_sp)
        
        # Build status group, light and text read only properties
        # Build lights
        l = []
        for light in status_group_l:
            l.append(
                ILight(no_csp(light), IPState.IDLE, light)
            )
        lp = ILightVector(
            l, MYDEVICE, 'state_message', IPState.IDLE, 0, None, 
            'State Message', MAIN_CONTROL_GROUP 
        )
        self.IDDef(lp)

        # Build texts
        t = []
        for text in status_group_t:
            t.append(IText(no_csp(text), '', text))
        tp = ITextVector(
            t, MYDEVICE, 'states', IPState.IDLE, IPerm.RO, 0, None, 'States',
            MAIN_CONTROL_GROUP
        )
        self.IDDef(tp)

        # Build engineering group, all text read only property
        t = []
        for text in engineering_group_t:
            t.append(IText(no_csp(text), '', text))
        tp = ITextVector(
            t, MYDEVICE, 'details', IPState.IDLE, IPerm.RO, 0, None,
            'Details', ENGINEERING_GROUP
        )
        self.IDDef(tp)

        return

    def ISNewText(self, device, name, names, values):
        """A new text vector has been updated from 
        the client. In this case we update the text
        vector with the IUUpdate function. In a real
        device driver you would probably want to do 
        something more than that. 

        This function is always called by the 
        mainloop
        """

        self.IDMessage(f"Updating {name} text")
        self.IUUpdate(device, name, names, values, Set=True)

    def ISNewNumber(self, device, name, names, values):

        """A numer vector has been updated from the client.
        In this case we update the number with the IUUpdate
        function. In a real device driver you would want to 
        do something more than this. 

        This function is always called by the 
        mainloop
        """

        self.IDMessage(f"Updating {name} number")
        self.IUUpdate(device, name, names, values, Set=True)

    def ISNewSwitch(self, device, name, names, values):

        """A numer switch has been updated from the client.
        This function handles when a new switch
        
        This function is always called by the 
        mainloop
        """


        self.IDMessage(f"{device}, {name=='CONNECTION'}, {names}, {values}")


    @device.repeat(1000)
    def update(self):
        """Gets the upperdome information and sets values"""
        engineering_details = self.IUFind('details')
        status_states = self.IUFind('states')
        state_message = self.IUFind('state_message')

        try:
            data = telescope.upperdome.request_all()
        except Exception:
            # Set to idle since failed to get
            engineering_details.state = IPState.IDLE
            status_states.state = IPState.IDLE
            state_message.state = IPState.IDLE
            self.IDSet(status_states)
            self.IDSet(engineering_details)
            self.IDSet(state_message)
            return
        
        # Update the state message, lights come on depending on what state
        # Reset the lights back to default
        reset_lights(state_message)
        light = state_message[no_csp(data['upperdome_state_message'])]
        state = set_state(light)
        light.value = state
        state_message.state = state
        
        # Set the change
        self.IDSet(state_message)
        
        # Go through and update properties for other sections
        update_properties(data, engineering_details)
        update_properties(data, status_states)
        
        # Set vector property states as OK meaning we got a response
        engineering_details.state = IPState.OK
        
        # Set alert if upperdome faulted
        if not data['upperdome_faulted']:
            status_states.state = IPState.OK
        else:
            status_states.state = IPState.ALERT

        self.IDSet(status_states)
        self.IDSet(engineering_details)

        return 


def no_csp(value):
    """Removes space and case"""
    return value.lower().replace(' ', '_')

def format_boolean(value):
    """Return yes or no"""
    return 'Yes' if value else 'No'

def reset_lights(lvp_selector, state=IPState.IDLE):
    """Resets the state of the light to state IDLE"""
    for l in lvp_selector:
        l.value = state
    return

def set_state(lp_selector):
    # Create sets to check
    ok = {'idle'}
    busy = {
        'domeslit_opening',
        'upper_windscreen_opening',
        'lower_windscreen_opening',
        'lower_windscreen_closing',
        'upper_windscreen_closing',
        'domeslit_closing',
    }
    alert = {'fault'}

    if lp_selector.name in ok:
        return IPState.OK
    elif lp_selector.name in busy:
        return IPState.BUSY
    
    # Return alert state if not found above
    return IPState.ALERT

def update_properties(data, vp_selector):
    """Updates the property values for vp selector"""
    for property in vp_selector:
        # Only update if exists
        if data.get(property.name) is not None:
            value = data[property.name]

            # Format if bool
            if isinstance(value, bool):
                value = format_boolean(value)
            property.value = value
    
    return


sk = Device(name=MYDEVICE)
sk.start()


