[![Build Status](https://travis-ci.org/gut-space/satnogs.svg?branch=master)](https://travis-ci.org/gut-space/satnogs)

<img align="right" width="128" height="128" src="https://github.com/gut-space/satnogs/blob/master/doc/logo.png">

The goal of this project is to build a fully functional automated VHF satellite ground station, loosely based on [satnogs](https://satnogs.org) project.

Project founders: [Sławek Figiel](https://github.com/fivitti) and [Tomek Mrugalski](https://github.com/tomaszmrugalski/)

# Project status

As of April 2020, the following features are working:

- WiMo TA-1 antenna, SDR and RPi4 are working
- Automated reception and transmission decoding for NOAA-15, NOAA-18 and NOAA-19 satellites (APT)
- Support for Meteor M2 transmissions (LRPT)
- Transmissions are decoded and uploaded automatically to our content server (see https://satnogs.klub.com.pl)
- automated updates for the server

Work in progress and plans for the next couple weeks:

- record TLE
- fly-over (azimuth/elevation) charts
- user management
- automated updates for the station
- quality assessment for decoded images
- georeferencing

# Documentation

- [Installation](doc/install.md)
- [Architecture](doc/arch.md)
- [User Management](doc/users.md)
- [Project report](doc/prototype-phase/satnogs-gdn-report.pdf)
- [Project poster 1](doc/prototype-phase/poster1-pl.jpg)
- [Project poster 2](doc/prototype-phase/poster2-en.jpg)
