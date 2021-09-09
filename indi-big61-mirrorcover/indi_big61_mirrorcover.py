#!/usr/bin/env python3
"""indi_big61_mirrorcover.py

One group - Main Control

Main Control
------------
ISwitchVector : Open, Close
    Want to make it busy when doing open or close
ITextVector : Opened, Closed, Error
    Opened - OK
    Closed - BUSY
    Error  - ALERT

Polling
-------
update : 1000ms
    Grabs the latest telemetry from the mirror covers and updates ITextVector
"""
# Python imports
import sys
from pathlib import Path

# Don't know what this does yet lol
sys.path.insert(0, str(Path.cwd().parent))

# Github imports
from mtnpy import Kuiper
from pyindi.device import *

# Constants
MYDEVICE = 'Mirror Cover'
MAIN_CONTROL_GROUP = 'Main Control'

# State machine for mirror cover
class MirrorCover():
    def __init__(self):
        self._closing = self._opening = False
        self._state = None
    
    @property
    def closing(self):
        return self._closing
    
    @property
    def opening(self):
        return self._opening
    
    @property
    def state(self):
        return self._state

    @closing.setter
    def closing(self, value):
        self._closing = value
        self._opening = False if value else True
    
    @opening.setter
    def opening(self, value):
        self._opening = value
        self._closing = False if value else True

    @state.setter
    def state(self, value):
        self._state = value
    
    def reset(self):
        self._opening = False
        self._closing = False
    
    def done(self):
        """Returns true if done or nothing is happening"""
        if self._closing:
            return self._state == 'Closed'
        elif self._opening:
            return self._state == 'Opened'
        else:
            return True
    def busy(self):
        """Returns true if opening or closing to avoid button presses"""
        return self._closing or self._opening

# Globals
telescope = Kuiper()
mc = MirrorCover()

class Device(device):
    def ISGetProperties(self, device=None):
        """Builds and returns INDI properties for this device"""
        # Build properties
        commands_s = [
            ISwitch(
                'open',      # Name (for internal use)
                ISState.OFF, # INDI State (ISState.ON:ISState.OFF)
                'Open'       # Label (for display)
            ),
            ISwitch('close', ISState.OFF, 'Close')
        ]
        commands_sp = ISwitchVector(
            commands_s,        # The switches in the vector group
            MYDEVICE,          # Device to attach to
            'commands',        # Name (for internal use)
            IPState.IDLE,      # INDI state for leds
            ISRule.ATMOST1,    # INDI switch rule
            IPerm.RW,          # Type of property
            0,                 # Timeout
            'Commands',        # Label (for display)
            MAIN_CONTROL_GROUP # Group to attach to
        )
        states_t = [
            IText(
                'mirror_cover_state',
                '',
                'Mirror Cover State'
            )
        ]
        states_tp = ITextVector(
            states_t,          # List of text properties
            MYDEVICE,          # Device to attach to
            'states',          # Name (for internal use)
            IPState.IDLE,      # INDI state
            IPerm.RO,          # INDI perm
            0,                 # Timeout
            None,              # Timestamp
            'States',          # Label (for display)
            MAIN_CONTROL_GROUP # Group to attach to
        )
        state_message_l = [
            ILight('idle', IPState.IDLE, 'Idle'),
            ILight(
                'mirror_cover_opening', IPState.IDLE, 'Mirror Cover Opening'
            ),
            ILight(
                'mirror_cover_closing', IPState.IDLE, 'Mirror Cover Closing'
            )
        ]
        state_message_lp = ILightVector(
            state_message_l, MYDEVICE, 'state_message', IPState.IDLE, 0, None,
            'State Message', MAIN_CONTROL_GROUP
        )
        
        # Define properties
        self.IDDef(commands_sp)
        self.IDDef(state_message_lp)
        self.IDDef(states_tp)

        return

    def ISNewText(self, device, name, names, values):
        pass

    def ISNewNumber(self, device, name, names, values):
        pass

    def ISNewSwitch(self, device, name, names, values):
        #self.IDMessage(f"{device}, {name=='CONNECTION'}, {names}, {values}")
        # Figure out what switch vp was clicked on
        if name == 'commands':
            if mc.busy():
                # Won't let mirror covers be sent a command when busy
                # Busy means it is either opening or closing
                self.IDMessage('BUSY ignoring button press')
                return

            switch = self.IUUpdate(device, name, names, values)
            if switch['open'].value == 'On':
                # Open the mirror covers
                try:
                    ok = telescope.mirror_cover.command_open()
                    if not ok: raise

                except Exception:
                    switch.state = IPState.ALERT
                    switch['open'].value = 'Off'
                    self.IDMessage('Failed to open mirror covers')
                    self.IDSet(switch)
                    return
                
                # Handle command being fine
                switch.state = IPState.BUSY
                
                mc.opening = True
                # Find state message, reset lights, update
                state_message = self.IUFind('state_message')
                reset_lights(state_message)
                state_message['mirror_cover_opening'].value = IPState.BUSY
                state_message.state = IPState.BUSY

            elif switch['close'].value == 'On':
                # Close the mirror covers
                try:
                    ok = telescope.mirror_cover.command_close()
                    if not ok: raise

                except Exception:
                    switch.state = IPState.ALERT
                    switch['close'].value = 'Off'
                    self.IDMessage('Failed to close mirror covers')
                    self.IDSet(switch)
                    return
                
                # Handle closing command ok
                switch.state = IPState.BUSY
                mc.closing = True
                # Find state message, reset lights, update
                state_message = self.IUFind('state_message')
                reset_lights(state_message)
                state_message['mirror_cover_closing'].value = IPState.BUSY
                state_message.state = IPState.BUSY
            
            self.IDSet(switch)
            self.IDSet(state_message)

        return

    def ISNewLight(self, device, name, names, values):
        pass

    # Poll decorator
    # TODO make async
    @device.repeat(1000)
    def update(self):
        """Called after first getProperties is initiated then every x secs"""
        # Get the vp's for mirror cover
        try:
            states = self.IUFind('states')
    
        except ValueError:
            # Could not find the vp's
            return

        # Get the data from mirror cover
        try:
            data = telescope.mirror_cover.request_state()
        except Exception:
            # Set IDLE for all vector properties for mirror cover
            states.state = IPState.ALERT
            self.IDSet(states)
            mc.state = None
            return
        
        # Go through data and update properties
        update_properties(data, states)
        mc.state = data['mirror_cover_state']
        
        

        # Set ALERT if error in mirror cover data
        indi_states = {
            'Error': IPState.ALERT,
            'Opened': IPState.OK,
            'Closed': IPState.BUSY,
            'Partially Opened': IPState.BUSY
        }
        states.state = indi_states[data['mirror_cover_state']]

        self.IDSet(states)

        # Update state machine for open/close switches
        # I want users to know that its done opening or closing
        if mc.done():
            try:
                commands = self.IUFind('commands')
                state_message = self.IUFind('state_message')
            except ValueError:
                return
            
            commands.state = IPState.IDLE # Reset to IDLE since done
            for c in commands:
                c.value = 'Off'
            mc.reset() # Reset the opening and closing states
            reset_lights(state_message)
            state_message['idle'].value = IPState.OK
            state_message.state = IPState.OK
            self.IDSet(commands)
            self.IDSet(state_message)

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
    
    # Set INDI state to OK since we got a response
    vp_selector.state = IPState.OK
    
    return

driver = Device(name=MYDEVICE)
driver.start()
