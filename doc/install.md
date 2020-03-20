[doc](../README.md) > Installation

This system consists of two elements: station (which is intended to run on a Raspberry Pi, but can be run on any Linux
box) and a server (which is intended to be run in a place with good uplink connectivity). If you are interested in
running your own station, you most likely want to deploy just the station and use existing server. Please contact
someone from the satnogs team and we'll hook you up.

# Station installation

You need to install [Rasbian](https://www.raspbian.org/) on your Raspberry Pi. Please follow any Raspbian installation
instruction, such as [this one](https://www.raspberrypi.org/documentation/installation/installing-images/). Once
done, connect to your Pi and do the following as root:

1. **Install necessary dependencies**:

```
apt update
apt install python3-minimal git
```

2. **Create satnogs user**:

```
# useradd satnogs
```

3. Now **switch to the satnogs user**:
```
su - satnogs
```

4. **Get the latest satnogs-gut code**. This and following steps should be done as satnogs user.

```
git clone https://github.com/gut-space/satnogs
```

5. **Install python dependencies**:

```
cd satnogs
pip install -r station/requirements.txt
```

This step will install necessary dependencies. It is a good practice to install them in virtual environment. However,
since the scripts will be called using crontab, it would've complicated the setup.

5. **Run the initial setup** script:

```
python3 station/setup.py
```
this script will conduct several things, such as setting up crontab to run observations periodically, create config file if there isn't any etc.

6. **Tweak the ~/.config/satnogs-gut/config.yml file**. In particular, you should tweak the location section. At the very least you need to specify the longitude and lattitude of your station. This is essential to predict satellite flyovers.

# Station management

There is a command line tool used to manage the station. You can run it with:

```
station/cli.py

usage: satnogs-gut [-h] {clear,plan,config} ...

positional arguments:
  {clear,plan,config}  commands
    clear              Clear all schedule receiving
    plan               Schedule planning receiving
    config             Configuration

optional arguments:
  -h, --help           show this help message and exit
  
```

You can use it to inspect your configuration, clear or schedule upcoming transmissions.

# Server installation

Server installation is a manual process. It is assumed that you already have running apache server. Here are the steps needed to get it up and running.

1. **Get the latest code**

```
git clone https://github.com/gut-space/satnogs
```

2. **Install PostgreSQL**:

```
apt install postgresql postgresql-client
su - postgres
psql
CREATE DATABASE satnogs;
CREATE USER satnogs WITH PASSWORD 'secret'; -- make sure to use an actual password here
GRANT ALL PRIVILEGES ON DATABASE satnogs TO satnogs;
```

3. **Modify your apache configuration**

The general goal is to have an apache2 running with WSGI scripting capability that runs Flask. See an [example
apache2 configuation](apache2/satnogs.conf). You may want to tweak the paths and TLS configuration to use LetsEncrypt
or another certificate of your choice. Make sure the paths are actually pointing to the right directory.

4. **Install Flask dependencies**

```
cd satnogs/backend
pip install -r requirements.txt
```

You can start flask manually to check if it's working. This is not needed once you have apache integration complete.

```
cd backend
./satnogs-web.py
```
