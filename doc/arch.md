[doc](../README.md) > Architecture

# Satnogs-GDN Architecture

![satnogs architecture](automation-server-arch.png)

The project consists of two major components: a station and a server. Station is a reasonably small set of tools that's
intended to be run on Rasbperry Pi (although it can be run on any Linux machine) that conducts the actual observations
and does most of the data processing. Once an observation is completed, it is uploaded to the server. Station is
intended to be fully automated.

The server is able to receive decoded information from multiple stations.
