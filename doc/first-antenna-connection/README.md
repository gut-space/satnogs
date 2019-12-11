---
title: Crossed Dipole antenna Evaluation
subtitle: Preliminary Report
author:
  - Sławomir Figiel
  - Tomasz Mrugalski
  - Ewelina Omernik
lang: en
date: |
   | Politechnika Gdańska
   | 2019-12-11
classoption: twocolumn
papersize: a4paper
---

# Antenna

We ordered a TA-1 Turnstile antenna directly from WiMo, a vendor based in Germany. It was shipped without any connectors, with bare coax cable. After consultation with dr Siwicki, an N-connector plug was chosen due to improved resilience to adverse weather. A low-loss adapter cable N-SMA has been obtained.

* Type: VHF
* Length: 130 cm
* Weight: 2 kg
* Polarization: circular, clockwise
* Range: 137-152 MHz
* Feed: 50 $\Omega$
* SWR: <2
* Gain: 0dB (high elv) <4 dB (low elv)

Antenna was mounted on the Tomek's terrace on the top floor. Mounting location has been chosen to maximize exposure to the southern sky. From the north side it was obscured by wall and roof.

# First connection

During the test time the best pass parameters had NOAA 18 satellite. We adjusted the SDR to frequency 137.9125 MHz and started observations. We noticed that the noise level was -82dB. However, the downlink signal had very poor quality. It was at level -78 dB. It had very narrow width, without any side bands. Such signal was deemed unusable and it was not possible to extract any imagery from this signal.

# Compare to old antenna

So far we used a simply turnstile antenna attached to SDR. It is low quality and small length. Nevertheless, we managed to receive and decode correctly a few images from NOAA satellites. It was replaced it with new antenna during NOAA 18 pass.
The parameters of the signal changed. The noise level increased to -75 dB. The downlink signal increased to -60 dB. At specified frequency we had noticeable, wide beam. We noticed also a lot of side bands.
Probably it is possible to extract imagery from recorded data, but we change the antenna in record time and our current algorithm wasn't prepare to handle it. Based on previous experienced the output picture will be strongly noised but on part recorded above antenna the details would be noticeable.

# Conclusions

There is definitely a problem with the new antenna. We cannot receive useful signal on selected frequency.  
The issue will be investigated further with the hope of finding the root cause of the problem. Several areas require further testing. First, we need to check the new cable cable (if it has good impedance and quality, if there is no short circuit) and antenna. The current plan is to test the antenna first in an open space around GUT campus area. Next we want to measure parameters of antenna in the laboratory.

![New antenna - very low quality signal. Only on main frequency exists little peak, but its level is greater by 4dB then noise. This peak is visible even when satellite doesn't pass. None side band occurs.](first-antenna-connection/signal_new.png)

![Old antenna - medium quality signal. We noticed data beam. We had 15 dB difference between useful signal and noise. Some side bands.](first-antenna-connection/signal_old.png)

![Waterfall of signal. At the bottom is signal on new antenna. The noise level is low (blue), but the signal is faint (center yellow). At the top is signal on old antenna. The noise level is high (yellow on sides). The useful signal is relative clear (center orange). At 17:48:30 the center line becomes zigzag. It is moment when satellite has passed the roof.](first-antenna-connection/wf_new_old.png)