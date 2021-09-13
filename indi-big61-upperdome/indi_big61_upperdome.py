#!/usr/bin/env python3
"""indi_big61_upperdome.py

Groups
------
Main Control : Primary actions and telemetry
Engineering  : Data for diagnostics and mtnops staff

Main Control
------------
SP : commands
     Open All, Close All, Stop

    Logic
    -----
    Cannot Open All then Close All until finished
    Can cancel Open All by Stop
    Cannot Close All then Open All until finished
    Can cancel Close All by Stop

    Switch Logic
    ------------
    Button stays depressed until state gets to IDLE or FAULT in state message

    LED SP Logic
    ------------
    IDLE  : No commands sent and not currently Open All or Close All
    OK    : Never
    BUSY  : When the state message is anything but Idle or Fault
    ALERT : When a command is failed to send or state message is Fault
    
LP : state_message
     Idle, Domeslit Opening, Upper Windscreen Opening, Lower Windscreen 
     Opening, Lower Windscreen Closing, Upper Windscreen Closing, Domslit 
     Closing, Fault

    Logic
    -----
    Update during polling
    Reset all lights 
    Update light that state message value is

    LED LP Logic
    ------------
    IDLE  : On startup and whenever communication drops
    OK    : Idle
    BUSY  : Domeslit Opening, Upper Windscreen Opening, Lower Windscreen 
            Opening, Lower Windscreen Closing, Upper Windscreen Closing, 
            Domslit Closing
    ALERT : Fault

TP : states
     Domeslit State, UpperWS State, LowerWS State, Local Mode SW, Upperdome
     Faulted

    Logic
    -----
    Updates during polling

    LED TP Logic
    ------------
    IDLE  : On startup and whenever communication drops
    OK    : Domeslit State & UpperWS State & LowerWS State all equals Opened
    BUSY  : Same as above but any of them equal to Closed
    ALERT : Local Mode SW or Upperdome Faulted are true (yes)

Engineering
-----------
TP : details
     Upperdome State Integer, Upperdome IO Byte, Upperdome Fault Byte, 
     Domeslit Opened LimitSW, Domeslit Closed LimitSW, UpperWS Opened LimitSW, 
     UpperWS Closed LimitSW, LowerWS Opened LimitSW, LowerWS Closed LimitSw, 
     Domeslit Faulted, UpperWS Faulted, LowerWS Faulted

    Logic
    -----
    Updates during polling

    LED TP Logic
    ------------
    IDLE  : On startup and whenever communication drops
    OK    : Communication was successful for polling
    BUSY  : Never
    ALERT : Never
"""
# Python imports
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd().parent))

# Github imports
from mtnpy import Kuiper
from pyindi.device import *

# Constants
MYDEVICE = 'Upper Dome'
MAIN_CONTROL_GROUP = 'Main Control'
ENGINEERING_GROUP = 'Engineering'

