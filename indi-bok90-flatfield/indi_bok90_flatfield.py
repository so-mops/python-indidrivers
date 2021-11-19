#!/usr/bin/env python3
# Python imports
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd().parent))

# Github imports
from mtnpy import Bok
from pyindi.device import *

# Constants
MYDEVICE = '90Prime Flatfield'
MAIN_CONTROL_GROUP = 'Main Control'

# Globals
telescope = Bok()

class Device(device):
    def ISGetProperties(self, device=None):
        commands_s = [
            ISwitch("halogen_power", ISState.OFF, "Halogen Power"),
            ISwitch("uband_power", ISState.OFF, "U Band Power"),
        ]
        commands_sp = ISwitchVector(
            commands_s,
            MYDEVICE,
            "commands",
            IPState.IDLE,
            ISRule.NOFMANY,
            IPerm.RW,
            0,
            "Flatfield Lamps",
            MAIN_CONTROL_GROUP
        )
        self.IDDef(commands_sp)

    def ISNewText(self, device, name, values, names):
        pass

    def ISNewNumber(self, device, name, values, names):
        pass

    def ISNewLight(self, device, name, values, names):
        pass

    def ISNewSwitch(self, device, name, values, names):
        """A switch was updated by the client"""
        # Figure out what switch vp was clicked on
        if name == 'commands':
            self.IDMessage(f'Value={values} names={names}')
            sp = self.IUUpdate(device, name, values, names)

            if sp['halogen_power'].value == 'On':
                # Turn on halogen
                try:
                    ok = telescope.ninety_prime_flatfield.command_halogen(True)
                    if not ok: raise
                except Exception as error:
                    self.IDMessage(error)
                    sp.state = IPState.ALERT

            if sp['uband_power'].value == 'On':
                # Turn on uband
                try:
                    ok = telescope.ninety_prime_flatfield.command_uband(True)
                    if not ok: raise
                except Exception as error:
                    self.IDMessage(error)
                    sp.state = IPState.ALERT

            if sp['uband_power'].value == 'Off':
                # Turn off uband
                try:
                    ok = telescope.ninety_prime_flatfield.command_uband(False)
                    if not ok: raise
                except Exception as error:
                    self.IDMessage(error)
                    sp.state = IPState.ALERT

            if sp['halogen_power'].value == 'Off':
                # Turn off halogen
                try:
                    ok = telescope.ninety_prime_flatfield.command_halogen(False)
                    if not ok: raise
                except Exception as error:
                    self.IDMessage(error)
                    sp.state = IPState.ALERT

            # Update switch
            self.IDSet(sp)

        return

    @device.repeat(500)
    def update(self):
        """Called after first getProperties and gets the lamp status"""
        # Get current state
        sp = self.IUFind('commands')
        try:
            data = telescope.ninety_prime_flatfield.request_all()
        except Exception as error:
            self.IDMessage(f'[ERROR] Could not fetch flatfield status')
            sp.state = IPState.ALERT
            self.IDSet(sp)
            return
        
        # Toggle on or off
        if data['uband_lamps']:
            sp['uband_power'].value = 'On'
        else: sp['uband_power'].value = 'Off'

        if data['halogen_lamps']:
            sp['halogen_power'].value = 'On'
        else: sp['halogen_power'].value = 'Off'

        # Set indicator to green
        sp.state = IPState.OK
        self.IDSet(sp)

        return

driver = Device(name=MYDEVICE)
driver.start()
            

