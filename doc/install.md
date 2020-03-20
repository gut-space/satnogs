[doc](../README.md) > Installation

This system consists of two elements: station (which is intended to run on a Raspberry Pi, but can be run on any Linux
box) and a server (which is intended to be run in a place with good uplink connectivity). If you are interested in
running your own station, you most likely want to deploy just the station and use existing server. Please contact
someone from the satnogs team and we'll hook you up.

# Station installation

You need to install [Rasbian](https://www.raspbian.org/) on your Raspberry Pi. Please follow any Raspbian installation
instruction, such as [this one](https://www.raspberrypi.org/documentation/installation/installing-images/). Once
done, connect to your Pi and do the following as root:

1. Install necessary dependencies:

```
apt update
apt install python3-minimal git
```

2. Create satnogs user:

```
# useradd satnogs
```

3. Now switch to the satnogs user:
```
su - satnogs
```

4. This and following steps should be done as satnogs user.

```
git clone https://github.com/gut-space/satnogs
```

5. Run the initial setup script:

```
cd satnogs
python3 station/setup.py
```
this script will conduct several things, such as setting up crontab to run observations periodically, create config file if there isn't any etc.

6. You should tweak the ~/.config/satnogs-gut/config.yml file. In particular, you should tweak the location section. At the very least you need to specify the longitude and lattitude of your station. This is essential to predict satellite flyovers.
