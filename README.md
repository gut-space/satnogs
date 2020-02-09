[![Build Status](https://travis-ci.org/gut-space/satnogs.svg?branch=master)](https://travis-ci.org/gut-space/satnogs)

The goal of this project is to build a fully functional automated VHF satellite ground station, loosely based on [satnogs](https://satnogs.org) project.

Project founders: [Sławek Figiel](https://github.com/fivitti) and [Tomek Mrugalski](https://github.com/tomaszmrugalski/)

# Project status

As of Feb 2020, the following features are working:

- WiMo TA-1 antenna, SDR and RPi4 are working
- We are able to receive and decode transmissions from NOAA-15, NOAA-18 and NOAA-19 satellites
- We are able to automatically process them and upload them to our content server (see https://satnogs.klub.com.pl)

# Project plans

- Implement more full featured web front-end (PostgreSQL, Flask, Angular)
- Add more ground stations
- Decode LRPT transmissions
- Migrate to higher bands
- Migrate to directional antenna