# INDI Properties
STATE_MESSAGE_LVP = [
    'Idle',
    'Domeslit Opening',
    'Upper Windscreen Opening',
    'Lower Windscreen Opening', 
    'Lower Windscreen Closing',
    'Upper Windscreen Closing', 
    'Domeslit Closing', 
    'Fault'
]
STATES_TVP = [
    'Domeslit State',
    'UpperWS State',
    'LowerWS State',
    'Local Mode SW',
    'Upperdome Faulted'
]
DETAILS_TVP = [
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

# State machine for upperdome
class UpperDome():
    def __init__(self):
        self._state = None
    
    @property
    def state(self):
        return self._state
    
    @state.setter
    def state(self, value):
        self._state = value
    
    def busy(self):
        """Returns true is state is anything but idle"""
        return self._state != 'Idle'

# Globals
telescope = Kuiper()
upper_dome = UpperDome()

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
        commands_svp = ISwitchVector(
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
        self.IDDef(commands_svp)
        
        # Build status group, light and text read only properties
        # Build lights
        lights = []
        for light in STATE_MESSAGE_LVP:
            lights.append(
                ILight(no_csp(light), IPState.IDLE, light)
            )
        lvp = ILightVector(
            lights, MYDEVICE, 'state_message', IPState.IDLE, 0, None, 
            'State Message', MAIN_CONTROL_GROUP 
        )
        self.IDDef(lvp)

        # Build texts
        texts = []
        for text in STATES_TVP:
            texts.append(IText(no_csp(text), '', text))
        tvp = ITextVector(
            texts, MYDEVICE, 'states', IPState.IDLE, IPerm.RO, 0, None, 
            'States', MAIN_CONTROL_GROUP
        )
        self.IDDef(tvp)

        # Build engineering group, all text read only property
        texts = []
        for text in DETAILS_TVP:
            texts.append(IText(no_csp(text), '', text))
        tvp = ITextVector(
            texts, MYDEVICE, 'details', IPState.IDLE, IPerm.RO, 0, None,
            'Details', ENGINEERING_GROUP
        )
        self.IDDef(tvp)

        return

    def ISNewText(self, device, name, values, names):
        pass

    def ISNewNumber(self, device, name, values, names):
        pass

    def ISNewLight(self, device, name, values, names):
        pass

    # FIXME Had to switch values and names because it was wrong order
    # FIXME Had to do this for IUUpdate as well since wrong order
    def ISNewSwitch(self, device, name, values, names):
        """A switch was updated by the client"""
        # Figure out what switch vp was clicked on
        if name == 'commands':
            self.IDMessage(f'values are equal to {values} names={names}')
            # If stop is selected...
            stop = False
            if 'stop' in names:
                stop_index = names.index('stop')
                stop = values[stop_index] == 'On'

            # Even if busy let it send stop
            if upper_dome.busy() and stop:
                svp = self.IUUpdate(device, name, values, names)
                # Send stop to upperdome
                try:
                    ok = telescope.upperdome.command_stop()
                    if not ok: raise

                    # Finish stop
                    svp.state = IPState.BUSY
                    self.IDMessage('Stopped upperdome')
                    self.IDSet(svp)
                    return 

                except Exception:
                    svp.state = IPState.ALERT
                    svp['stop'].value = 'Off'
                    self.IDMessage('Failed to stop upperdome')
                    self.IDSet(svp)

                    return
                
            elif upper_dome.busy():
                # Don't let upperdome be sent a command unless it is stop
                self.IDMessage('Busy...ignoring all buttons except stop')
                return
            
            # Handle normal cases
            svp = self.IUUpdate(device, name, values, names)
            if svp['open_all'].value == 'On':
                # Open all
                try:
                    ok = telescope.upperdome.command_all_open()
                    if not ok: raise
                except Exception:
                    svp.state = IPState.ALERT
                    svp['open_all'].value == 'Off'
                    self.IDMessage('Failed to open all upperdome')
                    self.IDSet(svp)
                    
                    return
                
                # SwitchLEDs are handled from state message

            elif svp['close_all'].value == 'On':
                # Close all
                try:
                    ok = telescope.upperdome.command_all_close()
                    if not ok: raise
                except Exception:
                    svp.state = IPState.ALERT
                    svp['close_all'].value == 'Off'
                    self.IDMessage('Failed to close all upperdome')
                    self.IDSet(svp)

                    return
                
            elif svp['stop'].value == 'On':
                # Stop it
                try:
                    ok = telescope.upperdome.command_stop()
                    if not ok: raise
                    # Even though state message updates LED, want users to see
                    # some busy light when stopped, even if a second
                    svp.state = IPState.BUSY
                except Exception:
                    svp.state = IPState.ALERT
                    svp['stop'].value == 'Off'
                    self.IDMessage('Failed to stop upperdome')
                    self.IDSet(svp)

                    return
            
            # Update commands switch
            self.IDSet(svp)
                          
        return
                    
    @device.repeat(1000)
    def update(self):
        """Gets the upperdome information and sets values"""
        try:
            engineering_details_tvp = self.IUFind('details')
            states_tvp = self.IUFind('states')
            state_message_lvp = self.IUFind('state_message')
        except ValueError:
            self.IDMessage('Cannot retrieve vector property')
            return

        try:
            data = telescope.upperdome.request_all()
        except Exception:
            # Set to idle since failed to get
            engineering_details_tvp.state = IPState.IDLE
            states_tvp.state = IPState.IDLE
            state_message_lvp.state = IPState.IDLE
            self.IDSet(states_tvp)
            self.IDSet(engineering_details_tvp)
            self.IDSet(state_message_lvp)
            return
        
        # Got a response, update state machine
        upper_dome.state = data['upperdome_state_message']

        # Update the state message, lights come on depending on what state
        # Reset the lights back to default
        reset_lights(state_message_lvp)
        message = no_csp(data['upperdome_state_message']) # Format to match
        light = state_message_lvp[message]
        state = set_state(light)
        light.value = state # Update light
        state_message_lvp.state = state # Update LP
        
        # Set the change
        self.IDSet(state_message_lvp)
        
        # Go through and update properties for other sections
        update_properties(data, engineering_details_tvp)
        update_properties(data, states_tvp)
        
        # Set vector property states as OK meaning we got a response
        engineering_details_tvp.state = IPState.OK
        
        # Set alert if upperdome faulted
        # Format States LED TP
        current_states = [
            data['domeslit_state'],
            data['upperws_state'],
            data['lowerws_state']
        ]
        if data['upperdome_faulted'] or data['local_mode_sw']:
            states_tvp.state = IPState.ALERT
        # Check if either Closed or Partially Opened in current_states
        elif any(s in ['Closed', 'Partially Opened'] for s in current_states):
            states_tvp.state = IPState.BUSY
        elif all(s == 'Opened' for s in current_states): # Check if all == Open
            states_tvp.state = IPState.OK
    
        self.IDSet(states_tvp)
        self.IDSet(engineering_details_tvp)

        # Update state machine for commands
        if not upper_dome.busy():
            try:
                commands = self.IUFind('commands')
            except ValueError:
                return
            
            commands.state = IPState.IDLE # Reset to IDLE since not busy

            # Update switches for commands
            for c in commands:
                c.value = 'Off'
            
            self.IDSet(commands)

        return 

def no_csp(value):
    """Removes space and case"""
    return value.lower().replace(' ', '_')

def format_boolean(value):
    """Return yes or no"""
    return 'Yes' if value else 'No'

def reset_lights(lvp, state=IPState.IDLE):
    """Resets the state of the light to state IDLE"""
    for light in lvp:
        light.value = state
    return

def set_state(light):
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

    if light.name in ok:
        return IPState.OK
    elif light.name in busy:
        return IPState.BUSY
    
    # Return alert state if not found above
    return IPState.ALERT

def update_properties(data, vp):
    """Updates the property values for vp selector"""
    for property in vp:
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


