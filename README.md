# python-indidrivers
Repo for experimenting with python indidrivers for pyindi

## Installation
To use one of these indidrivers you must:
1. Create a virtual env and install necessary requirements
```bash
cd indi-big61-weather
python3 -m venv env
source env/bin/activate
python3 -m pip install -r requirements.txt
deactivate
```
2. Create a small shell script that is called to run the python indidriver
```bash
nano indi_big61_weather

#!/bin/bash
/PATH/TO/REPO/python-indidrivers/indi-big61-weather/env/bin/python3 indi_big61_weather.py
```
3. Move shell script to /usr/local/bin
```bash
sudo cp indi_big61_weather /usr/local/bin
```

Now you can call it using indiserver -v indi_big61_weather

