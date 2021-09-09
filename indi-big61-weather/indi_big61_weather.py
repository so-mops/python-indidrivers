#!/usr/bin/env python3

import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd().parent))


from mtnpy import Kuiper
#from aiomtnpy import Kuiper

from pyindi.device import *

MYDEVICE = 'Weather'
OUTSIDE_GROUP = 'Outside'
INSIDE_GROUP = 'Inside'
BOLTWOOD_GROUP = 'Boltwood Information'

telescope = Kuiper()

class WeatherDevice(device):
    def ISGetProperties(self, device=None):
        """Property Definiations are generated
        by initProperties and buildSkeleton. No
        need to do it here. """
        """ 
        connectS = [
            ISwitch(
                "connect",   # Name (for internal use)
                ISState.OFF, # INDI State (ISState.ON:ISState.OFF)
                "Connect"    # Label (for display)
            ),
            ISwitch("disconnect", ISState.ON, "Disconnect")
        ]
        connectSP = ISwitchVector(
            connectS,         # The switches in the vector group
            MYDEVICE,         # The device it belongs to
            "connection",     # The name
            IPState.IDLE,       # INDI state for leds (IDLE:OK:BUSY:ALERT)
            ISRule.ONEOFMANY, # INDI switch rule (ATMOST1:ONEOFMANY:NOFMANY)
            IPerm.RW,         # Type of property (RW:W:R)
            0,                # Timeout
            "Connection",     # The label (for display)
            "Main Control"    # Group to attach to
        ) 
        """

        cloudConditionL = [
            ILight(
                "clear",      # Name (for internal use)
                IPState.IDLE, # INDI state (IDLE:OK:BUSY:ALERT)
                "Clear"       # Label (for display)
            ),
            ILight("cloudy", IPState.IDLE, "Cloudy"),
            ILight("very_cloudy", IPState.IDLE, "Very Cloudy"),
            ILight('unknown', IPState.IDLE, "Unknown")
        ]

        cloudConditionLP = ILightVector(
            cloudConditionL,   # The lights in this vector
            MYDEVICE,          # Device
            'cloud_condition', # Name (internal use)
            IPState.IDLE,      # INDI state for led
            0,                 # Timeout
            None,              # Timestamp
            "Cloud Condition", # Label (for display)
            OUTSIDE_GROUP      # Group to attach to
        )

        windConditionL = [
            ILight("calm", IPState.IDLE, "Calm"),
            ILight("windy", IPState.IDLE, "Windy"),
            ILight("very_windy", IPState.IDLE, "Very Windy"),
            ILight('unknown', IPState.IDLE, "Unknown")
        ]

        windConditionLP = ILightVector(
            windConditionL, MYDEVICE, 'wind_condition', IPState.IDLE, 0, None,
            "Wind Condition", OUTSIDE_GROUP
        )

        daylightConditionL = [
            ILight("dark", IPState.IDLE, "Dark"),
            ILight("light", IPState.IDLE, "Light"),
            ILight("very_light", IPState.IDLE, "Very Light"),
            ILight('unknown', IPState.IDLE, "Unknown")
        ]

        daylightConditionLP = ILightVector(
            daylightConditionL, MYDEVICE, 'daylight_condition', IPState.IDLE, 0, None,
            "Daylight Condition", OUTSIDE_GROUP
        )

        rainConditionL = [
            ILight("dry", IPState.IDLE, "Dry"),
            ILight("moist", IPState.IDLE, "Moist"),
            ILight("raining", IPState.IDLE, "Raining"),
            ILight('unknown', IPState.IDLE, "Unknown")
        ]

        rainConditionLP = ILightVector(
            rainConditionL, MYDEVICE, 'rain_condition', IPState.IDLE, 0, None,
            "Rain Condition", OUTSIDE_GROUP
        )

        out_readings_t = [
            IText(
                'outside_temperature', # Name (for internal use)
                '',                    # Value
                'Temperature'          # Label (for display)
            ),
            IText('outside_humidity', '', 'Humidity'),
            IText('outside_dew_point', '', 'Dew Point'),
            IText('wind_speed', '', 'Wind Speed')
        ]

        out_readings_tp = ITextVector(
            out_readings_t, # List of IText properties
            MYDEVICE,       # Device belongs to
            'out_readings', # Name (for internal use)
            IPState.IDLE,   # INDI state
            IPerm.RO,       # INDI perm (RW/RO)
            0,              # Timeout (float)
            None,           # Timestamp
            'Readings',     # Label (for display)
            OUTSIDE_GROUP   # Group to attach to
        )

        in_readings_t = [
            IText('tube_temperature', '', 'Tube Temperature'),
            IText('dome_temperature', '', 'Dome Temperature'),
            IText('dome_humidity', '', 'Dome Humidity'),
            IText('dome_dew_point', '', 'Dome Dew Point')
        ]

        in_readings_tp = ITextVector(
            in_readings_t, MYDEVICE, 'in_readings', IPState.IDLE, IPerm.RO, 0,
            None, 'Readings', INSIDE_GROUP
        )

        boltwood_t = [
            IText('sky_temperature', '', 'Sky Temperature'),
            IText('boltwood_sensor_temperature', '', 'Sensor Temperature'),
            IText('boltwood_heater', '', 'Heater On')
        ]

        boltwood_tp = ITextVector(
            boltwood_t, MYDEVICE, 'boltwood', IPState.IDLE, IPerm.RO, 0, None,
            'Boltwood', BOLTWOOD_GROUP
        )

        self.IDDef(cloudConditionLP)
        self.IDDef(windConditionLP)
        self.IDDef(daylightConditionLP)
        self.IDDef(rainConditionLP)
        self.IDDef(out_readings_tp)
        self.IDDef(in_readings_tp)
        self.IDDef(boltwood_tp)
        pass

    #def initProperties(self):
        """Build the vector properties from
        the skeleton file."""
        #self.buildSkeleton("indi_big61_weather.xml")

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
    def update_boltwood(self):
        """
        This function is called after the first get
        properties is initiated and then every 1000ms 
        after that. 
        """
        conditions = ['cloud', 'wind', 'rain', 'daylight']
        # Get the vp's for the boltwood
        try:
            out_readings = self.IUFind('out_readings')
            boltwood = self.IUFind('boltwood')
        except ValueError:
            # IUFind could not find the property
            return
        
        # Get the data using mtnpy
        try:
            data = telescope.boltwood.request_all()
        except Exception:
            # Set IDLE for all vector properties for boltwood
            for condition in conditions:
                # Find the light vector property
                try:
                    lvp_selector = self.IUFind(f'{condition}_condition')
                except ValueError:
                    # IUFind could not find the property
                    return
                lvp_selector.state = IPState.IDLE
                self.IDSet(lvp_selector)
                
            out_readings.state = IPState.IDLE
            boltwood.state = IPState.IDLE
            self.IDSet(out_readings)
            self.IDSet(boltwood)

            return

        # Go through all conditions and update lights
        for property in out_readings:
            property.value = data[property.name]
        
        for property in boltwood:
            property.value = data[property.name]

        out_readings.state = IPState.OK
        boltwood.state = IPState.OK
        self.IDSet(out_readings)
        self.IDSet(boltwood)
        
        # Update the light properties from boltwood
        conditions = ['cloud', 'wind', 'rain', 'daylight']
        for condition in conditions:
            # Find the light vector property
            try:
                lvp_selector = self.IUFind(f'{condition}_condition')
            except ValueError:
                # IUFind could not find the property
                return
                
            # Reset the lights back to default
            reset_lights(lvp_selector)

            # Select the correct light to change state
            lp_selector = lvp_selector[no_csp(data[f'{condition}_condition'])]
            state = set_state(lp_selector)
            lp_selector.value = state
            lvp_selector.state = state
            # Set the change
            self.IDSet(lvp_selector)
        
        return

    @device.repeat(1000)
    def update_onewire(self):
        """Gets the onewire information and sets values"""
        tvp_selector = self.IUFind('in_readings')
        # Get the data using mtnpy
        try:
            data = telescope.onewire.request_all()
        except Exception:
            # Set to idle since failed to parse
            tvp_selector.state = IPState.IDLE
            self.IDSet(tvp_selector)
            return
        
        # Go through and get all properties
        for key, value in data.items():
            tp_selector = tvp_selector[key]

            if isinstance(value, bool):
                value = format_boolean(value)
            
            tp_selector.value = value

        tvp_selector.state = IPState.OK
        self.IDSet(tvp_selector)








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
    ok = {'calm', 'clear', 'dry', 'dark'}
    busy = {'cloudy', 'windy', 'moist', 'light'}
    alert = {'very cloud', 'very windy', 'raining', 'very light', 'unknown'}

    if lp_selector.name in ok:
        return IPState.OK
    elif lp_selector.name in busy:
        return IPState.BUSY
    
    # Return alert state if not found above
    return IPState.ALERT

def pprint(value):
    sys.stderr.write(value)


sk = WeatherDevice(name=MYDEVICE)
sk.start()


